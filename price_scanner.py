#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu
# Last Updated: June 6, 2019

### PURPOSE:
### This code scans over already found URLs for arbitrage opportunities.

from selenium import webdriver              # Primary navigation of Steam price data.
from selenium.common.exceptions import NoSuchElementException 
                                            # ^^ Dealing with page load failure.
from utility_funcs import import_json_lines # Importing logged dataset
from utility_funcs import DBchange          # Add items to database safely
from datetime import datetime, timedelta    # Volumetric sale filtering based on date
import time                                 # Waiting so no server-side ban
import json                                 # Writing and reading logged dataset
# from analysis import ---- # Later include things like SMA here

### Hyperparameters {
navigation_time = 6 # Global wait time between page loads
username = 'datafarmer001'
password = 'u9hqgi3sl9'
startloc = 200 # Item in database to start price scanning from
### }

# -----------------------------------====Data Cleaning Functions====-----------------------------------
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def readUSD(dollars):
    numbers = set('0123456789.')
    return float(''.join([x for x in dollars if x in numbers]))

def cleanListing(mess, itemname):
    ### Sometimes Steam will dynamically show "Sold!" or the like when it sells at item. 
    #   This function prevents the reader from stumbling.
    mess = mess.split('\n')
    # Does this instead of a spacing-based system because 'Sold!' changes the spacing.
    disallowed = {'PRICE', 'SELLER', 'NAME', 'Sold!', 'Buy Now', 
                  'Counter-Strike: Global Offensive', itemname}
    numbers = set('0123456789.')
    return sorted([readUSD(x) for x in mess if x not in disallowed])

def cleanVolumetric(data):
    # Parses data from the price chart on an item listing
    data = data[data.find('var line1')+10:data.find(']];')+2] # Gets all price data from chart
    if data == '': # No recent prices - rarely sold item
        return []
    better_data = eval(data) # JS has the same format lists as Python, so eval is fine
    better_data = [[x[0][:3],x[0][4:6],x[0][7:11],x[0][12:14],x[1]] for x in better_data] # Cuts date info into easily accessible bits
    month_lookup = {'Jan': 1, 'Feb': 2, 'Mar': 3,
                    'Apr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9,
                    'Oct': 10, 'Nov': 11, 'Dec': 12}
    better_data = [[datetime(year=int(x[2]),month=month_lookup[x[0]],day=int(x[1]), hour=int(x[3])),x[4]] for x in better_data]

    # Cuts data to recent data (within last 30 days of sales)
    last_month = datetime.now() - timedelta(days=30)
    now = datetime.now()
    recent_data = [x for x in better_data if last_month < x[0] < now]
    
    return recent_data

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# -----------------------------------===============================-----------------------------------

def filter(DB):
    # Filter by volume; must have greater than 30 sales last month
    DB = [x for x in DBdata if len(x['Sales from last month']) > 30]
    return DB

class waitUntil():
    # Enforces that everything inside a "with waitUntil(10):" block waits 10 seconds to complete
    # For more info, see https://jeffknupp.com/blog/2016/03/07/python-with-context-managers/
    def __init__(self, lengthwait):
        self.start = 0
        self.lengthwait = lengthwait
    def __enter__(self):
        self.start = time.time()
        return self.start
    def __exit__(self, *args):
        elapsed = time.time() - self.start
        if elapsed < self.lengthwait:
            time.sleep(self.lengthwait-elapsed)

if __name__ == '__main__':
    DBdata = import_json_lines('pagedata.txt',encoding='utf_16',numlines=11)
    of_interest = filter(DBdata)
    of_interest = of_interest[startloc:] # See hyperparams for startloc
    assert len(of_interest) >= 10, ('price_scanner.py will not write if the volume filtered dataset'
                                    'is smaller than 10. Current size' + str(len(of_interest)))
    browser = webdriver.Chrome(r'/home/order/Videos/chromedriver/chromedriver') # Linux
    find_css = browser.find_element_by_css_selector

    # Login
    login_url = r'https://store.steampowered.com//login/'
    browser.get(login_url)
    time.sleep(3)
    username_box = find_css('#input_username')
    password_box = find_css('#input_password')
    username_box.send_keys(username)
    time.sleep(1)
    password_box.send_keys(password)
    time.sleep(3)
    sign_in = find_css('#login_btn_signin > button')
    sign_in.click()

    # Since we're using a verified account, need to have human fill out 2FA
    # Currently locked to my phone
    with waitUntil(navigation_time):
        code_confirmation = input('Did you enter your Steam confirmation code? [y\\n]')
        if code_confirmation not in ['y','Y','yes','Yes','yep']:
            raise Exception('Well why didn\'t you??')

    to_write = [] # Item data to be updated in database
    for itemno, item in enumerate(of_interest):
        browser.get(item['URL'])
        with waitUntil(navigation_time):
            browser.implicitly_wait(15)
            try:
                full_listing = find_css('#searchResultsRows').text
            except NoSuchElementException:
                browser.refresh()
                time.sleep(navigation_time*2)
                full_listing = find_css('#searchResultsRows').text
            itemized = cleanListing(full_listing,item['Item Name'])
            try:
                buy_rate = readUSD(find_css('#market_commodity_buyrequests > '
                                                'span:nth-child(2)').text)
                # ^^ Highest buy order currently on the market. 
                # If a price drops below this, it will immediately be purchased by the buy orderer.
            except NoSuchElementException:
                buy_rate = 0 # Sometimes there are no buy orders
            
            # Grab volumetric data for recent sales/prices (from chart).
            volumetrics = find_css('body > div.responsive_page_frame.with_header > div.responsive_page_content > div.responsive_page_template_content')
            recent_data = cleanVolumetric(volumetrics.get_attribute('outerHTML'))
            
            pagedata = {
                'Item Name': item['Item Name'],
                'URL': browser.current_url, # In case they update the URL and leave a redirect
                'Special Type': item['Special Type'],
                'Condition': item['Condition'],
                'Sales/Day': round(len(recent_data)/30, 2),
                'Buy Rate': buy_rate,
                'Date': datetime.now(),
                'Sales from last month': recent_data,
                'Listings': itemized
            }

            to_write.append(pagedata)

            # ========================== TODO: ANALYSIS GOES HERE ==========================
            # printable_outputs = anaylze([method1, method2, ...], logfile)
            # Logfile should only be written if positive outcome; we can do testing on analysis.py

            print('    ' + str(itemno+1) + '.', item['Item Name'], itemized[0], pagedata["Sales/Day"])
            # TODO: Add analysis output to print statement

            # Update pagedata file every 10 items
            if (itemno + 1)%10 == 0:
                DBchange(to_write,'update','pagedata.txt')
                to_write = []
                print('    [WROTE TO FILE.]')
                print()

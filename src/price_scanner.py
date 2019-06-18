#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### PURPOSE:
### This code scans over already found URLs for arbitrage opportunities.

from selenium import webdriver              # Primary navigation of Steam price data.
from selenium.common.exceptions import NoSuchElementException 
                                            # ^^ Dealing with page load failure.
import pandas as pd                         # Primary dataset format
from bs4 import BeautifulSoup               # Reading prices and seller ID from page
from utility_funcs import import_json_lines # Importing logged dataset
from utility_funcs import DBchange          # Add items to database safely
from analysis import volumeFilter           # Only want high sale volume items
from analysis import LessThanThirdQuartileHistorical 
                                            # Notify of buy-worthy things while running
from datetime import datetime, timedelta    # Volumetric sale filtering based on date
import time                                 # Waiting so no server-side ban
import json                                 # Writing and reading logged dataset

### Hyperparameters {
navigation_time = 2 # Global wait time between page loads
username = 'datafarmer001'
password = 'u9hqgi3sl9'
startloc = 0 # Item in database to start price scanning from
nloops = 12
verbose = False # Print data about each item when scanned
### }

# -----------------------------------====Data Cleaning Functions====-----------------------------------
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def readUSD(dollars):
    numbers = set('0123456789.')
    return float(''.join([x for x in dollars if x in numbers]))

def cleanListing(html):
    ### Get prices from html output from #searchresultsrows
    soup = BeautifulSoup(html, 'html.parser')
    priceraw = [x for x in soup.find_all('span', class_='market_listing_price market_listing_price_with_fee')]
    prices = []
    for i in priceraw:
        prices.append(i.get_text().strip())

    idraw = soup.find_all('a')
    ids = []
    for i in idraw:
        found = i.get('id')
        if found:
            ids.append(found.split('_')[1])

    # The following line filters out any items which say 'Sold!', which is a dynamic updating
    # thing that sometimes happens during data pull.
    # list(zip(*n)) does [(a1,b1),...] -> [[a1, a2, ...], [b1, b2, ...]]
    prices, ids = list(zip(*[(readUSD(x),y) for x,y in zip(prices, ids) if x != 'Sold!']))
    return prices, ids

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

def navigateItem(browser):
    # TODO: For later joining of selenium-related codes
    pass

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# -----------------------------------===============================-----------------------------------

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
    DBdata = pd.read_hdf('../data/item_info.h5', 'item_info')
    # DBdata = import_json_lines('../data/pagedata.txt',encoding='utf_8')
    of_interest = DBdata[DBdata['Sales/Day'] >= 1]
    # of_interest = [x for x in DBdata if volumeFilter(x, 30)]
    of_interest = of_interest.iloc[startloc:,:]
    # of_interest = of_interest[startloc:] # See hyperparams for startloc
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

    count = 0
    # to_write = [] # Item data to be updated in database
    for iterator in range(nloops):
        for itemno, item in of_interest.iterrows():
            # Note that itemno preserves the index from DBdata. Thus we need count for file writing
            # This is convenient for DBdata updates, however...
            haslistings = True
            browser.get(item['URL'])
            with waitUntil(navigation_time):
                browser.implicitly_wait(15)
                try:
                    prices_element = find_css('#searchResultsRows')
                except NoSuchElementException:
                    browser.refresh()
                    time.sleep(navigation_time*2)
                    try:
                        prices_element = find_css('#searchResultsRows')
                    except NoSuchElementException:
                        # Probably no items
                        haslistings = False
                
                if haslistings:
                    itemized, IDs = cleanListing(prices_element.get_attribute('outerHTML'))
                else:
                    itemized, IDs = ([], [])
                
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
                    'Listings': itemized,
                    'Listing IDs': IDs
                }

                # Itemno preserves the original DBdata index!
                DBdata.iloc[itemno,:] = pd.Series(pagedata)

                # to_write.append(pagedata)
                if itemized: # Nonempty
                    satcheck = LessThanThirdQuartileHistorical.runindividual(pagedata)
                    ### TODO: Once vks is done with analysis, convert this over.
                    ###       Should function as is for now.
                    if satcheck['Satisfied']:
                        print('!!!!', 'Found a Q3 satisfying item')
                        print(satcheck)
                        DBchange([pagedata],'add','../data/LTTQHitems.txt')
                    if verbose:
                        print('    ' + str(itemno+1) + '.', item['Item Name'], itemized[0], pagedata["Sales/Day"])
                else:
                    if verbose:
                        print('    ' + str(itemno+1) + '.', item['Item Name'], '[]', pagedata["Sales/Day"])

                # Update pagedata file every 10 items
                count += 1
                if (count + 1)%10 == 0:
                    DBdata.to_hdf('../data/item_info.h5','item_info')
                    print('    [WROTE TO FILE.]')
        print('New loop.')
#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu
# Last Updated: June 6, 2019

### PURPOSE:
### This program gathers URLs for steam items,  as well as relevant page information for that item.
### The idea is to later stick it into price_scanner.py for actual arbitrage search.

### TODO:

### 1. Implement streaming system (data gathering should asynchronously send data to 
###    another waiting socket which analyzes it).
###    This will greatly increase code readability (you can stick all the page navigation into 
###    a function, and then stick the data analysis elsewhere).
###    This will probably allow for actual automation, as well - 
###    we can have program change inputs on another socket, and change it while it runs.

### 2. Implement better fault tolerance for "NoSuchElementException"
###    In other words, write a with()able function which has graceful error handling

### 3. Dataset read is pretty slow - figure out a way to improve read rates. See analysis.py for
###    how slow it tends to be.

### 4. Bring price_scanner.py and utility_funcs.py in compliance with pylint + 100 character lines.

### 5. Log low volume items separately so it takes up less memory. Ideally, create a global
###    variable settings database for these kind of filterings.

### 6. Add a requirements.txt

### 7. Fix inconsistent casing (do camelCase on functions, caps for const.)

### 8. Contemplate adding type hints

from selenium import webdriver              # Primary navigation of Steam price data.
from selenium.common.exceptions import NoSuchElementException 
                                            # ^^ Dealing with page load failure.
from utility_funcs import import_json_lines # Importing logged dataset
from utility_funcs import DBchange          # Add items to database safely
from datetime import datetime, timedelta    # Volumetric sale filtering based on date
import time                                 # Waiting so no server-side ban
import sys                                  # Input pages from command line
import json                                 # Writing and reading logged dataset

### Hyperparameters {
GENERAL_URL = 'https://steamcommunity.com/market/search?q=&category_730_ItemSet%5B%5D=any&' \
              'category_730_ProPlayer%5B%5D=any&category_730_StickerCapsule%5B%5D=any&'     \
              'category_730_TournamentTeam%5B%5D=any&category_730_Weapon%5B%5D=any&'        \
              'category_730_Exterior%5B%5D=tag_WearCategory0&appid=730#p'
INITIAL_PAGE = int(sys.argv[1]) # 40
FINAL_PAGE = int(sys.argv[2]) # 70 # Inclusive
NAVIGATION_TIME = 6 # Global wait time between page loads
USERNAME = 'datafarmer001'
PASSWORD = 'u9hqgi3sl9'
### }

# ---------------------------------====Data Cleaning Functions====---------------------------------
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

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
    if data == '': # No last month sales
        return []
    better_data = eval(data) # JS has the same format lists as Python, so eval is fine
    better_data = [[x[0][:3], x[0][4:6], x[0][7:11], x[0][12:14], x[1]] for x in better_data] 
    #  ^^ Cuts date info into easily accessible bits
    month_lookup = {'Jan': 1, 'Feb': 2, 'Mar': 3,
                    'Apr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9,
                    'Oct': 10, 'Nov': 11, 'Dec': 12}
    better_data = [[datetime(year=int(x[2]), month=month_lookup[x[0]],
                    day=int(x[1]), hour=int(x[3])), x[4]]
                    for x in better_data]

    # Cuts data to recent data (within last 30 days of sales)
    last_month = datetime.now() - timedelta(days=30)
    now = datetime.now()
    lastmo_data = [x for x in better_data if last_month < x[0] < now]
    
    return lastmo_data

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# -----------------------------------===============================-------------------------------

# Enforces that everything inside a "with WaitUntil(10):" block waits 10 seconds to complete
# (waits at end if not timed out yet)
# For more info, see https://jeffknupp.com/blog/2016/03/07/python-with-context-managers/
class WaitUntil():
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

# Import old found items, ignore any with the same name. We're looking for new items only.
DBdata = import_json_lines('pagedata.txt', encoding='utf_16', numlines=11)
ignore_names = set([x['Item Name'] for x in DBdata])

browser = webdriver.Chrome(r'/home/order/Videos/chromedriver/chromedriver') # Linux
find_css = browser.find_element_by_css_selector

# Login
LOGIN_URL = r'https://store.steampowered.com//login/'
browser.get(LOGIN_URL)
time.sleep(3)
username_box = find_css('#input_username')
password_box = find_css('#input_password')
username_box.send_keys(USERNAME)
time.sleep(1)
password_box.send_keys(PASSWORD)
time.sleep(3)
sign_in = find_css('#login_btn_signin > button')
sign_in.click()

# Since we're using a verified account, need to have human fill out 2FA
# Currently locked to my phone
with WaitUntil(NAVIGATION_TIME):
    code_confirmation = input('Did you enter your Steam confirmation code? [y\\n]')
    if code_confirmation not in ['y', 'Y']:
        raise Exception('Well why didn\'t you??')

itemno = 0
PAGE_DIRECTION = [-1, 1][INITIAL_PAGE < FINAL_PAGE]
#  ^^ Automatically sets page traversal page_direction
for pageno in range(INITIAL_PAGE, FINAL_PAGE + PAGE_DIRECTION, PAGE_DIRECTION):
    # These pages are like this one:
    # https://steamcommunity.com/market/search?q=navaja+knife
    print('----------Page Number: ' + str(pageno) + ' ----------')
    search_url = GENERAL_URL + str(pageno) + '_price_desc'

    browser.get(search_url)
    time.sleep(NAVIGATION_TIME)

    obtained_data = [] # Page info to be written to file
    for searchpage in range(10):
        name_element = find_css('#result_' + str(searchpage) + '_name')
        name = name_element.text
        itemno += 1
        if name not in ignore_names: # ie not seen before
            with WaitUntil(NAVIGATION_TIME):
                name_element.click()
                browser.implicitly_wait(15) # Make sure everything loads in
                try:
                    full_listing = find_css('#searchResultsRows').text
                except NoSuchElementException:
                    browser.refresh()
                    time.sleep(NAVIGATION_TIME*2)
                    full_listing = find_css('#searchResultsRows').text
                itemized = cleanListing(full_listing, name)
                buy_rate = readUSD(find_css('#market_commodity_buyrequests > '
                                            'span:nth-child(2)').text)
                # ^^ Highest buy order currently on the market.
                # If a price drops below this, it will immediately be purchased by the buy orderer.

                # Grab volumetric data for recent sales/prices (from chart).
                volumetrics = find_css('body > div.responsive_page_frame.with_header >'
                                       'div.responsive_page_content >'
                                       'div.responsive_page_template_content')
                recent_data = cleanVolumetric(volumetrics.get_attribute('outerHTML'))

                item_split = name.split(' ')
                pagedata = {
                    'Item Name': name,
                    'URL': browser.current_url,
                    'Special Type': ['None', 'Souvenir'][item_split[0] == 'Souvenir'],
                    'Condition': ' '.join(item_split[-2:]),
                        # TODO: This fails for anything b4 the implementation of item conditions ex:
                        # https://steamcommunity.com/market/listings/730/%E2%98%85%20Navaja%20Knife
                    'Sales/Day': round(len(recent_data)/30, 2),
                    'Buy Rate': buy_rate,
                    'Date': datetime.now(),
                    'Sales from last month': recent_data,
                    'Listings': itemized
                }
                
                print('    ' + str(itemno) + '.', name, 'lowest_price=' + str(itemized[0]), 
                      'sales/day=' + str(pagedata["Sales/Day"]))

                obtained_data.append(pagedata)
                ignore_names.add(pagedata['Item Name'])
            with WaitUntil(NAVIGATION_TIME):
                browser.get(search_url)
        else:
            print('    ' + str(itemno) + '.', 'Skipped because seen before!')
    
    # Rewrite file at the end of every page (so every (NAVIGATION_TIME*10) seconds at most)
    DBchange(obtained_data,'add','pagedata.txt')

    print()

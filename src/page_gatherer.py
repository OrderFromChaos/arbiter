#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

"""
PURPOSE:
    This program gathers URLs for steam items,  as well as relevant page information for that item.
    The idea is to later stick it into price_scanner.py for actual arbitrage search.
USAGE:
    python3 page_gatherer INITIAL_PAGE FINAL_PAGE USERNAME PASSWORD
    
    or, interactively,

    ipython3 -i pagegatherer INITIAL_PAGE FINAL_PAGE USERNAME PASSWORD
"""


from datetime import datetime, timedelta    # Volumetric sale filtering based on date
from selenium import webdriver              # Primary navigation of Steam price data.
from selenium.common.exceptions import NoSuchElementException # Dealing with page load failure.
from urllib.parse import urlencode
from utility_funcs import DBchange          # Add items to database safely
from utility_funcs import import_json_lines # Importing logged dataset

import calendar
import json                                 # Writing and reading logged dataset
import numpy as np
import os
import pandas as pd
import pandas.io.json as pdjson
import random
import requests
import sys                                  # Input pages from command line
import time                                 # Waiting so no server-side ban

### Hyperparameters {
condition_dict = {
    'Factory New': 0,
    'Minimal Wear': 1,
    'Field-Tested': 2,
    'Well-Worn': 3,
    'Battle-Scarred': 4}
condition = condition_dict['Factory New']

# Testing 440, which is the Application ID of Team Fortress 2.
appid = 440
general_params = {
    'q': '',
    'category_' + str(appid) + '_ItemSet[]': 'any',
    'category_' + str(appid) + '_ProPlayer[]': 'any',
    'category_' + str(appid) + '_StickerCapsule[]': 'any',
    'category_' + str(appid) + '_TournamentTeam[]': 'any',
    'category_' + str(appid) + '_Weapon[]': 'any',
#    'category_' + str(appid) + '_Exterior[]': 'tag_WearCategory' + str(condition),
    'appid': str(appid)}


GENERAL_URL = 'https://steamcommunity.com/market/search?' + urlencode(general_params)

INITIAL_PAGE    = int(sys.argv[1])
FINAL_PAGE      = int(sys.argv[2])      # Inclusive
NAVIGATION_TIME = 6                     # Global wait time between page loads
USERNAME        = sys.argv[3] #'datafarmer001'
PASSWORD        = sys.argv[4] #'u9hqgi3sl9'
### }

# ---------------------------------====Data Cleaning Functions====---------------------------------
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def readUSD(dollars):
    numbers = set('0123456789.')
    return float(''.join([x for x in dollars if x in numbers]))

def cleanListing(mess, itemname):
    """
    Sometimes Steam will dynamically show "Sold!" or the like when it
    sells at item. This function prevents the reader from stumbling. 
    """
    
    mess = mess.split('\n')
    # Does this instead of a spacing-based system because 'Sold!'
    # changes the spacing. 
    disallowed = {'PRICE', 'SELLER', 'NAME', 'Sold!', 'Buy Now', 
                  'Counter-Strike: Global Offensive', itemname}
    return sorted([readUSD(x) for x in mess if x not in disallowed])

def cleanVolumetric(data):
    """
    Parses data from the price chart on an item listing.
    """
    
    data = data[data.find('var line1')+10:data.find(']];')+2] # Gets all price data from chart
    if data == '': # No last month sales
        return []
    better_data = eval(data) # JS has the same format lists as Python, so eval is fine
    # Cuts date info into easily accessible bits
    better_data = [[x[0][:3], x[0][4:6], x[0][7:11], x[0][12:14], x[1]] for x in better_data] 
    month_lookup = {mo: n for (n, mo) in enumerate(calendar.month_abbr) if n > 0} 
    better_data = [[datetime(year=int(x[2]), month=month_lookup[x[0]],
                    day=int(x[1]), hour=int(x[3])), x[4]]
                    for x in better_data]

    # Cuts data to recent data (within last 30 days of sales)
    last_month = datetime.now() - timedelta(days=30)
    now = datetime.now()
    last_month_data = [x for x in better_data if last_month < x[0] < now]
    
    return last_month_data

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# -----------------------------------===============================-------------------------------

# Enforces that everything inside a "with WaitUntil(10):" block waits 10
# seconds to complete (waits at end if not timed out yet)
# For more info, see
# https://jeffknupp.com/blog/2016/03/07/python-with-context-managers/ 
class WaitUntil():
    def __init__(self, lengthWait):
        self.start = 0
        self.lengthWait = lengthWait
    def __enter__(self):
        self.start = time.time()
        return self.start
    def __exit__(self, *args):
        elapsed = time.time() - self.start
        if elapsed < self.lengthWait:
            time.sleep(self.lengthWait-elapsed)

# Import old found items, ignore any with the same name. We're looking
# for new items only.

# TODO: This needs to be changed to reflect switch to pandas
DBdata = import_json_lines('../data/pagedata.txt', encoding='utf_8')
ignore_names = set([x['Item Name'] for x in DBdata])

# Assume chromedriver is in /usr/bin or one of the $PATH directories.
browser = webdriver.Chrome() 
# browser = webdriver.Chrome('/home/order/Videos/chromedriver/chromedriver') # Linux
find_css = browser.find_element_by_css_selector

# Login
LOGIN_URL = 'https://store.steampowered.com/login/'
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
    code_confirmation = input('Did you enter your Steam confirmation code? [y/n]')
    if code_confirmation not in ['y', 'Y']:
        raise Exception("Well why didn't you??")

item_no = 0
# Automatically set page traversal page_direction.
PAGE_DIRECTION = 1 if INITIAL_PAGE < FINAL_PAGE else -1

testing_list = []
item_info_df = pd.DataFrame()


# The code below which is commented out was an attempt to make the
# append to the DataFrame directly rather than make a list of 10 dicts
# and run pandas.io.json.json_noramlize. I'm still not sure if this is
# really that much more efficient...
#
# for page_no in range(INITIAL_PAGE, FINAL_PAGE + PAGE_DIRECTION, PAGE_DIRECTION):
#     print('----------Page Number: ' + str(page_no) + ' ----------')
#     search_url = GENERAL_URL + '#p' + str(page_no) + '_price_desc'

#     browser.get(search_url)
#     time.sleep(NAVIGATION_TIME)
#     for search_page in range(10):
#         name_element = find_css('#result_' + str(search_page) + '_name')
#         name = name_element.text
#         item_no += 1
#         if name not in ignore_names: # ie not seen before
#             with WaitUntil(NAVIGATION_TIME):
#                 name_element.click()
#                 browser.implicitly_wait(15) # Make sure everything loads in
#                 try:
#                     full_listing = find_css('#searchResultsRows').text
#                 except NoSuchElementException:
#                     browser.refresh()
#                     time.sleep(NAVIGATION_TIME*2)
#                     full_listing = find_css('#searchResultsRows').text
#                 itemized = cleanListing(full_listing, name)
#                 try:
#                     buy_rate = readUSD(find_css('#market_commodity_buyrequests > '
#                                                     'span:nth-child(2)').text)
#                     # ^^ Highest buy order currently on the market. 
#                     # If a price drops below this, it will immediately be purchased by the buy
#                     # orderer. 
#                 except NoSuchElementException:
#                     buy_rate = 0 # Sometimes there are no buy orders

#                 # Grab volumetric data for recent sales/prices (from chart).
#                 volumetrics = find_css('body > div.responsive_page_frame.with_header >'
#                                        'div.responsive_page_content >'
#                                        'div.responsive_page_template_content')
#                 recent_data = cleanVolumetric(volumetrics.get_attribute('outerHTML'))

#                 item_split = name.split(' ')
#                 new_row = pd.DataFrame(
#                     {'Item Name': name,
#                     'URL': browser.current_url,
#                     'Special Type': ['None', 'Souvenir'][item_split[0] == 'Souvenir'],
#                     'Condition': ' '.join(item_split[-2:]),
#                         # TODO: This fails for anything b4 the implementation of item conditions ex:
#                         # https://steamcommunity.com/market/listings/730/%E2%98%85%20Navaja%20Knife
#                      'Sales/Day': round(len(recent_data)/30, 2),
#                     'Buy Rate': buy_rate,
#                     'Date': datetime.now(),
#                     'Sales from last month': recent_data,
#                     'Listings': itemized})


                

for page_no in range(INITIAL_PAGE, FINAL_PAGE + PAGE_DIRECTION, PAGE_DIRECTION):
    # These pages are like this one:
    # https://steamcommunity.com/market/search?q=navaja+knife
    print('----------Page Number: ' + str(page_no) + ' ----------')
    search_url = GENERAL_URL + '#p' + str(page_no) + '_price_desc'

    browser.get(search_url)
    time.sleep(NAVIGATION_TIME)

    obtained_data = [] # Page info to be written to file
    for search_page in range(10):
        name_element = find_css('#result_' + str(search_page) + '_name')
        name = name_element.text
        item_no += 1
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
                try:
                    buy_rate = readUSD(find_css('#market_commodity_buyrequests > '
                                                    'span:nth-child(2)').text)
                    # ^^ Highest buy order currently on the market. 
                    # If a price drops below this, it will immediately be purchased by the buy
                    # orderer. 
                except NoSuchElementException:
                    buy_rate = 0 # Sometimes there are no buy orders

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
                if len(itemized) > 0: # Nonzero
                    print('    ' + str(item_no) + '.', name, 'lowest_price=' + str(itemized[0]), 
                        'sales/day=' + str(pagedata["Sales/Day"]))
                else:
                    print('    ' + str(item_no) + '.', name, 'lowest_price=EMPTY', 
                        'sales/day=' + str(pagedata["Sales/Day"]))

                obtained_data.append(pagedata)
                ignore_names.add(pagedata['Item Name'])
            with WaitUntil(NAVIGATION_TIME):
                browser.get(search_url)
        else:
            print('    ' + str(item_no) + '.', 'Skipped because seen before!')

    item_info_df = item_info_df.append(pdjson.json_normalize(obtained_data))
    
    # Rewrite file at the end of every page (so every (NAVIGATION_TIME*10) seconds at most)
    # DBchange(obtained_data,'add','../data/pagedata.txt')

    print()

item_info_df.index = np.arange(len(item_info_df))

# Write to HDF5
item_info_df.to_hdf('../data/item_info.h5', 'testing_tf2')


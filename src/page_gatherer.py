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


### External Libraries
from selenium import webdriver              # Primary navigation of Steam price data.
from selenium.common.exceptions import NoSuchElementException 
                                            # ^^ Dealing with page load failure.
import pandas as pd                         # Primary dataset format

### Standard libraries
import time                                 # Waiting so no server-side ban
import sys                                  # Input pages from command line
from urllib.parse import urlencode          # Generalized URL search for different games

### Local Functions
from analysis import LessThanThirdQuartileHistorical 
                                            # Notify of buy-worthy things while running
from browse_itempage import browseItempage  # Scrapes data from Steam item pages
from browse_itempage import WaitUntil       # Implements standard page waits in with block
from browse_itempage import steamLogin      # Make code more readable


### Hyperparameters {
condition_dict = {
    'Factory New': 0,
    'Minimal Wear': 1,
    'Field-Tested': 2,
    'Well-Worn': 3,
    'Battle-Scarred': 4}
condition = condition_dict['Factory New']


# Testing 440, which is the Application ID of Team Fortress 2.
# 730 = CSGO
appid = 730
general_params = {
    'q': '',
    'category_' + str(appid) + '_ItemSet[]': 'any',
    'category_' + str(appid) + '_ProPlayer[]': 'any',
    'category_' + str(appid) + '_StickerCapsule[]': 'any',
    'category_' + str(appid) + '_TournamentTeam[]': 'any',
    'category_' + str(appid) + '_Weapon[]': 'any',
    'category_' + str(appid) + '_Exterior[]': 'tag_WearCategory' + str(condition),
    'appid': str(appid)
}

GENERAL_URL = 'https://steamcommunity.com/market/search?' + urlencode(general_params)

INITIAL_PAGE    = int(sys.argv[1])
FINAL_PAGE      = int(sys.argv[2])      # Inclusive
NAVIGATION_TIME = 2                     # Global wait time between page loads
USERNAME        = sys.argv[3] #'datafarmer001'
PASSWORD        = sys.argv[4] #'u9hqgi3sl9'
### }

DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
ignore_names = set(DBdata['Item Name'])

# Assume chromedriver is in /usr/bin or one of the $PATH directories.
# browser = webdriver.Chrome() 
browser = webdriver.Chrome('/home/order/Videos/chromedriver/chromedriver') # Linux
find_css = browser.find_element_by_css_selector

browser = steamLogin(browser, USERNAME, PASSWORD, NAVIGATION_TIME)

itemno = 0
# Automatically set page traversal page_direction.
PAGE_DIRECTION = 1 if INITIAL_PAGE < FINAL_PAGE else -1         

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
        itemno += 1
        if name not in ignore_names: # ie not seen before
            with WaitUntil(NAVIGATION_TIME):
                name_element.click()
                temp_item = {
                    'Item Name': name
                }
                
                browser, pagedata = browseItempage(browser, temp_item, firstscan=True)

                if len(pagedata['Listings']) > 0: # Nonzero
                    print('    ' + str(itemno) + '.', name, 'lowest_price=' + 
                          str(pagedata['Listings'][0]), 'sales/day=' + str(pagedata["Sales/Day"]))
                else:
                    print('    ' + str(itemno) + '.', name, 'lowest_price=EMPTY', 
                        'sales/day=' + str(pagedata["Sales/Day"]))

                DBdata = DBdata.append(pagedata, ignore_index=True)

                ignore_names.add(pagedata['Item Name'])
            with WaitUntil(NAVIGATION_TIME):
                browser.get(search_url)
        else:
            print('    ' + str(itemno) + '.', 'Skipped because seen before!')
    
    # Rewrite file at the end of every page (so every (NAVIGATION_TIME*10) seconds at most)
    # DBchange(obtained_data,'add','../data/pagedata.txt')
    DBdata.to_hdf('../data/item_info.h5', 'csgo', mode='w')
    print('    [WROTE TO FILE.]')

    print()

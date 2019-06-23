#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu


"""
PURPOSE:
    This program gathers URLs for steam items,  as well as relevant page information for that item.
    The idea is to later stick it into price_scanner.py for actual arbitrage search.
"""


### External Libraries

# Primary navigation of Steam price data.
from selenium import webdriver
# Dealing with page load failure.
from selenium.common.exceptions import NoSuchElementException

import pandas as pd                         # Primary dataset format

### Standard libraries
import argparse
import time                                 # Waiting so no server-side ban
import sys                                  # Input pages from command line
from urllib.parse import urlencode          # Generalized URL search for different games
from datetime import datetime

### Local Functions
from analysis import LessThanThirdQuartileHistorical
                                            # Notify of buy-worthy things while running
from browse_itempage import browseItempage  # Scrapes data from Steam item pages
from browse_itempage import WaitUntil       # Implements standard page waits in with block
from browse_itempage import steamLogin      # Make code more readable


### Hyperparameters {


### Command-line options
parser = argparse.ArgumentParser(
    description=('Gather information for items for a given Steam game. '
                 'Currently supports CS:GO, Dota 2 and Team Fortress 2'))
parser.add_argument('--appid', metavar='N', type=int, default=730,
                    help=('The Application ID for the desired game. Currently supported are:'
                          '730 for CS:GO; '
                          '570 for Dota 2; '
                          '440 for Team Fortress 2'))
parser.add_argument('--pages', metavar=('START', 'END'), type=int, nargs=2,
                    help='What range of pages to fetch (inclusive).')
parser.add_argument('--username', metavar='NAME', type=str, help='Your username')
parser.add_argument('--password', metavar='PASS', type=str, help='Your password')
parser.add_argument('--condition', metavar='N', default=0, type=int,
                    help=('Wear Condition (if applicable). Available options:\n'
                          '0 for Factory New'
                          '1 for Minimal Wear; '
                          '2 for Field-Tested; '
                          '3 for well-Worn; '
                          '4 for Battle-Scarred' ))
args = parser.parse_args()

# APPID: 730 for CS:GO, 570 for Dota 2, 440 for Team Fortress 2.
APPID        = args.appid
INITIAL_PAGE = args.pages[0]
FINAL_PAGE   = args.pages[1]
USERNAME     = args.username
PASSWORD     = args.password
CONDITION    = args.condition

NAVIGATION_TIME = 2                     # Global wait time between page loads

general_params = {
    'q': '',
    'category_' + str(APPID) + '_ItemSet[]': 'any',
    'category_' + str(APPID) + '_ProPlayer[]': 'any',
    'category_' + str(APPID) + '_StickerCapsule[]': 'any',
    'category_' + str(APPID) + '_TournamentTeam[]': 'any',
    'category_' + str(APPID) + '_Weapon[]': 'any',
    'appid': str(APPID)
}

if APPID == 730:
    general_params['category_' + str(APPID) + '_Exterior[]'] = 'tag_WearCategory' + str(CONDITION)

GENERAL_URL = 'https://steamcommunity.com/market/search?' + urlencode(general_params)
### }

DBdata = pd.read_hdf('../../data/item_info.h5', 'csgo')
ignore_names = set(DBdata['Item Name'])

# Assume chromedriver is in /usr/bin or one of the $PATH directories.
browser = webdriver.Chrome()
#browser = webdriver.Chrome('/home/order/Videos/chromedriver/chromedriver') # Linux
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
    # DBchange(obtained_data,'add','../../data/pagedata.txt')

    appid_name_dict = {
        730: 'csgo',
        570: 'dota2',
        440:' tf2'
    }

    DBdata.to_hdf('../../data/item_info.h5', appid_name_dict[APPID], mode='w')
    print('    [WROTE TO FILE.]')

    print()

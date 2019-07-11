### External Libraries
from selenium import webdriver              # Primary navigation of Steam price data.
from selenium.common.exceptions import NoSuchElementException 
                                            # ^^ Dealing with page load failure.
import pandas as pd                         # Primary dataset format

### Standard libraries
import time                                 # Waiting so no server-side ban
import json

### Local Functions
from selenium_mr.browse_itempage import browseItempage  # Scrapes data from Steam item pages
from selenium_mr.browse_itempage import WaitUntil       # Implements standard page waits in with block
from selenium_mr.browse_itempage import steamLogin      # Make code more readable
from combinedfuncs import getLoginInfo

####################################################################################################

navigation_time = 2
identity = 'Syris'

with open('missinglog.json','r') as f:
    startloc = json.load(f)['Current_missing']

with open('../data/missing.json','r') as f:
    missing = json.load(f)

DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')

base = 'https://steamcommunity.com/market/listings/730/'
browser = webdriver.Chrome()
username, password = getLoginInfo(identity)
browser = steamLogin(browser, username, password, 2)

for index, name in enumerate(missing[startloc:]):
    item_url = base + name
    with WaitUntil(navigation_time):
        browser.get(item_url)
        temp_item = {
            'Item Name': name
        }
        
        browser, pagedata = browseItempage(browser, temp_item, navigation_time, firstscan=True)

        if len(pagedata['Listings']) > 0: # Nonzero
            print('    ' + str(index) + '.', name, 'lowest_price=' + 
                    str(pagedata['Listings'][0]), 'sales/day=' + str(pagedata["Sales/Day"]))
        else:
            print('    ' + str(index) + '.', name, 'lowest_price=EMPTY', 
                'sales/day=' + str(pagedata["Sales/Day"]))

        # TODO: Expect a bug when there's no sell history; haven't accounted for this yet.

        DBdata = DBdata.append(pagedata, ignore_index=True)

    if (index+1) % 30 == 0 or index == len(missing):
        DBdata.to_hdf('../data/item_info.h5', 'csgo', mode='w')
        print('    [WROTE TO FILE.]')
        print()

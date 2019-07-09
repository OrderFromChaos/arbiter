#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### External Libraries
from selenium import webdriver              # Primary navigation of Steam price data.
from selenium.common.exceptions import NoSuchElementException 
                                            # ^^ Dealing with page load failure.
import pandas as pd                         # Primary dataset format
import json                                 # Loading passwords

### Standard libraries
import time                                 # Waiting so no server-side ban

### Local Functions
from selenium_mr.analysis import LessThanThirdQuartileHistorical 
                                            # Notify of buy-worthy things while running
from selenium_mr.analysis import filterPrint            # Pretty printing by info in dict
from selenium_mr.browse_itempage import browseItempage  # Scrapes data from Steam item pages
from selenium_mr.browse_itempage import WaitUntil       # Implements standard page waits in with block
from selenium_mr.browse_itempage import steamLogin      # Make code more readable

####################################################################################################

def getLoginInfo(identity):
    with open('../passwords.json','r') as f:
        data = json.load(f)
    return (data[identity]['Username'], data[identity]['Password'])

####################################################################################################

def selenium_search(browser, infodict):
    # ### Hyperparameters {
    # identity = 'Syris'
    # pages_to_scan = infodict['Pages']
    # navigation_time = infodict['Load Time']
    # verbose = infodict['Verbose']
    # with open('combineddata.json','r') as f:
    #     data = json.load(f)
    # current_iloc = data['current_iloc']
    # ### }

    # print('Starting selenium scanner...')

    # username, password = getLoginInfo(identity)

    # DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
    # of_interest = DBdata[DBdata['Sales/Day'] >= 1]
    # dflength = len(of_interest.index)

    # browser = webdriver.Chrome() # Linux
    # browser = steamLogin(browser, username, password, navigation_time)

    # for i in range(pages_to_scan):
    #     item = of_interest.iloc[current_iloc+i]
        
    #     # Note that itemno preserves the index from DBdata. Thus we need count for file writing
    #     # This is convenient for DBdata updates, however...
    #     browser.get(item['URL'])
    #     with WaitUntil(navigation_time):
    #         # Obtains all the page information and throws it into a dict called pagedata
    #         browser, pagedata = browseItempage(browser, item, navigation_time)

    #         newentry = pd.Series(pagedata)
    #         DBdata.iloc[current_iloc+i] = newentry

    #         if pagedata['Listings']: # Nonempty
    #             model = LessThanThirdQuartileHistorical(1.15, [2,0])
    #             printkeys = model.printkeys
    #             satdf = model.run(pd.DataFrame([newentry]))
    #             if len(satdf.index) > 0:
    #                 print('!!!!', 'Found a Q3 satisfying item')
    #                 filterPrint(satdf, keys=printkeys)
    #             if verbose:
    #                 print('    ' + str(itemno+1) + '.', item['Item Name'], pagedata['Listings'][0], pagedata["Sales/Day"])
    #         else:
    #             if verbose:
    #                 print('    ' + str(itemno+1) + '.', item['Item Name'], '[]', pagedata["Sales/Day"])

    #         DBdata.to_hdf('../data/item_info.h5', 'csgo', mode='w')
    #         print('    [SELENIUM WROTE TO FILE.]')
    ### TODO: WRITE NEW CURRENT ILOC
    time.sleep(1)
    return (browser, [])

def json_search(browser, infodict):
    time.sleep(1)
    return (browser, [])
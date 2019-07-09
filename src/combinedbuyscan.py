#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### PURPOSE:
### Alternate between doing selenium updates (high fidelity, 1 item/selenium_loadtime)
###     and json updates (low fidelity - only price, and 100 item/selenium_loadtime)
### TODO: Implement concurrency and see how it works out.

####################################################################################################

### External libraries
from selenium import webdriver                     # Web navigation
import pandas as pd                                # Dataset format

### Standard libraries
from itertools import cycle                        # Specify a pattern to repeat forever
from copy import deepcopy                          # Python object reference refers to mem locations

### Local Functions
from combinedfuncs import getLoginInfo
from combinedfuncs import selenium_search, json_search
from selenium_mr.browse_itempage import steamLogin

### Hyperparameters {
selenium_loadtime = 2 # Selenium page loadtime
json_loadtime = 4     # Json page loadtime
                      # We only need to make 16 requests for CSGO factory new, 
                      # so we don't currently hit the server-side minute cap (>=20 req/min), 
                      # but it does seem to ban lower than this speed.
identity = 'Syris'
verbose = False       # Print data about each item when scanned
# Pattern: list of dicts (each of which represent steps) to be cycled over
#     [MANDATORY] step 'Method' is assumed to be a function in the current global namespace
#     The rest are optional inputs specific to that method function
# Implementation detail: make sure the wait happens at the end of the function; this will allow
#     methods to overlap nicely.
pattern = [
    {
        'Method': 'selenium_search',
        'Pages': 20,
        'Load Time': selenium_loadtime,
        'Verbose': verbose,
        'Identity': identity
    },
    {
        'Method': 'json_search',
        'Load Time': json_loadtime,
        'Identity': identity
    }
]
### }

####################################################################################################

class PatternExecuter:
    def __init__(self, pattern):
        self.pattern = pattern
        self.step = pattern.__next__()
    def run(self, browser_obj):
        print(self.step)
        fxn = globals()[self.step['Method']]
        infodict = deepcopy(self.step)
        del infodict['Method']
        if infodict: # Nonempty
            browser_obj, buyrecs = fxn(browser_obj, infodict)
        else:
            browser_obj, buyrecs = fxn(browser_obj)
        self.step = pattern.__next__()
        return browser_obj, buyrecs

####################################################################################################

if __name__ == '__main__':
    # Import dataset, filter to high volume
    DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
    of_interest = DBdata[DBdata['Sales/Day'] >= 1]

    # Login
    browser = webdriver.Chrome()
    username, password = getLoginInfo(identity)
    browser = steamLogin(browser, username, password, selenium_loadtime)

    # Set pattern to repeat
    pattern = cycle(pattern)

    executer = PatternExecuter(pattern)
    while True:
        browser, buyrecs = executer.run(browser)
        print(buyrecs)

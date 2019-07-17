#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### PURPOSE:
### Alternate between doing selenium updates (high fidelity, 1 item/selenium_loadtime)
###     and json updates (low fidelity - only price, and 100 item/selenium_loadtime)
### TODO: Implement concurrency and see how it works out.

####################################################################################################

### External libraries
from selenium import webdriver              # Web navigation
import pandas as pd                         # Dataset format
from sty import fg                          # Color printing

### Standard libraries
from itertools import cycle                 # Specify a pattern to repeat forever
from copy import deepcopy                   # Python object reference refers to mem locations
import warnings                             # Our data storage method produces a PerformanceWarning

### Local Functions
from combinedfuncs import getLoginInfo
from combinedfuncs import selenium_search, json_search
from selenium_mr.browse_itempage import steamLogin
from selenium_mr.analysis import filterPrint

### Hyperparameters {
selenium_loadtime = 3 # Selenium page loadtime
json_loadtime = 10.19 # Json page loadtime
                      # We only need to make 16 requests for CSGO factory new, 
                      # so we don't currently hit the server-side minute cap (>=20 req/min), 
                      # but it does seem to ban lower than this speed.
identity = 'Syris'
verbose = True       # Print data about each item when scanned
# Pattern: list of dicts (each of which represent steps) to be cycled over
#     [MANDATORY] step 'Method' is assumed to be a function in the current global namespace
#     The rest are optional inputs specific to that method function
# Implementation detail: make sure the wait happens at the end of the function; this will allow
#     methods to overlap nicely.
pattern = [
    # {
    #     'Method': 'selenium_search',
    #     'Pages': 40,
    #     'Load Time': selenium_loadtime,
    #     'Verbose': verbose
    # }
    {
        'Method': 'json_search',
        'Load Time': json_loadtime,
        'Verbose': verbose,
        'LTTQH Percent': 1.05 # Might as well log everything theoretically profitable and filter in post
    }
]
### }

warnings.simplefilter('ignore') # Not best practice, but wasn't sure how to make this more specific

####################################################################################################

class PatternExecuter:
    def __init__(self, pattern, DBdata):
        self.pattern = pattern
        self.step = pattern.__next__()
        self.DBdata = DBdata
    def run(self, browser_obj):
        print(self.step)
        fxn = globals()[self.step['Method']]
        infodict = deepcopy(self.step)
        del infodict['Method']
        if infodict: # Nonempty
            browser_obj, self.DBdata = fxn(browser_obj, self.DBdata, infodict)
        else:
            browser_obj, self.DBdata = fxn(browser_obj, self.DBdata)
        self.step = pattern.__next__()
        return browser_obj

####################################################################################################

if __name__ == '__main__':
    # Import dataset, filter to high volume
    DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
    DBdata = DBdata[DBdata['Sales/Day'] >= 1]

    # Login
    browser = webdriver.Chrome()
    username, password = getLoginInfo(identity)
    browser = steamLogin(browser, username, password, selenium_loadtime)

    # Set pattern to repeat
    pattern = cycle(pattern)

    executer = PatternExecuter(pattern, DBdata)
    total_found = 0
    while True:
        browser = executer.run(browser)

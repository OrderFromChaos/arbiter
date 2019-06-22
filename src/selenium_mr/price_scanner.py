#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### PURPOSE:
### This code scans over already found URLs for arbitrage opportunities.


### External Libraries
from selenium import webdriver              # Primary navigation of Steam price data.
from selenium.common.exceptions import NoSuchElementException 
                                            # ^^ Dealing with page load failure.
import pandas as pd                         # Primary dataset format

### Standard libraries
import time                                 # Waiting so no server-side ban

### Local Functions
from analysis import LessThanThirdQuartileHistorical 
                                            # Notify of buy-worthy things while running
from analysis import SpringSearch           # Filter by items with highest LTTQH promise
from analysis import filterPrint            # Pretty printing by info in dict
from browse_itempage import browseItempage  # Scrapes data from Steam item pages
from browse_itempage import WaitUntil       # Implements standard page waits in with block
from browse_itempage import steamLogin      # Make code more readable


### Hyperparameters {
navigation_time = 2 # Global wait time between page loads
username = 'datafarmer001'
password = 'u9hqgi3sl9'
nloops = 12
verbose = False # Print data about each item when scanned
springscan = False
### }


if __name__ == '__main__':
    DBdata = pd.read_hdf('../../data/item_info.h5', 'csgo')
    of_interest = DBdata[DBdata['Sales/Day'] >= 1]
    if springscan:
        of_interest = SpringSearch(1.15).run(of_interest)
        print('Filtered to', len(of_interest.index), 'SpringSearch satisfying items')

    browser = webdriver.Chrome() # Linux
    browser = steamLogin(browser, username, password, navigation_time)

    count = 0
    for iterator in range(nloops):
        for itemno, item in of_interest.iterrows():
            # Note that itemno preserves the index from DBdata. Thus we need count for file writing
            # This is convenient for DBdata updates, however...
            browser.get(item['URL'])
            with WaitUntil(navigation_time):
                # Obtains all the page information and throws it into a dict called pagedata
                browser, pagedata = browseItempage(browser, item)

                # Itemno preserves the original DBdata index!
                newentry = pd.Series(pagedata)
                DBdata.loc[itemno] = newentry

                if pagedata['Listings']: # Nonempty
                    model = LessThanThirdQuartileHistorical(1.15)
                    printkeys = model.printkeys
                    satdf = model.run(pd.DataFrame([newentry]))
                    if len(satdf.index) > 0:
                        print('!!!!', 'Found a Q3 satisfying item')
                        filterPrint(satdf, keys=printkeys)
                    if verbose:
                        print('    ' + str(itemno+1) + '.', item['Item Name'], pagedata['Listings'][0], pagedata["Sales/Day"])
                else:
                    if verbose:
                        print('    ' + str(itemno+1) + '.', item['Item Name'], '[]', pagedata["Sales/Day"])

                # Update pagedata file every 10 items
                count += 1
                if (count + 1)%10 == 0:
                    DBdata.to_hdf('../../data/item_info.h5', 'csgo', mode='w')
                    print('    [WROTE TO FILE.]')
                    print()
        print('New loop.')

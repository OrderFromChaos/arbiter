#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### External Libraries
from selenium import webdriver              # Primary navigation of Steam price data.
from selenium.common.exceptions import NoSuchElementException 
                                            # ^^ Dealing with page load failure.
import pandas as pd                         # Primary dataset format
from sty import fg                          # Convenient cross-platform color printing

### Standard libraries
import time                                 # Waiting so no server-side ban
import json                                 # Metadata read/write

### Local Functions
from selenium_mr.analysis import filterPrint            # Pretty printing by info in dict
from selenium_mr.analysis import historicalDateFilter   # Filter before doing quartiles
from selenium_mr.analysis import volumeFilter           # Ensure quartileHistorical runs without bugs
from selenium_mr.analysis import quartileHistorical     # Buy checks in json_search
from selenium_mr.analysis import LessThanThirdQuartileHistorical # Alerts during selenium_search
from selenium_mr.browse_itempage import browseItempage  # Scrapes data from Steam item pages
from selenium_mr.browse_itempage import WaitUntil       # Implements standard page waits in with block

####################################################################################################

def getLoginInfo(identity):
    with open('../passwords.json','r') as f:
        data = json.load(f)
    return (data[identity]['Username'], data[identity]['Password'])

####################################################################################################

def selenium_search(browser, infodict):
    ### Hyperparameters {
    pages_to_scan = infodict['Pages']
    navigation_time = infodict['Load Time']
    verbose = infodict['Verbose']
    with open('combineddata.json','r') as f:
        metadata = json.load(f)
    current_iloc = metadata['current_iloc']
    ### }

    DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
    of_interest = DBdata[DBdata['Sales/Day'] >= 1]
    dflength = len(of_interest.index)

    for i in range(pages_to_scan):
        item = of_interest.iloc[current_iloc]
        DBdata_index = of_interest.index[current_iloc]
        
        browser.get(item['URL'])
        with WaitUntil(navigation_time):
            # Obtains all the page information and throws it into a dict called pagedata
            browser, pagedata = browseItempage(browser, item, navigation_time)

            newentry = pd.Series(pagedata)
            DBdata.loc[DBdata_index] = newentry

            if pagedata['Listings']: # Nonempty
                model = LessThanThirdQuartileHistorical(1.15, [2,0])
                printkeys = model.printkeys
                satdf = model.run(pd.DataFrame([newentry]))
                if len(satdf.index) > 0:
                    print(fg.li_green + '!!!! Found a Q3 satisfying item' + fg.rs)
                    filterPrint(satdf, keys=printkeys, color=fg.li_green)
                if verbose:
                    print('    ' + str(DBdata.index[DBdata_index]+1) + '.', item['Item Name'], pagedata['Listings'][0], pagedata["Sales/Day"])
            else:
                if verbose:
                    print('    ' + str(DBdata.index[DBdata_index]+1) + '.', item['Item Name'], '[]', pagedata["Sales/Day"])
            current_iloc += 1
            if current_iloc >= dflength:
                print('Index reset!')
                current_iloc = 0

    DBdata.to_hdf('../data/item_info.h5', 'csgo', mode='w')
    if verbose:
        print('    [SELENIUM WROTE TO FILE.]')
    new_combined_data = metadata
    new_combined_data['current_iloc'] = current_iloc
    with open('combineddata.json', 'w') as f:
        json.dump(new_combined_data, f, indent=4)
    
    return (browser, [])

def json_search(browser, infodict):
    ###########################
    ### STEP 1: GATHER DATA ###
    ###########################

    ### Hyperparameters {
    navigation_time = infodict['Load Time']
    verbose = infodict['Verbose']
    with open('combineddata.json','r') as f:
        metadata = json.load(f)
    ### }
        
    conditions = [0, # Factory New
                1, # Minimal Wear
                2, # Field-Tested
                3, # Well-Worn
                4] # Battle-Scarred

    fullres = []
    for i in conditions:
        if verbose:
            print(fg.li_cyan + 'Starting condition ' + str(i) + fg.rs)
        allquery = ('https://steamcommunity.com/market/search/render/?category_730_ItemSet&'
                    'appid=730&norender=1&category_730_Exterior%5B%5D=tag_WearCategory' + str(i) +
                    '&count=100&start=')

        firstrun = True
        all_items_reached = False
        currloc = 0
        results = []
        find_xpath = browser.find_element_by_xpath
        while not all_items_reached:
            with WaitUntil(navigation_time):
                # Get json response using selenium (requests seemed to be more prone to breaking)
                try:
                    browser.get(allquery + str(currloc))
                    text = find_xpath('//body').text
                    response = json.loads(text)
                except json.decoder.JSONDecodeError:
                    print('502 Bad Gateway, waiting longer')
                    time.sleep(navigation_time*5)
                    browser.get(allquery + str(currloc))
                    text = find_xpath('//body').text
                    response = json.loads(text)
                try:
                    success = response['success']
                except TypeError:
                    print('Uh oh, null result. Reduce navigation_time. TODO: Implement a 5.05 minute cooldown here.')
                    raise Exception
                
                if verbose:
                    print(fg(245) + 'Got json at: ' + str(currloc) + fg.rs)
                results += response['results']

                # If first run, get total number of expected items
                if firstrun:
                    size = response['total_count']
                    firstrun = False
                
                # Loop breaking logic based on expected item count
                currloc += 100
                if currloc > size:
                    break

        for i, item in enumerate(results):
            results[i] = {'name': item['name'],
                          'sell_price': item['sell_price'],
                          'sell_listings': item['sell_listings']}
        fullres += results

    JSONdata = pd.DataFrame(fullres)

    # For logging; next step uses the 'data' variable
    JSONdata.to_hdf('../data/global_pricing.h5', 'csgo', mode='w')

    ############################################
    ### STEP 2: SEARCH FOR BUY OPPORTUNITIES ###
    ############################################

    DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
    # Filter to DBdata item names that are in JSONdata
   new_price_dict = {row['name']:row['sell_price'] for i, row in JSONdata.iterrows()}
    DBdata = DBdata[DBdata['Item Name'].isin(new_price_dict)]
    def convertListings(row):
        row['Listings'] = (round(new_price_dict[row['Item Name']]/100,2),)
        return row

    DBdata = DBdata.apply(convertListings, axis=1)

    satdf = LessThanThirdQuartileHistorical(1.15, [2,0]).run(DBdata)
    if len(satdf.index) > 0:
        final_results = satdf
        final_results.sort_values('Ratio', ascending=False)
    else:
        final_results = []

    return (browser, final_results)
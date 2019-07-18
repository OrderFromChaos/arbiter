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
from datetime import datetime               # Used for printing an error message and logging hash overlap
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

def getMetadata(filename):
    with open(filename,'r') as f:
        metadata = json.load(f)
    return metadata

def updateMetaData(filename, update_dict):
    # Assume metadata file isn't too big, so just do file I/O instead of taking metadata as a param
    metadata = getMetadata(filename)
    for key in update_dict:
        metadata[key] = update_dict[key]
    with open(filename, 'w') as f:
        json.dump(metadata, f, indent=4)

def writeMatch(filename, append_df):
    # matches = pd.read_hdf(filename, 'csgo')
    # matches = matches.append(append_df, ignore_index = True)
    matches = append_df
    matches.to_hdf(filename, 'csgo', mode='w')

####################################################################################################

def selenium_search(browser, DBdata, curr_queue, infodict):
    ### Hyperparameters {
    pages_to_scan = infodict['Pages']
    navigation_time = infodict['Load Time']
    verbose = infodict['Verbose']

    metadata = getMetadata('combineddata.json')
    current_iloc = metadata['selenium_iloc']
    item_base_url = 'https://steamcommunity.com/market/listings/730/'
    ### }

    dflength = len(of_interest.index)

    for i in range(pages_to_scan):
        item = of_interest.iloc[current_iloc]
        DBdata_index = of_interest.index[current_iloc]
        
        browser.get(item_base_url + item['Item Name'])
        with WaitUntil(navigation_time):
            # Obtains all the page information and throws it into a dict called pagedata
            browser, pagedata = browseItempage(browser, item, navigation_time)

            newentry = pd.Series(pagedata)
            DBdata.loc[DBdata_index] = newentry

            if pagedata['Listings']: # Nonempty
                # TODO: Log this in a different way
                # model = LessThanThirdQuartileHistorical(1.30, [8,0])
                # printkeys = model.printkeys
                # satdf = model.run(pd.DataFrame([newentry]))
                # if len(satdf.index) > 0:
                #     print(fg.li_green + '!!!! Found a Q3 satisfying item' + fg.rs)
                #     filterPrint(satdf, keys=printkeys, color=fg.li_green)
                if verbose:
                    print('    ' + str(DBdata_index+1) + '.', item['Item Name'], pagedata['Listings'][0], pagedata["Sales/Day"])
            else:
                if verbose:
                    print('    ' + str(DBdata_index+1) + '.', item['Item Name'], '[]', pagedata["Sales/Day"])
            current_iloc += 1
            if current_iloc >= dflength:
                print('Index reset!')
                current_iloc = 0

    DBdata.to_hdf('../data/item_info.h5', 'csgo', mode='w')
    if verbose:
        print('    [SELENIUM WROTE TO FILE.]')
    
    metadata_update = {
        'selenium_iloc': current_iloc
    }
    updateMetadata('combineddata.json', metadata_update)
    
    return (browser, DBdata, curr_queue)

def json_search(browser, DBdata, curr_queue, infodict):

    ### Hyperparameters {
    navigation_time = infodict['Load Time']
    verbose = infodict['Verbose']
    LTTQH_percent = infodict['LTTQH Percent']

    metadata = getMetadata('combineddata.json')
    condition = metadata['json_condition']
    ### }

    conditions = [0, # Factory New
                  1, # Minimal Wear
                  2, # Field-Tested
                  3, # Well-Worn
                  4] # Battle-Scarred

    price_query_url = ('https://steamcommunity.com/market/search/render/?category_730_ItemSet&'
                       'appid=730&norender=1&category_730_Exterior%5B%5D=tag_WearCategory' + str(condition) +
                       '&count=100&start=') # Can't put count higher, unfortunately

    find_xpath = browser.find_element_by_xpath

    try:
        browser.get(price_query_url + '0')
        text = find_xpath('//body').text
        response = json.loads(text)
    except json.decoder.JSONDecodeError:
        # TODO: Implement exponential backoff here
        print('502 Bad Gateway, waiting longer')
        time.sleep(navigation_time*5)
        browser.get(price_query_url + '0')
        text = find_xpath('//body').text
        response = json.loads(text)
    
    with WaitUntil(navigation_time):
        try:
            success = response['success']
        except TypeError:
            print('Uh oh, null result. Increase navigation_time. Server cooldown is roughly 5 minutes.')
            print('Waiting...')
            time.sleep(60*5)
            raise Exception('Restart program, please.')

        if verbose:
            print(fg(245), end='')
            print('    Checking out', [condition], '(first 100 method)')
            # Note that the 100 are ROUGHLY randomized. Not sure if they actually are; it seems like
            # it might be on a cycle.
            print(fg.rs, end='')
        results = response['results']
        # Cut to relevant data
        json_name_dict = dict()
        for res in results:
            json_name_dict[res['name']] = {
                'sell_price': round(res['sell_price']/100, 2),
                'sell_listings_num': res['sell_listings'] # Don't think this is needed
            }

        ############################################################################################

        filteredDBdata = DBdata[DBdata['Item Name'].isin(json_name_dict)]
        def convertListings(row):
            row['Listings'] = (json_name_dict[row['Item Name']]['sell_price'],)
            return row
        filteredDBdata = filteredDBdata.apply(convertListings, axis=1)
        satdf = LessThanThirdQuartileHistorical(LTTQH_percent, [8,0]).run(filteredDBdata)
        if len(satdf.index) > 0:
            satdf = satdf.sort_values('Ratio', ascending=False)
            print(fg.li_green, end='')
            filterPrint(satdf, printval=50, keys=['Item Name', 'Buy Rate', 'Sales/Day', 'Lowest Listing', 'Q3', 'Ratio'])
            print(fg.rs, end='')
            satdf.date = datetime.now() # Overwrite with time of match
            writeMatch('../data/LTTQHitems.h5', satdf)

        ############################################################################################

        # Update condition and condition_loc
        size = response['total_count']
        condition_num = conditions.index(condition)
        if condition_num == len(conditions) - 1:
            metadata_update = {
                'json_condition': 0
            }
        else:
            metadata_update = {
                'json_condition': conditions[condition_num+1],
            }
        updateMetaData('combineddata.json', metadata_update)
    return (browser, DBdata, curr_queue)

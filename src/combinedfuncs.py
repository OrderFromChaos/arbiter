#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### External Libraries
from selenium import webdriver              # Primary navigation of Steam price data.
from selenium.common.exceptions import NoSuchElementException 
                                            # ^^ Dealing with page load failure.
import pandas as pd                         # Primary dataset format

### Standard libraries
import time                                 # Waiting so no server-side ban
import json                                 # Metadata read/write

### Local Functions
from selenium_mr.analysis import LessThanThirdQuartileHistorical 
                                            # Notify of buy-worthy things while running
from selenium_mr.analysis import filterPrint            # Pretty printing by info in dict
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
    identity = 'Syris'
    pages_to_scan = infodict['Pages']
    navigation_time = infodict['Load Time']
    verbose = infodict['Verbose']
    with open('combineddata.json','r') as f:
        metadata = json.load(f)
    current_iloc = metadata['current_iloc']
    ### }

    print('Starting selenium scanner...')

    DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
    of_interest = DBdata[DBdata['Sales/Day'] >= 1]
    dflength = len(of_interest.index)

    for i in range(pages_to_scan):
        item = of_interest.iloc[current_iloc+i] ### BIG TODO UH-OH, BUG, ILOC OF_INTEREST != ILOC DBDATA.
                    # HAVE TO USE GIT TO GET OLD DATABASE COMMIT.
        DBdata_index = of_interest.index[current_iloc+i]
        
        browser.get(item['URL'])
        with WaitUntil(navigation_time):
            # Obtains all the page information and throws it into a dict called pagedata
            browser, pagedata = browseItempage(browser, item, navigation_time)

            newentry = pd.Series(pagedata)
            DBdata.loc[DBdata_index] = newentry

            if pagedata['Listings']: # Nonempty
                # model = LessThanThirdQuartileHistorical(1.15, [2,0])
                # printkeys = model.printkeys
                # satdf = model.run(pd.DataFrame([newentry]))
                # if len(satdf.index) > 0:
                #     print('!!!!', 'Found a Q3 satisfying item')
                #     filterPrint(satdf, keys=printkeys)
                if verbose:
                    print('    ' + str(DBdata.index[DBdata_index]+1) + '.', item['Item Name'], pagedata['Listings'][0], pagedata["Sales/Day"])
            else:
                if verbose:
                    print('    ' + str(DBdata.index[DBdata_index]+1) + '.', item['Item Name'], '[]', pagedata["Sales/Day"])

    DBdata.to_hdf('../data/item_info.h5', 'csgo', mode='w')
    print('    [SELENIUM WROTE TO FILE.]')
    new_combined_data = metadata
    new_combined_data['current_iloc'] = current_iloc + pages_to_scan
    with open('combineddata.json', 'w') as f:
        json.dump(new_combined_data, f, indent=4)
    
    return (browser, [])

def json_search(browser, infodict):
    ###########################
    ### STEP 1: GATHER DATA ### TODO TODO Check to see that it works with infodict, etc. TODO TODO
    ###########################

    # allquery = 'https://steamcommunity.com/market/search/render/?category_730_ItemSet&appid=730&norender=1&category_730_Exterior%5B%5D=tag_WearCategory0&count=100&start='

    # firstrun = True
    # all_items_reached = False
    # startloc = 0
    # results = []
    # browser = webdriver.Chrome()
    # find_xpath = browser.find_element_by_xpath
    # while not all_items_reached:
    #     # page = requests.get(allquery + str(startloc))
    #     # text = html.fromstring(page.content).xpath('text()')[0]
    #     # print(text)
    #     browser.get(allquery + str(startloc))
    #     text = find_xpath('//body').text
    #     # print(text)
    #     response = json.loads(text)
    #     # print(response)
    #     success = response['success']
    #     if success == True:
    #         print('Got json at:', startloc)
    #     else:
    #         print('Uh oh, pull failure:', success)
    #         raise Exception
    #     results += response['results']

    #     if firstrun:
    #         size = response['total_count']
    #         firstrun = False
        
    #     startloc += 100
    #     if startloc > size:
    #         break
    #     time.sleep(4)

    # for i, item in enumerate(results):
    #     results[i] = {'name': item['name'],
    #                 'sell_price': item['sell_price'],
    #                 'sell_listings': item['sell_listings']}
    # data = pd.DataFrame(results)

    # data.to_hdf('../../data/global_pricing.h5', 'csgo')

    ############################################
    ### STEP 2: SEARCH FOR BUY OPPORTUNITIES ###
    ############################################








    return (browser, [])
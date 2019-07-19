import json
from selenium import webdriver
import pandas as pd
from browse_itempage import WaitUntil       # Implements standard page waits in with block
import time                                 # Waiting so no server-side ban
from combinedfuncs import getLoginInfo
from browse_itempage import steamLogin

### Hyperparameters {
navigation_time = 7
verbose = True
identity = 'Syris'
### }

conditions = [0, # Factory New
              1, # Minimal Wear
              2, # Field-Tested
              3, # Well-Worn
              4] # Battle-Scarred

browser = webdriver.Chrome()
username, password = getLoginInfo(identity)
browser = steamLogin(browser, username, password, 2)

fullres = []
for i in conditions:
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
            browser.get(allquery + str(currloc))
            text = find_xpath('//body').text
            response = json.loads(text)
            try:
                success = response['success']
            except TypeError:
                print('Uh oh, pull failure. Try and figure out how long the cooldown is.')
                raise Exception
            
            if verbose:
                print('Got json at:', currloc)
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
        results[i] = item['name']
    fullres += results

DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
DBnames = set(DBdata['Item Name'].tolist())
missing = []
for founditem in fullres:
    if founditem not in DBnames:
        missing.append(founditem)

with open('../data/missing.json', 'w') as f:
    json.dump(missing, f, indent=4)

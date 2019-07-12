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

# ####################################################################################################

# def getLoginInfo(identity):
#     with open('../passwords.json','r') as f:
#         data = json.load(f)
#     return (data[identity]['Username'], data[identity]['Password'])

# ####################################################################################################

# ### Hyperparameters {
# identity = 'Syris'
# # pages_to_scan = infodict['Pages']
# # navigation_time = infodict['Load Time']
# # verbose = infodict['Verbose']
# ### }

# print('Starting selenium scanner...')

# username, password = getLoginInfo(identity)

# DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
# of_interest = DBdata[DBdata['Sales/Day'] >= 1]

# filterPrint(of_interest)
# print(len(of_interest.index))

JSONdata = pd.read_hdf('../data/global_pricing.h5', 'csgo')

DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
# Filter to DBdata item names that are in JSONdata
new_price_dict = {row['name']:row['sell_price'] for i, row in JSONdata.iterrows()}
DBdata = DBdata[DBdata['Item Name'].isin(new_price_dict)]
def convertListings(row):
    row['Listings'] = (round(new_price_dict[row['Item Name']]/100,2),)
    return row

DBdata = DBdata.apply(convertListings, axis=1)

satdf = LessThanThirdQuartileHistorical(1.15, [8,0]).run(DBdata)
if len(satdf.index) > 0:
    final_results = satdf.sort_values('Ratio', ascending=False)
    print(len(satdf.index))
else:
    final_results = []

filterPrint(final_results, keys=['Item Name', 'Date', 'Sales/Day', 'Lowest Listing', 'Q3', 'Ratio'])

### External Libraries
import pandas as pd                         # Primary dataset format
import json

### Standard libraries
import time                                 # Waiting so no server-side ban

###
from selenium_mr.analysis import filterPrint

####################################################################################################

def getLoginInfo(identity):
    with open('../passwords.json','r') as f:
        data = json.load(f)
    return (data[identity]['Username'], data[identity]['Password'])

####################################################################################################

### Hyperparameters {
identity = 'Syris'
# pages_to_scan = infodict['Pages']
# navigation_time = infodict['Load Time']
# verbose = infodict['Verbose']
### }

print('Starting selenium scanner...')

username, password = getLoginInfo(identity)

DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
of_interest = DBdata[DBdata['Sales/Day'] >= 1]

filterPrint(of_interest)
print(len(of_interest.index))
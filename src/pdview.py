import pandas as pd
import pickle
from selenium_mr.analysis import filterPrint
import time

class Timer():
    def __init__(self):
        self.start = 0
    def __enter__(self):
        self.start = time.time()
        return self.start
    def __exit__(self, *args):
        elapsed = time.time() - self.start
        print('Time elapsed:', elapsed)

pages_to_scan = 10

with Timer():
    DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')

# with open('../data/pickletest', 'wb') as f:
#     pickle.dump(DBdata, f)
# del DBdata

# with Timer():
#     with open('../data/pickletest', 'rb') as f:
#         DBdata = pickle.load(f)

# of_interest = DBdata[DBdata['Sales/Day'] >= 1]

# current_iloc = 0
# for i in range(pages_to_scan):
#     item = of_interest.iloc[current_iloc]
#     DBdata_index = of_interest.index[current_iloc]
#     print(item['Item Name'])
#     print(DBdata.loc[DBdata_index]['Item Name'])
#     print()
#     current_iloc += 1

# DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
# DBdata = DBdata[DBdata['Sales/Day'] >= 1]
# filterPrint(DBdata, printtype='head', printval=10, keys=['Item Name', 'Condition', 'Special Type', 'Buy Rate', 'Sales/Day'])
# print(DBdata.head(1).to_dict('records'))
# test = DBdata.head(100)
# for i, row in test.iterrows():
#     print(row)
#     print()

# print('Max index:', DBdata.index[-1])

# matches = pd.read_hdf('../data/LTTQHitems.h5', 'csgo')
# filterPrint(matches, printval=10000, keys=['Item Name', 'Buy Rate', 'Sales/Day', 'Lowest Listing', 'Q3', 'Ratio'])
# print(len(matches.index))
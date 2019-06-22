import sys
import pandas as pd
sys.path.append('..') # A little jank, but it works
from selenium_mr.analysis import quartileHistorical, standardFilter, historicalDateFilter
from selenium_mr.analysis import LessThanThirdQuartileHistorical, SpringSearch
from selenium_mr.analysis import filterPrint

jsondata = pd.read_hdf('../../data/global_pricing.h5', 'csgo')
seledata = pd.read_hdf('../../data/item_info.h5', 'csgo')
seledata = SpringSearch(1.15, numdays=7).run(seledata)

print(len(seledata.index))

# Find all elements in jsondata that exist in seledata
jsonnames = set(jsondata['name'])
jsonpos = jsondata['name'].tolist()

df = pd.DataFrame(columns=seledata.keys())
for i, x in seledata.iterrows():
    name = x['Item Name']
    if name in jsonnames:
        globprice = jsondata.iloc[jsonpos.index(name),:]['sell_price']/100
        x = x.append(pd.Series(data={'Price': globprice}))
        df = df.append([x], ignore_index = True)

print(len(df.index))

satdf = df
# satdf = standardFilter(df)
# satdf = historicalDateFilter(satdf, 15)

# details = satdf['Sales from last month'].apply(quartileHistorical)
# details = pd.DataFrame(details.tolist(), index=details.index, columns=['Q1','Q2','Q3'])
# satdf = satdf.join(details)

# filterPrint(satdf, keys=['Item Name', 'Buy Rate', 'Sales/Day', 'Price', 'Q1', 'Q2', 'Q3'])

wow = satdf[satdf['Price'] < satdf['Q1']]

filterPrint(wow, printval=200, keys=['Item Name', 'Buy Rate', 'Sales/Day', 'Price', 'Q1', 'Q2', 'Q3'])

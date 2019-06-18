import pandas as pd
import h5py
import datetime

pd.options.display.width = 0
pd.set_option('display.max_columns', 6)

with h5py.File('../data/item_info_2.h5','r') as f:
    print(list(f.keys()))

df = pd.read_hdf('../data/item_info_2.h5', 'item_info')

newitem = {
    "Item Name": "\u2605 Karambit | Blue Steel (Factory New)",
    "URL": "https://steamcommunity.com/market/listings/730/%E2%98%85%20Karambit%20%7C%20Blue%20Steel%20%28Factory%20New%29",
    "Special Type": "None",
    "Condition": "(Factory New)",
    "Sales/Day": 0.1,
    "Buy Rate": 295.34,
    "Date": datetime.datetime(2019, 6, 9, 21, 20, 40, 674902),
    "Sales from last month": [[datetime.datetime(2019, 5, 25, 0, 0), 352.32], [datetime.datetime(2019, 5, 25, 6, 0), 281.91], [datetime.datetime(2019, 6, 9, 10, 0), 294.67]],
    "Listings": [395.75, 396.58, 398.13],
    "Listing IDs": []
}

# print(df.dtypes)
# print(df[['Item Name','Condition','Sales/Day','Buy Rate']].tail(2))
# print(df.keys())
# df.iloc[1566,:] = pd.Series(newitem)
# print(df[['Item Name','Condition','Sales/Day','Buy Rate']].tail(2))
# print(list(df['Item Name']))

# for index, item in df.head(2).iterrows():
#     print(index)
#     print(item)
#     print(item['Item Name'])

# print(len(df['Item Name']))
# print(len(set(df['Item Name'])))

# df = df.append(newitem, ignore_index=True)
print(df.tail(2))
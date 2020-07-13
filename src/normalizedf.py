import pandas as pd
from analysis import filterPrint
from sty import fg

# Pulling missing items accidentally caused some weird data pulls, so this code fixes that by
# enforcing a particular style

# 1. Remove duplicates
# 2. Fix weird condition titles (from findmissing.py I think)

FIX_TUPLE_CONDITIONS = False
REMOVE_DUPLICATES = False

REMOVE_URLS = False
REMOVE_IDS = False
CONVERT_CONDITION = False
CONVERT_SPECIAL_TYPE = False
SORT_DF = True

WRITE_TO_FILE = True

print('Doing initial dataset import...')
DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')

if REMOVE_DUPLICATES:
    print('Dropping duplicates. Current size: {0}'.format(len(DBdata.index)))
    DBdata = DBdata.drop_duplicates(subset='Item Name')
    print('Duplicates dropped. Current size: {0}'.format(len(DBdata.index)))

if FIX_TUPLE_CONDITIONS:
    print('Fixing weird conditions (eg "(Stained (Battle-Scarred),)").')
    print('Num conditions: ', end='') 
    print(fg.li_red, end='')
    print(pd.unique(DBdata['Condition']).size, end='')
    print(fg.rs)
    for i, item in DBdata.iterrows():
        condition = item['Condition']
        if isinstance(condition, tuple):
            condition = str(condition)
        acceptable_cond = ['Factory New', 'Minimal Wear', 'Field-Tested', 
                        'Well-Worn', 'Battle-Scarred']
        for cond in acceptable_cond:
            find_attempt = condition.find(cond)
            if find_attempt != -1:
                DBdata.loc[i, 'Condition'] = cond
                break
    print('Item conditions fixed!')
    print('Num conditions: ', end='') 
    print(fg.li_green, end='')
    print(pd.unique(DBdata['Condition']).size, end='')
    print(fg.rs)

if REMOVE_URLS:
    print('Dropping URL column')
    DBdata = DBdata.drop('URL', axis=1)

if REMOVE_IDS:
    print('Dropping Listing IDs column')
    DBdata = DBdata.drop('Listing IDs', axis=1)

if CONVERT_CONDITION:
    print('Converting conditions to numbers')
    to_num = {
        'Factory New': 0,
        'Minimal Wear': 1,
        'Field-Tested': 2,
        'Well-Worn': 3,
        'Battle-Scarred': 4
    }
    DBdata['Condition'] = DBdata['Condition'].apply(lambda c: to_num[c])

if CONVERT_SPECIAL_TYPE:
    print('Converting special type to numbers')
    to_num = {
        'None': 0,
        'Souvenir': 1
    }
    DBdata['Special Type'] = DBdata['Special Type'].apply(lambda s: to_num[s])

if SORT_DF:
    DBdata = DBdata.sort_values('Buy Rate', ascending=False)

print(list(DBdata)) # Keys
print(DBdata['Condition'].unique())
print(DBdata['Special Type'].unique())
print(DBdata.dtypes)
filterPrint(DBdata, keys=['Item Name', 'Condition', 'Special Type', 'Buy Rate', 'Sales/Day'])

if WRITE_TO_FILE:
    DBdata.to_hdf('../data/item_info.h5', 'csgo', mode='w')
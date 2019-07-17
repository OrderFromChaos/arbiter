import pandas as pd
from selenium_mr.analysis import filterPrint
from sty import fg

# Pulling missing items accidentally caused some weird data pulls, so this code fixes that by
# enforcing a particular style

# 1. Remove duplicates
# 2. Fix weird condition titles (from findmissing.py I think)

print('Doing initial dataset import...')
DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
print('Dropping duplicates. Current size: {0}'.format(len(DBdata.index)))
DBdata = DBdata.drop_duplicates(subset='Item Name')
print('Duplicates dropped. Current size: {0}'.format(len(DBdata.index)))

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

DBdata.to_hdf('../data/item_info.h5', 'csgo', mode='w')

# Later TODO:
# 1. Purge URLs, not needed (can just shove item name into URL)
# 2. Change condition to underlying number (0,1,2,3,4)
# 3. Change special type to a number
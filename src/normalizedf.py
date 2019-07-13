import pandas as pd

# Pulling missing items accidentally caused some weird data pulls, so this code fixes that by
# enforcing a particular style

DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
for i, item in DBdata.iterrows():
    # Fix condition saying (Stained (Battle-Scarred),)
    condition = item['Condition']
    acceptable_cond = {'Factory New', 'Minimal Wear', 'Field-Tested', 'Well-Worn', 'Battle-Scarred'}
    if condition in acceptable_cond:
        pass
    else:
        # In format "(Stained (Battle-Scarred),)" (for some reason)
        new = '(' + condition.split('(')[2].split(')')[0] + ')'
    item['Condition'] = new

    
    # Convert listings to tuples only
    # Convert sales from last month to nested tuples
    # Convert listing IDs to tuples only
    # TODO: Make sure all other code uses this database style when writing
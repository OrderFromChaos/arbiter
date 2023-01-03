import pandas as pd

DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
print(sum([len(x) for x in DBdata['Sales from last month']]))
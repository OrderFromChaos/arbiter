import pandas as pd
from selenium_mr.analysis import filterPrint

df = pd.read_hdf('../data/item_info.h5', 'csgo')
filterPrint(df)

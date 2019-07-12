import pandas as pd
from selenium_mr.analysis import filterPrint

df = pd.read_hdf('../data/item_info.h5', 'csgo')
# filterPrint(df, printtype='tail', printval=100, keys=['Item Name', 'Condition', 'Buy Rate', 'Sales/Day'])
end = df.tail(10)
for i, row in end.iterrows():
    print(row)
    print()
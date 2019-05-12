import numpy as np
import matplotlib.pyplot as plt
# import seaborn as sns
from utility_funcs import Currency, import_json_lines

data = import_json_lines('buyable_simple.txt',encoding='utf_8')

names_data = [x['Item Name'] for x in data]
sales_data = [x['Sales/Day'] for x in data]
for sale, name in sorted(zip(sales_data,names_data)):
    print(sale, '(' + name + ')')
# plt.hist(np.array(sales_data), bins=np.arange(0,max(sales_data),.5))
# plt.show()
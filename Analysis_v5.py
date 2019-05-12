import json
import matplotlib.pyplot as plt
import numpy as np

with open('buyable_simple.txt','r') as f: # ,encoding='utf_16') as f:
    data = f.readlines()

search = lambda page: float(page["Sales/Day"]) >= 5

data = [json.loads(x) for x in data]
results = [x for x in data if search(x)]
print(len(results),'out of',len(data))
print('(' + str(round(len(results)/len(data)*100,1)) + '%)')

frequency = []
highest_sales = max([float(x["Sales/Day"]) for x in results])
for i in np.arange(0,highest_sales+1,0.1):
    search = lambda page: float(page["Sales/Day"]) >= i
    results = [x for x in data if search(x)]
    frequency.append(len(results)/len(data)*100)

# high_items = sorted(data,key=lambda x: x["Sales/Day"], reverse=True)
# for x in high_items[:3]:
#     print(x["Item Name"])

# plt.xlabel('Sales per day')
# plt.ylabel('Frequency in dataset (%)')
# plt.plot(np.arange(0,highest_sales+1,0.1),frequency)
# plt.show()

from utility_funcs import import_json_lines, readCurrency

data = import_json_lines('buyable_simple.txt',numlines=11)

def sma(dataset, n):
    if len(dataset) < n:
        return 'N is too high for this dataset (' + str(len(dataset)) + ' < ' + str(n) + ')'
    
    avg_list = []
    for i in range(0,len(dataset)-n):
        avg = sum(dataset[i:i+n])/n
        avg_list.append(avg)
    return avg_list

def remove_outliers(dataset,sigma):
    # Remove all data points that are greater than sigma away from the mean
    mean = sum(dataset)/len(dataset)
    stdev = (sum([(x-mean)**2 for x in dataset])/len(dataset))**0.5
    return [x for x in dataset if mean-sigma*stdev < x < mean+sigma*stdev]

newdata = []
for x in data:
    rawsales = [y[1] for y in x['Sales from last month']]
    if rawsales: # Nonzero
        sales = remove_outliers(rawsales,1)
        x['Sales from last month'] = sales
        if len(sales) > 7:
            newdata.append(x)

# data = [x for x in data if len() > 7]
names = [x['Item Name'] for x in newdata]
smallest_listing = [min(x['Listings']) for x in newdata]
buyprices = []
profit_per_item = []
for item in newdata:
    recentPrices = [x for x in item['Sales from last month'][-7:]]
    avg = sum(recentPrices)/7
    buyprices.append(round(avg/1.15,2))
    profit_per_item.append(buyprices[-1] - min(item['Listings']))

print(*sorted(zip(profit_per_item,smallest_listing,names), reverse=True))
print(sorted(smallest_listing))
from utility_funcs import import_json_lines, readCurrency
import json
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import lstsq # Linear regression by least squares

data = import_json_lines('buyable_simple.txt',numlines=11)

def sma(dataset, n):
    if len(dataset) < n:
        return 'N is too high for this dataset (' + str(len(dataset)) + ' < ' + str(n) + ')'
    
    avg_list = []
    for i in range(0,len(dataset)-n):
        avg = sum(dataset[i:i+n])/n
        avg_list.append(avg)
    return avg_list


    # avg = sum(dataset[:n])/n
    # avg_list = [avg]
    # for i in range(len(dataset)-n):
    #     avg_list.append(avg_list[-1]-dataset[i]+dataset[i+n])
    # return avg_list

def datesToDeltas(times):
    # Expected input: [datetime.datetime(2019, 5, 12, 6, 0), ...]
    # Output: 0, 2.4, ...
    day_deltas = []
    start = times[0]
    for sale in times:
        sale = sale - start
        day_deltas.append(sale.days + (sale.seconds//3600)/24)
    return day_deltas

def linearRegression(X,Y):
    X = np.array(X)
    Y = np.array(Y)
    M = X[:, np.newaxis]**[0, 1]
    p, res, rnk, s = lstsq(M, Y)
    return p

def mostRecent(X,Y, days):
    recentdata = [(x,y) for x,y in zip(X,Y) if x > 30-days]
    recentX = [x[0] for x in recentdata]
    recentY = [x[1] for x in recentdata]
    return recentX, recentY

source = data[49]
print(source)

X = source['Sales from last month']
Y = [x[1] for x in X]
X = datesToDeltas([x[0] for x in X])

Y_sma_week = sma(Y,7)

mean = sum(Y)/len(Y)
stdev = (sum([(y-mean)**2 for y in Y])/len(Y))**0.5
data_no_outliers = [(x,y) for x,y in zip(X,Y) if mean-stdev < y < mean+stdev]
X_no_outliers = [x[0] for x in data_no_outliers]
Y_no_outliers = [x[1] for x in data_no_outliers]
Y_sma_week_no_outliers = sma(Y_no_outliers,7)

p = linearRegression(X,Y)
xx = np.linspace(0,X[-1],101)
yy = p[0] + p[1]*xx

X_week, Y_week = mostRecent(X,Y,7)
p_week = linearRegression(X_week,Y_week)
xx_week = np.linspace(X_week[0],X_week[-1],101)
yy_week = p_week[0] + p_week[1]*xx_week

# plt.plot(X,Y, label='Last month\'s sale data')
plt.plot(X_no_outliers,Y_no_outliers, label='Outliers removed data')
# plt.plot(X[6:],Y_sma_week,label='SMA 7 sales (with outliers)')
plt.plot(X_no_outliers[7:],Y_sma_week_no_outliers,label='SMA 7 sales (no outliers)')
plt.plot(X[-1],mean,'o',label='Mean')
# plt.axhline(mean+stdev,c='red')
# plt.axhline(mean-stdev,c='red')
plt.plot(xx,yy,label='Linear regression (full month)')
plt.plot(xx_week,yy_week,label='Linear regression (last week)')
plt.xlabel('Days in last month')
plt.ylabel('Sale price ($USD)')
plt.ylim(2,5)
plt.title(source['Item Name'])
plt.legend(framealpha=1)

print('RECOMMENDED BUY PRICE: $' + str(round(Y_sma_week_no_outliers[-1]/1.15,2)))
plt.show()
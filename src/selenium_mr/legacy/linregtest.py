import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import lstsq # Linear regression by least squares
from datetime import datetime
from utility_funcs import readCurrency, import_json_lines

# Needs x (time) and y (sale price) data

data = import_json_lines('pagedata.txt',encoding='utf_16', keep_nontimed_salehistory=False)

raw_metadata = data[5]
raw = raw_metadata['Sales from last month']
print(raw)

startdate = raw[0][0]
X = []
Y = []
for sale in raw:
    delta = (sale[0] - startdate)
    X.append(delta.days + (delta.seconds//3600)/24)
    Y.append(float(sale[1]))

print(X)
print(Y)

X_week = []
Y_week = []
for subx,suby in zip(X,Y):
    if subx >= (30-7):
        X_week.append(subx)
        Y_week.append(suby)

if len(X_week) > 1:
    enough_data_week = True
else:
    enough_data_week = False

X = np.array(X)
Y = np.array(Y)
M = X[:, np.newaxis]**[0, 1]

if enough_data_week:
    X_week = np.array(X_week)
    Y_week = np.array(Y_week)
    M_week = X_week[:, np.newaxis]**[0, 1]

p, res, rnk, s = lstsq(M, Y)
print(p)
if enough_data_week:
    p2, res2, rnk2, s2 = lstsq(M_week,Y_week)
    print(p2)

plt.plot(X,Y,label='data')
xx = np.linspace(0,X.max(),101)
yy = p[0] + p[1]*xx
plt.plot(xx,yy,label='least squares regression (one month)')
if enough_data_week:
    xx2 = np.linspace(30-7,X.max(),101)
    yy2 = p2[0] + p2[1]*xx2
    plt.plot(xx2,yy2,label='least squares regression (one week)')
    plt.plot(xx2[-1],(yy2[-1]+yy[-1])/2,'o',label='Average of lstsq')
plt.legend(framealpha=1)
plt.show()

#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### PURPOSE:
### This program serves two purposes:
### 1. A source for buying/selling strategies to be slotted into other programs and
### 2. When run as itself, the ability to backtest strategies during development.

import pandas as pd                         # Dataset format
from datetime import datetime, timedelta    # Volumetric sale filtering based on date
from math import floor, ceil                # Data analysis use in medians

# Print settings
pd.options.display.width = 0
pd.set_option('display.max_columns', 6)

def filterPrint(df, printtype='head', printval=10, keys=['Item Name', 'Date', 'Buy Rate', 'Sales/Day']):
    if printtype == 'head':
        print(df[keys].head(printval))
    elif printtype == 'tail':
        print(df[keys].tail(printval))
    else:
        raise Exception('Unsupported print type: ' + printtype)

class Backtester:
    def __init__(self, strategy):
        self.strategy = strategy
        self.satdf = None
        self.run = False
    def runBacktest(self):
        # TODO: Update this info; no longer accurate
        # Results should be in the format:
        # [
        # {satisfied: True,    # if filter condition is satisfied
        #  name: ~itemname~,   # so it can be found later
        #  metric1: ~number~,
        #  ...},
        #  ...]
        # In other words, a dict of info about each item.
        global DBdata
        self.satdf = self.strategy.run(DBdata)
        self.run = True

def basicTest(strategy, inputs=None):
    if inputs:
        backtest = Backtester(strategy(*inputs))
    else:
        backtest = Backtester(strategy)
    backtest.runBacktest()
    satdf = backtest.satdf
    print('Number that satisfy', strategy.__name__ + ':', len(satdf.index))
    return satdf

### HELPER FUNCTIONS ###

# Numerical functions
def simpleMovingAvg(L, n):
    if len(L) < n:
        return 'N is too high for this list (' + str(len(L)) + ' < ' + str(n) + ')'
    
    avg_list = []
    for i in range(0,len(L)-n):
        avg = sum(L[i:i+n])/n
        avg_list.append(avg)
    return avg_list

def median(L):
    length = len(L)
    if length == 1:
        return L[0], 0
    L = sorted(L)
    if length % 2 == 1:
        pos = int(length/2) # int() automatically floors the result
        return L[pos], pos
    else:
        rightmid = length//2
        try:
            return (L[rightmid-1]+L[rightmid])/2, rightmid-0.5
        except:
            raise Exception('!!! ' + str(L))

def quartiles(L):
    assert len(L) >= 3, 'Quartiles are meaningless with less than 3 data points'
    L = sorted(L)

    Q2, midpoint = median(L)
    if isinstance(midpoint, int):
        Q1, Q1pos = median(L[:midpoint])
        Q3, Q3pos = median(L[midpoint+1:])
    elif isinstance(midpoint, float):
        Q1, Q1pos = median(L[:ceil(midpoint)])
        Q3, Q3pos = median(L[ceil(midpoint):])
    return (Q1,Q2,Q3)

def quartileHistorical(histL):
    return quartiles([x[1] for x in histL])

# Functions that act on an item subgroup and return a filtered list
def volumeFilter(df, saleslastmonth):
    return df[df['Sales from last month'].apply(len) >= saleslastmonth]

def listingFilter(df, amountoflistings):
    return df[df['Listings'].apply(len) >= amountoflistings]

def souvenirFilter(df):
    return df[df['Special Type'] != 'Souvenir']

def historicalDateFilter(item, ndays):
    filter_date = datetime.now() - timedelta(days=ndays)
    for i, row in DBdata.iterrows():
        historical = row['Sales from last month']
        DBdata.at[i,'Sales from last month'] = [x for x in historical if x[0] >= filter_date]
    return DBdata

def removeHistoricalOutliers(df, sigma):
    # Filter all data points that are greater than sigma away from the mean
    for i, row in DBdata.iterrows():
        historical = row['Sales from last month']
        historical_nums = [x[1] for x in historical]
        mean = sum(historical_nums)/len(historical_nums)
        stdev = (sum([(x-mean)**2 for x in historical_nums])/len(historical_nums))**0.5
        DBdata.at[i,'Sales from last month'] = [x for x in historical if x[0] >= filter_date]
    return DBdata

def profiler(dataset):
    # TODO: to be built later; used to mine frequency data from a group of items
    pass

########################


### ACTUAL STRATEGY ###

class SimpleListingProfit:
    def __init__(self, percentage):
        self.percentage = percentage # Steam % cut on Marketplace purchases for that game. 
                                     # For CS:GO, this is 15%
    def run(self, df):
        # Actual strategy
        satdf = listingFilter(df,4) # For very low listings, SLP is essentially meaningless 
        def listingRatio(L):
            L = sorted(L)
            return L[1]/L[0]
        details = pd.DataFrame(data={'Ratio': satdf['Listings'].apply(listingRatio)})
        satdf = satdf.join(details)
        satdf = satdf[satdf['Ratio'] > self.percentage + .01] # 1% margin is reasonable
        satdf['Ratio'] = satdf['Ratio'].apply(lambda x: round(x,2))

        return satdf

class LessThanThirdQuartileHistorical:
    def __init__(self, percentage):
        self.percentage = percentage # Steam % cut on Marketplace purchases for that game. 
                                     # For CS:GO, this is 15%
    
    def run(self, df):
        satdf = historicalDateFilter(df, 15)
        details = satdf['Sales from last month'].apply(quartileHistorical)
        details = pd.DataFrame(details.tolist(), index=details.index, columns=['Q1','Q2','Q3'])
        satdf = satdf.join(details)

        lowest_listings = pd.DataFrame(data={'Lowest Listing': satdf['Listings'].apply(lambda L: L[0])})
        satdf = satdf.join(lowest_listings)
        satdf = satdf[satdf['Lowest Listing'] < satdf['Q1']]
        satdf = satdf[satdf['Lowest Listing']*(self.percentage + .01) < satdf['Q3']]
        return satdf

    # TODO: Implement days to profit into models
    #     itemdict['Days To Profit'] = round(1/(item['Sales/Day']/4),2)
    #     # ^^ x/4 because 1/4th chance to appear at or above Q3
    #     itemdict['Profit'] = round(Q3-itemdict['Lowest Listing']*1.15,2)
    #     itemdict['Profit/Day'] = round(itemdict['Profit']*item['Sales/Day']/4,2)

    #     return itemdict

class SpringSearch:
    # Items whose historical data Q1 and Q3 differ by more than a given percentage
    def __init__(self, percentage):
        self.percentage = percentage # Steam % cut on Marketplace purchases for that game. 
                                     # For CS:GO, this is 15%
    
    def run(self, df):
        satdf = historicalDateFilter(df, 15)
        details = satdf['Sales from last month'].apply(quartileHistorical)
        details = pd.DataFrame(details.tolist(), index=details.index, columns=['Q1','Q2','Q3'])
        satdf = satdf.join(details)
        satdf = satdf[satdf['Q1']*(self.percentage) < satdf['Q3']]
        satdf = satdf[satdf['Q1'] > satdf['Buy Rate']]
        satdf = satdf[satdf['Q1'].apply(lambda q: q < 144.77)] # Account balance restriction
        return satdf

#######################

if __name__ == '__main__':
    print('Doing inital dataset import...')
    DBdata = pd.read_hdf('../data/item_info.h5', 'item_info')
    print('Successful import! Number of entries:', len(DBdata.index))
    DBdata = volumeFilter(DBdata, 30)
    DBdata = listingFilter(DBdata, 1)
    DBdata = souvenirFilter(DBdata) # I don't understand the pricing on these items.
    print('Number that satisfy volume, listing, and souvenir filters:', len(DBdata.index))
    print()

    # Testing SimpleListingProfit
    SLPsat = basicTest(SimpleListingProfit,inputs=[1.15])
    SLPsat = SLPsat.sort_values('Ratio', axis=0, ascending=False)
    filterPrint(SLPsat, keys=['Item Name', 'Date', 'Buy Rate', 'Sales/Day', 'Ratio'])
    print()

    # Testing LessThanThirdQuartileHistorical
    LTTQHsat = basicTest(LessThanThirdQuartileHistorical, inputs=[1.15])
    filterPrint(LTTQHsat, keys=['Item Name', 'Date', 'Buy Rate', 'Sales/Day', 'Lowest Listing', 'Q1'])
    # TODO: Implement writing to file
    # DBchange([x for x in DBdata if LessThanThirdQuartileHistorical.runindividual(x)['Satisfied']], 
    #          'add',
    #          '../data/LTTQHitems.txt')
    print()

    # # Testing SpringSearch
    SSsat = basicTest(SpringSearch, inputs=[1.15])
    filterPrint(SSsat, keys=['Item Name', 'Date', 'Buy Rate', 'Sales/Day'])
    print()

    # TODO: Implement profit guesses
    # print('Average daily profit at perfect information/liquidity:', round(sum([x['Profit/Day'] for x in SSsatresults]),2))
    # portfolio_size = 100
    # # print('Highest profit at',portfolio_size)

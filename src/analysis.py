#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### PURPOSE:
### This program serves two purposes:
### 1. A source for buying/selling strategies to be slotted into other programs and
### 2. When run as itself, the ability to backtest strategies during development.

from utility_funcs import import_json_lines # Importing logged dataset
from utility_funcs import DBchange          # Writing analysis items
from datetime import datetime, timedelta    # Volumetric sale filtering based on date
import json                                 # Writing and reading logged dataset
from math import floor, ceil                # Data analysis use in medians

class Backtester:
    def __init__(self, strategy):
        self.strategy = strategy
        self.results = []
    def runBacktest(self):
        # Results should be in the format:
        # [
        # {satisfied: True,    # if filter condition is satisfied
        #  name: ~itemname~,   # so it can be found later
        #  metric1: ~number~,
        #  ...},
        #  ...]
        # In other words, a dict of info about each item.
        global DBdata
        self.results = self.strategy.run(DBdata)
    def getSatisfied(self):
        if self.results == dict():
            self.runBacktest()
        return [x for x in self.results if x['Satisfied']]

def basicTest(strategy, inputs=None, printsat=True):
    if inputs is not None:
        backtest = Backtester(strategy(*inputs))
    else:
        backtest = Backtester(strategy)
    backtest.runBacktest()
    all_results = backtest.results
    positive_results = backtest.getSatisfied()
    print('Number that satisfy', strategy.__name__ + ':', len(positive_results))
    if printsat:
        for satdict in positive_results:
            print(satdict)
    return all_results, positive_results

### HELPER FUNCTIONS ###

# Numerical functions

def simpleMovingAvg(ser, n):
    """
    Compute a rolling average of a pandas Series, expressed as a Series.

    Keyword Arguments
    ser -- a pandas Series
    n -- the size of the window
    """

    if series.shape[0] < n:
        raise Exception('N is too high for this Series (' + str(len(L)) + ' < ' + str(n) + ')')
    return ser[ser.rolling(11).sum().notna()]

def median(ser):
    """
    Compute the median of a pandas Series.

    Keyword Arguments
    ser -- a pandas Series
    """

    return pd.median(ser)

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
    return (Q1,Q2,Q3), (Q1pos, midpoint, Q3pos)


# Functions that check whether items satisfy a condition and return a bool
def volumeFilter(df, min_sales):
    """
    Remove sales from last month from DataFrame that are less than
    min_sales
    """
    return df[df['Sales from last month'].shape[0] >= min_sales]

def listingFilter(df, min_listings):
    """
    Remove listings
    """
    return df[df['Listings'].shape[0] >= min_sales]

def removeOutliers(df, key, sigma):
    """
    Filter all data points that are greater than sigma away from the
    mean.
    """
    outlier_axis = df[key]
    mean = outlier_axis.mean()
    stdev = outlier_axis.std()
    return df[mean - sigma*stdev < df[key] < mean + sigma*stdev]


# TODO
def historicalDateFilter(df, num_days):
    for row in df:
        return
    filter_date = df['Date'] - timedelta(days=num_days)
    historical = df['Sales from last month']
    return df[[df['Sales from last month']]]

def historicalDateFilter(item, ndays):
    try:
        filter_date = item['Date'] - timedelta(days=ndays)
    except TypeError:
        raise Exception('item[\'Date\'] is a string! See here:' + str(repr(item['Date'])) + '\n' +
                        str(item))
    historical = item['Sales from last month']
    if isinstance(historical[0],list): # Fed in as standard [[datetime, price],...] format
        item['Sales from last month'] = [x for x in historical if x[0] >= filter_date]
    else:
        raise Exception('Unrecognized instance! ' + str(historical[0]))
    return item

def profiler(dataset):
    # TODO
    # to be built later; used to mine frequency data from the items that satisfy a filter
    pass

# Functions that work on a dataset
def head(dataset,n): # Similar to *nix "head -n 3 /etc/datafile"
    for i in dataset[:n]:
        print(i)

########################


### ACTUAL STRATEGY ###

class SimpleListingProfit:
    def __init__(self, percentage):
        # Steam % cut on Marketplace purchases for that game.
        # For CS:GO, this is 15%
        self.percentage = percentage
    def run(self, df):
        outputs = []
        df =
        dataset = [x for x in dataset if listingFilter(x,4)]
        for item in dataset:
            itemdict = dict()
            listings = item['Listings']
            relevant_listings = sorted(listings[:2])
            ratio = relevant_listings[1]/relevant_listings[0]

            itemdict['Satisfied'] = (ratio > self.percentage and
                                     item['Special Type'] != 'Souvenir')
            itemdict['Name'] = item['Item Name']
            itemdict['Price'] = relevant_listings[0]
            itemdict['Ratio'] = round(ratio,2)

            outputs.append(itemdict)
        return outputs

class LessThanThirdQuartileHistorical:
    def run(dataset):
        outputs = []
        for item in dataset:
            itemdict = LessThanThirdQuartileHistorical.runindividual(item)
            outputs.append(itemdict)
        return outputs
    def runindividual(item):
        # Assume already volume filtered (>30 sales last month recommended)
        itemdict = dict()
        item = historicalDateFilter(item,15)
        historical = [x[1] for x in item['Sales from last month']]

        quarts, _ = quartiles(historical)
        Q1, Q2, Q3 = quarts

        itemdict['Satisfied'] = (item['Listings'][0]*1.16 < Q3
                                 and item['Listings'][0] < Q1
                                 and item['Special Type'] != 'Souvenir')
        itemdict['Name'] = item['Item Name']
        itemdict['Quartiles'] = tuple(map(lambda x: round(x,2), (Q1,Q2,Q3)))
        itemdict['Lowest Listing'] = item['Listings'][0]
        itemdict['Days To Profit'] = round(1/(item['Sales/Day']/4),2)
        # ^^ x/4 because 1/4th chance to appear at or above Q3
        itemdict['Profit'] = round(Q3-itemdict['Lowest Listing']*1.15,2)
        itemdict['Profit/Day'] = round(itemdict['Profit']*item['Sales/Day']/4,2)

        return itemdict

class SpringSearch:
    # Items whose historical data Q1 and Q3 differ by more than 15%
    def run(dataset):
        outputs = []
        for item in dataset:
            itemdict = SpringSearch.runIndividual(item)
            outputs.append(itemdict)
        return outputs
    def runIndividual(item):
        # Assume historical has >= 3 sales
        itemdict = dict()
        cutoff_ratio = 1.15
        item = historicalDateFilter(item,15)

        historical = [x[1] for x in item['Sales from last month']]
        quarts, _ = quartiles(historical)
        Q1, Q2, Q3 = quarts

        itemdict['Satisfied'] = (item['Special Type'] != 'Souvenir'
                                # Souvenirs aren't very predictable imo
                                    and Q3/cutoff_ratio > item['Buy Rate']
                                    # If buy rate is higher than profit pt., no chance of profit
                                    and Q1*cutoff_ratio < Q3
                                    # Actual profit filter
                                    and quarts[0] <= 144.77
                                    # Account balance is limited
                                )
        itemdict['Name'] = item['Item Name']
        itemdict['Quartiles'] = tuple(map(lambda x: round(x,2), quarts))
        itemdict['Days/Profit'] = round(1/(item['Sales/Day']/8),2)
        # ^^ x/8 because 1/4th chance to appear at or below Q1, 1/4th at or above Q3
        itemdict['Ratio'] = round(Q3/Q1,2)
        itemdict['Profit'] = round((itemdict['Ratio']-1.15)*Q1,2) # Buy at Q1, sell at Q3
        itemdict['Profit/Day'] = round(itemdict['Profit']*item['Sales/Day']/8,2)

        return itemdict

#######################

if __name__ == '__main__':
    print('Doing inital dataset import...')
    DBdata = import_json_lines('../data/pagedata 1.txt', encoding='utf_16')
    print('Successful import! Number of entries:', len(DBdata))
    DBdata = [x for x in DBdata if volumeFilter(x, 30)]
    DBdata = [x for x in DBdata if listingFilter(x, 1)]
    print('Number that satisfy volume and listing filter:', len(DBdata))
    print()

    # Testing SimpleListingProfit
    SLPresults, SLPsatresults = basicTest(SimpleListingProfit,inputs=[1.15], printsat=False)
    SLPsatresults = sorted(SLPsatresults, key = lambda x: x['Ratio'], reverse=True)
    head(SLPsatresults,10)
    print()

    # Testing LessThanThirdQuartileHistorical
    LTTQHresults, LTTQHsatresults = basicTest(LessThanThirdQuartileHistorical, printsat=False)
    LTTQHsatresults = sorted(LTTQHsatresults, key = lambda x: x['Profit/Day'], reverse=True)
    head(LTTQHsatresults,10)
    DBchange([x for x in DBdata if LessThanThirdQuartileHistorical.runindividual(x)['Satisfied']],
             'add',
             '../data/LTTQHitems.txt')
    print()

    # Testing SpringSearch
    SSresults, SSsatresults = basicTest(SpringSearch, printsat=False)
    SSsatresults = sorted(SSsatresults, key = lambda x: x['Profit/Day'], reverse=True)
    head(SSsatresults,10)
    print()

    print('Average daily profit at perfect information/liquidity:', round(sum([x['Profit/Day'] for x in SSsatresults]),2))

    portfolio_size = 100
    # print('Highest profit at',portfolio_size)

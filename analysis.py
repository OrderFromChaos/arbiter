#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu
# Last Updated: June 7, 2019

### PURPOSE:
### This program serves two purposes:
### 1. A source for buying/selling strategies to be slotted into other programs and
### 2. When run as itself, the ability to backtest strategies during development.

### TODO: 

### 1. Figure out how to do something similar to lstsq_before_hour for graphical analysis.

### 2. Incorporate stuff from expectedprice.py and linregtest.py
###    (early analysis attempts)

from utility_funcs import import_json_lines # Importing logged dataset
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
    if inputs:
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

def simpleMovingAvg(dataset, n):
    if len(dataset) < n:
        return 'N is too high for this dataset (' + str(len(dataset)) + ' < ' + str(n) + ')'
    
    avg_list = []
    for i in range(0,len(dataset)-n):
        avg = sum(dataset[i:i+n])/n
        avg_list.append(avg)
    return avg_list

def removeOutliers(dataset, key, sigma):
    # Remove all data points that are greater than sigma away from the mean
    outlier_axis = [x[key] for x in dataset]
    mean = sum(outlier_axis)/len(outlier_axis)
    stdev = (sum([(x-mean)**2 for x in outlier_axis])/len(outlier_axis))**0.5
    return [x for x in dataset if mean-sigma*stdev < x[key] < mean+sigma*stdev]

def volumeFilter(dataset, saleslastmonth): # Run for all strategies by default
    return [x for x in dataset if len(x['Sales from last month']) >= saleslastmonth]

def listingFilter(dataset, amountoflistings):
    return [x for x in dataset if len(x['Listings']) >= amountoflistings]

def profiler(items):
    # to be built later; used to mine frequency data from the items that satisfy a filter
    pass

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
        return (L[rightmid-1]+L[rightmid])/2, rightmid-0.5

def quartiles(L):
    L = sorted(L)

    Q2, midpoint = median(L)
    if isinstance(midpoint, int):
        Q1, Q1pos = median(L[:midpoint])
        Q3, Q3pos = median(L[midpoint+1:])
    elif isinstance(midpoint, float):
        Q1, Q1pos = median(L[:ceil(midpoint)])
        Q3, Q3pos = median(L[ceil(midpoint):])
    return (Q1,Q2,Q3), (Q1pos, midpoint, Q3pos)

def dateFilter(dataset, ndays):
    for index, item in enumerate(dataset):
        filter_date = item['Sales from last month'][-1][0] - timedelta(days=ndays)
        dataset[index]['Sales from last month'] = [x for x in item['Sales from last month'] 
                                                   if x[0] >= filter_date]
    return dataset

def tail(dataset,n):
    for i in dataset[:n]:
        print(i)

########################



### ACTUAL STRATEGY ###

class SimpleListingProfit:
    def __init__(self, percentage):
        self.percentage = percentage # Steam % cut on Marketplace purchases for that game. 
                                     # For CS:GO, this is 15%
    def run(self, dataset):
        outputs = []
        dataset = listingFilter(dataset,4)
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
        # dataset = dateFilter(dataset,15)
        dataset = volumeFilter(dataset,30) # Q3 is meaningless without this
        # dataset = removeOutliers(dataset,'Sales from last month',2) # Bugged for some reason
        for item in dataset:
            itemdict = LessThanThirdQuartileHistorical.runindividual(item)
            # itemdict['Expected Profit/Day'] = round(Q3-itemdict['Lowest Listing']*1.15,2)
            outputs.append(itemdict)
        return outputs
    def runindividual(item):
        itemdict = dict()
        # Assume already volume filtered
        historical = [x[1] for x in item['Sales from last month']]

        quarts, anchors = quartiles(historical)
        Q1, Q2, Q3 = quarts
        _, _, Q3pos = anchors
        # Q3pos is for the later to be implemented Expected Profit/Day

        itemdict['Satisfied'] = (item['Listings'][0]*1.15 < Q3 
                                    and item['Special Type'] != 'Souvenir')
        itemdict['Name'] = item['Item Name']
        itemdict['Quartiles'] = tuple(map(lambda x: round(x,2), (Q1,Q2,Q3)))
        itemdict['Lowest Listing'] = item['Listings'][0]
        itemdict['Sales/Day'] = item['Sales/Day']
        itemdict['Expected Profit'] = round(Q3-itemdict['Lowest Listing']*1.15,2)

        return itemdict

class SpringSearch:
    # Items whose historical data Q1 and Q3 differ by more than 15%
    def run(dataset):
        outputs = []
        dataset = volumeFilter(dataset,30) # Spring is likely not meaningful without large vol.
        dataset = dateFilter(dataset,15)
        for item in dataset:
            itemdict = SpringSearch.runIndividual(item)
            outputs.append(itemdict)
        return outputs
    def runIndividual(item):
        # Assume already volume filtered
        itemdict = dict()
        cutoff_ratio = 1.15
        item = dateFilter([item],15)[0]

        historical = [x[1] for x in item['Sales from last month']]
        quarts, anchors = quartiles(historical)
        Q1, Q2, Q3 = quarts

        itemdict['Satisfied'] = (item['Special Type'] != 'Souvenir'
                                    and Q3/cutoff_ratio > item['Buy Rate']
                                    and Q1*cutoff_ratio < Q3
                                    and item['Sales/Day'] >= 2)
        itemdict['Name'] = item['Item Name']
        itemdict['Quartiles'] = tuple(map(lambda x: round(x,2), quarts))
        itemdict['Sales/Day'] = item['Sales/Day']
        itemdict['Ratio'] = round(Q3/Q1,2)
        itemdict['Profit'] = round((itemdict['Ratio']-1.15)*Q1,2) # Buy at Q1, sell at Q3

        return itemdict

#######################

if __name__ == '__main__':
    print('Doing inital dataset import...')
    DBdata = import_json_lines('pagedata.txt', encoding='utf_16', numlines=11)
    print('Successful import! Number of entries:', len(DBdata))
    DBdata = volumeFilter(DBdata, 30)
    DBdata = listingFilter(DBdata, 1)
    print('Number that satisfy volume and listing filter:', len(DBdata))

    # Testing SimpleListingProfit
    SLPresults, SLPsatresults = basicTest(SimpleListingProfit,inputs=[1.15], printsat=False)
    tail(sorted(SLPsatresults, key = lambda x: x['Ratio'], reverse=True),10)

    # Testing LessThanThirdQuartileHistorical
    LTTQHresults, LTTQHsatresults = basicTest(LessThanThirdQuartileHistorical)

    # Testing SpringSearch
    SSresults, SSsatresults = basicTest(SpringSearch, printsat=False)
    tail(sorted(SSsatresults, key = lambda x: x['Profit'], reverse=True),10)

#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu
# Last Updated: June 5, 2019

### PURPOSE:
### This program serves two purposes:
### 1. A source for buying/selling strategies to be slotted into other programs and
### 2. When run as itself, the ability to backtest strategies during development.

### TODO: 

### 1. Figure out how to do something similar to lstsq_before_hour for graphical analysis.

### 2. Incorporate stuff from complexanalysis.py, expectedprice.py, and linregtest.py
###    (early analysis attempts)

### 3. Figure out how to incorporate analysis funcs into price_scanner.py

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

def dateFilter(dataset, ndays):
    for index, item in enumerate(dataset):
        filter_date = item['Sales from last month'][-1][0] - timedelta(days=ndays)
        dataset[index]['Sales from last month'] = [x for x in item['Sales from last month'] 
                                                   if x[0] >= filter_date]
    return dataset

########################



### ACTUAL STRATEGY ###

class SimpleListingProfit:
    def __init__(self, percentage):
        self.percentage = percentage # Steam % cut on Marketplace purchases for that game. 
                                     # For CS:GO, this is 15%
    def run(self, dataset):
        outputs = []
        dataset = listingFilter(dataset,2)
        for item in dataset:
            itemdict = dict()
            listings = item['Listings']
            relevant_listings = sorted(listings[:2])
            ratio = relevant_listings[1]/relevant_listings[0]

            itemdict['Satisfied'] = ratio > self.percentage
            itemdict['Name'] = item['Item Name']
            itemdict['Ratio'] = round(ratio,2)

            outputs.append(itemdict)
        return outputs

class LessThanThirdQuartileHistorical:
    def run(dataset):
        outputs = []
        # dataset = dateFilter(dataset,15)
        # for index, item in enumerate(dataset): # Filter out now irrelevant info
        #     dataset[index]['Sales from last month'] = [x[1] for x in item['Sales from last month']]
        dataset = volumeFilter(dataset,3) # Q3 is meaningless without this
        # dataset = removeOutliers(dataset,'Sales from last month',2) # Bugged for some reason
        for item in dataset:
            itemdict = dict()
            historical = sorted([x[1] for x in item['Sales from last month']])

            Q2, midpoint = median(historical)
            if isinstance(midpoint, int):
                Q1, _ = median(historical[:midpoint])
                Q3, Q3list = median(historical[midpoint+1:])
            elif isinstance(midpoint, float):
                Q1, _ = median(historical[:ceil(midpoint)])
                Q3, Q3list = median(historical[ceil(midpoint):])
            
            itemdict['Satisfied'] = (item['Listings'][0]*1.15 < Q3 
                                     and item['Special Type'] != 'Souvenir')
            itemdict['Name'] = item['Item Name']
            itemdict['Quartiles'] = tuple(map(lambda x: round(x,2), (Q1,Q2,Q3)))
            itemdict['Lowest Listing'] = item['Listings'][0]
            itemdict['Sales/Day'] = item['Sales/Day']
            itemdict['Expected Profit'] = round(Q3-itemdict['Lowest Listing']*1.15,2)
            itemdict['Expected Profit/Day'] = round(Q3-itemdict['Lowest Listing']*1.15,2)
            outputs.append(itemdict)
        return outputs

### TODO: Implement "spring" model - items that can likely be buy/sold right away just by vigilantly
###       watching.

# [INSERT MORE HERE]

#######################

if __name__ == '__main__':
    print('Doing inital dataset import...')
    DBdata = import_json_lines('pagedata.txt', encoding='utf_16', numlines=11)
    print('Successful import! Number of entries:', len(DBdata))
    DBdata = volumeFilter(DBdata, 30)
    DBdata = listingFilter(DBdata, 1)
    print('Number that satisfy volume and listing filter:', len(DBdata))

    # Testing simple listing profit
    SLPresults, SLPsatresults = basicTest(SimpleListingProfit,inputs=[1.15], printsat=False)

    # Testing LessThanThirdQuartileHistorical
    LTTQHresults, LTTQHsatresults = basicTest(LessThanThirdQuartileHistorical)

    ### [Write your strategy backtests here]

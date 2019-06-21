#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### PURPOSE:
### This program serves two purposes:
### 1. A source for buying/selling strategies to be slotted into other programs and
### 2. When run as itself, the ability to test and backtest strategies during development.

import pandas as pd                         # Dataset format
from datetime import datetime, timedelta    # Volumetric sale filtering based on date
from math import floor, ceil                # Data analysis use in medians

# Print settings
pd.options.display.width = 0
pd.set_option('display.max_columns', 7)

def filterPrint(df, printtype='head', printval=10, keys=['Item Name', 'Date', 'Buy Rate', 'Sales/Day']):
    if printtype == 'head':
        print(df[keys].head(printval))
    elif printtype == 'tail':
        print(df[keys].tail(printval))
    else:
        raise Exception('Unsupported print type: ' + printtype)

class BackTester:
    # This looks at historical data to see if a particular strategy would have worked.
    # Assumptions: 
    #    1. Ignore market updates based on your price listings. This is imperfect
    #       (you're part of the market), but I have no idea how to account for this.
    # Inputs:
    #    Strategy to use. It will scan over (say) a day and buy any satisfied items.
    #    Historical days to test the buying algorithm process over: [start, end]
    #    ie "testing region"
    #        if integers, X days in past
    #        if datetime, specific dates
    #    Sell time - how many days to hold. 
    #        TODO: Allow for dynamic sell region in the future. LTTQH usually has a variable
    #              expected sell date.
    #    Sell capturing ability - how well you can sell. This is in quartiles, so .95 means you
    #        do not have access to the top 5% of sale prices (maybe these were irrational consumers)
    #        [IMPLEMENTATION: Might be useful to use numpy.quantiles]
    # Outputs:
    #    Profit
    #    Overall cashflow to achieve profit
    #    Max portfolio holding (max resources to get this profit?)
    #    Buy/sell history
    # 
    # Ideally, this can later be thrown into a profit-maximizing optimization algorithm,
    #     so we can use the "best" strategy according to backtesting.
    def __init__(self, strategy, testregion, liquidation_force_days, capturing_ratio):
        # "strategy" is a class with an implemented .runBacktest() function which returns
        #     profit, overall cashflow to achieve profit, max portfolio holding, 
        #     and buy/sell history
        # "testregion" is a two-len list with [startdate, enddate]. These dates can be a mix of
        #     integers (floor(today) - X days ago, where X is the int) or datetime objects.
        # "liquidation_force_days" and "capturing_ratio" tells the algorithm how to liquidate buys;
        #     it will select liquidation_force_days after the buy and pick the highest value after
        #     getting everything less than the capturing_ratio quantile (eg .95, so everything
        #     except the top 5% of sales). Picking these is a bit of an art, and might be worthwhile
        #     to TODO update based on number of sales in question. 0.85 seems like a good place to
        #     start on capturing_ratio based on it excluding the highest 1/7 sales.
        #     Note that reducing liquidation_force_days does decrease the portfolio use, but also
        #     decreases profit potential (on average), assuming item prices stay generally constant.
        self.strategy = strategy
        self.testregion = testregion
        self.liquidation_force_days = liquidation_force_days
        self.capturing_ratio = capturing_ratio
        self.purchases = []
    def runBacktest(self):
        global DBdata
        test_samples = historicalSelectorDF(DBdata, self.testregion)
        self.purchases = self.strategy.runBacktest(DBdata, test_samples, self.testregion)
        # Now take these purchases and carry out liquidation sells
        # Note that if you hold eg. 5 of an item, you permanently remove one of the possible sell
        #     maxes, so you have to sell for a lower price

class CurrTester:
    def __init__(self, strategy):
        self.strategy = strategy
        self.satdf = None
    def runCurrtest(self):
        # Calls the strategy's "run" function to get the dataframe that satisfies the strategy
        global DBdata
        self.satdf = self.strategy.run(DBdata)

def basicTest(strategy, inputs=None):
    if inputs:
        currtest = CurrTester(strategy(*inputs))
    else:
        currtest = CurrTester(strategy)
    currtest.runCurrtest()
    satdf = currtest.satdf
    printkeys = currtest.strategy.printkeys
    print('Number that satisfy', strategy.__name__ + ':', len(satdf.index))
    return satdf, printkeys

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

def standardFilter(df):
    df = volumeFilter(df, 30)
    df = souvenirFilter(df)
    return df

def dayFloorDate(date):
    return datetime(date.year, date.month, date.day)

def historicalSelector(L, dateregion=[7,0]):
    # Note that L is a series
    for index, date in enumerate(dateregion):
        if isinstance(date, int):
            rightmost_date = L[-1][0]
            rightfloor = dayFloorDate(rightmost_date)
            dateregion[index] = rightfloor - timedelta(days=date)
        elif isinstance(date, datetime):
            pass
        else:
            raise Exception('Unsupported type! Must be int or datetime. Your type: ' + 
                            str(type(date)))

    L = [saleinfo for saleinfo in L if dateregion[0] <= saleinfo[0] <= dateregion[1]]
    return L

def historicalSelectorDF(df, dateregion):
    df['Sales from last month'] = df['Sales from last month'].apply(historicalSelector, 
                                                                    dateregion=dateregion)
    return df

def historicalDateFilter(df, ndays):
    df = historicalSelectorDF(df, [ndays, 0])
    return df

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
        self.printkeys = ['Item Name', 'Date', 'Buy Rate', 'Sales/Day', 'Ratio'] # For filterPrint
    
    def run(self, df):
        # Actual strategy
        satdf = standardFilter(df)
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
        self.printkeys = ['Item Name', 'Date', 'Sales/Day', 'Lowest Listing', 'Q3', 'Ratio']
    
    def prepare(self, df, dateregion=[15,0]):
        satdf = standardFilter(df)
        satdf = historicalSelectorDF(satdf, dateregion)
        satdf = volumeFilter(satdf, 3)

        details = satdf['Sales from last month'].apply(quartileHistorical)
        details = pd.DataFrame(details.tolist(), index=details.index, columns=['Q1','Q2','Q3'])
        satdf = satdf.join(details)
        return satdf

    def run(self, df):
        satdf = prepare(df)

        lowest_listings = pd.DataFrame(data={'Lowest Listing': satdf['Listings'].apply(lambda L: L[0])})
        satdf = satdf.join(lowest_listings)
        satdf = satdf[satdf['Lowest Listing'] < satdf['Q1']]
        satdf = satdf[satdf['Lowest Listing']*(self.percentage + .01) < satdf['Q3']]

        details = pd.DataFrame(satdf['Q3']/satdf['Lowest Listing'], columns=['Ratio'])
        satdf = satdf.join(details)
        satdf['Ratio'] = satdf['Ratio'].apply(lambda x: round(x,2))

        return satdf

    # TODO: Implement days to profit into models
    #     itemdict['Days To Profit'] = round(1/(item['Sales/Day']/4),2)
    #     # ^^ x/4 because 1/4th chance to appear at or above Q3
    #     itemdict['Profit'] = round(Q3-itemdict['Lowest Listing']*1.15,2)
    #     itemdict['Profit/Day'] = round(itemdict['Profit']*item['Sales/Day']/4,2)
    #     return itemdict

    def runBacktest(self, df, test_samples, test_region):
        # 'test_samples' is a dataframe where everything in 'Sales from last month' are buy prices 
        #     to check for that item
        # 'test_region' tells you were to measure quartiles from
        ndays = 7

        satdf = prepare(df, [test_region[0] - ndays, test_region[0]])
        purchases = pd.DataFrame(columns=['Name', 'Date', 'Buy Price'])

        # Algorithm, in short:
        # for each item in df
        #     check each item in test_samples
        #     if satisfied, log as buy
        # return buy list

        for index, historical_row in satdf.iterrows():
            test_row = test_region.iloc[index]
            good_to_buy = test_row['Sales from last month']
            good_to_buy = [x for x in good_to_buy if x[1] < historical_row['Q1']]
            for purchase in good_to_buy:
                p = pd.Series(data={'Name': historical_row['Item Name'],
                                    'Date': purchase[0],
                                    'Buy Price': purchase[1],
                                    'Q1': historical_row['Q1'],
                                    'Q3': historical_row['Q3']})
                purchases = purchases.append([p], ignore_index=True)

        return purchases

class SpringSearch:
    # Items whose historical data Q1 and Q3 differ by more than a given percentage
    def __init__(self, percentage, numdays=15):
        self.percentage = percentage # Steam % cut on Marketplace purchases for that game. 
                                     # For CS:GO, this is 15%
        self.numdays = numdays
        self.printkeys = ['Item Name', 'Date', 'Buy Rate', 'Sales/Day', 'Ratio']
    
    def run(self, df):
        satdf = standardFilter(df)
        satdf = historicalDateFilter(satdf, self.numdays)
        satdf = volumeFilter(satdf, 3)

        details = satdf['Sales from last month'].apply(quartileHistorical)
        details = pd.DataFrame(details.tolist(), index=details.index, columns=['Q1','Q2','Q3'])
        satdf = satdf.join(details)

        satdf = satdf[satdf['Q1']*(self.percentage) < satdf['Q3']]
        satdf = satdf[satdf['Q1'] > satdf['Buy Rate']]

        details = pd.DataFrame(satdf['Q3']/satdf['Q1'], columns=['Ratio'])
        satdf = satdf.join(details)
        satdf['Ratio'] = satdf['Ratio'].apply(lambda x: round(x,2))
        # satdf = satdf[satdf['Q1'].apply(lambda q: q < 144.77)] # Account balance restriction
        return satdf

#######################

if __name__ == '__main__':
    print('Doing inital dataset import...')
    DBdata = pd.read_hdf('../../data/item_info.h5', 'csgo')
    print('Successful import! Number of entries:', len(DBdata.index))
    DBdata = standardFilter(DBdata)
    print('Number that satisfy volume, listing, and souvenir filters:', len(DBdata.index))
    print()

    # Testing SimpleListingProfit
    SLPsat, printkeys = basicTest(SimpleListingProfit,inputs=[1.15])
    SLPsat = SLPsat.sort_values('Ratio', ascending=False)
    filterPrint(SLPsat, keys=printkeys)
    print()

    # Testing LessThanThirdQuartileHistorical
    LTTQHsat, printkeys = basicTest(LessThanThirdQuartileHistorical, inputs=[1.15])
    LTTQHsat = LTTQHsat.sort_values('Ratio', ascending=False)
    filterPrint(LTTQHsat, keys=printkeys)
    # TODO: Implement writing to file
    # DBchange([x for x in DBdata if LessThanThirdQuartileHistorical.runindividual(x)['Satisfied']], 
    #          'add',
    #          '../../data/LTTQHitems.txt')
    print()

    # Testing SpringSearch
    SSsat, printkeys = basicTest(SpringSearch, inputs=[1.15])
    SSsat = SSsat.sort_values('Ratio', ascending=False)
    filterPrint(SSsat, keys=printkeys)
    print()

    # TODO: Implement profit guesses
    # print('Average daily profit at perfect information/liquidity:', round(sum([x['Profit/Day'] for x in SSsatresults]),2))
    # portfolio_size = 100
    # # print('Highest profit at',portfolio_size)

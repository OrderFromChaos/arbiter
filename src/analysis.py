#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### PURPOSE:
### This program serves two purposes:
### 1. A source for buying/selling strategies to be slotted into other programs and
### 2. When run as itself, the ability to test and backtest strategies during development.

import pandas as pd                         # Dataset format
import matplotlib.pyplot as plt             # Graphing backtest outputs
import seaborn as sns                       # Nicer plots
import numpy as np
from scipy.stats import binned_statistic    
from datetime import datetime, timedelta    # Volumetric sale filtering based on date
from math import ceil                       # Data analysis use in medians
from copy import deepcopy                   # Working around Python's habit of shallow copies
from sty import fg                          # Cross-platform color printing
import statistics                           # Convenience

def filterPrint(df, printtype='head', printval=10, keys=['Item Name', 'Date', 'Buy Rate', 'Sales/Day'], color=None):
    if printtype == 'head':
        if color:
            print(color)
            print(df[keys].head(printval)) 
            print(fg.rs)
        else:
            print(df[keys].head(printval))
    elif printtype == 'tail':
        if color:
            print(color)
            print(df[keys].tail(printval)) 
            print(fg.rs)
        else:
            print(df[keys].tail(printval))
    else:
        raise Exception('Unsupported print type: ' + printtype)

class BackTesterV2:
    # This looks at historical data to see if a particular strategy would have worked.
    # Assumptions:
    #    1. Ignore market updates based on your price listings. This is imperfect
    #       (you're part of the market), but I have no idea how to account for this.
    #    2. Perfect information on the purchasing side. I know I have imperfect information on sell,
    #       so the algorithm sells only at the recommend price (eg Q3) instead of the actual higher
    #       real sell. The reasoning is that this shows there is an economic market for high prices.
    #       This could be spurious, since it would auto-sell on a weird spike, but it's an alright
    #       approximation. TODO: See how heavily pushing this down would affect the algorithm.
    # 
    # Later, this can be thrown into a profit-maximizing optimization algorithm,
    #     so we can use the "best" strategy according to backtesting. However, I feel like given the
    #     numerous potential pitfalls, it is best to work using graphs and human analysis.
    def __init__(self, strategy, testregion, liquidation_force_days, inputs=None, usefallbackmethod=False):
        # "strategy" is a class with an implemented .runBacktest() function which returns
        #     recommended buys and recommended sell/fallback prices. This class takes care of the
        #     selling process.
        # "testregion" is a two-len list with [startdate, enddate]. These dates can be a mix of
        #     integers (floor(today) - X days ago, where X is the int) or datetime objects.
        # "liquidation_force_days" tells the algorithm how to liquidate buys. After
        #     purchase, but before buy_date + liquidation_force_days, the algo with attempt to sell at
        #     the strategy-recommended sell price. If there is a sell above this pricing, it will sell
        #     at the recommended price anyway (just shows that consumer willingness was there).
        #     After buy_date + liquidation_force_days, algo will attempt to sell at fallback price for
        #     remainder of history.
        # "inputs" is for inputs to the functions, like the 15% Steam cut
        # "usefallbackmethod" tells the backtester whether to use sell fallback price or sell fallback
        #     method. "true" is by fiat more reactive to pricing shifts and almost always better.
        self.strategy = strategy
        self.testregion = testregion
        self.liquidation_force_days = liquidation_force_days
        self.inputs = inputs
        self.usefallbackmethod = usefallbackmethod
        # Will eventually be a list of 
        # [{'Buy Date': , 'Recommended Sell': , 'Fallback Sell': }
        #   , ...]
        self.purchases = []
    def runBacktest(self, DBdata, verbose=True):
        # First, obtain purchases.
        if verbose:
            print('Backtesting [{0}]...'.format(self.strategy.__name__))
        sacrificial_testregion = deepcopy(self.testregion)
        # historicalSelectorDF modifies DBdata historical to be over the testregion
        sacrificial_DBdata = deepcopy(DBdata) 
        test_samples = historicalSelectorDF(sacrificial_DBdata, sacrificial_testregion)

        self.strategy = self.strategy(*self.inputs)
        if verbose:
            print('Generating purchases over testregion...')
        # runBacktestV2 modifies DBdata historical to be after the testregion
        sacrificial_DBdata = deepcopy(DBdata)
        self.purchases = self.strategy.runBacktestV2(sacrificial_DBdata, test_samples, self.testregion)
        # Note that the format of self.purchases is:
        # {
        #     "Name": "Some Item (Factory New)",
        #     // Some metadata about that item here
        #     "Purchases": {
        #         "Name": "Some Item (Factory New)",
        #         "Buy Date": ...,
        #         "Buy Price": ...,
        #         "Recommended Sell": ...,
        #         "Fallback Sell": ...,
        #         "Fallback Method": ...
        #     }
        # }
        # Name is redundant, but some inner loops use that information, so it's probably best to just
        # pass it along. TODO: Remove this redundancy.

        # Now, sell your inventory.
        # Note that if you hold eg. 5 of an item, you permanently remove one of the possible sells.
        # (Unsurprisingly, this increases implementation complexity)
        if verbose:
            print('Number of purchases:', sum([len(x['Purchases']) for x in self.purchases]))
            print('Running liquidation sell process...')

        nametoindex = {x['Item Name']: i for i, x in DBdata.iterrows()}
        phase1sell = [] # Sold at recommended sell
        phase2sell = [] # Sold at fallback sell
        phase3sell = [] # Never sold
        for unique_name in self.purchases:
            firstrun = True
            relevant_history = DBdata.loc[nametoindex[unique_name['Name']]]['Sales from last month']

            for i, p in enumerate(unique_name['Purchases']): # For each purchase under that item name
                # The following code uses a rolling window sell region to avoid repeated sells.
                ### Sell Window Updating {
                if firstrun: # Initialize rolling window
                    phase1bounds = [p['Buy Date'], p['Buy Date'] + timedelta(days=self.liquidation_force_days)]
                    phase1region = historicalSelector(relevant_history, phase1bounds)
                    phase2bounds = [phase1bounds[1], unique_name['Date Pulled']]
                    phase2region = historicalSelector(relevant_history, phase2bounds)
                else:
                    # Remove old left region; sell dates should be +0 or increasing
                    phase1region = [x for x in phase1region if x > p['Buy Date']]
                    phase2region = [x for x in phase2region if x > p['Buy Date']]

                    # Add new rightmost region (only for phase1region; phase2region extends to end)
                    previous_end = (unique_name['Purchases'][i-1]['Date'] + timedelta(days=self.liquidation_force_days))
                    if previous_end > p['Buy Date']:
                        rightaddition = [previous_end, p['Buy Date'] + timedelta(days=self.liquidation_force_days)]
                    else:
                        rightaddition = [p['Buy Date'], p['Buy Date'] + timedelta(days=self.liquidation_force_days)]
                    phase1region += historicalSelector(relevant_history, rightaddition)
                p['Regions'] = (phase1bounds, phase2bounds) # Used during graphical analysis of backtest
                ### Sell Window Updating }
                
                ### Actual selling {
                while True: # Enforces recommended sell -> fallback sell logic
                    # Phase 1 checks
                    soldphase1 = False
                    for index, historicalsell in enumerate(phase1region):
                        if historicalsell[1] >= p['Recommended Sell']:
                            soldphase1 = True
                            del phase1region[index]
                            p['Profit'] = p['Recommended Sell']/1.15 - p['Buy Price']
                            p['Sell Date'] = historicalsell[0]
                            phase1sell.append(p)
                            break
                    if soldphase1:
                        break

                    # Phase 2 checks
                    soldphase2 = False
                    if self.usefallbackmethod: # Use the intelligent re-estimate function passed along
                        fxn = p['Fallback Method']
                        price_estimate = fxn(relevant_history, phase1bounds, p)
                    else: # Go based on the less intelligent estimated fallback price
                        price_estimate = p['Fallback Sell']
                    
                    # Try and find a sell for the fallback estimate price
                    for index, historicalsell in enumerate(phase2region):
                        if historicalsell[1] >= price_estimate:
                            soldphase2 = True
                            del phase2region[index]
                            p['Profit'] = price_estimate/1.15 - p['Buy Price']
                            p['Sell Date'] = historicalsell[0]
                            phase2sell.append(p)
                            break
                    if soldphase2:
                        break
                    else:
                        # Neither conditions satisfied, so append to phase3sell
                        phase3sell.append(p)
                        break
        if verbose:
            print('Finished figuring out sales! Sending sells to analysis...')

        return (self.purchases, (phase1sell, phase2sell, phase3sell))

def basicTest(strategy, inputs=None):
    if inputs:
        strategy = strategy(*inputs)
    else:
        strategy = strategy()
    satdf = strategy.run(DBdata)
    printkeys = strategy.printkeys
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
    assert len(L) >= 3, ('Quartiles are meaningless with less than 3 data points.'
                         ' Did you use volumeFilter after using historicalSelector?')
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

def listingPriceFilter(df, price):
    return df[df['Buy Rate'] >= price]

def souvenirFilter(df):
    return df[df['Special Type'] != 1]

def standardFilter(df):
    df = volumeFilter(df, 30)
    df = souvenirFilter(df)
    df = listingPriceFilter(df, 1.00)
    return df

def dayFloorDate(date):
    return datetime(date.year, date.month, date.day)

def historicalSelector(L, dateregion=[7,0]):
    # Note that L is a list
    for index, date in enumerate(dateregion):
        if isinstance(date, int) or isinstance(date, float):
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

def removeHistoricalOutliers(L, sigma=1):
    # Filter all data points that are greater than sigma away from the mean
    historical_nums = [x[1] for x in L]
    mean = statistics.mean(historical_nums)
    stdev = statistics.stdev(historical_nums)
    finL = [x for x in L if abs((x[1]-mean)/stdev) <= sigma]
    return finL

########################


### ACTUAL STRATEGY ###

# DO NOT USE FOR BACKTESTING; NO POSSIBLE RUNBACKTEST FUNCTION
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
    def __init__(self, percentage, dateregion):
        self.percentage = percentage # percent less than Q3 before a buy will trigger.
        self.dateregion = dateregion
        self.printkeys = ['Item Name', 'Date', 'Sales/Day', 'Lowest Listing', 'Q3', 'Ratio']
    
    def prepare(self, df, dateregion=None):
        if not dateregion:
            dateregion = self.dateregion
        
        df = deepcopy(df)

        satdf = standardFilter(df)
        satdf = volumeFilter(satdf, 60) # Make quartiles more meaningful
        satdf = historicalSelectorDF(satdf, dateregion)
        satdf = volumeFilter(satdf, 3)
        satdf['Sales from last month'] = satdf['Sales from last month'].apply(removeHistoricalOutliers, sigma=1.5)
        satdf = volumeFilter(satdf, 5)

        details = satdf['Sales from last month'].apply(quartileHistorical)
        details = pd.DataFrame(details.tolist(), index=details.index, columns=['Q1','Q2','Q3'])
        satdf = satdf.join(details)
        return satdf

    def run(self, df):
        satdf = self.prepare(df)

        lowest_listings = pd.DataFrame(data={'Lowest Listing': satdf['Listings'].apply(lambda L: L[0])})
        satdf = satdf.join(lowest_listings)
        satdf = satdf[satdf['Lowest Listing']*(self.percentage + .01) < satdf['Q3']]

        details = pd.DataFrame(satdf['Q3']/satdf['Lowest Listing'], columns=['Ratio'])
        satdf = satdf.join(details)
        satdf['Ratio'] = satdf['Ratio'].apply(lambda x: round(x,2))

        return satdf
    
    def runBacktestV2(self, df, test_samples, test_region):
        # 'test_samples' is DBdata, but 'Sales from last month' is filtered to the buy region
        # 'test_region' is the boundaries of the historical region to check quartiles over

        satdf = self.prepare(df, dateregion=[test_region[0] + (self.dateregion[0]-self.dateregion[1]), test_region[0]])
        purchases = []

        def fallbackPricing(fullhistory, phase1bounds, purchase_data):
            # phase1bounds = [p['Buy Date'], p['Buy Date'] + timedelta(days=self.liquidation_force_days)]
            # phase1region = historicalSelector(relevant_history, phase1bounds)
            phase1bounds = deepcopy(phase1bounds)
            phase1bounds[0] -= timedelta(days=2) # Increase window size on the left
            newregion = historicalSelector(fullhistory, phase1bounds)
            if len(newregion) >= 3:
                Q1, Q2, Q3 = quartileHistorical(newregion)
                return Q3
            else:
                # Cannot find quartiles with this few data points, so use old fallback sell instead
                return purchase_data['Fallback Sell']

        for index, historical_row in satdf.iterrows():
            test_row = test_samples.loc[index]
            good_to_buy = test_row['Sales from last month']
            good_to_buy = [x for x in good_to_buy if x[1] < historical_row['Q3']/(self.percentage + .01)
                                                  and x[1] < historical_row['Q1']]
            item_dict = {'Name': historical_row['Item Name'],
                         'Date Pulled': historical_row['Date'],
                         'Sales/Day': historical_row['Sales/Day'],
                         'Q1': historical_row['Q1'],
                         'Q2': historical_row['Q2'],
                         'Q3': historical_row['Q3'],
                         'Purchases': []}
            for purchase in good_to_buy:
                p = {'Name': item_dict['Name'],
                    'Buy Date': purchase[0],
                    'Buy Price': purchase[1],
                    'Recommended Sell': item_dict['Q3'],
                    'Fallback Sell': item_dict['Q2'],
                    'Fallback Method': fallbackPricing}
                item_dict['Purchases'].append(p)
            if item_dict['Purchases']:
                purchases.append(item_dict)

        return purchases

#######################

if __name__ == '__main__':
    print('Doing inital dataset import...')
    DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
    print('Successful import! Number of entries:', len(DBdata.index))
    DBdata = standardFilter(DBdata)
    print('Number that satisfy volume, souvenir, and price filters:', len(DBdata.index))

    # # Testing LessThanThirdQuartileHistorical
    # LTTQHsat, printkeys = basicTest(LessThanThirdQuartileHistorical, inputs=[1.15, [8,0]])
    # LTTQHsat = LTTQHsat.sort_values('Ratio', ascending=False)
    # filterPrint(LTTQHsat, keys=printkeys)
    # print()

    # BacktesterV2: (historical buy region L, R), days of rec. sell, [function hyperparams, ...]  
    hmeta = ([5,4], 2)
    tester = BackTesterV2(LessThanThirdQuartileHistorical, hmeta[0], hmeta[1], 
                          inputs=[1.23, [8,0]], usefallbackmethod=True)
    purchases, phasesells = tester.runBacktest(DBdata)
    phase1sell, phase2sell, phase3sell = phasesells
    print('Never sold items:')
    print([p['Name'] for p in phase3sell])

    def profitAnalysisV2(phase1sell, phase2sell, phase3sell, historical_metadata, DBdata):
        # historical_metadata: ((5,4), 2)
        # The holding stats part of the code needs the test region and liquidation_force_sell

        # Basic stats
        actually_sold = phase1sell + phase2sell
        all_profits = [x['Profit'] for x in actually_sold]
        positive_profits = sum([x for x in all_profits if x > 0])
        negative_profits = sum([x for x in all_profits if x < 0]) - sum([x['Buy Price']-x['Buy Price']/(1.15**2) for x in phase3sell])
        net = positive_profits + negative_profits

        # Holding stats
        # Goal: iterate over each available hour. Sum over currently active buys (inclusive) to
        #       see current portfolio usage. This allows us to keep track of max inventory size and
        #       max money input.
        #       Generate a graph with this data. Output max holding.
        # Region is different for every item, so must use the stored item buy and sell date
        holding_time = [(x['Sell Date'] - x['Buy Date']).total_seconds()//3600 for x in actually_sold]  # in hrs
        hourly_bins = int(max(holding_time))
        # Then, figure out portfolio holdings
        all_buys = phase1sell + phase2sell + phase3sell
        mindate = min([x['Regions'][0][0] for x in all_buys])
        maxdate = max([x['Regions'][1][1] for x in all_buys])
        expected_hours = int((maxdate-mindate).total_seconds()//3600)
        end_of_buys = (historical_metadata[0][0] - historical_metadata[0][1])*24
        end_of_LFD = (end_of_buys//24 + historical_metadata[1])*24
        hour_spread = pd.date_range(start=mindate.strftime('%Y-%m-%d'), 
                                    end=maxdate.strftime('%Y-%m-%d'),
                                    periods=expected_hours+1)
        portfolio_size = [0]*(expected_hours+1)
        num_held = deepcopy(portfolio_size) # Lazy/10
        for p in all_buys:
            has_sale = False
            buy_date = p['Buy Date']
            if 'Sell Date' in p:
                has_sale = True
                sell_date = p['Sell Date']
            buy_price = p['Buy Price']
            for index, hour in enumerate(hour_spread):
                if has_sale:
                    if buy_date <= hour <= sell_date:
                        portfolio_size[index] += buy_price
                        num_held[index] += 1
                else:
                    if buy_date <= hour:
                        portfolio_size[index] += buy_price
                        num_held[index] += 1

        # Printing/graphing results
        cround = lambda currency: round(currency, 2)
        percent_all = lambda L: '({0}% of total)'.format(cround(100*len(L)/len(all_buys)))
        print('###################################################################################')
        print('Phase 1 sells:', len(phase1sell), percent_all(phase1sell))
        print('Phase 2 sells:', len(phase2sell), percent_all(phase2sell))
        print('Never sold:', len(phase3sell), percent_all(phase3sell))
        print('Net profit:', cround(net))
        print('Total loss:', cround(negative_profits))
        print('Total gain:', cround(positive_profits))
        print('Longest time to sale (hours):', max(holding_time))
        print('Maximum portfolio $$$:', cround(max(portfolio_size)))
        print('Highest holding number:', max(num_held))

        # Histogram: time to sale
        sns.distplot(holding_time, bins=hourly_bins+1, kde=False)
        plt.xlabel('Hours to sale')
        plt.ylabel('Volume of item sales')
        plt.show()

        # Plot: portfolio over time, in $ and quantity
        plt.plot(portfolio_size, color='blue', label='$$$ in portfolio')
        plt.plot(num_held, color='red', label='Number of items in inventory')
        plt.axvline(end_of_buys)
        plt.text(end_of_buys, max(portfolio_size)*1.1, 'End of buys')
        plt.axvline(end_of_LFD)
        plt.text(end_of_LFD, max(portfolio_size)*1.1, 'End of recommended sell')
        plt.xlabel('Hours into sale period')
        plt.ylabel('$$$ Portfolio Allocation')
        plt.legend(['$$$ in portfolio', 'Number of items in inventory'], loc='upper right')
        plt.show()

        # Plot: average return % at each initial Q3/Buy % (lower Q3/Buy is usually worse)
        buy_ratios = [int(round(p['Recommended Sell']/p['Buy Price'], 2)*100) for p in actually_sold]
        low_buy = min(buy_ratios)
        high_buy = max(buy_ratios)
        profit_ratios = [int(round(p['Profit']/p['Buy Price'], 2)*100) for p in actually_sold]
        bins = high_buy-low_buy
        stats, bin_edges, numbins = binned_statistic(buy_ratios, profit_ratios, statistic='mean', bins=bins)
        # print(stats)
        # stats[np.isnan(stats)] = 0
        # plt.bar(bin_edges[:-1], stats, width=1, align='edge')
        # plt.show()

        # Scatter: 
        plt.scatter(x=[p['Recommended Sell']/p['Buy Price'] for p in actually_sold], y=[p['Profit']/p['Buy Price']*100 for p in actually_sold])
        # plt.xlim([1,2.5])
        # plt.ylim([-5,5])
        # plt.axvline(1.30, c='k')
        # plt.axvline(1.31, c='k')
        # plt.axvline(1.32, c='k')
        # plt.axvline(1.33, c='k')
        # plt.axvline(1.34, c='k')
        # plt.axvline(1.35, c='k')
        # plt.axvline(1.40, c='k')
        # plt.axvline(1.50, c='k')
        plt.xlabel('Ratio Q3/Buy')
        plt.ylabel('Actual Profit (% above break even)')
        plt.show()

    profitAnalysisV2(phase1sell, phase2sell, phase3sell, hmeta, DBdata)

    # print('Testing for optimal strategy on given timescale...')

    # day_x = []
    # day_y = []
    # for dayregion in range(11,26):
    #     print('Testing {0}-{1} days ago...'.format(dayregion, dayregion-1))
    #     ndays_list = []
    #     net_profits = []
    #     for days_sell in range(1,11):
    #         ndays_list.append(days_sell)
    #         _, profits = BackTester(LessThanThirdQuartileHistorical,
    #                                 [dayregion,dayregion-1], days_sell, .85, [2]).runBacktest(verbose=False)
    #         net_profits.append(sum(profits))
    #     day_x.append(ndays_list)
    #     day_y.append(net_profits)
    
    # # # Figure out highest profit day model
    # # perdayprofit = [0]*len(day_y[0])
    # # for x in day_y:
    # #     highest_profit = max(x)
    # #     for i, day in enumerate(x):
    # #         perdayprofit[i] += day/highest_profit
    # # print(perdayprofit)

    # plt.xlabel('Force_liquidation_sell parameter value (days)')
    # plt.ylabel('Net $$$ profit')
    # for i, x in enumerate(day_x):
    #     plt.plot(x, day_y[i], label='Jun ' + str(16-i))
    # plt.legend(loc='upper left')
    # plt.show()

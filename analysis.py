from utility_funcs import import_json_lines # Importing logged dataset
from datetime import datetime, timedelta    # Volumetric sale filtering based on date
import json                                 # Writing and reading logged dataset

### TODO: Clean up old files; there really only should be page_gatherer, price_scanner, analysis,
###       utility_funcs, and the logfiles.
### TODO: Figure out how to do something similar to lstsq_before_hour for graphical analysis.

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

### HELPER FUNCTIONS ###

def simpleMovingAvg(dataset, n):
    if len(dataset) < n:
        return 'N is too high for this dataset (' + str(len(dataset)) + ' < ' + str(n) + ')'
    
    avg_list = []
    for i in range(0,len(dataset)-n):
        avg = sum(dataset[i:i+n])/n
        avg_list.append(avg)
    return avg_list

def removeOutliers(dataset,sigma):
    # Remove all data points that are greater than sigma away from the mean
    mean = sum(dataset)/len(dataset)
    stdev = (sum([(x-mean)**2 for x in dataset])/len(dataset))**0.5
    return [x for x in dataset if mean-sigma*stdev < x < mean+sigma*stdev]

def volumeFilter(dataset, saleslastmonth): # Run for all strategies by default
    return [x for x in dataset if len(x['Sales from last month']) >= saleslastmonth]

def profiler(items):
    # to be built later; stores all the 
    pass

########################



### ACTUAL STRATEGY ###

class simpleListingProfit:
    def __init__(self, percentage):
        self.percentage = percentage # Steam % cut on Marketplace purchases for that game. 
                                     # For CS:GO, this is 15%
    def run(self, dataset):
        outputs = []
        for item in dataset:
            itemdict = dict()
            listings = item['Listings']
            if len(listings) > 0:
                relevant_listings = sorted(listings[:2])
                ratio = relevant_listings[1]/relevant_listings[0]
                itemdict['Satisfied'] = ratio > self.percentage
                itemdict['Name'] = item['Item Name']
                itemdict['Ratio'] = ratio
            else: # Shouldn't run because volume filter, but possible
                itemdict['Satisfied'] = False
                itemdict['Name'] = item['Item Name']
                itemdict['Ratio'] = 0
            outputs.append(itemdict)
        return outputs


# [INSERT MORE HERE]

#######################

############### By way of reminder, expected format
# pagedata = {
#     'Item Name': item_name,
#     'URL': browser.current_url,
#     'Special Type': ['None','Souvenir'][item_split[0] == 'Souvenir'],
#     'Condition': ' '.join(item_split[-2:]),
#     'Sales/Day': str(round(len(recent_data)/30, 2)),
#     'Buy Rate': buy_rate,
#     'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#     'Sales from last month': str([[x[0].strftime('%Y-%m-%d %H'),x[1]] for x in recent_data]),
#     'Listings': str(itemized)
# }

if __name__ == '__main__':
    print('Doing inital dataset import...')
    DBdata = import_json_lines('pagedata.txt', encoding='utf_16', numlines=11)
    print('Successful import! Number of entries:', len(DBdata))
    DBdata = volumeFilter(DBdata, 30)
    print('Number that satisfy volume filter:', len(DBdata))

    # Testing simple listing profit
    backtest = Backtester(simpleListingProfit(1.15))
    backtest.runBacktest()
    all_results = backtest.results
    positive_results = backtest.getSatisfied()
    print('Number that satisfy simpleListingProfit:', len(positive_results))
    for satdict in positive_results:
        print(satdict)


    ### [Write your strategy backtests here]

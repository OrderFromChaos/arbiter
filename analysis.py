from utility_funcs import import_json_lines # Importing logged dataset
from datetime import datetime, timedelta    # Volumetric sale filtering based on date
import json                                 # Writing and reading logged dataset

### TODO: Clean up old files; there really only should be page_gatherer, price_scanner, analysis,
###       and the logfiles.
### TODO: Figure out how to do something similar to lstsq_before_hour for graphical analysis.

class Backtester:
    def __init__(self, methodology, inputs):
        self.methodology = methodology
        self.inputs = inputs # Should be formatted as [input1, input2, ...]
        self.results = dict()
    def runBacktest(self):
        # Logs should be in the format:
        # {satisfied: True, # if filter condition is satisfied
        #  metric1: ~number~,
        #  ...}
        global DBdata
        self.results = methodology(DBdata, *self.inputs)
    def getSatisfied(self):
        if results == dict():
            self.runBacktest()
        else:
            return [x for x in self.results if x['Satisfied']]

### HELPER FUNCTIONS ###

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

########################



### ACTUAL STRATEGY ###

# 404 not found

#######################

if __name__ == '__main__':
    DBdata = import_json_lines('pagedata.txt', encoding='utf_16', numlines=11)
    # Write your strategy backtests here
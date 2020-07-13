import pandas as pd
from datetime import datetime, timedelta
from copy import deepcopy
import matplotlib.pyplot as plt
import seaborn as sns
import statistics
from analysis import historicalSelectorDF, standardFilter, volumeFilter

GRAPH_ACTIVITY = True # Graph activity by hour
SHOW_OUTLIERS = True # Graph average distribution of outliers for all items
if SHOW_OUTLIERS:
    N_DAYS = 8

DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')
DBdata = standardFilter(DBdata)

if GRAPH_ACTIVITY:
    def convert_to_daytime_seconds(time):
        floor_time = datetime(year=time.year, month=time.month, day=time.day)
        return (time-floor_time).total_seconds()/3600

    all_seconds = []
    for i, row in DBdata.iterrows():
        history = [convert_to_daytime_seconds(x[0]) for x in row['Sales from last month']]
        all_seconds += history

    sns.distplot(all_seconds, bins=24, kde=False)
    plt.xlim([0,23])
    plt.xlabel('Hour of day, 0-23')
    plt.ylabel('Volume of sells')
    plt.show()

if SHOW_OUTLIERS:
    def convert_to_sigmas(L):
        mean = statistics.mean(L)
        std = statistics.stdev(L)
        return [(x-mean)/std for x in L]
    all_sigmas = []
    local_DBdata = deepcopy(DBdata)
    local_DBdata = historicalSelectorDF(local_DBdata, [N_DAYS, 0])
    local_DBdata = volumeFilter(local_DBdata, 10)
    for i, row in local_DBdata.iterrows():
        history = convert_to_sigmas([x[1] for x in row['Sales from last month']])
        all_sigmas += history
    sns.distplot(all_sigmas, kde=False)
    plt.xlabel('Sigmas away from mean')
    plt.xlim([-5,5])
    plt.show()
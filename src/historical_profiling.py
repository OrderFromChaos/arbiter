import pandas as pd
from datetime import datetime, timedelta
from copy import deepcopy
import matplotlib.pyplot as plt
import seaborn as sns

# Want to generate a graph of activity in the marketplace by time

DBdata = pd.read_hdf('../data/item_info.h5', 'csgo')

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
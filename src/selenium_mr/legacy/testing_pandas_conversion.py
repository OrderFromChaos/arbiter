import utility_funcs
import pandas as pd
import pandas.io.json as pdjson
import time

testing_df = pdjson.json_normalize(utility_funcs.import_json_lines('../../../../data/pagedata.txt',
                                                                   encoding='utf-8', numlines=11))
print('FIRST 10 ROWS:\n\n', testing_df.head(30))
print('TENTH ROW:\n\n', testing_df.iloc[9])


print('\n')

t0 = time.time()
testing_df.to_pickle('../../data/item_info.pkl.bz2', compression='bz2')
print('to_pickle took ' + str(time.time() - t0) + ' seconds to run with ' +
      str(testing_df.shape[0]) + ' rows.')

print('\n')

t0 = time.time()
testing_read_pickle = pd.read_pickle('../../data/item_info.pkl.bz2', compression='bz2')
print('read_pickle took ' + str(time.time() - t0) + ' seconds to run with ' +
      str(testing_df.shape[0]) + ' rows.')

print('\n')

t0 = time.time()
testing_df.to_hdf('../../data/item_info.h5', 'item_info')
print('to_hdf took ' + str(time.time() - t0) + ' seconds to run with ' +
      str(testing_df.shape[0]) + ' rows.')

print('\n')

t0 = time.time()
testing_read_hdf = pd.read_hdf('../../data/item_info.h5', 'item_info')
print('read_hdf took ' + str(time.time() - t0) + ' seconds to run with ' +
      str(testing_df.shape[0]) + ' rows.')

print('\n')



# THIS METHOD SUCKS:

t0 = time.time()
testing_df.to_msgpack('../../data/item_info.msg')
print('to_msgpack took ' + str(time.time() - t0) + ' seconds to run with ' +
      str(testing_df.shape[0]) + ' rows.')

print('\n')

t0 = time.time()
testing_read_msgpack = pd.read_msgpack('../../data/item_info.msg')
print('read_msgpack took ' + str(time.time() - t0) + ' seconds to run with ' +
      str(testing_df.shape[0]) + ' rows.')

print('\n')

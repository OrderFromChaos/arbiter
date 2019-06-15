import utility_funcs
import pandas as pd
import pandas.io.json as pdjson

testing_df = pdjson.json_normalize(utility_funcs.import_json_lines('../data/pagedata.txt',
                                                                   encoding='utf-8', numlines=11))
print('FIRST 30 ENTRIES:\n\n', testing_df.head(30))
print('TENTH ROW:\n\n', testing_df.iloc[9])

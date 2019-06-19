#!/usr/bin/env python3

import pandas as pd

def read_json(file_name):
    return pandas.read_json(file_name, date_unit='ns')

def to_json(df):
    return pandas.to_json(df)

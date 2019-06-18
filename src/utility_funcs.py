#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu
# Last Updated: June 7, 2019

import json
import datetime
import pandas as pd


def import_json_lines(filename,
                      encoding = 'utf_8',
                      numlines = 12,
                      # Config consists of names of entries and how to read them.
                      # Should always be updated to most recent version, but left here for
                      # functionality on things like mergeDatabase.
                      config = lambda pagedata: {
                        'Item Name': pagedata['Item Name'],
                        'URL': pagedata['URL'],
                        'Special Type': pagedata['Special Type'],
                        'Condition': pagedata['Condition'],
                        'Sales/Day': float(pagedata['Sales/Day']),
                        'Buy Rate': float(pagedata['Buy Rate']),
                        'Date': eval(pagedata['Date']),
                        'Sales from last month': eval(pagedata['Sales from last month']),
                        'Listings': eval(pagedata['Listings']),
                        'Listing IDs': eval(pagedata['Listing IDs'])
                      }):

    with open(filename, 'r', encoding=encoding) as f:
        data = f.readlines()
    jsondata = []
    for i in range(0, len(data)-1, numlines): # -1 as file ends in \n
        entry = '\n'.join(data[i : i + numlines])
        jsondata.append(json.loads(entry))

    # Reformat to expected objects
    newdata = [config(pagedata) for pagedata in jsondata]

    return newdata

def DBchange(entries, state, DBfile):

    """
    If state is 'add':
        directly append list of dicts to end of file
        [when using, make sure the dicts aren't already in the file]
        (page_gatherer.py would use this)
    If state is 'update':
        update (replace) entries with new list of dicts
        compares database with given entries
        would be used on price_scanner.py
    Assume entries are dicts but not yet json formatted.
    """
    # if state == "add":
    #     with open(DBfile, 'a', encoding='utf_8') as f:



    if state == 'add':
        with open(DBfile,'a', encoding='utf_8') as f:
            for entry in entries:
                # Single datetimes get converted into %Y-%m-%d %H:%M:%S for some reason.
                # This is not very easy to work with, so to decrease complexity, I just make it
                # eval()'able.
                entry['Date'] = repr(entry['Date'])

                entry['Sales from last month'] = str(entry['Sales from last month'])
                # Don't want it to spread these across multiple lines (makes parsing hard)
                entry['Listings'] = str(entry['Listings'])
                entry['Listing IDs'] = str(entry['Listing IDs'])
                # ^^ Don't want it to spread these lists across multiple lines
                # Try-except block is for extensibility
                prettyentry = json.dumps(entry, indent=4)
                f.write(prettyentry)
                f.write('\n')
    elif state == 'update':
        dataset = import_json_lines(DBfile, encoding='utf_8')
        position = [x['Item Name'] for x in dataset]
        quick_lookup = set(position)
        for entry in entries:
            entry_name = entry['Item Name']
            if entry_name in quick_lookup:
                dataset[position.index(entry_name)] = entry
        with open(DBfile, 'w'): # Clear file before writing; items will be written individually
            pass
        DBchange(dataset, 'add', DBfile)
    elif state == 'sort': # Human-compatibility; sort by lowest listing
        dataset = import_json_lines(DBfile, encoding='utf_8')
        dataset = [x for x in dataset if len(x['Listings']) > 0]
        dataset = sorted(dataset, key=lambda x: x['Listings'][0], reverse=True)
        with open(DBfile,'w'):
            pass
        DBchange(dataset, 'add', DBfile)



def jsonToDf(file_name):
    return pandas.read_json(file_name, date_unit='ns')

def dfToJson(df):
    return pandas.to_json(df, date_unit='ns')

def hdfToDf(file_name, index):
    return pd.read_hdf(file_name, index)

def dfToHdf(df, file_name, index):
    return df.to_hdf(file_name, index)

def pagedataToDf(file_name):
    data_set = utility_funcs.import_json_lines(file_name)
    return pd.json_normalize(data_set)


def mergeDatabases(old_filename,
                   oldlines,
                   oldconfig,
                   new_filename,
                   newlines,
                   newconfig,
                   optional_output=None):
    # Takes in two files and merges the database between the two
    DBold = import_json_lines(old_filename, encoding='utf_8', numlines=oldlines, config=oldconfig)
    DBnew = import_json_lines(new_filename, encoding='utf_8', numlines=newlines, config=newconfig)
    newnames = [x['Item Name'] for x in DBnew] # For indexing
    newset = set(newnames)        # Quick lookup

    ### Special code for each merge. Delete this if you're doing a new merge {
    for itemno in range(len(DBold)):
        DBold[itemno]['Listing IDs'] = []
    ### }

    ### General code
    for item in DBold:
        currname = item['Item Name']
        if currname in newset:
            newindex = newnames.index(currname)
            newmatch = DBnew[newindex]
            if item['Date'] > newmatch['Date']:
                DBnew[newindex] = item
            # Otherwise leave alone
        else:
            DBnew.append(item)

    if optional_output:
        # Create/clear optional_output file
        with open(optional_output, 'w') as f:
            pass
        DBchange(DBnew, 'add', optional_output)
    else:
        # Clear newDB file and overwrite
        with open(new_filename, 'w') as f:
            pass
        DBchange(DBnew, 'add', new_filename)

if __name__ == '__main__':
    # to_add = []
    # DBchange(to_add,'sort','../data/pagedata1.txt')
    mergeDatabases('../data/pagedata.txt', 11,
                    lambda pagedata: {
                        'Item Name': pagedata['Item Name'],
                        'URL': pagedata['URL'],
                        'Special Type': pagedata['Special Type'],
                        'Condition': pagedata['Condition'],
                        'Sales/Day': float(pagedata['Sales/Day']),
                        'Buy Rate': float(pagedata['Buy Rate']),
                        'Date': eval(pagedata['Date']),
                        'Sales from last month': eval(pagedata['Sales from last month']),
                        'Listings': eval(pagedata['Listings']) # Without listing IDs
                    },
                   '../data/utf8pagedata1.txt', 12,
                    lambda pagedata: {
                        'Item Name': pagedata['Item Name'],
                        'URL': pagedata['URL'],
                        'Special Type': pagedata['Special Type'],
                        'Condition': pagedata['Condition'],
                        'Sales/Day': float(pagedata['Sales/Day']),
                        'Buy Rate': float(pagedata['Buy Rate']),
                        'Date': eval(pagedata['Date']),
                        'Sales from last month': eval(pagedata['Sales from last month']),
                        'Listings': eval(pagedata['Listings']),
                        'Listing IDs': eval(pagedata['Listing IDs'])
                    },
                   '../data/pagedatamerge.txt')

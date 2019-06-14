#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu
# Last Updated: June 7, 2019

import json
import datetime

# def import_json_lines(filename, encoding='utf_8'):

#     """
    
#     """
#     with open(filename, 'r', encoding=encoding) as f:
#         for line in f.readlines():
            

def import_json_lines(filename, encoding='utf_16', numlines=11):
    with open(filename, 'r', encoding=encoding) as f:
        data = f.readlines()
    jsondata = []
    for i in range(0, len(data)-1, numlines): # -1 as file ends in \n
        entry = '\n'.join(data[i : i + numlines])
        jsondata.append(json.loads(entry))

    # Reformat to expected objects
    newdata = [{
        'Item Name': pagedata['Item Name'],
        'URL': pagedata['URL'],
        'Special Type': pagedata['Special Type'],
        'Condition': pagedata['Condition'],
        'Sales/Day': float(pagedata['Sales/Day']),
        'Buy Rate': float(pagedata['Buy Rate']),
        'Date': eval(pagedata['Date']),
        'Sales from last month': eval(pagedata['Sales from last month']),
        'Listings': eval(pagedata['Listings'])
    } for pagedata in jsondata]

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
    #     with open(DBfile, 'a', encoding='utf-8') as f:
            

    if state == 'add':
        with open(DBfile,'a', encoding='utf-8') as f:
            for entry in entries:
                # Single datetimes get converted into %Y-%m-%d %H:%M:%S for some reason.
                # This is not very easy to work with, so to decrease complexity, I just make it
                # eval()'able.
                entry['Date'] = repr(entry['Date'])

                entry['Sales from last month'] = str(entry['Sales from last month'])
                # Don't want it to spread these across multiple lines (makes parsing hard)
                entry['Listings'] = str(entry['Listings'])

                prettyEntry = json.dumps(entry, indent=4)
                f.write(prettyEntry)
                f.write('\n')
    elif state == 'update':
        dataset = import_json_lines(DBfile, encoding='utf_16')
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
        dataset = sorted(dataset, key=lambda x: x['Listings'][0], reverse=True)
        with open(DBfile,'w'):
            pass
        DBchange(dataset, 'add', DBfile)

if __name__ == '__main__':
    to_add = []
    DBchange(to_add,'sort','../data/pagedata.txt')

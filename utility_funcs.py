import json
import datetime

def import_json_lines(filename, encoding='utf_16', keep_as_string=False, numlines=11):
    with open(filename, 'r', encoding=encoding) as f:
        data = f.readlines()
    jsondata = []
    for i in range(0,len(data)-1,numlines): # -1 as file ends in \n
        entry = '\n'.join(data[i:i+numlines])
        jsondata.append(json.loads(entry))
    data = jsondata

    if keep_as_string:
        return data

    ############### Expected format [May not be accurate anymore]
    # pagedata = {
    #     'Item Name': item_name,
    #     'URL': browser.current_url,
    #     'Special Type': ['None','Souvenir'][item_split[0] == 'Souvenir'],
    #     'Condition': ' '.join(item_split[-2:]),
    #     'Sales/Day': str(round(len(recent_data)/30, 2)),
    #     'Buy Rate': buy_rate,
    #     'Date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #     'Sales from last month': str([[x[0].strftime('%Y-%m-%d %H'),x[1]] for x in recent_data]),
    #     'Listings': str(itemized)
    # }

    # Reformat to expected objects

    newdata = [{
        'Item Name': pagedata['Item Name'],
        'URL': pagedata['URL'],
        'Special Type': pagedata['Special Type'],
        'Condition': pagedata['Condition'],
        'Sales/Day': float(pagedata['Sales/Day']),
        'Buy Rate': float(pagedata['Buy Rate']),
        'Date': eval(pagedata['Date']) if pagedata['Date'][0] == 'd' else datetime.datetime.strptime(pagedata['Date'],'%Y-%m-%d %H:%M:%S'),
        'Sales from last month': eval(pagedata['Sales from last month']),
        'Listings': eval(pagedata['Listings'])
    } for pagedata in data]

    return newdata

def DBupdate(entries,state,DBfile):
    # If state is 'add':
    #     directly append list of dicts to end of file
    #     [when using, make sure the dicts aren't already in the file]
    #     (page_gatherer.py would use this)
    # If state is 'update':
    #     update (replace) entries with new list of dicts
    #     compares database with given entries
    #     would be used on price_scanner.py
    # Assume entries are dicts but not yet json formatted
    if state == 'add':
        with open(DBfile,'a', encoding='utf-16') as f:
            for entry in entries:
                entry['Date'] = repr(entry['Date'])
                # ^^ Single datetimes get converted into %Y-%m-%d %H:%M:%S for some reason.
                # This is not very easy to work with, so to decrease complexity, I just make it
                # eval()'able.
                entry['Sales from last month'] = str(entry['Sales from last month'])
                entry['Listings'] = str(entry['Listings'])
                # ^^ Don't want it to spread these across multiple lines (makes parsing hard)
                prettyentry = json.dumps(entry, indent=4)
                f.write(prettyentry)
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
        DBupdate(dataset, 'add', DBfile)

if __name__ == '__main__':
    # TODO: Stick tests here later
    to_add = []

    DBupdate(to_add,'update','pagedata.txt')
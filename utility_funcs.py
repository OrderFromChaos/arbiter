import json
from datetime import datetime

def readCurrency(money):
    numbers = set('0123456789.')
    if type(money) in [float, int]:
        return float(money)
    elif type(money) == str:
        money = money.strip()
        if len([x for x in money if x in numbers]) == len(money):
            return float(money)
        elif money[0] == '$':
            return float(money[1:])
        else:
            raise Exception('Unrecognized currency ' + str(repr(money)))
    else:
        raise Exception('Type must be one of [float, int, str]. Bad string: ' + str(repr(money)))

def import_json_lines(filename, encoding='utf_16', keep_as_string=False, numlines=11):
    with open(filename, 'r', encoding=encoding) as f:
        data = f.readlines()
    if numlines == 1:
        data = [json.loads(x) for x in data if x.strip() != '']
    else:
        jsondata = []
        for i in range(0,len(data),numlines): # -1 as file ends in \n
            entry = '\n'.join(data[i:i+numlines])
            if entry.strip() != '':
                jsondata.append(json.loads(entry))
        data = jsondata

    if keep_as_string:
        return data

    ############### Expected format
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

    newdata = []
    for ind, pagedata in enumerate(data):
        sales_month = eval(pagedata['Sales from last month'])
        if sales_month: # Nonzero
            if type(sales_month[0]) == list:
                sales_month = [[datetime.strptime(x[0],'%Y-%m-%d %H'),readCurrency(x[1])] for x in sales_month]
                newpagedata = {
                    'Item Name': pagedata['Item Name'],
                    'URL': pagedata['URL'],
                    'Special Type': pagedata['Special Type'],
                    'Condition': pagedata['Condition'],
                    'Sales/Day': float(pagedata['Sales/Day']),
                    'Buy Rate': readCurrency(pagedata['Buy Rate']),
                    'Date': datetime.strptime(pagedata['Date'],'%Y-%m-%d %H:%M:%S'),
                    'Sales from last month': sales_month,
                    'Listings': eval(pagedata['Listings'])
                }
                newdata.append(newpagedata)
        else:
            newpagedata = {
                'Item Name': pagedata['Item Name'],
                'URL': pagedata['URL'],
                'Special Type': pagedata['Special Type'],
                'Condition': pagedata['Condition'],
                'Sales/Day': float(pagedata['Sales/Day']),
                'Buy Rate': readCurrency(pagedata['Buy Rate']),
                'Date': datetime.strptime(pagedata['Date'],'%Y-%m-%d %H:%M:%S'),
                'Sales from last month': sales_month,
                'Listings': eval(pagedata['Listings'])
            }
            newdata.append(newpagedata)

    return newdata
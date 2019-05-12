import json
from datetime import datetime

class Currency:
    def __init__(self,amount):
        numbers = set('0123456789.')
        if type(amount) in [float, int]:
            self.value = float(amount)
            self.type = 'USD'
        elif type(amount) == str:
            if len([x for x in amount if x in numbers]) == len(amount):
                self.value = float(amount)
                self.type = 'USD'
            elif amount[0] == '$':
                self.value = float(amount[1:])
                self.type = 'USD'
            else:
                raise Exception('Unrecognized currency ' + str(repr(amount)))
        else:
            raise Exception('Type must be one of [float, str]. Bad string: ' + str(repr(amount)))
    def __add__(self, other):
        if self.type == other.type:
            return self.value + other.value
        else:
            raise Exception('Unable to add two non-USD currencies')
    def __float__(self):
        return self.value

def import_json_lines(filename, encoding='utf_16', keep_nontimed_salehistory=True):
    with open(filename, 'r', encoding=encoding) as f:
        data = f.readlines()
    data = [json.loads(x) for x in data if x.strip() != '']

    # Expected format
    # pagedata = {
    #     'Item Name': item_name,
    #     'URL': browser.current_url,
    #     'Special Type': ['None','Souvenir'][item_split[0] == 'Souvenir'],
    #     'Condition': ' '.join(item_split[-2:]),
    #     'Sales/Day': str(round(len(recent_data)/30, 2)),
    #     'Buy Rate': buy_rate,
    #     'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #     'Sales from last month': str([[x[0].strftime('%Y-%m-%d'),x[1]] for x in recent_data]),
    #     'Listings': str(itemized)
    # }
    # Note that recent_data is a list of [[date, sale price],...] or a list of [sale price, ...] so you have to support both

    newdata = []
    for ind, pagedata in enumerate(data):
        sales_month = eval(pagedata['Sales from last month'])
        if keep_nontimed_salehistory:
            if sales_month: # Nonzero
                if type(sales_month[0]) == list:
                    sales_month = [[datetime.strptime(x[0],'%Y-%m-%d'),Currency(x[1])] for x in sales_month]
                if type(sales_month[0]) in [float, int]:
                    sales_month = [Currency(x) for x in sales_month]
                else:
                    raise Exception('Something weird happened in importing sales from a previous month')
            newpagedata = {
                'Item Name': pagedata['Item Name'],
                'URL': pagedata['URL'],
                'Special Type': pagedata['Special Type'],
                'Condition': pagedata['Condition'],
                'Sales/Day': float(pagedata['Sales/Day']),
                'Buy Rate': Currency(pagedata['Buy Rate']),
                'Date': datetime.strptime(pagedata['Date'],'%Y-%m-%d %H:%M:%S'),
                'Sales from last month': sales_month,
                'Listings': eval(pagedata['Listings'])
            }
            newdata.append(newpagedata)
        else:
            if sales_month: # Nonzero
                if type(sales_month[0]) == list:
                    sales_month = [[datetime.strptime(x[0],'%Y-%m-%d'),Currency(x[1])] for x in sales_month]
                    newpagedata = {
                        'Item Name': pagedata['Item Name'],
                        'URL': pagedata['URL'],
                        'Special Type': pagedata['Special Type'],
                        'Condition': pagedata['Condition'],
                        'Sales/Day': float(pagedata['Sales/Day']),
                        'Buy Rate': Currency(pagedata['Buy Rate']),
                        'Date': datetime.strptime(pagedata['Date'],'%Y-%m-%d %H:%M:%S'),
                        'Sales from last month': sales_month,
                        'Listings': eval(pagedata['Listings'])
                    }
                    newdata.append(newpagedata)

    return newdata
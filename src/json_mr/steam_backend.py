from selenium import webdriver
import pandas as pd
import time
import json

allquery = 'https://steamcommunity.com/market/search/render/?category_730_ItemSet&appid=730&norender=1&category_730_Exterior%5B%5D=tag_WearCategory0&count=100&start='
history_query = 'https://steamcommunity.com/market/pricehistory/?country=US&currency=3&appid=440&market_hash_name=Specialized%20Killstreak%20Brass%20Beast'

firstrun = True
all_items_reached = False
startloc = 0
results = []
browser = webdriver.Chrome()
find_xpath = browser.find_element_by_xpath
while not all_items_reached:
    # page = requests.get(allquery + str(startloc))
    # text = html.fromstring(page.content).xpath('text()')[0]
    # print(text)
    browser.get(allquery + str(startloc))
    text = find_xpath('//body').text
    # print(text)
    response = json.loads(text)
    # print(response)
    success = response['success']
    if success == True:
        print('Got json at:', startloc)
    else:
        print('Uh oh, pull failure:', success)
        raise Exception
    results += response['results']

    if firstrun:
        size = response['total_count']
        firstrun = False
    
    startloc += 100
    if startloc > size:
        break
    time.sleep(4)

for i, item in enumerate(results):
    results[i] = {'name': item['name'],
                  'sell_price': item['sell_price'],
                  'sell_listings': item['sell_listings']}
data = pd.DataFrame(results)

data.to_hdf('../../data/global_pricing.h5', 'csgo')

# important stuff per item:
# 'name'
# 'sell_price'
# 'sell_listings'

# print(type(data))
# for i in data['results']:
#     print(i['name'], round(i['sell_price']/100,2))

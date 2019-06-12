# from selenium import webdriver              # Primary navigation of Steam price data.
# from selenium.common.exceptions import NoSuchElementException 
                                            # ^^ Dealing with page load failure.
from bs4 import BeautifulSoup
import time                                 # Waiting so no server-side ban
import json                                 # Writing and reading logged dataset

with open('userid_html.html','r') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

priceraw = [x for x in soup.find_all('span', class_='market_listing_price market_listing_price_with_fee')]
prices = []
for i in priceraw:
    prices.append(i.get_text().strip())

idraw = soup.find_all('a')
ids = []
for i in idraw:
    found = i.get('id')
    if found:
        ids.append(found.split('_')[1])

prices, ids = list(zip(*[(x,y) for x,y in zip(prices, ids) if x != 'Sold!']))
print(prices) 
print(ids)

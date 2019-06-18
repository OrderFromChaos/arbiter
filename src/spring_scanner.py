#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### PURPOSE:
### This code scans over Spring-satisfying items, defined in analysis.py


### External Libraries
from selenium import webdriver              # Primary navigation of Steam price data.
from selenium.common.exceptions import NoSuchElementException 
                                            # ^^ Dealing with page load failure.
import pandas as pd                         # Primary dataset format

### Standard libraries
import time                                 # Waiting so no server-side ban

### Local Functions
from analysis import SpringSearch           # Filter before scanning
from analysis import LessThanThirdQuartileHistorical 
                                            # Notify of buy-worthy things while running
from browse_itempage import browseItempage  # Scrapes data from Steam item pages
from browse_itempage import WaitUntil       # Implements standard page waits in with block
from browse_itempage import steamLogin      # Make code more readable


### Hyperparameters {
navigation_time = 6 # Global wait time between page loads
username = 'datafarmer001'
password = 'u9hqgi3sl9'
startloc = 0 # Item in database to start price scanning from
nloops = 10
### }


if __name__ == '__main__':
    DBdata = import_json_lines('../data/pagedata.txt',encoding='utf_16')
    of_interest = [x for x in DBdata if volumeFilter(x,30)]
    of_interest = [x for x in of_interest if SpringSearch.runIndividual(x)['Satisfied']]
    of_interest = of_interest[startloc:] # See hyperparams for startloc
    assert len(of_interest) >= 10, ('price_scanner.py will not write if the volume filtered dataset'
                                    'is smaller than 10. Current size' + str(len(of_interest)))
    browser = webdriver.Chrome(r'/home/order/Videos/chromedriver/chromedriver') # Linux
    find_css = browser.find_element_by_css_selector

    # Login
    login_url = r'https://store.steampowered.com//login/'
    browser.get(login_url)
    time.sleep(3)
    username_box = find_css('#input_username')
    password_box = find_css('#input_password')
    username_box.send_keys(username)
    time.sleep(1)
    password_box.send_keys(password)
    time.sleep(3)
    sign_in = find_css('#login_btn_signin > button')
    sign_in.click()

    # Since we're using a verified account, need to have human fill out 2FA
    # Currently locked to my phone
    with waitUntil(navigation_time):
        code_confirmation = input('Did you enter your Steam confirmation code? [y\\n]')
        if code_confirmation not in ['y','Y','yes','Yes','yep']:
            raise Exception('Well why didn\'t you??')

    to_write = [] # Item data to be updated in database
    for iterator in range(nloops):
        for itemno, item in enumerate(of_interest):
            browser.get(item['URL'])
            with waitUntil(navigation_time):
                browser.implicitly_wait(15)
                try:
                    full_listing = find_css('#searchResultsRows').text
                except NoSuchElementException:
                    browser.refresh()
                    time.sleep(navigation_time*2)
                    full_listing = find_css('#searchResultsRows').text
                itemized = cleanListing(full_listing,item['Item Name'])
                try:
                    buy_rate = readUSD(find_css('#market_commodity_buyrequests > '
                                                    'span:nth-child(2)').text)
                    # ^^ Highest buy order currently on the market. 
                    # If a price drops below this, it will immediately be purchased by the buy orderer.
                except NoSuchElementException:
                    buy_rate = 0 # Sometimes there are no buy orders
                
                # Grab volumetric data for recent sales/prices (from chart).
                volumetrics = find_css('body > div.responsive_page_frame.with_header > div.responsive_page_content > div.responsive_page_template_content')
                recent_data = cleanVolumetric(volumetrics.get_attribute('outerHTML'))
                
                pagedata = {
                    'Item Name': item['Item Name'],
                    'URL': browser.current_url, # In case they update the URL and leave a redirect
                    'Special Type': item['Special Type'],
                    'Condition': item['Condition'],
                    'Sales/Day': round(len(recent_data)/30, 2),
                    'Buy Rate': buy_rate,
                    'Date': datetime.now(),
                    'Sales from last month': recent_data,
                    'Listings': itemized
                }

                to_write.append(pagedata)
                
                if itemized: # Nonempty
                    satcheck = LessThanThirdQuartileHistorical.runindividual(pagedata)
                    if satcheck['Satisfied']:
                        print('!!!!', 'Found a Q3 satisfying item')
                        print(satcheck)
                

                print('    ' + str(itemno+1) + '.', item['Item Name'], itemized[0], pagedata["Sales/Day"])

                # Update pagedata file every 10 items
                if (itemno + 1)%10 == 0:
                    DBchange(to_write,'update','../data/pagedata.txt')
                    to_write = []
                    print('    [WROTE TO FILE.]')
                    print()
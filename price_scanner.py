#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu
# Last Updated: June 2, 2019

### PURPOSE:
### This code scans over already found URLs for arbitrage opportunities.

from selenium import webdriver              # Primary navigation of Steam price data. Used for login.
from selenium.common.exceptions import NoSuchElementException # Used for the occasional page load failure.
import time                                 # Page waits
from datetime import datetime, timedelta    # Volumetric sale filtering based on date
import json                                 # Data logging - update database
from utility_funcs import readCurrency      # " $27.45" -> 27.45
from utility_funcs import import_json_lines # Importing logged dataset
# from analysis import ---- # Later include things like SMA here

### Hyperparameters {
navigation_time = 6 # Global wait time between page loads
username = 'datafarmer001'
password = 'u9hqgi3sl9'
### }

# -----------------------------------====Data Cleaning Functions====-----------------------------------
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def cleanListing(mess,itemname):
    ### Sometimes Steam will dynamically show "Sold!" or the like when it sells at item. This prevents the parser from stumbling
    mess = mess.split('\n')
    # Does this instead of a spacing-based system because 'Sold!' changes the spacing.
    disallowed = ['PRICE','SELLER','NAME','Sold!','Buy Now','Counter-Strike: Global Offensive',itemname]
    numbers = set('0123456789.')
    return sorted([float(''.join([char for char in x if char in numbers])) for x in mess if x not in disallowed])

def cleanVolumetric(data):
    # Parses data from the price chart on an item listing
    data = data[data.find('var line1')+10:data.find(']];')+2] # Gets all price data from chart
    if data == '': # No recent prices - rarely sold item
        return []
    better_data = eval(data) # JS has the same format lists as Python, so eval is fine
    better_data = [[x[0][:3],x[0][4:6],x[0][7:11],x[0][12:14],x[1]] for x in better_data] # Cuts date info into easily accessible bits
    month_lookup = {'Jan': 1, 'Feb': 2, 'Mar': 3,
                    'Apr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9,
                    'Oct': 10, 'Nov': 11, 'Dec': 12}
    better_data = [[datetime(year=int(x[2]),month=month_lookup[x[0]],day=int(x[1]), hour=int(x[3])),x[4]] for x in better_data]

    # Cuts data to recent data (within last 30 days of sales)
    last_month = datetime.now() - timedelta(days=30)
    now = datetime.now()
    recent_data = [x for x in better_data if last_month < x[0] < now]
    
    return recent_data

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# -----------------------------------===============================-----------------------------------

def sma(dataset, n):
    if len(dataset) < n:
        return 'N is too high for this dataset (' + str(len(dataset)) + ' < ' + str(n) + ')'
    
    avg_list = []
    for i in range(0,len(dataset)-n):
        avg = sum(dataset[i:i+n])/n
        avg_list.append(avg)
    return avg_list

def remove_outliers(dataset,sigma):
    # Remove all data points that are greater than sigma away from the mean
    mean = sum(dataset)/len(dataset)
    stdev = (sum([(x-mean)**2 for x in dataset])/len(dataset))**0.5
    return [x for x in dataset if mean-sigma*stdev < x < mean+sigma*stdev]






DBdata = import_json_lines('pagedata.txt',encoding='utf_16',numlines=11)
DBdata_names = [x['Item Name'] for x in DBdata]
ignore_pages = set([x['Item Name'] for x in DBdata if x['Sales/Day'] < 1 or ( x['Buy Rate'] > x['Listings'][0]/1.15 ) ])

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

### Since we're using a verified account
confirm_start = time.time()
code_confirmation = input('Did you enter your Steam confirmation code? [y\\n]')
if code_confirmation not in ['y','Y','yes','Yes','yep']:
    raise('Well why didn\'t you??')

confirm_time = time.time()-confirm_start
if confirm_time < navigation_time:
    time.sleep(navigation_time-confirm_time)

itemno = 0 # Initialization
page_direction = [-1,1][initial_page < final_page] # Automatically sets page traversal page_direction
# Switching directory pages
for pageno in range(initial_page, final_page+page_direction ,page_direction):
    print('----------Page Number: ' + str(pageno) + ' ----------')
    page_url = general_url + str(pageno) + '_price_desc'
    # Navigating for items on each directory page
    skipped_item = False
    for directorypage in range(10):
        browser.get(page_url)
        
        if not skipped_item:
            time.sleep(2) # Wait for selenium element database to get updated
        skipped_item = False
        browser.implicitly_wait(30)
        # This is where the page occasionally doesn't load, 
        # so if it gets an exception, it'll just refresh.
        try:
            current_item = find_css('#result_' + str(directorypage))
        except NoSuchElementException:
            browser.get(page_url)
            time.sleep(navigation_time*2)
            browser.implicitly_wait(10)
            current_item = find_css('#result_' + str(directorypage))
        
        # Get item name, then go to page
        item_name = current_item.text
        item_name = item_name.split('\n')[3]
        if item_name not in ignore_pages:
            time.sleep(navigation_time)
            current_item.click()
            
            before_price_data = time.time()
            
            # Get price data
            browser.implicitly_wait(15)
            try:
                full_listing = find_css('#searchResultsRows').text
            except NoSuchElementException:
                browser.refresh()
                time.sleep(5)
                full_listing = find_css('#searchResultsRows').text
            itemized = cleanListing(full_listing,item_name)
            try:
                buy_rate = find_css('#market_commodity_buyrequests > span:nth-child(2)').text
            except NoSuchElementException:
                browser.refresh()
                time.sleep(10)
                buy_rate = find_css('#market_commodity_buyrequests > span:nth-child(2)').text
            # print(str(itemno) + '. ' + item_name)
            # print('  ', end = '')
            # print(itemized)
            itemno += 1
            
            # Grab volumetric data for recent sales/prices (from chart).
            volumetrics = find_css('body > div.responsive_page_frame.with_header > div.responsive_page_content > div.responsive_page_template_content')
            recent_data = cleanVolumetric(volumetrics.get_attribute('outerHTML'))
            # print('Recent prices:', recent_prices)
            
            item_split = item_name.split(' ')
            pagedata = {
                'Item Name': item_name,
                'URL': browser.current_url,
                'Special Type': ['None','Souvenir'][item_split[0] == 'Souvenir'],
                'Condition': ' '.join(item_split[-2:]),
                'Sales/Day': str(round(len(recent_data)/30, 2)),
                'Buy Rate': buy_rate,
                'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Sales from last month': str([[x[0].strftime('%Y-%m-%d %H'),x[1]] for x in recent_data]),
                'Listings': str(itemized)
            }

            if pagedata['Item Name'] not in DBdata_names:
                DBdata.append(pagedata)
                DBdata_names.append(pagedata['Item Name'])
            else:
                DBdata[DBdata_names.index(pagedata['Item Name'])] = pagedata
                print('    ', 'Sucessfully updated some old data!')
            
            # if len(itemized) > 4: # Technically only > 1 is needed, but I don't want to waste my time with inefficient pricing
            #     prettyjson = json.dumps(pagedata, indent=4)
            #     if itemized[0]*1.16 < itemized[1]: # and float(pagedata['Sales/Day']) > 1:
            #         print('        ','FOUND A SIMPLE BUYABLE ITEM @',round((itemized[1]/itemized[0]-1.15)*itemized[1],2),'%')
                    # with open('buyable_simple.txt','a', encoding='utf-16') as f:
                    #     f.write(prettyjson)
                    #     f.write('\n')
            if recent_data: # Nonzero
                sales = remove_outliers([x[1] for x in recent_data],1)
                if len(sales) > 15:
                    recentsales = sales[-7:]
                    prediction = sum(recentsales)/len(recentsales)
                    expected_profit = prediction/1.15 - itemized[0]
                    if expected_profit > itemized[0]*-.05:
                        # print('        ','Expected profit: $',round(expected_profit,2))
                        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                        pagedata['Recent Month Data'] = recentsales
                        pagedata['Prediction'] = prediction
                        prettyjson = json.dumps(pagedata, indent=4)
                        with open('buyable_complex.txt','a', encoding='utf-16') as f:
                            f.write(prettyjson)
                            f.write('\n')
                    print('    ' + str(itemno) + '.', item_name, itemized[0], pagedata["Sales/Day"], round(expected_profit,2))
                    
                else:
                    print('    ' + str(itemno) + '.', item_name, itemized[0], pagedata["Sales/Day"],'NESTP')
            else:
                print('    ' + str(itemno) + '.', item_name, itemized[0], pagedata["Sales/Day"],'NESTP')
            
            price_elapsed = time.time() - before_price_data
            
            if price_elapsed < navigation_time: # No reason to wait if processing the price data already took awhile
                time.sleep(navigation_time-price_elapsed)
        else:
            print('    ','Ignored',item_name)
            skipped_item = True
            pagedata = DBdata[DBdata_names.index(item_name)]
            
    
    browser.get(page_url)
    
    start_write = time.time()
    # Rewrite file at the end of every page (so every 30 seconds or so)
    with open('pagedata.txt','w',encoding='utf_16') as f:
        pass
    for pagedata in DBdata:
        if pagedata['Sales from last month']:
            if type(pagedata['Sales from last month'][0][0]) == type(datetime(2017,9,17)):
                pagedata['Sales from last month'] = str([[x[0].strftime('%Y-%m-%d %H'),x[1]] for x in pagedata['Sales from last month']])
        stringified = {x:str(pagedata[x]) for x in pagedata}
        prettyjson = json.dumps(stringified, indent=4)
        with open('pagedata.txt','a',encoding='utf_16') as f:
            f.write(prettyjson)
            f.write('\n')

    time.sleep(navigation_time-(time.time()-start_write))
    if page_direction == -1:
        arrow = find_css('#searchResults_btn_prev')
    if page_direction == 1:
        arrow = find_css('#searchResults_btn_next')
    arrow.click()

    print()


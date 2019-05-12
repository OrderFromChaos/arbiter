#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu
# Last Updated: May 11, 2019
#################### Last page stopped: 49


### TODO:
### Implement better fault tolerance for "NoSuchElementException"
### Implement "market disruption" indication based on distribution of prices
### Implement predictions of profit based on previous value
### Change find_css to account for nosuchelementexception

from selenium import webdriver              # Primary navigation of Steam price data. Used for login.
from selenium.common.exceptions import NoSuchElementException # Used for the occasional page load failure.
import time                                 # Treating Steam right (also not being kicked out)
import math                                 # For math.floor() and math.ceil()s
import sys                                  # Input pages from command line
from datetime import datetime, timedelta    # Non jury-rigged dates for volumetric sales
                                            # The intention is to only use items that turn over at LEAST daily
import json                                 # Data logging
from utility_funcs import Currency, import_json_lines

### Hyperparameters {
general_url = 'https://steamcommunity.com/market/search?q=&category_730_ItemSet%5B%5D=any&category_730_ProPlayer%5B%5D=any&category_730_StickerCapsule%5B%5D=any&category_730_TournamentTeam%5B%5D=any&category_730_Weapon%5B%5D=any&category_730_Exterior%5B%5D=tag_WearCategory0&appid=730#p'
initial_page = int(sys.argv[1]) # 40
final_page = int(sys.argv[2]) # 70 # Inclusive
navigation_time = 5 # Global wait time between page loads
username = 'datafarmer001'
password = 'u9hqgi3sl9'
### }

# Automatically sets page traversal page_direction
page_direction = [-1,1][initial_page < final_page]

# -----------------------------------====Primary Functions====-----------------------------------
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def cleanListing(mess,itemname):
    ### Sometimes Steam will dynamically show "Sold!" or the like when it sells at item. This prevents the parser from stumbling
    mess = mess.split('\n')
    # Does this instead of a spacing-based system because 'Sold!' changes the spacing.
    disallowed = ['PRICE','SELLER','NAME','Sold!','Buy Now','Counter-Strike: Global Offensive',itemname]
    numbers = set('0123456789.')
    return sorted([float(''.join([char for char in x if char in numbers])) for x in mess if x not in disallowed])

def cleanChart(data):
    ### According to year-ago me, this is apparently non-functional. I'm guessing it's missing a metric for volume evaluations.
    
    # Parses data from the price chart on an item listing
    data = data[data.find('var line1')+10:data.find(']];')+2] # Gets all price data from chart
    if data == '': # No recent prices - rarely sold item
        return []
    better_data = eval(data) # JS has the same format lists as Python, so eval is fine
    print(better_data)
    better_data = [[x[0][:3],x[0][4:6],x[0][7:11],x[1]] for x in better_data] # Cuts date info into easily accessible bits
    month_lookup = {'Jan': 1,
                    'Feb': 2,
                    'Mar': 3,
                    'Apr': 4,
                    'May': 5,
                    'Jun': 6,
                    'Jul': 7,
                    'Aug': 8,
                    'Sep': 9,
                    'Oct': 10,
                    'Nov': 11,
                    'Dec': 12}
    better_data = [[datetime(year=int(x[2]),month=month_lookup[x[0]],day=int(x[1])),x[3]] for x in better_data]

    # Cuts data to recent data (within last 30 days of sales)
    last_month = datetime.now() - timedelta(days=30)
    now = datetime.now()
    recent_data = [x for x in better_data if last_month < x[0] < now]
    # recent_prices = [x[1] for x in recent_data]
    
    return recent_data

maindata = import_json_lines('pagedata.txt',utf_16=True)
maindata_names = [x['Item Name'] for x in maindata]
ignore_pages = set([x['Item Name'] for x in maindata if x['Sales/Day'] < 1 or ( x['Buy Rate'] >= x['Listings'][0]/1.15 ) ])

browser = webdriver.Chrome(r'/home/order/Videos/chromedriver/chromedriver') # Linux
find_css = browser.find_element_by_css_selector

# Login
login_url = r'https://store.steampowered.com//login/'
browser.get(login_url)
time.sleep(3)
username_box = find_css('#input_username')
password_box = find_css('#input_password')
username_box.send_keys(username)
password_box.send_keys(password)

time.sleep(1)

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
            
            # Grab volumetric data for recent sales/prices (from chart). Fortunately already in USD.
            # Ignoring these for now since the rest runs stably
            volumetrics = find_css('body > div.responsive_page_frame.with_header > div.responsive_page_content > div.responsive_page_template_content')
            recent_data = cleanChart(volumetrics.get_attribute('outerHTML'))
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
                'Sales from last month': str([[x[0].strftime('%Y-%m-%d'),x[1]] for x in recent_data]),
                'Listings': str(itemized)
            }

            print('    ' + str(itemno) + '.', item_name, itemized[0], pagedata["Sales/Day"])
            
            if pagedata['Item Name'] not in maindata_names:
                maindata.append(pagedata)
                maindata_names.append(pagedata['Item Name'])
            else:
                print('Sucessfully updated some old data!')
                maindata[maindata_names.index(pagedata['Item Name'])] = pagedata
            
            if len(itemized) > 4: # Technically only > 1 is needed, but I don't want to waste my time with inefficient pricing
                prettyjson = json.dumps(pagedata)
                if itemized[0]*1.16 < itemized[1]: # and float(pagedata['Sales/Day']) > 1:
                    print('        ','FOUND A SIMPLE BUYABLE ITEM @',round((itemized[1]/itemized[0]-1.15)*itemized[1],2),'%')
                    with open('buyable_simple.txt','a', encoding='utf-16') as f:
                        f.write(prettyjson)
                        f.write('\n')
            
            price_elapsed = time.time() - before_price_data
            
            if price_elapsed < navigation_time: # No reason to wait if processing the price data already took awhile
                time.sleep(navigation_time-price_elapsed)
        else:
            skipped_item = True
    
    browser.get(page_url)
    
    start_write = time.time()
    # Rewrite file at the end of every page (so every 30 seconds or so)
    with open('pagedata.txt','w',encoding='utf_16') as f:
        pass
    for pagedata in maindata:
        prettyjson = json.dumps(pagedata) # Had to remove indent=4 for reading the file later
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


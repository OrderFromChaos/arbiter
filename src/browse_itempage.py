from selenium import webdriver              # Primary navigation of Steam price data.
from selenium.common.exceptions import NoSuchElementException 
                                            # ^^ Dealing with page load failure.
from bs4 import BeautifulSoup               # Reading prices and seller ID from page
import time                                 # Waiting so no server-side ban
from datetime import datetime, timedelta    # Volumetric sale filtering based on date

def readUSD(dollars):
    numbers = set('0123456789.')
    return float(''.join([x for x in dollars if x in numbers]))

def cleanListing(html):
    ### Get prices from html output from #searchresultsrows
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

    # The following line filters out any items which say 'Sold!', which is a dynamic updating
    # thing that sometimes happens during data pull.
    # It also sorts listings; sometimes Steam displays them out of order.
    # list(zip(*n)) does [(a1,b1),...] -> [[a1, a2, ...], [b1, b2, ...]]
    prices, ids = list(zip(*sorted([(readUSD(x),y) for x,y in zip(prices, ids) if x != 'Sold!'], key = lambda x: x[0])))
    return prices, ids

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

class WaitUntil():
    # Enforces that everything inside a "with WaitUntil(10):" block waits 10 seconds to complete
    # For more info, see https://jeffknupp.com/blog/2016/03/07/python-with-context-managers/
    def __init__(self, lengthwait):
        self.start = 0
        self.lengthwait = lengthwait
    def __enter__(self):
        self.start = time.time()
        return self.start
    def __exit__(self, *args):
        elapsed = time.time() - self.start
        if elapsed < self.lengthwait:
            time.sleep(self.lengthwait-elapsed)

def browseItempage(browser, item, navigation_time, firstscan=False):
    # Input: Browser currently on item page, item obj
    # Output: Browser still on item page, pagedata dict (scraped info)
    find_css = browser.find_element_by_css_selector
    haslistings = True

    try:
        find_css('#message > h3') # Sorry! You've made too many requests recently. Please wait and...
        raise Exception('CRITICAL: Server temp-banned you based on request freqency. Turn up selenium_loadtime.')
    except NoSuchElementException:
        pass

    try:
        prices_element = find_css('#searchResultsRows')
    except NoSuchElementException:
        browser.refresh()
        time.sleep(navigation_time*2)
        try:
            prices_element = find_css('#searchResultsRows')
        except NoSuchElementException:
            # Probably no items
            haslistings = False
    
    if haslistings:
        itemized, IDs = cleanListing(prices_element.get_attribute('outerHTML'))
    else:
        itemized, IDs = ([], [])
    
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
    
    pagedata = dict()
    if firstscan:
        name = item['Item Name']
        pagedata['Item Name'] = name
        pagedata['Special Type'] = [0, 1][name.split(' ')[0] == 'Souvenir']
        # TODO: This fails for anything b4 the implementation of item conditions ex:
        # https://steamcommunity.com/market/listings/730/%E2%98%85%20Navaja%20Knife
        raw_condition_name =  name.split('(')[-1][:-1]
        to_num = {
            'Factory New': 0,
            'Minimal Wear': 1,
            'Field-Tested': 2,
            'Well-Worn': 3,
            'Battle-Scarred': 4
        }
        pagedata['Condition'] = to_num(raw_condition_name)
    else:
        pagedata['Item Name'] = item['Item Name']
        pagedata['Special Type'] = item['Special Type']
        pagedata['Condition'] = item['Condition']

    pagedata['Sales/Day'] = round(len(recent_data)/30, 2)
    pagedata['Buy Rate'] = buy_rate
    pagedata['Date'] = datetime.now()
    pagedata['Sales from last month'] = recent_data
    pagedata['Listings'] = itemized

    return browser, pagedata

def steamLogin(browser, username, password, navigation_time):
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
    with WaitUntil(navigation_time):
        code_confirmation = input('Did you enter your Steam confirmation code? [y\\n] ')
        if code_confirmation not in ['y','Y','yes','Yes','yep']:
            raise Exception('Well why didn\'t you??')
    
    return browser
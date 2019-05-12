# encoding: utf-8? whatever allows for currency symbols

# Author: Syris Norelli, snore001@ucr.edu
# Last Updated: July 2018

### TODO:
### Implement better fault tolerance for "NoSuchElementException"
### Implement "market disruption" indication based on distribution of prices
### Implement predictions of profit based on previous value

from selenium import webdriver              # Primary navigation of Steam price data. Used for login.
from selenium.common.exceptions import NoSuchElementException # Used for the occasional page load failure.
import time                                 # Treating Steam right (also not being kicked out)
import math                                 # For math.floor() and math.ceil()s
import sys                                  # Input pages from command line

### With a USD account, currency conversion isn't a thing that needs to be done.
# Leaving in for legacy stuff - shouldn't hurt runtime, just a second on startup
import requests                             # Used for Bloomberg currency requests
from lxml import html                       # Used for Bloomberg currency requests


### Hyperparameters
# Name without page number or direction info
general_url = 'https://steamcommunity.com/market/search?q=&category_730_ItemSet%5B%5D=any&category_730_ProPlayer%5B%5D=any&category_730_StickerCapsule%5B%5D=any&category_730_TournamentTeam%5B%5D=any&category_730_Weapon%5B%5D=any&category_730_Exterior%5B%5D=tag_WearCategory0&appid=730#p'
initial_page = int(sys.argv[1]) # 40
final_page = int(sys.argv[2]) # 70 # Inclusive
navigation_time = 5 # Global wait time between page loads
username = 'datafarmer001'
password = 'u9hqgi3sl9'

# Automatically sets page traversal direction
adder = 0
if initial_page < final_page:
    adder = 1
else:
    adder = -1
currency_rates = {'USD': 1} # Legacy initialization, leaving it in since it's harmless
       # Dictionary of currency conversions; updated by toUSD()

# -----------------------------------====Primary Functions====-----------------------------------
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

# Import data cleaning functions ---------------------------------------------

def cleanListing(mess,itemname):
    ### Sometimes Steam will dynamically show "Sold!" or the like when it sells at item. This prevents the parser from stumbling
    mess = mess.split('\n')
    # Does this instead of a spacing-based system because 'Sold!' changes the spacing.
    disallowed = ['PRICE','SELLER','NAME','Sold!','Buy Now','Counter-Strike: Global Offensive',itemname]
    return [x for x in mess if x not in disallowed]

def cleanName(name):
    ### Legacy helper for a list comprehension
    # (I don't want to have to rewrite a year-old data parser, so this is staying in)
    return name.split('\n')[3]

def cleanChart(data):
    ### According to year-ago me, this is apparently non-functional. I'm guessing it's missing a metric for volume evaluations.
    
    # Parses data from the price chart on an item listing
    data = data[data.find('var line1')+10:data.find(']];')+2] #Gets all price data from chart
    better_data = eval(data) # JS has the same format lists as Python, so eval is fine
    better_data = [[x[0][:3],x[0][4:6],x[0][7:11],x[1]] for x in better_data] # Cuts date info into easily accessible bits
    
    # Cuts data to recent data (within last month of sales)
    month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']    
    current_month = month[int(time.strftime('%m'))-1]
    prev_month = month[int(time.strftime('%m'))-2] # Never used??
    recent_data = [x for x in better_data if x[0] == current_month and x[2] == time.strftime('%Y')]
    recent_prices = [x[3] for x in recent_data]
    
    # print('Number of recent sales: ' + str(len(recent_data)) + ' (' + "%.2f" % (len(recent_data)/int(time.strftime('%d'))) + ' per day on average)')
    # print('Average recent sale price: ' + "%.2f" % average(previous_prices))
    # print('Average median sale price: ' + "%.2f" % median(previous_prices))
    
    mean = lambda x: sum(x)/len(x)
    stdev = lambda x: (sum([(mean(x)-y)**2 for y in x])/(len(x)-1))**0.5
    try:
        potential = mean(recent_prices)
        return potential, stdev(recent_prices)
    except ZeroDivisionError:
        return 0,0 # No point trying to buy an item that doesn't turn over within a month

def cleanCommas(val, case):
    ### Helper function for arbitrary prices
    # Basically built to format the prices for the number cutout.
    val = val.replace(' ', '') #Necessary for cases >=3.
    if case == 0:
        return val #No need to add case for commas since number cutout works without cutting
    if case == 1:
        return val.replace(',','.')
    if case == 2: #Specifically for Rubles (683,99 pуб.)
        val = val[:len(val)-2] #To cut out last '.'
        return val.replace(',','.')
    if case == 3: #Specifically for Indonesian Rupees (Rp 185 500)
        #Also, seriously, who fucked up on Steam's backend? Bloomberg's?
        return val[:2] + str(float(val[2:])/100)
    if case == 4: #For Korean Won (Bloomberg has inaccurate values)
        #The value is off by 100, so I'll just simply divide by 100.
        val = val.replace(',', '')                  #    ₩ 15,202.21
        return val[:1] + str(float(val[1:])/100)
    if case == 5: #For Vietnamese Dong (550.450,18₫)
        return val.replace('.','').replace(',','.')

def toUSD(prices, condition): # Condition is for bug checking; set to 1 just return currency table.
    ### Initially, this was very long because I was trying to use a non-authenticated account.
    ### This is unnecessary. Now everything is in USD, but this function is left in so stuff doesn't break.
    ### You may skip down to ############# [[[[[[[SKIP TO HERE]]]]]]] ############# to read through the functional portion of the code.

    usd_prices = []
    
    ### Data format for currency_cases:
    # [read_direction, position, symbol, standard_currency_value, commas]
    # read_direction: 0 for forward reading, 1 for backwards reading
    # position: index of key symbol
    # symbol: symbol you're looking for (eg '$')
    # standard_currency_value: three-character string used by other currency sources (eg 'USD')
    #     ^^ This is so it can be looked up at the time of running
    # commas: what to do about commas. 0 = nothing, 1 = replace with periods, else = exotic
    
    # Example:
    # [0, 0, '$', 'USD', 0]
    
    # Using the above method, here's the parse settings for each currency -------------------------------------------
    currency_cases = [
        #Organized by 1st term then 2nd term to make collision checking easy.
        #Note that last tuple MUST not have a comma at the end.
        (0, 0, '$', 'USD', 0), #US Dollars                              #$15.23
        # Have to include USD so recognizer works properly.
        (0, 0, 'H', 'HKD', 0), #Hong Kong Dollars                       #HK$ 115.00
        #(0, 0, '¥', 'CNY', 0), #Chinese Yuan                            #¥ 87
        #Removing for now because of weird inconsistencies
        (0, 0, '£', 'GBP', 0), #British Pound                           #£9.86
        (0, 0, 'S', 'SGD', 0), #Singaporean Dollar                      #S$17.25
        # Collision between this and Brazilian Real ('BRL') fixed by putting break into interpreter
        # so that only the first matching value is used.
        (0, 0, '₹', 'INR', 0), #Indian Rupee                            #₹ 842.50
        (0, 0, '₩', 'KRW', 4), #Korean Won                              #₩ 15,202.21
        # Bloomberg is off by a factor of 100 on the currency value, so I have to correct it
        # By putting a decimal on value after the comma (1520.221)
        #(0, 0, 'R', 'ZAR', 0), #South Afrian Rand                       #R 230.00
        #Causes collisions. Create better method than direct symbol search. (ie phrase search)
        (0,0, '฿', 'THB', 0), #Thai Baht                                 #฿402.50
        
        (0, 1, 'H', 'CHF', 0), #Swiss Franc                             #CHF 12.39
        (0, 1, 'D', 'CAD', 0), #Canadian Dollar                         #CDN$ 16.50
        (0, 1, 'M', 'MYR', 0), #Malaysian Ringgit                       #RM275.50
        (0, 1, 'p', 'IDR', 3), #Indonesian Rupee                        #Rp 185 500
        # Exotic case 2: Indonesian Rupees don't make any sense.
        #                Basically, you have to remove the last two values and divide by 2.
        (0, 1, '$', 'BRL', 1), #Brazilian Real                          #R$ 40,25
        (0, 1, 'T', 'TWD', 0), #Tiawanese Dollar                        #NT$ 460
        (0, 1, 'Z', 'NZD', 0), #New Zealand Dollar                      #NZ$ 19.64
        #(0, 1, 'L', 'CLP', 0), #Chilean Peso
        
        (1, 0, '€', 'EUR', 1), #Euro                                    #11,38€
        # Note about Euros - often, Steam will show them as '25,--€'. However, this should
        # be fine due to how the number finding section of the code works.
        (1, 0, 'r', 'NOK', 1), #Swedish Krona                           #106,50 kr
        (1, 0, 'L', 'TRY', 1), #Turkish Lira                            #73,99 TL
        (1, 1, 'б', 'RUB', 2), #Russian Ruble                           #683,99 pуб.
        # Exotic case 1: Rubles have a period already in the data pull, which would mess up the
        #                numerical program. Thus, it will automatically remove the last comma
        #                before running the rest of the code (except for the recognizer).
        (1, 2, 'A', 'AED', 0), #United Arab Emirates Dirham             #51.75 AED
        # CLP$ 13.800 CLP Chilean Peso
        (1, 0, '₫', 'VND', 5), #Vietnamese Dong                         #550.450,18₫
        (1, 0, '₴', 'UAH', 1),  #Ukranian Hryvnia                       #674,49₴
        (1, 0, 'ł', 'PLN', 1)  #Polish Zloty                            #100,00zł
    ]
    ignore_unrecognized = ['¥','R']
    
    if condition == 1: #For bug checking (see collision_check())
        return currency_cases
    

    ############# [[[[[[[SKIP TO HERE]]]]]]] #############
    numbers = [str(x) for x in range(10)] + ['.'] # Used to extract numbers from text
    for i in prices:
        
        # The following lines figure out the correct currency per listing.
        ref = -1
        for j,x in enumerate(currency_cases):
            if x[0] == 0:
                if i[x[1]] == x[2]: # If symbol in position matches target symbol
                    ref = x # Set config to "ref"
                    break
            else:
                if i[-1-x[1]] == x[2]: # If symbol in position matches target symbol (reading backwards)
                    ref = x # Set config to "ref"
                    break

        if ref == -1: # If there's no matching currency, just print the error dump to stdout and carry on.
            if i.split(' ')[0] not in ignore_unrecognized:
                print('!!!! -------- !!!!! Unrecognized currency! ' + i)
        else: # A match was found!
            # Grabs currency conversion rate
            if ref[3] in currency_rates: # Global array of currency values
                rate = currency_rates[ref[3]] # If currency is found
                # Note that USD is initialized to 1:1, reasonably enough
            else:
                # If currency not found, look it up online
                url = 'https://www.bloomberg.com/quote/' + ref[3] + 'USD:CUR'
                page = requests.get(url)
                tree = html.fromstring(page.content)
                text = tree.xpath('//*[@id="content"]/div/div/div[1]/div/div[4]/div[2]/text()')
                rate = float(text[0])
                currency_rates[ref[3]] = rate
            
            # Converts currency to USD based on conversion rate
            internal_price = cleanCommas(i, ref[4]) # Cut out potentially problematic symbols, make sure numbers are correct for currency
            internal_price = [x for x in list(internal_price) if x in numbers] # Extract numbers
            internal_price = float(''.join(internal_price))
            usd_prices.append(internal_price*rate)
    
    #Checks if greater than [percent], then returns it so it looks nice for humans
    usd_prices_sort = sorted(usd_prices)
    # print(usd_prices_sort[1]-usd_prices_sort[0],prices)
    # Gets percent of first vs second, and first vs last on page. Weak predictor of market buy potential
    percent1 = usd_prices_sort[1]/usd_prices_sort[0]
    percent2 = usd_prices_sort[-1]/usd_prices_sort[0]
    # Nice human readable format
    usd_prices = ['$' + str(x) for x in usd_prices]
    usd_prices_sort = ['$' + str(x) for x in usd_prices_sort]
    return usd_prices, usd_prices_sort, percent1, percent2

be_polite = time.sleep # Just for fun

# Linux
browser = webdriver.Chrome(r'/home/order/Videos/chromedriver/chromedriver')

# Login
login_url = r'https://store.steampowered.com//login/'
browser.get(login_url)
be_polite(navigation_time)
username_box = browser.find_element_by_css_selector('#input_username')
password_box = browser.find_element_by_css_selector('#input_password')
username_box.send_keys(username)
password_box.send_keys(password)

be_polite(navigation_time)

sign_in = browser.find_element_by_css_selector('#login_btn_signin > button')
sign_in.click()

### Since we're using a verified account
confirm_start = time.time()
code_confirmation = input('Did you enter your Steam confirmation code? [y\\n]')
if code_confirmation not in ['y','Y','yes','Yes','yep']:
    raise('Well why didn\'t you??')

confirm_time = time.time()-confirm_start
if confirm_time < navigation_time:
    be_polite(navigation_time-confirm_time)

itemno = 1 # Initialization
# Switching directory pages
for pageno in range(initial_page, final_page+adder ,adder):
    print('----------Page Number: ' + str(pageno) + ' ----------')
    page_url = general_url + str(pageno) + '_price_desc'
    # Navigating for items on each directory page
    for directorypage in range(10):
        browser.get(page_url)
        
        time.sleep(2) # Wait for selenium element database to get updated
        browser.implicitly_wait(30)
        # This is where the page occasionally doesn't load, 
        # so if it gets an exception, it'll just refresh.
        try:
            current_item = browser.find_element_by_css_selector('#result_' + str(directorypage))
        except NoSuchElementException:
            browser.get(page_url)
            time.sleep(navigation_time*2)
            browser.implicitly_wait(10)
            current_item = browser.find_element_by_css_selector('#result_' + str(directorypage))
        
        # Get item name, then go to page
        item_name = current_item.text
        item_name = cleanName(item_name)
        time.sleep(navigation_time)
        current_item.click()
        
        before_price_data = time.time()
        
        # Get price data
        browser.implicitly_wait(30)
        full_listing = browser.find_element_by_css_selector('#searchResultsRows').text
        itemized = cleanListing(full_listing,item_name)
        #print(str(itemno) + '. ' + item_name)
        #print('  ', end = '')
        #print(itemized)
        itemno += 1
        
        # Grab volumetric data for recent sales/prices (from chart). Fortunately already in USD.
        # Ignoring these for now since the rest runs stably
        volumetrics = browser.find_element_by_css_selector('body > div.responsive_page_frame.with_header > div.responsive_page_content > div.responsive_page_template_content')
        average_sale, stdev = cleanChart(volumetrics.get_attribute('outerHTML'))
        
        # For once the USD converter is finished
        USDitemized, USDitemizedSort, lowpercent, highpercent = toUSD(itemized,0)
        if lowpercent >= 1.2 and (average_sale*1.1)+stdev >= float(USDitemizedSort[0][1:]): # Since Steam cut is 15%, 20% is reasonable margin on my side
                                        # Also guarantees that turnover is at least current month
            print('Found item with price difference greater than ' + '20%!')
            print(str(itemno) + '. ' + item_name)
            print('  ' + str(itemized))
            print('  ' + str(USDitemized))
            print('  ' + str(USDitemizedSort))
        
        # elif lowpercent >= 1.2 and average_sale <= float(USDitemizedSort[0][1:])*1.1:
        #     # Used for dev context, should be off during normal runtime
        #     print('[FAKE] Item is most likely Souvenir...')
        #     print(str(itemno) + '. ' + item_name)
        #     print('  ' + str(itemized))
        #     print('  ' + str(USDitemized))
        #     print('  ' + str(USDitemizedSort))
        ### Currency conversion errors don't exist anymore because of trusted account
        # if highpercent >= 10.0:
        #     # Would be useful to know currency type here (you think?? year ago me sucked at structuring code)
        #     # Doesn't matter anyway though - we're still going to stay in USD.
        #     print('The last value is much higher than the lower value. Maybe something wrong?')
        #     print(str(itemno) + '. ' + item_name)
        #     print('  ' + str(itemized))
        #     print('  ' + str(USDitemized))
        #     print('  ' + str(USDitemizedSort))
        
        price_elapsed = time.time() - before_price_data
        
        if price_elapsed < navigation_time: # No reason to wait if processing the price data already took awhile
            time.sleep(navigation_time-price_elapsed)
    
    browser.get(page_url)
    time.sleep(navigation_time)
    if adder < 0:
        prevarrow = browser.find_element_by_css_selector('#searchResults_btn_prev')
        prevarrow.click()
    if adder > 0:
        nextarrow = browser.find_element_by_css_selector('#searchResults_btn_next')
        nextarrow.click()
    
    print('\n')


### Here's a function that might be useful for debugging
### It's essentially a unit test for the the toUSD() function
def checkCollisions():
    currencycases = toUSD(None, 1)
    testcases = [
        '$15.23',
        '¥ 87',
        '£9.86',
        'S$17.25',
        '₹ 842.50',
        '₩ 15,202.21',
        'R 230.00',
        'CHF 12.39',
        'HK$ 115.00',
        'CDN$ 16.50',
        'RM275.50',
        'Rp 185 500',
        'R$ 40,25',
        'NT$ 460',
        'NZ$ 19.64',
        '11,38€',
        '106,50 kr',
        '73,99 TL',
        '683,99 pуб.',
    ]
    for i in testcases:
        #Recognizer: Finds matching currency
        match = -1
        for j,x in enumerate(currencycases):
            if x[0] == 0:
                if i[x[1]] == x[2]: #If symbol in position matches target symbol
                    match = j       #Set to index of currency_case index of match
                    print(i)
                    print('  ' + str(x))
                    #break           #Sets it to first case that matches
            else:
                if i[len(i)-1-x[1]] == x[2]: #If symbol in position matches target symbol
                    match = j                #Set to index of currency_case index of match
                    print(i)
                    print('  ' + str(x))
                    #break                    #Sets it to first case that matches

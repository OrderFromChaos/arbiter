
# coding: utf-8

# In[2]:

# Implement better fault tolerance for "NoSuchElementException"
# Implement "market disruption" indication based on distribution of prices
# Implement predictions of profit based on previous value

from selenium import webdriver              # Primary navigation of Steam price data. Used for login.
from selenium.common.exceptions import NoSuchElementException # Used for the occasional page load failure.
import time                                 # Used to ensure Steam doesn't get angry
import math                                 # For math.floor() and math.ceil()s

import requests                             # Used for Bloomberg currency requests
from lxml import html                       # Used for Bloomberg currency requests


# In[3]:

### Used only to start dummy instance of selenium - don't run normally
webdriver.Chrome(r'/home/order/Videos/chromedriver/chromedriver')
# username = 'datafarmer001'
# password = 'u9hqgi3sl9'


# In[2]:

#Initial conditions
general_url = 'http://steamcommunity.com/market/search?q=&category_730_ItemSet%5B%5D=any&category_730_ProPlayer%5B%5D=any&category_730_StickerCapsule%5B%5D=any&category_730_TournamentTeam%5B%5D=any&category_730_Weapon%5B%5D=any&category_730_Exterior%5B%5D=tag_WearCategory0&appid=730#p'
initial_page = 50
final_page = 30
navigation_time = 5
currency_rates = {'USD': 1} #Dictionary of currency conversions; updated by toUSD()

adder = 0
if initial_page < final_page:
    adder = 1
else:
    adder = -1


# In[7]:

# -----------------------------------====Primary Functions====-----------------------------------
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

#Import data cleaning functions ---------------------------------------------

def cleanListing(mess,itemname):
    mess = mess.split('\n')
    #Does this instead of a spacing-based system because 'Sold!' changes the spacing.
    disallowed = ['PRICE','SELLER','NAME','Sold!','Buy Now','Counter-Strike: Global Offensive',itemname]
    return [x for x in mess if x not in disallowed]

def cleanName(name):
    return name.split('\n')[3]

def cleanChart(data):
    data = data[data.find('var line1')+10:data.find(']];')+2] #Gets all price data from chart
    better_data = eval(data) # Fortunately it's already formatted as a Python array, 
                # so I literally just need to evaluate it.
    better_data = [[x[0][:3],x[0][4:6],x[0][7:11],x[1]] for x in better_data]
                # Cuts date info into easily accessible parts.
    
    month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    
    current_month = month[int(time.strftime('%m'))-1]
    prev_month = month[int(time.strftime('%m'))-2]
    
    recent_data = [x for x in better_data if x[0] == current_month and x[2] == time.strftime('%Y')]
    recent_prices = [x[3] for x in recent_data]
    print('Number of recent sales: ' + str(len(recent_data)) + ' (' + "%.2f" % (len(recent_data)/int(time.strftime('%d'))) + ' per day on average)')
    print('Average recent sale price: ' + "%.2f" % average(previous_prices))
    print('Average median sale price: ' + "%.2f" % median(previous_prices))
    #Not gonna bother making it functional.

def cleanCommas(val, case):
    #Basically built to format the prices for the number cutout.
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
        return val.replace('.','').replace(','.'.')

#Import currency conversion cases -------------------------------------------
def toUSD(prices, condition): #Condition is for bug checking; set to 1 to return currency table.
    #This is by far going to be the longest function because of how dumb steam's currency thing is.
    usd_prices = []
    
    #Data format for currency_cases:
    # [read_direction, position, symbol, standard_currency_value, commas]
    # read_direction: 0 for forward reading, 1 for backwards reading
    # position: index of key symbol
    # symbol: symbol you're looking for (eg '$')
    # standard_currency_value: three-character string used by other currency sources (eg 'USD')
    #     ^^ This is so it can be looked up at the time of running
    # commas: what to do about commas. 0 = nothing, 1 = replace with periods, else = exotic
    
    # Example:
    # [0, 0, '$', 'USD', 0]
    
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
    
    numbers = [str(x) for x in range(10)] + ['.'] #Used for number cutout
    #Mildly inefficient; searches over the whole case space.
    for i in prices:
        #Recognizer: Finds matching currency
        match = -1
        for j,x in enumerate(currency_cases):
            if x[0] == 0:
                if i[x[1]] == x[2]: #If symbol in position matches target symbol
                    match = j       #Set to index of currency_case index of match
                    break           #Sets it to first case that matches
            else:
                if i[len(i)-1-x[1]] == x[2]: #If symbol in position matches target symbol
                    match = j                #Set to index of currency_case index of match
                    break                    #Sets it to first case that matches
        if match == -1: #If there's no currency in the list matching the value.
            if i.split(' ')[0] not in ignore_unrecognized:
                #There are some currencies I recognize the problems with, and they're program-specific.
                #This prevents the print from spamming the output.
                print('!!!! -------- !!!!! Unrecognized currency! ' + i)
        else:
            ref = currency_cases[match]
            #Grabs currency conversion rate and stores it internally to speed up local runs
            if ref[3] in currency_rates: #Global array of currency values
                rate = currency_rates[ref[3]] #If currency is found
            else:
                    #If currency not found
                url = 'https://www.bloomberg.com/quote/' + ref[3] + 'USD:CUR'
                    #Uses Bloomberg to look up currency values (since XE doesn't like bots)
                page = requests.get(url)
                tree = html.fromstring(page.content)
                text = tree.xpath('//*[@id="content"]/div/div/div[1]/div/div[4]/div[2]/text()')
                    #Location of price data
                rate = float(text[0])
                currency_rates[ref[3]] = rate
            
            #Converts currency to USD based on conversion rate
            internal_price = cleanCommas(i, ref[4]) #A function that cleans up and controls
            internal_price = [x for x in list(internal_price) if x in numbers] #Number cutout
            internal_price = float(''.join(internal_price))
            usd_prices.append(internal_price*rate)
    
    #Checks if greater than [percent], then returns it so it looks nice for humans
    usd_prices_sort = sorted(usd_prices)
    percent1 = usd_prices_sort[1]/usd_prices_sort[0]
    percent2 = usd_prices_sort[len(usd_prices_sort)-1]/usd_prices_sort[0]
    usd_prices = ['$' + ("%.2f" % x) for x in usd_prices]
    usd_prices_sort = ['$' + ("%.2f" % x) for x in usd_prices_sort]
    return usd_prices, usd_prices_sort, percent1, percent2


# In[6]:

# Windows
# browser = webdriver.Chrome(r'C:\Users\Syris Norelli\Downloads\ChromeDriver\ChromeDriver.exe')
# Linux
browser = webdriver.Chrome(r'/home/order/Videos/chromedriver/chromedriver')

#Login
login_url = r'https://store.steampowered.com//login/'
browser.get(login_url)
time.sleep(5)
username = 'datafarmer001'
password = 'u9hqgi3sl9' #Generated password; see below cell
username_box = browser.find_element_by_css_selector('#input_username')
password_box = browser.find_element_by_css_selector('#input_password')
username_box.send_keys(username)
password_box.send_keys(password)

time.sleep(5)

sign_in = browser.find_element_by_css_selector('#login_btn_signin > button')
sign_in.click()

time.sleep(5)

itemno = 1
#Switching directory pages
for pageno in range(initial_page, final_page+adder ,adder):
    print('----------Page Number: ' + str(pageno) + ' ----------')
    page_url = general_url + str(pageno) + '_price_desc'
    #Navigating single directory page
    for directorypage in range(10):
        browser.get(page_url)
        
        #Select item in directory + get item name, then go to page
        browser.implicitly_wait(30)
        #This is where the page occasionally doesn't load, 
        #so if it gets an exception, it'll just refresh.
        try:
            current_item = browser.find_element_by_css_selector('#result_' + str(directorypage))
        except NoSuchElementException:
            browser.get(page_url)
            time.sleep(navigation_time*2)
            browser.implicitly_wait(10)
            current_item = browser.find_element_by_css_selector('#result_' + str(directorypage))
        
        item_name = current_item.text
        item_name = cleanName(item_name)
        time.sleep(navigation_time)
        current_item.click()
        
        before_price_data = time.time()
        
        #Get price data
        browser.implicitly_wait(30)
        full_listing = browser.find_element_by_css_selector('#searchResultsRows').text
        itemized = cleanListing(full_listing,item_name)
        #print(str(itemno) + '. ' + item_name)
        #print('  ', end = '')
        #print(itemized)
        itemno += 1
        
        #For once the USD converter is finished
        USDitemized, USDitemizedSort, lowpercent, highpercent = toUSD(itemized,0)
        if lowpercent >= 1.2:
            print('Found item with price difference greater than ' + '20%!')
            print(str(itemno) + '. ' + item_name)
            print('  ' + str(itemized))
            print('  ' + str(USDitemized))
            print('  ' + str(USDitemizedSort))
        if highpercent >= 10.0:
            # Would be useful to know currency type here
            print('The last value is much higher than the lower value. Maybe something wrong?')
            print(str(itemno) + '. ' + item_name)
            print('  ' + str(itemized))
            print('  ' + str(USDitemized))
            print('  ' + str(USDitemizedSort))
        
        #Grab volumetric data for recent sales/prices (from chart). Fortunately already in USD.
        #Ignoring these for now since the rest runs stably
        #volumetrics = browser.find_element_by_css_selector('body > div.responsive_page_frame.with_header > div.responsive_page_content > div.responsive_page_template_content > script:nth-child(9)')
        #cleanChart(volumetrics.get_attribute('outerHTML'))
        
        price_elapsed = time.time() - before_price_data
        
        if price_elapsed < navigation_time: #No reason to wait if processing the price data already took awhile
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

#Things to do after all the data is collected
#Possibly print errors
#Send notification sound


# In[8]:

#Password generator
import random
allowed = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','1','2','3','4','5','6','7','8','9','0']

def generate(length):
    password = str()
    for i in range(length):
        password += allowed[random.randint(0,len(allowed)-1)]
    return password

botpass = generate(10)
print(botpass)


# In[28]:

print(currency_rates)


# In[43]:

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

checkCollisions()


# In[ ]:




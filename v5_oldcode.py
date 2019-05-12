regex_matches = {
    # Currency: [re match, how_to_split]
    # how_to_split types:
    #   0: Usual "XXX,XXX.XX"
    #   1: BRL, EUR, VND "XXX.XXX,XX"
    'USD': [re.compile('^\$[0-9\,]+\.[0-9]{2}'),0],       #US Dollars                              #$15.23
    'HKD': [re.compile('^HK\$\s[0-9\,]+\.[0-9]{2}'),0],   #Hong Kong Dollars                       #HK$ 115.00
    #'CNY': re.compile(???)                               #Chinese Yuan                            #¥ 87
    'GBP': [re.compile('^£[0-9\,]+\.[0-9]{2}'),0],        #British Pound                           #£9.86
    'SGD': [re.compile('^S\$[0-9\,]+\.[0-9]{2}'),0],      #Singaporean Dollar                      #S$17.25
    'INR': [re.compile('^₹\s[0-9\,]+\.[0-9]{2}'),0],      #Indian Rupee                            #₹ 842.50
    # 'KRW': [re.compile('^₩\s[0-9\,]+\.[0-9]{2}'),0],   #Korean Won                              #₩ 15,202.21
    'ZAR': [re.compile('^R\s[0-9\,]+\.[0-9]{2}'),0],      #South Afrian Rand                       #R 230.00
    'THB': [re.compile('^฿[0-9\,]+\.[0-9]{2}'),0],        #Thai Baht                               #฿402.50
    'CHF': [re.compile('^CHF\s[0-9\,]+\.[0-9]{2}'),0],    #Swiss Franc                             #CHF 12.39
    'CAD': [re.compile('^CDN\$\s[0-9\,]+\.[0-9]{2}'),0],  #Canadian Dollar                         #CDN$ 16.50
    'MYR': [re.compile('^RN[0-9\,]+\.[0-9]{2}'),0],       #Malaysian Ringgit                       #RM275.50
    # 'IDR': [re.compile('^Rp\s[0-9\,]+\s[0-9]{2}'),1],   #Indonesian Rupee                        #Rp 185 500
    'BRL': [re.compile('^R\$\s[0-9]+\,[0-9]{2}'),1],      #Brazilian Real                          #R$ 40,25
    # TWD': [re.compile('^NT\$\s[0-9]+'),0],              #Tiawanese Dollar                        #NT$ 460
    'NZD': [re.compile('^NZ\$\s[0-9\,]+\.[0-9]{2}'),0],   #New Zealand Dollar                      #NZ$ 19.64
    'CLP': [re.compile('^CLP\$\s[0-9\,]+\.[0-9]{2}'),0],  #Chilean Peso                            #CLP$ 13.800
    'EUR': [re.compile('^[0-9]+\,[0-9\-]{2}€'),1],        #Euro                                    #11,38€   25,--€
    'NOK': [re.compile('^[0-9]+\,[0-9]{2}\skr'),1],       #Swedish Krona                           #106,50 kr
    'TRY': [re.compile('^[0-9]+\,[0-9\-]{2}\sTL'),1],     #Turkish Lira                            #73,99 TL
    'RUB': [re.compile('^[0-9]+\,[0-9\-]{2}\pуб'),1],     #Russian Ruble                           #683,99 pуб.
    'AED': [re.compile('^[0-9]+\,[0-9\-]{2}\sAED'),0],    #United Arab Emirates Dirham             #51.75 AED
    'VND': [re.compile('^[0-9\.]+\,[0-9\-]{2}\s₫'),1],    #Vietnamese Dong                         #550.450,18₫
    'UAH': [re.compile('^[0-9]+\,[0-9\-]{2}\s₴'),1],      #Ukranian Hryvnia                        #674,49₴
    'PLN': [re.compile('^[0-9]+\,[0-9\-]{2}\szł'),1]      #Polish Zloty                            #100,00zł
}
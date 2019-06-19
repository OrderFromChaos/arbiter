import json

with open('../../backend.txt','r') as f:
    data = json.load(f)

item = data['results']
item = sorted(item, key=lambda x: x['sell_price'], reverse=True)

for i in item[:100]:
    print(i['name'], i['sell_listings'], i['sell_price'])
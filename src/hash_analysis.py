import json
import matplotlib.pyplot as plt

with open('combineddata.json','r') as f:
    metadata = json.load(f)
hashes = metadata['json_hashes']
print('Number of hashes:', len(hashes))

with open('hash_overlap.txt','r') as f:
    data = f.read()

pairing = data.split(' ')
pairing = [(int(x), int(y)) for x, y in zip(pairing[::2],pairing[1::2])]
print('Number of entries:', len(pairing))

seconds, hashno = list(zip(*pairing))
plt.scatter(seconds, hashno)
plt.show()
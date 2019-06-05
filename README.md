# steam-private

Built to do arbitrage on the Steam marketplace, or at least recommend to a human when to buy/sell.

The first phase of data gathering is in `page_gatherer.py`, which scans down the list of Factory New CSGO items. It logs basic price and volume information, as well as URLs for later.

The second phase is where the actual meat of the program is: `price_scanner.py`. This program scans through the list of URLs that page_gatherer.py found after filtering away undesirable traits, like low volume (no point trading anything with less than daily turnover).

`page_scanner.py` calls `analysis.py` to figure out whether there's actually anything good happening with the item it's looking at. `analysis.py` also includes a backtesting suite for rapid evaluation of new strategies, which helps them be implemented much faster.
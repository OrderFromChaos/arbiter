# arbiter

### Overview

Built to do arbitrage on the Steam marketplace, or at least recommend to a human when to buy/sell. Arbitrage is defined as differences in pricing an item between different markets or sellers. Sometimes people will sell out for less than the market value; this program tries to swoop in and catch those before someone else does.

In the development process, this ended up leading to the development of a robust framework for data scraping, gathering historical data, and flexible application and development of trading strategies. This will allow for future work on building an ML-based bot for Steam trading.

### Technical

The Steam marketplace has thousands of items; most of them don't have enough liquidity to do any worthwhile trading optimization on. As a result, the data gathering is split into two parts.

The first phase is `src/page_gatherer.py`, which scans down the Steam listing of Factory New CS:GO items. It logs basic price and volume information, as well as URLs for later.

The second phase is where the actual meat of the program is: `src/price_scanner.py`. This program filters the list of URLs that page_gatherer.py found, and scans them for purchasing opportunities.

Once it loads a URL, `src/page_scanner.py` calls `analysis.py` to figure out whether there's actually anything good happening with the item it's looking at. `analysis.py` also includes a backtesting suite for rapid evaluation of new strategies. There are two current strategies:

- SimpleListingProfit. This strategy looks only at the current listings and buys if the cheapest sale is at least 15% less than than the second cheapest. This is naive as it completely ignores historical context, and doesn't inherently understand monopoly pricing (if there are three sales at 200, 300, and 400 for an item with a market rate of 50, it should NOT buy).

- LessThanThirdQuartileHistorical (LTTQH). This strategy splits the historical sales into quartiles, and decides that if a sale price times 1.15x is less than Q3, then it purchases the item. This is much better as it means we have evidence the item can in theory be sold, but it performs poorly when there is a large and fast item price drop.

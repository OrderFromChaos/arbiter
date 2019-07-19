### GENERAL ALGORITHM: (Final version)
# Over the course of a day,
# 1. Scan for buys, spend up to full portfolio allocation (could implement optimal stopping?)
# 2. Sell at force buy n_liquidation_days later
# 3. Record all intermediate data to see if the supposed best strategy actually worked.

### GENERAL ALGORITHM: (Current version)
# Over the course of a day,
# 1. Scan for buys
# It's important to know whether these are being sold in 1 minute or 15 minutes. Thus, gotta check.
# Saying "I could have performed perfectly with perfect information" is only mildly good.


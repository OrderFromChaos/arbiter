### TODO:

### 1. Add open ports so the program can be told what to do while running
###    and run on a "while True" loop in the background

### 2. Dataset read is pretty slow - figure out a way to improve read rates. See analysis.py for
###    how slow it tends to be.

### 3. Bring price_scanner.py and utility_funcs.py in compliance with pylint + 100 character lines.

### 4. Log low volume items separately so it takes up less memory. Ideally, create a global
###    variable settings database for these kind of filterings.

### 5. Fix inconsistent casing (do camelCase on functions, caps for const.)

### 6. Add type hints

### 7. Figure out ways to reduce edge cases on the quartile model (probably about 30% of output
###    is good, others are too low profit or bad for other reasons, like listing location)

### 8. Implement text or email notifications; right now I have to be sitting near it when I'm doing
###    scanning. I set up csgomarketrequests@gmail.com.

### 9. Design a system to react to price updates on item holdings. Sometimes when trying to sell an
###    item at Q3, someone will try and undercut me. Do an analysis on when price updating is best
###    and when letting them sell for less than market rate and waiting for someone else to buy at
###    your price point is right.

### 10. Some data still seems to be getting lost; we used to have 1600 table entries, now we have
###     954. Investigate.

### 11. Fix removeOutliers() bug in analysis.py.

### 12. Standardize input names for helper functions in analysis.py.
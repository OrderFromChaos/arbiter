#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### PURPOSE:
### Given cost to limited unit A and profit in unit B, how to maximize unit B profit?
### This is the continuous (over reals) 0/1 knapsack problem.
### https://en.wikipedia.org/wiki/Knapsack_problem#0/1_knapsack_problem
### However, it uses strictly positive real numbers instead of strictly positive integers.
### We can convert this to an integer 0/1 knapsack problem simply by multiplying by 100; we are
###     dealing with currencies, after all...

def knapsack(weights, values, weightlimit):
    assert len(weights) == len(values), ('Mismatched number of costs and values ' + 
                                       (len(costs),len(values)))
    costs = [int(x*100) for x in costs] # Conversion to integer costs

    n = len(weights)
    dpdict = {(-1, x):0 for x in range(weightlimit+1)} # Base cases
    optimal_items = []

    for i in range(0, n): # itemcount
        for w in range(weightlimit+1): # weight
            if weights[i] > w:
                dpdict[(i ,w)] = dpdict[(i-1, w)]
            else:
                nochange = dpdict[(i-1, w)]
                new_is_better = dpdict[(i-1, w-weights[i])] + values[i]
                if nochange > new_is_better:
                    dpdict[(i, w)] = nochange
                else:
                    dpdict[(i, w)] = new_is_better

    optimal_value = dpdict[(n-1), weightlimit]

    # Find optimal items

    for item in dpdict.items():
        print(item)
    
    # for i in range(n, 0, -1): 
    #     if optimal_value != dpdict[(i-1, w)]:
    #         optimal_items.append(weights[i-1])
    #         # Since this weight is included, its value is deducted 
    #         optimal_value = optimal_value - values[i-1] 
    #         w = w - weights[i-1]

    return (optimal_value, optimal_items)

if __name__ == '__main__':
    optimal, boxes = knapsack([24,10,10,10],[24,9,9,9],30)
    # print(ans)
    print(optimal, boxes)
    # Expected: 18, [1,2]

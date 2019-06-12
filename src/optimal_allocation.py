#!/usr/bin/env python3

# Author: Syris Norelli, snore001@ucr.edu

### PURPOSE:
### Given cost to limited unit A and profit in unit B, how to maximize unit B profit?
### This is the continuous (over reals) 0/1 knapsack problem.
### https://en.wikipedia.org/wiki/Knapsack_problem#0/1_knapsack_problem
### However, it uses strictly positive real numbers instead of strictly positive integers.

def knapsack(costs, values, costlimit):
    assert len(costs) == len(values), ('Mismatched number of costs and values ' + 
                                       (len(costs),len(values)))
    n = range(len(costs))
    maxdp = {0:0} # Base case

    for itemcount in range(1,n):
        cost = costs[itemcount]
        previous = maxdp[itemcount-1]
        if cost > costlimit:
            maxdp[itemcount] = previous
        else:
            maxdp[itemcount] = max(previous, previous + )
            newsum = maxdp[itemcount-1] + cost


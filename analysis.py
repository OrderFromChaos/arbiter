def sma(dataset, n):
    if len(dataset) < n:
        return 'N is too high for this dataset (' + str(len(dataset)) + ' < ' + str(n) + ')'
    
    avg_list = []
    for i in range(0,len(dataset)-n):
        avg = sum(dataset[i:i+n])/n
        avg_list.append(avg)
    return avg_list

def remove_outliers(dataset,sigma):
    # Remove all data points that are greater than sigma away from the mean
    mean = sum(dataset)/len(dataset)
    stdev = (sum([(x-mean)**2 for x in dataset])/len(dataset))**0.5
    return [x for x in dataset if mean-sigma*stdev < x < mean+sigma*stdev]
import math
from scipy.stats import norm

def Exponential_distribution(lambdaValue, arrivalTime_seed, run):
    global r1
    if run % 2 == 0:
        r1 = arrivalTime_seed.rand()
    if run % 2 == 1:
        r1 = 1 - r1
    if (r1 == 0): r1 += 0.0001
    r2 = -math.log(r1) / lambdaValue
    return r2

def Normal_distribution(mean, stdev, arrivalTime_seed, run):
    global r1
    if run % 2 == 0:
        r1 = arrivalTime_seed.rand()
    if run % 2 == 1:
        r1 = 1 - r1
    if (r1 == 0): r1 += 0.0001
    output = norm.ppf(r1, loc=mean, scale= stdev)
    return output

def Bernouilli_distribution(prob, arrivalTime_seed, run):
    global u1
    if run % 2 == 0:
        u1 = arrivalTime_seed.rand()
    if run % 2 == 1:
        u1 = 1 - u1 
    if (u1 < prob):
        return 0
    else:
        return 1
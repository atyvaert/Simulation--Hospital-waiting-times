import numpy as np
import math
from collections import defaultdict
from scipy.stats import t as T_value
from scipy.stats import norm
import matplotlib.pyplot as plt
import time
import csv

def Exponential_distribution(lambdaValue, randomState):
    j1 = randomState.rand()
    #Implementing antithetic VR
    if run % 2 == 1:
        j1 = 1 - j1  
    if (j1 == 0): j1 += 0.0001
    j2 = -math.log(j1) / lambdaValue
    return j2

def Poisson_distribution(lambdaValue):
    j1 = np.random.uniform(0, 1)
    k = p = 0
    L = math.exp(-lambdaValue)
    j3 = 0
    while (j1 >= j3):
        j2 = L * pow(lambdaValue, k)
        p = 1
        for i6 in range(0, k + 1):
            if (i6 == 0):
                p = 1
            else:
                p *= i6
        j2 /= p
        j3 += j2
        k += 1
    return k - 1

def Normal_distribution(mean, stdev):
    # TO MODEL BASED ON CUMULATIVE DENSITY FUNCTION OF NORMAL DISTRIBUTION BASED ON BOOK OF SHELDON ROSS, Simulation, The polar method, p80.
    t = r1 = r2 = x = 0
    while (t >= 1 or t == 0):
        r1 = np.random.uniform(0, 1) * 2 - 1  # randomNumber 1
        r2 = np.random.uniform(0, 1) * 2 - 1
        t = r1 * r1 + r2 * r2

    multiplier = math.sqrt(-2 * math.log(t) / t)
    x = r1 * multiplier * stdev + mean
    return x

def Bernouilli_distribution(prob):
    j1 = np.random.uniform(0, 1)
    if (j1 < prob):
        return 0
    else:
        return 1

def Uniform_distribution(a, b):
    j1 = np.random.uniform(0, 1)
    x = a + (b - a) * j1
    return x

def Triangular_distribution(a, b, c):
    j1 = np.random.uniform(0, 1)
    L = 0
    x = a
    while (j1 >= L):
        if (x <= b):
            L = pow((x - a), 2) / ((c - a) * (b - a))
        else:
            L = 1 - (pow(c - x, 2) / ((c - a) * (c - b)))
            x += 1
    return x - 1
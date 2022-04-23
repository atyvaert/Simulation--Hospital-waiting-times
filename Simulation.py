from random import seed
import numpy as np
import math
from collections import defaultdict
from scipy.stats import t as T_value
from scipy.stats import norm
import matplotlib.pyplot as plt
import time
from Helper import *


class Slot():
    # Variables and parameters
    global startTime, appTime, slotType, patientType

    def __init__(self, startTime, appTime, slotType, patientType):
        self.startTime = startTime
        self.appTime = appTime
        self.slotType = slotType
        self.patientType = patientType
    # Functions


class Patient():
    # Initializing

    global nr, patientType, scanType, callWeek, callDay, callTime, tardiness, isNoShow, duration

    def __init__(self, nr, patientType, scanType, callWeek, callDay, callTime, tardiness, isNoShow, duration):
        self.nr = nr
        self.patientType = patientType
        self.scanType = scanType
        self.callWeek = callWeek
        self.callDay = callDay
        self.callTime = callTime
        self.scanWeek = -1
        self.scanDay = -1
        self.slotNr = -1
        self.appTime = -1
        self.tardiness = tardiness
        self.isNoShow = isNoShow
        self.duration = duration
        self.scanTime = -1.0

    # Functions
    def getAppWT(self):
        if self.scanTime != -1:
            return (((self.scanWeek - self.callWeek) * 7 + self.scanDay - self.callDay) * 24 + self.appTime - self.callTime)  # in hours
        else:
            print("CAN NOT CALCULATE APPOINTMENT WT OF PATIENT", self.nr)
            exit(1)

    def getScanWT(self):
        if self.scanTime != 0:
            wt = 0
            if self.patientType == 1:
                wt = self.scanTime - (self.appTime + self.tardiness)
            else:
                wt = self.scanTime - self.callTime
            return max(0.0, wt)
        else:
            print("CAN NOT CALCULATE SCAN WT OF PATIENT", self.nr)  # in hours
            exit(1)


class simulation():
    global inputFileName, D, amountOTSlotsPerDay, S, slotLength, lambdaElective, meanTardiness, stdevTardiness, probNoShow, meanElectiveDuration, \
        stdevElectiveDuration, lambdaUrgent, probUrgentType, cumulativeProbUrgentType, meanUrgentDuration, stdevUrgentDuration, weightEl, weightUr, \
        d, s, w, r, patients, patient, movingAvgElectiveAppWT, movingAvgElectiveScanWT, movingAvgUrgentScanWT, movingAvgOT, avgElectiveAppWT, avgElectiveScanWT, \
        avgUrgentScanWT, avgOT, numberOfElectivePatientsPlanned, numberOfUrgentPatientsPlanned
    inputFileName = ".../input-S1-14.txt"
    global W, R, rule
    W = 10  # number of weeks to simulate = runlength
    R = 1  # number of replications
    rule = 1

    avgElectiveAppWT = 0
    avgElectiveScanWT = 0
    avgUrgentScanWT = 0
    avgOT = 0
    numberOfElectivePatientsPlanned = 0
    numberOfUrgentPatientsPlanned = 0

    weekSchedule = Slot * [D]
    for d in D:
        weekSchedule[d] = Slot[S]
    movingAvgElectiveAppWT = [W]
    movingAvgElectiveScanWT = [W]
    movingAvgUrgentScanWT = [W]
    movingAvgOT = [W]

    # Variables and parameters
    inputFileName = "../GitHub/Simulation/data"
    D = 6  # number of days per week (NOTE: Sunday not included! so do NOT use to calculate appointment waiting time)
    amountOTSlotsPerDay = 10  # number of overtime slots per day
    S = 32 + amountOTSlotsPerDay  # number of slots per day
    slotLength = 15.0 / 60.0  # duration of a slot (in hours)
    lambdaElective = 28.345
    meanTardiness = 0
    stdevTardiness = 2.5
    probNoShow = 0.02
    meanElectiveDuration = 15
    stdevElectiveDuration = 3
    lambdaUrgent = [2.5, 1.25]
    probUrgentType = [0.7, 0.1, 0.1, 0.05, 0.05]
    cumulativeProbUrgentType = [0.7, 0.8, 0.9, 0.95, 1.0]
    meanUrgentDuration[5] = [15, 17.5, 22.5, 30, 30]
    stdevUrgentDuration[5] = [2.5, 1, 2.5, 1, 4.5]
    weightEl = 1.0 / 168.0  # objective weight elective
    weightUr = 1.0 / 9.0  # objective weight urgent scan

    # Functions
    def setWeekSchedule(self):
        # Read and set the slot types (0=none, 1=elective, 2=urgent within normal working hours)
        return 0

    def resetSystem(self):
        global avgElectiveAppWT, avgElectiveScanWT, avgUrgentScanWT, avgOT, numberOfElectivePatientsPlanned, numberOfUrgentPatientsPlanned
        # reset all variables related to 1 replication
        patients.clear()
        avgElectiveAppWT = 0
        avgElectiveScanWT = 0
        avgUrgentScanWT = 0
        avgOT = 0
        numberOfElectivePatientsPlanned = 0
        numberOfUrgentPatientsPlanned = 0

        for w in movingAvgElectiveAppWT:
            movingAvgElectiveAppWT[w] = 0
        for w in movingAvgElectiveScanWT:
            movingAvgElectiveScanWT[w] = 0
        for w in movingAvgUrgentScanWT:
            movingAvgUrgentScanWT[w] = 0
        for w in movingAvgOT:
            movingAvgOT[w] = 0

    def getRandomScanType(self):
        r = np.random.uniform(0, 1)
        type = -1
        for x in range(0, 5):
            if type != -1:
                break
            if r < cumulativeProbUrgentType[x]:
                type = x
        return type

    def generatePatients(self):
        global arrivalTimeNext, counter, patientType, scanType, endTime, callTime, tardiness, duration, lambdaa, noShow, lambdaElective, lambdaUrgent
        counter = 0  # total number of patients so far
        for w in W:
            for d in D:  # not on Sunday
                # generate ELECTIVE patients for this day
                if d < D - 1:  # not on Saturday either
                    arrivalTimeNext = 8 + Exponential_distribution(lambdaElective) * (17 - 8)
                    while arrivalTimeNext < 17:  # desk open from 8h until 17h
                        patientType = 1  # elective
                        scanType = 0  # no scan type
                        callTime = arrivalTimeNext  # set call time, i.e. arrival event time
                        tardiness = Normal_distribution(meanTardiness,
                                                        stdevTardiness) / 60.0  # in practice this is not known yet at time  of call
                        noShow = Bernouilli_distribution(
                            probNoShow)  # in practice this is not known yet at time of call
                        duration = Normal_distribution(meanElectiveDuration,
                                                       stdevElectiveDuration) / 60.0  # in practice this is not known yet at time of call
                        patient = Patient(counter, patientType, scanType, w, d, callTime, tardiness, noShow, duration)
                        patients.append(patient)
                        counter = counter + 1
                        arrivalTimeNext = arrivalTimeNext + Exponential_distribution(lambdaElective) * (
                                    17 - 8)  # arrival time of next patient (if < 17h)

                # generate URGENT patients for this day
                if ((d == 3) | (d == 5)):
                    lambda_local = lambdaUrgent[1]  # on Wed and Sat, only half a day!
                    endTime = 12
                else:
                    lambda_local = lambdaUrgent[1]
                    endTime = 17
                arrivalTimeNext = 8 + Exponential_distribution(lambda_local) * (endTime - 8)
                while arrivalTimeNext < endTime:  # desk open from 8h until 17h
                    patientType = 2  # urgent
                    scanType = self.getRandomScanType()  # set scan type
                    callTime = arrivalTimeNext  # set arrival time, i.e. arrival event time
                    tardiness = 0  # urgent patients have an arrival time = arrival event time
                    noShow = False  # urgent patients are never no-show
                    duration = Normal_distribution(meanUrgentDuration[scanType], stdevUrgentDuration[
                        scanType]) / 60.0  # in practice this is not known yet at time of arrival
                    patient = Patient(counter, patientType, scanType, w, d, callTime, tardiness, noShow, duration)
                    patients.append(patient)
                    counter = counter + 1
                    arrivalTimeNext = arrivalTimeNext + Exponential_distribution(lambda_local) * (
                                endTime - 8)  # arrival time of next patient (if < 17h)

    def getNextSlotNrFromTime(self, day, patientType, time):
        found = False
        slotNr = -1
        for s in range(0, S):
            if found:
                break
            if self.weekSchedule[day][s].appTime > time and patientType == self.weekSchedule[day][s].patientType:
                found = True
                slotNr = s
        if (found == False):
            print("NO SLOT EXISTS DURING TIME %.2f \n", time)
            exit(0)
        return slotNr

    def schedulePatients(self):
        return 0

    def sortPatientsOnAppTime(self):
        return 0

    def runOneSimulation(self):
        return 0

    def runSimulations(self):
        electiveAppWT = 0
        electiveScanWT = 0
        urgentScanWT = 0
        OT = 0
        OV = 0
        self.setWeekschedule()  # set cyclic slot schedule based on given input file
        print("r \t elAppWT \t elScanWT \t urScanWT \t OT \t OV \n")
        # run R replications 
        for r in range(0, R):
            self.resetSystem()  # reset all variables related to 1 replication
            seed  # set seed value for random value generator
            self.runOneSimulation()  # run 1 simulation / replication
            electiveAppWT = electiveAppWT + avgElectiveAppWT
            electiveScanWT = electiveScanWT + avgElectiveScanWT
            urgentScanWT = avgUrgentScanWT + urgentScanWT
            OT = avgOT + OT
            OV = OV + (avgElectiveAppWT / weightEl + avgUrgentScanWT / weightUr)
            print("%d \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \n", r, avgElectiveAppWT, avgElectiveScanWT,
                  avgUrgentScanWT, avgOT, avgElectiveAppWT / weightEl + avgUrgentScanWT / weightUr)
        electiveAppWT = electiveAppWT / R
        electiveScanWT = electiveScanWT / R
        urgentScanWT = urgentScanWT / R
        OT = OT / R
        OV = OV / R
        objectiveValue = electiveAppWT / weightEl + urgentScanWT / weightUr
        print("Avg.: \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \n", electiveAppWT, electiveScanWT, urgentScanWT, OT,
              objectiveValue)

        # print results
        # inputFileName = "/Users/wouterdewitte/Documents/1e Master Business Engineering_Data Analytics/Semester 2/Simulation Modelling and Analyses/Project/project SMA 2022 student code /input-S1-14.txt";
        # todo: print the output you need to a .txt file
        # fclose(file);

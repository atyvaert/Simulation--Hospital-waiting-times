from random import seed
from Helper import *
import numpy as np
import pandas as pd

class Slot():
    # all information about slots
    # Variables and parameters
    global startTime, appTime, slotType, patientType

    def __init__(self, startTime, appTime, slotType, patientType):
        self.startTime = startTime      # the actual start time independent of scheduling rule
        self.appTime = appTime          # time the patient receives and DEPENDS ON THE RULE (same as starttime for fifo)
        self.slotType = slotType        # type of slot (0=none, 1=elective, 2=urgent within normal working hours, 3=urgent in overtime)
        self.patientType = patientType  # 1 (= elective) or 2 (= urgent) or 0 to represent a break
    # Functions


class Patient():
    # Initializing

    global nr, patientType, scanType, callWeek, callDay, callTime, tardiness, isNoShow, duration

    def __init__(self, nr, patientType, scanType, callWeek, callDay, callTime, tardiness, isNoShow, duration):
        self.nr = nr                    # individual nr to identify
        self.patientType = patientType  # same as for patienttype in slot class
        self.scanType = scanType        # 0 for elective patients, but 5 types for urgent patients
        
        # next 3 variables indicate time at which patient requests an appointment
        self.callWeek = callWeek        # week of arrival (elective: call, urgent: actual arrival)
        self.callDay = callDay          # day of arrival (elective: call, urgent: actual arrival)
        self.callTime = callTime        # time of arrival (elective: call, urgent: actual arrival) (in hours)
        
        # next 4 variables indicate appointment of the patients
        # default of -1 means unscheduled
        self.scanWeek = -1              # week of appointment
        self.scanDay = -1               # day of appointment
        self.slotNr = -1                # slot number of appointment
        self.appTime = -1               # time of appointment (elective: according to RULE, urgent: slot start time) (in hours)

        self.tardiness = tardiness
        self.isNoShow = isNoShow
        self.duration = duration        # actual duration taken from random distr
        self.scanTime = -1.0            # actual start time of the patients appointment

    # Functions
    def getAppWT(self):
        if self.slotNr != -1: # AANPASSEN VOLGERNS MIJ NAAR SELF.SLOTNR (@WOuter of Viktor)
            return (((self.scanWeek - self.callWeek) * 7 + self.scanDay - self.callDay) * 24 + self.appTime - self.callTime)  # in hours
        else:
            print("CAN NOT CALCULATE APPOINTMENT WT OF PATIENT", self.nr)
            exit(1)

    def getScanWT(self):
        if self.scanTime != 0:
            wt = 0
            if self.patientType == 1: # elective patients
                wt = self.scanTime - (self.appTime + self.tardiness)
            else: # urgent patients
                wt = self.scanTime - self.callTime
            return max(0.0, wt)
        else:
            print("CAN NOT CALCULATE SCAN WT OF PATIENT", self.nr)  # in hours
            exit(1)


class simulation():
    # Variables and parameters
    global inputFileName, D, amountOTSlotsPerDay, S, slotLength, lambdaElective, meanTardiness, stdevTardiness, probNoShow, meanElectiveDuration, \
        stdevElectiveDuration, lambdaUrgent, probUrgentType, cumulativeProbUrgentType, meanUrgentDuration, stdevUrgentDuration, weightEl, weightUr, \
        d, s, w, r, patients, patient, movingAvgElectiveAppWT, movingAvgElectiveScanWT, movingAvgUrgentScanWT, movingAvgOT, avgElectiveAppWT, avgElectiveScanWT, \
        avgUrgentScanWT, avgOT, numberOfElectivePatientsPlanned, numberOfUrgentPatientsPlanned, W, R, rule

    # parameters given in the assignment
    inputFileName = "/input-S1-14.txt"
    D = 6                           # number of days per week (NOTE: Sunday not included! so do NOT use to calculate appointment waiting time)
    amountOTSlotsPerDay = 10        # number of overtime slots per day
    S = 32 + amountOTSlotsPerDay    # number of slots per day
    slotLength = 15.0 / 60.0        # duration of a slot (in hours)
    lambdaElective = 28.345
    meanTardiness = 0
    stdevTardiness = 2.5
    probNoShow = 0.02
    meanElectiveDuration = 15
    stdevElectiveDuration = 3
    lambdaUrgent = [2.5, 1.25]
    probUrgentType = [0.7, 0.1, 0.1, 0.05, 0.05]
    cumulativeProbUrgentType = [0.7, 0.8, 0.9, 0.95, 1.0]
    meanUrgentDuration = [15, 17.5, 22.5, 30, 30]
    stdevUrgentDuration = [2.5, 1, 2.5, 1, 4.5]
    weightEl = 1.0 / 168.0          # objective weight elective
    weightUr = 1.0 / 9.0            # objective weight urgent scan

    
    # variables we have to SET OURSELVES
    W = 10      # number of weeks to simulate = runlength
    R = 1       # number of replications
    rule = 1    # integer indicating which scheduling rule you are testing

    avgElectiveAppWT = 0
    avgElectiveScanWT = 0
    avgUrgentScanWT = 0
    avgOT = 0
    numberOfElectivePatientsPlanned = 0
    numberOfUrgentPatientsPlanned = 0

    # a 2D array of slot objects indicating week schedule you want to test,
    # fill this by input file of 0 and 1 indicating the slots (later in code)
    weekSchedule = np.zeros((D, S)) 
    for row in weekSchedule:
        for elem in row:
            elem = Slot(0,0,0,0)
    
    # variables specific to one simulation run (patients list and some objectives)
    patients = [] 
    movingAvgElectiveAppWT = [W]
    movingAvgElectiveScanWT = [W]
    movingAvgUrgentScanWT = [W]
    movingAvgOT = [W]



    # Functions
    def setWeekSchedule(self):
        # Read and set the slot types (0=none, 1=elective, 2=urgent within normal working hours)
        
        # 1) read in the input file indicating the week schedule
        with open(datapath + inputFileName, 'r') as file:
        schedule = file.read()
        elementInt = -1
        for s in range(0,32):
            for d in range(0,D):
                weekSchedule[d][s].slotType = elementInt
                weekSchedule[d][s].patientType = elementInt
        
    

    def resetSystem(self):
        global avgElectiveAppWT, avgElectiveScanWT, avgUrgentScanWT, avgOT, numberOfElectivePatientsPlanned, numberOfUrgentPatientsPlanned, patients, \
            movingAvgElectiveAppWT, movingAvgElectiveScanWT, movingAvgUrgentScanWT
        # reset all variables related to 1 replication
        patients.clear()
        avgElectiveAppWT = 0
        avgElectiveScanWT = 0
        avgUrgentScanWT = 0
        avgOT = 0
        numberOfElectivePatientsPlanned = 0
        numberOfUrgentPatientsPlanned = 0

        for w in movingAvgElectiveAppWT:
            w = 0
        for w in movingAvgElectiveScanWT:
            w = 0
        for w in movingAvgUrgentScanWT:
            w = 0
        for w in movingAvgOT:
            w = 0

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

    # method called by the main (starts the whole simulation process):
    def runSimulations(self):
        global avgOT, avgElectiveAppWT, avgElectiveScanWT, avgUrgentScanWT
        electiveAppWT = 0
        electiveScanWT = 0
        urgentScanWT = 0
        OT = 0
        OV = 0
        # first set weekSchedule by filling in 2D slot array
        self.setWeekSchedule()  # set cyclic slot schedule based on given input file
        column_names = ["r", "elAppWT", "elScanWT", "urScanWT", "OT", "OV"]
        output = pd.DataFrame(columns=column_names)
        #print("r \t elAppWT \t elScanWT \t urScanWT \t OT \t OV \n")
        # run R replications 
        for r in range(0, R):
            self.resetSystem()  # 2) reset all variables related to 1 replication
            seed  # set seed value for random value generator
            self.runOneSimulation()  # 3) run 1 simulation / replication
            electiveAppWT = electiveAppWT + avgElectiveAppWT
            electiveScanWT = electiveScanWT + avgElectiveScanWT
            urgentScanWT = avgUrgentScanWT + urgentScanWT
            OT = avgOT + OT
            OV = OV + (avgElectiveAppWT / weightEl + avgUrgentScanWT / weightUr)
            values_to_add = {'r': r, 'elAppWT': avgElectiveAppWT, 'elScanWT': avgElectiveScanWT, 'urScanWT': avgUrgentScanWT, 'OT': avgOT, 'OV': avgElectiveAppWT / weightEl + avgUrgentScanWT / weightUr}
            row_to_add = pd.Series(values_to_add, name="run " + str(r))
            output = output.append(row_to_add)
            #print("%d \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \n", r, avgElectiveAppWT, avgElectiveScanWT,
             #     avgUrgentScanWT, avgOT, avgElectiveAppWT / weightEl + avgUrgentScanWT / weightUr)
        electiveAppWT = electiveAppWT / R
        electiveScanWT = electiveScanWT / R
        urgentScanWT = urgentScanWT / R
        OT = OT / R
        OV = OV / R
        objectiveValue = electiveAppWT / weightEl + urgentScanWT / weightUr
        values_to_add = {'r': r, 'elAppWT': electiveAppWT, 'elScanWT': electiveScanWT,
                         'urScanWT': urgentScanWT, 'OT': OT,
                         'OV': objectiveValue}
        row_to_add = pd.Series(values_to_add, name="Average")
        output = output.append(row_to_add)
        print(output)
        #print("Avg.: \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \n", electiveAppWT, electiveScanWT, urgentScanWT, OT,
         #     objectiveValue)

        # print results
        # inputFileName = "/Users/wouterdewitte/Documents/1e Master Business Engineering_Data Analytics/Semester 2/Simulation Modelling and Analyses/Project/project SMA 2022 student code /input-S1-14.txt";
        # todo: print the output you need to a .txt file
        # fclose(file);

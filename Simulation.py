from Helper import *
import numpy as np
import pandas as pd
from sys import exit


class Slot():
    # all information about slots
    # Variables and parameters
    global startTime, appTime, slotType, patientType

    def __init__(self, startTime, appTime, slotType, patientType):
        self.startTime = startTime      # the actual start time independent of scheduling rule
        self.appTime = appTime          # time the patient receives and DEPENDS ON THE RULE (same as starttime for fifo)
        self.slotType = slotType        # type of slot (0=none, 1=elective, 2=urgent within normal working hours, 3=urgent in overtime)
        self.patientType = patientType  # 1 (= elective) or 2 (= urgent) or 0 to represent a break

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

    #For printing while testing/debugging    
    def __repr__(self):
        return f' {self.callWeek}, {self.callDay}, {self.scanWeek}, {self.scanDay}, {self.scanTime}, {self.patientType}'

    # Functions
    def getAppWT(self):
        if self.slotNr != -1:
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
        avgUrgentScanWT, avgOT, numberOfElectivePatientsPlanned, numberOfUrgentPatientsPlanned, W, R, rule, weekSchedule, Warm_Up

    #(un)comment the strategy you want to use   
    # Method 1
    #inputFileName = "./data/scenario1_14Slots.txt"
    inputFileName = "./data/scenario1_10Slots.txt"
    #inputFileName = "./data/scenario1_20Slots.txt"
    #inputFileName = "./data/scenario1_16Slots.txt"

    # Method 2
    #inputFileName = "./data/scenario2_10Slots.txt"
    #inputFileName = "./data/scenario2_12Slots.txt"
    #inputFileName = "./data/scenario2_16Slots.txt"
    #inputFileName = "./data/scenario2_18Slots.txt"
    #inputFileName = "./data/scenario2_20Slots.txt"

    # Method 3
    #inputFileName = "./data/scenario3_10Slots.txt"
    #inputFileName = "./data/scenario3_12Slots.txt"
    #inputFileName = "./data/scenario3_16Slots.txt"
    #inputFileName = "./data/scenario3_20Slots.txt"

    Warm_Up = 150
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
    W = 300      # number of weeks to simulate = runlength
    R = 5        # number of replications
    rule = 1    # integer indicating which scheduling rule you are testing

    avgElectiveAppWT = 0
    avgElectiveScanWT = 0
    avgUrgentScanWT = 0
    avgOT = 0
    numberOfElectivePatientsPlanned = 0
    numberOfUrgentPatientsPlanned = 0

    weekSchedule = dict()
    for d in range(0, D):
        weekSchedule[d] = dict()
        for s in range(0, S):
            weekSchedule[d][s] = 0
    
    # variables specific to one simulation run (patients list and some objectives)
    patients = [] 
    movingAvgElectiveAppWT = [0] * W
    movingAvgElectiveScanWT = [0] * W
    movingAvgUrgentScanWT = [0] * W
    movingAvgOT = [0] * W

    # Functions
    def setWeekSchedule(self):
        # Read and set the slot types (0=none, 1=elective, 2=urgent within normal working hours)
        global slotLength;
        # 1) read in the input file indicating the week schedule
        schedule = pd.read_csv(inputFileName, sep = '\t', header = None)
        # 2) loop over the different time slot each day and assign the slot type defined in the schedule
        for s in range(0, 32):
            for d in range(0, D):
                weekSchedule[d][s] = Slot(0, 0, schedule[d][s], schedule[d][s])
        # 3) Set the type of the overtime slots (3=urgent in overtime)
        for d in range(0, D):
            for s in range(32, S):
                weekSchedule[d][s] = Slot(0, 0, 3, 2)
        run2 = 0        
        # 4) set the start and the appointment time of the slot
        for d in range(0,D):
            time = 8          # as the first slot is at 8 am
            for s in range(0,S):
                # define the start time of the slot
                weekSchedule[d][s].startTime = time
                # define the appointment time of the slot
                # A) for non-elective slot types: appointment time = slot start time
                if(weekSchedule[d][s].slotType != 1):
                    weekSchedule[d][s].appTime = time
                # B) for elective slots: appointment time depends on the RULE
                else:
                    if (rule == 1):  # FIFO rule
                        weekSchedule[d][s].appTime = time
                        # update the time variable
                    elif (rule == 2): # Bailey-Welch rule 
                        K = 2  # number of patients that are asigned to the first slot, can be adjusted
                        if s in range(0, K):
                            weekSchedule[d][s].appTime = 8
                        else:
                            #time = time + Normal_distribution(15,3)  # appoitment time of the previous patient + scan time will be the appoitment time of the next patient
                            weekSchedule[d][s].appTime = time - Normal_distribution(15,3, setWeekSchedule_seed, run2)  # set this appointment time
                            run2 += 1
                    elif (rule == 3): # Blocking rule
                        K = 2 # number of blocks, fixed
                        if s in range(0,K):
                            weekSchedule[d][s].appTime = 8
                        if s % K != 0:
                            weekSchedule[d][s].appTime = time - slotLength
                        else:
                            #time = time + slotLength * K
                            weekSchedule[d][s].appTime = time
                    elif (rule == 4): # Benchmarking rule 
                        kAlpha = 0.5  # designates how much the possible deviations in the scan duration are taken into account, assumption
                        SD = 3  # standard deviation is fixed
                        if (time - kAlpha * SD < 8):
                            weekSchedule[d][s].appTime = 8
                        else:
                            weekSchedule[d][s].appTime = time - kAlpha * SD
                time = time + slotLength
                # skip to the end of the lunch break if it is lunch
                if(time == 12):
                    time = 13

    def resetSystem(self):
        global avgElectiveAppWT, run, avgElectiveScanWT, avgUrgentScanWT, avgOT, numberOfElectivePatientsPlanned, numberOfUrgentPatientsPlanned, patients, \
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

    def getRandomScanType(self, arrivalTime_seed):
        r = arrivalTime_seed.rand()
        type = -1
        for x in range(0, 5):
            if type != -1:
                break
            if r < cumulativeProbUrgentType[x]:
                type = x
        return type


    # the next function generates a patient list
    def generatePatients(self):
        global arrivalTimeNext, counter, run, patientType, scanType, endTime, callTime, tardiness, duration, noShow,arrivalTime_seed,lambdaElective, lambdaUrgent, W, D
        counter = 0  # total number of patients so far
        
        # go over each week and each day and generate a patient list depending on the day
        run = 0
        for w in range(0,W):
            for d in range(0,D):  # not on Sunday
                # generate ELECTIVE patients for this day
                if d < D - 1:  # not on Saturday either
                    arrivalTimeNext = 8 + Exponential_distribution(lambdaElective, arrivalTime_seed, run) * (17 - 8)
                    while arrivalTimeNext < 17:  # desk open from 8h until 17h
                        # fill in as many information as you can yourself
                        patientType = 1     # elective
                        scanType = 0        # no scan type
                        callTime = arrivalTimeNext  # set call time, i.e. arrival event time
                        tardiness = Normal_distribution(meanTardiness, stdevTardiness, arrivalTime_seed, run) / 60.0  # in practice this is not known yet at time  of call
                        noShow = not bool(Bernouilli_distribution(probNoShow, arrivalTime_seed, run))  # in practice this is not known yet at time of call
                        duration = Normal_distribution(meanElectiveDuration, stdevElectiveDuration, arrivalTime_seed, run) / 60.0  # in practice this is not known yet at time of call

                        # add the fields to the object and the patient ot the list
                        patient = Patient(counter, patientType, scanType, w, d, callTime, tardiness, noShow, duration)
                        patients.append(patient)
                        counter = counter + 1
                        run += 1
                        arrivalTimeNext = arrivalTimeNext + Exponential_distribution(lambdaElective, arrivalTime_seed, run) * (17 - 8)  # arrival time of next patient (if < 17h)
                # generate URGENT patients for this day
                if ((d == 3) | (d == 5)):
                    lambda_local = lambdaUrgent[1]  # on Wed and Sat, only half a day
                    endTime = 12
                else:
                    lambda_local = lambdaUrgent[1]
                    endTime = 17
                run += 1
                arrivalTimeNext = 8 + Exponential_distribution(lambda_local, arrivalTime_seed, run) * (endTime - 8)
                while arrivalTimeNext < endTime:  # desk open from 8h until 17h
                    patientType = 2  # urgent
                    scanType = self.getRandomScanType(arrivalTime_seed)  # set scan type
                    callTime = arrivalTimeNext  # set arrival time, i.e. arrival event time
                    tardiness = 0  # urgent patients have an arrival time = arrival event time
                    noShow = False  # urgent patients are never no-show
                    duration = Normal_distribution(meanUrgentDuration[scanType], stdevUrgentDuration[scanType], arrivalTime_seed, run) / 60.0  # in practice this is not known yet at time of arrival
                    patient = Patient(counter, patientType, scanType, w, d, callTime, tardiness, noShow, duration)
                    patients.append(patient)
                    counter = counter + 1
                    run += 1
                    arrivalTimeNext = arrivalTimeNext + Exponential_distribution(lambda_local, arrivalTime_seed, run) * (endTime - 8)  # arrival time of next patient (if < 17h)

    def getNextSlotNrFromTime(self, day, patientType, time):
        found = False
        slotNr = -1
        for s in range(0, S):
            if found:
                break
            if((weekSchedule[day][s].appTime > time) and (patientType == weekSchedule[day][s].patientType)):
                found = True
                slotNr = s

        if (found == False):
            print("NO SLOT EXISTS DURING TIME %.2f \n", time)
            exit(0)
        return slotNr


    # sort arrival events (= patient list) on arrival 
    # time (call time for elective patients, arrival time for urgent)
    def schedulePatients(self):
        global inputFileName, D,run, amountOTSlotsPerDay, S, slotLength, lambdaElective, meanTardiness, stdevTardiness, probNoShow, meanElectiveDuration, \
            stdevElectiveDuration, lambdaUrgent, probUrgentType, cumulativeProbUrgentType, meanUrgentDuration, stdevUrgentDuration, weightEl, weightUr, \
            d, s, w, r, patients, patient, movingAvgElectiveAppWT, movingAvgElectiveScanWT, movingAvgUrgentScanWT, movingAvgOT, avgElectiveAppWT, avgElectiveScanWT, \
            avgUrgentScanWT, avgOT, numberOfElectivePatientsPlanned, numberOfUrgentPatientsPlanned, W, R, rule, weekSchedule

        # this ranks all patients based upon the callWeek first, callDay then, etc. 
        # for patientType 2 is more important than 1 
        patients.sort(key=lambda x: (x.callWeek, x.callDay, x.callTime, -x.patientType))
        
        # create 3 new variables to indicate first available slot in the agenda
        week = [0,0]     # week of the next available slot {elective,urgent}
        day = [0,0]      # day of the next available slot {elective,urgent}
        slot = [0,0]     # slotNr of the next available slot {elective,urgent}
        
        # find first slot of each patient type
        # (note, we assume each day (i.e. also day 0) has at least one slot of each patient type!)
        # A) elective
        found = False
        d=0
        for s in range(0,S):
            if(found != True):
                if(weekSchedule[d][s].patientType == 1):
                    day[0] = d
                    slot[0] = s
                    found = True
        
        # B) Urgent
        found = False
        for s in range(0,S):
            if(found != True):
                if(weekSchedule[d][s].patientType == 2):
                    day[1] = d
                    slot[1] = s
                    found = True
        
        # go over SORTED patient list and assign slots
        
        # keep track of week to know when to update moving average elective appointment waiting time
        previousWeek = 0
        numberOfElective = 0
        numberOfElectivePerWeek = 0
        
        # loop through all the patients, this is possible because it is an
        # ordered list
        for patient in patients:

            # set index i dependent on the patient type
            # to know which type of slot we have to look at
            i = patient.patientType - 1

            # if still within the planning horizon, start looking for a slot:
            if(week[i] < W):


                # determine week where we start searching for a slot
                # if the patient called after the current week, start looking
                # in the patients callWeek (same principle for day and time)
                if(patient.callWeek > week[i]):
                    week[i] = patient.callWeek
                    day[i] = 0
                    slot[i] = self.getNextSlotNrFromTime(day[i], patient.patientType, 0)
                    # note we assume there is at least one slot of each patient type per day 
                    # => this line will find first slot of this type


                # determine day where we start searching for a slot
                if((patient.callWeek == week[i]) and (patient.callDay > day[i])):
                    day[i] = patient.callDay
                    slot[i] = self.getNextSlotNrFromTime(day[i], patient.patientType, 0)
                    # note we assume there is at least one slot of each patient type per day 
                    # => this line will find first slot of this type

                # determine slot
                if((patient.callWeek == week[i]) and (patient.callDay == day[i])
                   and (patient.callTime >= weekSchedule[day[i]][slot[i]].appTime)):

                    # 1) find last slot on day "day[i]"
                    found = False
                    slotNr = -1
                    s = S - 1
                    for s in range(S-1, -1, -1):
                        if((found != True)):
                            if(weekSchedule[day[i]][s].patientType == patient.patientType):
                                found = True
                                slotNr = s


                    # 2) urgent patients have to be treated on the same day 
                    # either in normal hours or in overtime
                    # !! make sure there are enough overtime slots
                    
                    # for elective patients: check if the patient call time is before the last slot, 
                    # i.e. if the patient can be planned on day "day[i]"
                    
                    # for urgent patients or elective with a free slot that day
                    if((patient.patientType == 2) or (patient.callTime < weekSchedule[day[i]][slotNr].appTime)):
                        slot[i] = self.getNextSlotNrFromTime(day[i], patient.patientType, patient.callTime)
                    
                    # for elective patients with no free slot available
                    else:
                        # determine the next day
                        if(day[i] < D - 1):
                            day[i] = day[i] + 1
                        
                        else:
                            day[i] = 0
                            week[i] = week[i] + 1
                        # find the first slot on the next day (if within the planning horizon)
                        if(week[i] < W):
                            slot[i] = self.getNextSlotNrFromTime(day[i], patient.patientType, 0)
                    
                
                # schedule the patient to selected slot
                patient.scanWeek = week[i]
                patient.scanDay = day[i]
                patient.slotNr = slot[i]
                patient.appTime = weekSchedule[day[i]][slot[i]].appTime
                
                
                # update moving average elective appointment waiting time
                if (patient.patientType == 1):
                    if (previousWeek < week[i]):
                        movingAvgElectiveAppWT[previousWeek] = movingAvgElectiveAppWT[previousWeek] / numberOfElectivePerWeek
                        numberOfElectivePerWeek = 0
                        previousWeek = week[i]

                    wt = patient.getAppWT()
                    movingAvgElectiveAppWT[week[i]] = movingAvgElectiveAppWT[week[i]] + wt
                    numberOfElectivePerWeek += 1
                    avgElectiveAppWT += wt
                    numberOfElective += 1

                # set next slot of the current patient type
                found = False
                startD = day[i]
                startS = slot[i] + 1
                
                # update the week, day and slot we are currently looking at
                # this is the next available slot for this patientType
                for w in range(week[i], W):
                    if(found != True):
                        for d in range(startD, D):
                            if(found != True):
                                for s in range(startS, S):
                                    if (found != True):
                                        if(weekSchedule[d][s].patientType == patient.patientType):
                                            week[i] = w
                                            day[i] = d
                                            slot[i] = s
                                            found = True
                        
                                startS = 0
                    
                        startD = 0
                
                # if no slot is found, we are at the end of the scheduling horizon
                if(found != True):
                    week[i] = W
        
        
        # update moving average elective appointment waiting time in last week
        movingAvgElectiveAppWT[W-1] = movingAvgElectiveAppWT[W-1] / numberOfElectivePerWeek
        # calculate objective value
        avgElectiveAppWT = avgElectiveAppWT / numberOfElective


    def sortPatientsOnAppTime(self):
        patients.sort(key=lambda x: (x.scanWeek, x.scanDay, x.appTime, x.callWeek, x.callDay, x.callTime, -x.patientType))
        i = 0
        for patient in patients:
            if patient.scanWeek == -1:
                patients.insert(-1, patients.pop(i))
        i += 1

    def runOneSimulation(self):
        global prevWeek, prevDay,run, numberOfPatientsWeek, numberOfPatients, arrivalTime, wt, prevScanEndTime, prevIsNoShow, \
            avgUrgentScanWT, movingAvgOT, avgElectiveScanWT,arrivalTime_seed, movingAvgUrgentScanWT, movingAvgElectiveScanWT, avgOT, D, W, movingAvgElectiveAppWT, r, R

        self.generatePatients() # create patient arrival events (elective patients call, urgent patients arrive at the hospital)
        self.schedulePatients() # schedule urgent and elective patients in slots based on their arrival events => determine the appointment wait time
        self.sortPatientsOnAppTime() # sort patients on their appointment time (unscheduled patients are grouped at the end of the list)
        prevWeek = 0
        prevDay = -1
        numberOfPatientsWeek = [0,0]
        numberOfPatients = [0,0]
        prevScanEndTime = float(0)
        prevIsNoShow = bool(False)
        for patient in patients:
            if patient.scanWeek == -1:
                break # stop at the first unplanned patient because we then have visited all scheduled patients
            arrivalTime = float(patient.appTime + patient.tardiness)

            #Scan WT (only done for patients who actually show up)
            if patient.isNoShow == False:
                if ((patient.scanWeek != prevWeek) or (patient.scanDay != prevDay)):
                    patient.scanTime = arrivalTime
                elif(prevIsNoShow == True):
                    patient.scanTime = max(weekSchedule[patient.scanDay][patient.slotNr].startTime, max(prevScanEndTime, arrivalTime))
                else:
                    patient.scanTime = max(prevScanEndTime, arrivalTime)
                
                wt = patient.getScanWT()

                if(patient.patientType == 1):
                    movingAvgElectiveScanWT[patient.scanWeek] += wt
                else:
                    movingAvgUrgentScanWT[patient.scanWeek] += wt
                numberOfPatientsWeek[patient.patientType -1] +=1

                if(patient.patientType == 1):
                    avgElectiveScanWT += wt
                else:
                    avgUrgentScanWT += wt
                
                numberOfPatients[patient.patientType - 1] +=1

            #Overtime
            if((prevDay > -1) and (prevDay != patient.scanDay)):
                if((prevDay == 3) or (prevDay == 5)):
                    movingAvgOT[prevWeek] = movingAvgOT[prevWeek] + max(0.0, prevScanEndTime - 13)
                else:
                    movingAvgOT[prevWeek] = movingAvgOT[prevWeek] + max(0.0, prevScanEndTime - 17)
                if((prevDay == 3) or (prevDay == 5)):
                    avgOT += max(0.0, prevScanEndTime - 13)
                else:
                    avgOT += max(0.0, prevScanEndTime - 17)
            
            #Update moving averages if week ends
            if(prevWeek != patient.scanWeek):
                if(numberOfPatientsWeek[0 != 0]):
                    movingAvgElectiveScanWT[prevWeek] = movingAvgElectiveScanWT[prevWeek]/numberOfPatientsWeek[0]
                if(numberOfPatientsWeek[1] != 0):
                    movingAvgUrgentScanWT[prevWeek] = movingAvgUrgentScanWT[prevWeek]/numberOfPatientsWeek[1]
                movingAvgOT[prevWeek] = movingAvgOT[prevWeek] / D
                numberOfPatientsWeek[0] = 0
                numberOfPatientsWeek[1] = 0

            
            #set prev patient
            if(patient.isNoShow == True):
                prevIsNoShow = True
                if((patient.scanWeek != prevWeek) or (patient.scanDay != prevDay)):
                    prevScanEndTime = weekSchedule[patient.scanDay][patient.slotNr].startTime
            else:
                prevScanEndTime = patient.scanTime + patient.duration
                prevIsNoShow = False
            prevWeek = patient.scanWeek
            prevDay = patient.scanDay

        #update moving averages of the last week
        movingAvgElectiveScanWT[W-1] = movingAvgElectiveScanWT[W-1] / numberOfPatientsWeek[0]
        movingAvgUrgentScanWT[W-1] = movingAvgUrgentScanWT[W-1] / numberOfPatientsWeek[1]
        movingAvgOT[W-1] = movingAvgOT[W-1] / D
    
        #calculate objective values
        avgElectiveScanWT = avgElectiveScanWT / numberOfPatients[0]
        avgUrgentScanWT = avgUrgentScanWT / numberOfPatients[1]
        avgOT = avgOT / (D * W)

        column_names = ["week", "elAppWT", "elScanWT", "urScanWT", "OT"]
        output_average = pd.DataFrame(columns=column_names)
        for w in range(W):
            values_to_add = {'week': w, 'elAppWT': movingAvgElectiveAppWT[w], 'elScanWT': movingAvgElectiveScanWT[w],
                             'urScanWT': movingAvgUrgentScanWT[w], 'OT': movingAvgOT[w]}
            row_to_add = pd.Series(values_to_add, name="Average")
            output_average = output_average.append(row_to_add)
        path = "./data/output_correct/moving_average_10_FIFO_R" + str(appel) + ".xlsx"
        output_average.to_excel(path, sheet_name='output')

    # method called by the main (starts the whole simulation process):
    def runSimulations(self):
        global avgOT, avgElectiveAppWT, avgElectiveScanWT, avgUrgentScanWT, arrivalTime_seed, run, setWeekSchedule_seed, appel, movingAvgElectiveAppWT, \
        movingAvgElectiveScanWT, movingAvgUrgentScanWT, movingAvgOT, Warm_Up
        electiveAppWT_SS = 0
        electiveScanWT_SS = 0
        urgentScanWT_SS = 0
        OT_SS = 0
        OV_SS = 0

        # first set weekSchedule by filling in 2D slot array
        setWeekSchedule_seed = np.random.RandomState(40)
        self.setWeekSchedule()  # set cyclic slot schedule based on given input file
        column_names = ["r", "elAppWT", "elScanWT", "urScanWT", "OT", "OV"]
        output = pd.DataFrame(columns=column_names)
        # run R replications
        appel = 0
        for r in range(0, R):
            self.resetSystem()  # 2) reset all variables related to 1 replication
            arrivalTime_seed = np.random.RandomState((r+333) * 51 + 5)
            self.runOneSimulation()  # 3) run 1 simulation / replication
            avgElectiveAppWT_SS = 0
            avgElectiveScanWT_SS = 0
            avgUrgentScanWT_SS = 0
            avgOT_SS = 0
            for w in range(Warm_Up, W):
                avgElectiveAppWT_SS = avgElectiveAppWT_SS + movingAvgElectiveAppWT[w]
                avgElectiveScanWT_SS = avgElectiveScanWT_SS + movingAvgElectiveScanWT[w]
                avgUrgentScanWT_SS = avgUrgentScanWT_SS + movingAvgUrgentScanWT[w]
                avgOT_SS = avgOT_SS + movingAvgOT[w]

            avgElectiveAppWT_SS= avgElectiveAppWT_SS / (W - Warm_Up)
            avgElectiveScanWT_SS = avgElectiveScanWT_SS / (W - Warm_Up)
            avgUrgentScanWT_SS = avgUrgentScanWT_SS / (W - Warm_Up)
            avgOT_SS = avgOT_SS / (W - Warm_Up)

            electiveAppWT_SS = electiveAppWT_SS + avgElectiveAppWT_SS
            electiveScanWT_SS = electiveScanWT_SS + avgElectiveScanWT_SS
            urgentScanWT_SS =  urgentScanWT_SS + avgUrgentScanWT_SS
            OT_SS = OT_SS + avgOT_SS
            OV_SS = avgElectiveAppWT_SS * weightEl + avgUrgentScanWT_SS * weightUr


            #electiveAppWT = electiveAppWT + avgElectiveAppWT
            #electiveScanWT = electiveScanWT + avgElectiveScanWT
            #urgentScanWT = avgUrgentScanWT + urgentScanWT
            #OT = avgOT + OT
            #OV = avgElectiveAppWT_SS * weightEl + avgUrgentScanWT_SS * weightUr
            values_to_add = {'r': r, 'elAppWT': avgElectiveAppWT_SS, 'elScanWT': avgElectiveScanWT_SS,
                             'urScanWT': avgUrgentScanWT_SS, 'OT': avgOT_SS,
                             'OV': OV_SS}
            row_to_add = pd.Series(values_to_add, name="run " + str(r))
            output = output.append(row_to_add)
            appel += 1

        electiveAppWT_SS = electiveAppWT_SS / R
        electiveScanWT_SS = electiveScanWT_SS / R
        urgentScanWT_SS = urgentScanWT_SS / R
        OT_SS = OT_SS / R
        OV_SS = OV_SS / R
        objectiveValue_SS = electiveAppWT_SS * weightEl + urgentScanWT_SS * weightUr
        values_to_add = {'r': r, 'elAppWT': electiveAppWT_SS, 'urScanWT': urgentScanWT_SS, 'elScanWT': electiveScanWT_SS,
                         'OT': OT_SS,
                         'OV': objectiveValue_SS}
        row_to_add = pd.Series(values_to_add, name="Average")
        output = output.append(row_to_add)
        path = "./data/output_correct/output_Strategy3b_10_FIFO.xlsx"
        #output.to_excel(path, sheet_name='output')
        print(output)
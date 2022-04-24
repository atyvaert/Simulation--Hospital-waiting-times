from pickle import FALSE
from random import seed
import random
from Helper import *
import numpy as np
import pandas as pd

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
    # Variables and parameters
    global inputFileName, D, amountOTSlotsPerDay, S, slotLength, lambdaElective, meanTardiness, stdevTardiness, probNoShow, meanElectiveDuration, \
        stdevElectiveDuration, lambdaUrgent, probUrgentType, cumulativeProbUrgentType, meanUrgentDuration, stdevUrgentDuration, weightEl, weightUr, \
        d, s, w, r, patients, patient, movingAvgElectiveAppWT, movingAvgElectiveScanWT, movingAvgUrgentScanWT, movingAvgOT, avgElectiveAppWT, avgElectiveScanWT, \
        avgUrgentScanWT, avgOT, numberOfElectivePatientsPlanned, numberOfUrgentPatientsPlanned, W, R, rule


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
    meanUrgentDuration = [15, 17.5, 22.5, 30, 30]
    stdevUrgentDuration = [2.5, 1, 2.5, 1, 4.5]
    weightEl = 1.0 / 168.0  # objective weight elective
    weightUr = 1.0 / 9.0  # objective weight urgent scan

    inputFileName = ".../input-S1-14.txt"

    W = 10  # number of weeks to simulate = runlength
    R = 1  # number of replications
    rule = 1

    avgElectiveAppWT = 0
    avgElectiveScanWT = 0
    avgUrgentScanWT = 0
    avgOT = 0
    numberOfElectivePatientsPlanned = 0
    numberOfUrgentPatientsPlanned = 0

    weekSchedule = np.zeros((D, S))
    for row in weekSchedule:
        for elem in row:
            elem = Slot(0,0,0,0)
    patients = []
    movingAvgElectiveAppWT = [W]
    movingAvgElectiveScanWT = [W]
    movingAvgUrgentScanWT = [W]
    movingAvgOT = [W]



    # Functions
    def setWeekSchedule(self):
        # Read and set the slot types (0=none, 1=elective, 2=urgent within normal working hours)
        return 0

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
        patients.sort(key=lambda x: (x.scanWeek, x.scanDay, x.appTime, x.callWeek, x.callDay, x.callTime, -x.patientType))
        i = 0
        for patient in patients:
            if patient.scanWeek == -1:
                patients.insert(-1, patients.pop(i))
        i += 1

    def runOneSimulation(self):
        global prevWeek, prevDay, numberOfPatientsWeek, numberOfPatients, arrivalTime, wt, prevScanEndTime, prevIsNoShow
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
                if (patient.scanWeek != prevWeek or patient.scanDay != prevDay):
                    patient.scanTime = patient.arrivalTime
                elif(prevIsNoShow == True):
                    ## zal wel nog niet kloppen --> hangt af van Artur zijn invulling van zijn weekschedule
                    patient.scanTime = max(weekSchedule[patient.scanDay][patient.slotNr].startTime, max(prevScanEndTime, patient.arrivalTime))
                else:
                    patient.scanTime = max(prevScanEndTime, patient.arrivalTime)
                
                wt = patient.getScanWT()
                if(patient.pantientType == 1):
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
            if(prevDay > -1 and prevDay != patient.scanDay):
                if(prevDay == 3 or prevDay == 5):
                    movingAvgOT[prevWeek] += max(0.0, prevScanEndTime - 13)
                else:
                    movingAvgOT[prevWeek] += max(0.0, prevScanEndTime - 17)
                if(prevDay == 3 or prevDay == 5):
                    avgOT += max(0.0, prevScanEndTime - 13)
                else:
                    avgOT += max(0.0, prevScanEndTime - 17)
            
            #Update moving averages if week ends
            if(prevWeek != patient.scanWeek):
                movingAvgElectiveScanWT[prevWeek] = movingAvgElectiveScanWT[prevWeek]/numberOfPatientsWeek[0]
                movingAvgUrgentScanWT[prevWeek] = movingAvgUrgentScanWT[prevWeek]/numberOfPatientsWeek[1]
                movingAvgOT = movingAvgOT[prevWeek] / D
                numberOfPatientsWeek[0] = 0
                numberOfPatientsWeek[1] = 0
            
            #set prev patient
            if(patient.isNoShow == True):
                prevIsNoShow = True
                if(patient.scanWeek != prevWeek or patient.scanDay != prevDay):
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

            # print moving avg (UIT C++ CODE)
    # /*FILE *file = fopen("/Users/tinemeersman/Documents/project SMA 2022 student code /output-movingAvg.txt", "a"); // TODO: use your own directory
    # fprintf(file,"week \t elAppWT \t elScanWT \t urScanWT \t OT \n");
    # for(w = 0; w < W; w++){
    #     fprintf(file, "%d \t %.2f \t %.2f \t %.2f \t %.2f \n", w, movingAvgElectiveAppWT[w], movingAvgElectiveScanWT[w], movingAvgUrgentScanWT[w], movingAvgOT[w]);
    # }
    # fclose(file);*/

    def runSimulations(self):
        global avgOT, avgElectiveAppWT, avgElectiveScanWT, avgUrgentScanWT
        electiveAppWT = 0
        electiveScanWT = 0
        urgentScanWT = 0
        OT = 0
        OV = 0
        self.setWeekSchedule()  # set cyclic slot schedule based on given input file
        column_names = ["r", "elAppWT", "elScanWT", "urScanWT", "OT", "OV"]
        output = pd.DataFrame(columns=column_names)
        #print("r \t elAppWT \t elScanWT \t urScanWT \t OT \t OV \n")
        # run R replications 
        for r in range(0, R):
            self.resetSystem()  # reset all variables related to 1 replication
            random.seed(r)  # set seed value for random value generator
            self.runOneSimulation()  # run 1 simulation / replication
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

if __name__ == "__main__":
    testing = simulation()
    testing.runSimulations()
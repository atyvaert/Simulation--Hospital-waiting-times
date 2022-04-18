class simulation():
    # Variables and parameters
    global inputFileName, D, amountOTSlotsPerDay, S, slotLength, lambaElective, meanTardiness, stdevTardiness, probNoShow, meanElectiveDuration, \
        stdevElectiveDuration, lambdaUrgent, probUrgentType, cumulativeProbUrgentType, meanUrgentDuration, stdevUrgentDuration, weightEl, weightUr, W, \
        R, d, s, w, r, rule;

    inputFileName = "/Users/wouterdewitte/Documents/1e Master Business Engineering_Data Analytics/Semester 2/Simulation Modelling and Analyses/Project/project SMA 2022 student code /input-S1-14.txt";
    D = 6; #number of days per week (NOTE: Sunday not included! so do NOT use to calculate appointment waiting time)
    amountOTSlotsPerDay = 10; #number of overtime slots per day
    S = 32 + amountOTSlotsPerDay; #number of slots per day
    slotLength = 15.0 / 60.0; #duration of a slot (in hours)
    lambaElective = 28.345;
    meanTardiness = 0;
    stdevTardiness = 2.5;
    probNoShow = 0.02;
    meanElectiveDuration = 15;
    stdevElectiveDuration = 3;
    lambdaUrgent = [2.5, 1.25];
    probUrgentType = [0.7, 0.1, 0.1, 0.05, 0.05];
    cumulativeProbUrgentType = [0.7, 0.8, 0.9, 0.95, 1.0];
    meanUrgentDuration[5] = [15, 17.5, 22.5, 30, 30];
    stdevUrgentDuration[5] = [2.5, 1, 2.5, 1, 4.5];
    weightEl = 1.0 / 168.0; #objective weight elective
    weightUr = 1.0 / 9.0 #objective weight urgent scan

    # Variables within one simulation
    global patients, patient, movingAvgElectiveAppWT, movingAvgElectiveScanWT, movingAvgUrgentScanWT, movingAvgOT, avgElectiveAppWT, avgElectiveScanWT, \
        avgUrgentScanWT, avgOT, numberOfElectivePatientsPlanned, numberOfUrgentPatientsPlanned;


    # Functions
    def setWeekSchedule(self):
        return 0;
    def resetSystem(self):
        return 0;
    def getRandomScanType(self):
        return 0;
    def generatePatients(self):
        return 0;
    def getNextSlotNrFromTime(self,  day, patientType, time):
        return 0;
    def schedulePatients(self):
        return 0;
    def sortPatientsOnAppTime(self):
        return 0;
    def runOneSimulation(self):
        return 0;
    def runSimulations(self):
        return 0;

class Slot:
    # Variables and parameters
    global startTime, appTime, slotType, patientType;

    # Functions

class Patient():

    # Initializing

    def __init__(self, nr, patientType, scanType, callWeek, callDay, callTime, tardiness, isNoShow, duration):
        self.nr = nr;
        self.patientType = patientType;
        self.scanType = scanType;
        self.callWeek = callWeek;
        self.callDay = callDay;
        self.callTime = callTime;
        self.scanWeek = -1;
        self.scanDay = -1;
        self.slotNr = -1;
        self.appTime = -1;
        self.tardiness = tardiness;
        self.isNoShow = isNoShow;
        self.duration = duration;
        self.scanTime = -1.0;

    # Functions
    def getAppWT(self):
        if self.scanTime != -1:
            return (((self.scanWeek - self.callWeek)*7 + self.scanDay - self.callDay)*24 + self.appTime - self.callTime); # in hours
        else:
            print("CAN NOT CALCULATE APPOINTMENT WT OF PATIENT", self.nr);
            exit(1);

    def getScanWT(self):
        if self.scanTime != 0:
            wt = 0;
            if self.patientType == 1:
                wt = self.scanTime - (self.appTime + self.tardiness);
            else:
                wt = self.scanTime - self.callTime;
            return max(0.0,wt);
        else:
            print("CAN NOT CALCULATE SCAN WT OF PATIENT", self.nr); # in hours
            exit(1);

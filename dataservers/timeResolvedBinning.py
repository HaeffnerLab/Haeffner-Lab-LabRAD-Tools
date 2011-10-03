from dataProcess import dataProcess
import numpy as np

class timeResolvedBinning(dataProcess):
    """
    Bins the time resolved data
    @inputs: timelength is the timelength of the original trace where points are recorded with a certain resolution
    """
    name = 'timeResolvedBinning'
    inputsRequired = ['timelength','resolution']
    inputsOptional = [('bintime',100*10**-6)]
    
    def initialize(self):
        self.bintime = self.inputDict['bintime']
        self.timelength = self.inputDict['timelength']
        self.resolution = self.inputDict['resolution']
        self.binNumber = np.ceil(self.timelength/self.bintime) #number of bins
        self.result = np.zeros([self.binNumber,2])
        self.result[:,0] = np.arange(self.binNumber) * self.bintime

    def processNewData(self, newdata):
        newdata = newdata.asarray
        nonZeroPositions = newdata[:,0]
        correspondingElements = newdata[:,1]
        print nonZeroPositions
        print correspondingElements
        #expanding compressed data to bit representation
        correspondingElements = map(self.converter , correspondingElements)
        #for every bit, calculate the time of photon arrival and add to appropriate bin
        for byteNumber,bytePosition in enumerate(nonZeroPositions):
            byte = correspondingElements[byteNumber]
            for bitposition in byte.nonzero()[0]:
                arrivalTime = (bytePosition * 16 + bitposition)*self.resolution
                binNumber = np.floor(arrivalTime / self.bintime)
                print self.result.shape
                print binNumber
                self.result[binNumber,1] += 1
                
    def getResult(self):
        return self.result

    @staticmethod
    #goes from 255 to [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1]
    def converter(x):
        str = bin(x)[2:].zfill(16)
        l = [int(s) for s in str]
        return np.array(l)
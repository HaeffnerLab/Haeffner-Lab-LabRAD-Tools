import numpy
from hardwareConfiguration import hardwareConfiguration

class Sequence():
    """Sequence for programming pulses"""
    def __init__(self, parent):
        self.ddsChannelTotal = hardwareConfiguration.ddsChannelTotal
        self.timeResolution = hardwareConfiguration.timeResolution
        self.ddsSettings = {}
        self.parent = parent
        
    def addDDS(self, chan, start, setting):
        '''add DDS setting'''
        timeStep = self.secToStep(start)
        if self.ddsSettings.has_key(timeStep):
            #if dds settings already exist, check for duplicate entry
            if self.ddsSettings[timeStep][chan]: raise Exception ('Double setting at time {} for DDS channel {}'.format(timeStep, chan))
        else:
            #else, create it
            self.ddsSettings[timeStep] = numpy.zeros(self.ddsChannelTotal, dtype = numpy.uint32)
        self.ddsSettings[timeStep][chan] = setting

    def secToStep(self, sec):
        '''converts seconds to time steps'''
        return int( sec / self.timeResolution) 
    
    def progRepresentation(self):
        ddsSettings = self.parseDDS()
        return ddsSettings
    
    def userAddedDDS(self):
        return bool(len(self.ddsSettings.keys()))
    
    def parseDDS(self):
        '''
        uses the ddsSettings dictionary to create an easily programmable list in the form
        [buf_for_chan0, buf_for_chan1,...]
        The length of each bufstring is equal to the number of total number of dds settings because all the ttl settings are advanced together:
        If a setting doesn't change, it's repeated.
        During the parsing the necessary ttls to advance dds settings are added automatically.
        At the end of the pulse sequence, the ram position of dds is set again to the initial value of 0.
        '''
        if not self.userAddedDDS(): return None
        totalState = ['']*self.ddsChannelTotal
        state = numpy.zeros(self.ddsChannelTotal, dtype = numpy.uint32)
        for key,settings in sorted(self.ddsSettings.iteritems()):
            updated = settings.nonzero()
            state[updated] = settings[updated]
            for i in range(len(state)):
                totalState[i] += self.parent._intToBuf(state[i])
        #add termination
        for i in range(len(totalState)):
            totalState[i] +=  '\x00\x00'
        return totalState
    
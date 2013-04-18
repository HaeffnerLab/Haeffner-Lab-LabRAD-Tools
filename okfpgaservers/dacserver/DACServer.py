'''
### BEGIN NODE INFO
[info]
name = DAC Server
version = 1.0
description =
instancename = DAC Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20

### END NODE INFO
'''

import sys
from labrad.server import LabradServer, setting, Signal, inlineCallbacks
from twisted.internet import reactor
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred
from twisted.internet.threads import deferToThread
from scipy import interpolate
from scipy.interpolate import UnivariateSpline as UniSpline
from numpy import genfromtxt, arange, dot
from api import api
from DacConfiguration import hardwareConfiguration as hc

SERVERNAME = 'DAC Server'
SIGNALID = 270837

class Voltage( object ):
    def __init__( self, channel, analogVoltage = None, digitalVoltage = None ):
        self.channel = channel
        self.digitalVoltage = digitalVoltage
        self.analogVoltage = analogVoltage

    def program( self, setNum ):
        '''
        Compute the hex code to progam this voltage
        '''
        self.setNum = setNum
        if self.analogVoltage is not None:
            (vMin, vMax) = self.channel.allowedVoltageRange
            if self.analogVoltage < vMin: self.analogVoltage = vMin
            if self.analogVoltage > vMax: self.analogVoltage = vMax
            self.digitalVoltage = self.channel.computeDigitalVoltage(self.analogVoltage)
        self.hexRep = self.__getHexRep()
        
    def __getHexRep( self ):
        '''
        If pulse triggering is enabled in the configuration file,
        then always write set 1 to the DAC. However, still keep track
        of the set numbers to write them in order to the DAC.
        '''
        port = bin(self.channel.dacChannelNumber)[2:].zfill(5)

        if hc.pulseTriggered: setN = bin(self.setNum)[2:].zfill(10)
        else: setN = bin(1)[2:].zfill(10)

        value = bin(self.digitalVoltage)[2:].zfill(16)

        big = value + port + setN + '0'        
        return chr(int(big[8:16], 2)) + chr(int(big[:8],2))+ chr(int(big[24:32], 2)) + chr(int(big[16:24], 2))
        
class Queue( object ):
    def __init__( self ):
        self.currentSet = 1
        self.setDict = {i: [] for i in range(1, hc.maxCache + 1)}

    def advance( self ):
        self.currentSet = (self.currentSet % hc.maxCache) + 1

    def reset( self ):
        self.currentSet = 1

    def insert( self, v ):
        ''' Always insert voltages to the current queue position '''
        v.program(self.currentSet)
        self.setDict[self.currentSet].append(v)

    def get( self ):        
        v = self.setDict[self.currentSet].pop(0)
        return v

class DACServer( LabradServer ):
    """
    DAC Server
    Used for controlling DC trap electrodes
    """
    name = SERVERNAME
    onNewUpdate = Signal(SIGNALID, 'signal: ports updated', 's')
    registryPath = [ '', 'Servers', hc.EXPNAME + SERVERNAME ]
    currentPosition = 0
    CfileName = 'None Specified'
    
    @inlineCallbacks
    def initServer( self ):
        self.api = api()
        self.inCommunication = DeferredLock()
        self.registry = self.client.registry        
        self.dacDict = dict(hc.elecDict.items() + hc.smaDict.items())
        self.queue = Queue()
        self.multipoles = hc.defaultMultipoles
        self.currentVoltages = {}
        self.initializeBoard()
        self.listeners = set() 
        yield self.setCalibrations()
        self.setPreviousControlFile()

    def initializeBoard(self):
        connected = self.api.connectOKBoard()
        if not connected:
            raise Exception ("FPGA Not Found")     

    @inlineCallbacks
    def setCalibrations( self ):
        ''' Go through the list of sma outs and electrodes and try to detect calibrations '''
        yield self.registry.cd(self.registryPath + ['Calibrations'], True)
        subs, keys = yield self.registry.dir()
        print 'Calibrated channels: ', subs
        for chan in self.dacDict.values():
            chan.voltageList = []
            c = [] # list of calibration coefficients in form [c0, c1, ..., cn]
            if str(chan.dacChannelNumber) in subs:
                yield self.registry.cd(self.registryPath + ['Calibrations', str(chan.dacChannelNumber)])
                dirs, coeffs = yield self.registry.dir()
                for n in range( len(coeffs) ):
                    e = yield self.registry.get( 'c'+str(n) )
                    c.append(e)
                chan.calibration = c
            else:
                (vMin, vMax) = chan.boardVoltageRange
                prec = hc.PREC_BITS
                chan.calibration = [2**(prec - 1), float(2**(prec))/(vMax - vMin) ]
    
    @inlineCallbacks
    def setPreviousControlFile( self ):
        try:
            yield self.registry.cd(self.registryPath)
            CfilePath = yield self.registry.get('MostRecentCfile')
            yield self.setMultipoleControlFile(0, CfilePath)
        except: 
            self.multipoleMatrix = {k: {j: [.1] for j in self.multipoles} for k in hc.elecDict.keys()} # if no previous Cfile was set, set all entries to 0.1
            self.numCols = 1
            yield self.registry.cd(self.registryPath + ['None Specified'])
            yield self.setMultipoleValues(0, [(k, 0) for k in self.multipoles])
            yield self.setIndividualAnalogVoltages(0, [(k, 0) for s in hc.smaDict.keys()])

    @inlineCallbacks
    def setPreviousVoltages( self ):
        ''' Try to set previous voltages used with current Cfile '''
        yield self.registry.cd(self.registryPath + [self.CfileName], True)
        try: self.currentPosition = yield self.registry.get('position')
        except: self.currentPosition = 0
        
        try: ms = yield self.registry.get('MultipoleSet')         
        except: ms = [(k, 0) for k in self.multipoles] # if no previous multipole values have been recorded, set them to zero. 
        yield self.setMultipoleValues(0, ms)      
        
        yield self.registry.cd(self.registryPath + [self.CfileName, 'smaVoltages'], True)
        for k in hc.smaDict.keys():
            try: av = yield self.registry.get(k)
            except: av = 0. # if no previous voltage has been recorded, set to zero. 
            yield self.setIndividualAnalogVoltages(0, [(k, av)])

    @setting( 0, "Set Multipole Control File", CfilePath = 's')
    def setMultipoleControlFile(self, c, CfilePath):
        data = open(CfilePath)
        mults = data.readline().rstrip('\n').split(':')
        if len(mults) > 1: 
            self.multipoles = mults[1].split(',')
        else: 
            data = open(CfilePath)
        data = genfromtxt(data)
        self.numCols = data[1].size
        if self.numCols == 1: data = [[data[i]] for i in range(data.size)]
        self.multipoleMatrix = {elec: {mult: data[int(elec) + index*len(hc.elecDict) - 1] for index, mult in enumerate(self.multipoles)} for elec in hc.elecDict.keys()}
        self.positionList = data[-1]

        if sys.platform.startswith('linux'): self.CfileName = CfilePath.split('/')[-1]
        elif sys.platform.startswith('win'): self.CfileName = CfilePath.split('\\')[-1]
        
        yield self.setPreviousVoltages()
        yield self.registry.cd(self.registryPath)
        yield self.registry.set('MostRecentCfile', CfilePath)

    @setting( 1, "Set Multipole Values", ms = '*(sv): dictionary of multipole values')
    def setMultipoleValues(self, c, ms):
        """
        set should be a dictionary with keys 'Ex', 'Ey', 'U2', etc.
        """
        self.multipoleSet = {m: v for (m,v) in ms}
        voltageMatrix = {}
        for e in hc.elecDict.keys():
            voltageMatrix[e] = [0. for n in range(self.numCols)]
            for n in range(self.numCols):
                for m in self.multipoles: voltageMatrix[e][n] += self.multipoleMatrix[e][m][n] * self.multipoleSet[m]
        if self.numCols > 1:
            voltageMatrix = self.interpolateVoltageMatrix(voltageMatrix)
        self.voltageMatrix = voltageMatrix
        yield self.setVoltages(c, newPosition = self.currentPosition)

        yield self.registry.cd(self.registryPath + [self.CfileName], True)
        yield self.registry.set('MultipoleSet', ms)

    def interpolateVoltageMatrix( self, voltageMatrix ):
        # fix step size here
        numPositions = 10*(self.numCols - 1.)
        inc = (self.numCols-1)/numPositions
        partition = arange(0, (numPositions + 1) * inc, inc)
        splineFit = {elec: UniSpline(range(self.numCols) , voltageMatrix[elec], s = 0 ) for elec in hc.elecDict.keys()}
        interpolatedVoltageMatrix = {elec: splineFit[elec](partition) for elec in hc.elecDict.keys()}
        return interpolatedVoltageMatrix

    @inlineCallbacks
    def setVoltages(self, c, newPosition = currentPosition, writeSMAs = False):
        n = newPosition
        newVoltageSet = []
        for e in hc.elecDict.keys():
            av = self.voltageMatrix[e][n]
            newVoltageSet.append( (e, av) )

        # if changing DAC FPGA voltage set, write sma voltages. 
        if writeSMAs: 
            for s in hc.smaDict.keys(): newVoltageSet.append( (s, self.currentVoltages[s]) )
        yield self.setIndividualAnalogVoltages(c, newVoltageSet)
        newVoltageSet.append(newVoltageSet[len(newVoltageSet)-1])
        self.currentPosition = n

        yield self.registry.cd(self.registryPath + [self.CfileName])
        yield self.registry.set('position', self.currentPosition)

    @inlineCallbacks
    def writeToFPGA(self, c):
        yield self.resetFIFODAC()
        for i in range(len(self.queue.setDict[self.queue.currentSet])):
            v = self.queue.get()            
            yield self.setDACVoltages(v.hexRep)
            print v.channel.name, v.analogVoltage
            self.currentVoltages[v.channel.name] = v.analogVoltage
            self.notifyOtherListeners(c)

    @inlineCallbacks
    def setDACVoltages(self, stringy):
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.setDACVoltage, stringy)
        # self.api.setDACVoltage(stringy)
        self.inCommunication.release()
    
    @inlineCallbacks
    def resetFIFODAC(self):
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.resetFIFODAC)
        # self.api.resetFIFODAC()
        self.inCommunication.release()            

    @setting( 2, "Set Digital Voltages", digitalVoltages = '*v', setNum = 'i', returns = '')
    def setDigitalVoltages( self, c, digitalVoltages, setNum):
        """
        Pass digitalVoltages, a list of digital voltages to update.
        Currently, there must be one for each port.
        """
        l = zip(self.dacDict.keys(), digitalVoltages)
        self.setIndivDigVoltages(c, l, setNum)

    @setting( 3, "Set Analog Voltages", analogVoltages = '*v', setNum = 'i', returns = '')
    def setAnalogVoltages( self, c, analogVoltages, setNum):
        """
        Pass analogVoltages, a list of analog voltages to update.
        Currently, there must be one for each port.
        """
        l = zip(self.dacDict.keys(), analogVoltages)
        yield self.setIndivAnaVoltages(c, l, setNum)

    @setting( 4, "Set Individual Digital Voltages", digitalVoltages = '*(si)', returns = '')
    def setIndividualDigitalVoltages(self, c, digitalVoltages, setNum = 0):
        """
        Pass a list of tuples of the form:
        (portNum, newVolts)
        """
        for (port, dv) in digitalVoltages:
            self.queue.insert(Voltage(self.dacDict[port], digitalVoltage = dv))
        yield self.writeToFPGA(c)

    @setting( 5, "Set Individual Analog Voltages", analogVoltages = '*(sv)', returns = '')
    def setIndividualAnalogVoltages(self, c, analogVoltages):
        """
        Pass a list of tuples of the form:
        (portNum, newVolts)
        """
        for (port, av) in analogVoltages:
            self.queue.insert(Voltage(self.dacDict[port], analogVoltage = av))
            if self.dacDict[port].smaOutNumber:
                yield self.registry.cd(self.registryPath + [self.CfileName, 'smaVoltages'])
                yield self.registry.set(port, av)
        yield self.writeToFPGA(c)
    
    @setting( 6, "Set First Voltages")
    def setFirstVoltages(self, c):
        self.queue.reset()
        yield self.setVoltages(c, newPosition = self.currentPosition, writeSMAs = True)

    @setting( 7, "Set Next Voltages", newPosition = 'i')
    def setFutureVoltages(self, c, newPosition):
        self.queue.advance()
        yield self.setVoltages(c, newPosition, True)

    @setting( 8, "Set Next Voltages New Multipoles", multipoles = '*(sv)')
    def setNextVoltagesNewMultipoles(self, c, multipoles):
        self.queue.advance()
        yield self.setMultipoleValues(c, multipoles)

    @setting( 9, "Get Analog Voltages", returns = '*(sv)' )
    def getCurrentVoltages(self, c):
        """
        Return the current voltage
        """
        return self.currentVoltages.items()        

    @setting( 10, "Get Multipole Values",returns='*(s, v)')
    def getMultipoleValues(self, c):
        """
        Return a list of multipole voltages
        """
        return self.multipoleSet.items()

    @setting( 11, "Get Multipole Names",returns='*s')
    def getMultipoleNames(self, c):
        """
        Return a list of multipole voltages
        """
        return self.multipoles        

    @setting( 12, "Get Position", returns = 'i')
    def getPosition(self, c):
        return self.currentPosition

    def initContext(self, c):
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)
    
    def notifyOtherListeners(self, context):
        notified = self.listeners.copy()
        try: notified.remove(context.ID)
        except: pass
        self.onNewUpdate('Channels updated', notified)

if __name__ == "__main__":
    from labrad import util
    util.runServer( DACServer() )

"""
Notes for setting up DACSERVER:

example of a Cfile corresponding to a trap w/ 23 electrodes, 4 multipole values, and trap position of 850um:

multipoles: Ex, Ey, Ez, U2
Ex_1
Ex_2
.
.
.
Ex_23
Ey_1
.
.
.
U2_23
850

The first line, "multipoles: Ex, ...", lets you specify a unique set of multipoles for each Cfile. It is optional.
If you choose not to include it, the server will instead use the default multipoles specified in DacConfiguration.py


If you intend to do shuttling, place Cfiles next to each other:

multipoles: Ex, Ey, Ez, U2
Ex_1.1   Ex_1.2
Ex_2.1   Ex_2.2
.        .
.        .
.        .
Ex_23.1  .
Ey_1.1   .
.        .
.        .
.        .
U2_23.1  U2_23.2
850      900


    def getPlatformInfo(self):
        Figures out if running on Windows or Linux and returns platform
        dependent information
        if sys.platform.startswith('win'):
            portrange = range(1,20)
            prefix = 
            portstring = 'COM{}'
            message = 'cannot find'
        elif sys.platform.startswith('linux'):
            portrange = range(0,20)
            prefix = '/dev/'
            portstring = 'ttyUSB{}'
            message = 'could not open'
        elif sys.platform.startswith('darwin'):
            raise Exception("Not Implemented on Mac")
        return portrange,prefix,portstring,message
"""

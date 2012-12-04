'''
### BEGIN NODE INFO
[info]
name = CCTDAC Pulser v2
version = 1.0
description = 
instancename = CCTDAC Pulser v2

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20

### END NODE INFO
'''

from labrad.server import LabradServer, setting, Signal, inlineCallbacks 
from twisted.internet import reactor
from twisted.internet.defer import returnValue
from scipy import interpolate
from scipy.interpolate import UnivariateSpline as UniSpline
from time import *
from numpy import *
import sys
from cct.scripts.PulseSequences.advanceDACs import ADV_DAC

SERVERNAME = 'CCTDAC Pulser v2'
PREC_BITS = 16.
SIGNALID = 270837
NUMCHANNELS = 28
NOMINAL_VMIN = -40.
NOMINAL_VMAX = 40.

class Voltage(object):
    def __init__(self, n, i, v):        
        self.portNum = n
        self.setNum = i
        self.voltage = v
        
class AnalogVoltage(Voltage):
    def __init__(self, n, i, v):
        super(AnalogVoltage, self).__init__(n, i, v)
        self.type = 'analog'

class DigitalVoltage(Voltage):
    def __init__(self, n, i, v):
        super(DigitalVoltage, self).__init__(n, i, v)
        self.type = 'digital'
        
class Port():
    """
    Store information about ports
    
    calibrationCoeffs is a list of the form [c0, c1, ..., cn]
    such that
    dv = c0 + c1*(av) + c2*(av)**2 + ... + cn*(av)**n
    """
    def __init__(self, portNumber, physicalChannel = None, calibrationCoeffs = None):        
        self.portNumber = portNumber
        if physicalChannel is not None:
            self.physicalChannel = physicalChannel
        else:
            self.physicalChannel = portNumber
        self.analogVoltage = None
        self.digitalVoltage = None
        self.hexRep = None
        if not calibrationCoeffs:
            self.coeffs = [2**(PREC_BITS - 1), float(2**(PREC_BITS))/(NOMINAL_VMAX - NOMINAL_VMIN) ]
        else:
            self.coeffs = calibrationCoeffs
        
    def setVoltage(self, v):
        """
        setting digital voltages does not use soft -> hard mapping. this may make calibrating DACs easier. 
        """
        if v.type == 'analog':
            self.analogVoltage = float(v.voltage)
            dv = int(round(sum( [ self.coeffs[n]*self.analogVoltage**n for n in range(len(self.coeffs)) ] )))
            print 'Channel: ' + str(v.portNum)
            print 'Voltage Set: ' + str(v.setNum)
            print 'Analog Voltage Value: '+str(self.analogVoltage)
            print 'Digital Voltage Value: '+str(dv) + '\n'
            if dv < 0:
                self.digitalVoltage = 0 # Set to the minimum acceptable code
            elif dv > ( 2**PREC_BITS - 1 ): # Largest acceptable code
                self.digitalVoltage = (2**PREC_BITS - 1)
            else:
                self.digitalVoltage = dv
            self.hexRep = self.getHexRep(v.setNum, self.physicalChannel, self.digitalVoltage)
                                                
        if v.type == 'digital':
            dv = int(v.voltage)
            if dv < 0:
                self.digitalVoltage = 0
                self.analogVoltage = NOMINAL_VMIN
            elif dv > ( 2**PREC_BITS - 1 ):
                self.digitalVoltage = (2**PREC_BITS - 1)
                self.analogVoltage = NOMINAL_VMAX
            else:
                self.digitalVoltage = dv
            self.hexRep = self.getHexRep(v.setNum, self.portNumber, self.digitalVoltage)                        
    
    def getHexRep(self, setNum, portNum, value):
        port = self.f(portNum, 5)
        set = self.f(setNum, 10)
        value = self.f(value, 16)        
        big = value + port + set + [False]
        return self.g(big[8:16]) + self.g(big[:8]) + self.g(big[24:32]) + self.g(big[16:24])
            
    def f(self, num, bits): #binary representation of values in the form of a list
        listy = [None for i in range(bits)]
        for i in range(len(listy)):
            if num >= 2**(len(listy)-1)/(2**i):
                listy[i] = True
                num -= 2**(len(listy)-1)/(2**i)
            else:
                listy[i] = False 
        return listy

    def g(self, listy):
        num = 0
        for i in range(8):
            if listy[i]:
                num += 2**7/2**i
        return chr(num)                                    
        
class CCTDACServer( LabradServer ):
    """
    CCTDAC Server
    Used for controlling DC trap electrodes
    """
    name = SERVERNAME
    serNode = 'cctmain'
    onNewUpdate = Signal(SIGNALID, 'signal: ports updated', 's')
    multipoles = ['Ex1', 'Ey1', 'Ez1', 'U1', 'U2', 'U3', 'U4', 'U5']
    maxDACIndex = 126    
    DACIndex = 1
    nextDACIndex = 2 
    positionIndex = 0      
    
    @inlineCallbacks
    def initServer( self ):  
        from labrad.wrappers import connectAsync
        cxn = yield connectAsync()
        self.pulser = cxn.pulser
        self.registry = self.client.registry        
        self.createInfo() 
        self.listeners = set()
            
    @inlineCallbacks
    def createInfo( self ):             
        self.portList = []
        ''' See if there's a map between digital channels and analog channels.    
        cctdac.conf should be of the form:
        (software channel) -> (hardware channel)
        calibrations are stored wrt hardware channel
        '''
        try:
            with open('cctdac.conf') as f:                                
                map = [c.split('->') for c in f]
                mappedChannels = {}
                for (softChan, hardChan) in map:
                    mappedChannels[softChan] = int(hardChan)         
        except IOError as e:
            print "No port mapping found"    
                
        degreeOfCalibration = 3 # 1st order fit. update this to auto-detect 
        yield self.registry.cd(['', 'cctdac_pulser', 'Calibrations'])
        subs, keys = yield self.registry.dir()
        sbs = ''
        for s in subs:
            sbs += s + ', '
        print 'Calibrated channels: ' + sbs 
        for i in range(1, NUMCHANNELS + 1): # Port nums are indexed from 1
            c = [] # list of calibration coefficients in form [c0, c1, ..., cn]
            if str(i) in subs:
                yield self.registry.cd(['', 'cctdac_pulser', 'Calibrations', str(mappedChannels[str(i)])])
                for n in range( degreeOfCalibration + 1):
                    e = yield self.registry.get( 'c'+str(n) )                    
                    c.append(e)
                self.portList.append(Port(i, mappedChannels[str(i)], c))
            else:
                self.portList.append(Port(i)) # no preset calibration
        for p in self.portList:
            p.analogVoltage = 0 
        self.ionInfo = {}                       
        yield self.registry.cd(['', 'cctdac_pulser'])
        self.positionIndex = yield self.registry.get('IonPosition')
        Cpath = yield self.registry.get('MostRecent')
        yield self.setMultipoleControlFile(0, Cpath)
        ms = yield self.registry.get('MultipoleSet')
        yield self.setMultipoleValues(0, ms)
           
        
    @inlineCallbacks
    def sendToPulser(self, c, v):
        self.pulser.reset_fifo_dac()
        self.portList[v.portNum - 1].setVoltage(v)
        yield self.pulser.set_dac_voltage(self.portList[v.portNum - 1].hexRep)
        self.notifyOtherListeners(c)

    def initContext(self, c):
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)
    
    def notifyOtherListeners(self, context):   
        notified = self.listeners.copy()
        try: notified.remove(context.ID)
        except: pass
        self.onNewUpdate('Channels updated', notified)      

    @setting( 0 , "Set Digital Voltages", digitalVoltages = '*v', setNum = 'i', returns = '')
    def setDigitalVoltages( self, c, digitalVoltages, setNum):
        """
        Pass digitalVoltages, a list of digital voltages to update.
        Currently, there must be one for each port.
        """        
        l = zip(range(1, NUMCHANNELS + 1), digitalVoltages)
        self.setIndivDigVoltages(c, l, setNum)        

    @setting( 1 , "Set Analog Voltages", analogVoltages = '*v', setNum = 'i', returns = '')
    def setAnalogVoltages( self, c, analogVoltages, setNum):
        """
        Pass analogVoltages, a list of analog voltages to update.
        Currently, there must be one for each port.
        """        
        l = zip(range(1, NUMCHANNELS + 1), analogVoltages)
        yield self.setIndivAnaVoltages(c, l, setNum)

    @setting( 2, "Set Individual Digital Voltages", digitalVoltages = '*(iv)', setNum= 'i', returns = '')
    def setIndivDigVoltages(self, c, digitalVoltages, setNum):
        """
        Pass a list of tuples of the form:
        (portNum, newVolts)
        """
        if setNum == 1111: setNum = self.nextDACIndex     
        for (portNum, dv) in digitalVoltages:
            yield self.sendToPulser(c, DigitalVoltage(portNum, setNum, dv) )        

    @setting( 3, "Set Individual Analog Voltages", analogVoltages = '*(iv)', setNum= 'i', returns = '')
    def setIndivAnaVoltages(self, c, analogVoltages, setNum):
        """
        Pass a list of tuples of the form:
        (portNum, newVolts)
        """
        if setNum == 1111: setNum = self.nextDACIndex
        for (portNum, av) in analogVoltages:      
            yield self.sendToPulser(c, AnalogVoltage( portNum, setNum, av)) ###!!! setindex --> self.DACIndex

    @setting( 4, "Get Digital Voltages", returns = '*v' )
    def getDigitalVoltages(self, c):
        """
        Return a list of digital voltages currently in portList
        """
        return [ p.digitalVoltage for p in self.portlist ]            

    @setting( 5, "Get Analog Voltages", returns = '*v' )
    def getAnalogVoltages(self, c):
        """
        Return a list of the analog voltages currently in portList
        """
        return [ p.analogVoltage for p in self.portList ] # Yay for list comprehensions
    
    @setting( 6, "Set Multipole Control File", file = 's')
    def setMultipoleControlFile(self, c, file):                
        data = genfromtxt(file)
        numCols = data.size / (23 * 8)
        numPositions = (numCols - 1) * 10.
        sp = {}
        spline = {}
        x = range(numCols)                     
        p = arange(0, (numCols -1) * (1 + 1/numPositions), (numCols - 1)/numPositions)
        
        for i in range(23):
            n = 0
            sp[i] = {}
            spline[i] = {}      
            for j in self.multipoles:                
                sp[i][j] = UniSpline(x, data[i + n], s = 0 )                
                spline[i][j] = sp[i][j](p)                                
                n += 23                           
        self.spline = spline
        #yield self.advDACs(1)
        self.DACIndex = 1
        
        # get ion position info
        y = data[23 * 8]        
        fit = interpolate.interp1d(x, y, 'linear')
        self.pos = fit(p)

        self.ionInfo['positionIndex'] = self.positionIndex
        self.ionInfo['position'] = self.pos[self.positionIndex]
        self.ionInfo['ionRange']  = list(y)
        
        yield self.registry.cd(['', 'cctdac_pulser'])
        yield self.registry.set('MostRecent', file)        

    @setting( 7, "Set Multipole Values", ms = '*(sv): dictionary of multipole values')
    def setMultipoleValues(self, c, ms):
        """
        set should be a dictionary with keys 'Ex', 'Ey', 'U1', etc.
        """
        self.multipoleSet = {}
        for (k,v) in ms:
            self.multipoleSet[k] = v
            
        self.nextDACIndex = self.DACIndex # self.nextDACIndex = self.DACIndex + 1
        if self.nextDACIndex > self.maxDACIndex: self.nextDACIndex = 1
        yield self.setVoltages(c, self.positionIndex, self.nextDACIndex)
#        yield self.advDACs()
        self.DACIndex = self.nextDACIndex
        
        yield self.registry.cd(['', 'cctdac_pulser'])
        yield self.registry.set('MultipoleSet', ms)
    
    @setting( 8, "Get Multipole Voltages",returns='*(s,v)')
    def getMultipoleVolgates(self, c):
        """
        Return a list of multipole voltages
        """
        return self.multipoleSet.items()

    @setting( 20, "Get Multipole Values",returns='*(s,v)')
    def getMultipoleValues(self, c):
        """
        Return a list of multipole voltages
        """
        return self.multipoleSet.items()

    @setting( 9, "Shuttle Ion", position = 'i: position to move to')
    def shuttleIon(self, c, position):            
        n = self.DACIndex 
#        if position > self.positionIndex: ordering = range(self.positionIndex, position)
#        else: ordering = range(position, self.positionIndex)[::-1]
        if position > self.positionIndex:
            print range(self.positionIndex, position)
            for i in range(self.positionIndex, position):
                n+=1
                if n != self.maxDACIndex + 1:
                    yield self.setVoltages(c, i + 1, n)
                else:
                    yield self.setVoltages(c, i+1, 1)
                    self.nextDACIndex = self.maxDACIndex
                    yield self.advDACs()
                    yield self.advDACs(1)
                    self.DACIndex = 1
                    n = 1                            
        elif position < self.positionIndex:
            for i in range(position, self.positionIndex)[::-1]:
                n+=1
                if n != self.maxDACIndex + 1:
                    yield self.setVoltages(c, i + 1, n)
                else:
                    self.setVoltages(c, i+1, 1)
                    self.nextDACIndex = self.maxDACIndex
                    yield self.advDACs()
                    yield self.advDACs(1)
                    self.DACIndex = 1
                    n = 1        
        self.nextDACIndex = n
        yield self.advDACs()
        self.positionIndex = position
        self.ionInfo['position'] = self.pos[position]
        self.ionInfo['positionIndex'] = position

        yield self.registry.cd(['', 'cctdac_pulser'])
        yield self.registry.set('IonPosition', self.positionIndex)  
                
    @inlineCallbacks
    def advDACs(self, reset = 0):        
        """Pulse Sequence"""
        import labrad.types as T
        # pulser = yield self.pulser
        # seq = ADV_DAC(pulser)        
        # pulser.new_sequence()
        # params = {
        #           'startIndex': self.DACIndex,
        #           'stopIndex': self.nextDACIndex,
        #           'maxIndex': self.maxDACIndex,
        #           'duration': T.Value(10e-4, 's'),
        #           'reset': reset
        #          }
        # print params.items()
        # seq.setVariables(**params)
        # seq.defineSequence()
        # pulser.program_sequence()
        # pulser.start_single()
        # pulser.wait_sequence_done()
        # pulser.stop_sequence()
        # pulser.reset_timetags()
        # if reset: self.nextDACIndex = 1
        # self.DACIndex = self.nextDACIndex
        
    @setting( 10, "Set Voltages", newPosition = 'i', index = 'i')
    def setVoltages(self, c, newPosition = positionIndex, index = nextDACIndex):        
        n = newPosition
        realVolts = zeros(NUMCHANNELS)
        for i in range(5):
            realVolts[i] = self.portList[i].analogVoltage  
        for i in range(23): 
            for j in self.multipoles:                 
                realVolts[i + 5] += self.spline[i][j][n] * self.multipoleSet[j] 
        yield self.setAnalogVoltages(c, realVolts, index)
        self.positionIndex = n
        
    @setting(11, "Return Ion Info", returns = '(s, v), (s, i), (s, *v)')
    def retIonIndex(self, c):
        """
        returns info regarding the ion position         
        """
        return self.ionInfo.items()
    
    @setting( 13, "Return Number Wells", returns = 'i')
    def returnNumWells(self, c):
        """
        Return the number of wells as determined by the size of the current Cfile
        """
        self.numWells = 1
        return self.numWells       
        
    @setting(12, "do nothing")
    def doNone(self, c):
        pass
                
if __name__ == "__main__":
    from labrad import util
    util.runServer( CCTDACServer() )

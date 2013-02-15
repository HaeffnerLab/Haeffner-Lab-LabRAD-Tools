'''
### BEGIN NODE INFO
[info]
name = CCTDAC
version = 1.0
description =
instancename = CCTDAC

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
from cct.scripts.PulseSequences.advanceDACs import ADV_DACS
from DacConfiguration import hardwareConfiguration as hc

SERVERNAME = 'CCTDAC'
SIGNALID = 270837

class InvalidChannelError(Exception):
    def __init__(self, channel):
        self.channel = channel

class Voltage(object):
    def __init__(self, channel, analogVoltage = None, digitalVoltage = None):
        self.channel = channel
        self.digitalVoltage = digitalVoltage
        if analogVoltage is not None:
            self.analogVoltage = analogVoltage
            
    def program(self, setNum):
        '''
        Compute the hex code to progam this voltage
        '''
        self.setNum = setNum
        if self.analogVoltage is not None:
            c = self.channel.calibration
            (vMin, vMax) = self.channel.allowedVoltageRange
            if self.analogVoltage < vMin: self.analogVoltage = vMin
            if self.analogVoltage > vMax: self.analogVoltage = vMax
            self.digitalVoltage = int(round(sum( [c[n]*self.analogVoltage**n for n in range(len(c)) ] )))            
        self.hexRep = self.__getHexRep()
        
    def __getHexRep(self):
        '''
        If pulse triggering is enabled in the configuration file,
        then always write set 1 to the DAC. However, still keep track
        of the set numbers to write them in order to the DAC.
        '''
        port = self.__f(self.channel.dacChannelNumber, 5)

        if hc.pulseTriggered: set = self.__f(self.setNum, 10)
        else: set = self.__f(1, 10)

        value = self.__f(self.digitalVoltage, 16)
        big = value + port + set + [False]
        return self.__g(big[8:16]) + self.__g(big[:8]) + self.__g(big[24:32]) + self.__g(big[16:24])
            
    def __f(self, num, bits): # binary representation of values in the form of a list
        listy = [None for i in range(bits)]
        for i in range(len(listy)):
            if num >= 2**(len(listy)-1)/(2**i):
                listy[i] = True
                num -= 2**(len(listy)-1)/(2**i)
            else:
                listy[i] = False
        return listy

    def __g(self, listy):
        num = 0
        for i in range(8):
            if listy[i]:
                num += 2**7/2**i
        return chr(num)
        
class Queue(object):
    def __init__(self):
        self.currentSet = 1
        self.setDict = {}.fromkeys( range(1, hc.maxCache + 1), [] )

    def advance(self):
        self.currentSet = (self.currentSet % max) + 1

    def insert(self, v):
        ''' Always insert voltages to the current queue position '''
        v.program(self.currentSet)
        self.setDict[self.currentSet].append(v)

    def get(self):
        try:
            v = self.setDict[self.currentSet].pop(0)
            return v
        except IndexError:
            self.advance()
            return False


class CCTDACServer( LabradServer ):
    """
    CCTDAC Server
    Used for controlling DC trap electrodes
    """
    name = SERVERNAME
    serNode = 'cctmain'
    onNewUpdate = Signal(SIGNALID, 'signal: ports updated', 's')
    positionIndex = 0
    registryPath = ['', 'Servers', SERVERNAME]
    
    @inlineCallbacks
    def initServer( self ):
        from labrad.wrappers import connectAsync
        cxn = yield connectAsync()
        self.pulser = cxn.pulser
        self.registry = self.client.registry
        
        self.DACs = hc.DACDict
        self.queue = Queue()
        self.current = {}      
        self.createInfo()
        self.listeners = set()

    @inlineCallbacks
    def createInfo( self ):
        ''' Go through the list of sma outs and electrodes and try to detect calibrations '''
        degreeOfCalibration = 3 # 1st order fit. update this to auto-detect
        yield self.registry.cd(self.registryPath + ['Calibrations'])
        subs, keys = yield self.registry.dir()
        sbs = ''
        for s in subs: sbs += s + ', '
        print 'Calibrated channels: ' + sbs
        for chan in self.DACs.values():
            chan.voltageList = []
            c = [] # list of calibration coefficients in form [c0, c1, ..., cn]
            if str(chan.dacChannelNumber) in subs:
                yield self.registry.cd(self.registryPath + ['Calibrations', str(chan.dacChannelNumber)])
                for n in range( degreeOfCalibration + 1):
                    e = yield self.registry.get( 'c'+str(n) )
                    c.append(e)
                chan.calibration = c
            else:
                (vMin, vMax) = chan.boardVoltageRange
                prec = hc.PREC_BITS
                chan.calibration = [2**(prec - 1), float(2**(prec))/(vMax - vMin) ]

        yield self.registry.cd(self.registryPath)
        smaVoltages = yield self.registry.get('smaVoltages')
        self.current = {k: v for (k, v) in smaVoltages}
        Cpath = yield self.registry.get('MostRecent')
        yield self.setMultipoleControlFile(0, Cpath)
        ms = yield self.registry.get('MultipoleSet')
        yield self.setMultipoleValues(0, ms)        

    @inlineCallbacks
    def sendToPulser(self, c):
        '''
        Send the current queue to the dac
        '''
        self.pulser.reset_fifo_dac()
        for i in range(len(self.queue.setDict[self.queue.currentSet])):
            v = self.queue.get()            
            if v == None:
                break
            yield self.pulser.set_dac_voltage(v.hexRep)
            print v.channel.name, v.analogVoltage
            self.current[v.channel.name] = v.analogVoltage
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
        l = zip(range(1, hc.numDacChannels + 1), digitalVoltages)
        self.setIndivDigVoltages(c, l, setNum)

    @setting( 1 , "Set Analog Voltages", analogVoltages = '*v', setNum = 'i', returns = '')
    def setAnalogVoltages( self, c, analogVoltages, setNum):
        """
        Pass analogVoltages, a list of analog voltages to update.
        Currently, there must be one for each port.
        """
        l = zip(range(1, hc.numDacChannels + 1), analogVoltages)
        yield self.setIndivAnaVoltages(c, l, setNum)

    @setting( 2, "Set Individual Digital Voltages", digitalVoltages = '*(iv)', returns = '')
    def setIndividualDigitalVoltages(self, c, digitalVoltages, setNum):
        """
        Pass a list of tuples of the form:
        (portNum, newVolts)
        """
        for (port, dv) in digitalVoltages:
            self.queue.insert(Voltage(self.DACs[port], digitalVoltage = dv))
        yield self.sendToPulser(c)

    @setting( 3, "Set Individual Analog Voltages", analogVoltages = '*(sv)', returns = '')
    def setIndividualAnalogVoltages(self, c, analogVoltages):
        """
        Pass a list of tuples of the form:
        (portNum, newVolts)
        """
        for (port, av) in analogVoltages:
            self.queue.insert(Voltage(self.DACs[port], analogVoltage = av))
        yield self.sendToPulser(c)

    @setting( 4, "Get Analog Voltages", returns = '*(sv)' )
    def getCurrentVoltages(self, c):
        """
        Return the current voltage
        """
        return self.current.items()
    
    @setting( 6, "Set Multipole Control File", file = 's')
    def setMultipoleControlFile(self, c, file):                
        data = genfromtxt(file)
        numPositions = 10
        numCols = data[1].size
        numElectrodes = (data[:,1].size - 1) / len(hc.multipoles)
        inc = (numCols - 1.) / numPositions
        p = arange(0, (numPositions + 1) * inc, inc)
        
        sp = {}
        self.spline = {}           
        for k in self.DACs.keys():
            if self.DACs[k].trapElectrodeNumber: 
                n = 0
                sp[k] = {}
                self.spline[k] = {}      
                for j in hc.multipoles:   
                    try:             
                        sp[k][j] = UniSpline(range(numCols) , data[int(k) + n - 1], s = 0 )                
                        self.spline[k][j] = sp[k][j](p)                                
                    except: self.spline[k][j] = data[int(k) + n -1]
                    n += numElectrodes                           

        y = data[numElectrodes * len(hc.multipoles)]        
        fit = interpolate.interp1d(range(numCols) , y, 'linear')
        self.position = fit(p)
    
        yield self.registry.cd(self.registryPath)
        yield self.registry.set('MostRecent', file)  

    @setting( 7, "Set Multipole Values", ms = '*(sv): dictionary of multipole values')
    def setMultipoleValues(self, c, ms):
        """
        set should be a dictionary with keys 'Ex', 'Ey', 'U1', etc.
        """
        self.multipoleSet = {}
        for (k,v) in ms:
            self.multipoleSet[k] = v
        yield self.setVoltages(c, self.positionIndex)
        yield self.registry.cd(self.registryPath)
        yield self.registry.set('MultipoleSet', ms)

    @setting( 20, "Get Multipole Values",returns='*(s,v)')
    def getMultipoleValues(self, c):
        """
        Return a list of multipole voltages
        """
        return self.multipoleSet.items()
                        
    @setting( 10, "Set Voltages", newPosition = 'i')
    def setVoltages(self, c, newPosition = positionIndex):
        n = newPosition
        newVoltageSet = []
        for k in self.DACs.keys():
            if self.DACs[k].smaOutNumber:
                val = self.current[k]
                newVoltageSet.append( (k, val) )
            else:
                val = 0
                for j in hc.multipoles:
                    val += self.spline[k][j][n] * self.multipoleSet[j]
                newVoltageSet.append( (k, val) )
        yield self.setIndividualAnalogVoltages(c, newVoltageSet)
        self.positionIndex = n
                
    @setting(12, "do nothing")
    def doNone(self, c):
        pass
                
if __name__ == "__main__":
    from labrad import util
    util.runServer( CCTDACServer() )
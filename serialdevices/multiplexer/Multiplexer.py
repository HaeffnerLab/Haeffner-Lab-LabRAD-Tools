'''
### BEGIN NODE INFO
[info]
name = Multiplexer Server
version = 1.03
description =
instancename = Multiplexer Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
'''
#@author: Michael Ramm, Christopher Reilly
from serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from twisted.internet.defer import returnValue
from twisted.internet.threads import deferToThread
from labrad.types import Error
import time
import subprocess as sp
from twisted.internet import reactor
from labrad.server import Signal
from labrad.units import WithUnit
from Multiplexer_config import multiplexer_config as config

NUMCHANNELS = 16
BAUDRATE = 115200
DelayWhenSwtch = 100.0
CycleDelay = 100.0
SetExposureFile = 'setExposure.exe'
GetFreqFile = 'getFreq.exe'
NotMeasuredCode = -6.0

SIGNALID1 = 270580
SIGNALID2 = 270581
SIGNALID3 = 270582
SIGNALID4 = 270583

class channelInfo(object):
    def __init__(self):
        self.channelDict = {}
        self.lastMeasured = None
        self.lastExposure = 1
        
    class channel():
        def __init__(self, chanName, chanNumber, wavelength):
            self.chanName = chanName
            self.chanNumber = chanNumber
            self.wavelength = wavelength
            self.state = None
            self.exp = None
            self.freq = NotMeasuredCode
         
    def addChannel(self, chanName, chanNumber, wavelength):
        self.channelDict[chanName] = self.channel(chanName, chanNumber, wavelength)
    #returns names of all selected channels, that is all channels whose state == 1
    def getSelectedChannels(self):
        return [ch.chanName for ch in self.channelDict.values() if ch.state == 1]
    
    #determines what is the next selected channel to be measured, and whether a switch of channels is required
    def getNextChannel(self):
        selected = sorted(self.getSelectedChannels())
        if not selected: return [None, None] #if no channels are selected, ruturn None
        if self.lastMeasured not in selected: #if the previously measured channel is no longer selected, measure the first of currently selected ones
            next = selected[0]
            switch = True
        else:
            newindex = ((selected.index(self.lastMeasured) + 1) % len(selected)) #new index in the next item in the selected list with cyclical boundary conditions
            next = selected[newindex]
            switch =  (next != self.lastMeasured)
        self.lastMeasured = next
        return [next, switch]
            
    def getChanNames(self):
        return self.channelDict.keys()
    
    def getChanNumber(self, chanName):
        return self.channelDict[chanName].chanNumber
    
    def setState(self, chanName, state):
        self.channelDict[chanName].state = state
        
    def getState(self, chanName):
        return self.channelDict[chanName].state
    
    def setExposure(self, chanName, exp):
        self.channelDict[chanName].exp = exp
    
    def getExposure(self, chanName):
        return self.channelDict[chanName].exp
    
    def setFreq(self, chanName, freq):
        self.channelDict[chanName].freq = freq
    
    def getFreq(self, chanName):
        return self.channelDict[chanName].freq
    
    def getWavelength(self, chanName):
        return self.channelDict[chanName].wavelength

class Multiplexer( SerialDeviceServer ):
    '''
    LabRAD Sever for interfacing with the Wavemeter and the Multiplexer
    '''  
    name = 'Multiplexer Server' 
    regKey = 'Multiplexer'
    port = None
    serNode = 'lab-49'
    timeout = WithUnit(1.0, 's')
    
    onNewState = Signal(SIGNALID1, 'signal: channel toggled', '(sb)')
    onNewExposure = Signal(SIGNALID2, 'signal: new exposure set', '(sv)')
    onNewFreq = Signal(SIGNALID3, 'signal: new frequency measured', '(sv)')
    onCycling = Signal(SIGNALID4, 'signal: updated whether cycling', 'b')

    @inlineCallbacks
    def initServer( self ):
        self.createChannelInfo()
        if not self.regKey or not self.serNode: raise SerialDeviceError( 'Must define regKey and serNode attributes' )
        port = yield self.getPortFromReg( self.regKey )
        self.port = port
        try:
            serStr = yield self.findSerial( self.serNode )
            self.initSerial( serStr, port, baudrate = BAUDRATE )
        except SerialConnectionError, e:
            self.ser = None
            if e.code == 0:
                print 'Could not find serial server for node: %s' % self.serNode
                print 'Please start correct serial server'
            elif e.code == 1:
                print 'Error opening serial connection'
                print 'Check set up and restart serial server'
            else: raise
        self.reg = self.client.registry
        self.loadChannelInfo()
        self.listeners = set()
        self.isCycling = False
    
    def createChannelInfo(self):
        self.info = channelInfo()
        for channel_name, channel_info in config.info.iteritems():
            channel_number, channel_wavelength = channel_info
            self.info.addChannel(channel_name, channel_number, channel_wavelength)
        
    @inlineCallbacks
    def loadChannelInfo(self):
        yield self.reg.cd(['','Servers','Multiplexer'],True)
        for chanName in self.info.getChanNames():
            try:
                [state, exp] = yield self.reg.get(chanName)    
            except Error, e:
                if e.code is 21:
                    [state, exp] = [True , 1]
            self.info.setState(chanName, state)
            self.info.setExposure(chanName, exp)
    
    @inlineCallbacks
    def saveChannelInfo(self):
        for chanName in self.info.getChanNames():
            state = self.info.getState(chanName)
            exp = self.info.getExposure(chanName)
            yield self.client.registry.set(chanName,(state,exp))
    
    def validateInput(self, input, type):
        if type is 'channelName':
            if input not in self.info.getChanNames():
                raise Error('No such channel')
        if type is 'exposure':
            if not 0 <= input <= 2000:
                raise Error('exposure invalid')     
    
    @inlineCallbacks
    def _setExposure(self, exp):
        yield deferToThread(sp.Popen(SetExposureFile, shell=False, stdin = sp.PIPE).communicate, str(exp))
    
    @inlineCallbacks
    def _getFreq(self):
        result = yield deferToThread(sp.Popen(GetFreqFile, shell=False, stdout = sp.PIPE).communicate)
        returnValue(result[0])
    
    @inlineCallbacks
    def _switchChannel(self, chan):
        line = 'I1 ' + str(chan) +'\r' #format specified by DiCon Manual p7
        yield self.ser.write(line)
            
    @inlineCallbacks
    def measureChan(self):
        if not self.isCycling: return
        [next, switch] = self.info.getNextChannel()
        if next is None:
            reactor.callLater(.5, self.measureChan)
            return
        if switch:
            ch = self.info.getChanNumber(next)
            yield self._switchChannel(ch)
        curExp = self.info.getExposure(next)
        yield self._setExposure(curExp)
        if switch:
            prevExp = self.info.lastExposure
            waittime = 2*prevExp + 2*curExp + DelayWhenSwtch
            yield deferToThread(time.sleep, waittime / 1000.0)
            self.info.lastExposure = curExp
        else:
            yield deferToThread(time.sleep, .1)
        freq = yield self._getFreq()
        if freq is not self.info.getFreq(next) and self.info.getState(next) and self.isCycling: #if a new frequency is found and still need to measure
            self.info.setFreq(next, freq)
            self.onNewFreq((next, freq))
        reactor.callLater(CycleDelay / 1000.0,self.measureChan)
    
    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)
    
    def expireContext(self, c):
        self.listeners.remove(c.ID)
    
    def getOtherListeners(self,c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified
    
    @setting(0,'Start Cycling', returns = '')
    def startCycling(self,c):
        self.isCycling = True
        notified = self.getOtherListeners(c)
        self.onCycling(True, notified)
        self.measureChan()
                
    @setting(1,'Stop Cycling', returns = '')
    def stopCycling(self,c):
        self.isCycling = False
        notified = self.getOtherListeners(c)
        self.onCycling(False,notified)
        for name in self.info.getChanNames():
            self.info.setFreq(name, NotMeasuredCode)
            self.onNewFreq((name, NotMeasuredCode))
    
    @setting(2, 'Is Cycling',returns = 'b')
    def isCycling(self,c):
        return self.isCycling
    
    @setting(3,'Get Available Channels', returns = '*s: list of connected channels')
    def getAvailableChannels(self,c):
        return self.info.getChanNames()
    
    @setting(4,'Get State', chanName = 's: name of the channel, i.e 422', returns = 'b: is channel selected')
    def getState(self, c , chanName):
        self.validateInput(chanName, 'channelName')
        return self.info.getState(chanName)
    
    @setting(5,'Set State', chanName = 's: name of the channel, i.e 422', state='b', returns='')
    def setState(self,c, chanName, state):
        self.validateInput(chanName, 'channelName')
        self.info.setState(chanName, state)
        notified = self.getOtherListeners(c)
        self.onNewState((chanName, state),notified)
        self.saveChannelInfo()
        if not state:
            self.info.setFreq(chanName, NotMeasuredCode)
            self.onNewFreq((chanName,NotMeasuredCode))
            
    @setting(6,'Select One Channel', chanName = 's: name of the channel, i.e 422', returns = '')
    def selectOneChan(self,c,chanName):
        self.validateInput(chanName, 'channelName')
        notified = self.getOtherListeners(c)
        for ch in self.info.getChanNames():
            if ch == chanName:
                self.info.setState(ch, True)
                self.onNewState((ch, True),notified)
            else:
                self.info.setState(ch, False)
                self.onNewState((ch, False),notified)
    
    @setting(7,'Get Exposure', chanName = 's: name of the channel, i.e 422', returns = 'w: exposure')
    def getExposure(self, c , chanName):
        self.validateInput(chanName, 'channelName')
        return self.info.getExposure(chanName)
    
    @setting(8,'Set Exposure', chanName = 's: name of the channel, i.e 422', exposure = 'w : exposure in ms', returns = '')
    def setExposure(self,c,chanName,exposure):
        self.validateInput(chanName, 'channelName')
        self.validateInput(exposure,'exposure')
        self.info.setExposure(chanName, exposure)
        notified = self.getOtherListeners(c)
        self.onNewExposure((chanName, exposure),notified)
        self.saveChannelInfo()
    
    @setting(9, 'Get Wavelength From Channel', chanName = 's: name of the channel, i.e 422', returns = 's')
    def wlfromch(self, c, chanName):
        self.validateInput(chanName, 'channelName')
        return self.info.getWavelength(chanName)

    @setting(10,'Get Frequency',chanName = 's: name of the channel, i.e 422',returns ='v: laser frequency')
    def getFreq(self,c, chanName):
        self.validateInput(chanName, 'channelName')
        return self.info.getFreq(chanName)
    
if __name__ == "__main__":
    from labrad import util
    util.runServer(Multiplexer())
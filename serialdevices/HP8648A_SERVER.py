"""
### BEGIN NODE INFO
[info]
name = HP Server
version = 1.0
description = 
instancename = %LABRADNODE% HP Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad.types import Error
from twisted.internet import reactor
from twisted.internet.defer import returnValue
from labrad.server import Signal

SIGNALID = 209057
SIGNALID1 = 209058

class HPServer( SerialDeviceServer ):
    """Controls HP8648A Signal Generator"""

    name = '%LABRADNODE% HP Server'
    regKey = 'HPsiggen'
    port = None
    serNode = 'lattice-pc'
    timeout = 1.0
    gpibaddr = 0
    onNewUpdate = Signal(SIGNALID, 'signal: settings updated', '(sv)')
    onStateUpdate = Signal(SIGNALID1, 'signal: state updated', 'b')
    
    @inlineCallbacks
    def initServer( self ):
        self.createDict()
        if not self.regKey or not self.serNode: raise SerialDeviceError( 'Must define regKey and serNode attributes' )
        port = yield self.getPortFromReg( self.regKey )
        self.port = port
        try:
            serStr = yield self.findSerial( self.serNode )
            self.initSerial( serStr, port )
        except SerialConnectionError, e:
            self.ser = None
            if e.code == 0:
                print 'Could not find serial server for node: %s' % self.serNode
                print 'Please start correct serial server'
            elif e.code == 1:
                print 'Error opening serial connection'
                print 'Check set up and restart serial server'
            else: raise
            
        self.ser.write(self.SetAddrStr(self.gpibaddr)) #set gpib address
        self.SetControllerWait(0) #turns off automatic listen after talk, necessary to stop line unterminated errors
        yield self.populateDict()
        self.listeners = set()
        
    def createDict(self):
        d = {}
        d['state'] = None #state is a boolean
        d['power'] = None #power is in dBm
        d['freq'] = None #frequency is in MHz
        d['powerrange'] = (-5.9,5.0)
        d['freqrange'] = (14.5,15.5) #MHz
        self.hpDict = d

    
    @inlineCallbacks
    def populateDict(self):
        state = yield self._GetState() 
        freq = yield self._GetFreq()
        power = yield self._GetPower()
        self.hpDict['state'] = bool(state) 
        self.hpDict['power'] = float(power)
        self.hpDict['freq'] = float(freq)
    
    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)
    
    def expireContext(self, c):
        self.listeners.remove(c.ID)
        
    def getOtherListeners(self,c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified
    
    @setting(1, "Identify", returns='s')
    def Identify(self, c):
        '''Ask instrument to identify itself'''
        command = self.IdenStr()
        self.ser.write(command)
        self.ForceRead() #expect a reply from instrument
        answer = yield self.ser.readline()
        returnValue(answer[:-1])

    @setting(2, "GetFreq", returns='v')
    def GetFreq(self,c):
        '''Returns current frequency'''
        return self.hpDict['freq']

    @setting(3, "SetFreq", freq = 'v', returns = "")
    def SetFreq(self,c,freq):
        '''Sets frequency, enter value in MHZ'''
        command = self.FreqSetStr(freq)
        self.ser.write(command)
        self.hpDict['freq'] = freq
        notified = self.getOtherListeners(c)
        self.onNewUpdate(('freq',freq),notified )
      
    @setting(4, "GetState", returns='b')
    def GetState(self,c):
        '''Request current on/off state of instrument'''
        return self.hpDict['state']
    
    @setting(5, "SetState", state= 'b', returns = "")
    def SetState(self,c, state):
        '''Sets on/off '''
        command = self.StateSetStr(state)
        self.ser.write(command)
        self.hpDict['state'] = state
        notified = self.getOtherListeners(c)
        self.onStateUpdate(state,notified)
    
    @setting(6, "GetPower", returns = 'v')
    def GetPower(self,c):
        ''' Returns current power level in dBm'''
        return self.hpDict['power']
    
    @setting(7, "SetPower", level = 'v',returns = "")
    def SetPower(self,c, level):
        '''Sets power level, enter power in dBm'''
        self.checkPower(level)
        command = self.PowerSetStr(level)
        self.ser.write(command)
        self.hpDict['power'] = level
        notified = self.getOtherListeners(c)
        self.onNewUpdate(('power',level),notified)
    
    @setting(8, "Get Power Range", returns = "*v:")
    def GetPowerRange(self,c):
        return self.hpDict['powerrange']
    
    @setting(9, "Get Frequency Range", returns = "*v:")
    def getFreqRange(self,c):
        return self.hpDict['freqrange']
    
    def checkPower(self, level):
        MIN,MAX = self.hpDict['powerrange']
        if not MIN <= level <= MAX:
            raise('Power Out of Allowed Range')
    
    def checkFreq(self, freq):
        MIN,MAX = self.hpDict['freqrange']
        if not MIN <= freq <= MAX:
            raise('Frequency Out of Allowed Range')
    
    @inlineCallbacks
    def _GetState(self):
        command = self.StateReqStr()
        yield self.ser.write(command)
        yield self.ForceRead() #expect a reply from instrument
        answer = yield self.ser.readline()
        answer = bool(answer)
        returnValue(answer)
    
    @inlineCallbacks
    def _GetFreq(self):
        command = self.FreqReqStr()
        yield self.ser.write(command)
        yield self.ForceRead() #expect a reply from instrument
        freq = yield self.ser.readline()
        freq = float(freq) / 10**6 #state is in MHz 
        returnValue(freq)
        
    @inlineCallbacks
    def _GetPower(self):
        command = self.PowerReqStr()
        yield  self.ser.write(command)
        yield self.ForceRead() #expect a reply from instrument
        answer = yield self.ser.readline()
        returnValue(answer)
        
    #send message to controller to indicate whether or not (status = 1 or 0)
    #a response is expected from the instrument
    @inlineCallbacks
    def SetControllerWait(self,status):
        command = self.WaitRespStr(status) #expect response from instrument
        yield self.ser.write(command)

    @inlineCallbacks
    def ForceRead(self):
        command = self.ForceReadStr()
        yield self.ser.write(command)
  
    def IdenStr(self):
        return '*IDN?'+'\n'
    # string to request current frequency
    def FreqReqStr(self):
        return 'FREQ:CW?' + '\n'
    # string to set freq (in MHZ)
    def FreqSetStr(self,freq):
        return 'FREQ:CW '+ str(freq) +'MHZ'+'\n'
    # string to request on/off?
    def StateReqStr(self):
        return 'OUTP:STAT?' + '\n'

    # string to set on/off (state is given by 0 or 1)
    def StateSetStr(self, state):
        if state:
            comstr = 'OUTP:STAT ON' + '\n'
        else:
            comstr = 'OUTP:STAT OFF' + '\n'
        return comstr

    # string to request current power
    def PowerReqStr(self):
        return 'POW:AMPL?' + '\n'

    # string to set power (in dBm)
    def PowerSetStr(self,pwr):
        return 'POW:AMPL ' +str(pwr) + 'DBM' + '\n'

    # string to force read
    def ForceReadStr(self):
        return '++read eoi' + '\n'
    # string for prologix to request a response from instrument, wait can be 0 for listen / for talk
    def WaitRespStr(self, wait):
        return '++auto '+ str(wait) + '\n'
    
    # string to set the addressing of the prologix
    def SetAddrStr(self, addr):
        return '++addr ' + str(addr) + '\n'

if __name__ == "__main__":
    from labrad import util
    util.runServer(HPServer())

"""
### BEGIN NODE INFO
[info]
name = HP Server
version = 1.1
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
from twisted.internet.defer import returnValue

class HPServer( SerialDeviceServer ):
    """Controls HP8648A Signal Generator"""

    name = '%LABRADNODE% HP Server'
    regKey = 'HPsiggen'
    port = None
    serNode = 'lattice-imaging'
    timeout = 1.0
    gpibaddr = 0
    
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
            
        yield self.ser.write(self.SetAddrStr(self.gpibaddr)) #set gpib address
        self.SetControllerWait(0) #turns off automatic listen after talk, necessary to stop line unterminated errors
        yield self.populateDict()
        self.listeners = set()
        
    def createDict(self):
        d = {}
        d['state'] = None #state is a boolean
        d['power'] = None #power is in dBm
        d['freq'] = None #frequency is in MHz
        d['powerrange'] = (-136.0,13.0) #dBm
        d['freqrange'] = (0.1,1000.0) #MHz
        self.hpDict = d
    
    @inlineCallbacks
    def populateDict(self):
        state = yield self._GetState() 
        freq = yield self._GetFreq()
        power = yield self._GetPower()
        self.hpDict['state'] = bool(state) 
        self.hpDict['power'] = float(power)
        self.hpDict['freq'] = float(freq)

    
    @setting(1, "Identify", returns='s')
    def identify(self, c):
        '''Ask instrument to identify itself'''
        command = self.IdenStr()
        yield self.ser.write(command)
        self.ForceRead() #expect a reply from instrument
        answer = yield self.ser.readline()
        returnValue(answer[:-1])
        
    @setting(2, 'Frequency', f=['v[MHz]'], returns=['v[MHz]'])
    def frequency(self, c, f = None):
        """Get or set the CW frequency."""
        if f is not None:
            f = float(f)
            self.checkFreq(f)
            command = self.FreqSetStr(f)
            yield self.ser.write(command)
            self.hpDict['freq'] = f
        returnValue( self.hpDict['freq'] )    
        
    @setting(3, 'Amplitude', a=['v[dBm]'], returns=['v[dBm]'])
    def amplitude(self, c, a = None):
        """Get or set the CW amplitude."""
        if a is not None:
            a = float(a)
            self.checkPower(a)
            command = self.PowerSetStr(a)
            yield self.ser.write(command)
            self.hpDict['power'] = a    
        returnValue( self.hpDict['power'] )
    
    @setting(4, 'Output', os=['b'], returns=['b'])
    def output(self, c, os=None):
        """Get or set the output status."""
        if os is not None:
            command = self.StateSetStr(os)
            yield self.ser.write(command)
            self.hpDict['state'] = os
        returnValue( self.hpDict['state'] )     
    
    @inlineCallbacks
    def _GetState(self):
        command = self.StateReqStr()
        yield self.ser.write(command)
        yield self.ForceRead() #expect a reply from instrument
        answer = yield self.ser.readline()
        answer = bool(int(answer)) #returns a string
        returnValue(answer)
    
    @inlineCallbacks
    def _GetFreq(self):
        command = self.FreqReqStr()
        yield self.ser.write(command)
        yield self.ForceRead() #expect a reply from instrument
        freq = yield self.ser.readline()
        freq = float(freq) / 10.0**6 #state is in MHz 
        returnValue(freq)
        
    @inlineCallbacks
    def _GetPower(self):
        command = self.PowerReqStr()
        yield self.ser.write(command)
        yield self.ForceRead() #expect a reply from instrument
        answer = yield self.ser.readline()
        returnValue(answer)
    
    def checkPower(self, level):
        MIN,MAX = self.hpDict['powerrange']
        if not MIN <= level <= MAX:
            raise Exception('Power Out of Allowed Range')
    
    def checkFreq(self, freq):
        MIN,MAX = self.hpDict['freqrange']
        if not MIN <= freq <= MAX:
            raise Exception('Frequency Out of Allowed Range')
        
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

"""
### BEGIN NODE INFO
[info]
name = Keithley 6487 Server
version = 1.1
description = 
instancename = %LABRADNODE% Keithley 6487 Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from twisted.internet.threads import deferToThread
import time
from twisted.internet.defer import returnValue

class KEITHLY6487( SerialDeviceServer ):
    """Controls KEITHLY6487 Signal Generator"""

    name = '%LABRADNODE% KEITHLY 6487'
    regKey = 'KEITHLY6487'
    port = None
    serNode = 'lattice-imaging'
    timeout = 1.0
    gpibaddr = 22
    
    @inlineCallbacks
    def initServer( self ):
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
        yield self.SetControllerWait(0) #turns off automatic listen after talk, necessary to stop line unterminated errors
        self.initialize()
        self.listeners = set()
    
    @setting(1, "Identify", returns='s')
    def identify(self, c):
        '''Ask instrument to identify itself'''
        command = self.IdenStr()
        yield self.ser.write(command)
        yield deferToThread(time.sleep, .5)
        yield self.ForceRead() #expect a reply from instrument
        answer = yield self.ser.readline()
        returnValue(answer[:-1])
        
    @setting(2, 'Measure Current', number = 'i', returns='*v')
    def measureCurrent(self, c, number):
        """Measure the Current"""
        command = self.SetTrigCount(number)
        yield self.ser.write(command)
        yield deferToThread(time.sleep, .5)
        command = self.startMeasurement()
        yield self.ser.write(command)
        yield deferToThread(time.sleep, number)
        yield self.ForceRead()
        answer = yield self.ser.readline()
        answer = answer.split(',')
        current = 0.0
        measurementTime = 0.0        
        for i in range(number):
            current += float(answer[i*3][1:-1])
            measurementTime += float(answer[i*3+1][1:len(answer[i*3+1])])
        current /= number
        print 'Current: ', current
        measurementTime /= number
        print 'Time: ', measurementTime
        returnValue([measurementTime, current])    
        
    @setting(3, 'Close', returns = '')
    def close(self, c):
        self.ser.close()
    

        
    #send message to controller to indicate whether or not (status = 1 or 0)
    #a response is expected from the instrument
    @inlineCallbacks
    def SetControllerWait(self,status):
        command = self.WaitRespStr(status) #expect response from instrument
        yield self.ser.write(command)
        
    @inlineCallbacks
    def initialize(self):
#        yield self.ser.write('*RST'+'\n')
#        yield deferToThread(time.sleep, 1)
        yield self.ser.write('ARM:SOUR IMM'+'\n')
        yield deferToThread(time.sleep, .5)
        yield self.ser.write('ARM:COUN 1'+'\n')
        yield deferToThread(time.sleep, .5)
        yield self.ser.write('TRIG:SOUR IMM'+'\n')
        yield deferToThread(time.sleep, .5)  
#        yield self.ser.write('SYST:ZCH OFF'+'\n')
#        yield deferToThread(time.sleep, 1)
              

    @inlineCallbacks
    def ForceRead(self):
        command = self.ForceReadStr()
        yield self.ser.write(command)
  
    def IdenStr(self):
        return '*IDN?'+'\n'

    # string to force read
    def ForceReadStr(self):
        return '++read eoi' + '\n'
    # string for prologix to request a response from instrument, wait can be 0 for listen / for talk
    def WaitRespStr(self, wait):
        return '++auto '+ str(wait) + '\n'
    
    # string to set the addressing of the prologix
    def SetAddrStr(self, addr):
        return '++addr ' + str(addr) + '\n'
    
    # Set the number of triggers
    def SetTrigCount(self, count):
        return 'TRIG:COUNT ' + str(count) + '\n'
    
    # start measurement
    def startMeasurement(self):
        return 'READ?' + '\n'
    
if __name__ == "__main__":
    from labrad import util
    util.runServer(KEITHLY6487())

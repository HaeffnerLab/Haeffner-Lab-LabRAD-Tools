from serialdeviceserver import  setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad.types import Error
from twisted.internet import reactor
from twisted.internet.defer import returnValue
from labrad.server import LabradServer, setting

port = 'COM3'

class U3751Server( LabradServer ):
    """Controls U3751 Spectrum Analyzer"""
    name = 'U3751 Server'
    regKey = ''
    gpibaddr = 1

    @inlineCallbacks
    def initServer( self ):
        print 1
        ser = self.client.lab_197_serial_server
        print 2
        self.ser = ser
        print 3
        self.ser.open(port)
        print 4
        self.ser.write(self.SetAddrStr(self.gpibaddr)) #set gpib address
        #self.SetControllerWait(0) #turns off automatic listen after talk, necessary to stop line unterminated errors
        print 5
        yield None

    # def initContext(self, c):
        """Initialize a new context object."""
    #     self.listeners.add(c.ID)
    
    # def expireContext(self, c):
    #     self.listeners.remove(c.ID)
        
    # def getOtherListeners(self,c):
    #     notified = self.listeners.copy()
    #     notified.remove(c.ID)
    #     return notified
    
    def SetAddrStr(self, addr):
        return '++addr ' + str(addr) + '\n'
        
    @setting(1, "TraceReq", returns = '*v')
    def TraceReq(self, c):
        command = self.TraceReqStr()
        self.ser.write(command)
        return self.ser.read()


    #1 is 16  bit integer, 3 is 32 bit ieee float
    @setting(2, "SetTraceFormat", format = 'i', returns = "")
    def SetTraceFormat(self, c,  format):      
        if format!=1 and format!=3:
                print "Format must be 1 or 3"
                return
        command = self.SetTraceFormatStr(format)
        self.ser.write(command)
    
    @setting(3, "SelectedTraceQuery", returns = 'i')
    def SelectedTraceQuery(self,c):
        self.ser.write("TRACESEL?\r")
        self.ForceRead()
        answer = self.ser.read_line()
        return answer
        
    @inlineCallbacks
    def ForceRead(self):
        command = self.ForceReadStr()
        yield self.ser.write(command)

    def TraceReqStr(self):
        return 'TAA?' + '\n'
    
    def SetTraceFormatStr(self, format):
        return 'FORM' + str(format) + '\n'


    # string to force read
    def ForceReadStr(self):
        return '++read eoi' + '\n'
    
    # string for prologix to request a response from instrument, wait can be 0 for listen / for talk
    def WaitRespStr(self, wait):
        return '++auto '+ str(wait) + '\n'
    
    # string to set the addressing of the prologix


if __name__ == "__main__":
    from labrad import util
    util.runServer(U3751Server())

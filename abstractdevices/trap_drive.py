"""
### BEGIN NODE INFO
[info]
name = Trap Drive
version = 1.0
description = 
instancename = Trap Drive

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, Signal, setting
from twisted.internet.defer import inlineCallbacks, returnValue

class TrapDrive( LabradServer ):
    """Controls Trap Drive"""

    name = 'Trap Drive'
    onNewUpdate = Signal(209057, 'signal: settings updated', '(sv)')
    onStateUpdate = Signal(209058, 'signal: state updated', 'b')
    
    @inlineCallbacks
    def initServer( self ):
        self.powerRange = (-20.0,0.0) #dBM
        self.freqRange = (30.0,40.0) #MHz
        self.listeners = set()
        self.serverName = 'RohdeSchwarz Server'
        self.device = 'lattice-imaging GPIB Bus - USB0::0x0AAD::0x0054::104541'
        try:
            self.server = yield self.connectToServer()
        except KeyError:
            print '{} not connected'.format(self.serverName)
            self.server = None
    
    @inlineCallbacks
    def connectToServer(self):
        server = self.client[self.serverName]
        yield server.select_device(self.device)
        returnValue(server)
        
    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)
  
    def getOtherListeners(self,c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified
    
    @setting(1, 'Frequency', f=['v[MHz]'], returns=['v[MHz]'])
    def frequency(self, c, f = None):
        """Get or set the CW frequency."""
        if self.server is None: raise Exception ('{} not connected'.format(self.serverName))
        if f is not None: self.checkFreq(f)
        freq = yield self.server.frequency(f)
        if f is not None:
            otherListeners = self.getOtherListeners(c)
            self.onNewUpdate(('frequency', freq), otherListeners)
        returnValue(freq)
    
    @setting(2, 'Amplitude', a=['v[dBm]'], returns=['v[dBm]'])
    def amplitude(self, c, a = None):
        """Get or set the CW amplitude."""
        if self.server is None: raise Exception ('{} not connected'.format(self.serverName))
        if a is not None: self.checkPower(a)
        ampl = yield self.server.amplitude(a)
        if a is not None: 
            otherListeners = self.getOtherListeners(c)
            self.onNewUpdate(('amplitude', ampl), otherListeners)
        returnValue(ampl)
    
    @setting(3, 'Output',  os=['b'], returns=['b'])
    def output(self, c, os = None):
        """Get or set the output status."""
        if self.server is None: raise Exception ('{} not connected'.format(self.serverName))
        outp = yield self.server.output(os)
        if os is not None:
            otherListeners = self.getOtherListeners(c)
            self.onStateUpdate(os)
        returnValue(outp)
    
    @setting(4, 'Get Amplitude Range', returns = '(vv)')
    def getPowerRange(self, c):
        return self.powerRange
    
    @setting(5, 'Get Frequency Range', returns = '(vv)')
    def getAmplitudeRange(self, c):
        return self.freqRange
        
    def checkPower(self, level):
        MIN,MAX = self.powerRange
        if not MIN <= level <= MAX:
            raise('Power Out of Allowed Range')
    
    def checkFreq(self, freq):
        MIN,MAX = self.freqRange
        if not MIN <= freq <= MAX:
            raise('Frequency Out of Allowed Range')
    
    @inlineCallbacks
    def serverConnected( self, ID, name ):
        """Connect to the server"""
        if name == self.serverName:
            self.server = yield self.connectToServer()
            print '{} connected'.format(self.serverName)

    def serverDisconnected( self, ID, name ):
        """Close connection"""
        if name == self.serverName:
            print '{} disconnected'.format(self.serverName)
            self.server = None

if __name__ == "__main__":
    from labrad import util
    util.runServer(TrapDrive())

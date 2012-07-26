'''
### BEGIN NODE INFO
[info]
name = Pulser_729
version = 0.1
description =
instancename = Pulser_729

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
'''
#TODO1 : remove unused imports
#TODO2 : DDS Signal
#reset
#switch off

from labrad.server import LabradServer, setting, Signal
from twisted.internet import reactor
from twisted.internet.defer import returnValue, DeferredLock, Deferred, inlineCallbacks
from twisted.internet.threads import deferToThread
import numpy
from api import api
from sequence import Sequence
from dds import DDS
from hardwareConfiguration import hardwareConfiguration

class Pulser_729(LabradServer, DDS):
    name = 'Pulser_729'
    onSwitch = Signal(611052, 'signal: switch toggled', '(ss)')
    
    @inlineCallbacks    
    def initServer(self):
        self.api  = api()
        self.timeResolution = hardwareConfiguration.timeResolution
        self.ddsDict = hardwareConfiguration.ddsDict
        self.inCommunication = DeferredLock()
        yield self.initializeBoard()
        yield self.initializeDDS()
        self.listeners = set()
    
    @inlineCallbacks
    def initializeBoard(self):
        connected = self.api.connectOKBoard()
        while not connected:
            print 'not connected, waiting for 10 seconds to try again'
            yield self.wait(10.0)
            connected = self.api.connectOKBoard()
    
    def wait(self, seconds, result=None):
        """Returns a deferred that will be fired later"""
        d = Deferred()
        reactor.callLater(seconds, d.callback, result)
        return d
    
    @setting(0, "New Sequence", returns = '')
    def newSequence(self, c):
        """
        Create New Pulse Sequence
        """
        c['sequence'] = Sequence()
    
    @setting(1, "Program Sequence", returns = '')
    def programSequence(self, c, sequence):
        """
        Programs Pulser with the current sequence.
        """
        sequence = c.get('sequence')
        if not sequence: raise Exception ("Please create new sequence first")
        if sequence.userAddedDDS():
            self._addDDSInitial(sequence)
        dds = sequence.progRepresentation()
        yield self.inCommunication.acquire()
        if dds is not None: yield deferToThread(self._programDDSSequence, dds)
        self.inCommunication.release()
    
    def notifyOtherListeners(self, context, message, f):
        """
        Notifies all listeners except the one in the given context, executing function f
        """
        notified = self.listeners.copy()
        notified.remove(context.ID)
        f(message,notified)
    
    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)
    
    def expireContext(self, c):
        self.listeners.remove(c.ID)

if __name__ == "__main__":
    from labrad import util
    util.runServer( Pulser_729() )
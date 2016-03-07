# @author: Dylan Gorman, Haeffner lab

'''
### BEGIN NODE INFO
[info]
name = Picomotor
version = 1.2
description =
instancename = Picomotor
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
'''

from labrad.server import LabradServer, setting, Signal
from twisted.internet import reactor
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred
from twisted.internet.threads import deferToThread
from controller import Controller

class PicomotorServer(LabradServer):

    name = 'PicomotorServer'
    
    # signal arguments are (axis, new absolute position)
    on_position_change = Signal(144821, 'signal: position change', '(ii)' )

    def construct_command(self, axis, command, nn = None):
        if nn is None:
            return str(axis) + command
        else:
            return str(axis) + command + str(nn)

    @inlineCallbacks
    def initServer(self):
        self.controller = yield Controller( idProduct=0x4000, idVendor=0x104d )
        self.position_dict = dict.fromkeys( [1, 2, 3, 4], 0)
        self.setpoint = dict.fromkeys( [1, 2, 3, 4], 0)
        self.inCommunication = DeferredLock()
        self.listeners = set()


    @setting(0, 'Get Position', axis = 'i', returns = 'i')
    def get_position(self, c, axis):
        """
        Query the controller for the position of the given axis
        and also update position_dict
        """
        yield self.inCommunication.acquire()
        pos = yield self.controller.get_position(axis)
        self.inCommunication.release()

        self.position_dict[axis] = pos
        self.notifyOtherListeners(c, (axis, pos))
        returnValue(pos)

    @setting(1, 'Absolute Move', axis = 'i', pos = 'i')
    def absolute_move(self, c, axis, pos):
        """
        Move the given axis to a given absolute position
        """
        yield self.inCommunication.acquire()
        yield self.controller.absolute_move(axis, pos)
        self.inCommunication.release()

        self.position_dict[axis] = pos
        self.notifyOtherListeners(c, (axis, pos))    

    @setting(2, 'Relative Move', axis = 'i', steps = 'i', returns = 'i')
    def relative_move(self, c, axis, steps):
        """
        Move the given axis the given number of steps.
        Returns the new absolute position.
        """
        yield self.inCommunication.acquire()
        yield self.controller.relative_move(axis, steps)
        self.inCommunication.release()

        self.position_dict[axis] += steps
        self.notifyOtherListeners(c, (axis, self.position_dict[axis]) )
        
        returnValue(self.position_dict[axis])

    @setting(3, 'Mark current setpoint')
    def mark_setpoint(self, c):
        """
        Save the current position of all the axes
        to possibly return to later
        """
        
        axes = [1, 2, 3, 4]
        yield self.inCommunication.acquire()
        for axis in axes:
            pos = yield self.controller.get_position(axis)
            self.position_dict[axis] = pos
        self.inCommunication.release()
        
        self.setpoint = position_dict.copy()

    @setting(4, 'Return to setpoint')
    def return_to_setpoint(self, c):
        """
        Return all axes to the saved setpoint
        """
        axes = [1, 2, 3, 4]
        yield self.inCommunication.acquire()
        for axis in axes:
            yield self.controller.absolute_move( axis, self.setpoint[axis] )
            pos = self.setpoint[axis]
            self.position_dict[axis] = pos
            self.notifyOtherListeners(c, (axis, pos))
        self.inCommunication.release()

    def notifyOtherListeners(self, context, message):
        notified = self.listeners.copy()
        notified.remove(context.ID)
        self.on_position_change(message, notified)

    def initContext(self, c):
        self.listeners.add(c.ID)
    
    def expireContext(self, c):
        self.listeners.remove(c.ID)

if __name__ == "__main__":
    from labrad import util
    util.runServer( PicomotorServer() )

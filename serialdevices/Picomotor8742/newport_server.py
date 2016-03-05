# @author: Dylan Gorman, Haeffner lab

'''
### BEGIN NODE INFO
[info]
name = Newport
version = 1.2
description =
instancename = Newport
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

class NewportServer(LabradServer):

    name = 'NewportServer'

    def construct_command(self, axis, command, nn = None):
        if nn is None:
            return str(axis) + command
        else:
            return str(axis) + command + str(nn)

    @inlineCallbacks
    def initServer(self):
        self.controller = yield Controller( idProduct=0x4000, idVendor=0x104d )

    @setting(1, 'Get Position', axis = 'i', returns = 'i')
    def get_position(self, c, axis):
        cmd = self.construct_command(axis, 'TP?')
        pos = yield self.controller.command(cmd)
        print pos
        return pos

    @setting(2, 'Absolute Move', axis = 'i', pos = 'i')
    def absolute_move(self, c, axis, pos):
        cmd = self.construct_command(axis, 'PA', pos)
        yield self.controller.command(cmd)
    
    @setting(3, 'Relative Move', axis = 'i', steps = 'i')
    def relative_move(self, c, axis, steps):
        cmd = self.construct_command(axis, 'PR', steps)
        yield self.controller.command(cmd)
    
    
        

if __name__ == "__main__":
    from labrad import util
    util.runServer( NewportServer() )

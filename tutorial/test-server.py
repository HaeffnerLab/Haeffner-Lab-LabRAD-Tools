from labrad.server import LabradServer, setting
from twisted.internet.defer import inlineCallbacks, returnValue

class MyServer(LabradServer):
    name = "My Server"    # Will be labrad name of server

    @inlineCallbacks
    def initServer(self):  # Do initialization here
        pass

    @setting(10, data='?', returns='b')
    def is_true(self, c, data):
        return bool(data)

__server__ = MyServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)

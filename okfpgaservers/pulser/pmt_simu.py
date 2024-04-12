#from PyQt4 import QtGui

from twisted.internet import reactor
from labrad.server import setting, LabradServer
from labrad.types import Error
from twisted.internet.defer import returnValue, Deferred

import numpy as np

class pmt_simu(LabradServer):

    name = 'PMT Simulator'

    def initServer(self):
        print("Initializing pmt ...")
        self.state = 0
        pass

    @setting(1, buf='s', returns='s')
    def return_counts(self, c, buf):        
        
        #buf = "\x00" * ( 2 * 2 )

        buf = "\x00\x00"

        counts = int(self.get_excitation())
        buf += chr(counts)

        buf += "\x00"

        self.state = self.state + 1
        print(self.state)
        return buf

    def get_excitation(self):

        max_counts = 255
        t0 = 20
        w = 10

        t = self.state

        excitation = max_counts * np.exp( -(t - t0)**2/w**2 )

        if self.state == 2*t0:
            self.state = 0

        return excitation    

if __name__=="__main__":

    #a = QtGui.QApplication([])
    #import qt4reactor
    #qt4reactor.install()

    from labrad import util
    util.runServer( pmt_simu() )


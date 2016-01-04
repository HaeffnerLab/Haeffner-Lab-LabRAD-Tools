'''
The Real Simple Grapher
'''

from GraphWindow import GraphWindow
from Dataset import Dataset
from PyQt4 import QtGui
a = QtGui.QApplication( [])
import qt4reactor
qt4reactor.install()
#import server libraries
from twisted.internet.defer import returnValue, DeferredLock, Deferred, inlineCallbacks
from twisted.internet.threads import deferToThread
from twisted.internet import reactor
from labrad.server import LabradServer, setting


"""
### BEGIN NODE INFO
[info]
name =  Real Simple Grapher
version = 1.0
description = 
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

class RealSimpleGrapher(LabradServer):
    
    """ Methods for controlling graphing """

    name = "Grapher"

    @inlineCallbacks
    def initServer(self):
        self.listeners = set()
        self.gui = GraphWindow(reactor)
        self.dv = yield self.client.data_vault

    def make_dataset(self, path, name, dataset):
        cxt = self.client.context()
        ds = Dataset(self.dv, cxt, dataset, path, name, reactor)
        return ds

    def do_plot(self, path, graph, name, dataset, send_to_current):
        if (graph != 'Current') and (send_to_current == True):
            # add the plot to the Current tab as well as an additional
            # specified tab for later examination
            ds = self.make_dataset(path, name, dataset)
            self.gui.graphDict['Current'].add_dataset(ds)
        ds = self.make_dataset(path, name, dataset)
        self.gui.graphDict[graph].add_dataset(ds)
        
    @setting(1, 'Plot', path = '*s', graph = 's', name='s', dataset = ['i', 's'], send_to_current = 'b' ,returns = '')
    def plot(self, c, path, graph, name, dataset = 1, send_to_current = True):
        self.do_plot(path, graph, name, dataset, send_to_current)

    @setting(2, 'Plot with axis', path='*s', graph = 's', name='s', axis = '*v', dataset=['i', 's'], send_to_current = 'b', returns = '')
    def plot_with_axis(self, c, path, graph, name, axis, dataset = 1, send_to_current = True):
        
        if (graph != 'Current') and (send_to_current == True):
            self.gui.graphDict['Current'].set_xlimits([min(axis).value, max(axis).value])
        self.gui.graphDict[graph].set_xlimits([min(axis).value, max(axis).value])
        self.do_plot(path, graph, name, dataset, send_to_current)

if __name__ == '__main__':
    from labrad import util
    util.runServer(RealSimpleGrapher())

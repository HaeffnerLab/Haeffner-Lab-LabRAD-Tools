from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread

from listener import Listener
from PlotWindow import PlotWindow

GraphRefreshTime = 0.1

class Plotter(Listener):

    '''
    This is the main plotter client. It will, as all plotters will,
    inherit from Listener.
    
    Listener provides the interaction with the datavault.

    '''
    

    def __init__(self, filter, ignore, reactor, parent=None):
        Listener.__init__(self, filter, ignore, reactor)
        self.reactor = reactor
        self.dwDict = {} # Dictionary to keep track of which dataset goes to which window
        self.windowDict = {} # Maps window names to PlotWindow objects
        self.startTimer()
        
    def prepareDataset(self, datasetObject):
        '''
        This is mostly for deciding what window to put the dataset in.
        '''

        windowName = datasetObject.windowName
        print "preparing dataset " + datasetObject.datasetName
        print windowName
        if windowName in self.windowDict.keys():
            window = self.windowDict[windowName]
            self.dwDict[datasetObject] = window
            window.new_dataset(datasetObject)
        else:
            window = PlotWindow(self.reactor)
            window.setWindowTitle(windowName)
            window.new_dataset(datasetObject)
            self.dwDict[datasetObject] = window
            self.windowDict[windowName] = window
            window.show()
    
    def startTimer(self):
        lc = LoopingCall(self.timerEvent)
        lc.start(GraphRefreshTime)

    @inlineCallbacks
    def timerEvent(self):
        '''
        Loop through the windows and does updates
        '''

        for datasetObject in self.dwDict.keys():
            window = self.dwDict[datasetObject]
            if (datasetObject.data != None):
                yield window.new_data(datasetObject)

if __name__ == '__main__':

    a = QtGui.QApplication( [] )
    import common.clients.qt4reactor as qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor

    filter = [''] # listen to everything
    ignore = ['None'] # ignore nothing

    grapher = Plotter(filter, ignore, reactor)

    reactor.run()

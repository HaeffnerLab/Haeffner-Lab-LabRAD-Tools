'''

Parent class for datasets. Inherit from here to plot a new kind of dataset.

'''

from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from PyQt4 import QtCore
from twisted.internet.threads import deferToThread
import numpy as np

class Dataset(QtCore.QObject):

    def __init__(self,  cxn, context, dataset, directory, datasetName, reactor, parent=None):
        super(Dataset, self).__init__()
        self.data = None
        self.accessingData = DeferredLock()
        self.parent = parent
        self.reactor = reactor
        self.cxn = cxn
        self.context = context
        self.dataset = dataset
        self.directory = directory
        self.datasetName = datasetName
        self.updateCounter = 0
        self.connectDataVault()
        self.setupListeners()
        self.windowName = 'general'
        #self.openDataset()
        #self.getData()

    @inlineCallbacks
    def connectDataVault(self):
        yield self.cxn.data_vault.cd(self.directory, context = self.context)
        yield self.cxn.data_vault.open(self.dataset, context = self.context)

    @inlineCallbacks
    def setupListeners(self):
        yield self.cxn.data_vault.signal__data_available(11111, context = self.context)
        yield self.cxn.data_vault.addListener(listener = self.updateData, source = None, ID = 11111, context = self.context)
    
    @inlineCallbacks
    def openDataset(self):
        yield self.cxn.data_vault.cd(self.directory, context = self.context)
        yield self.cxn.data_vault.open(self.dataset, context = self.context)
        yield self.getParameters()

    @inlineCallbacks
    def getParameters(self):
        self.parameters = yield self.cxn.data_vault.parameters(context = self.context)
        self.parameterValues = []
        for parameter in self.parameters:
            parameterValue = yield self.cxn.data_vault.get_parameter(parameter, context = self.context)
            self.parameterValues.append(parameterValue)

    # signal for new data avalable
    def updateData(self, x, y):
        print("data updated")
        self.updateCounter += 1
        self.getData()

    @inlineCallbacks
    def getData(self):
        Data = yield self.cxn.data_vault.get(100, context = self.context)
        if (self.data == None):
            yield self.accessingData.acquire()
            self.data = Data.asarray
            self.xdata = self.data[:,0]
            self.ydata = self.data[:,1]
            self.accessingData.release()

        else:
            yield self.accessingData.acquire()
            self.data = np.append(self.data, Data.asarray, 0)
            self.xdata = self.data[:,0]
            self.ydata = self.data[:,1]
            self.accessingData.release()

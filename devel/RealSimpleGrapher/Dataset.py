'''
Parent class for datasets
'''
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from PyQt4 import QtCore
from twisted.internet.threads import deferToThread
import numpy as np

class Dataset(QtCore.QObject):
    
    def __init__(self, data_vault, context, dataset, directory, datasetName, reactor, parent=None):
        super(Dataset, self).__init__()
        self.data = None
        self.accessingData = DeferredLock()
        self.parent = parent
        self.reactor = reactor
        self.dataset = dataset
        self.directory = directory
        self.datasetName = datasetName
        self.data_vault = data_vault
        self.updateCounter = 0
        self.context = context
        self.connectDataVault()
        self.setupListeners()

    @inlineCallbacks
    def connectDataVault(self):
        self.context = yield self.cxn.context()
        yield self.data_vault.cd(self.directory, context = self.context)
        yield self.data_vault.open(self.dataset, context = self.context)

    @inlineCallbacks
    def setupListeners(self):
        yield self.data_vault.signal__data_available(11111, context = self.context)
        yield self.data_vault.addListener(listener = self.updateData, source = None, ID = 11111, context = self.context)


    @inlineCallbacks
    def openDataset(self):
        yield self.data_vault.cd(self.directory, context = self.context)
        yield self.data_vault.open(self.dataset, context = self.context)
        #yield self.getParameters()

    @inlineCallbacks
    def getParameters(self):
        self.parameters = yield self.data_vault.parameters(context = self.context)
        self.parameterValues = []
        for parameter in self.parameters:
            parameterValue = yield self.data_vault.get_parameter(parameter, context = self.context)
            self.parameterValues.append(parameterValue)

    # signal for new data avalable
    def updateData(self, x, y):
        print "data updated"
        self.updateCounter += 1
        self.getData()

    @inlineCallbacks
    def getData(self):
        Data = yield self.data_vault.get(100, context = self.context)
        if (self.data == None):
            yield self.accessingData.acquire()
            self.data = Data.asarray
            self.accessingData.release()
        else:
            yield self.accessingData.acquire()
            self.data = np.append(self.data, Data.asarray, 0)
            self.accessingData.release()

    @inlineCallbacks
    def getLabels(self):
        labels = []
        yield self.openDataset()
        variables = yield self.data_vault.variables(context = self.context)
        for i in range(len(variables[1])):
            labels.append(variables[1][i][1] + ' - ' + self.datasetName)
        returnValue(labels)

    @inlineCallbacks
    def disconnectDataSignal(self):
        yield self.data_vault.removeListener(listener = self.updateData, source = None, ID = 11111, context = self.context)

'''
Parent class for datasets
'''
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from PyQt5 import QtCore
from twisted.internet.threads import deferToThread
import numpy as np

class Dataset(QtCore.QObject):
    
    def __init__(self, data_vault, context, dataset_location,reactor):
        super(Dataset, self).__init__()
        self.data = None
        self.accessingData = DeferredLock()
        self.reactor = reactor
        self.dataset_location = dataset_location
        self.data_vault = data_vault
        self.updateCounter = 0
        self.context = context
        self.connectDataVault()
        self.setupListeners()

    @inlineCallbacks
    def connectDataVault(self):
        yield self.data_vault.cd(self.dataset_location[0], context = self.context)
        path, dataset_name = yield self.data_vault.open(self.dataset_location[1], context = self.context)
        self.dataset_name = dataset_name

    @inlineCallbacks
    def setupListeners(self):
        yield self.data_vault.signal__data_available(11111, context = self.context)
        yield self.data_vault.addListener(listener = self.updateData, source = None, ID = 11111, context = self.context)


    @inlineCallbacks
    def openDataset(self):
        yield self.data_vault.cd(self.dataset_location[0], context = self.context)
        yield self.data_vault.open(self.dataset_location[1], context = self.context)

    @inlineCallbacks
    def getParameters(self):
        parameters = yield self.data_vault.parameters(context = self.context)
        parameterValues = []
        for parameter in parameters:
            parameterValue = yield self.data_vault.get_parameter(parameter, context = self.context)
            parameterValues.append( (parameter, parameterValue) )
        returnValue(parameterValues)

    def updateData(self, x, y):
        self.updateCounter += 1
        self.getData()

    @inlineCallbacks
    def getData(self):
        Data = yield self.data_vault.get(100, context = self.context)
        if (self.data is None):
            yield self.accessingData.acquire()
            try:
                self.data = Data.asarray
            except:
                self.data = Data
            self.accessingData.release()
        else:
            yield self.accessingData.acquire()
            try:
                self.data = np.append(self.data, Data.asarray, 0)
            except:
                self.data = np.append(self.data, Data, 0)
            self.accessingData.release()

    @inlineCallbacks
    def getLabels(self):
        labels = []
        yield self.openDataset()
        variables = yield self.data_vault.variables(context = self.context)
        for i in range(len(variables[1])):
            labels.append(variables[1][i][1] + ' - ' + self.dataset_name)
        returnValue(labels)

    @inlineCallbacks
    def disconnectDataSignal(self):
        yield self.data_vault.removeListener(listener = self.updateData, source = None, ID = 11111, context = self.context)

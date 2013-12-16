'''

Parent class for datasets. Inherit from here to plot a new kind of dataset.

'''

from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from PyQt4 import QtCore
from twisted.internet.threads import deferToThread

class Dataset(QtCore.QObject):

    def __init__(self, parent, cxn, context, dataset, directory, datasetName, reactor):
        super(Dataset, self).__init__()

        self.parent = parent
        self.cxn = cxn
        self.context = context
        self.datset = dataset
        self.directory = directory
        
        self.setupListeners(self.context)

    @inlineCallbacks
    def setupListeners(self, context):
        yield self.cxn.data_vault.signal__data_available(11111, context = context)
        yield self.cxn.data_vault.addListener(listener = self.updateData, source = None, ID = 11111, context = context)
    
    @inlineCallbacks
    def openDataset(self, context):
        yield self.cxn.data_vault.cd(self.directory, context = context)
        yield self.cxn.data_vault.open(self.dataset, context = context)
        self.parameters = yield self.cxn.data_vault.parameters(context = context)
        self.parameterValues = []
        for parameter in self.parameters:
            parameterValue = yield self.cxn.data_vault.get_parameter(parameter, context = context)
            self.parameterValues.append(parameterValue)

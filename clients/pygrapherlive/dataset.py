'''
The data is assumed to be an array with at least 2 dimensions: a list of x values,
and at least one list of y values.

Data is temporarily stored in a buffer. Once the data is retrieved by the Connections
class, the buffer emptied.

'''

from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from PyQt4 import QtCore
from twisted.internet.threads import deferToThread
import numpy as np
import time

class Dataset(QtCore.QObject):
    
    """Class to handle incoming data and prepare them for plotting """
    def __init__(self, cxn, context, dataset, directory):
        super(Dataset, self).__init__()
        self.accessingData = DeferredLock()
        self.cxn = cxn
        self.context = context # context of the first dataset in the window
        self.dataset = dataset
        self.directory = directory
        self.data = None
        self.hasPlotParameter = False
        self.cnt = 0
        self.setupDataListener(self.context)
        
    @inlineCallbacks
    def checkForPlotParameter(self):
        self.parameters = yield self.cxn.data_vault.get_parameters(context = self.context)
        if (self.parameters != None):
            for (parameterName, value) in self.parameters:
                if (str(parameterName) == 'plotLive'):
                    self.hasPlotParameter = True
                    
    # open dataset in order to listen for new data signals in current context        
    @inlineCallbacks
    def openDataset(self, context):
        yield self.cxn.data_vault.cd(self.directory, context = context)
        yield self.cxn.data_vault.open(self.dataset, context = context)
    
    @inlineCallbacks
    def setupParameterListener(self, context):
        yield self.cxn.data_vault.signal__new_parameter(66666, context = context)
        yield self.cxn.data_vault.addListener(listener = self.updateParameter, source = None, ID = 66666, context = context)
    
    # Over 60 seconds, check if the dataset has the appropriate 'plotLive' parameter            
    @inlineCallbacks
    def listenForPlotParameter(self):
        for i in range(120):
            if (self.hasPlotParameter == True):
                returnValue(self.hasPlotParameter)
            yield deferToThread(time.sleep, .5)
        returnValue(self.hasPlotParameter)
            
    def updateParameter(self, x, y):
        if (self.hasPlotParameter == False):
            self.hasPlotParameter = True
        self.checkForPlotParameter()

        #append whatever to self.parameters
    
    # sets up the listener for new data
    @inlineCallbacks
    def setupDataListener(self, context):
        yield self.cxn.data_vault.signal__data_available(11111, context = context)
        yield self.cxn.data_vault.addListener(listener = self.updateData, source = None, ID = 11111, context = context)
        #self.setupDeferred.callback(True)
         
    # new data signal
    def updateData(self,x,y):
        self.getData(self.context)
      
    # returns the current data
    @inlineCallbacks
    def getData(self,context):
        Data = yield self.cxn.data_vault.get(100, context = context)
        if (self.data == None):
            self.data = Data.asarray
        else:
            yield self.accessingData.acquire()         
            self.data = np.append(self.data, Data.asarray, 0)
            self.accessingData.release()
        
    @inlineCallbacks
    def emptyDataBuffer(self):
        yield self.accessingData.acquire()
        del(self.data)
        self.data = None
        self.accessingData.release()
    
    @inlineCallbacks
    def getYLabels(self):
        labels = []
        variables = yield self.cxn.data_vault.variables(context = self.context)
        for i in range(len(variables[1])):
            labels.append(variables[1][i][1])
        returnValue(labels)
            
        
from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread
from grapherwindow import FirstWindow, GrapherWindow
from dataset import Dataset
import time

GraphRefreshTime = .1; # s, how often the plot updates

class CONNECTIONS(QtGui.QGraphicsObject):
    '''
    The CONNECTIONS serves as a mediator between the Dataset class and the GrapherWindow
    class. 
    
    A grapher works by keeping track of datasets and determining which windows
    to plot them on. The main dictionary, dwDict, relates Dataset objects with GrapherWindow
    objects. Each time a new dataset is created, CONNECTIONS creates a unique 
    Dataset object. It then determines which GrapherWindow objects the dataset should
    be drawn on. i.e.:
    
        Without dataset overlaying (dwDict):
        
            [Dataset1] = [GrapherWindow1]
            [Dataset2] = [GrapherWindow2]
            [Dataset3] = [GrapherWindow3]
                       .
                       .
                       .
    
        With dataset overlaying (dwDict):

            [Dataset1] = [GrapherWindow1, GrapherWindow3]
            [Dataset2] = [GrapherWindow2]
            [Dataset3] = [GrapherWindow3, GrapherWindow2]
                       .
                       .
                       .
    
    GrapherWindow objects are added and removed from the dictionary depending on factors
    such as overlaying datasets or closing windows.
    
    Note: the grapher will only plot datasets that possess the 'plotLive' parameter. This 
    parameter is checked for in the Dataset class. This prevents unwanted new datasets from being plotted
    Old datasets that are manually loaded from graph are exempt from this requirement.
    
    There is a main timer event that retrieves data from the Dataset buffer, sends it to
    the GrapherWindow, and calls on GrapherWindow to draw the plot. This ensures that all datasets
    are plotted constantly in order to maintain a live update.     

    '''

    def __init__(self, reactor, parent=None):
        super(CONNECTIONS, self).__init__()
        self.reactor = reactor
        self.dwDict = {} # dictionary relating Dataset and ApplicationWindow
        self.datasetDict = {} # dictionary relating a Dataset object with the dataset and directory 
        self.winList = []
        self.connect()
        self.startTimer()

    # connect to the data vault    
    @inlineCallbacks    
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        self.cxn = yield connectAsync()
        self.server = yield self.cxn.data_vault
        yield self.setupListeners()
        context = yield self.cxn.context() # create a new context
        self.introWindow = FirstWindow(self, context)
        self.introWindow.show()
        print 'Connection established: now listening dataset.'

    # set up dataset listener    
    @inlineCallbacks
    def setupListeners(self):               
        yield self.server.signal__new_dataset_dir(99999)#, context = context)
        yield self.server.addListener(listener = self.updateDataset, source = None, ID = 99999)#, context = context)    
        yield self.server.signal__new_directory(77777)#, context = context)
        yield self.server.addListener(listener = self.addDirItem, source = None, ID = 77777)#, context = context)

    def addDirItem(self,x,y):
        #directory = tuple(eval(str(y))) 
        self.introWindow.datavaultwidget.populateList()
        for i in self.winList:
            i.datavaultwidget.populateList()
           
    # new dataset signal
    def updateDataset(self,x,y):
        dataset = int(y[0][0:5]) # retrieve dataset number
        directory = y[1] # retrieve directory
        itemLabel = y[0]
        self.addDatasetItem(itemLabel, directory)
        print directory
        print dataset
        manuallyLoaded = False # ensure that this dataset was not loaded manually
        self.newDataset(dataset, directory, manuallyLoaded)
 
    def addDatasetItem(self, itemLabel, directory):
        self.introWindow.datavaultwidget.addDatasetItem(itemLabel, directory)
        for i in self.winList:
            i.datavaultwidget.addDatasetItem(itemLabel, directory)
 
    # Creates a new Dataset object and checks if it has the 'plotLive' parameter
    @inlineCallbacks
    def newDataset(self, dataset, directory, manuallyLoaded):
        context = yield self.cxn.context() # create a new context
        datasetObject = Dataset(self.cxn, context, dataset, directory)
        self.datasetDict[dataset, directory] = datasetObject
        yield datasetObject.openDataset(context)
        yield datasetObject.setupParameterListener(context)
        yield datasetObject.checkForPlotParameter()
        datasetLabels = yield datasetObject.getYLabels()
        # if the dataset was loaded manually, it does not require the 'plotLive' parameter 
        if (manuallyLoaded == True):
            self.prepareDataset(datasetObject, dataset, directory, datasetLabels, context)
        else:        
            hasPlotParameter = yield datasetObject.listenForPlotParameter()
            if (hasPlotParameter == True):
                self.prepareDataset(datasetObject, dataset, directory, datasetLabels, context)
            else:
                # This data is not for plotting. Remove it.
                # There should be a cleaner way of doing this
                del datasetObject

    # Prepare the dataset for plotting
    @inlineCallbacks
    def prepareDataset(self, datasetObject, dataset, directory, datasetLabels, context):
        #if windows request overlay, update those. else, create a new window.
        overlayWindows = self.getOverlayingWindows()
        if overlayWindows:
            self.dwDict[datasetObject] = overlayWindows
            for window in overlayWindows:
                window.qmc.initializeDataset(dataset, directory, datasetLabels)
                window.createDatasetCheckbox(dataset, directory) 
        else:
            win = self.newGraph(context)
            yield deferToThread(time.sleep, .01)
            self.dwDict[datasetObject] = [win]
            win.qmc.initializeDataset(dataset, directory, datasetLabels)
            win.createDatasetCheckbox(dataset, directory) 

    # create a new graph window
    def newGraph(self, context):
        win = GrapherWindow(self, context)
        self.winList.append(win)
        win.show()
        return win
            
    def startTimer(self): 
        lc = LoopingCall(self.timerEvent)
        lc.start(GraphRefreshTime)
     
    # Main timer, cycles through dwDict. For each dataset, determines...
    # ... which windows to draw the dataset on. Then draws the plot.   
    @inlineCallbacks
    def timerEvent(self):
        for datasetObject in self.dwDict.keys():
            windowsToDrawOn = self.dwDict[datasetObject]
            if (datasetObject.data != None):
                data = datasetObject.data
                yield datasetObject.emptyDataBuffer()
                for i in windowsToDrawOn:
                    i.qmc.setPlotData(datasetObject.dataset, datasetObject.directory, data)
            for i in windowsToDrawOn:
                # if dataset is intended to be drawn (a checkbox governs this)
                if i.datasetCheckboxes[datasetObject.dataset, datasetObject.directory].isChecked():
                    i.qmc.drawPlot(datasetObject.dataset, datasetObject.directory)
    
    # Cycles through the values in each key for checked Overlay boxes, returns the windows...
    # ...with the overlay button checked
    def getOverlayingWindows(self):
        self.overlaidWindows = []
        for i in self.dwDict.keys():
            values = self.dwDict[i]
            for j in values:
                if j.cb2.isChecked():
                    # skip duplicates
                    if j in self.overlaidWindows:
                        pass
                    else:
                        self.overlaidWindows.append(j)
        return self.overlaidWindows
    
    def getParameters(self, dataset, directory):
        parameters = self.datasetDict[dataset, directory].parameters
        return parameters
    
    # Datasets no longer need to be drawn on closed windows
    def removeWindowFromDictionary(self, win):
        for i in self.dwDict.keys():
            values = self.dwDict[i]
            for j in values:
                if j == win:
                    self.dwDict[i].remove(j)
                    
    # Datavault widgets no longer need to be updated
    def removeWindowFromWinList(self, win):
        for i in self.winList:
            if i == win:
                self.winList.remove(i)
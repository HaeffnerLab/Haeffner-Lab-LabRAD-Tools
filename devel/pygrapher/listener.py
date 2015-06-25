'''
Tool for listening to datavault. It is designed to be easily imported
for writing specialized "grapher" applications. Each grapher application
will contain a Listener.

The logic flow is something like this:
1. Define a Listener object, a filter, and an ignore list. The filter specifies which datavault
directories to respond to. For the "main" grapher app, just pass filter=['']--
meaning listen to everything. But if you want a specialized grapher to plot
the output of a particular experiment in some way, make a filter like
filter=['', 'Experiments', 'SomeExperiment'] to only respond to data coming into
that directory. The ignore list is the complement of the filter. It allows
you to ignore anything in some directory. This is because you might have a specialized
grapher responding to a certain directory, you want to also tell the main grapher
to ignore this directory.

2. Decide if a Dataset object needs to be created for this new data.

To make a graphing window, inherit the Listener class. In order to inherit the
Listener class, you need to implement:
1. prepareDataset() -- stuff for preparing to call

'''
from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from twisted.internet.threads import deferToThread
import importlib
from dataset import Dataset
import pdb

class Listener(QtGui.QGraphicsObject):
    
    def __init__(self, filter, ignore, reactor):
        self.reactor = reactor
        self.filter = filter
        self.ignore = ignore
        self.datasetDict = {}
        self.connect()

    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        
        self.cxn = yield connectAsync()
        self.context = yield self.cxn.context()
        self.setupListeners()

    @inlineCallbacks
    def setupListeners(self):
        #yield self.dv.signal__new_dataset_dir(88888, context = self.context)
        #yield self.dv.addListener(listener = self.updateDataset, source = None, ID = 88888, context = self.context)    
        #yield self.dv.signal__new_directory(77777, context = self.context)
        #yield self.dv.addListener(listener = self.addDirItem, source = None, ID = 77777, context = self.context)
        yield self.cxn.data_vault.signal__new_parameter_dataset(99999, context = self.context)
        yield self.cxn.data_vault.addListener(listener = self.updateParameter, source = None, ID = 99999, context = self.context)

    # is this a signal we should be listening to?
    def check_filter(self, dir):
        '''
        We just check to see if the filter, as a set, is a subset of the directory
        that we're looking at. This can be nice because it gives a bit of flexibility
        in how you organize your datavault.

        i.e. If I want to organize my datavault with experiments first, then days,
        the filter ['', 'SomeExperiment'] works, as ['', 'SomeExperiment', 'SomeDate'] would
        be the directory. But it also works if the directory is ['', 'SomeDate', 'SomeExperiment']

        But it can also lead to problems if directories are stupidly named, (i.e. you want to
        listen to ['', 'SomeExperiment', 'SomeSubData'], but not ['', 'SomeSubData', 'SomeExperiment'])

        ignore has precedence over filter
        '''
        
        if set(self.ignore).issubset(dir):
            print "ignoring"
            return False
        elif set(self.filter).issubset(set(dir)): return True
        else: return False

    # new dataset signal
    def updateParameter(self, x, y):
        dataset = y[0]
        datasetName = y[1]
        dir = y[2]
        print y[3]
        if self.check_filter(dir):
            # This is a dataset we should care about
            if (y[3] == 'plotLive'):
                # param to plot this data on the fly
                self.newDataset(dataset, dir, datasetName)
    
    @inlineCallbacks
    def newDataset(self, dataset, dir, datasetName):
        '''
        First, see if someone has been courteous enough to tell us what kind of dataset
        we're dealing with. Then create the appropriate dataset object, and then
        call prepareDataset() -- implemented by derived class!!
        '''
        #from PyQt4.QtCore import pyqtRemoveInputHook
        #pyqtRemoveInputHook()
        #pdb.set_trace()
        print datasetName
        context = yield self.cxn.context()
        yield self.cxn.data_vault.cd(dir, context = context)
        yield self.cxn.data_vault.open(dataset, context = context)
        try:
            # if the plot type is defined, assign the dataset to a predefined type
            plotTypePath = yield self.cxn.data_vault.get_parameter('plotTypePath', context = context)
            plotClass = yield self.cxn.data_vault.get_parameter('plotClass', context = context)            
            module = importlib.import_module(plotTypePath)
            cls = getattr(module, plotClass)
            datasetObject = cls(self.cxn, context, dataset, dir, datasetName, self.reactor)
        except:
            # no plot type is defined. Now we just get the general type
            datasetObject = Dataset(self.cxn, context, dataset, dir, datasetName, self.reactor)

        self.datasetDict[dataset, dir] = datasetObject
        self.prepareDataset(datasetObject)

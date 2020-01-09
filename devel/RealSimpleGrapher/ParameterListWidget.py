import os
import cPickle as pickle
from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred

class ParameterList(QtGui.QWidget):
    
    def __init__(self, dataset):
        super(ParameterList, self).__init__()
        self.dataset = dataset
        mainLayout = QtGui.QVBoxLayout() 
        self.parameterListWidget = QtGui.QListWidget()
        mainLayout.addWidget(self.parameterListWidget)        
        self.setWindowTitle(str(dataset.dataset_name))# + " " + str(dataset.directory))
        self.populate()
        self.setLayout(mainLayout)
        self.show()

    @inlineCallbacks
    def populate(self):
        dsn = self.dataset.dataset_location
        folder = "/home/staq/data/" + ".dir/".join(dsn[0][1:]) + ".dir/"
        file =  dsn[1] + ".pickle"
        
        if file in os.listdir(folder):
            pkl_file = open(folder + file, "rb")
            d = pickle.load(pkl_file)
            parameters = sorted(d.items())
        else:
            parameters = yield self.dataset.getParameters()
        
        self.parameterListWidget.clear()
        self.parameterListWidget.addItems([str(x) for x in sorted(parameters)])

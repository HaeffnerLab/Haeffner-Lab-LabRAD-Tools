import os
import pickle as pickle
from PyQt5 import QtCore, QtGui, QtWidgets
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred

class ParameterList(QtWidgets.QWidget):
    
    def __init__(self, dataset):
        super(ParameterList, self).__init__()
        self.dataset = dataset
        mainLayout = QtWidgets.QVBoxLayout() 
        self.parameterListWidget = QtWidgets.QListWidget()
        mainLayout.addWidget(self.parameterListWidget)        
        self.setWindowTitle(str(dataset.dataset_name))# + " " + str(dataset.directory))
        self.populate()
        self.setLayout(mainLayout)
        self.show()

    @inlineCallbacks
    def populate(self):
        dsn = self.dataset.dataset_location
        folder = "/home/space-time/data/" + ".dir/".join(dsn[0][1:]) + ".dir/"
        file =  dsn[1] + ".pickle"
        
        if file in os.listdir(folder):
            pkl_file = open(folder + file, "rb")
            d = pickle.load(pkl_file)
            parameters = sorted(d.items())
        else:
            parameters = yield self.dataset.getParameters()
        
        self.parameterListWidget.clear()
        self.parameterListWidget.addItems([str(x) for x in sorted(parameters)])

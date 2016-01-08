import sys
from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred

class ParameterList(QtGui.QWidget):
    
    def __init__(self, dataset):
        super(ParameterList, self).__init__()
        self.dataset = dataset
        mainLayout = QtGui.QVBoxLayout() 
        self.parameterListWidget = QtGui.QListWidget()
        mainLayout.addWidget(self.parameterListWidget)        
        self.setWindowTitle(str(dataset.dataset) + " " + str(dataset.directory))
        self.populate()
        self.setLayout(mainLayout)
        self.show()

    @inlineCallbacks
    def populate(self):
        parameters = yield self.dataset.getParameters()
        self.parameterListWidget.clear()
        self.parameterListWidget.addItems([str(x) for x in sorted(parameters)])

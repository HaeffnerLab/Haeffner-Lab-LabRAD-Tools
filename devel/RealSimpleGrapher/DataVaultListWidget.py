import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
#from labrad.wrappers import connectAsync
import socket

class DataVaultList(QtWidgets.QWidget):

    def __init__(self, tracename, parent = None):
        super(DataVaultList, self).__init__()
        self.tracename = tracename
        self.connect()

    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(name = socket.gethostname() + ' Data Vault Client')
        self.grapher = yield self.cxn.grapher
        self.dv = yield self.cxn.data_vault
        self.initializeGUI()

    def initializeGUI(self):
        mainLayout = QtWidgets.QVBoxLayout() 
        self.dataListWidget = QtWidgets.QListWidget()
        self.dataListWidget.setSortingEnabled(True)
        self.dataListWidget.doubleClicked.connect(self.onDoubleclick)
        mainLayout.addWidget(self.dataListWidget)        
        self.setWindowTitle('Data Vault')
        self.setLayout(mainLayout)
        self.populate()
        self.show()

    @inlineCallbacks
    def populate(self):
        self.dataListWidget.clear()
        ls = yield self.dv.dir()
        self.dataListWidget.addItem('...')
        self.dataListWidget.addItems(ls[0])
        if ls[1] is not None:
            self.dataListWidget.addItems(sorted(ls[1]))
    
    @inlineCallbacks
    def onDoubleclick(self, item):
        item = self.dataListWidget.currentItem().text()
        if item == '...':
            yield self.dv.cd(1)
        else:
            try:
                yield self.dv.cd(str(item))
            except:
                path = yield self.dv.cd()
                yield self.grapher.plot((path, str(item)), self.tracename, False)
        self.populate()

    def closeEvent(self, event):
        self.cxn.disconnect()

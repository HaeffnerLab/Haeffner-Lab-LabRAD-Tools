import sys
from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
#from labrad.wrappers import connectAsync
import socket

class DataVaultList(QtGui.QWidget):
    traceClicked = QtCore.pyqtSignal('QString')

    def __init__(self, parent = None):
        super(DataVaultList, self).__init__()
	self.connect()

    @inlineCallbacks
    def connect(self):
	from labrad.wrappers import connectAsync
	self.cxn = yield connectAsync(name = socket.gethostname() + ' Data Vault Client')
	self.dv = yield self.cxn.data_vault
	self.initializeGUI()

    def initializeGUI(self):
        mainLayout = QtGui.QVBoxLayout() 
        self.dataListWidget = QtGui.QListWidget()
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
		self.dataListWidget.addItems(ls[1])
    
    @inlineCallbacks
    def onDoubleclick(self, item):
	item = self.dataListWidget.currentItem().text()
	if item == '...':
	     yield self.dv.cd(1)
	else:
	     try:
	          yield self.dv.cd(str(item))
	     except:
		  self.traceClicked.emit(str(item))
	self.populate()

    def closeEvent(self, event):
	self.cxn.disconnect()

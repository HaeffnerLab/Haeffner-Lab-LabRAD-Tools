from PyQt4 import QtGui, QtCore, uic
from twisted.internet.defer import inlineCallbacks, returnValue
import os

SIGNALID = 874193

class pmtWidget(QtGui.QWidget):
    def __init__(self, reactor, parent=None):
        super(pmtWidget, self).__init__(parent)
        self.reactor = reactor
        basepath =  os.path.dirname(__file__)
        path = os.path.join(basepath,"qtui", "pmtfrontend.ui")
        uic.loadUi(path,self)
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        cxn = yield connectAsync()
        self.server = cxn.normalpmtflow
        yield self.initializeContent()
        yield self.setupListeners()
        #connect functions
        self.pushButton.toggled.connect(self.on_toggled)
        self.newSet.clicked.connect(self.onNewSet)
        self.doubleSpinBox.valueChanged.connect(self.onNewDuration)
        self.comboBox.currentIndexChanged.connect(self.onNewMode)
    
    @inlineCallbacks
    def setupListeners(self):
        yield self.server.signal__new_count(SIGNALID)
        yield self.server.addListener(listener = self.followSignal, source = None, ID = SIGNALID)
    
    @inlineCallbacks
    def initializeContent(self):
        dataset = yield self.server.currentdataset()
        self.lineEdit.setText(dataset)
        running = yield self.server.isrunning()
        self.pushButton.setChecked(running)
        self.setText(self.pushButton)
        duration = yield self.server.get_time_length()
        range = yield self.server.get_time_length_range()
        self.doubleSpinBox.setRange(*range)
        self.doubleSpinBox.setValue(duration)
    
    def followSignal(self,signal,value):
        self.lcdNumber.display(value)
    
    @inlineCallbacks
    def on_toggled(self, state):
        if state:
            yield self.server.record_data()
            newset = yield self.server.currentdataset()
            self.lineEdit.setText(newset)
        else:
            yield self.server.stoprecording()
            self.lcdNumber.display(0)
        self.setText(self.pushButton)
    
    @inlineCallbacks
    def onNewSet(self, x):
        yield self.server.start_new_dataset()
        newset = yield self.server.currentdataset()
        self.lineEdit.setText(newset)
    
    @inlineCallbacks
    def onNewMode(self, mode):
        text = str(self.comboBox.itemText(mode))
        yield self.server.set_mode(text)
        
    def setText(self, obj):
        state = obj.isChecked()
        if state:
            obj.setText('ON')
        else:
            obj.setText('OFF')
    
    def onNewData(self,count):
        self.lcdNumber.display(count)
    
    @inlineCallbacks
    def onNewDuration(self, value):
        yield self.server.set_time_length(value)
    
    def closeEvent(self, x):
        self.reactor.stop()   

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    pmtWidget = pmtWidget(reactor)
    pmtWidget.show()
    reactor.run()
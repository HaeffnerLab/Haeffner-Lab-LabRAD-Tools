from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks

SIGNALID = 378903

class hvWidget(QtGui.QFrame):
    def __init__(self, reactor, parent=None):
        super(hvWidget, self).__init__(parent)
        #which channels to show and in what order, if None, then shows all
        self.reactor = reactor
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync()
        self.server = yield self.cxn.highvolta
        self.initializeGUI()
        yield self.setupListeners()
        
    @inlineCallbacks
    def initializeGUI(self):
        #set layout
        self.setFrameStyle(0x0001 | 0x0030)
        title = QtGui.QLabel("HighVolt A")
        title.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        rmin, rmax = yield self.server.get_range()
        voltage = yield self.server.getvoltage()
        self.spin = QtGui.QDoubleSpinBox()
        self.spin.setRange(rmin, rmax)
        self.spin.setValue(voltage)
        self.spin.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        self.spin.setDecimals(0)
        self.spin.setSuffix(' V')
        self.spin.valueChanged.connect(self.onNewVoltage)
        self.spin.setKeyboardTracking(False)
        layout = QtGui.QGridLayout()
        layout.addWidget(title, 0, 0)
        layout.addWidget(self.spin, 1 , 0)
        self.setLayout(layout)
    
    @inlineCallbacks
    def onNewVoltage(self, val):
        yield self.server.setvoltage(val)
    
    @inlineCallbacks
    def setupListeners(self):
        yield self.server.signal__new_voltage(SIGNALID)
        yield self.server.addListener(listener = self.followSignal, source = None, ID = SIGNALID)
    
    def followSignal(self, x, volt):
        self.spin.blockSignals(True)
        self.spin.setValue(volt)
        self.spin.blockSignals(False)

    def closeEvent(self, x):
        self.reactor.stop()
    
    def sizeHint(self):
        return QtCore.QSize(100,100)
            
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    hvWidget = hvWidget(reactor)
    hvWidget.show()
    reactor.run()
from qtui.QCustomFreqPower import QCustomFreqPower
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui

SIGNAL_ID1 = 187571
SIGNAL_ID2 = 187572

class TRAPDRIVE_CONTROL(QCustomFreqPower):
    def __init__(self,reactor, parent=None):
        super(TRAPDRIVE_CONTROL, self).__init__('Trap Drive', parent)
        self.reactor = reactor
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync()
        self.server = self.cxn.lattice_pc_hp_server
        self.setupWidget()
        self.setupListeners()
        
    @inlineCallbacks
    def setupListeners(self):
        yield self.server.signal__settings_updated(SIGNAL_ID1)
        yield self.server.addListener(listener = self.followNewSetting, source = None, ID = SIGNAL_ID1)
        yield self.server.signal__state_updated(SIGNAL_ID2)
        yield self.server.addListener(listener = self.followNewState, source = None, ID = SIGNAL_ID2)
    
    def followNewSetting(self, x, (kind,value)):
        if kind == 'freq':
            self.setFreqNoSignal(value)
        elif kind == 'power':
            self.setPowerNoSignal(value)
    
    def followNewState(self, x, checked):
        self.setStateNoSignal(checked)
        
    @inlineCallbacks
    def setupWidget(self):
        #get ranges
        MinPower,MaxPower = yield self.server.get_power_range()
        MinFreq,MaxFreq = yield self.server.get_frequency_range()
        self.setPowerRange((MinPower,MaxPower))
        self.setFreqRange((MinFreq,MaxFreq))
        #get initial values
        initpower = yield self.server.getpower()
        initfreq = yield self.server.getfreq()
        initstate = yield self.server.getstate()
        self.spinPower.setValue(initpower)
        self.spinFreq.setValue(initfreq)
        self.buttonSwitch.setChecked(initstate)
        self.setText(initstate)
        #connect functions
        self.spinPower.valueChanged.connect(self.powerChanged)
        self.spinFreq.valueChanged.connect(self.freqChanged) 
        self.buttonSwitch.toggled.connect(self.switchChanged)
        
    @inlineCallbacks
    def powerChanged(self, pwr):
        yield self.server.setpower(pwr)
        
    @inlineCallbacks
    def freqChanged(self, freq):
        yield self.server.setfreq(freq)
        
    @inlineCallbacks
    def switchChanged(self, pressed):
        if pressed:
            yield self.server.setstate(pressed)
        else:
            self.dlg = MyAppDialog()
            self.dlg.accepted.connect(self.userAccept)
            self.dlg.rejected.connect(self.userReject)
            self.dlg.show()
    
    @inlineCallbacks 
    def userAccept(self):
        yield self.server.setstate(False)
        
    def userReject(self):
        self.setStateNoSignal(True)     
    
    def closeEvent(self, x):
        self.reactor.stop()   
    
class MyAppDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.confirmButton = QtGui.QPushButton(Dialog)
        self.confirmButton.setText('Confirm')
        self.gridLayout.addWidget(self.confirmButton,1,0)
        self.declineButton = QtGui.QPushButton(Dialog)
        self.declineButton.setText('Decline')
        self.gridLayout.addWidget(self.declineButton,1,1)
        self.label = QtGui.QLabel('Turning off RF')
        self.font = QtGui.QFont()
        self.font.setPointSize(20)
        self.label.setFont(self.font)
        self.gridLayout.addWidget(self.label,0,0)
        self.confirmButton.clicked.connect(Dialog.accept)
        self.declineButton.clicked.connect(Dialog.reject)

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    trapdriveWidget = TRAPDRIVE_CONTROL(reactor)
    trapdriveWidget.show()
    reactor.run()
from PyQt4 import QtGui
from PyQt4 import QtCore,uic
from twisted.internet.defer import inlineCallbacks, returnValue
from Devices_config import Device_config



#############

#### = updated in _mod version. Changes: values are not applied on entry, rather we wait until the 'Set' button is pressed

#############

MinPower = -86 #dbM
MaxPower = 25
DEFPower = -20
MinFreq = 0 #Mhz
MaxFreq = 99
DEFFreq = 10

class TD(QtGui.QWidget):
    def __init__(self, reactor, parent=None):
        super(TD,self).__init__(parent)
        self.reactor = reactor
        self.connect()
        self.makeGUI()
        
    def makeGUI(self):
        layout = QtGui.QGridLayout()
        subLayout = QtGui.QGridLayout()
        superLayout = QtGui.QGridLayout()
        groupbox = QtGui.QGroupBox('Trap Drive')
        groupboxLayout = QtGui.QGridLayout()
        self.powerCtrl = QtGui.QDoubleSpinBox()
        self.powerCtrl.setRange (MinPower,MaxPower)
        self.powerCtrl.setDecimals (2)
        self.powerCtrl.setSingleStep(.5)
#        self.powerCtrl.setSuffix(' dBm')
        self.frequencyCtrl = QtGui.QDoubleSpinBox()
        self.frequencyCtrl.setRange (MinFreq,MaxFreq)
      
        self.frequencyCtrl.setDecimals (5)
        self.frequencyCtrl.setSingleStep(.1)
#        self.frequencyCtrl.setSuffix(' MHz')
        self.updateButton = QtGui.QPushButton('Get')
        self.stateButton = QtGui.QPushButton()
        self.maximumButton = QtGui.QPushButton('Maximum')
        
        ####   button to apply user-specified frequency and power
        self.setButton = QtGui.QPushButton('Set')
        
        superLayout.addLayout(layout,0,0)
        groupbox.setLayout(groupboxLayout)
        layout.addWidget(groupbox,0,0)
        groupboxLayout.addWidget(QtGui.QLabel('Frequency [MHz]'),1,0) 
        groupboxLayout.addWidget(self.frequencyCtrl,1,1)
        groupboxLayout.addWidget(QtGui.QLabel('Power [dBm]'),2,0) 
        groupboxLayout.addWidget(self.powerCtrl,2,1)
        groupboxLayout.addWidget(self.stateButton,0,0,1,1)
        groupboxLayout.addWidget(self.updateButton,0,1,1,1)
        groupboxLayout.addWidget(self.maximumButton)

        ####
        groupboxLayout.addWidget(self.setButton)
        
        self.setLayout(superLayout)
    
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        from labrad import types as T
        self.T = T
        self.cxn = yield connectAsync()
        self.server = yield self.cxn.rohdeschwarz_server()
        #self.SMAGPIB = 'cct_camera GPIB Bus - GPIB0::1'
        try:
            yield self.server.select_device()
            #yield self.server.select_device(self.SMAGPIB)
        except Error:
            self.setEnabled(False)
            return
        self.update(0)
        currentpower = yield self.server.amplitude()
        currentfreq = yield self.server.frequency()
        self.powerCtrl.setValue(currentpower)
        self.frequencyCtrl.setValue(currentfreq)
            
        #### Nothing happens on value change!          
        
        ####self.powerCtrl.valueChanged.connect(self.onPowerChange)
        ####self.frequencyCtrl.valueChanged.connect(self.onFreqChange)
        
        self.stateButton.clicked.connect(self.onOutputChange)
        self.updateButton.clicked.connect(self.update)
 #       self.maximumButton.clicked.connect(self.checkMax)
 
        #### connect set Button to the method that writes values to server.
        self.setButton.clicked.connect(self.setFreqAndPower)
    
    @inlineCallbacks
    def onOutputChange(self, state):
        if self.state:
            self.stateButton.setText('Trap Drive   : OFF')
            yield self.server.output(False)
        if not self.state:
            self.stateButton.setText('Trap Drive: ON')
            yield self.server.output(True)
        self.state = not self.state

        
    @inlineCallbacks
    def update(self, c):
        currentpower = yield self.server.amplitude()
        currentfreq = yield self.server.frequency()
        currentstate = yield self.server.output()
      

        self.powerCtrl.setValue(currentpower)
        self.frequencyCtrl.setValue(currentfreq)
        if currentstate:
            self.stateButton.setText('Trap Drive: ON')
        else:
            self.stateButton.setText('Trap Drive: OFF')
        self.state = currentstate
        
    @inlineCallbacks
    def onFreqChange(self, f):
        yield self.server.frequency(self.T.Value(self.frequencyCtrl.value(), 'MHz'))
        


    @inlineCallbacks
    def onPowerChange(self, p):
        yield self.server.amplitude(self.T.Value(self.powerCtrl.value(), 'dBm'))

    #### method to write frequency and power to server (marconi)
    @inlineCallbacks
    def setFreqAndPower(self, state):
        yield self.server.frequency(self.T.Value(self.frequencyCtrl.value(), 'MHz'))
        yield self.server.amplitude(self.T.Value(self.powerCtrl.value(), 'dBm'))

    
    def closeEvent(self, x):
        self.reactor.stop()

class TD_CONTROL(QtGui.QMainWindow):
    def __init__(self, reactor, parent=None):
        super(TD_CONTROL, self).__init__(parent)
        self.reactor = reactor
        W = self.buildW(reactor)
        widget = QtGui.QWidget()
        gridLayout = QtGui.QGridLayout()    
        gridLayout.addWidget(W, 1, 0)
        self.setWindowTitle('Trap Drive Control')
        widget.setLayout(gridLayout) 
        self.setCentralWidget(widget)

    def buildW(self, reactor):        
        W = QtGui.QWidget()
        subLayout = QtGui.QGridLayout()
        subLayout.addWidget(TD(reactor), 1, 0)
        W.setLayout(subLayout)
        return W
                
    def closeEvent(self, x):
        self.reactor.stop()
        
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    TD_CONTROL = TD_CONTROL(reactor)
    TD_CONTROL.show()
    reactor.run()

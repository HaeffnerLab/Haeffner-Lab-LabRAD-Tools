from PyQt4 import QtGui, QtCore
from qtui.QCustomFreqPower import QCustomFreqPower
from twisted.internet.defer import inlineCallbacks

MinPower = -36 #dbM
MaxPower = 0
MinFreq = 0 #Mhz
MaxFreq = 20

class TRAPDRIVE_MODULATION_CONTROL(QCustomFreqPower):
    def __init__(self, reactor, parent=None):
        self.reactor = reactor
        super(TRAPDRIVE_MODULATION_CONTROL,self).__init__('Trap Drive Modulation', parent)
        self.setFreqRange((MinFreq, MaxFreq))
        self.setPowerRange((MinPower,MaxPower))
        self.connect()
    
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        self.cxn = yield connectAsync()
        self.server = yield self.cxn.agilent_server
        try:
            yield self.server.select_device('lattice-pc GPIB Bus - USB0::0x0957::0x0407::MY44051933')
        except Error:
            self.setEnabled(False)
            return
        #set initial values
        initpower = yield self.server.amplitude()
        initfreq = yield self.server.frequency()
        initstate = yield self.server.output()
        #set properties
        self.spinFreq.setDecimals(5)
        self.spinFreq.setSingleStep(10**-4) #set step size to 100HZ
        self.spinPower.setValue(initpower)
        self.spinFreq.setValue(initfreq)
        self.buttonSwitch.setChecked(initstate)
        self.setText(initstate)
        #connect functions
        self.spinPower.valueChanged.connect(self.onPowerChange)
        self.spinFreq.valueChanged.connect(self.onFreqChange) 
        self.buttonSwitch.toggled.connect(self.onOutputChange)   
    
    @inlineCallbacks
    def onOutputChange(self, state):
        yield self.server.output(state)
        
    @inlineCallbacks
    def onFreqChange(self, freq):
        yield self.server.frequency(freq)

    @inlineCallbacks
    def onPowerChange(self, power):
        yield self.server.amplitude(power)
    
    def closeEvent(self, x):
        self.reactor.stop()

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    TRAPDRIVE_MODULATION_CONTROL = TRAPDRIVE_MODULATION_CONTROL(reactor)
    TRAPDRIVE_MODULATION_CONTROL.show()
    reactor.run()
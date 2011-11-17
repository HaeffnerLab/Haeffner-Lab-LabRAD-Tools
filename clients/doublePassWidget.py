from PyQt4 import QtGui, QtCore
from qtui.QCustomFreqPower import QCustomFreqPower
from twisted.internet.defer import inlineCallbacks, returnValue

SIGNALID = 86806

class doublePassWidget(QtGui.QWidget):
    def __init__(self, reactor, parent=None):
        super(doublePassWidget, self).__init__(parent)
        self.reactor = reactor
        self.connect()
        
    @inlineCallbacks
    def connect(self):

        from labrad.wrappers import connectAsync
        from labrad.types import Error
        try:
            self.cxn = yield connectAsync()
            self.server = yield self.cxn.double_pass
        except:
            self.setEnabled(False)
            return
        yield self.loadDict()
        yield self.setupListeners()
        yield self.initializeGUI()
    
    @inlineCallbacks
    def loadDict(self):
        self.d = {}
        names = yield self.server.get_double_pass_list()
        for name in names:
            self.d[name] = QCustomFreqPower(name)
    
    @inlineCallbacks
    def setupListeners(self):
        yield self.server.signal__double_pass_updated(SIGNALID)
        yield self.server.addListener(listener = self.followSignal, source = None, ID = SIGNALID)
    
    def followSignal(self, x, (chanName,typ , value)):
        widget = self.d[chanName]
        if typ == 'frequency':
            widget.spinFreq.blockSignals(True)
            widget.spinFreq.setValue(value)
            widget.spinFreq.blockSignals(False)
        elif typ == 'amplitude':
            widget.spinPower.blockSignals(True)
            widget.spinPower.setValue(value)
            widget.spinPower.blockSignals(False)
        elif typ == 'output':
            value = bool(value)
            widget.buttonSwitch.blockSignals(True)
            widget.buttonSwitch.setChecked(value)
            widget.setText(value)
            widget.buttonSwitch.blockSignals(False)
                
    @inlineCallbacks
    def initializeGUI(self):
        #supply initial information from server
        keys = self.d.keys()
        keys.sort()
        for chanName in keys:
            self.server.select(chanName)
            freq =  yield self.server.frequency()
            ampl = yield self.server.amplitude()
            outp = yield self.server.output()
            freqRange = yield self.server.frequency_range()
            amplRange = yield self.server.amplitude_range()      
            widget = self.d[chanName]
            widget.setPowerRange(amplRange)
            widget.setFreqRange(freqRange)
            widget.spinPower.setValue(ampl)
            widget.spinFreq.setValue(freq)
            widget.buttonSwitch.setChecked(outp)
            widget.setText(outp)
            #connect functions
            widget.spinPower.valueChanged.connect(self.onPowerChange(chanName))
            widget.spinFreq.valueChanged.connect(self.onFreqChange(chanName)) 
            widget.buttonSwitch.toggled.connect(self.onSwitchChanged(chanName))
        #add to layout
        layout =QtGui.QGridLayout()
        self.setLayout(layout)
        for index, chanName in enumerate(keys):
            layout.addWidget(self.d[chanName],index/2, index % 2)
            
    def onPowerChange(self, name):
        @inlineCallbacks
        def func(ampl):
            yield self.server.select(name)
            yield self.server.amplitude(ampl)
        return func
    
    def onFreqChange(self, name):
        @inlineCallbacks
        def func(freq):
            yield self.server.select(name)
            yield self.server.frequency(freq)
        return func
    
    def onSwitchChanged(self, name):
        @inlineCallbacks
        def func(outp):
            yield self.server.select(name)
            yield self.server.output(outp)
        return func

    def sizeHint(self):
        return QtCore.QSize(1000,200)
    
    def closeEvent(self, x):
        self.reactor.stop()
        
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    doublePassWidget = doublePassWidget(reactor)
    doublePassWidget.show()
    reactor.run()
from qtui.QCustomFreqPower import QCustomFreqPower
from twisted.internet.defer import inlineCallbacks
from DDS_CONTROL_config import dds_control_config
from connection import connection
from PyQt4 import QtGui

class DDS_CHAN(QCustomFreqPower):
    def __init__(self, chan, reactor, cxn, context, parent=None):
        super(DDS_CHAN, self).__init__('DDS: {}'.format(chan), True, parent)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor
        self.context = context
        self.chan = chan
        self.server = cxn.servers['Pulser']
        self.import_labrad()
        
    def import_labrad(self):
        from labrad import types as T
        from labrad.types import Error
        self.Error = Error
        self.T = T
        self.setupWidget()

    @inlineCallbacks
    def setupWidget(self, connect = True):
        #get ranges
        MinPower,MaxPower = yield self.server.get_dds_amplitude_range(self.chan, context = self.context)
        MinFreq,MaxFreq = yield self.server.get_dds_frequency_range(self.chan, context = self.context)
        self.setPowerRange((MinPower,MaxPower))
        self.setFreqRange((MinFreq,MaxFreq))
        #get initial values
        initpower = yield self.server.amplitude(self.chan, context = self.context)
        initfreq = yield self.server.frequency(self.chan, context = self.context)
        initstate = yield self.server.output(self.chan, context = self.context)
        self.setStateNoSignal(initstate)
        self.setPowerNoSignal(initpower)
        self.setFreqNoSignal(initfreq)
        #connect functions
        if connect:
            self.spinPower.valueChanged.connect(self.powerChanged)
            self.spinFreq.valueChanged.connect(self.freqChanged) 
            self.buttonSwitch.toggled.connect(self.switchChanged)
    
    def setParamNoSignal(self, param, value):
        if param == 'amplitude':
            self.setPowerNoSignal(value)
        elif param == 'frequency':
            self.setFreqNoSignal(value)
        elif param == 'state':
            self.setStateNoSignal(value)
        
    @inlineCallbacks
    def powerChanged(self, pwr):
        val = self.T.Value(pwr, 'dBm')
        try:
            yield self.server.amplitude(self.chan, val, context = self.context)
        except self.Error as e:
            old_value =  yield self.server.amplitude(self.chan, context = self.context)
            self.setPowerNoSignal(old_value)
            self.displayError(e.msg)
            
    @inlineCallbacks
    def freqChanged(self, freq):
        val = self.T.Value(freq, 'MHz')
        try:
            yield self.server.frequency(self.chan, val, context = self.context)
        except self.Error as e:
            old_value =  yield self.server.frequency(self.chan, context = self.context)
            self.setFreqNoSignal(old_value)
            self.displayError(e.msg)
            
    
    @inlineCallbacks
    def switchChanged(self, pressed):
        try:
            yield self.server.output(self.chan,pressed, context = self.context)
        except self.Error as e:
            old_value =  yield self.server.frequency(self.chan, context = self.context)
            self.setStateNoSignal(old_value)
            self.displayError(e.msg)
    
    def displayError(self, text):
        message = QtGui.QMessageBox()
        message.setText(text)
        message.exec_()

    def closeEvent(self, x):
        self.reactor.stop()

class DDS_CONTROL(QtGui.QFrame):
    
    SIGNALID = 319182
    
    def __init__(self, reactor, cxn = None):
        super(DDS_CONTROL, self).__init__()
        self.setFrameStyle(QtGui.QFrame.Panel  | QtGui.QFrame.Sunken)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor
        self.cxn = cxn
        self.channels = dds_control_config.channels
        self.widgets_per_row = dds_control_config.widgets_per_row
        self.widgets = {}.fromkeys(self.channels)
        self.initialized = False
        self.setupDDS()
       
        
    @inlineCallbacks
    def setupDDS(self):
        if self.cxn is None:
            self.cxn = connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()
        try:
            yield self.initialize()
        except Exception, e:
            print 'DDS CONTROL: Pulser not available'
            self.setDisabled(True)
        self.cxn.on_connect['Pulser'].append( self.reinitialize)
        self.cxn.on_disconnect['Pulser'].append( self.disable)
     
    @inlineCallbacks
    def initialize(self):
        server = self.cxn.servers['Pulser']
        yield server.signal__new_dds_parameter(self.SIGNALID, context = self.context)
        yield server.addListener(listener = self.followSignal, source = None, ID = self.SIGNALID, context = self.context)
        yield self.do_layout(server)
        self.initialized = True
    
    @inlineCallbacks
    def reinitialize(self):
        self.setDisabled(False)
        server = self.cxn.servers['Pulser']
        if not self.initialized:
            yield server.signal__new_dds_parameter(self.SIGNALID, context = self.context)
            yield server.addListener(listener = self.followSignal, source = None, ID = self.SIGNALID, context = self.context)
            yield self.do_layout(server)
            self.initialized = True
        else:
            #update any changes in the parameters
            yield server.signal__new_dds_parameter(self.SIGNALID, context = self.context)
            for w in self.widgets.values():
                yield w.setupWidget(connect = False)
    
    @inlineCallbacks
    def do_layout(self, server):
        allChannels = yield server.get_dds_channels(context = self.context)
        layout = QtGui.QGridLayout()
        item = 0
        for chan in self.channels:
            if chan in allChannels:
                widget = DDS_CHAN(chan, self.reactor, self.cxn, self.context)
                self.widgets[chan] = widget
                layout.addWidget(widget, item // self.widgets_per_row, item % self.widgets_per_row)
                item += 1
        self.setLayout(layout)
        
    
    @inlineCallbacks
    def disable(self):
        self.setDisabled(True)
        yield None
    
    def followSignal(self, x, y):
        chan, param, val = y
        w = self.widgets[chan]
        w.setParamNoSignal(param, val)

    def closeEvent(self, x):
        self.reactor.stop()
        
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    trapdriveWidget = DDS_CONTROL(reactor)
    trapdriveWidget.show()
    reactor.run()
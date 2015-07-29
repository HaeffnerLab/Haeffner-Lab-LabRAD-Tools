from qtui.QCustomFreqPower import QCustomFreqPower
from twisted.internet.defer import inlineCallbacks, returnValue
from connection import connection
from PyQt4 import QtGui

'''
User control for the CW dds boards.
'''
class DDS_CHAN(QCustomFreqPower):
    def __init__(self, chan, step_size, reactor, cxn, context, parent=None):
        super(DDS_CHAN, self).__init__('DDS: {}'.format(chan), True, parent, step_size)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor
        self.context = context
        self.chan = chan
        self.cxn = cxn
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
        self.server = yield self.cxn.get_server('DDS_CW')
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

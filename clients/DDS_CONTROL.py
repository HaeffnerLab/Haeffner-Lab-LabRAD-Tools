from qtui.QCustomFreqPower import QCustomFreqPower
from twisted.internet.defer import inlineCallbacks, returnValue
from connection import connection
from PyQt4 import QtGui

'''
The DDS Control GUI lets the user control the DDS channels of the Pulser
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
        self.server = yield self.cxn.get_server('Pulser')
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
        #runs the message box in a non-blocking method
        message = QtGui.QMessageBox(self)
        message.setText(text)
        message.open()
        message.show()
        message.raise_()

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
        self.initialized = False
        self.setupDDS()
       
    @inlineCallbacks
    def setupDDS(self):
        if self.cxn is None:
            self.cxn = connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()
        try:
            from labrad.types import Error
            self.Error = Error
            yield self.initialize()
        except Exception, e:
            print e
            print 'DDS CONTROL: Pulser not available'
            self.setDisabled(True)
        self.cxn.add_on_connect('Pulser', self.reinitialize)
        self.cxn.add_on_disconnect('Pulser', self.disable)
     
    @inlineCallbacks
    def initialize(self):
        server = yield self.cxn.get_server('Pulser')
        yield server.signal__new_dds_parameter(self.SIGNALID, context = self.context)
        yield server.addListener(listener = self.followSignal, source = None, ID = self.SIGNALID, context = self.context)
        self.display_channels, self.step_sizes, self.widgets_per_row = yield self.get_displayed_channels()
        self.widgets = {}.fromkeys(self.display_channels)
        self.do_layout()
        self.initialized = True
    
    @inlineCallbacks
    def get_displayed_channels(self):
        '''
        get a list of all available channels from the pulser. only show the ones
        listed in the registry. If there is no listing, will display all channels.
        '''
        server = yield self.cxn.get_server('Pulser')
        
        all_channels = yield server.get_dds_channels(context = self.context)
        
        channels_to_display, widgets_per_row = yield self.registry_load_displayed(all_channels, 1)
        
        step_sizes = yield self.registry_load_step_sizes(channels_to_display)
        if channels_to_display is None:
            channels_to_display = all_channels
        if widgets_per_row is None:
            widgets_per_row = 1
        channels = [name for name in channels_to_display if name in all_channels]
        returnValue((channels, step_sizes, widgets_per_row))
     
    @inlineCallbacks
    def registry_load_displayed(self, all_names, default_widgets_per_row):
        reg = yield self.cxn.get_server('Registry')
        yield reg.cd(['','Clients','DDS Control'], True, context = self.context)
        try:
            displayed = yield reg.get('display_channels', context = self.context)
        except self.Error as e:
            yield reg.set('display_channels', all_names, context = self.context)
            displayed = None

        try:
            widgets_per_row = yield reg.get('widgets_per_row', context = self.context)
        except self.Error as e:
            yield reg.set('widgets_per_row', 1, context = self.context)
            widgets_per_row = None
        returnValue((displayed, widgets_per_row))

    @inlineCallbacks
    def registry_load_step_sizes(self, channels_to_display):
        reg = yield self.cxn.get_server('Registry')
        #yield reg.cd(['Clients', 'DDS Control'], True, context = self.context)
        step_sizes = []
        for channel in channels_to_display:
            try:
                step_size = yield reg.get(channel, context = self.context)
                step_sizes.append(step_size)
            except self.Error as e:
                #print e
                #if e.code == 21:
                 #   step_sizes.append(0.1) # default step size
                #else:
                    #raise
                step_sizes.append(0.1)
        returnValue(step_sizes)

    @inlineCallbacks
    def reinitialize(self):
        self.setDisabled(False)
        server = yield self.cxn.get_server('Pulser')
        if not self.initialized:
            yield server.signal__new_dds_parameter(self.SIGNALID, context = self.context)
            yield server.addListener(listener = self.followSignal, source = None, ID = self.SIGNALID, context = self.context)
            self.do_layout()
            self.initialized = True
        else:
            #update any changes in the parameters
            yield server.signal__new_dds_parameter(self.SIGNALID, context = self.context)
            #iterating over all setup channels
            for widget in self.widgets.values():
                if widget is not None:
                    yield widget.setupWidget(connect = False)
    
    def do_layout(self):
        layout = QtGui.QGridLayout()
        item = 0
        for chan, step_size in zip(self.display_channels, self.step_sizes):
            print step_size
            widget = DDS_CHAN(chan, step_size, self.reactor, self.cxn, self.context)
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
        if chan in self.widgets.keys():
            #this check is neeed in case signal comes in about a channel that is not displayed
            self.widgets[chan].setParamNoSignal(param, val)

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
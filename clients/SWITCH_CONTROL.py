from PyQt4 import QtGui
from twisted.internet.defer import inlineCallbacks, returnValue
from connection import connection

'''
The Switch Control GUI lets the user control the TTL channels of the Pulser

Version 1.0
'''

SIGNALID = 378902

class switchWidget(QtGui.QFrame):
    def __init__(self, reactor, cxn = None, parent=None):
        super(switchWidget, self).__init__(parent)
        self.initialized = False
        self.reactor = reactor
        self.cxn = cxn
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        if self.cxn is  None:
            self.cxn = connection()
            yield self.cxn.connect()
            from labrad.types import Error
            self.Error = Error
        self.context = yield self.cxn.context()
        try:
            displayed_channels = yield self.get_displayed_channels()
            yield self.initializeGUI(displayed_channels)
            yield self.setupListeners()
        except Exception, e:
            print e
            print 'SWTICH CONTROL: Pulser not available'
            self.setDisabled(True)
        self.cxn.add_on_connect('Pulser', self.reinitialize)
        self.cxn.add_on_disconnect('Pulser', self.disable)
    
    @inlineCallbacks
    def get_displayed_channels(self):
        '''
        get a list of all available channels from the pulser. only show the ones
        listed in the registry. If there is no listing, will display all channels.
        '''
        server = yield self.cxn.get_server('Pulser')
        all_channels = yield server.get_channels(context = self.context)
        all_names = [el[0] for el in all_channels]
        channels_to_display = yield self.registry_load_displayed(all_names)
        if channels_to_display is None:
            channels_to_display = all_names
        channels = [name for name in channels_to_display if name in all_names]
        returnValue(channels)
    
    @inlineCallbacks
    def registry_load_displayed(self, all_names):
        reg = yield self.cxn.get_server('Registry')
        yield reg.cd(['Clients','Switch Control'], True, context = self.context)
        try:
            displayed = yield reg.get('display_channels', context = self.context)
        except self.Error as e:
            if e.code == 21:
                #key error
                yield reg.set('display_channels', all_names, context = self.context)
                displayed = None
            else:
                raise
        returnValue(displayed)
    
    @inlineCallbacks
    def reinitialize(self):
        self.setDisabled(False)
        server = yield self.cxn.get_server('Pulser')
        if self.initialized:
            yield server.signal__switch_toggled(SIGNALID, context = self.context)
            for name in self.d.keys():
                self.setStateNoSignals(name, server)
        else:
            yield self.initializeGUI()
            yield self.setupListeners()
    
    @inlineCallbacks
    def initializeGUI(self, channels):
        '''
        Lays out the GUI
        
        @var channels: a list of channels to be displayed.
        '''
        server = yield self.cxn.get_server('Pulser')
        self.d = {}
        #set layout
        layout = QtGui.QGridLayout()
        self.setFrameStyle(QtGui.QFrame.Panel  | QtGui.QFrame.Sunken)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        #get switch names and add them to the layout, and connect their function
        layout.addWidget(QtGui.QLabel('Switches'),0,0)
        for order,name in enumerate(channels):
            #setting up physical container
            groupBox = QtGui.QGroupBox(name) 
            groupBoxLayout = QtGui.QVBoxLayout()
            buttonOn = QtGui.QPushButton('ON')
            buttonOn.setAutoExclusive(True)
            buttonOn.setCheckable(True)
            buttonOff = QtGui.QPushButton('OFF')
            buttonOff.setCheckable(True)
            buttonOff.setAutoExclusive(True)
            buttonAuto = QtGui.QPushButton('Auto')
            buttonAuto.setCheckable(True)
            buttonAuto.setAutoExclusive(True)
            groupBoxLayout.addWidget(buttonOn)
            groupBoxLayout.addWidget(buttonOff)
            groupBoxLayout.addWidget(buttonAuto)
            groupBox.setLayout(groupBoxLayout)
            #adding to dictionary for signal following
            self.d[name] = {}
            self.d[name]['ON'] = buttonOn
            self.d[name]['OFF'] = buttonOff
            self.d[name]['AUTO'] = buttonAuto
            #setting initial state
            yield self.setStateNoSignals(name, server)                   
            buttonOn.clicked.connect(self.buttonConnectionManualOn(name, server))
            buttonOff.clicked.connect(self.buttonConnectionManualOff(name, server))
            buttonAuto.clicked.connect(self.buttonConnectionAuto(name, server))
            layout.addWidget(groupBox,0,1 + order)
        self.setLayout(layout)
        self.initialized = True
    
    @inlineCallbacks
    def setStateNoSignals(self, name, server):
        initstate = yield server.get_state(name, context = self.context)
        ismanual = initstate[0]
        manstate = initstate[1]
        if not ismanual:
            self.d[name]['AUTO'].blockSignals(True)
            self.d[name]['AUTO'].setChecked(True)
            self.d[name]['AUTO'].blockSignals(False)
        else:
            if manstate:
                self.d[name]['ON'].blockSignals(True)
                self.d[name]['ON'].setChecked(True)
                self.d[name]['ON'].blockSignals(False)
            else:
                self.d[name]['OFF'].blockSignals(True)
                self.d[name]['OFF'].setChecked(True)
                self.d[name]['OFF'].blockSignals(False)
    
    def buttonConnectionManualOn(self, name, server):
        @inlineCallbacks
        def func(state):
            yield server.switch_manual(name, True, context = self.context)
        return func
    
    def buttonConnectionManualOff(self, name, server):
        @inlineCallbacks
        def func(state):
            yield server.switch_manual(name, False, context = self.context)
        return func
    
    def buttonConnectionAuto(self, name, server):
        @inlineCallbacks
        def func(state):
            yield server.switch_auto(name, context = self.context)
        return func
    
    @inlineCallbacks
    def setupListeners(self):
        server = yield self.cxn.get_server('Pulser')
        yield server.signal__switch_toggled(SIGNALID, context = self.context)
        yield server.addListener(listener = self.followSignal, source = None, ID = SIGNALID, context = self.context)
    
    def followSignal(self, x, (switchName, state)):
        if switchName not in self.d.keys(): return None
        if state == 'Auto':
            button = self.d[switchName]['AUTO']
        elif state == 'ManualOn':
            button = self.d[switchName]['ON']
        elif state == 'ManualOff':
            button = self.d[switchName]['OFF']
        button.setChecked(True)

    def closeEvent(self, x):
        self.reactor.stop()
    
    @inlineCallbacks
    def disable(self):
        self.setDisabled(True)
        yield None
            
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    triggerWidget = switchWidget(reactor)
    triggerWidget.show()
    reactor.run()
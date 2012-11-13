from PyQt4 import QtGui
from twisted.internet.defer import inlineCallbacks
from SWITCH_CONTROL_config import switch_control_config
from connection import connection

SIGNALID = 378902

class switchWidget(QtGui.QFrame):
    def __init__(self, reactor, cxn = None, parent=None):
        super(switchWidget, self).__init__(parent)
        self.initialized = False
        self.channels = switch_control_config.channels
        self.reactor = reactor
        self.cxn = cxn
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        if self.cxn is  None:
            self.cxn = connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()
        try:
            yield self.initializeGUI()
            yield self.setupListeners()
        except Exception, e:
            print 'SWTICH CONTROL: Pulser not available'
            self.setDisabled(True)
        self.cxn.on_connect['Pulser'].append( self.reinitialize)
        self.cxn.on_disconnect['Pulser'].append( self.disable)
    
    @inlineCallbacks
    def reinitialize(self):
        self.setDisabled(False)
        server = self.cxn.servers['Pulser']
        if self.initialized:
            yield server.signal__switch_toggled(SIGNALID, context = self.context)
            for name in self.d.keys():
                self.setStateNoSignals(name, server)
        else:
            yield self.initializeGUI()
            yield self.setupListeners()
    
    @inlineCallbacks
    def initializeGUI(self):
        server = self.cxn.servers['Pulser']
        self.d = {}
        #set layout
        layout = QtGui.QGridLayout()
        self.setFrameStyle(QtGui.QFrame.Panel  | QtGui.QFrame.Sunken)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        #get switch names and add them to the layout, and connect their function
        layout.addWidget(QtGui.QLabel('Switches'),0,0)
        switchNames = yield server.get_channels(context = self.context)
        switchNames = [el[0] for el in switchNames] #picking first of the tuple
        channels = [name for name in self.channels if name in switchNames]
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
        server = self.cxn.servers['Pulser']
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
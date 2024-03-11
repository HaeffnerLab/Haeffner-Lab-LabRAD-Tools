from PyQt5 import QtCore, QtGui, QtWidgets
from twisted.internet.defer import inlineCallbacks
#from connection import connection

SIGNALID = 378903

class TextChangingButton(QtWidgets.QPushButton):
    """Button that changes its text to ON or OFF and colors when it's pressed""" 
    def __init__(self, parent = None):
        super(TextChangingButton, self).__init__(parent)
        self.setCheckable(True)
        self.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=10))
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        #connect signal for appearance changing
        self.toggled.connect(self.setAppearance)
        self.setAppearance(self.isDown())
    
    def set_value_no_signal(self, down):
        self.blockSignals(True)
        self.setChecked(down)
        self.setAppearance(down)
        self.blockSignals(False)
    
    def setAppearance(self, down):
        if down:
            self.setText('I')
            self.setPalette(QtGui.QPalette(QtCore.Qt.darkGreen))
        else:
            self.setText('O')
            self.setPalette(QtGui.QPalette(QtCore.Qt.black))
    
    def sizeHint(self):
        return QtCore.QSize(37, 26)

class linetriggerWidget(QtWidgets.QFrame):
    def __init__(self, reactor, cxn = None, parent=None):
        super(linetriggerWidget, self).__init__(parent)
        self.initialized = False
        self.reactor = reactor
        self.cxn = cxn
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        if self.cxn is  None:
            self.cxn = connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()
        print(self.context)
        from labrad.units import WithUnit
        self.WithUnit = WithUnit
        try:
            yield self.initializeGUI()
            yield self.setupListeners()
        except Exception as e:
            print(e)
            print('linetriggerWidget: Pulser not available')
            self.setDisabled(True)
        yield self.cxn.add_on_connect('Pulser',self.reinitialize)
        yield self.cxn.add_on_disconnect('Pulser',self.reinitialize)
    
    @inlineCallbacks
    def reinitialize(self):
        self.setDisabled(False)
        server = yield self.cxn.get_server('Pulser')
        if self.initialized:
            yield server.signal__new_line_trigger_parameter(SIGNALID, context = self.context)
            state = yield server.line_trigger_state(context = self.context)
            duration = yield server.line_trigger_duration(context = self.context)
            self.followSignal(None, (state, duration))
        else:
            yield self.initializeGUI()
            yield self.setupListeners()
    
    @inlineCallbacks
    def initializeGUI(self):
        server = yield self.cxn.get_server('Pulser')
        #set layout
        layout = QtWidgets.QGridLayout()
        self.setFrameStyle(QtWidgets.QFrame.Panel  | QtWidgets.QFrame.Sunken)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        #get initial parameters and use them to create the layout
        #button
        self.button_linetrig = TextChangingButton()
        self.button_linetrig.setCheckable(True)
        self.button_linetrig.setStyleSheet("QPushButton { background-color: gray }"
                                           "QPushButton:On { background-color: green}")
        state = yield server.line_trigger_state(context = self.context)
        self.button_linetrig.setChecked(state)
        self.button_linetrig.toggled.connect(self.setState)
        #duration
        self.spinbox = QtWidgets.QSpinBox()
        self.spinbox.setKeyboardTracking(False)
        self.spinbox.setSuffix(' us')
        duration = yield server.line_trigger_duration(context = self.context)
        limits = yield server.get_line_trigger_limits()
        limits = [l['us'] for l in limits]
        self.spinbox.setRange(int(limits[0]), int(limits[1]))
        self.spinbox.setValue(int(duration['us']))
        self.spinbox.valueChanged.connect(self.setDuration)
        #putton for dds Reset
        button_reset_dds = QtWidgets.QPushButton()
        button_reset_dds.pressed.connect(self.resetDDS)
        label = QtWidgets.QLabel("Line Triggering")
        layout.addWidget(label, 0, 0)
        layout.addWidget(self.button_linetrig, 0, 1)
        label = QtWidgets.QLabel("Offset Duration (broken)")
        layout.addWidget(label, 1, 0)
        layout.addWidget(self.spinbox, 1, 1)
        label = QtWidgets.QLabel("Clear DDS Lock")
        layout.addWidget(label, 2, 0)
        layout.addWidget(button_reset_dds, 2, 1)
        self.setLayout(layout)
        self.initialized = True
    
    @inlineCallbacks
    def resetDDS(self):
        server = yield self.cxn.get_server('Pulser')
        yield server.clear_dds_lock(context = self.context)
        
    @inlineCallbacks
    def setDuration(self, duration):
        duration = self.WithUnit(duration, 'us')
        server = self.cxn.get_server('Pulser')
        yield server.line_trigger_duration(duration, context = self.context)
    
    @inlineCallbacks
    def setState(self, state):
        server = yield self.cxn.get_server('Pulser')
        print(server)
        yield server.line_trigger_state(state, context = self.context)
    
    @inlineCallbacks
    def setupListeners(self):
        server = yield self.cxn.get_server('Pulser')
        yield server.signal__new_line_trigger_parameter(SIGNALID, context = self.context)
        yield server.addListener(listener = self.followSignal, source = None, ID = SIGNALID, context = self.context)
    
    def followSignal(self, x, ins):
        state = ins[0]
        duration = ins[1]
        self.spinbox.blockSignals(True)
        self.button_linetrig.set_value_no_signal(state)
        self.spinbox.setValue(duration)
        self.spinbox.blockSignals(False)

    def closeEvent(self, x):
        self.reactor.stop()
    
    @inlineCallbacks
    def disable(self):
        self.setDisabled(True)
        yield None
            
if __name__=="__main__":
    a = QtWidgets.QApplication( [] )
    import qt5reactor
    qt5reactor.install()
    from connection import connection
    from twisted.internet import reactor
    triggerWidget = linetriggerWidget(reactor)
    triggerWidget.show()
    reactor.run()

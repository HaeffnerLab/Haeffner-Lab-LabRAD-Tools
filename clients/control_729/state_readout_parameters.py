from PyQt4 import QtGui, QtCore
from configuration import state_readout as c
from async_semaphore import async_semaphore, Parameter

class general_state_readout(QtGui.QWidget):
    def __init__(self, reactor, cxn = None, parent = None):
        super(general_state_readout, self).__init__(parent)
        self.reactor = reactor
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.initializeGUI()
    
    def initializeGUI(self):
        layout = QtGui.QGridLayout()
        font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        #threshold and readout
        self.threshold = QtGui.QSpinBox()
        self.threshold.setKeyboardTracking(False)
        self.threshold.setFont(font)
        self.readout_time = QtGui.QDoubleSpinBox()
        self.readout_time.setKeyboardTracking(False)
        self.readout_time.setFont(font)
        self.readout_time.setSuffix('ms')
        self.readout_time.setDecimals(1)
        self.readout_time.setSingleStep(0.1)
        #repeats
        self.repeats = QtGui.QSpinBox()
        self.repeats.setKeyboardTracking(False)
        self.repeats.setFont(font)
        label = QtGui.QLabel("Repeat Each Point")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)      
        layout.addWidget(label, 1, 0, 1, 1)
        layout.addWidget(self.repeats, 1, 1, 1, 1)
        #amplitudes
        self.state_readout_amplitude_397 = QtGui.QDoubleSpinBox()
        self.state_readout_amplitude_866 = QtGui.QDoubleSpinBox()
        for w in [self.state_readout_amplitude_866, self.state_readout_amplitude_397]:
            w.setFont(font)
            w.setSuffix('dBm')
            w.setDecimals(1)
            w.setSingleStep(0.1)
            w.setKeyboardTracking(False)
        #frequency
        self.state_readout_frequency_397 = QtGui.QDoubleSpinBox()
        self.state_readout_frequency_866 = QtGui.QDoubleSpinBox()
        for w in [self.state_readout_frequency_397, self.state_readout_frequency_866]:
            w.setFont(font)
            w.setKeyboardTracking(False)
            w.setSuffix('MHz')
            w.setDecimals(1)
        #add threshold and redout labels
        thresholdLabel = QtGui.QLabel("Threshold (Photon Counts Per Readout)")
        readoutTimeLabel = QtGui.QLabel("Readout Time")
        for l in [thresholdLabel, readoutTimeLabel]:
            l.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            l.setFont(font)
        layout.addWidget(thresholdLabel, 0, 0)
        layout.addWidget(self.threshold, 0, 1)
        layout.addWidget(readoutTimeLabel, 0, 2)
        layout.addWidget(self.readout_time, 0, 3)
        #add to layout
        label = QtGui.QLabel("Readout Frequency 397")
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        label.setFont(font)
        layout.addWidget(label, 2, 0, 1, 1)
        layout.addWidget(self.state_readout_frequency_397, 2, 1, 1, 1)
        label = QtGui.QLabel("Readout Amplitude 397")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 2, 2, 1, 1)
        layout.addWidget(self.state_readout_amplitude_397, 2, 3, 1, 1)
        label = QtGui.QLabel("Readout Frequency 866")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 3, 0, 1, 1)
        layout.addWidget(self.state_readout_frequency_866, 3, 1, 1, 1)
        label = QtGui.QLabel("Readout Amplitude 866")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 3, 2, 1, 1)
        layout.addWidget(self.state_readout_amplitude_866, 3, 3, 1, 1)
        self.setLayout(layout)
    
    def closeEvent(self, x):
        self.reactor.stop()

class general_parameters_connection(general_state_readout, async_semaphore):
    
    def __init__(self, reactor, cxn = None, parent = None):
        super(general_parameters_connection, self).__init__(reactor)
        self.subscribed = False
        self.cxn = cxn
        self.createDict()
        self.semaphoreID = c.ID
        self.connect_labrad()
        
    def createDict(self):
        '''dictionary for tracking relevant setters and getters for all the parameters coming in from semaphore'''
        def setValueBlocking(w):
            def func(val):
                w.blockSignals(True)
                w.setValue(val)
                w.blockSignals(False)
            return func
        
        def do_nothing(*args):
            pass
        
        self.d = {
                #spin boxes
                tuple(c.state_readout_frequency_397): Parameter(c.state_readout_frequency_397, setValueBlocking(self.state_readout_frequency_397), self.state_readout_frequency_397.valueChanged, self.state_readout_frequency_397.setRange, 'MHz'),
                tuple(c.state_readout_amplitude_397): Parameter(c.state_readout_amplitude_397, setValueBlocking(self.state_readout_amplitude_397), self.state_readout_amplitude_397.valueChanged, self.state_readout_amplitude_397.setRange, 'dBm'),
                tuple(c.state_readout_frequency_866): Parameter(c.state_readout_frequency_866, setValueBlocking(self.state_readout_frequency_866), self.state_readout_frequency_866.valueChanged, self.state_readout_frequency_866.setRange, 'MHz'),
                tuple(c.state_readout_amplitude_866): Parameter(c.state_readout_amplitude_866, setValueBlocking(self.state_readout_amplitude_866), self.state_readout_amplitude_866.valueChanged, self.state_readout_amplitude_866.setRange, 'dBm'),
                tuple(c.readout_time_dir): Parameter(c.readout_time_dir, setValueBlocking(self.readout_time), self.readout_time.valueChanged, self.readout_time.setRange, 'ms'),
                #int
                tuple(c.repeat_each_measurement): Parameter(c.repeat_each_measurement, setValueBlocking(self.repeats), self.repeats.valueChanged, self.repeats.setRange, None),
                tuple(c.readout_threshold_dir): Parameter(c.readout_threshold_dir, setValueBlocking(self.threshold), self.threshold.valueChanged, self.threshold.setRange, None),
                
               }

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = general_parameters_connection(reactor)
    widget.show()
    reactor.run()
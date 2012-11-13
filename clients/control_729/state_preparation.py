from PyQt4 import QtGui, QtCore
from configuration import config_729_state_preparation as c
from async_semaphore import async_semaphore, Parameter
from helper_widgets import frequency_wth_dropdown

class optical_pumping_frame(QtGui.QFrame):
    def __init__(self, reactor, title, font, large_font):
        super(optical_pumping_frame, self).__init__()
        self.reactor = reactor
        self.setFrameStyle(QtGui.QFrame.Panel  | QtGui.QFrame.Sunken)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.initializeGUI(title, font, large_font)
    
    def initializeGUI(self, title, font, large_font):
        layout = QtGui.QGridLayout()
        #make title
        title_label = QtGui.QLabel(title, font = large_font)
        title_label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        layout.addWidget(title_label, 0, 0, 1, 2)
        #enable button
        label = QtGui.QLabel('Enable', font = font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 0, 2)
        self.enable = QtGui.QCheckBox()
        layout.addWidget(self.enable, 0, 3)
        #exculsive check boxes
        self.continous = QtGui.QRadioButton()
        self.pulsed = QtGui.QRadioButton()
        bg = QtGui.QButtonGroup()
        #make them exclusive
        bg.addButton(self.continous)
        bg.addButton(self.pulsed)
        label = QtGui.QLabel('Continous', font = font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 4, 0)
        layout.addWidget(self.continous, 4, 1)
        label = QtGui.QLabel('Pulsed', font = font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 4, 2)
        layout.addWidget(self.pulsed, 4, 3)
        bg.setExclusive(True)
        #frequencies and amplitudes
        self.freq729 = frequency_wth_dropdown(self.reactor, parameter_name = 'Frequency 729', suffix = 'MHz', sig_figs = 4, font = font)
        self.freq854 = QtGui.QDoubleSpinBox()
        self.freq866 = QtGui.QDoubleSpinBox()
        self.ampl729 = QtGui.QDoubleSpinBox()
        self.ampl854 = QtGui.QDoubleSpinBox()
        self.ampl866 = QtGui.QDoubleSpinBox()
        for w in [self.freq854, self.freq866]:
            w.setFont(font)
            w.setKeyboardTracking(False)
            w.setSuffix('MHz')
            w.setDecimals(1)
            w.setFont(font)
        for w in [self.ampl729, self.ampl854, self.ampl866]:
            w.setSuffix('dBm')
            w.setDecimals(1)
            w.setSingleStep(0.1)
            w.setKeyboardTracking(False)
            w.setFont(font)
        layout.addWidget(self.freq729, 1, 1, 1, 1)
        label = QtGui.QLabel("Amplitude 729")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 1, 2, 1, 1)
        layout.addWidget(self.ampl729, 1, 3, 1, 1)
        label = QtGui.QLabel("Frequency 854")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 2, 0, 1, 1)
        layout.addWidget(self.freq854, 2, 1, 1, 1)
        label = QtGui.QLabel("Amplitude 854")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 2, 2, 1, 1)
        layout.addWidget(self.ampl854, 2, 3, 1, 1)
        label = QtGui.QLabel("Frequency 866")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 3, 0, 1, 1)
        layout.addWidget(self.freq866, 3, 1, 1, 1)
        label = QtGui.QLabel("Amplitude 866")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 3, 2, 1, 1)
        layout.addWidget(self.ampl866, 3, 3, 1, 1)
        #durations
        self.continous_duration = QtGui.QDoubleSpinBox()
        self.repump_additional = QtGui.QDoubleSpinBox()
        self.between_pulses = QtGui.QDoubleSpinBox()
        for w in [self.continous_duration, self.repump_additional, self.between_pulses]:
            w.setKeyboardTracking(False)
            w.setSuffix('us')
            w.setDecimals(1)
            w.setSingleStep(0.1)
            w.setFont(font)
        self.pulses = QtGui.QSpinBox()
        self.pulses.setKeyboardTracking(False)
        self.pulses.setFont(font)
        self.pulse_729 = QtGui.QDoubleSpinBox()
        self.pulse_repumps = QtGui.QDoubleSpinBox()
        self.pulse_866_additional = QtGui.QDoubleSpinBox()
        for w in [self.pulse_729, self.pulse_repumps, self.pulse_866_additional]:
            w.setSuffix('\265s')
            w.setDecimals(1)
            w.setSingleStep(0.1)
            w.setKeyboardTracking(False)
            w.setFont(font)
        label =  QtGui.QLabel("Duration")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 5, 0, 1, 1)
        layout.addWidget(self.continous_duration, 5, 1, 1, 1)
        label =  QtGui.QLabel("Additional Repump")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 6, 0, 1, 1)
        layout.addWidget(self.repump_additional, 6, 1, 1, 1)
        label =  QtGui.QLabel("Cycles")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 5, 2, 1, 1)
        layout.addWidget(self.pulses, 5, 3, 1, 1)
        label =  QtGui.QLabel("Pulse 729")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 6, 2, 1, 1)
        layout.addWidget(self.pulse_729, 6, 3, 1, 1)
        label =  QtGui.QLabel("Pulse Repumps")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 7, 2, 1, 1)
        layout.addWidget(self.pulse_repumps, 7, 3, 1, 1)
        label =  QtGui.QLabel("Additional 866")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 8, 2, 1, 1)
        layout.addWidget(self.pulse_866_additional, 8, 3, 1, 1)
        label =  QtGui.QLabel("Between Pulses")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 9, 2, 1, 1)
        layout.addWidget(self.between_pulses, 9, 3, 1, 1)
        self.setLayout(layout)
    
    def closeEvent(self, x):
        self.reactor.stop()
        

class state_preparation(QtGui.QWidget):
    def __init__(self, reactor, cxn = None, parent = None):
        super(state_preparation, self).__init__(parent)
        self.reactor = reactor
        self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.large_font = QtGui.QFont('MS Shell Dlg 2',pointSize=14)
        self.initializeGUI()
    
    def initializeGUI(self):
        repump_d_frame = self.make_repump_d_frame()
        heating_frame = self.make_heating_frame()
        doppler_cooling_frame = self.make_doppler_cooling_frame()
        self.optical_pumping_frame = self.make_optical_pumping_frame()
#        sideband_cooling_frame = self.make_sideband_cooling_frame()
        widgetLayout = QtGui.QVBoxLayout()
        widgetLayout.addWidget(repump_d_frame)
        widgetLayout.addWidget(doppler_cooling_frame)
        widgetLayout.addWidget(self.optical_pumping_frame)
#        widgetLayout.addWidget(sideband_cooling_frame)
        widgetLayout.addWidget(heating_frame)
        self.setLayout(widgetLayout)
    
    def make_optical_pumping_frame(self):
        frame = optical_pumping_frame(self.reactor, 'Optical Pumping', self.font, self.large_font)
        return frame
    
#    def make_sideband_cooling_frame(self):
#        frame = optical_pumping_frame('Sideband Cooling', self.font, self.large_font)
#        return frame
    
    def make_doppler_cooling_frame(self):
        frame = QtGui.QFrame()
        frame.setFrameStyle(QtGui.QFrame.Panel  | QtGui.QFrame.Sunken)
        frame.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        layout = QtGui.QGridLayout()
        self.doppler_duration = QtGui.QDoubleSpinBox()
        self.doppler_duration.setSuffix('ms')
        self.doppler_duration_additional = QtGui.QDoubleSpinBox()
        for w in [self.doppler_duration, self.doppler_duration_additional]:
            w.setKeyboardTracking(False)
            w.setFont(self.font)
            w.setDecimals(1)
        self.doppler_duration_additional.setSuffix('\265s')
        self.doppler_amplitude_397 = QtGui.QDoubleSpinBox()
        self.doppler_amplitude_866 = QtGui.QDoubleSpinBox()
        self.doppler_frequency_866 = QtGui.QDoubleSpinBox()
        self.doppler_frequency_397 = QtGui.QDoubleSpinBox()
        for w in [self.doppler_amplitude_866, self.doppler_amplitude_397]:
            w.setSuffix('dBm')
            w.setDecimals(1)
            w.setSingleStep(0.1)
            w.setKeyboardTracking(False)
            w.setFont(self.font)
        for w in [self.doppler_frequency_397, self.doppler_frequency_866]:
            w.setKeyboardTracking(False)
            w.setSuffix('MHz')
            w.setDecimals(1)
            w.setFont(self.font)
        label = QtGui.QLabel("Doppler Cooling", font = self.large_font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)      
        layout.addWidget(label, 0, 0, 1, 2)
        label = QtGui.QLabel("Duration", font = self.font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 0, 2)
        layout.addWidget(self.doppler_duration, 0, 3)
        label = QtGui.QLabel("Frequency 397", font = self.font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 1, 0)
        layout.addWidget(self.doppler_frequency_397, 1, 1)
        label = QtGui.QLabel("Amplitude 397", font = self.font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 1, 2)
        layout.addWidget(self.doppler_amplitude_397, 1, 3)
        label = QtGui.QLabel("Frequency 866", font = self.font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 2, 0)
        layout.addWidget(self.doppler_frequency_866, 2, 1)
        label = QtGui.QLabel("Amplitude 866", font = self.font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 2, 2)
        layout.addWidget(self.doppler_amplitude_866, 2, 3)
        label = QtGui.QLabel("Extended 866 Repump", font = self.font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 3, 2)
        layout.addWidget(self.doppler_duration_additional, 3, 3)
        frame.setLayout(layout)
        return frame
        
    def make_heating_frame(self):
        frame = QtGui.QFrame()
        frame.setFrameStyle(QtGui.QFrame.Panel  | QtGui.QFrame.Sunken)
        frame.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        layout = QtGui.QGridLayout()
        self.heating = QtGui.QDoubleSpinBox()
        self.heating.setKeyboardTracking(False)
        self.heating.setSuffix('ms')
        self.heating.setFont(self.font)
        label = QtGui.QLabel("Background Heating", font = self.large_font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)      
        layout.addWidget(label, 0, 0, 1, 2)
        label = QtGui.QLabel("Duration", font = self.font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 0, 2)
        layout.addWidget(self.heating, 0, 3)
        frame.setLayout(layout)
        return frame
    
    def make_repump_d_frame(self):
        #repump D
        self.repump_d_duration = QtGui.QDoubleSpinBox()
        self.repump_d_duration.setSuffix('\265s')
        self.repump_d_duration.setKeyboardTracking(False)
        self.repump_d_duration.setFont(self.font)
        self.repump_d_duration.setDecimals(1)
        #amplitudes
        self.ampl_854 = QtGui.QDoubleSpinBox()
        self.freq_854 = QtGui.QDoubleSpinBox()
        for w in [self.ampl_854]:
            w.setSuffix('dBm')
            w.setDecimals(1)
            w.setSingleStep(0.1)
            w.setKeyboardTracking(False)
            w.setFont(self.font)
        for w in [self.freq_854]:
            w.setKeyboardTracking(False)
            w.setSuffix('MHz')
            w.setDecimals(1)
            w.setFont(self.font)
        #repump d layout
        frame = QtGui.QFrame()
        frame.setFrameStyle(QtGui.QFrame.Panel  | QtGui.QFrame.Sunken)
        frame.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        layout = QtGui.QGridLayout()
        title = QtGui.QLabel("Repump D5/2", font = self.large_font)
        title.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        layout.addWidget(title, 0, 0, 1, 2)
        label = QtGui.QLabel("Amplitude 854", font = self.font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 1, 2)
        layout.addWidget(self.ampl_854, 1, 3)
        label = QtGui.QLabel("Frequency 854", font = self.font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 1, 0)
        layout.addWidget(self.freq_854, 1, 1)
        label = QtGui.QLabel("Duration", font = self.font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 0, 2)
        layout.addWidget(self.repump_d_duration, 0, 3)
        frame.setLayout(layout)
        return frame

    def closeEvent(self, x):
        self.reactor.stop()

class state_preparation_connection(state_preparation, async_semaphore):
    
    def __init__(self, reactor, cxn = None, parent = None):
        super(state_preparation_connection, self).__init__(reactor)
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
        
        def setValueBlocking_cb(w):
            def func(val):
                #dont' have to block checkboxes
                w.setChecked(val)
            return func
        
        def do_nothing(*args):
            pass
        
        class no_signal(object):
            @staticmethod
            def connect(*args):
                pass
        
        self.d = {
                #repump d5/2
                tuple(c.repump_d_duration): Parameter(c.repump_d_duration, setValueBlocking(self.repump_d_duration), self.repump_d_duration.valueChanged, self.repump_d_duration.setRange, 'us'),
                tuple(c.repump_d_amplitude_854): Parameter(c.repump_d_amplitude_854, setValueBlocking(self.ampl_854), self.ampl_854.valueChanged, self.ampl_854.setRange, 'dBm'),
                #doppler cooling
                tuple(c.doppler_cooling_duration):Parameter(c.doppler_cooling_duration, setValueBlocking(self.doppler_duration), self.doppler_duration.valueChanged, self.doppler_duration.setRange, 'ms'),
                tuple(c.doppler_cooling_repump_additional):Parameter(c.doppler_cooling_repump_additional, setValueBlocking(self.doppler_duration_additional), self.doppler_duration_additional.valueChanged, self.doppler_duration_additional.setRange, 'us'),
                tuple(c.doppler_cooling_frequency_397):Parameter(c.doppler_cooling_frequency_397, setValueBlocking(self.doppler_frequency_397), self.doppler_frequency_397.valueChanged, self.doppler_frequency_397.setRange, 'MHz'),
                tuple(c.doppler_cooling_amplitude_397): Parameter(c.doppler_cooling_amplitude_397, setValueBlocking(self.doppler_amplitude_397), self.doppler_amplitude_397.valueChanged, self.doppler_amplitude_397.setRange, 'dBm'),
                tuple(c.doppler_cooling_amplitude_866): Parameter(c.doppler_cooling_amplitude_866, setValueBlocking(self.doppler_amplitude_866), self.doppler_amplitude_866.valueChanged, self.doppler_amplitude_866.setRange, 'dBm'),
                #optical pumping
                tuple(c.optical_pumping_enable):Parameter(c.optical_pumping_enable, setValueBlocking_cb(self.optical_pumping_frame.enable), updateSignal = self.optical_pumping_frame.enable.toggled),                          
                tuple(c.optical_pumping_continuous):Parameter(c.optical_pumping_continuous, setValueBlocking_cb(self.optical_pumping_frame.continous), updateSignal = self.optical_pumping_frame.continous.toggled),
                tuple(c.optical_pumping_pulsed):Parameter(c.optical_pumping_pulsed, setValueBlocking_cb(self.optical_pumping_frame.pulsed), updateSignal = self.optical_pumping_frame.pulsed.toggled),
                tuple(c.optical_pumping_pulsed_cycles):Parameter(c.optical_pumping_pulsed_cycles, setValueBlocking(self.optical_pumping_frame.pulses), self.optical_pumping_frame.pulses.valueChanged, self.optical_pumping_frame.pulses.setRange, None),
                tuple(c.optical_pumping_frequency_729):Parameter(c.optical_pumping_frequency_729, self.optical_pumping_frame.freq729.set_freq_value_no_signals, self.optical_pumping_frame.freq729.valueChanged, self.optical_pumping_frame.freq729.setRange, 'MHz'),
                tuple(c.optical_pumping_amplitude_729): Parameter(c.optical_pumping_amplitude_729, setValueBlocking(self.optical_pumping_frame.ampl729), self.optical_pumping_frame.ampl729.valueChanged, self.optical_pumping_frame.ampl729.setRange, 'dBm'),
                tuple(c.optical_pumping_amplitude_854): Parameter(c.optical_pumping_amplitude_854, setValueBlocking(self.optical_pumping_frame.ampl854), self.optical_pumping_frame.ampl854.valueChanged, self.optical_pumping_frame.ampl854.setRange, 'dBm'),
                tuple(c.optical_pumping_amplitude_866): Parameter(c.optical_pumping_amplitude_866, setValueBlocking(self.optical_pumping_frame.ampl866), self.optical_pumping_frame.ampl866.valueChanged, self.optical_pumping_frame.ampl866.setRange, 'dBm'),
                tuple(c.optical_pumping_continuous_duration):Parameter(c.optical_pumping_continuous_duration, setValueBlocking(self.optical_pumping_frame.continous_duration), self.optical_pumping_frame.continous_duration.valueChanged, self.optical_pumping_frame.continous_duration.setRange, 'us'),
                tuple(c.optical_pumping_continuous_pump_additional):Parameter(c.optical_pumping_continuous_pump_additional, setValueBlocking(self.optical_pumping_frame.repump_additional), self.optical_pumping_frame.repump_additional.valueChanged, self.optical_pumping_frame.repump_additional.setRange, 'us'),
                tuple(c.optical_pumping_pulsed_duration_729):Parameter(c.optical_pumping_pulsed_duration_729, setValueBlocking(self.optical_pumping_frame.pulse_729), self.optical_pumping_frame.pulse_729.valueChanged, self.optical_pumping_frame.pulse_729.setRange, 'us'),
                tuple(c.optical_pumping_pulsed_duration_repumps):Parameter(c.optical_pumping_pulsed_duration_repumps, setValueBlocking(self.optical_pumping_frame.pulse_repumps), self.optical_pumping_frame.pulse_repumps.valueChanged, self.optical_pumping_frame.pulse_repumps.setRange, 'us'),
                tuple(c.optical_pumping_pulsed_duration_additional_866):Parameter(c.optical_pumping_pulsed_duration_additional_866, setValueBlocking(self.optical_pumping_frame.pulse_866_additional), self.optical_pumping_frame.pulse_866_additional.valueChanged, self.optical_pumping_frame.pulse_866_additional.setRange, 'us'), 
                tuple(c.optical_pumping_pulsed_duration_between_pulses):Parameter(c.optical_pumping_pulsed_duration_between_pulses, setValueBlocking(self.optical_pumping_frame.between_pulses), self.optical_pumping_frame.between_pulses.valueChanged, self.optical_pumping_frame.between_pulses.setRange, 'us'), 
                tuple(c.saved_lines_729):Parameter(c.saved_lines_729, self.optical_pumping_frame.freq729.set_dropdown, no_signal, do_nothing, c.line_parameter_units), 
                tuple(c.optical_pumping_use_saved_line):Parameter(c.optical_pumping_use_saved_line, self.optical_pumping_frame.freq729.set_selected, self.optical_pumping_frame.freq729.useSavedLine, do_nothing, None), 
                tuple(c.optical_pumping_use_saved):Parameter(c.optical_pumping_use_saved, self.optical_pumping_frame.freq729.set_use_saved, updateSignal = self.optical_pumping_frame.freq729.useSaved),
                #heating
                tuple(c.background_heating_duration): Parameter(c.background_heating_duration, setValueBlocking(self.heating), self.heating.valueChanged, self.heating.setRange, 'ms'),
                #multiple keys connected to same widgets
                tuple(c.optical_pumping_frequency_854):[
                                                        Parameter(c.optical_pumping_frequency_854, setValueBlocking(self.optical_pumping_frame.freq854), self.optical_pumping_frame.freq854.valueChanged, self.optical_pumping_frame.freq854.setRange, 'MHz'),
                                                        Parameter(c.repump_d_frequency_854, setValueBlocking(self.freq_854), self.freq_854.valueChanged, self.freq_854.setRange, 'MHz'),
                                                        ],
               tuple(c.optical_pumping_frequency_866):[
                                                       Parameter(c.optical_pumping_frequency_866, setValueBlocking(self.optical_pumping_frame.freq866), self.optical_pumping_frame.freq866.valueChanged, self.optical_pumping_frame.freq866.setRange, 'MHz'),
                                                       Parameter(c.doppler_cooling_frequency_866, setValueBlocking(self.doppler_frequency_866), self.doppler_frequency_866.valueChanged, self.doppler_frequency_866.setRange, 'MHz'),
                                                       ]
               }

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = state_preparation_connection(reactor)
    widget.show()
    reactor.run()
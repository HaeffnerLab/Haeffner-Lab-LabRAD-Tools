from PyQt4 import QtGui, QtCore
from helper_widgets.compound_widgets import frequency_wth_selector
from configuration import config_729_sideband_cooling as c
from async_semaphore import async_semaphore, Parameter


class sideband_cooling_widget(QtGui.QWidget):
    def __init__(self, reactor, cxn = None, parent = None):
        super(sideband_cooling_widget, self).__init__(parent)
        self.reactor = reactor
        self.input_font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.input_font_large = QtGui.QFont('MS Shell Dlg 2',pointSize=14)
        self.setup_layout()
    
    def setup_layout(self):
        layout = QtGui.QVBoxLayout()
        self.cooling = sideband_cooling_frame(self.reactor, "Sideband Cooling", self.input_font, self.input_font_large)
        layout.addWidget(self.cooling)
        self.setLayout(layout)

class sideband_cooling_frame(QtGui.QFrame):
    def __init__(self, reactor, title, font, large_font):
        super(sideband_cooling_frame, self).__init__()
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
        self.continuous = QtGui.QRadioButton()
        self.pulsed = QtGui.QRadioButton()
        bg = QtGui.QButtonGroup()
        #make them exclusive
        bg.addButton(self.continuous)
        bg.addButton(self.pulsed)
        label = QtGui.QLabel('Continuous 729', font = font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 7, 0)
        layout.addWidget(self.continuous, 7, 1)
        label = QtGui.QLabel('Pulsed 729', font = font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 7, 2)
        layout.addWidget(self.pulsed, 7, 3)
        bg.setExclusive(True)
        #number of cycles
        self.cycles = QtGui.QSpinBox()
        self.cycles.setKeyboardTracking(False)
        self.setFont(font)
        #frequencies and amplitudes
        self.freq_selector = frequency_wth_selector(self.reactor, parameter_name = 'Frequency 729', suffix = 'MHz', 
                                                    sig_figs = 4, font = font, only_show_favorites = True, expandable = False)
        self.freq_selector.setContentsMargins(0, 0, 0, 0)
        self.freq_selector.setMinimumHeight(300)
        self.freq_selector.set_favorites(c.sideband_coooling_favorite_lines)
        self.freq854 = QtGui.QDoubleSpinBox()
        self.freq866 = QtGui.QDoubleSpinBox()
        self.ampl729 = QtGui.QDoubleSpinBox()
        self.ampl854 = QtGui.QDoubleSpinBox()
        self.ampl866 = QtGui.QDoubleSpinBox()
        self.increment_729 = QtGui.QDoubleSpinBox()
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
        layout.addWidget(self.freq_selector, 1, 0, 1, 4)
        label = QtGui.QLabel("Cycles")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 5, 0, 1, 1)
        layout.addWidget(self.cycles, 5, 1, 1, 1)
        label = QtGui.QLabel("Increment 729 Duration Each Cycle")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 5, 2, 1, 1)
        layout.addWidget(self.increment_729, 5, 3, 1, 1)
        label = QtGui.QLabel("Amplitude 729")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 2, 2, 1, 1)
        layout.addWidget(self.ampl729, 2, 3, 1, 1)
        label = QtGui.QLabel("Frequency 854")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 3, 0, 1, 1)
        layout.addWidget(self.freq854, 3, 1, 1, 1)
        label = QtGui.QLabel("Amplitude 854")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 3, 2, 1, 1)
        layout.addWidget(self.ampl854, 3, 3, 1, 1)
        label = QtGui.QLabel("Frequency 866")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 4, 0, 1, 1)
        layout.addWidget(self.freq866, 4, 1, 1, 1)
        label = QtGui.QLabel("Amplitude 866")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 4, 2, 1, 1)
        layout.addWidget(self.ampl866, 4, 3, 1, 1)
        #durations
        self.continuous_duration = QtGui.QDoubleSpinBox()
        self.repump_additional = QtGui.QDoubleSpinBox()
        self.between_pulses = QtGui.QDoubleSpinBox()
        self.optical_pumping_duration = QtGui.QDoubleSpinBox()
        for w in [self.continuous_duration, self.repump_additional, self.between_pulses, self.optical_pumping_duration]:
            w.setKeyboardTracking(False)
            w.setSuffix('us')
            w.setDecimals(1)
            w.setSingleStep(0.1)
            w.setFont(font)
        self.pulses_per_cycle = QtGui.QSpinBox()
        self.pulses_per_cycle.setKeyboardTracking(False)
        self.pulses_per_cycle.setFont(font)
        self.pulse_729 = QtGui.QDoubleSpinBox()
        self.pulse_repumps = QtGui.QDoubleSpinBox()
        self.pulse_866_additional = QtGui.QDoubleSpinBox()
        for w in [self.pulse_729, self.pulse_repumps, self.pulse_866_additional, self.increment_729]:
            w.setSuffix('\265s')
            w.setDecimals(1)
            w.setSingleStep(0.1)
            w.setKeyboardTracking(False)
            w.setFont(font)
        label =  QtGui.QLabel("Optical Pumping Duration")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 6, 0, 1, 1)
        layout.addWidget(self.optical_pumping_duration, 6, 1, 1, 1)
        label =  QtGui.QLabel("Cycle Duration")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 8, 0, 1, 1)
        layout.addWidget(self.continuous_duration, 8, 1, 1, 1)
        label =  QtGui.QLabel("Additional Repump")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 9, 0, 1, 1)
        layout.addWidget(self.repump_additional, 9, 1, 1, 1)
        label =  QtGui.QLabel("Pulses Per Cycle")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 8, 2, 1, 1)
        layout.addWidget(self.pulses_per_cycle, 8, 3, 1, 1)
        label =  QtGui.QLabel("Pulse 729")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 9, 2, 1, 1)
        layout.addWidget(self.pulse_729, 9, 3, 1, 1)
        label =  QtGui.QLabel("Pulse Repumps")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 10, 2, 1, 1)
        layout.addWidget(self.pulse_repumps, 10, 3, 1, 1)
        label =  QtGui.QLabel("Additional 866")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 11, 2, 1, 1)
        layout.addWidget(self.pulse_866_additional, 11, 3, 1, 1)
        label =  QtGui.QLabel("Between Pulses")
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        layout.addWidget(label, 12, 2, 1, 1)
        layout.addWidget(self.between_pulses, 12, 3, 1, 1)
        self.setLayout(layout)
    
    def closeEvent(self, x):
        self.reactor.stop()
        
class sideband_cooling_connection(sideband_cooling_widget, async_semaphore):
    
    def __init__(self, reactor, cxn = None, parent = None):
        super(sideband_cooling_connection, self).__init__(reactor)
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
                #optical pumping
                tuple(c.sideband_cooling_enable):Parameter(c.sideband_cooling_enable, setValueBlocking_cb(self.cooling.enable), updateSignal = self.cooling.enable.toggled),                          
                tuple(c.sideband_cooling_continuous):Parameter(c.sideband_cooling_continuous, setValueBlocking_cb(self.cooling.continuous), updateSignal = self.cooling.continuous.toggled),
                tuple(c.sideband_cooling_pulsed):Parameter(c.sideband_cooling_pulsed, setValueBlocking_cb(self.cooling.pulsed), updateSignal = self.cooling.pulsed.toggled),
                tuple(c.sideband_cooling_cycles):Parameter(c.sideband_cooling_cycles, setValueBlocking(self.cooling.cycles), self.cooling.cycles.valueChanged, self.cooling.cycles.setRange, None),
                tuple(c.sideband_cooling_pulsed_cycles):Parameter(c.sideband_cooling_pulsed_cycles, setValueBlocking(self.cooling.pulses_per_cycle), self.cooling.pulses_per_cycle.valueChanged, self.cooling.pulses_per_cycle.setRange, None),
                tuple(c.sideband_cooling_frequency_729): Parameter(c.sideband_cooling_frequency_729, self.cooling.freq_selector.set_freq_value_no_signals, self.cooling.freq_selector.manual_entry_value_changed, self.cooling.freq_selector.setRange, 'MHz'),
                tuple(c.sideband_cooling_amplitude_729): Parameter(c.sideband_cooling_amplitude_729, setValueBlocking(self.cooling.ampl729), self.cooling.ampl729.valueChanged, self.cooling.ampl729.setRange, 'dBm'),
                tuple(c.sideband_cooling_amplitude_854): Parameter(c.sideband_cooling_amplitude_854, setValueBlocking(self.cooling.ampl854), self.cooling.ampl854.valueChanged, self.cooling.ampl854.setRange, 'dBm'),
                tuple(c.sideband_cooling_amplitude_866): Parameter(c.sideband_cooling_amplitude_866, setValueBlocking(self.cooling.ampl866), self.cooling.ampl866.valueChanged, self.cooling.ampl866.setRange, 'dBm'),
                tuple(c.sideband_cooling_continuous_duration):Parameter(c.sideband_cooling_continuous_duration, setValueBlocking(self.cooling.continuous_duration), self.cooling.continuous_duration.valueChanged, self.cooling.continuous_duration.setRange, 'us'),
                tuple(c.sideband_cooling_continuous_pump_additional):Parameter(c.sideband_cooling_continuous_pump_additional, setValueBlocking(self.cooling.repump_additional), self.cooling.repump_additional.valueChanged, self.cooling.repump_additional.setRange, 'us'),
                tuple(c.sideband_cooling_pulsed_duration_729):Parameter(c.sideband_cooling_pulsed_duration_729, setValueBlocking(self.cooling.pulse_729), self.cooling.pulse_729.valueChanged, self.cooling.pulse_729.setRange, 'us'),
                tuple(c.sideband_cooling_pulsed_duration_repumps):Parameter(c.sideband_cooling_pulsed_duration_repumps, setValueBlocking(self.cooling.pulse_repumps), self.cooling.pulse_repumps.valueChanged, self.cooling.pulse_repumps.setRange, 'us'),
                tuple(c.sideband_cooling_pulsed_duration_additional_866):Parameter(c.sideband_cooling_pulsed_duration_additional_866, setValueBlocking(self.cooling.pulse_866_additional), self.cooling.pulse_866_additional.valueChanged, self.cooling.pulse_866_additional.setRange, 'us'), 
                tuple(c.sideband_cooling_pulsed_duration_between_pulses):Parameter(c.sideband_cooling_pulsed_duration_between_pulses, setValueBlocking(self.cooling.between_pulses), self.cooling.between_pulses.valueChanged, self.cooling.between_pulses.setRange, 'us'),
                tuple(c.sideband_cooling_pulsed_duration_repumps):Parameter(c.sideband_cooling_pulsed_duration_repumps, setValueBlocking(self.cooling.pulse_repumps), self.cooling.pulse_repumps.valueChanged, self.cooling.pulse_repumps.setRange, 'us'), 
                #sideband_cooling_optical_pumping_duration            
                tuple(c.sideband_cooling_optical_pumping_duration):
                    Parameter(c.sideband_cooling_optical_pumping_duration, setValueBlocking(self.cooling.optical_pumping_duration), self.cooling.optical_pumping_duration.valueChanged, self.cooling.optical_pumping_duration.setRange, 'us'), 
                #sideband_cooling_duration_729_increment_per_cycle                
                tuple(c.sideband_cooling_duration_729_increment_per_cycle):
                    Parameter(c.sideband_cooling_duration_729_increment_per_cycle, setValueBlocking(self.cooling.increment_729), self.cooling.increment_729.valueChanged, self.cooling.increment_729.setRange, 'us'), 
                #sideband_cooling_line_selection
                tuple(c.sideband_cooling_line_selection):
                    Parameter(c.sideband_cooling_line_selection, self.cooling.freq_selector.set_selection, self.cooling.freq_selector.on_new_selection, do_nothing, None), 
                #sideband_cooling_use_line_selection
                tuple(c.sideband_cooling_use_line_selection):
                    Parameter(c.sideband_cooling_use_line_selection, self.cooling.freq_selector.should_use_saved, updateSignal = self.cooling.freq_selector.use_selector),
                #sideband_cooling_frequency_854
                tuple(c.sideband_cooling_frequency_854):
                    Parameter(c.sideband_cooling_frequency_854, setValueBlocking(self.cooling.freq854), self.cooling.freq854.valueChanged, self.cooling.freq854.setRange, 'MHz'),
                #sideband_cooling_frequency_866
                tuple(c.sideband_cooling_frequency_866):
                    Parameter(c.sideband_cooling_frequency_866, setValueBlocking(self.cooling.freq866), self.cooling.freq866.valueChanged, self.cooling.freq866.setRange, 'MHz'),           
                #saved liens
                tuple(c.saved_lines_729):
                    Parameter(c.saved_lines_729, self.cooling.freq_selector.set_dropdown, no_signal, do_nothing, c.line_parameter_units),
                }

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = sideband_cooling_connection(reactor)
    widget.show()
    reactor.run()
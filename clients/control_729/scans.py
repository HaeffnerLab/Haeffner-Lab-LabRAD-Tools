from PyQt4 import QtGui,QtCore
from helper_widgets import durationWdiget, limitsWidget, frequency_wth_dropdown, lineinfo_table, dropdown
from configuration import config_729_spectrum as c
from async_semaphore import async_semaphore, Parameter

class line_info(QtGui.QFrame):
    
    def __init__(self, reactor, font):
        super(line_info, self).__init__()
        self.reactor = reactor
        self.setFrameStyle(QtGui.QFrame.Panel  | QtGui.QFrame.Sunken)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.initializeGUI(font)
        
    def initializeGUI(self, font):
        self.lineinfo = lineinfo_table(self.reactor, sig_figs = c.line_parameter_sig_figs, column_names = c.line_parameter_names, suffix = c.line_parameter_units)
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.lineinfo)
        self.setLayout(layout)
    
    def closeEvent(self, x):
        self.reactor.stop()

class spectrum(QtGui.QFrame):
    def __init__(self, reactor, font, large_font):
        super(spectrum, self).__init__()
        self.reactor = reactor
        self.setFrameStyle(QtGui.QFrame.Panel  | QtGui.QFrame.Sunken)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.initializeGUI(font, large_font)
    
    def initializeGUI(self, font, large_font):
        layout = QtGui.QGridLayout()
        #make title
        title_label = QtGui.QLabel("Spectrum", font = large_font)
        title_label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        layout.addWidget(title_label, 0, 0, 1, 1)
        self.duration = durationWdiget(self.reactor)
        self.duration.layout().setContentsMargins(0,0,0,0)
        layout.addWidget(self.duration, 0, 1, 2, 2)
        self.ampl_729 = QtGui.QDoubleSpinBox()
        self.ampl_729.setSuffix('dBm')
        self.ampl_729.setDecimals(1)
        self.ampl_729.setSingleStep(0.1)
        self.ampl_729.setKeyboardTracking(False)
        self.ampl_729.setFont(font)
        label = QtGui.QLabel("Spectrum Amplitude 729", font = font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        layout.addWidget(label, 0, 3)
        layout.addWidget(self.ampl_729, 1, 3, 1, 1)
        self.limitWidget = limitsWidget(self.reactor, 'MHz', sigfigs = 4)
        layout.addWidget(self.limitWidget, 4, 0, 1, 4)
        label = QtGui.QLabel("Use Saved Line Info", font = font)
        self.use_saved_line = QtGui.QCheckBox()
        self.dropdown = dropdown(font, info_position = 0)
        self.setLayout(layout)
        layout.addWidget(label, 0, 5, 1, 1)
        layout.addWidget(self.use_saved_line, 0, 6, 1, 1)
        layout.addWidget(self.dropdown, 1, 5, 1, 2)
        self.use_saved_line.toggled.connect(self.on_use_saved)
        self.setLayout(layout)
    
    def on_use_saved(self, use_saved):
        to_disable = [self.limitWidget, self.ampl_729, self.duration]
        if use_saved:
            for w in to_disable:
                w.setDisabled(True)
        else:
            for w in to_disable:
                w.setDisabled(False)
    
    def closeEvent(self, x):
        self.reactor.stop()
        
class rabi(QtGui.QFrame):
    def __init__(self, reactor, font, large_font):
        super(rabi, self).__init__()
        self.reactor = reactor
        self.setFrameStyle(QtGui.QFrame.Panel  | QtGui.QFrame.Sunken)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.initializeGUI(font, large_font)
    
    def initializeGUI(self, font, large_font):
        layout = QtGui.QGridLayout()
        title_label = QtGui.QLabel("Rabi Flopping", font = large_font)
        title_label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        layout.addWidget(title_label, 0, 0, 1, 1)
        self.freq729 = frequency_wth_dropdown(self.reactor, parameter_name = 'Rabi Frequency 729', font = font, suffix = 'MHz', sig_figs = 4)
        self.freq729.layout().setContentsMargins(0,0,0,0)
        self.ampl729 = QtGui.QDoubleSpinBox()
        self.ampl729.setSuffix('dBm')
        self.ampl729.setDecimals(1)
        self.ampl729.setSingleStep(0.1)
        self.ampl729.setKeyboardTracking(False)
        self.ampl729.setFont(font)
        layout.addWidget(self.freq729, 0, 1, 2, 1)
        label = QtGui.QLabel("Rabi Amplitude 729", font = font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        layout.addWidget(label, 0, 2, 1, 1)
        layout.addWidget(self.ampl729, 1, 2, 1, 1)
        self.lim = limitsWidget(self.reactor, '\265s')
        layout.addWidget(self.lim, 2, 0, 1, 4)
        self.setLayout(layout)
        
    def closeEvent(self, x):
        self.reactor.stop()
   
class scans(QtGui.QWidget):
       
    def __init__(self, reactor, parent=None):
        super(scans, self).__init__(parent)
        self.reactor = reactor
        self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.large_font = QtGui.QFont('MS Shell Dlg 2',pointSize=14)
        self.initializeGUI()
        
    def initializeGUI(self):
        layout = QtGui.QVBoxLayout()
        self.lineinfo = line_info(self.reactor, self.font)
        self.spectrum = spectrum(self.reactor, self.font, self.large_font)
        self.rabi = rabi(self.reactor, self.font, self.large_font)
        layout.addWidget(self.lineinfo)
        layout.addWidget(self.spectrum)
        layout.addWidget(self.rabi)
        self.setLayout(layout)
        return layout
        
    def closeEvent(self, x):
        self.reactor.stop()
        
class scans_connection(scans, async_semaphore):
    
    def __init__(self, reactor, cxn = None, parent = None):
        super(scans_connection, self).__init__(reactor)
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
        
        class no_signal(object):
            @staticmethod
            def connect(*args):
                pass
        
        self.d = {
                #spin boxes
                tuple(c.spectrum_excitation_time): Parameter(c.spectrum_excitation_time, self.spectrum.duration.setNewDuration_blocking, self.spectrum.duration.new_duration, self.spectrum.duration.duration.setRange, 'us'),
                tuple(c.spectrum_amplitude_729): Parameter(c.spectrum_amplitude_729, setValueBlocking(self.spectrum.ampl_729), self.spectrum.ampl_729.valueChanged, self.spectrum.ampl_729.setRange, 'dBm'),
                tuple(c.spectrum_use_saved):Parameter(c.spectrum_use_saved, self.spectrum.use_saved_line.setChecked, updateSignal = self.spectrum.use_saved_line.toggled),
                tuple(c.spectrum_saved_freq):Parameter(c.spectrum_saved_freq, self.spectrum.dropdown.set_selected, self.spectrum.dropdown.currentIndexChanged[QtCore.QString], do_nothing, None), 
                #list
                tuple(c.spectrum_frequencies):Parameter(c.spectrum_frequencies, do_nothing, self.spectrum.limitWidget.new_list_signal, self.spectrum.limitWidget.setRange, 'MHz'),
                tuple(c.rabi_frequency): Parameter(c.rabi_frequency, self.rabi.freq729.set_freq_value_no_signals, self.rabi.freq729.valueChanged, self.rabi.freq729.setRange, 'MHz'),
                tuple(c.rabi_amplitude_729): Parameter(c.rabi_amplitude_729, setValueBlocking(self.rabi.ampl729), self.rabi.ampl729.valueChanged, self.rabi.ampl729.setRange, 'dBm'),


                #list
                tuple(c.rabi_excitation_times):Parameter(c.rabi_excitation_times, do_nothing, self.rabi.lim.new_list_signal, self.rabi.lim.setRange, 'us'),
                tuple(c.rabi_saved_freq):Parameter(c.rabi_saved_freq, self.rabi.freq729.set_selected, self.rabi.freq729.useSavedLine, do_nothing, None), 
                tuple(c.rabi_use_saved):Parameter(c.rabi_use_saved, self.rabi.freq729.set_use_saved, updateSignal = self.rabi.freq729.useSaved),
                #saved lines
                tuple(c.saved_lines_729):[
                                          Parameter(c.saved_lines_729, self.rabi.freq729.set_dropdown, no_signal, do_nothing, c.line_parameter_units),
                                          Parameter(c.saved_lines_729, self.lineinfo.lineinfo.set_info,  self.lineinfo.lineinfo.info_updated, self.lineinfo.lineinfo.set_range, c.line_parameter_units),
                                          Parameter(c.saved_lines_729, self.spectrum.dropdown.set_dropdown, no_signal, do_nothing, c.line_parameter_units),
                                          ], 
                  }
        
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = scans_connection(reactor)
    widget.show()
    reactor.run()
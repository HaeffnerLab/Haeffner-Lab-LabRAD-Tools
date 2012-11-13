from PyQt4 import QtGui, QtCore
import numpy

class durationWdiget(QtGui.QWidget):
    
    new_duration = QtCore.pyqtSignal(float)
    
    def __init__(self, reactor, value = 1, init_range = (1,1000), font = None, parent=None):
        super(durationWdiget, self).__init__(parent)
        self.reactor = reactor
        self.value = value
        self.ran = init_range
        if font is None:
            self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        else:
            self.font = font
        self.initializeGUI()
        
    def initializeGUI(self):
        layout = QtGui.QGridLayout()
        durationLabel = QtGui.QLabel('Excitation Time', font = self.font)
        bandwidthLabel =  QtGui.QLabel('Fourier Bandwidth', font = self.font)
        durationLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        bandwidthLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        self.duration = duration = QtGui.QSpinBox()
        duration.setFont(self.font)
        duration.setSuffix('\265s')
        duration.setKeyboardTracking(False)
        duration.setRange(*self.ran)
        duration.setValue(self.value)
        initband = self.conversion(self.value)
        self.bandwidth = bandwidth = QtGui.QDoubleSpinBox()
        bandwidth.setFont(self.font)
        bandwidth.setDecimals(1)
        bandwidth.setKeyboardTracking(False)
        bandwidth.setRange(*[self.conversion(r) for r in [self.ran[1],self.ran[0]]])
        bandwidth.setValue(initband)
        bandwidth.setSuffix('kHz')
        #connect
        duration.valueChanged.connect(self.onNewDuration)
        bandwidth.valueChanged.connect(self.onNewBandwidth)
        #add to layout
        layout.addWidget(durationLabel, 0, 0)
        layout.addWidget(bandwidthLabel, 0, 1)
        layout.addWidget(duration, 1, 0)
        layout.addWidget(bandwidth, 1, 1)
        self.setLayout(layout)

    def onNewDuration(self, dur):
        band = self.conversion(dur)
        self.bandwidth.blockSignals(True)
        self.bandwidth.setValue(band)
        self.bandwidth.blockSignals(False)
        self.new_duration.emit(dur)
    
    def onNewBandwidth(self, ban):
        dur =  self.conversion(ban)
        self.duration.blockSignals(True)
        self.duration.setValue(dur)
        self.duration.blockSignals(False)
        self.new_duration.emit(dur)
    
    def setNewDuration_blocking(self, dur):
        '''for external access, setting both duration and bandwidth while emitting no signals'''
        band = self.conversion(dur)
        self.duration.blockSignals(True)
        self.duration.setValue(dur)
        self.duration.blockSignals(False)
        self.bandwidth.blockSignals(True)
        self.bandwidth.setValue(band)
        self.bandwidth.blockSignals(False)
        
        
    @staticmethod
    def conversion(x):
        return 10**3 * (1.0 / (2.0 * numpy.pi * float(x) ) ) #fourier bandwidth, and unit conversion
    
    def closeEvent(self, x):
        self.reactor.stop()
    
class limitsWidget(QtGui.QWidget):
    
    new_list_signal = QtCore.pyqtSignal(list)
    
    def __init__(self, reactor, suffix = '', abs_range = None, sigfigs = 3,  font = None, parent=None):
        super(limitsWidget, self).__init__(parent)
        self.reactor = reactor
        self.suffix = suffix
        self.sigfigs = sigfigs
        if font is None:
            self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        else:
            self.font = font
        
        self.initializeGUI()
        if abs_range is not None:
            self.setRange(*abs_range)
            self.setInitialValuesFromRange(*abs_range)
        
    def initializeGUI(self):
        layout = QtGui.QGridLayout()
        self.start = start = QtGui.QDoubleSpinBox()
        self.stop = stop = QtGui.QDoubleSpinBox()
        self.center = center = QtGui.QDoubleSpinBox()
        self.span = span = QtGui.QDoubleSpinBox()
        self.setresolution = setresolution = QtGui.QDoubleSpinBox()
        self.resolution = resolution = QtGui.QLineEdit( font = self.font)
        self.steps = steps = QtGui.QSpinBox()
        self.lockSteps = lockSteps = QtGui.QRadioButton()
        self.lockResolution = lockResolution = QtGui.QRadioButton()
        bg = QtGui.QButtonGroup()
        #make them exclusive
        bg.addButton(self.lockSteps)
        bg.addButton(self.lockResolution)
        bg.setExclusive(True)
        self.lockResolution.setChecked(True)
        steps.setRange(1,1000)
        resolution.setReadOnly(True)
        steps.setKeyboardTracking(False)
        steps.setFont(self.font)
        for widget in [start, stop, setresolution, center, span]:
            widget.setKeyboardTracking(False)
            widget.setDecimals(self.sigfigs)
            widget.setSuffix(self.suffix)
            widget.setSingleStep(10**-self.sigfigs)
            widget.setFont(self.font)
        self.updateResolutionLabel(setresolution.value())
        #connect
        start.valueChanged.connect(self.onNewStartStop)
        stop.valueChanged.connect(self.onNewStartStop)
        setresolution.valueChanged.connect(self.onNewResolution)
        steps.valueChanged.connect(self.onNewSteps)
        span.valueChanged.connect(self.onNewCenterSpan)
        center.valueChanged.connect(self.onNewCenterSpan)
        #add to layout
        layout.addWidget( QtGui.QLabel('Start', font = self.font), 0, 0, 1, 1)
        layout.addWidget(QtGui.QLabel('Stop', font = self.font), 0, 1, 1, 1)
        layout.addWidget(QtGui.QLabel('Set Resolution', font = self.font), 0, 2, 1, 1)
        layout.addWidget(QtGui.QLabel('Set Steps', font = self.font), 0, 3, 1, 1)
        layout.addWidget(QtGui.QLabel('Resolution', font = self.font), 0, 4, 1, 1)
        layout.addWidget(QtGui.QLabel('Center', font = self.font), 2, 0, 1, 1)
        layout.addWidget(QtGui.QLabel('Span', font = self.font), 2, 1, 1, 1)
        layout.addWidget(QtGui.QLabel('Lock Resolution', font = self.font), 2, 2, 1, 1)
        layout.addWidget(QtGui.QLabel('Lock Steps', font = self.font), 2, 3, 1, 1)
        layout.addWidget(start, 1, 0, 1, 1)
        layout.addWidget(stop, 1, 1, 1, 1)
        layout.addWidget(setresolution, 1, 2, 1, 1)
        layout.addWidget(steps, 1, 3, 1, 1)
        layout.addWidget(resolution, 1, 4, 1, 1)
        layout.addWidget(center, 3, 0, 1, 1)
        layout.addWidget(span, 3, 1, 1, 1)
        layout.addWidget(lockResolution, 3, 2, 1, 1)
        layout.addWidget(lockSteps, 3, 3, 1, 1)
        self.setLayout(layout)
    
    def setRange(self, minim, maxim):
        ran = (minim,maxim)
        for widget in [self.start, self.stop]:
            widget.setRange(*ran)
        max_diff = ran[1] - ran[0]
        self.span.setRange(-max_diff, max_diff)
        self.center.setRange(ran[0], ran[1])
        self.setresolution.setRange(-max_diff, max_diff)
    
    def setInitialValuesFromRange(self, minim, maxim):
        self.start.setValue(minim)
        self.stop.setValue(maxim)
        self.span.setValue(maxim - minim)
        self.center.setValue( (minim + maxim)/ 2.0)
        self.setresolution.setValue( maxim - minim)
    
    def onNewCenterSpan(self, x):
        center = self.center.value()
        span = self.span.value()
        start = center - span / 2.0
        stop = center + span/2.0
        self.start.blockSignals(True)
        self.stop.blockSignals(True)
        self.start.setValue(start)
        self.stop.setValue(stop)
        self.start.blockSignals(False)
        self.stop.blockSignals(False)
        self.updateResolutionSteps()
        self.new_list_signal.emit( self.frequencies)
    
    def onNewStartStop(self, x):
        start = self.start.value()
        stop = self.stop.value()
        #update center and span
        self.center.blockSignals(True)
        self.span.blockSignals(True)
        self.center.setValue((start + stop)/2.0)
        self.span.setValue(stop - start)
        self.center.blockSignals(False)
        self.span.blockSignals(False)
        self.updateResolutionSteps()
        self.new_list_signal.emit( self.frequencies)
    
    def updateResolutionSteps(self):
        '''calculate and update the resolution or the steps depending on which is locked'''
        if self.lockSteps.isChecked():
            self.onNewSteps(self.steps.value())
        else:
            self.onNewResolution(self.setresolution.value())
        
    def updateResolutionLabel(self, val):
        text = '{:.3f} {}'.format(val, self.suffix)
        self.resolution.setText(text)
    
    def onNewSteps(self, steps):
        start = self.start.value()
        stop = self.stop.value()
        res = self._resolution_from_steps(start, stop, steps)
        self._set_resolution_no_signal(res)
        self.updateResolutionLabel(res)
        self.new_list_signal.emit( self.frequencies)
    
    def onNewResolution(self, res):
        '''called when resolution is updated'''
        start = self.start.value()
        stop = self.stop.value()
        steps = self._steps_from_resolution(start, stop, res)
        self._set_steps_nosignal(steps)
        final_res = self._resolution_from_steps(start, stop, steps)
        self.updateResolutionLabel(final_res)
        self.new_list_signal.emit( self.frequencies)
    
    def _set_steps_nosignal(self, steps):
        self.steps.blockSignals(True)
        self.steps.setValue(steps)
        self.steps.blockSignals(False)
    
    def _set_resolution_no_signal(self, res):
        self.setresolution.blockSignals(True)
        self.setresolution.setValue(res)
        self.setresolution.blockSignals(False)
    
    def _resolution_from_steps(self, start, stop, steps):
        '''computes the resolution given the number of steps'''
        if steps > 1:
            res = numpy.linspace(start, stop, steps, endpoint = True, retstep = True)[1]
        else:
            res = stop - start
        return res
    
    def _steps_from_resolution(self, start, stop, res):
        '''computes the number of steps given the resolution'''
        try:
            steps = int(round( (stop - start) / res))
        except ZeroDivisionError:
            steps = 0                                
        steps = 1 +  max(0, steps) #make sure at least 1
        return steps
    
    @property
    def frequencies(self):
        start = self.start.value()
        stop = self.stop.value()
        steps = self.steps.value()
        return numpy.linspace(start, stop, steps, endpoint = True).tolist()
    
    def closeEvent(self, x):
        self.reactor.stop()

class saved_frequencies_table(QtGui.QTableWidget):
    def __init__(self, reactor, sig_figs = 4, suffix = '', parent=None):
        super(saved_frequencies_table, self).__init__(parent)
        self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.sig_figs = sig_figs
        self.suffix = suffix
        self.reactor = reactor
        self.initializeGUI()
        
    def initializeGUI(self):
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setColumnCount(2)
    
    def fill_out_widget(self, info):
        self.setRowCount(len(info))
        form = '{' + '0:.{}f'.format(self.sig_figs) + '}' + ' {}'.format( self.suffix)
        for enum,tup in enumerate(info):
            name,val = tup
            val_name = form.format(val)
            try:
                label = self.cellWidget(enum, 0)
                label.setText(name)
                sample = self.cellWidget(enum, 1)
                sample.setText(val_name)
            except AttributeError:
                label = QtGui.QTableWidgetItem(name)
                label.setFont(self.font)
                self.setItem(enum , 0 , label)
                sample = QtGui.QTableWidgetItem(val_name)
                sample.setFont(self.font)
                self.setItem(enum , 1 , sample)
            
    def closeEvent(self, x):
        self.reactor.stop()
        
class dropdown(QtGui.QComboBox):
    def __init__(self, font = None, names = [], info_position = None, parent = None ):
        super(dropdown, self).__init__(parent)
        self.info_position = info_position
        self.selected = None
        if font is not None:
            self.setFont(font)
        self.setInsertPolicy(QtGui.QComboBox.InsertAlphabetically)
        self.SizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.set_dropdown(names)
        
    def set_selected(self, text):
        self.selected = text
        item = self.findText(text)
        if item is not -1:
            self.blockSignals(True)
            self.setCurrentIndex(item)
            self.blockSignals(False)
    
    def set_dropdown(self, info):
        self.blockSignals(True)
        for values in info:
            if self.info_position is not None:
                name = values[self.info_position]
            else:
                name = values
            self.addItem(name)
        if self.selected is not None:
            self.set_selected(self.selected)
        self.blockSignals(False)

class saved_frequencies_dropdown(QtGui.QTableWidget):
    def __init__(self, reactor, limits = (0,500), sig_figs = 4, names = [], entries = 2, suffix = '', parent=None):
        super(saved_frequencies_dropdown, self).__init__(parent)
        self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.limits = limits
        self.sig_figs = sig_figs
        self.names = names
        self.entries = entries
        self.suffix = suffix
        self.reactor = reactor
        self.initializeGUI()
        
    def initializeGUI(self):
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setColumnCount(2)
        self.setRowCount(self.entries)
        self.fill_out()
    
    def fill_out(self, names = None):
        if names is not None:
            self.names = names
        for i in range(self.entries):
            drop = dropdown(names = self.names, font=self.font)
            self.setCellWidget(i ,0 , drop)
            sample = QtGui.QDoubleSpinBox()
            sample.setFont(self.font)
            sample.setRange(*self.limits)
            sample.setDecimals(self.sig_figs)
            sample.setSingleStep(10**-self.sig_figs)
            sample.setSuffix(self.suffix)
            self.setCellWidget(i, 1, sample)
    
    def get_info(self):
        info = []
        for i in range(self.entries):
            duration = self.cellWidget(i, 0)
            text = duration.currentText()
            text = str(text)
            spin =  self.cellWidget( i, 1)
            val = spin.value()
            info.append((text, val))
        return info

    def closeEvent(self, x):
        self.reactor.stop()

class lineinfo_table(QtGui.QTableWidget):
    
    info_updated = QtCore.pyqtSignal(list)
    
    def __init__(self, reactor, sig_figs = 4, column_names = ['line', 'parameter'], suffix = ['MHz'], parent=None):
        super(lineinfo_table, self).__init__(parent)
        self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.sig_figs = sig_figs
        self.column_names = column_names
        self.parameter_name = column_names[1]
        self.suffix = suffix
        self.r_min = None
        self.r_max = None
        self.reactor = reactor
        self.initializeGUI()
        
    def initializeGUI(self):
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setColumnCount(len(self.column_names))
        self.setHorizontalHeaderLabels(self.column_names)
    
    def set_info(self, info):
        self.setRowCount(len(info))
        for enum, tup in enumerate(info):
            name = tup[0] 
            try:
                label = self.cellWidget(enum, 0)
                label.setText(name)
            except AttributeError:            
                label = QtGui.QLabel(name)
                label.setFont(self.font)
                self.setCellWidget(enum ,0 , label)
            for col in range(1,self.columnCount()):
                try:
                    spin = self.cellWidget(enum, col)
                    spin.blockSignals(True)
                    spin.setValue(tup[col])
                    spin.blockSignals(False)
                except AttributeError: 
                    spin = QtGui.QDoubleSpinBox()
                    spin.setFont(self.font)
                    spin.setDecimals(self.sig_figs[col - 1])
                    spin.setSingleStep(10**-self.sig_figs[col - 1])
                    spin.setSuffix(' ' + self.suffix[col - 1])
                    spin.blockSignals(True)
                    if self.r_min is not None and self.r_max is not None:
                        spin.setRange(self.r_min[col -1 ],self.r_max[col -1 ])
                    spin.setValue(tup[col])
                    spin.blockSignals(False)
                    spin.valueChanged.connect(self.on_new_info)
                    self.setCellWidget(enum, col, spin)
    
    def on_new_info(self, val):
        info = self.get_info()
        self.info_updated.emit(info)
    
    def set_range(self, r_min, r_max):
        self.r_min = r_min
        self.r_max = r_max
        for enum in range( self.rowCount() ):
            for col in range(1,self.columnCount()):
                try:
                    spin = self.cellWidget(enum, col)
                except AttributeError:
                    pass
                else:
                    spin.blockSignals(True)
                    spin.setRange(r_min[col - 1],r_max[col -1])
                    spin.blockSignals(False)

    def get_info(self):
        info = []
        for enum in range( self.rowCount() ):
            l = []
            label = self.cellWidget(enum, 0)
            name = label.text()
            l.append(str(name))
            for col in range(1,self.columnCount()):
                spin =  self.cellWidget( enum, col)
                val = spin.value()
                l.append(val)
            info.append(tuple(l))
        return info
    
    def closeEvent(self, x):
        self.reactor.stop()

class frequency_wth_dropdown(QtGui.QWidget):
    
    valueChanged = QtCore.pyqtSignal(float)
    useSaved = QtCore.pyqtSignal(bool)
    useSavedLine = QtCore.pyqtSignal(str)
    
    def __init__(self, reactor, limits = (0,500), parameter_name = 'Frequency', sig_figs = 4, names = [], suffix = ' MHz', font = None, parent=None):
        super(frequency_wth_dropdown, self).__init__(parent)  
        self.reactor = reactor
        self.parameter_name = parameter_name
        self.limits = limits
        self.sig_figs =  sig_figs
        self.names = names
        self.suffix = suffix
        self.font = font
        self.selected = None
        if self.font is None:
            self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.initializeGUI()
        self.connect_layout()

    
    def initializeGUI(self):  
        layout = QtGui.QGridLayout()
        #frequency spin box  
        self.freq = QtGui.QDoubleSpinBox()
        self.freq.setKeyboardTracking(False)
        self.freq.setSuffix(self.suffix)
        self.freq.setDecimals(self.sig_figs)
        self.freq.setSingleStep(10**-self.sig_figs)
        self.freq.setRange(*self.limits)
        self.freq.setFont(self.font)
        #toggle button group
        self.select_freq = QtGui.QRadioButton()
        self.select_line = QtGui.QRadioButton()
        bg = QtGui.QButtonGroup()
        bg.setExclusive(True)
        bg.addButton(self.select_freq)
        bg.addButton(self.select_line)
        self.select_line.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.select_freq.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        layout.addWidget(self.select_freq, 1, 0)
        layout.addWidget(self.select_line, 1, 2)
        self.dropdown = dropdown(font = self.font, names = self.names, info_position = 0)
        label = QtGui.QLabel(self.parameter_name)
        label.setFont(self.font)
        label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        layout.addWidget(label,0, 1)
        layout.addWidget(self.freq, 1, 1)
        label = QtGui.QLabel('Saved Line')
        label.setFont(self.font)
        label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        layout.addWidget(label, 0, 3)
        layout.addWidget(self.dropdown, 1, 3)
        self.setLayout(layout)
    
    def connect_layout(self):
        self.freq.valueChanged.connect(self.valueChanged.emit)
        self.select_line.toggled.connect(self.useSaved.emit)
        self.dropdown.currentIndexChanged[QtCore.QString].connect(self.useSavedLine)
        
    def set_selected(self, text):
        self.dropdown.set_selected(text)
        
    def set_freq_value_no_signals(self, value):
        self.freq.blockSignals(True)
        self.freq.setValue(value)
        self.freq.blockSignals(False)
    
    def set_use_saved(self, val):
        self.select_line.setChecked(val)
        self.select_freq.setChecked(not val)
    
    def set_dropdown(self, names):
        self.dropdown.set_dropdown(names)
    
    def setRange(self, r_min, r_max):
        self.freq.setRange(r_min,r_max)
    
    def closeEvent(self, x):
        self.reactor.stop()

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
#    widget = limitsWidget(reactor, suffix = 'us', abs_range = (0,100))
#    widget = durationWdiget(reactor)
#    widget = saved_frequencies(reactor)
#    widget = saved_frequencies_table(reactor)
    widget = lineinfo_table(reactor)
    widget.show()
    reactor.run()
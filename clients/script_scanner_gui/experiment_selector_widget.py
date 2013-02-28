from PyQt4 import QtGui, QtCore, uic
from numpy import linspace
import os

basepath =  os.path.dirname(__file__)
path = os.path.join(basepath, "Views", "selectScan.ui")
base, form = uic.loadUiType(path)

class dialog_ui(base, form):
    def __init__(self, parent = None):
        super(dialog_ui, self).__init__(parent)
        self.setupUi(self)

class scan_dialog(QtGui.QDialog, dialog_ui):
    def __init__(self, selected, experiment_list, parameter_info, parent = None):
        QtGui.QDialog.__init__(self)
        dialog_ui.__init__(self, parent)
        self.setWindowTitle('Scan')
        self.parameter_info = {}
        self.setup_layout(selected, experiment_list, parameter_info)
        self.connect_layout()
        self.on_same_checked(self.same.isChecked())
        self.on_parameter_picked(self.parameter.currentIndex())
        
    def get_parameter(self):
        index = self.parameter.currentIndex()
        collection, parameter =  self.parameter.itemData(index).toPyObject()
        return (collection, parameter)
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Enter:
            pass
        else:
            super(scan_dialog, self).keyPressEvent(event)
        
    def setup_layout(self, selected, experiment_list, parameter_info):
        self.scan.setText(selected)
        self.measure.addItems(experiment_list)
        self.process_parameter_info(parameter_info)
    
    def process_parameter_info(self, info):
        for collection, parameter, minim, maxim, units in sorted(info):
            self.parameter.addItem(collection + ' : ' + parameter, userData = (collection, parameter) )
            self.parameter_info[(collection,parameter)] = (minim, maxim, units)
        
    def connect_layout(self):
        self.uiDecimals.valueChanged.connect(self.on_new_decimals)
        self.uiStart.editingFinished.connect(self.onNewStartStop)
        self.uiStop.editingFinished.connect(self.onNewStartStop)
        self.uiSetResolution.editingFinished.connect(self.onNewResolution)
        self.uiSteps.editingFinished.connect(self.onNewSteps)
        self.uiSpan.editingFinished.connect(self.onNewCenterSpan)
        self.uiCenter.editingFinished.connect(self.onNewCenterSpan)
        
        self.parameter.currentIndexChanged.connect(self.on_parameter_picked)
        self.same.stateChanged.connect(self.on_same_checked)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
    
    def on_parameter_picked(self, index):
        collection, parameter =  self.parameter.itemData(index).toPyObject()
        minim,maxim,units = self.parameter_info[(collection,parameter)]
        self.set_suffix(units)
        self.uiMin.setValue(minim)
        self.uiMax.setValue(maxim)
        self.set_minimum(minim)
        self.set_maximum(maxim)
    
    def on_same_checked(self, checked):
        self.measure.setDisabled(checked)
        index = self.measure.findText(self.scan.text())
        self.measure.setCurrentIndex(index)
    
    def on_new_decimals(self, decimals):
        for widget in [self.uiMin, self.uiMax, self.uiStart, self.uiStop, self.uiCenter, self.uiSpan,
                       self.uiSetResolution, self.uiActualResolution]:
            widget.setSingleStep(10**-decimals)
            widget.setDecimals(decimals)
    
    def set_suffix(self, suffix):
        for widget in [self.uiMin, self.uiMax, self.uiStart, self.uiStop, self.uiCenter, self.uiSpan,
                       self.uiSetResolution, self.uiActualResolution]:
            widget.setSuffix(suffix)
    
    def set_minimum(self, value):
        for widget in [self.uiStart, self.uiStop, self.uiCenter]:
            widget.setMinimum(value)
    
    def set_maximum(self, value):
        for widget in [self.uiStart, self.uiStop, self.uiCenter]:
            widget.setMaximum(value)

    def onNewCenterSpan(self):
        center = self.uiCenter.value()
        span = self.uiSpan.value()
        start = center - span / 2.0
        stop = center + span/2.0
        self.uiStart.setValue(start)
        self.uiStop.setValue(stop)
        self.updateResolutionSteps()

    def onNewStartStop(self):
        start = self.uiStart.value()
        stop = self.uiStop.value()
        self.uiCenter.setValue((start + stop)/2.0)
        self.uiSpan.setValue(stop - start)
        self.updateResolutionSteps()

    def updateResolutionSteps(self):
        '''calculate and update the resolution or the steps depending on which is locked'''
        if self.uiLockSteps.isChecked():
            self.onNewSteps()
        else:
            self.onNewResolution()
            
    def updateActualResolution(self, val):
        self.uiActualResolution.setValue(val)

    def onNewSteps(self):
        steps = self.uiSteps.value()
        start = self.uiStart.value()
        stop = self.uiStop.value()
        res = self._resolution_from_steps(start, stop, steps)
        self.uiSetResolution.setValue(res)
        self.updateActualResolution(res)
        
    def onNewResolution(self):
        '''called when resolution is updated'''
        res = self.uiSetResolution.value()
        start = self.uiStart.value()
        stop = self.uiStop.value()
        steps = self._steps_from_resolution(start, stop, res)
        self.uiSteps.setValue(steps)
        final_res = self._resolution_from_steps(start, stop, steps)
        self.updateActualResolution(final_res)

    def _resolution_from_steps(self, start, stop, steps):
        '''computes the resolution given the number of steps'''
        if steps > 1:
            res = linspace(start, stop, steps, endpoint = True, retstep = True)[1]
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

class repeat_dialog(QtGui.QDialog):
    def __init__(self):
        super(repeat_dialog, self).__init__()
        self.setWindowTitle('Repeat')
        self.setupLayout()
        self.connect_layout()
    
    def setupLayout(self):
        layout = QtGui.QHBoxLayout()
        rep_label = QtGui.QLabel("Repetitions")
        self.repeat = QtGui.QSpinBox()
        self.repeat.setKeyboardTracking(False)
        self.repeat.setRange(1, 10000)
        save_label = QtGui.QLabel("Save Data")
        self.should_save = QtGui.QCheckBox()
        self.should_save.setChecked(True)
        self.okay_button = QtGui.QPushButton('Okay')
        self.cancel_button = QtGui.QPushButton("Cancel")
        layout.addWidget(rep_label)
        layout.addWidget(self.repeat)
        layout.addWidget(save_label)
        layout.addWidget(self.should_save)
        layout.addWidget(self.okay_button)
        layout.addWidget(self.cancel_button)
        self.setLayout(layout)
    
    def connect_layout(self):
        self.okay_button.pressed.connect(self.accept)
        self.cancel_button.pressed.connect(self.reject)

class schedule_dialog(QtGui.QDialog):
    def __init__(self):
        super(schedule_dialog, self).__init__()
        self.setWindowTitle('Schedule')
        self.setupLayout()
        self.connect_layout()
    
    def setupLayout(self):
        layout = QtGui.QHBoxLayout()
        self.duration = QtGui.QSpinBox()
        self.duration.setSuffix(' sec')
        self.duration.setKeyboardTracking(False)
        self.duration.setRange(1, 10000)
        self.okay_button = QtGui.QPushButton('Okay')
        self.cancel_button = QtGui.QPushButton("Cancel")
        self.priority = QtGui.QComboBox()
        self.priority.addItems(['Normal', 'First in Queue','Pause All Others'])
        self.start_immediately = QtGui.QCheckBox()
        self.start_immediately.setCheckable(True)
        self.start_immediately.setChecked(True)
        label = QtGui.QLabel("Period")
        layout.addWidget(label)
        layout.addWidget(self.duration)
        label = QtGui.QLabel("Priority")
        layout.addWidget(label)
        layout.addWidget(self.priority)
        label = QtGui.QLabel("Start Immediately")
        layout.addWidget(label)
        layout.addWidget(self.start_immediately)
        layout.addWidget(self.okay_button)
        layout.addWidget(self.cancel_button)
        self.setLayout(layout)
    
    def connect_layout(self):
        self.okay_button.pressed.connect(self.accept)
        self.cancel_button.pressed.connect(self.reject)

class experiment_selector_widget(QtGui.QWidget):
    
    on_run = QtCore.pyqtSignal(str)
    on_repeat = QtCore.pyqtSignal(str, int, bool)
    on_schedule = QtCore.pyqtSignal(str, float, str, bool)
    on_experiment_selected = QtCore.pyqtSignal(str)
    on_scan = QtCore.pyqtSignal(str, str, tuple, float, float, int, str)
    
    def __init__(self, reactor, parent, font = None):
        self.font = font
        self.reactor = reactor
        self.parent = parent
        self.experiments = []
        super(experiment_selector_widget, self).__init__()
        if self.font is None:
            self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.setupLayout()
        self.connect_layout()
        
    def setupLayout(self):
        layout = QtGui.QGridLayout()
        label = QtGui.QLabel("Experiment", font = self.font)
        self.dropdown = QtGui.QComboBox()
        self.dropdown.setMaxVisibleItems(30)
        self.dropdown.addItem('')#add empty item for no selection state    
        #enable sorting
        sorting_model = QtGui.QSortFilterProxyModel(self.dropdown)
        sorting_model.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        sorting_model.setSourceModel(self.dropdown.model())
        self.dropdown.model().setParent(sorting_model)
        self.dropdown.setModel(sorting_model)
        self.run_button = QtGui.QPushButton("Run")
        self.repeat_button = QtGui.QPushButton("Repeat")
        self.scan_button = QtGui.QPushButton("Scan")
        self.schedule_button = QtGui.QPushButton("Schedule")
        layout.addWidget(label, 0, 0, 1 , 1)
        layout.addWidget(self.dropdown, 0, 1, 1, 3)
        layout.addWidget(self.run_button, 1, 0, 1, 1)
        layout.addWidget(self.repeat_button, 1, 1, 1, 1)
        layout.addWidget(self.scan_button, 1, 2, 1, 1,)
        layout.addWidget(self.schedule_button, 1, 3, 1, 1)
        self.setLayout(layout)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        self.check_button_disable(self.dropdown.currentText())
    
    def clear_all(self):
        self.dropdown.clear()
        self.experiments = []
        self.dropdown.addItem('')#add empty item for no selection state
    
    def connect_layout(self):
        self.run_button.pressed.connect(self.run_emit_selected)
        self.repeat_button.pressed.connect(self.on_repeat_button)
        self.schedule_button.pressed.connect(self.on_schedule_button)
        self.scan_button.pressed.connect(self.on_scan_button)
        self.dropdown.currentIndexChanged[QtCore.QString].connect(self.on_experiment_selected)
        self.dropdown.currentIndexChanged[QtCore.QString].connect(self.check_button_disable)
    
    def check_button_disable(self, selection):
        if not selection:
            for button in [self.run_button, self.repeat_button, self.schedule_button, self.scan_button]:
                button.setDisabled(True)
        else:
            for button in [self.run_button, self.repeat_button, self.schedule_button, self.scan_button]:
                button.setDisabled(False)
        
    def on_schedule_button(self):
        dialog = schedule_dialog()
        if dialog.exec_():
            duration = dialog.duration.value()
            name = self.dropdown.currentText()
            priority = dialog.priority.currentText()
            run_now = dialog.start_immediately.isChecked()
            self.on_schedule.emit(name, duration, priority, run_now)
    
    def on_repeat_button(self):
        dialog = repeat_dialog()
        if dialog.exec_():
            duration = dialog.repeat.value()
            name = self.dropdown.currentText()
            should_save = dialog.should_save.isChecked()
            self.on_repeat.emit(name, duration, should_save)
    
    def on_scan_button(self):
        experiment = self.dropdown.currentText()
        parameter_info = self.parent.get_scannable_parameters()
        dialog = scan_dialog(experiment, self.experiments, parameter_info)
        if dialog.exec_():
            scan = dialog.scan.text()
            measure = dialog.measure.currentText()
            parameter = dialog.get_parameter()
            start = dialog.uiStart.value()
            stop = dialog.uiStop.value()
            steps = dialog.uiSteps.value()
            units = dialog.uiStart.suffix()
            self.on_scan.emit(scan, measure, parameter, start, stop, steps, units)
    
    def run_emit_selected(self):
        self.on_run.emit(self.dropdown.currentText())
    
    def addExperiment(self, experiment):
        self.dropdown.addItem(experiment)
        self.dropdown.model().sort(0)
        self.experiments.append(experiment)
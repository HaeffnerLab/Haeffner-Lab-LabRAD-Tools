from PyQt4 import QtGui, QtCore

class repeat_dialog(QtGui.QDialog):
    def __init__(self):
        super(repeat_dialog, self).__init__()
        self.setupLayout()
        self.connect_layout()
    
    def setupLayout(self):
        layout = QtGui.QHBoxLayout()
        label = QtGui.QLabel("Repetitions")
        self.repeat = QtGui.QSpinBox()
        self.repeat.setKeyboardTracking(False)
        self.repeat.setRange(1, 10000)
        self.okay_button = QtGui.QPushButton('Okay')
        self.cancel_button = QtGui.QPushButton("Cancel")
        layout.addWidget(label)
        layout.addWidget(self.repeat)
        layout.addWidget(self.okay_button)
        layout.addWidget(self.cancel_button)
        self.setLayout(layout)
    
    def connect_layout(self):
        self.okay_button.pressed.connect(self.accept)
        self.cancel_button.pressed.connect(self.reject)

class schedule_dialog(QtGui.QDialog):
    def __init__(self):
        super(schedule_dialog, self).__init__()
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
    on_repeat = QtCore.pyqtSignal(str, int)
    on_schedule = QtCore.pyqtSignal(str, float, str, bool)
    on_experiment_selected = QtCore.pyqtSignal(str)
    
    def __init__(self, reactor, font = None):
        self.font = font
        self.reactor = reactor
        super(experiment_selector_widget, self).__init__()
        if self.font is None:
            self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.setupLayout()
        self.connect_layout()
        
    def setupLayout(self):
        layout = QtGui.QGridLayout()
        label = QtGui.QLabel("Experiment", font = self.font)
        self.dropdown = QtGui.QComboBox()
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
    
    def clear_all(self):
        self.dropdown.clear()
        self.dropdown.addItem('')#add empty item for no selection state    
    
    def connect_layout(self):
        self.run_button.pressed.connect(self.run_emit_selected)
        self.repeat_button.pressed.connect(self.on_repeat_button)
        self.schedule_button.pressed.connect(self.on_schedule_button)
        self.dropdown.currentIndexChanged[QtCore.QString].connect(self.on_experiment_selected)
    
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
            self.on_repeat.emit(name, duration)
    
    def run_emit_selected(self):
        self.on_run.emit(self.dropdown.currentText())
    
    def addExperiment(self, experiment):
        self.dropdown.addItem(experiment)
        self.dropdown.model().sort(0)
from PyQt4 import QtGui, QtCore
from scheduled_widget import scheduled_combined
from running_scans_widget import running_combined
from queued_widget import queued_combined
from experiment_selector_widget import experiment_selector_widget

class scripting_widget(QtGui.QWidget):
    
    on_run = QtCore.pyqtSignal(str)
    on_repeat = QtCore.pyqtSignal((str, int, bool))
    on_scan = QtCore.pyqtSignal(str, str, tuple, float, float, int, str)
    on_cancel_queued = QtCore.pyqtSignal(int)
    on_cancel_scheduled = QtCore.pyqtSignal(int)
    on_schedule = QtCore.pyqtSignal(str,float, str, bool)
    on_schedule_duration = QtCore.pyqtSignal((int, float))
    on_running_stop = QtCore.pyqtSignal(int)
    on_running_pause = QtCore.pyqtSignal(int, bool)
    on_experiment_selected = QtCore.pyqtSignal(str)
        
    def __init__(self, reactor, parent):
        super(scripting_widget, self).__init__()
        self.parent = parent
        self.reactor = reactor
        self.setupLayout()
    
    def setupLayout(self):
        layout = QtGui.QVBoxLayout()
        self.selector = experiment_selector_widget(self.reactor, parent = self)
        self.running = running_combined(self.reactor)
        self.scheduled = scheduled_combined(self.reactor)
        self.queued = queued_combined(self.reactor)
        layout.addWidget(self.selector)
        layout.addWidget(self.scheduled)
        layout.addWidget(self.queued)
        layout.addWidget(self.running)
        self.setLayout(layout)
    
    def get_scannable_parameters(self):
        return self.parent.get_scannable_parameters()
    
    def clear_all(self):
        '''clears all information'''
        self.selector.clear_all()
        self.running.clear_all()
        self.scheduled.clear_all()
        self.queued.clear_all()
    
    #selector
    def addExperiment(self, experiment):
        self.selector.addExperiment(experiment)
    
    #queued
    def addQueued(self, ident, name, order):
        self.queued.add(ident, name, order)
    
    def removeQueued(self, ident):
        self.queued.remove(ident)
        
    #scheduled    
    def addScheduled(self, ident, name, duration):
        self.scheduled.add(ident, name, duration)
    
    def removeScheduled(self, ident):
        self.scheduled.remove(ident)
    
    def newScheduledDuration(self, info):
        ident, duration = info
        self.scheduled.change(ident, duration)
        
    #running
    def runningScriptPaused(self, ident, is_paused):
        self.running.paused(ident, is_paused)
    
    def runningScriptFinished(self, ident):
        self.running.finish(ident)
    
    def addRunning(self, ident, name):
        self.running.add(ident, name)
    
    def runningNewStatus(self, ident, status, percentage):
        self.running.set_status(ident, status, percentage)
     
    def connect_layout(self):
        self.selector.on_run.connect(self.on_run.emit)
        self.selector.on_repeat.connect(self.on_repeat)
        self.selector.on_schedule.connect(self.on_schedule)
        self.selector.on_experiment_selected.connect(self.on_experiment_selected.emit)
        self.selector.on_scan.connect(self.on_scan.emit)
        self.queued.ql.on_cancel.connect(self.on_cancel_queued.emit)
        self.scheduled.sl.on_cancel.connect(self.on_cancel_scheduled.emit)
        self.scheduled.sl.on_new_duration.connect(self.on_schedule_duration.emit)
        self.running.scans_list.on_stop.connect(self.on_running_stop.emit)
        self.running.scans_list.on_pause.connect(self.on_running_pause.emit)
           
    def closeEvent(self, event):
        self.reactor.stop()
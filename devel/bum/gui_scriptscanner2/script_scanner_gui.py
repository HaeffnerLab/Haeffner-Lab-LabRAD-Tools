from PyQt4 import QtGui
from twisted.internet.defer import inlineCallbacks
from scripting_widget import scripting_widget
from common.clients.connection import connection
from tree_view.Controllers import ParametersEditor
from parameter_importer.script_explorer_widget import script_explorer_widget
from scan_widget import scan_widget

class script_scanner_gui(QtGui.QWidget):
    
    SIGNALID = 319245
    
    def __init__(self, reactor, cxn = None):
        super(script_scanner_gui, self).__init__()
        self.cxn = cxn
        self.reactor = reactor
        self.setupWidgets()
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        from labrad.units import WithUnit
        from labrad.types import Error
        self.WithUnit = WithUnit
        self.Error = Error
        self.subscribedScriptScanner = False
        self.subscribedParametersVault = False
        if self.cxn is None:
            self.cxn = connection()
            yield self.cxn.connect()

        self.context = yield self.cxn.context()
        try:
            yield self.populateExperiments()
            yield self.populateParameters()
            yield self.setupListenersScriptScanner()
            yield self.setupListenersParameterVault()
            self.connect_layouts()
        except Exception, e:
            print e
            raise
            print 'script_scanner_gui: servers not available'
            self.disable(True)
        yield self.cxn.add_on_connect('ScriptScanner',self.reinitialize_scriptscanner)
        yield self.cxn.add_on_disconnect('ScriptScanner',self.disable)
    
    @inlineCallbacks
    def reinitialize_scriptscanner(self):
        self.scripting_widget.clear_all()
        yield self.populateExperiments()
        yield self.populateParameters()
        yield self.setupListenersScriptScanner()
        try:
            yield self.cxn.get_server('ScriptScanner')
            self.disable(False)
        except Exception as e:
            print e
            
    def disable(self, should_disable = True):
        if should_disable:
            self.scripting_widget.setDisabled(should_disable)
            self.ParametersEditor.setDisabled(should_disable)
        else:
            self.scripting_widget.setEnabled(True)
            self.ParametersEditor.setEnabled(True)
    
    @inlineCallbacks
    def populateExperiments(self):
        sc = yield self.cxn.get_server('ScriptScanner')
        available = yield sc.get_available_sequences(context = self.context)
        queued = yield sc.get_queue(context = self.context)
        running = yield sc.get_running(context = self.context)
        scheduled = yield sc.get_scheduled(context = self.context)
        for experiment in available:
            self.scripting_widget.addExperiment(experiment)
            scannable_params = yield sc.get_sequence_scannables(experiment)
            self.scan_widget.buildSequenceWidget(experiment, scannable_params)
            
        for ident,name,order in queued:
            self.scripting_widget.addQueued(ident, name, order)
        for ident,name,duration in scheduled:
            self.scripting_widget.addScheduled(ident,name,duration)
        for ident,name in running:
            self.scripting_widget.addRunning(ident,name)
        
    @inlineCallbacks
    def populateParameters(self):
        pv = yield self.cxn.get_server('ScriptScanner')
        collections = yield pv.get_collections(context = self.context)
        for collection in collections:
            self.ParametersEditor.add_collection_node(collection)
            parameters = yield pv.get_parameter_names(collection)
            for param_name in parameters:
                value = yield pv.get_parameter(collection, param_name, False)
                self.ParametersEditor.add_parameter(collection, param_name, value)

    @inlineCallbacks
    def populateUndefinedParameters(self, script):
        pv = yield self.cxn.get_server('ScriptScanner')
        sc = yield self.cxn.get_server('ScriptScanner')
        # these collections already exist in parametervault
        collections = yield pv.get_collections(context = self.context)
        undef = yield sc.get_undefined_parameters(script)
        undef = sorted(undef, key = lambda k: k[0]) # sort by collection
        self.script_explorer.clear()
        for collection, param in undef:
            self.script_explorer.add_parameter(collection, param)
            
    @inlineCallbacks
    def setupListenersScriptScanner(self):
        sc = yield self.cxn.get_server('ScriptScanner')
        #connect server signals
        yield sc.signal_on_queued_new_script(self.SIGNALID, context = self.context)
        yield sc.signal_on_queued_removed(self.SIGNALID + 1, context = self.context)
        yield sc.signal_on_scheduled_new_duration(self.SIGNALID + 2, context = self.context)
        yield sc.signal_on_scheduled_new_script(self.SIGNALID + 3, context = self.context)    
        yield sc.signal_on_scheduled_removed(self.SIGNALID + 4, context = self.context)  
        yield sc.signal_on_running_new_script(self.SIGNALID + 5, context = self.context)
        yield sc.signal_on_running_new_status(self.SIGNALID + 6, context = self.context)
        yield sc.signal_on_running_script_finished(self.SIGNALID + 7, context = self.context)
        yield sc.signal_on_running_script_finished_error(self.SIGNALID + 8, context = self.context)
        yield sc.signal_on_running_script_paused(self.SIGNALID + 9, context = self.context)
        #signals
        if not self.subscribedScriptScanner:
            yield sc.addListener(listener = self.on_new_queued_script, source = None, ID = self.SIGNALID, context = self.context) 
            yield sc.addListener(listener = self.on_removed_queued_sciprt, source = None, ID = self.SIGNALID + 1, context = self.context)   
            yield sc.addListener(listener = self.on_scheduled_new_duration, source = None, ID = self.SIGNALID + 2, context = self.context)
            yield sc.addListener(listener = self.on_scheduled_new_script, source = None, ID = self.SIGNALID + 3, context = self.context)
            yield sc.addListener(listener = self.on_scheduled_removed, source = None, ID = self.SIGNALID + 4, context = self.context)
            yield sc.addListener(listener = self.on_running_new_script, source = None, ID = self.SIGNALID + 5, context = self.context)
            yield sc.addListener(listener = self.on_running_new_status, source = None, ID = self.SIGNALID + 6, context = self.context)
            yield sc.addListener(listener = self.on_running_script_finished, source = None, ID = self.SIGNALID + 7, context = self.context)
            yield sc.addListener(listener = self.on_running_script_finished_error, source = None, ID = self.SIGNALID + 8, context = self.context)
            yield sc.addListener(listener = self.on_running_script_paused, source = None, ID = self.SIGNALID + 9, context = self.context)           
            self.subscribedScriptScanner = True

    @inlineCallbacks
    def setupListenersParameterVault(self):
        pv = yield self.cxn.get_server('ScriptScanner')
        yield pv.signal__parameter_change(self.SIGNALID + 10, context = self.context)
        if not self.subscribedParametersVault:
            yield pv.addListener(listener = self.on_pv_parameter_change, source = None, ID = self.SIGNALID + 10, context = self.context) 
            self.subscribedParametersVault = True
        
    @inlineCallbacks
    def on_pv_parameter_change(self, signal, info):
        collection, name = info
        pv = yield self.cxn.get_server('ScriptScanner')
        full_info = yield pv.get_parameter(collection, name, False, context = self.context)
        self.ParametersEditor.set_parameter(collection, name, full_info)
    
    def get_scannable_parameters(self):
        return self.ParametersEditor.get_scannable_parameters()
    
    def on_running_script_finished_error(self, signal, info):
        ident, message = info
        self.scripting_widget.runningScriptFinished(ident)
        text = "Experiment {0} ended with an error {1}".format(ident, message)
        self.displayError(text)
    
    def on_running_script_paused(self, signal, info):
        self.scripting_widget.runningScriptPaused(*info)
         
    def on_running_script_finished(self, signal, ident):
        self.scripting_widget.runningScriptFinished(ident)

    def on_running_new_script(self, signal, info):
        self.scripting_widget.addRunning(*info)
    
    def on_running_new_status(self, signal, info):
        self.scripting_widget.runningNewStatus(*info)
        
    def on_scheduled_new_duration(self, signal, info):
        self.scripting_widget.newScheduledDuration(info)
        
    def on_scheduled_new_script(self, signal, info):
        self.scripting_widget.addScheduled(*info)
    
    def on_scheduled_removed(self, signal, info):
        self.scripting_widget.removeScheduled(info)
         
    def on_new_queued_script(self, signal, info):
        self.scripting_widget.addQueued(*info)
    
    def on_removed_queued_sciprt(self, signal, ident):
        self.scripting_widget.removeQueued(ident) 
    
    def connect_layouts(self):
        #scripting widget
        self.scripting_widget.connect_layout()
        self.scripting_widget.on_run.connect(self.run_script)
        self.scripting_widget.on_cancel_queued.connect(self.on_cancel_queued)
        self.scripting_widget.on_repeat.connect(self.repeat_script)
        self.scripting_widget.on_schedule.connect(self.schedule_script)
        self.scripting_widget.on_cancel_scheduled.connect(self.scheduled_cancel)
        self.scripting_widget.on_schedule_duration.connect(self.scheduled_duration)
        self.scripting_widget.on_running_stop.connect(self.running_stop)
        self.scripting_widget.on_running_pause.connect(self.running_pause)
        self.scripting_widget.on_experiment_selected.connect(self.on_experiment_selected)
        self.scripting_widget.on_scan.connect(self.scan_script)
        #parameter widget
        self.ParametersEditor.on_parameter_change.connect(self.on_new_parameter)
    
    @inlineCallbacks
    def scan_script(self, scan_script, measure_script, parameter, minim, maxim, steps, units):
        scan_script = str(scan_script)
        measure_script = str(measure_script)
        collection, parameter_name = parameter
        steps = int(steps)
        units = str(units)
        #maxim = float(maxim)
        #minim = float(minim)
        #maxim=U.Value(maxim,units)
        #minim=U.Value(minim,units)
        #steps=U.Value(steps,units)

        sc = yield self.cxn.get_server('ScriptScanner')
        try:
            yield sc.new_script_scan(scan_script, measure_script, collection, parameter_name, minim, maxim, steps, units)
        except self.Error as e:
            self.displayError(e.msg)
    
    @inlineCallbacks
    def on_experiment_selected(self, selected_experiment):
        sc = yield self.cxn.get_server('ScriptScanner')
        selected_experiment = str(selected_experiment)
        self.ParametersEditor.show_all()
        #    try:
        #        parameters = yield sc.get_sequence_parameters(selected_experiment)
        #        yield self.populateUndefinedParameters(selected_experiment)
        #    except self.Error as e:
        #        self.displayError(e.msg)
        #    else:
        #        self.ParametersEditor.show_only(parameters)
        #else:
        #    #empty string corresponds to no selection
        #    self.ParametersEditor.show_all()
    
    @inlineCallbacks
    def on_new_parameter(self, path, value):
        pv = yield self.cxn.get_server('ScriptScanner')
        try:
            yield pv.set_parameter(path[0], path[1], value, True, context = self.context)
        except self.Error as e:
            self.displayError(e.msg)
        except Exception as e:
            print e
    
    @inlineCallbacks
    def running_stop(self, ident):
        sc = yield self.cxn.get_server('ScriptScanner')
        ident = int(ident)
        try:
            yield sc.stop_script(ident)
        except self.Error as e:
            self.displayError(e.msg)
        except Exception as e:
            print e
    
    @inlineCallbacks
    def running_pause(self, ident, should_pause):
        sc = yield self.cxn.get_server('ScriptScanner')
        ident = int(ident)
        try:
            yield sc.pause_script(ident, should_pause)
        except self.Error as e:
            self.displayError(e.msg)
        except Exception as e:
            print e
    
    @inlineCallbacks
    def scheduled_duration(self, ident, duration):
        sc = yield self.cxn.get_server('ScriptScanner')
        ident = int(ident)
        duration = self.WithUnit(float(duration), 's')
        try:
            yield sc.change_scheduled_duration(ident, duration)
        except self.Error as e:
            self.displayError(e.msg)
    
    @inlineCallbacks
    def scheduled_cancel(self, ident):
        ident = int(ident)
        sc = yield self.cxn.get_server('ScriptScanner')
        try:
            yield sc.cancel_scheduled_script(ident)
        except self.Error as e:
            self.displayError(e.msg)
        except Exception as e:
            print e
        
    @inlineCallbacks
    def schedule_script(self, name, duration, priority, start_now):
        sc = yield self.cxn.get_server('ScriptScanner')
        name = str(name)
        priority = str(priority)
        duration = self.WithUnit(duration, 's')
        try:
            yield sc.new_script_schedule(name, duration, priority, start_now)
        except self.Error as e:
            self.displayError(e.msg)
        except Exception as e:
            print e
        
    @inlineCallbacks
    def repeat_script(self, name, repeatitions, save):
        sc = yield self.cxn.get_server('ScriptScanner')
        name = str(name)
        try:
            yield sc.new_script_repeat(name, repeatitions, save)
        except self.Error as e:
            self.displayError(e.msg)
        except Exception as e:
            print e
            
    @inlineCallbacks
    def on_cancel_queued(self, ident):
        sc = yield self.cxn.get_server('ScriptScanner')
        ident = int(ident)
        try:
            yield sc.remove_queued_script(ident, context = self.context)
        except self.Error as e:
            self.displayError(e.msg)
        except Exception as e:
            print e
        
    @inlineCallbacks
    def run_script(self, script):
        sc = yield self.cxn.get_server('ScriptScanner')
        script = str(script)
        try:
            yield sc.new_experiment(script, context = self.context)
        except self.Error as e:
            self.displayError(e.msg)
        except Exception as e:
            print e
               
    def setupWidgets(self):
        self.scripting_widget = scripting_widget(self.reactor, self)
        self.ParametersEditor = ParametersEditor(self.reactor)
        self.scan_widget = scan_widget(self.reactor, self)

        topLevelLayout = QtGui.QHBoxLayout()

        tab = QtGui.QTabWidget()
        control = QtGui.QWidget()
        layout = QtGui.QHBoxLayout()
        
        layout.addWidget(self.scripting_widget)
        layout.addWidget(self.scan_widget)
        #layout.addWidget(self.ParametersEditor)
        control.setLayout(layout)
        self.script_explorer = script_explorer_widget(self)
        tab.addTab(control, 'Scan Control')
        tab.addTab(self.ParametersEditor, 'Parameters')
        tab.addTab(self.script_explorer, 'Parameter Creator')

        topLevelLayout.addWidget(tab)
        self.setLayout(topLevelLayout)
        self.setWindowTitle('Script Scanner Gui')
    
    def displayError(self, text):
        #runs the message box in a non-blocking method
        message = QtGui.QMessageBox(self.scripting_widget)
        message.setText(text)
        message.open()
        message.show()
        message.raise_()
    
    def closeEvent(self, event):
        self.reactor.stop()

if __name__=="__main__":
    a = QtGui.QApplication( ["Script Scanner"] )
    from common.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    gui = script_scanner_gui(reactor)
    gui.show()
    reactor.run()

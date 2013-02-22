from time import localtime, strftime
from numpy import linspace
import labrad
from treedict import TreeDict
from labrad.units import WithUnit

class experiment_info(object):
    '''
    holds informaton about the experiment
    '''
    required_parameters = []
    name = ''
    
    def __init__(self, name = None, required_parameters = None):
        if name is not None:
            self.name = name
        if required_parameters is not None:
            self.required_parameters = required_parameters
        self.parameters = TreeDict()
        
class experiment(experiment_info):
    
    def __init__(self, name = None, required_parameters = None, cxn = None):
        super(experiment, self).__init__(name, required_parameters)
        self.cxn = cxn
        self.pv = None
        self.sc = None
        self.context = None
    
    def _connect(self):
        if self.cxn is None:
            try:
                self.cxn = labrad.connect()
            except Exception as e:
                raise Exception ("Not able to connecto LabRAD")
        try:
            self._define_servers(self.cxn)
        except Exception as e:
            raise Exception ("ScriptScanner or ParameterVault are not running")
    
    def _define_servers(self, cxn):
        self.sc = cxn.servers['ScriptScanner']
        self.pv = cxn.servers['ParameterVault']
        self.context = cxn.context()
    
    def execute(self, ident):
        '''
        executes the experiment
        '''
        self.ident = ident
        try:
            self._connect()
            self._initialize(self.cxn, self.context, ident)
            self._run(self.cxn, self.context)
            self._finalize(self.cxn, self.context)
        except Exception as e:
            print e
            if hasattr(self, 'sc'):
                self.sc.error_finish_confirmed(self.ident, str(e))
        finally:
            if hasattr(self, 'cxn'):
                self.cxn.disconnect()
        
    def _initialize(self, cxn, context, ident):
        self._load_parameters()
        self.initialize(cxn, context, ident)
        self.sc.launch_confirmed(ident)
    
    def _run(self, cxn, context):
        self.run(cxn, context)
    
    def _load_parameters(self, overwrite = False):
        d = self._load_parameters_dict(self.required_parameters)
        self.parameters.update(d, overwrite = overwrite)

    def _load_parameters_dict(self, required):
        '''loads the required parameter into a treedict'''
        d = TreeDict()
        for collection,parameter_name in required:
            try:
                value = self.pv.get_parameter(collection, parameter_name)
            except Exception as e:
                raise Exception ("In {}: Parameter {} not found among Parameter Vault parameters".format(self.name, (collection, parameter_name)))
            else:
                d['{0}.{1}'.format(collection, parameter_name)] = value
        return d
    
    def set_parameters(self, parameter_dict):
        '''
        can reload all parameter values from parameter_vault or replace parameters with values from the provided parameter_dict
        '''
        udpate_dict = TreeDict()
        for (collection,parameter_name), value in parameter_dict.iteritems():
            udpate_dict['{0}.{1}'.format(collection, parameter_name)] = value
            self.parameters.update(udpate_dict)
    
    def reload_parameters_vault(self):
        self._load_parameters(overwrite = True)
    
    def _finalize(self, cxn, context):
        self.finalize(cxn, context)
        self.sc.finish_confirmed(self.ident)
    
    #useful functions to be used in subclasses
    def pause_or_stop(self):
        '''
        allows to pause and to stop the experiment
        '''
        should_stop = self.sc.pause_or_stop(self.ident)
        if should_stop:
            self.sc.stop_confirmed(self.ident)
            return True
    
    def make_experiment(self, subexprt_cls):
        subexprt = subexprt_cls(cxn = self.cxn)
        subexprt._connect()
        subexprt._load_parameters()
        return subexprt
    
    #functions to reimplement in the subclass
    def initialize(self, cxn, context, ident):
        '''
        implemented by the subclass
        '''
    def run(self, cxn, context, replacement_parameters = {}):
        '''
        implemented by the subclass
        '''
    def finalize(self, cxn, context):
        '''
        implemented by the subclass
        '''
        
class single(experiment):
    '''
    runs a single epxeriment
    '''
    def __init__(self, script_cls):
        self.script_cls = script_cls
        super(single,self).__init__(self.script_cls.name)
    
    def initialize(self, cxn, context, ident):
        self.script = self.make_experiment(self.script_cls)
        self.script.initialize(cxn, context, ident)
    
    def run(self, cxn, context, replacement_parameters = {}):
        self.script.run(cxn, context)
    
    def finalize(self, cxn, context):
        self.script.finalize(cxn, context)

class repeat_reload(experiment):
    '''
    Used to repeat an experiment multiple times, while reloading the parameters every repeatition
    '''
    def __init__(self, script_cls, repetitions, min_progress = 0.0, max_progress = 100.0, save_data = False):
        self.script_cls = script_cls
        self.repetitions = repetitions
        self.save_data = save_data
        self.min_progress = min_progress
        self.max_progress = max_progress
        scan_name = self.name_format(script_cls.name)
        super(repeat_reload,self).__init__(scan_name)

    def name_format(self, name):
        return 'Repeat {0} {1} times'.format(name, self.repetitions)
    
    def initialize(self, cxn, context, ident):
        self.script = self.make_experiment(self.script_cls)
        self.script.initialize(cxn, context, ident)
        if self.save_data:
            self.navigate_data_vault(cxn, context)
    
    def run(self, cxn, context):
        for i in range(self.repetitions):
            if self.pause_or_stop(): return
            self.script.reload_parameters_vault()
            result = self.script.run(cxn, context)
            if self.save_data and result is not None:
                cxn.data_vault.add([i, result], context = context)
            self.update_progress(i)
    
    def navigate_data_vault(self, cxn, context):
        dv = cxn.data_vault
        localtime = localtime()
        dataset_name = self.name + strftime("%Y%b%d_%H%M_%S",localtime)
        directory = ['','ScriptScanner']
        directory.extend([strftime("%Y%b%d",localtime), strftime("%H%M_%S", localtime)])
        dv.cd(directory, True, context = context)
        dv.new(dataset_name, [('Iteration', 'Arb')], [self.script.name, 'Arb', 'Arb'])
            
    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / self.repetitions
        self.sc.script_set_progress(self.ident,  progress)
    
    def finalize(self, cxn, context):
        self.script.finalize(cxn, context)
        
class scan_experiment_1D(experiment):
    '''
    Used to repeat an experiment multiple times
    '''
    def __init__(self, script_cls, parameter, minim, maxim, steps, units, min_progress = 0.0, max_progress = 100.0, save_data = False):
        self.script_cls = script_cls
        self.parameter = parameter
        self.scan_points = linspace(minim, maxim, steps)
        self.scan_points = [WithUnit(pt, units) for pt in self.scan_points ]
        self.min_progress = min_progress
        self.max_progress = max_progress
        self.save_data = save_data
        scan_name = self.name_format(script_cls.name)
        super(scan_experiment_1D,self).__init__(scan_name)
        
    def name_format(self, name):
        return 'Scanning {0} in {1}'.format(self.parameter, name)
    
    def initialize(self, cxn, context, ident):
        self.script = self.make_experiment(self.script_cls)
        self.script.initialize(cxn, context, ident)
        if self.save_data:
            self.navigate_data_vault(cxn, context)
    
    def run(self, cxn, context):
        for i, scan_value in enumerate(self.scan_points):
            if self.pause_or_stop(): return
            self.script.set_parameters({self.parameter: scan_value})
            result = self.script.run(cxn, context)
            if self.save_data and result is not None:
                cxn.data_vault.add([i, result], context = context)
            self.update_progress(i)
    
    def navigate_data_vault(self, cxn, context):
        dv = cxn.data_vault
        localtime = localtime()
        dataset_name = self.name + strftime("%Y%b%d_%H%M_%S",localtime)
        directory = ['','ScriptScanner']
        directory.extend([strftime("%Y%b%d",localtime), strftime("%H%M_%S", localtime)])
        dv.cd(directory, True, context = context)
        dv.new(dataset_name, [('Iteration', 'Arb')], [self.script.name, 'Arb', 'Arb'])
            
    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / len(self.scan_points)
        self.sc.script_set_progress(self.ident,  progress)
    
    def finalize(self, cxn, context):
        self.script.finalize(cxn, context)
            
#class excite_D(experiment):
#    
#    name = "Excite D"
#    required_parameters = ['pulse_sequence_repetitions']
#    #required_parameters.extend(self.sequence.all_variables())
#
#    def initialize(self, cxn, context, ident):
#        self.cxn = cxn
#        self.pulser = cxn.pulser
#        self.context = context
#        self.ident = ident
#    
#    def set_parameters(self, parameters):
#        self.pulse_sequence_repetitions = parameters.get('pulse_sequence_repetitions', None)
#    
#    def check_parameters(self):
#        #check self.pulse_sequence_repetitions
#        pass
#    
#    def run(self):
#        #saving and so on
#        pass
#
#class spectrum729(experiment):
#    
#    name = "Spectrum 729"
#    required_parameters = ['line_to_scan', 'should_save_data', 'should_fit']
#    
#    def initiailze(self, cxn, context, ident):
#        self.cxn = cxn
#        self.pulser = cxn.pulser
#        self.context = context
#        self.ident = ident
#        self.fit = None
#        
#    def set_parameters(self , parameters):
#        self.line_to_scan = parameters.get('line_to_scan', None)
#        self.should_save_data = parameters.get('should_save_data', True)
#        self.should_fit = parameters.get('should_fit', False)
#        self.sequence_repetitions = parameters.get('sequence_repetitions', None)
#        
#    def get_fit(self):
#        if self.fit is None:
#            raise Exception("No Fit Available")
#        return self.fit
#    
#    def get_fit_center(self):
#        fit = self.get_fit()
#        return fit[0]#or something
#        
#    def run(self):
#        pass
#    
#    def finalize(self):
#        pass
#    
#class cavity729_drift_track_scans(experiment):
#    
#    name = 'Drift Tracker 729'
#    required_parameters = ['lines_to_scan']
#    
#    def initialize(self, cxn, ident):
#        self.cxn = cxn
#        self.dv = cxn.data_vault
#        self.sd_tracker = cxn.sd_tracker
#        self.spectrum = spectrum729()
#        self.spectrum.initiailze(cxn, cxn.context(), ident)
#    
#    def set_parameters(self, d):
#        self.lines_to_scan = d.get('lines_to_scan', None)
#        
#    def check_parameters(self):
#        if self.lines_to_scan is None:
#            raise Exception("{0}: lines_to_scan parameter not provided".format(self.name)
#        elif not len(self.lines_to_scan) == 2:
#            raise Exception("{0}: incorrect number of lines in lines_to_scan parameter".format(self.name()))
#        transition_names = set(self.sd_tracker.get_transition_names())
#        if not set(self.lines_to_scan).issubset(transition_names):
#            raise Exception("{0}: some names in lines_to_scan are not recognized")
#    
#    def run(self):
#        self.check_parameters()
#        line_centers = []
#        for line in self.lines_to_scan:
#            self.spectrum.set_parameter({'line_to_scan':line})
#            self.spectrum.run()
#            try:
#                center = self.spectrum.get_fit_center()
#                line_centers.append(center)
#            except Exception:
#                #fit not found
#                return
#        submission = zip(self.lines_to_scan, line_centers)
#        self.sd_tracker.submit_line_centers(submission)
#        
#    def finalize(self):
#        self.spectrum.finalize()
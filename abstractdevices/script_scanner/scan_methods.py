from time import localtime, strftime
from numpy import linspace
import labrad
from labrad.units import WithUnit

class experiment_info(object):
    '''
    holds informaton about the experiment
    '''
    required_parameters = []
    required_subexperiments = []
    name = ''
    
    def __init__(self, name = None):
        self.replacement_parameters = {}
        if name is not None:
            self.name = name

class experiment(experiment_info):
    
    def execute(self, ident):
        '''
        executes the experiment
        '''
        self.ident = ident
        cxn = labrad.connect()
        self.sc = cxn.servers['ScriptScanner']
        self.pv = cxn.servers['Parameter Vault']
        context = cxn.context()
        try:
            self._initialize(cxn, context, ident)
            self._run(cxn, context)
            self._finalize(cxn, context)
        except Exception as e:
            print e#temp
            self.sc.error_finish_confirmed(self.ident, str(e))
        finally:
            cxn.disconnect()
        
    def _initialize(self, cxn, context, ident):
        self._load_parameters()
        self.check_parameters_filled()
        self.initialize(cxn, context, ident)
        self.sc.launch_confirmed(ident)
    
    def _run(self, cxn, context):
        self.run(cxn, context)
    
    def _load_parameters(self, overwrite = False):
        for collection,parameter_name in self.required_parameters:
            try:
                value = self.pv.get_parameter(collection, parameter_name)
            except Exception as e:
                raise Exception ("In {}: Parameter {} not found among Parameter Vault parameters".format(self.name, (collection, parameter_name)))
            else:
                already_have = parameter_name in self.__dict__.keys()
                if (already_have and overwrite) or not already_have:
                    self.__dict__[parameter_name] = value
    
    def set_parameters(self, parameter_dict = {}):
        '''
        can reload all parameter values from parameter_vault or replace parameters with values from the provided parameter_dict
        '''
        required = [(self.name, req) for req in self.required_parameters]
        for param,value in parameter_dict.keys():
            if param in required:
                self.pv.check_parameters(param, value)
                self.__dict__[param] = value
    
    def reload_parameters_vault(self):
        self._load_parameters(overwrite = True)
                
    def check_parameters_filled(self):
        for collection, parameter_name in self.required_parameters:
            if parameter_name not in self.__dict__:
                raise Exception("Parameter {0} not provided for experiment {1}".format(parameter, self.name)) 
    
    def _finalize(self, cxn, context):
        self.finalize(cxn, context)
        self.sc.finish_confirmed(self.ident)
        
    def pause_or_stop(self):
        '''
        allows to pause and to stop the experiment
        '''
        should_stop = self.sc.pause_or_stop(self.ident)
        if should_stop:
            self.sc.stop_confirmed(self.ident)
            return True
    
    def initialize(self, cxn, context, ident):
        '''
        implemented by the subclass
        '''
        print 'what?'
        
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
        super(single,self).__init__(script_cls.name())
    
    def initialize(self, cxn, context, ident):
        self.script = self.script_cls()
        self.script.initialize(cxn, context, ident)
    
    def run(self, cxn, context, replacement_parameters = {}):
        self.script.run(cxn, context)
    
    def finalize(self, cxn, context):
        self.script.finalize(cxn, context)

class repeat_reload(experiment):
    '''
    Used to repeat an experiment multiple times, while reloading the parameters every repeatition
    '''
    def __init__(self, script_cls, repeatitions, min_progress = 0.0, max_progress = 100.0, save_data = False):
        self.script_cls = script_cls
        self.repeatitions = repeatitions
        self.save_data = save_data
        self.min_progress = min_progress
        self.max_progress = max_progress
        scan_name = self.name_format(script_cls.name())
        super(repeat_reload,self).__init__(scan_name)

    def name_format(self, name):
        return 'Repeat {0} {1} times'.format(name, self.repeatitions)
    
    def initialize(self, cxn, context, ident):
        self.script = self.script_cls()
        self.script.initialize(cxn, context, ident)
        if self.save_data:
            self.navigate_data_vault(cxn, context)
    
    def run(self, cxn, context):
        for i in range(self.repeatitions):
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
        dv.new(dataset_name, [('Iteration', 'Arb')], [self.script.name(), 'Arb', 'Arb'])
            
    def update_progress(self, iteration):
#        print 'updating progress'
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / self.repeatitions
        self.sc.script_set_progress(self.ident,  progress)
#        print self.ident, progress
    
    def finalize(self, cxn, context):
        self.script.finalize(cxn, context)
        
class scan_experiment_1D(experiment):
    '''
    Used to repeat an experiment multiple times
    '''
    def __init__(self, script_cls, parameter, minim, maxim, steps, units, min_progress = 0.0, max_progress = 100.0, save_data = False):
        self.script_cls = script_cls
        scan_name = self.name_format(script_cls.name())
        super(scan_experiment_1D,self).__init__(scan_name)
        self.parameter = parameter
        self.scan_points = linspace(minim, maxim, steps)
        self.scan_points = [WithUnit(pt, units) for pt in self.scan_points ]
        self.min_progress = min_progress
        self.max_progress = max_progress
        self.save_data = save_data
        
    def name_format(self, name):
        return 'Scanning {0} in {1}'.format(self.parameter, name)
    
    def initialize(self, cxn, context, ident):
        self.script = self.script_cls()
        self.script.initialize(cxn, context, ident)
        if self.save_data:
            self.navigate_data_vault(cxn, context)
    
    def run(self, cxn, context):
        for i in range(self.repeatitions):
            if self.pause_or_stop(): return
            self.script.set_parameters({self.parameter: self.scan_points[i]})
            result = self.script.run()
            if self.data_save and result is not None:
                cxn.data_vault.add([i, result], context = context)
            self.update_progress(i)
    
    def navigate_data_vault(self, cxn, context):
        dv = cxn.data_vault
        localtime = localtime()
        dataset_name = self.name + strftime("%Y%b%d_%H%M_%S",localtime)
        directory = ['','ScriptScanner']
        directory.extend([strftime("%Y%b%d",localtime), strftime("%H%M_%S", localtime)])
        dv.cd(directory, True, context = context)
        dv.new(dataset_name, [('Iteration', 'Arb')], [self.script.name(), 'Arb', 'Arb'])
            
    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / len(self.scan_points)
        self.sc.script_set_progress(self.ident,  progress)
    
    def finalize(self):
        self.script.finalize()
            
#class excite_D(experiment):
#    
#    name = "Excite D"
#    required_parameters = ['pulse_sequence_repeatitions']
#    #required_parameters.extend(self.sequence.all_variables())
#
#    def initialize(self, cxn, context, ident):
#        self.cxn = cxn
#        self.pulser = cxn.pulser
#        self.context = context
#        self.ident = ident
#    
#    def set_parameters(self, parameters):
#        self.pulse_sequence_repeatitions = parameters.get('pulse_sequence_repeatitions', None)
#    
#    def check_parameters(self):
#        #check self.pulse_sequence_repeatitions
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
#    required_subexperiments = [excite_D]
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
#        self.sequence_repeatitions = parameters.get('sequence_repeatitions', None)
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
#    required_subexperiments = [spectrum729]
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
#            raise Exception("{0}: lines_to_scan parameter not provided".format(self.name()))
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
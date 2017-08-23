# wrapper for composite pulse sequences

import numpy as np
from treedict import TreeDict
import labrad
from labrad.units import WithUnit as U
#from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, DeferredList, returnValue, Deferred
from twisted.internet.threads import blockingCallFromThread
import dvParameters
from analysis import readouts
import sys
from sequence_wrapper import pulse_sequence_wrapper

class multi_sequence_wrapper(pulse_sequence_wrapper):
    
    def __init__(self, module, sc, cxn):
        super(multi_sequence_wrapper,self).__init__( module, sc, cxn)
        
        
    #def set_scan(self, scan_param, minim, maxim, steps, unit):
    def set_scan(self, settings):
        self.scans = {}
        for sequence_name, sc in settings:
            param, minim, maxim, steps, unit = sc
            scan = np.arange(minim, maxim, steps)
            scan = [U(pt, unit) for pt in scan]
            self.scans[sequence_name] = (param, unit, scan)
        
        #try:
        #    self.window = self.module.scannable_params[scan_param][1]
        #except:
        #    self.window = 'current' # no window defined
        
        
    def run(self, ident):
        self.ident = ident
        sequences = self.module.sequences
        
        for seq in sequences:
            self.parameter_to_scan, self.scan_unit, self.scan = self.scans[seq.__name__]
            #self.name = seq.__name__
            try:
                self.window = seq.scannable_params[self.parameter_to_scan][1]
            except:
                self.window = 'current'    
            self.run_single(seq)
            
        self.sc._finish_confirmed(self.ident)
            
    def run_single(self, module):
        #import time
        cxn = labrad.connect()
        pulser = cxn.pulser
        self.update_params(self.sc.all_parameters())
        self.setup_data_vault(cxn, module.__name__)

        module.run_initial(cxn, self.parameters_dict)
        self.readout_save_iteration = 0
        print "THIS IS THE MOUDLE RUNNING {}".format(module.__name__)
        print "SCAN:"
        print self.scan
        all_data = [] # 2d numpy array
        for x in self.scan:
            #time.sleep(0.5)
            print " scan param.{}".format(x)
            should_stop = self.sc._pause_or_stop(self.ident)
            if should_stop: break
            update = {self.parameter_to_scan: x}
            self.update_params(update)
            seq = module(self.parameters_dict)
            seq.programSequence(pulser)
            print "programmed pulser"
            self.plot_current_sequence(cxn)
            pulser.start_number(int(self.parameters_dict.StateReadout.repeat_each_measurement))
            print "started {} sequences".format(int(self.parameters_dict.StateReadout.repeat_each_measurement))
            pulser.wait_sequence_done()
            print "done"
            pulser.stop_sequence()
            
            rds = pulser.get_readout_counts()
            ion_state = readouts.pmt_simple(rds, self.parameters_dict.StateReadout.threshold_list)
            submission = [x[self.scan_unit]]
            submission.extend(ion_state)
            
            module.run_in_loop(cxn, self.parameters_dict, submission)
            
            self.dv.add(submission, context = self.data_save_context)
            self.save_data(rds)
            print "done waiting"
                ### program pulser, get readouts
        module.run_finally(cxn, self.parameters_dict, all_data)
        self._finalize_single(cxn)
        
    def _finalize_single(self, cxn):
        # Add finalize the camera when needed 
        dvParameters.saveParameters(self.dv, dict(self.parameters_dict), self.data_save_context)
        cxn.disconnect()

        
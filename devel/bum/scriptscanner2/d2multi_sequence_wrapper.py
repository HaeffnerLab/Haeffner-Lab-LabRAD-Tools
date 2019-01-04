# wrapper for composite pulse sequences

import numpy as np
import cPickle as pickle
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
from configuration import config
from time import sleep

class d2multi_sequence_wrapper(pulse_sequence_wrapper):
    
    def __init__(self, module, sc, cxn):
        super(d2multi_sequence_wrapper,self).__init__( module, sc, cxn)

        
    #def set_scan(self, scan_param, minim, maxim, steps, unit):
    def set_scan(self, settings):
        self.scans = {}

        for sequence_name, sc in settings:
            param, minim, maxim, steps, unit = sc
            
            # maxim+steps is a hack to get plotted data to correspond to usr input range.
            # actually an additional point is being taken
            #scan = np.arange(minim, maxim+steps+1, steps)
            # adding the last element to the scan
            scan = np.arange(minim, maxim, steps)
            scan = np.append(scan,maxim)
            
            scan = [U(pt, unit) for pt in scan]
            
            x = scan[0]
            
            if x.isCompatible('s'): 
                submit_unit = 'us'
                
            elif x.isCompatible('Hz'):
                submit_unit = 'MHz' 
    
            elif x.isCompatible('deg'):
                submit_unit = 'deg' 
                
            else:
                #submit_unit = self.scan_unit
                print "Need to figure out what to do here"
                
            scan_submit = [pt[submit_unit] for pt in scan]
            scan_submit = [U(pt, submit_unit) for pt in scan_submit]
            
            self.scans[sequence_name] = (param, unit, scan, submit_unit, scan_submit)
            print " this is the submit_unit "
            print submit_unit
        #try:
        #    self.window = self.module.scannable_params[scan_param][1]
        #except:
        #    self.window = 'current' # no window defined
        
        
    def run(self, ident):
        self.ident = ident
        sequences = self.module.sequences

        cxn = labrad.connect()

        self.parameter_to_scan_1d, self.scan_unit_1d, self.scan_1d, self.submit_unit_1d, self.scan_submit_1d = self.scans['1d']
        try:
            self.window_1d = self.module.scannable_params[self.parameter_to_scan_1d][1]
        except:
            self.window_1d = 'current'


        self.directory_1d, self.ds_1d, self.data_save_context_1d = self.setup_experiment(cxn, self.scan_1d, self.submit_unit_1d, self.parameter_to_scan_1d, self.module.d1_scan, window = self.window_1d)


        
        for scan_param1 in self.scans['1d'][2]:

            single_results = []

            for seq in sequences:

                if type(seq) == tuple:
                    multisequence_params = seq[1]
                    self.parameter_to_scan, self.scan_unit, self.scan, self.submit_unit, self.scan_submit = self.scans[seq[0].__name__]          
                else:
                    multisequence_params = None
                    self.parameter_to_scan, self.scan_unit, self.scan, self.submit_unit, self.scan_submit = self.scans[seq.__name__]
                
                try:
                    if type(seq) == tuple:
                        self.window = seq[0].scannable_params[self.parameter_to_scan][1]
                    else:
                        self.window = seq.scannable_params[self.parameter_to_scan][1]
                except:
                    self.window = 'current'

        
                # run the single scan 
                should_stop = self.sc._pause_or_stop(self.ident)
                if should_stop: 
                    print " stoping the scan and not proceeding to the next "
                    break

                self.update_params(self.sc.all_parameters())
                update_1d = {self.parameter_to_scan_1d: scan_param1}
                self.update_params(update_1d)
                self.update_scan_param(update_1d)
            
                single_results.append(self.run_single(seq))

            try:
                processed_data = self.module.final_data_process(cxn, single_results)
            except:
            	print "something wrong!@$%^^&**(())"
            	pass
            else:
                submission_1d = [scan_param1[self.submit_unit_1d], processed_data]
                dv = cxn.data_vault
                dv.cd(self.directory_1d, context = self.data_save_context_1d)
                dv.open_appendable(self.ds_1d[1], context = self.data_save_context_1d)
                dv.add(submission_1d, context = self.data_save_context_1d)
        
            
        cxn.disconnect()    

        self.sc._finish_confirmed(self.ident)
            


    def set_multisequence_params(self, params):
        for key, val in params.items():
            d = {}
            if "." in val:
                d[key] = self.parameters_dict[val]
                self.update_params(d)
            else:
                d[key] = val
                self.update_params(d)

            
        

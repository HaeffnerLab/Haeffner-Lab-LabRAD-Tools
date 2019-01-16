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
import inspect

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

        cxn = labrad.connect()

        self.fixed_parameters_dict = TreeDict()

        self.loop_run(self.module, cxn)
            
        cxn.disconnect()    

        self.sc._finish_confirmed(self.ident)


    def loop_run(self, module, cxn):
        if not inspect.ismethod(module.sequence):

            module.run_initial(cxn, self.parameters_dict)

            if module.__name__ not in self.scans.keys() and type(module.sequence) == list:
                seq_results = []
                seq_results_name = []
                self.update_fixed_params(module.fixed_params, overwrite = False)
                self.update_fixed_params(module.fixed_params, overwrite = False)
                current_fixed_parameters_dict = self.fixed_parameters_dict
                for seq in module.sequence:
                    should_stop = self.sc._pause_or_stop(self.ident)
                    if should_stop:
                        print " stoping the scan and not proceeding to the next "
                        break
                    if type(seq) == tuple:
                        self.fixed_parameters_dict = current_fixed_parameters_dict
                        multisequence_params = seq[1]
                        self.set_multisequence_params(multisequence_params, overwrite = False)
                        result = self.loop_run(seq[0], cxn)
                        seq_results.append(result)
                        seq_results_name.append(seq[0].__name__)
                    else:
                        self.fixed_parameters_dict = current_fixed_parameters_dict
                        result = self.loop_run(seq, cxn)
                        seq_results.append(result)
                        seq_results_name.append(seq.__name__)
                    module.run_in_loop(cxn, self.parameters_dict, seq_results, seq_results_name)
                print "!!!!!!!!!!!!!!!!!!!!", seq_results, seq_results_name
                final_result = module.run_finally(cxn, self.parameters_dict, seq_results, seq_results_name)
                return final_result
            elif module.__name__ in self.scans.keys() and not type(module.sequence) == list:
                parameter_to_scan, scan_unit, scan, submit_unit, scan_submit = self.scans[module.__name__]
                try:
                    window = module.scannable_params[parameter_to_scan][1]
                except:
                    window = 'current'
                directory, ds, data_save_context = self.setup_experiment(cxn, scan, submit_unit, parameter_to_scan, module.__name__, window = window)
                results = []
                results_x = []
                self.update_fixed_params(module.fixed_params, overwrite = False)
                self.update_fixed_params(module.fixed_params, overwrite = False)
                for scan_param in scan:
                    print "!!!!!!!!!!!!!!!!!!!!"
                    should_stop = self.sc._pause_or_stop(self.ident)
                    if should_stop:
                        print " stoping the scan and not proceeding to the next "
                        break
                    update = {parameter_to_scan: scan_param}
                    self.update_params(update)
                    self.update_scan_param(update)
                    result = self.loop_run(module.sequence, cxn)
                    results.append(result)
                    results_x.append(scan_param[submit_unit])
                    submission = [scan_param[submit_unit]]
                    submission.append(result)
                    submission = [num for item in submission for num in (item if isinstance(item, list) else (item,))]
                    dv = cxn.data_vault
                    dv.cd(directory, context = data_save_context)
                    dv.open_appendable(ds[1], context = data_save_context)
                    dv.add(submission, context = data_save_context)
                    module.run_in_loop(cxn, self.parameters_dict, results, results_x)
                print "!!!!!!!!!!!!!!!!!!!!", results, results_x
                final_result = module.run_finally(cxn, self.parameters_dict, results, results_x)
                return final_result
            else:
            	raise Exception("please specify either sequence list or scan params")

        else:
            self.parameter_to_scan, self.scan_unit, self.scan, self.submit_unit, self.scan_submit = self.scans[module.__name__]
            try:
                self.window = module.scannable_params[self.parameter_to_scan][1]
            except:
                self.window = 'current'
            self.update_fixed_params(module.fixed_params, overwrite = False)
            self.update_fixed_params(module.fixed_params, overwrite = False)
            self.update_params(self.sc.all_parameters(), overwrite = True)
            self.update_params(self.fixed_parameters_dict, overwrite = True)
            result = self.run_single(module)
            return result


    @inlineCallbacks
    def update_params(self, update, overwrite = True):
        # also update from the drift tracker here?
#        print "UPDATING"
        carrier_translation = {'S+1/2D-3/2':'Carriers.c0',
                               'S-1/2D-5/2':'Carriers.c1',
                               'S+1/2D-1/2':'Carriers.c2',
                               'S-1/2D-3/2':'Carriers.c3',
                               'S+1/2D+1/2':'Carriers.c4',
                               'S-1/2D-1/2':'Carriers.c5',
                               'S+1/2D+3/2':'Carriers.c6',
                               'S-1/2D+1/2':'Carriers.c7',
                               'S+1/2D+5/2':'Carriers.c8',
                               'S-1/2D+3/2':'Carriers.c9',
                               }
        
        update_dict = {}
        carriers_dict = {}
        for key in update.keys():
            if type(key) == tuple:
                print key
                update_dict['.'.join(key)] = update[key]
            else:
                update_dict[key] = update[key]
        


        self.parameters_dict.update(update_dict, overwrite = overwrite)
        
        if self.parameters_dict.DriftTracker.global_sd_enable:
            # using global sd 
            print 'using global sd'
            # there was a problem connecting in the regular sync was we had to establish a
            carriers = yield self.get_lines_from_global_dt()
            if carriers:
                for c, f in carriers:
                    carriers_dict[carrier_translation[c]] = f
        else:
            print "using the local dt"
            if self.dt is not None:
                # connect to drift tracker to get the extrapolated lines
                carriers = yield self.dt.get_current_lines()
                for c, f in carriers:
                    carriers_dict[carrier_translation[c]] = f
                
        
        self.parameters_dict.update(carriers_dict)

    def update_scan_param(self, update, overwrite = True):
        update_dict = {}
        for key in update.keys():
            if type(key) == tuple:
                print key
                update_dict['.'.join(key)] = update[key]
            else:
                update_dict[key] = update[key]
        # self.parameters_dict.update(update)
        self.parameters_dict.update(update_dict, overwrite = overwrite)

    def update_fixed_params(self, update, overwrite = True):
        update_dict = {}
        for key in update.keys():
            if type(key) == tuple:
                print key
                update_dict['.'.join(key)] = update[key]
            else:
                update_dict[key] = update[key]
        # self.parameters_dict.update(update)
        self.fixed_parameters_dict.update(update_dict, overwrite = overwrite)

            


    def set_multisequence_params(self, params, overwrite = True):
        for key, val in params.items():
            d = {}
            if "." in val:
                d[key] = self.parameters_dict[val]
                self.update_fixed_params(d, overwrite)
            else:
                d[key] = val
                self.update_fixed_params(d, overwrite)

            
        

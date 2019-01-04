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

class multi_sequence_wrapper(pulse_sequence_wrapper):
    
    def __init__(self, module, sc, cxn):
        super(multi_sequence_wrapper,self).__init__( module, sc, cxn)
        
        
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

            self.update_params(self.sc.all_parameters())
            if not multisequence_params is None:
                self.set_multisequence_params(multisequence_params)
          
            if not self.parameters_dict.Display.relative_frequencies:
            
                if self.window == "car1":
                    line = self.parameters_dict.DriftTracker.line_selection_1
                    center_frequency = cxn.sd_tracker.get_current_line(line)
                    
                elif self.window == "car2":
                    line = self.parameters_dict.DriftTracker.line_selection_2
                    center_frequency = cxn.sd_tracker.get_current_line(line)
                    
                elif self.window == "spectrum" and self.parameters_dict.Spectrum.scan_selection == "auto":
                    line = self.parameters_dict.Spectrum.line_selection
                    center_frequency = cxn.sd_tracker.get_current_line(line)
                    sideband_selection = self.parameters_dict.Spectrum.sideband_selection
                    trap = self.parameters_dict.TrapFrequencies
                     
                    center_frequency = self.add_sidebands(center_frequency, sideband_selection, trap)
     
                else:
                    center_frequency = U(0., self.submit_unit)    
            
            else:
                center_frequency = U(0., self.submit_unit)
            
            self.center_frequency = center_frequency
            
            
            # run the single scan 
            should_stop = self.sc._pause_or_stop(self.ident)
            if should_stop: 
                print " stoping the scan and not proceeding to the next "
                break
            
            self.run_single(seq)
        
            
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

            
        

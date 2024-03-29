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
            
    def run_single(self, module):
        
        cxn = labrad.connect()
        pulser = cxn.pulser
        
        self.update_params(self.sc.all_parameters())
        if type(module) == tuple:
            multisequence_params = module[1]
            self.set_multisequence_params(multisequence_params)
            module = module[0]
            
        self.setup_data_vault(cxn, module.__name__)

       
               
        if 'camera' in self.parameters_dict.StateReadout.readout_mode: 
            self.use_camera = True
            self.initialize_camera(cxn)
            camera = cxn.andor_server
        else:
            self.use_camera = False



        module.run_initial(cxn, self.parameters_dict)
        self.readout_save_iteration = 0
        
        all_data = [] # 2d numpy array
        data_x = []
        data = [] 
        
        

        for x in self.scan:
            print " scan param.{}".format(x)
            should_stop = self.sc._pause_or_stop(self.ident)
            if should_stop: break
            update = {self.parameter_to_scan: x}
            self.update_params(update)
            self.update_scan_param(update)
            seq = module(self.parameters_dict)
            seq.programSequence(pulser)
            print "programmed pulser"          
            self.plot_current_sequence(cxn)
            
            repetitions=int(self.parameters_dict.StateReadout.repeat_each_measurement)
            if self.use_camera:
                
                exposures = repetitions 
                camera.set_number_kinetics(exposures)
                camera.start_acquisition()
                
            
            pulser.start_number(int(self.parameters_dict.StateReadout.repeat_each_measurement))
            print "started {} sequences".format(int(self.parameters_dict.StateReadout.repeat_each_measurement))
            pulser.wait_sequence_done()
            pulser.stop_sequence()
            
            if not self.use_camera:
                readout_mode=self.parameters_dict.StateReadout.readout_mode 
                rds = pulser.get_readout_counts()
                ion_state = readouts.pmt_simple(rds, self.parameters_dict.StateReadout.threshold_list,readout_mode)
                self.save_data(rds)
                data.append(ion_state)
                
            else:
                #get the percentage of excitation using the camera state readout
                proceed = camera.wait_for_kinetic()
                
                if not proceed:
                    camera.abort_acquisition()
                    self._finalize_single(cxn)
                    raise Exception ("Did not get all kinetic images from camera")
                
                images = camera.get_acquired_data(exposures)
                camera.abort_acquisition()
                
                if self.name == 'ReferenceImage':
                    data=images
                    ion_state=np.ones(self.parameters_dict.IonsOnCamera.ion_number)
                else:
                    ion_state, cam_readout, confidences = readouts.camera_ion_probabilities(images, exposures, self.parameters_dict.IonsOnCamera,self.parameters_dict.StateReadout.readout_mode)
                    self.save_confidences(confidences)
                    data.append(ion_state)
                
                #useful for debugging, saving the images
                #numpy.save('readout {}'.format(int(time.time())), images)
            x_shift=self.Scan_shift()
            
            submission = [x[self.submit_unit]+x_shift[self.submit_unit]]  # + center_frequency[self.submit_unit]]
            submission.extend(ion_state)
            data_x.append(x[self.submit_unit] + x_shift[self.submit_unit])
            
            module.run_in_loop(cxn, self.parameters_dict, np.array(data),np.array(data_x))
            #submit the results to the data vault
            self.dv.add(submission, context = self.data_save_context)
                
           
               
                        
        module.run_finally(cxn, self.parameters_dict, np.array(data), np.array(data_x))
        self._finalize_single(cxn)
        
    def _finalize_single(self, cxn):
        # Add finalize the camera when needed 
        
        
#        import time
        # Bypass configParser and save parameters as a pickled dict
        if self.parameters_dict.global_scan_options.quick_finish:
#           t0 = time.time()
            d = self.readout_save_directory
            loc = "/home/lattice/data/" + ".dir/".join(d[1:]) + ".dir/00001 - %s.pickle" %d[-1] 
            pickle_out = open(loc, "wb")
            pickle.dump(dict(self.parameters_dict), pickle_out)
            pickle_out.close()
#            t1 = time.time()
#            print "TIME", t1-t0
            
        
        else:
#            t0 = time.time()
            dvParameters.saveParameters(self.dv, dict(self.parameters_dict), self.data_save_context)
#            t1 = time.time()
#            print "TIME", t1-t0
        
        # Add finalize the camera when needed 
#         self.sc._finish_confirmed(self.ident)
        
        
        if self.use_camera:
            #if used the camera, return it to the original settings
            camera = cxn.andor_server
            camera.set_trigger_mode(self.initial_trigger_mode)
            camera.set_exposure_time(self.initial_exposure)
            camera.set_image_region(self.initial_region)
            if self.camera_initially_live_display:
                camera.start_live_display()
                
        cxn.disconnect()


    def set_multisequence_params(self, params):
        for key, val in params.items():
            d = {}
            if "." in val:
                d[key] = self.parameters_dict[val]
                self.update_params(d)
            else:
                d[key] = val
                self.update_params(d)

            
        

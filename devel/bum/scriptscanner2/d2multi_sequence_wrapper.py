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
        
    def setup_experiment(self, cxn, scan, unit, parameter_to_scan ='param', dependents_name = 'default', num_of_params_to_sub =1, window = 'current'):
        # paramter to scan
        # sets up the data vault 
        # setup the grapher
        import time
        
        dv = cxn.data_vault
        grapher = cxn.grapher
        
        localtime = time.localtime()
        timetag = time.strftime('%H%M_%S', localtime)
        directory = ['', 'Experiments', time.strftime('%Y%m%d', localtime), self.module.__name__, timetag]
        data_save_context_extra = cxn.context()       
        dv.cd(directory, True, context = data_save_context_extra)
        
        # creating the col names in the output file
        dependents = [('', dependents_name+'{}'.format(x), '') for x in range(num_of_params_to_sub)]
                
        ds = dv.new( timetag ,[(parameter_to_scan, unit)],dependents, context = data_save_context_extra )
        
        
        if grapher is not None:           
            grapher.plot_with_axis(ds, window, scan) # -> plot_with_axis
        
        return directory, ds, data_save_context_extra
        
    def run(self, ident):
        self.ident = ident

        cxn = labrad.connect()

        self.fixed_parameters_dict = TreeDict()

        self.scan_structure = self.get_scan_structure(self.module)

        print "Scan tructure: ", self.scan_structure

        self.total_scan = self.calc_total_scan(self.scan_structure)

        print "Total scan rounds: ", self.total_scan

        status_list = []

        self.loop_run(self.module, cxn, status_list)
            
        cxn.disconnect()    

        self.sc._finish_confirmed(self.ident)


    def loop_run(self, module, cxn, lis):
        if not inspect.ismethod(module.sequence):

            module.run_initial(cxn, self.parameters_dict)

            if module.__name__ not in self.scans.keys() and type(module.sequence) == list:
                seq_results = []
                seq_results_name = []
                self.update_fixed_params(module.fixed_params, overwrite = False)
                self.update_fixed_params(module.fixed_params, overwrite = False)
                current_fixed_parameters_dict = self.fixed_parameters_dict.copy(deep = True)
                for index, seq in enumerate(module.sequence):
                    lis1 = lis + [index]
                    self.should_stop = self.sc._pause_or_stop(self.ident)
                    if self.should_stop:
                        print " stoping the scan and not proceeding to the next "
                        break
                    if type(seq) == tuple:
                        self.fixed_parameters_dict = current_fixed_parameters_dict.copy(deep = True)
                        multisequence_params = seq[1]
                        self.set_multisequence_params(multisequence_params, overwrite = False)
                        result = self.loop_run(seq[0], cxn, lis1)
                        seq_results.append(result)
                        seq_results_name.append(seq[0].__name__)
                    else:
                        self.fixed_parameters_dict = current_fixed_parameters_dict.copy(deep = True)
                        result = self.loop_run(seq, cxn, lis1)
                        seq_results.append(result)
                        seq_results_name.append(seq.__name__)
                    module.run_in_loop(cxn, self.parameters_dict, seq_results, seq_results_name)
                if not self.should_stop:
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
                current_fixed_parameters_dict = self.fixed_parameters_dict.copy(deep = True)
                for index, scan_param in enumerate(scan):
                    lis1 = lis + [index]
                    self.should_stop = self.sc._pause_or_stop(self.ident)
                    if self.should_stop:
                        print " stoping the scan and not proceeding to the next "
                        break
                    self.fixed_parameters_dict = current_fixed_parameters_dict.copy(deep = True)
                    update = {parameter_to_scan: scan_param}
                    self.update_fixed_params(update)
                    result = self.loop_run(module.sequence, cxn, lis1)
                    if not self.should_stop:
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
                if not self.should_stop:
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
            print "fixed params for {} scan:",format(module.__name__), self.fixed_parameters_dict.makeReport()
            result = self.run_single(module, lis)
            return result

    def run_single(self, module, lis):
        
        cxn = labrad.connect()
        pulser = cxn.pulser
        
        # self.update_params(self.sc.all_parameters())
        
        print "!!!!!readout mode:",self.parameters_dict.StateReadout.readout_mode
            
        self.setup_data_vault(cxn, module.__name__)

       
               
        if 'camera' in self.parameters_dict.StateReadout.readout_mode: 
            self.use_camera = True
            self.initialize_camera(cxn)
            camera = cxn.andor_server
        else:
            self.use_camera = False



        module.run_initial(cxn, self.parameters_dict)
        self.readout_save_iteration = 0

        data_x = []
        data = [] 
        
        

        for index, x in enumerate(self.scan):

            print " scan param.{}".format(x)
            self.should_stop = self.sc._pause_or_stop(self.ident)
            if self.should_stop: break
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
            self.dv.cd(self.readout_save_directory, context = self.data_save_context)
            self.dv.open_appendable(self.ds[1], context = self.data_save_context)
            self.dv.add(submission, context = self.data_save_context)

            lis1 = lis + [index + 1]
            temp_structure = self.scan_structure    
            progress = 100 * self.calc_current_step(temp_structure, lis1)/self.total_scan
            print "Current progress: {}%".format(progress)
            self.sc.sequence_set_progress(None, self.ident, progress)
           
        if not self.should_stop:                
            single_result = module.run_finally(cxn, self.parameters_dict, np.array(data), np.array(data_x))
            self._finalize_single(cxn)
            self.sc.save_parameters()

            return single_result


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
        print "fixed_params!!!!!!!!!!!!!!!!!!!", update_dict

            


    def set_multisequence_params(self, params, overwrite = True):
        for key, val in params.items():
            d = {}
            if type(val) == str and "." in val:
                d[key] = self.parameters_dict[val]
                self.update_fixed_params(d, overwrite)
            else:
                d[key] = val
                self.update_fixed_params(d, overwrite)

    def get_scan_structure(self, module):
        if not inspect.ismethod(module.sequence):
            if type(module.sequence) == type:
                dic = {}
                scan_rep = len(self.scans[module.__name__][2])
                dic[scan_rep] = self.get_scan_structure(module.sequence)
                return dic
            elif type(module.sequence) == list:
                li = []
                for seq in module.sequence:
                    if type(seq) == tuple:
                        li.append(self.get_scan_structure(seq[0]))
                    else:
                        li.append(self.get_scan_structure(seq))
                return li
        else:
            return len(self.scans[module.__name__][2])

    def calc_total_scan(self, structure):
        if type(structure) == dict:
            temp = self.calc_total_scan(structure.values()[0])
            return structure.keys()[0] * temp
        elif type(structure) == list:
            n = 0
            for i in structure:
                temp = self.calc_total_scan(i)
                n += temp
            return n
        elif type(structure) == int:
            return structure

    def calc_current_step(self, structure, prog_li):
        prog = 0
        for i in prog_li:
            if type(structure) == dict:
                structure = structure.values()[0]
                res = i * self.calc_total_scan(structure)
                prog += res
            elif type(structure) == list:
                for j in range(i):
                    res = self.calc_total_scan(structure[j])
                    prog += res
                structure = structure[i]
            elif type(structure) == int:
                prog += i
        return prog

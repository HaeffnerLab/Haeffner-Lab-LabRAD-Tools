"""
     Wrapper class for pulse sequences

Current idea:
pulse sequence is a pure python file which gets parsed
by the wrapper class.

script scanner will generate a pulse_sequence_wrapper object
on the fly, passing the pulse sequence definition module
path to the pulse sequence definition file,
as well as the current parameter vault downloaded as a TreeDict

1. First parse which parameters are scannable out of the XML definition file
2. GUI takes these parameters to show

Generate sequence. First pass ENTIRE parameter vault parameters
to the sequence object

"""
import numpy as np
import cPickle as pickle
from time import sleep
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
import time
from common.client_config import client_info as dt_config
from configuration import config
import inspect
import traceback


class pulse_sequence_wrapper(object):
    
    def __init__(self, module, sc, cxn):
        self.module = module # pulse sequence module
        self.name = module.__name__
        # copy the parameter vault dict by value
        self.parameters_dict = TreeDict()
        self.show_params = module.show_params
        self.scan = None
        self.sc = sc # reference to scriptscanner class, not through the labrad connection
        self.cxn = cxn
        # try:

        #     self.dt = self.cxn.sd_tracker
        # except:
        #     self.dt = None
        try:
            self.grapher = cxn.grapher
        except:
            self.grapher = None
        self.total_readouts = []


    def set_scan(self, settings):
        #not used currently?? - sara
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
            
                
            if x.isCompatible('Hz'):
                submit_unit = 'MHz' 

             # elif x.isCompatible('s'): 
            #     submit_unit = 'us'               
    
            elif x.isCompatible('deg'):
                submit_unit = 'deg' 
                
            else:
                submit_unit = unit
                
            scan_submit = [pt[submit_unit] for pt in scan]
            scan_submit = [U(pt, submit_unit) for pt in scan_submit]
            
            self.scans[sequence_name] = (param, unit, scan, submit_unit, scan_submit)
            # print " this is the submit_unit "
            # print submit_unit
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
        directory = ['', 'Experiments', time.strftime('%Y%m%d', localtime), dependents_name, timetag]
        data_save_context_extra = cxn.context()       
        dv.cd(directory, True, context = data_save_context_extra)
        
        # creating the col names in the output file
        dependents = [('', dependents_name+'{}'.format(x), '') for x in range(num_of_params_to_sub)]
                
        ds = dv.new( timetag ,[(parameter_to_scan, unit)],dependents, context = data_save_context_extra )
        
        if self.do_shift:
            pv = cxn.parametervault
            shift = pv.get_parameter('Display','shift') # where shift is set in the experiment. 
        if grapher is not None:           
            grapher.plot_with_axis(ds, window, scan) # -> plot_with_axis
        
        return directory, ds, data_save_context_extra
        
        
    def run(self, ident):
        self.ident = ident

        cxn = labrad.connect()

        try:

            # define a new parameter dict to allow non-overwrite update
            self.fixed_parameters_dict = TreeDict()

            # get scan structure, 
            # i.e. {5:[10,20]} means scan two sequences for 5 times, 
            # sequence1 contains 10 repititions, sequence2 contains 20 repititions
            self.scan_structure = self.get_scan_structure(self.module)
            print "Scan structure: ", self.scan_structure

            # calculate total repititions from scan structure
            self.total_scan = self.calc_total_scan(self.scan_structure)
            print "Total scan rounds: ", self.total_scan

            # status_list defines current status
            status_list = []

            # call loop function to generate complicated scan
            self.loop_run(self.module, cxn, status_list)
            self.sc._finish_confirmed(self.ident)

        except Exception as e:
            reason = traceback.format_exc()
            print reason
            self.sc.error_finish_confirmed(None, self.ident, reason)

        cxn.disconnect()


    def loop_run(self, module, cxn, lis):
        '''
        Generate complicated scan loops by calling itself 
        '''

        # judge if module.sequence is a function
        if not inspect.ismethod(module.sequence):

            # non-overwrite update
            self.update_fixed_params(module.fixed_params, overwrite = False)
            self.update_fixed_params(module.fixed_params, overwrite = False)
            self.update_params(self.sc.all_parameters(), overwrite = True)
            self.update_params(self.fixed_parameters_dict, overwrite = True)

            module.run_initial(cxn, self.parameters_dict)

            # module.sequence == list indicates multi sequence scan
            if module.__name__ not in self.scans.keys() and type(module.sequence) == list:
                seq_results = []
                seq_results_name = []
                self.update_fixed_params(module.fixed_params, overwrite = False)
                self.update_fixed_params(module.fixed_params, overwrite = False)

                # save fixed parameter dict before multi sequence scan
                # to avoid conflict between sequences
                current_fixed_parameters_dict = self.fixed_parameters_dict.copy(deep = True)
                for index, seq in enumerate(module.sequence):

                    # pass number of current scan status
                    lis1 = lis + [index]

                    # check if should stop
                    self.should_stop = self.sc._pause_or_stop(self.ident)
                    if self.should_stop:
                        print " stopping the scan and not proceeding to the next "
                        break

                    # if elements in sequence list is tuple, it contains fixed parameters
                    if type(seq) == tuple:

                        # restore to the copy of fixed parameter dict before subsequence parameter update
                        self.fixed_parameters_dict = current_fixed_parameters_dict.copy(deep = True)

                        # update fixed parameter for subsequence in sequence list
                        multisequence_params = seq[1]
                        self.set_multisequence_params(multisequence_params, overwrite = False)

                        # run subsequence
                        result = self.loop_run(seq[0], cxn, lis1)
                        seq_results.append(result)
                        seq_results_name.append(seq[0].__name__)

                    # if elements in sequence is class, there is no fixed parameters
                    elif type(seq) == type:

                        # restore to the copy of fixed parameter dict before subsequence parameter update
                        self.fixed_parameters_dict = current_fixed_parameters_dict.copy(deep = True)

                        # run subsequence
                        result = self.loop_run(seq, cxn, lis1)
                        seq_results.append(result)
                        seq_results_name.append(seq.__name__)

                    else:
                        raise Exception("Wrong type of sequence inside sequence list")

                    module.run_in_loop(cxn, self.parameters_dict, seq_results, seq_results_name)

                # process data using run_finally function if should not stop, 
                # to eliminate possible errors in data propagation 
                if not self.should_stop:
                    print "Results for {} !!!!!!!!!!!!!!!!!!!!".format(module.__name__), seq_results, seq_results_name
                    final_result = module.run_finally(cxn, self.parameters_dict, seq_results, seq_results_name)
                    return final_result

            # module.sequence == class indicates higher dimensional scan
            elif module.__name__ in self.scans.keys() and not type(module.sequence) == list:
                parameter_to_scan, scan_unit, scan, submit_unit, scan_submit = self.scans[module.__name__]
                try:
                    window = module.scannable_params[parameter_to_scan][1]
                except:
                    window = 'current'
                directory =  ds = data_save_context = None
                results = []
                results_x = []
                self.update_fixed_params(module.fixed_params, overwrite = False)
                self.update_fixed_params(module.fixed_params, overwrite = False)

                # copy fixed parameters before scan, make sure no conflict between subscan sequence fixed parameters
                current_fixed_parameters_dict = self.fixed_parameters_dict.copy(deep = True)
                for index, scan_param in enumerate(scan):

                    # pass number of current scan status
                    lis1 = lis + [index]

                    # check if should stop
                    self.should_stop = self.sc._pause_or_stop(self.ident)
                    if self.should_stop:
                        print " stoping the scan and not proceeding to the next "
                        break

                    # restore to the copy of fixed parameter dict before subsequence parameter update
                    self.fixed_parameters_dict = current_fixed_parameters_dict.copy(deep = True)

                    # update scan parameter
                    # need to overwrite
                    update = {parameter_to_scan: scan_param}
                    self.update_fixed_params(update)

                    # run subsequence
                    result = self.loop_run(module.sequence, cxn, lis1)
                    results.append(result)
                    results_x.append(scan_param[submit_unit])

                    # submit result to data vault if should not stop
                    if not self.should_stop:
                        submission = [scan_param[submit_unit]]
                        submission.append(result)
                        submission = [num for item in submission for num in (item if isinstance(item, list) or isinstance(item, tuple) else (item,))]
                        if not ds:
                            directory, ds, data_save_context = self.setup_experiment(cxn, scan, submit_unit, parameter_to_scan = parameter_to_scan, dependents_name = module.__name__, num_of_params_to_sub = len(submission)-1, window = window)
                        dv = cxn.data_vault
                        dv.cd(directory, context = data_save_context)
                        dv.open_appendable(ds[1], context = data_save_context)
                        dv.add(submission, context = data_save_context)
                        module.run_in_loop(cxn, self.parameters_dict, results, results_x)

                # process data using run_finally function if should not stop, 
                # to eliminate possible errors in data propagation 
                if not self.should_stop:
                    print "Results for {} !!!!!!!!!!!!!!!!!!!!".format(module.__name__), results, results_x
                    final_result = module.run_finally(cxn, self.parameters_dict, results, results_x)
                    return final_result

            else:
                raise Exception("please specify either sequence list or scan params")

        # if sequence is function, it is a fundamental sequence
        else:
            self.parameter_to_scan, self.scan_unit, self.scan, self.submit_unit, self.scan_submit = self.scans[module.__name__]
            try:
                self.do_shift = module.scannable_params[self.parameter_to_scan][2]
            except:
                self.do_shift = False
            try:
                self.window = module.scannable_params[self.parameter_to_scan][1]
            except:
                self.window = 'current'


            # non-overwrite update
            self.update_fixed_params(module.fixed_params, overwrite = False)
            self.update_fixed_params(module.fixed_params, overwrite = False)
            self.update_params(self.sc.all_parameters(), overwrite = True)
            self.update_params(self.fixed_parameters_dict, overwrite = True)

            # print final version of fixed parameter dict before a fundamental sequence run
            print "fixed params for {} scan: ".format(module.__name__), self.fixed_parameters_dict.makeReport()

            # run fundamental sequence
            result = self.run_single(module, lis)
            return result

    def run_single(self, module, lis):

        
        cxn = labrad.connect()
        pulser = cxn.pulser

        print "!!!!!readout mode:",self.parameters_dict.StateReadout.readout_mode
          
        if 'camera' in self.parameters_dict.StateReadout.readout_mode: 
            self.use_camera = True
            self.initialize_camera(cxn)
            camera = cxn.andor_server
        else:
            self.use_camera = False

        sleep(1)
        module.run_initial(cxn, self.parameters_dict)
        self.setup_data_vault(cxn, module.__name__)

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
            x_shift=self.Scan_shift(cxn)
            
            submission = [x[self.submit_unit]+x_shift[self.submit_unit]]  # + center_frequency[self.submit_unit]]
            submission.extend(ion_state)
            data_x.append(x[self.submit_unit] + x_shift[self.submit_unit])
            
            module.run_in_loop(cxn, self.parameters_dict, np.array(data),np.array(data_x))
            #submit the results to the data vault
            self.dv.cd(self.readout_save_directory, context = self.data_save_context)
            self.dv.open_appendable(self.ds[1], context = self.data_save_context)
            self.dv.add(submission, context = self.data_save_context)

            # calculate current progress
            lis1 = lis + [index + 1]
            temp_structure = self.scan_structure    
            progress = 100 * self.calc_current_step(temp_structure, lis1)/self.total_scan
            print "Current progress: {}%".format(progress)
            self.sc.sequence_set_progress(None, self.ident, progress)
                          
        single_result = module.run_finally(cxn, self.parameters_dict, np.array(data), np.array(data_x))
        self._finalize_single(cxn)
        self.sc.save_parameters()

        return single_result


    def _finalize_single(self, cxn):
        # Add finalize the camera when needed 
        
        
        # Bypass configParser and save parameters as a pickled dict
        if self.parameters_dict.global_scan_options.quick_finish:
#            t0 = time.time()
            d = self.readout_save_directory
            loc = config.quick_finish_path + ".dir/".join(d[1:]) + ".dir/00001 - %s.pickle" %d[-1] 
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
        
        
        if self.use_camera:
            #if used the camera, return it to the original settings
            camera = cxn.andor_server
            camera.set_trigger_mode(self.initial_trigger_mode)
            camera.set_exposure_time(self.initial_exposure)
            camera.set_image_region(self.initial_region)
            if self.camera_initially_live_display:
                camera.start_live_display()      
        cxn.disconnect()



    @inlineCallbacks
    def update_params(self, update, overwrite = True):
        # also update from the drift tracker here?
        print "UPDATING"
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
        
        # using global sd 
        # there was a problem connecting in the regular sync was we had to establish a
        #print "trying"
        carriers = yield self.get_lines_from_global_dt()
        if carriers:
            for c, f in carriers:
                carriers_dict[carrier_translation[c]] = f
        
        self.parameters_dict.update(carriers_dict)


    @inlineCallbacks
    def get_lines_from_global_dt(self):
        # added this function to support async connection to the 
        from labrad.wrappers import connectAsync
        try:
            print "connecting async to global sd"
            global_sd_cxn = yield connectAsync(dt_config.global_address, password = dt_config.global_password,tls_mode='off')
            carriers =  yield global_sd_cxn.sd_tracker_global.get_current_lines(dt_config.client_name)
            # need to add some delay time because it casues a problem with the camera ????
            yield global_sd_cxn.disconnect()
            sleep(0.05)
            # print carriers 
        except:
            print "Problem with the global_sd. Make sure you have submitted a line."
        else:
            returnValue(carriers)


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




    def save_data(self, readouts):
        #save the current readouts
        iters = np.ones_like(readouts) * self.readout_save_iteration
        self.dv.add(np.vstack((iters, readouts)).transpose(), context = self.readout_save_context)
        self.readout_save_iteration += 1
        self.total_readouts.extend(readouts)
        if (len(self.total_readouts) >= 500):
            hist, bins = np.histogram(self.total_readouts, 50)
            self.dv.cd(self.readout_save_directory ,True, context = self.histogram_save_context)
            self.dv.new('Histogram',[('Counts', 'Arb')],[('Occurence','Arb','Arb')], context = self.histogram_save_context )
            self.dv.add(np.vstack((bins[0:-1],hist)).transpose(), context = self.histogram_save_context )
            self.dv.add_parameter('Histogram729', True, context = self.histogram_save_context )
            self.total_readouts = []
    
    def save_confidences(self, confidences):
        '''
        saves confidences readings for the camera state detection
        '''
        self.total_camera_confidences.extend(confidences)
        if (len(self.total_camera_confidences) >= 300):
            hist, bins = np.histogram(self.total_camera_confidences, 30)
            self.dv.cd(self.readout_save_directory ,True, context = self.histogram_save_context)
            #self.dv.new('Histogram Camera {}'.format(self.datasetNameAppend),[('Counts', 'Arb')],[('Occurence','Arb','Arb')], context = self.histogram_save_context )
            self.dv.new('Histogram Camera',[('Counts', 'Arb')],[('Occurence','Arb','Arb')], context = self.histogram_save_context )
            self.dv.add(np.vstack((bins[0:-1],hist)).transpose(), context = self.histogram_save_context )
            self.dv.add_parameter('HistogramCameraConfidence', True, context = self.histogram_save_context )
            self.total_camera_confidences = []


    def setup_data_vault(self, cxn, name):
        
        localtime = time.localtime()
        self.dv = cxn.data_vault
        self.timetag = time.strftime('%H%M_%S', localtime)
        print self.parameters_dict.global_scan_options.save_folder
        if self.parameters_dict.global_scan_options.save_folder == 'date':
            directory = ['', 'Experiments', time.strftime('%Y%m%d', localtime), name, self.timetag]
        elif self.parameters_dict.global_scan_options.save_folder == 'experiment':
            directory = ['', 'Experiments', name, time.strftime('%Y%m%d', localtime), self.timetag]
        else:
            directory = []
            print "saving convention not recognized. check global_scan_options.save_folder"
        self.data_save_context = cxn.context()
        self.readout_save_context = cxn.context()
        self.histogram_save_context = cxn.context()
        self.dv.cd(directory, True, context = self.data_save_context)
        
        # creating the col names in the output file
        #dependents = [('', 'Col {}'.format(x), '') for x in range(self.output_size())]
        dependents = self.col_names()
       
        self.ds = self.dv.new(self.timetag, [(self.parameter_to_scan, self.submit_unit)], dependents, context = self.data_save_context)
        
        shift=U(0,self.submit_unit)

        if self.do_shift:
            pv = cxn.parametervault
            shift = pv.get_parameter('Display','shift') # where shift is set in the experiment.
        
        # if not self.parameters_dict.Display.relative_frequencies:
        #     # using global sd 
        #     print 'using global sd'
        #     # cannot use asynchrounous connection here
        #     # from labrad.wrappers import connectAsync
        #     try:
        #         print "connecting synchronous to global sd"
        #         global_sd_cxn = labrad.connect(dt_config.global_address, password = dt_config.global_password,tls_mode='off')
        #         # global_sd_cxn = yield connectAsync('192.168.169.86' , password ='',tls_mode='off')
        #     except:
        #         print "cannot connect to global sd tracker"
        #     else:
        #         if self.window == "car1":
        #             line = self.parameters_dict.DriftTracker.line_selection_1
        #             shift = global_sd_cxn.sd_tracker_global.get_current_line(line, dt_config.client_name)
        #         elif self.window == "car2":
        #             line = self.parameters_dict.DriftTracker.line_selection_2
        #             shift = global_sd_cxn.sd_tracker_global.get_current_line(line, dt_config.client_name)
        #         elif 'sideband_detuning' in self.parameter_to_scan or self.window == "spectrum":# and self.parameters_dict.Spectrum.scan_selection == "auto":  ## I don't think you want this
        #             if self.name != 'RabiFloppingManual' :
        #                 line = self.parameters_dict.Spectrum.line_selection 
        #                 shift = global_sd_cxn.sd_tracker_global.get_current_line(line, dt_config.client_name)
        #                 # adding the shift for the sideband  
 
        #                 sideband= self.parameters_dict.Spectrum.selection_sideband
        #                 if sideband == 'Ignore Me!':
        #                     shift += self.calculate_spectrum_shift()
        #                 else:
        #                     order = int(self.parameters_dict.Spectrum.order)
        #                     shift += 1.0*order*self.parameters_dict.TrapFrequencies[sideband]

        #         global_sd_cxn.disconnect()
        #         # sleep(0.05)

        # else:
        #     try:
        #         print "connecting synchronous to global sd"
        #         global_sd_cxn = labrad.connect(dt_config.global_address, password = dt_config.global_password,tls_mode='off')
        #         # global_sd_cxn = yield connectAsync('192.168.169.86' , password ='',tls_mode='off')
        #     except:
        #         print "cannot connect to global sd tracker"
        #     else:
        #         if self.window == "car1":
        #             line = self.parameters_dict.DriftTracker.line_selection_1
        #             shift = global_sd_cxn.sd_tracker_global.get_current_line(line, dt_config.client_name)
        #         elif self.window == "car2":
        #             line = self.parameters_dict.DriftTracker.line_selection_2
        #             shift = global_sd_cxn.sd_tracker_global.get_current_line(line, dt_config.client_name)
        #         global_sd_cxn.disconnect()
        #     # when we scan the sideband in spectrum we want to have thier offset from the carrier
        #     if 'sideband_detuning' in self.parameter_to_scan or self.name == "Spectrum":
        #         sideband= self.parameters_dict.Spectrum.selection_sideband
        #         if sideband == 'Ignore Me!':
        #             shift = self.calculate_spectrum_shift()
        #         else:
        #             order = int(self.parameters_dict.Spectrum.order)
        #             shift = 1.0*order*self.parameters_dict.TrapFrequencies[sideband]

        #     elif self.name == "MotionAnalysisSpectrum" or self.name == "MotionAnalysisSpectrumMulti":
        #         # MotionAnalysisSpectrum is always on the 1st-order sideband
        #         sideband = self.parameters_dict.Motion_Analysis.sideband_selection
        #         shift = self.parameters_dict.TrapFrequencies[sideband]
                
           
   
        if self.grapher is not None:            
            self.grapher.plot_with_axis(self.ds, self.window, [x+shift for x in self.scan_submit]) # -> plot_with_axis
            
        self.readout_save_directory = directory
        # save the readouts
        self.dv.cd(directory, True, context = self.readout_save_context)
        self.dv.new('Readouts',[('Iteration', 'Arb')],[('Readout Counts','Arb','Arb')], context = self.readout_save_context)
        

        #print self.sc.datasets[self.ident]
        
        # for the scheduled scan this is no creating the dataset for some reason?
        try:
            self.sc.datasets[self.ident].append(self.ds)
        except KeyError:
            self.sc.datasets[self.ident]=[self.ds] # empty list
            #self.sc.datasets[self.ident].append()
            #self.sc.datasets[self.ident]= self.ds
#         print "SETUP datavalut succeeded" 
        
    
    def Scan_shift(self,cxn):
        line=None
        sideband= None
        order = 0
        
        carrier_translation = {'S+1/2D-3/2':'c0',
                               'S-1/2D-5/2':'c1',
                               'S+1/2D-1/2':'c2',
                               'S-1/2D-3/2':'c3',
                               'S+1/2D+1/2':'c4',
                               'S-1/2D-1/2':'c5',
                               'S+1/2D+3/2':'c6',
                               'S-1/2D+1/2':'c7',
                               'S+1/2D+5/2':'c8',
                               'S-1/2D+3/2':'c9',
                               }
#         print "switching to relative units"
#         print self.parameters_dict.Display.relative_frequencies
#         print self.name
        
        #line='none'
        ## running in abs frequency mode

        if self.do_shift:
            pv = cxn.parametervault
            shift = pv.get_parameter('Display','shift') # where shift is set in the experiment.
        else:
            shift = U(0,self.submit_unit)

#         if not self.parameters_dict.Display.relative_frequencies:
#             if self.window == "car1":
#                 line = self.parameters_dict.DriftTracker.line_selection_1
#             elif self.window == "car2":
#                 line = self.parameters_dict.DriftTracker.line_selection_2
#             elif 'sideband_detuning' in self.parameter_to_scan or self.name == "Spectrum":# and self.parameters_dict.Spectrum.scan_selection == "auto":
# #                 print "scanning the Spectrum in a false relative freq"
#                 line = self.parameters_dict.Spectrum.line_selection
#                 if self.parameters_dict.Spectrum.selection_sideband == 'Ignore Me!':
#                     shift = self.calculate_spectrum_shift()
#                     shift += self.parameters_dict.Carriers[carrier_translation[line]]
#                     return shift 
#                 else:
#                     order = int(self.parameters_dict.Spectrum.order)  
#                     if  order != 0 :
#                         sideband= self.parameters_dict.Spectrum.selection_sideband#self.parameters_dict.Spectrum.selection_sideband
                    
#         else:
#             # when we scan the sideband in spectrum we want to have thier offset from the carrier
#             if 'sideband_detuning' in self.parameter_to_scan or self.name == "Spectrum":
#                 sideband= self.parameters_dict.Spectrum.selection_sideband
#                 if sideband == 'Ignore Me!':
#                     shift = self.calculate_spectrum_shift()
#                 else:
#                     order = int(self.parameters_dict.Spectrum.order)
#                     shift = 1.0*order*self.parameters_dict.TrapFrequencies[sideband]

#                 return shift
#             ## handling
#             # elif 'frequency729' in self.parameter_to_scan:
#                 ############BALAHDHGSDLFH:OSIH:SFg

#             elif self.name == "MotionAnalysisSpectrum" or self.name == "MotionAnalysisSpectrumMulti":
#                 # MotionAnalysisSpectrum is always on the 1st-order sideband
#                 sideband = self.parameters_dict.Motion_Analysis.sideband_selection
#                 shift = self.parameters_dict.TrapFrequencies[sideband]
#                 return shift
               

#         if line != None:
#             center_frequency = self.parameters_dict.Carriers[carrier_translation[line]] 
#             if sideband != None:
#                 center_frequency += 1.0*order*self.parameters_dict.TrapFrequencies[sideband]
                
#             shift=center_frequency
#         else:
#             shift = U(0, self.scan_unit) 

        
        return shift
        
    # def set_scan_none(self):
    #     """
    #     Set the current scan to None,
    #     allowing the pulse sequence to be run
    #     with the selected parameters
    #     """
    #     self.scan = None
    #     self.parameter_to_scan = 'None'
    #     self.scan_unit = 'None'
        self.window = 'current'

    def initialize_camera(self, cxn):
        camera = cxn.andor_server
        self.total_camera_confidences = []
        self.camera_initially_live_display = camera.is_live_display_running()
        camera.abort_acquisition()
        self.initial_exposure = camera.get_exposure_time()
      
        exposure = self.parameters_dict.StateReadout.state_readout_duration
        p = self.parameters_dict.IonsOnCamera
        camera.set_exposure_time(exposure)
        self.initial_region = camera.get_image_region()
        self.image_region = [
                             int(p.horizontal_bin),
                             int(p.vertical_bin),
                             int(p.horizontal_min),
                             int(p.horizontal_max),
                             int(p.vertical_min),
                             int(p.vertical_max),
                             ]
        
        #print "Image region{}".format(self.image_region)
        ## comparing to the base excitation there are a few lines missing???
        camera.set_image_region(*self.image_region)
        camera.set_acquisition_mode('Kinetics')
        self.initial_trigger_mode = camera.get_trigger_mode()
        camera.set_trigger_mode('External')
        
        
    def col_names(self):
        mode = self.parameters_dict.StateReadout.readout_mode  
        names = np.array(range(self.output_size())[::-1])+1
         
        if mode == 'pmt':
            if self.output_size==1:
                dependents = [('', 'prob dark ', '')]
            else:
                dependents = [('', 'num dark {}'.format(x), '') for x in names ]
                
        if mode == 'pmt_states':
            if self.output_size==1:
                dependents = [('', 'prob dark ', '')]
            else:
                dependents = [('', ' {} dark ions'.format(x-1), '') for x in names ]
                
        if mode == 'pmt_parity':
            if self.output_size==1:
                dependents = [('', 'prob dark ', '')]
            else:
                dependents = [('', ' {} dark ions'.format(x-1), '') for x in names[1:] ]
                
            dependents.append(('', 'Parity', ''))   

        if mode == 'pmt_excitation':
            dependents = [('', 'prob dark ','')]    
                
        if mode == 'camera':
            dependents = [('', ' prob ion {}'.format(x), '') for x in range(self.output_size())]
            
        if mode == 'camera_states':
            num_of_ions=int(self.parameters_dict.IonsOnCamera.ion_number)
            names = range(2**num_of_ions)
            dependents=[]
            for name in names:
                temp= np.binary_repr(name,width=num_of_ions)
                temp = self.binary_to_state(temp)
                temp=('', 'Col {}'.format(temp), '')
                dependents.append(temp)
        
        if mode == 'camera_parity':
            num_of_ions=int(self.parameters_dict.IonsOnCamera.ion_number)
            names = range(2**num_of_ions)
            dependents=[]
            for name in names:
                temp= np.binary_repr(name,width=num_of_ions)
                temp = self.binary_to_state(temp)
                temp=('', 'Col {}'.format(temp), '')
                dependents.append(temp)
            dependents.append(('', 'Parity', ''))

        return  dependents
    

    def output_size(self):
        # function that gives the number of output cols in the readout file
        mode = self.parameters_dict.StateReadout.readout_mode
      
        # Temporary fix
        # n_temp = 2
        if mode == 'pmt':
            return len(self.parameters_dict.StateReadout.threshold_list.split(','))
        if mode == 'pmt_states':
            return len(self.parameters_dict.StateReadout.threshold_list.split(',')) + 1
        if mode == 'pmt_parity':
            # cols for the states and plus one for the parity calculation 
            return len(self.parameters_dict.StateReadout.threshold_list.split(',')) + 2
        if  mode == 'pmt_excitation':
            # col for excitation only
            return 1
        
        if mode == 'camera':
            return int(self.parameters_dict.IonsOnCamera.ion_number)
        if mode == 'camera_states':
            num_of_ions=int(self.parameters_dict.IonsOnCamera.ion_number)
            return 2**num_of_ions
        if mode == 'camera_parity':
            num_of_ions=int(self.parameters_dict.IonsOnCamera.ion_number)
            return 2**num_of_ions+1
        
        
    def binary_to_state(self,name):
        state = ''
        rev_name=name[::-1]
        for j in rev_name:
            if j=='0':
                state=state+'S'
            else:
                state=state+'D'
        return state    

    
    # def run_single_point(self,cxn,x=0):
    #     cxn = labrad.connect()
    #     pulser = cxn.pulser
    #     seq = self.module(self.parameters_dict)
    #     seq.programSequence(pulser)
    #     sleep(0.1)
    #     print "programmed pulser for a single point"
    #     repetitions=int(self.parameters_dict.StateReadout.repeat_each_measurement)
    #     pulser.start_number(repetitions)
    #     # print "started {} sequences".format(int(self.parameters_dict.StateReadout.repeat_each_measurement))
    #     pulser.wait_sequence_done()
    #     pulser.stop_sequence()
            

    def plot_current_sequence(self, cxn):
        
        # Bypass creating pulse sequence plot
        if self.parameters_dict.global_scan_options.quick_finish:
            return
        
        #t0 = time.time()
        from common.okfpgaservers.pulser.pulse_sequences.plot_sequence import SequencePlotter
        dds = cxn.pulser.human_readable_dds()
        ttl = cxn.pulser.human_readable_ttl()
        channels = cxn.pulser.get_channels()
        #sp = SequencePlotter(ttl, dds.aslist, channels)
        sp = SequencePlotter(ttl, dds, channels)
        sp.makePDF()
        #t1 = time.time()
        #print "TIME", t1-t0


    def calculate_spectrum_shift(self):
        shift = 0
        trap = self.parameters_dict.TrapFrequencies
        sideband_selection = self.parameters_dict.Spectrum.sideband_selection
        sideband_frequencies = [trap.radial_frequency_1, trap.radial_frequency_2, trap.axial_frequency, trap.rf_drive_frequency]
        for order,sideband_frequency in zip(sideband_selection, sideband_frequencies):
            shift += order * sideband_frequency
        return shift

        
    
    
if __name__=='__main__':
    from example import Example
    pv = TreeDict.fromdict({'DopplerCooling.duration':U(5, 'us')})
    psw = pulse_sequence_wrapper(Example, pv)

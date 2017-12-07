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
        try:
            self.dt = self.cxn.sd_tracker
        except:
            self.dt = None
        try:
            self.grapher = cxn.grapher
        except:
            self.grapher = None
        self.total_readouts = []

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
        
        import time
        localtime = time.localtime()
        self.dv = cxn.data_vault
        print "data vault connected"
        self.timetag = time.strftime('%H%M_%S', localtime)
        directory = ['', 'Experiments', time.strftime('%Y%m%d', localtime), name, self.timetag]
        self.data_save_context = cxn.context()
        self.readout_save_context = cxn.context()
        self.histogram_save_context = cxn.context()
        self.dv.cd(directory, True, context = self.data_save_context)
        
        # creating the col names in the output file
        #dependents = [('', 'Col {}'.format(x), '') for x in range(self.output_size())]
        dependents = self.col_names()
        print "number of depe"
       
        self.ds = self.dv.new(self.timetag, [(self.parameter_to_scan, self.submit_unit)], dependents, context = self.data_save_context)
        
        shift=U(0,self.submit_unit)
        
        #print "4321 display relative" , self.parameters_dict.Display.relative_frequencies
        if not self.parameters_dict.Display.relative_frequencies:
            if self.window == "car1":
                line = self.parameters_dict.DriftTracker.line_selection_1
                shift = cxn.sd_tracker.get_current_line(line)
            elif self.window == "car2":
                line = self.parameters_dict.DriftTracker.line_selection_2
                shift = cxn.sd_tracker.get_current_line(line)
            elif self.window == "spectrum":# and self.parameters_dict.Spectrum.scan_selection == "auto":
                #print "name of theseq", self.name 
                if self.name != 'RabiFloppingManual' :
                    print "scanning the Spectrum in a false relative freq"
                    line = self.parameters_dict.Spectrum.line_selection 
                    shift = cxn.sd_tracker.get_current_line(line) 
                    # adding the shift for the sideband
                    order = int(self.parameters_dict.Spectrum.order)  
                    if  order != 0 :
                        sideband= self.parameters_dict.Spectrum.selection_sideband
                        shift += 1.0*order*self.parameters_dict.TrapFrequencies[sideband]
        else:
            # when we scan the sideband in spectrum we want to have thier offset from the carrier
            if self.name == "Spectrum":
                order = int(self.parameters_dict.Spectrum.order)
                if  order != 0 :
                    sideband= self.parameters_dict.Spectrum.selection_sideband#self.parameters_dict.Spectrum.selection_sideband
                    shift= 1.0*order*self.parameters_dict.TrapFrequencies[sideband]
                          
        
                    
                
           
   
        if self.grapher is not None:
            
            
            print "this is the scan_submit"
            print self.scan_submit
            print "this is the shift", shift
            
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
        print "SETUP datavalut succeeded" 
        
        
        
    @inlineCallbacks
    def update_params(self, update):
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
        if self.dt is not None:
            carriers = yield self.dt.get_current_lines()
            for c, f in carriers:
                carriers_dict[carrier_translation[c]] = f
                
        self.parameters_dict.update(update_dict)
        self.parameters_dict.update(carriers_dict)
        self.parameters_dict.update(self.module.fixed_params)
        
        
    def update_scan_param(self, update):
        update_dict = {}
        for key in update.keys():
            if type(key) == tuple:
                print key
                update_dict['.'.join(key)] = update[key]
            else:
                update_dict[key] = update[key]
        self.parameters_dict.update(update)
            

    def set_scan(self, scan_param, minim, maxim, steps, unit):
        self.parameter_to_scan = scan_param
                        
        try:
            self.window = self.module.scannable_params[scan_param][1]                   

        except:
            self.window = 'current' # no window defined
        
        # Enable scan only from the scannable params 
        #m1, m2, default, unit = self.module.scannable_params[scan_param][0]
        self.scan_unit = unit      
        
        # adding the last element to the scan
        self.scan = np.arange(minim, maxim, steps)
        self.scan = np.append(self.scan,maxim)

        self.scan = [U(pt, unit) for pt in self.scan]
        
        x=self.scan[0]
        if x.isCompatible('s'): 
            self.submit_unit='us'
        
        elif x.isCompatible('Hz'):
            self.submit_unit='MHz'       
        else:
            self.submit_unit=self.scan_unit    
        
        self.scan_submit = [pt[self.submit_unit] for pt in self.scan]
        self.scan_submit = [U(pt, self.submit_unit) for pt in self.scan_submit]
        print self.scan_submit
        
        #if not self.parameters_dict.Display.relative_frequencies:
        #    self.relative_freq()
#         print self.scan_submit
#         print self.scan
#         
        #print "setting up the scan params"
        
    
    # calculate the relative freq
    
 
    
    def Scan_shift(self):
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
        print "switching to relative units"
        print self.parameters_dict.Display.relative_frequencies
        print self.name
        
        #line='none'
        ## running in abs frequency mode
        if not self.parameters_dict.Display.relative_frequencies:
            if self.window == "car1":
                line = self.parameters_dict.DriftTracker.line_selection_1
            elif self.window == "car2":
                line = self.parameters_dict.DriftTracker.line_selection_2
            elif self.name == "Spectrum":# and self.parameters_dict.Spectrum.scan_selection == "auto":
                print "scanning the Spectrum in a false relative freq"
                line = self.parameters_dict.Spectrum.line_selection
                order = int(self.parameters_dict.Spectrum.order)  
                if  order != 0 :
                    sideband= self.parameters_dict.Spectrum.selection_sideband#self.parameters_dict.Spectrum.selection_sideband
                    
        else:
            # when we scan the sideband in spectrum we want to have thier offset from the carrier
            if self.name == "Spectrum":
                order = int(self.parameters_dict.Spectrum.order)
                if  order != 0 :
                    sideband= self.parameters_dict.Spectrum.selection_sideband#self.parameters_dict.Spectrum.selection_sideband
                    shift= 1.0*order*self.parameters_dict.TrapFrequencies[sideband]
                    print "1234"  
                    print "this is the shift for the sideband in relative mode" , shift
                    return shift
               
        print "1234"        
        print line 
        print order
        print sideband 
        
        if line != None:
            center_frequency = self.parameters_dict.Carriers[carrier_translation[line]] 
            if sideband != None:
                center_frequency += 1.0*order*self.parameters_dict.TrapFrequencies[sideband]
                
            shift=center_frequency
        else:
            shift = U(0, self.scan_unit) 
        print "this is the shift in the scan {}".format(shift)
        
        return shift
            #self.scan_submit=[center_frequency + x for x in self.scan_submit]
        #center_frequency = self.parameters_dict.Carriers[carrier_translation[line]]
        
    def set_scan_none(self):
        """
        Set the current scan to None,
        allowing the pulse sequence to be run
        with the selected parameters
        """
        self.scan = None
        self.parameter_to_scan = 'None'
        self.scan_unit = 'None'
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

    def output_size(self):
        # function that gives the number of output cols in the readout file
        mode = self.parameters_dict.StateReadout.readout_mode
        print mode
        
        if mode == 'pmt':
            return len(self.parameters_dict.StateReadout.threshold_list.split(','))
        if mode == 'pmt_states':
            return len(self.parameters_dict.StateReadout.threshold_list.split(',')) + 1
        if mode == 'pmt_parity':
            # cols for the states and plus one for the parity calculation 
            return len(self.parameters_dict.StateReadout.threshold_list.split(',')) + 2
        
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
        
        
    def col_names(self):
        mode = self.parameters_dict.StateReadout.readout_mode     
        names = np.array(range(self.output_size())[::-1])+1
#         
#         print "555"
#         print "this is the readout mode", mode
#         print "this is the readout names", names
#         
         
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

#         print "this is the readout dependents", dependents
        return  dependents
    
    
        
    def run(self, ident):
        
        print " started running"
        self.ident = ident
        #import time
        cxn = labrad.connect()
        pulser = cxn.pulser
        ### camera debug
        #cxn.scriptscanner.set_parameter(['StateReadout','use_camera_for_readout', True])

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
              
        self.update_params(self.sc.all_parameters())
        line=self.parameters_dict.Spectrum.line_selection   
        #print "Spectrum scan line:"
        #print line
        #print "729 freq {}".format(self.parameters_dict.Carriers[carrier_translation[line]])  
        #print "This is the scan Shift {}".format( self.Scan_shift())
        
        self.setup_data_vault(cxn, self.name)
        #print self.window
        #print self.name
        
       
        self.use_camera = False
        
        
        ## camera
        #self.use_camera = self.parameters_dict.StateReadout.use_camera_for_readout
        #if use_camera_override != None:
        #    self.use_camera=use_camera_override
        
        
        if 'camera' in self.parameters_dict.StateReadout.readout_mode: 
            self.use_camera = True
            self.initialize_camera(cxn)
            camera = cxn.andor_server
            print "Using Camera"
            print self.name
        else:
            self.use_camera = False

        
                    
        # sequence initializing hardware (dds_cw or mirrors?)    
        self.module.run_initial(cxn, self.parameters_dict)
        
        self.readout_save_iteration = 0
        #print "SCAN:"
        #print self.scan
        
        data = [] 
        data_x = []
        
        for it,x in enumerate(self.scan):
           
            print " currently scanning point {}".format(x)
            
            should_stop = self.sc._pause_or_stop(ident)
            if should_stop: break
            update = {self.parameter_to_scan: x}
            ## needs the two lines of update to ensure the proper updating!!!
            self.update_params(update)
            self.update_scan_param(update)
            #self.parameters_dict.update(update)
            #print "PARAMETER {}".format(self.parameters_dict.RabiFlopping.duration)
            seq = self.module(self.parameters_dict)
            seq.programSequence(pulser)
            #sleep(0.1)
            
            print "programmed pulser"
            self.plot_current_sequence(cxn)
            
                        
            repetitions=int(self.parameters_dict.StateReadout.repeat_each_measurement)
            if self.use_camera:
                print " setting up kineticks"
                print "repetitions",repetitions 
                print "corrected repetitions", int(self.parameters_dict.IonsOnCamera.reference_exposure_factor) * repetitions
                
                exposures = repetitions # int(self.parameters_dict.IonsOnCamera.reference_exposure_factor) * repetitions
                camera.set_number_kinetics(exposures)
                camera.start_acquisition()
                
            
            pulser.start_number(repetitions)
            print "started {} sequences".format(int(self.parameters_dict.StateReadout.repeat_each_measurement))
            pulser.wait_sequence_done()
            print "done"
            pulser.stop_sequence()
            #print "done waiting"
            
            if not self.use_camera:
                readout_mode=self.parameters_dict.StateReadout.readout_mode 
                print "Using the PMT! in redout_mode:",readout_mode
                rds = pulser.get_readout_counts()
                ion_state = readouts.pmt_simple(rds, self.parameters_dict.StateReadout.threshold_list,readout_mode)
                #print "646884:  ", ion_state
                self.save_data(rds)
                data.append(ion_state)
                
            else:
                #get the percentage of excitation using the camera state readout
                proceed = camera.wait_for_kinetic()
                
                if not proceed:
                    camera.abort_acquisition()
                    self._finalize(cxn)
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
            print "this is x_shift {}".format(x_shift)
            print "this is x in submission units {}".format(x[self.submit_unit])
            
            submission = [x[self.submit_unit]+x_shift[self.submit_unit]]  # + center_frequency[self.submit_unit]]
            print "the x submission", submission
            submission.extend(ion_state)
            
            #data.append(submission)
            #print "data {}".format(data)
            # run in the loop to calculate something
            data_x.append(x[self.submit_unit] + x_shift[self.submit_unit])
            
            self.module.run_in_loop(cxn, self.parameters_dict, np.array(data),np.array(data_x))
            #submit the results to the data vault
            self.dv.add(submission, context = self.data_save_context)
                
           
                
        self.module.run_finally(cxn, self.parameters_dict, data, np.array(data_x))

        self._finalize(cxn) 
    
    def run_single_point(self,cxn,x=0):
        print x
        cxn = labrad.connect()
        pulser = cxn.pulser
        seq = self.module(self.parameters_dict)
        seq.programSequence(pulser)
        sleep(0.1)
        print "programmed pulser for a single point"
        repetitions=int(self.parameters_dict.StateReadout.repeat_each_measurement)
        pulser.start_number(repetitions)
        print "started {} sequences".format(int(self.parameters_dict.StateReadout.repeat_each_measurement))
        pulser.wait_sequence_done()
        print "done"
        pulser.stop_sequence()
            
            
        
    
    def _finalize(self, cxn):
        # Add finalize the camera when needed 
        dvParameters.saveParameters(self.dv, dict(self.parameters_dict), self.data_save_context)
        self.sc._finish_confirmed(self.ident)
        
        
        if self.use_camera:
            #if used the camera, return it to the original settings
            camera = cxn.andor_server
            camera.set_trigger_mode(self.initial_trigger_mode)
            camera.set_exposure_time(self.initial_exposure)
            camera.set_image_region(self.initial_region)
            if self.camera_initially_live_display:
                camera.start_live_display()
                
        cxn.disconnect()

    def plot_current_sequence(self, cxn):
        from common.okfpgaservers.pulser.pulse_sequences.plot_sequence import SequencePlotter
        dds = cxn.pulser.human_readable_dds()
        ttl = cxn.pulser.human_readable_ttl()
        channels = cxn.pulser.get_channels()
        #sp = SequencePlotter(ttl, dds.aslist, channels)
        sp = SequencePlotter(ttl, dds, channels)
        sp.makePDF()

    @classmethod
    def add_sidebands(cls, freq, sideband_selection, trap):
        sideband_frequencies = [trap.radial_frequency_1, trap.radial_frequency_2, trap.axial_frequency, trap.rf_drive_frequency]
        for order,sideband_frequency in zip(sideband_selection, sideband_frequencies):
            freq += order * sideband_frequency
        return freq
    
    
if __name__=='__main__':
    from example import Example
    pv = TreeDict.fromdict({'DopplerCooling.duration':U(5, 'us')})
    psw = pulse_sequence_wrapper(Example, pv)

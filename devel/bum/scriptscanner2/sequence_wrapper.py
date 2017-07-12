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
from treedict import TreeDict
import labrad
from labrad.units import WithUnit as U
#from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, DeferredList, returnValue, Deferred
from twisted.internet.threads import blockingCallFromThread
from analysis import readouts

class pulse_sequence_wrapper(object):
    
    def __init__(self, module, sc, cxn):
        self.module = module
        self.name = module.__name__
        # copy the parameter vault dict by value
        self.parameters_dict = TreeDict()
        #self.parameters_dict.update(pv_dict)
        self.show_params = module.show_params
        self.scan = None
        self.sc = sc # reference to scriptscanner class, not through the labrad connection
        self.cxn = cxn
        #self.seq = module(self.pv_dict)
    
    def setup_data_vault(self, cxn):
        import time
        localtime = time.localtime()
        self.dv = cxn.data_vault
        self.timetag = time.strftime('%H%M_%S', localtime)
        directory = ['', 'Experiments', time.strftime('%Y%m%d', localtime), self.timetag]
        self.data_save_context = cxn.context()
        self.dv.cd(directory, True, context = self.data_save_context)
        dependents = [('', 'Col {}'.format(x), '') for x in range(self.output_size())]
        print dependents
        self.ds = self.dv.new(self.timetag, [('','')], dependents, context = self.data_save_context)

    def update_params(self, update):
        # also update from the drift tracker here?
        self.parameters_dict.update(update)

    def set_scan(self, scan_param, minim, maxim, steps, unit):
        self.parameter_to_scan = scan_param
        m1, m2, default, unit = self.module.scannable_params[scan_param]
        self.scan_unit = unit
        self.scan = np.linspace(minim, maxim, steps)
        self.scan = [U(pt, unit) for pt in self.scan]

    def set_scan_none(self):
        """
        Set the current scan to None,
        allowing the pulse sequence to be run
        with the selected parameters
        """
        self.scan = None

    def initialize_camera(self):
        camera = self.cxn.andor_server
        self.total_camera_confidences = []
        self.camera_initially_live_display = self.camera.is_live_display_running()
        camera.abort_acquisition()
        self.initial_exposure = camera.get_exposure_time()
        p = self.parameters_dict
        exposure = p.StateReadout.state_readout_duration
        camera.set_exposure_time(exposure)
        self.initial_region = self.camera.get_image_region()
        self.image_region = [
                             int(p.horizontal_bin),
                             int(p.vertical_bin),
                             int(p.horizontal_min),
                             int(p.horizontal_max),
                             int(p.vertical_min),
                             int(p.vertical_max),
                             ]

        camera.set_image_region(*self.image_region)
        camera.set_acquisition_mode('Kinetics')
        self.initial_trigger_mode = camera.get_trigger_mode()
        camera.set_trigger_mode('External')

    def output_size(self):
        mode = self.parameters_dict.StateReadout.readout_mode
        if mode == 'pmt':
            return 1
        if mode == 'camera':
            return int(self.parameters_dict.IonsOnCamera.ion_number)
        
    def run(self, ident):
        self.ident = ident
        import time
        cxn = labrad.connect()
        #pulser = cxn.pulser
        #t = cxn.testserver
        # first, get the current parameters from scriptscanner
        #self.update_params(self.sc._get_all_parameters())

        self.setup_data_vault(cxn)
        #localtime = time.localtime()
        #self.dv = cxn.data_vault
        #self.timetag = time.strftime('%H%M_%S', localtime)
        #directory = ['', 'Experiments', time.strftime('%Y%m%d', localtime), self.timetag]

        self.run_initial()
        for x in self.scan:
            time.sleep(0.5)
            should_stop = self.sc._pause_or_stop(ident)
            if should_stop: break
            update = {self.parameter_to_scan: x}
            self.update_params(update)
            self.run_in_loop()
            seq = self.module(self.parameters_dict)
            #seq.programSequence(pulser)
            #pulser.start_number(repetitions)
            #pulser.wait_sequence_done()
            #pulser.stop_sequence()
            rds = np.random.randint(0, 50, 100)
            threshold = int(self.parameters_dict.StateReadout.threshold)
            ion_state = readouts.pmt_simple(rds, threshold)
            submission = [x[self.scan_unit]]
            submission.extend(ion_state)
            self.dv.add(submission, context = self.data_save_context)
            #print "done waiting"
                ### program pulser, get readouts
        self.run_finally()
        self._finalize(cxn)

    def run_initial(self):
        pass
    def run_in_loop(self):
        pass
    def run_finally(self):
        pass
        
    def _finalize(self, cxn):
        self.sc._finish_confirmed(self.ident)
        cxn.disconnect()

if __name__=='__main__':
    from example import Example
    pv = TreeDict.fromdict({'DopplerCooling.duration':U(5, 'us')})
    psw = pulse_sequence_wrapper(Example, pv)

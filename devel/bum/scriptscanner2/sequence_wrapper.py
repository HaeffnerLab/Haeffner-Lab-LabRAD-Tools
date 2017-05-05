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
from labrad.units import WithUnit as U
#from subsequences import *

class pulse_sequence_wrapper(object):
    
    def __init__(self, module, drift_tracker = None):  
        self.module = module
        self.name = module.__name__
        # copy the parameter vault dict by value
        self.parameters_dict = TreeDict()
        #self.parameters_dict.update(pv_dict)
        self.show_params = module.show_params
        self.scan = None
        self.drift_tracker = drift_tracker
        #self.seq = module(self.pv_dict)
    
    def setup_data_vault(self):
        pass

    def update_params(self, update):
        # also update from the drift tracker here?
        self.parameters_dict.update(update)

    def set_scan(self, scan_param, minim, maxim, steps, unit):
        self.parameter_to_scan = scan_param
        m1, m2, default, unit = self.module.scannable_params[scan_param]
        self.scan = np.linspace(minim, maxim, steps)
        self.scan = [U(pt, unit) for pt in self.scan]
        print self.scan

    def set_scan_none(self):
        """
        Set the current scan to None,
        allowing the pulse sequence to be run
        with the selected parameters
        """
        self.scan = None

    def run(self, ident):
        self.ident = ident
        for x in self.scan:
            print x
            update = {self.parameter_to_scan: x}
            self.update_params(update)
            #seq = self.module(self.parameters_dict)
            ### program pulser, get readouts

if __name__=='__main__':
    from example import Example
    pv = TreeDict.fromdict({'DopplerCooling.duration':U(5, 'us')})
    psw = pulse_sequence_wrapper(Example, pv)

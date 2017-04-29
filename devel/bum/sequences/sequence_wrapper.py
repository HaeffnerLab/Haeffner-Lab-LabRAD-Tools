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
import xml.etree.ElementTree as ET
from treedict import TreeDict
from labrad.units import WithUnit as U
from pulse_sequence import pulse_sequence
from subsequences import *

class pulse_sequence_wrapper(object):
    
    def __init__(self, module, pv_dict):  
        self.module = module
        self.pv_dict = pv_dict
        self.scannable_params = module.scannable_params
        self.show_params = module.show_params
        self.scan = None
        self.seq = module(self.pv_dict)
        
    def parse_scannable_parameters(self, tree):
        params = tree.find('params')
        for child in params:
            param_name = child.attrib['name']
            # remove all whitespace and split the items by commas
            minim, maxim, value, unit = ''.join(child.text.split()).split(',')
            minim = float(minim)
            maxim = float(maxim)
            value = float(value)
            self.scannable_params[param_name] = (minim, maxim, value, unit)
    
    def setup_data_vault(self):
        pass

    def build_sequence(self, replace):
        """
        Build  the pulse sequence for the current set of parameters.
        First copy the parameter vault keys and then overwrite
        the scanned parameters
        """
        new_dict = TreeDict()
        for key in self.pv_dict.keys():
            new_dict[key] = self.pv_dict[key]
        
        for key in replace.keys():
            new_dict[key] = replace[key]
        seq = pulse_sequence(new_dict)

    def select_scan(self, scan_param, minim, maxim, steps):
        self.scan = scan_param
        
    def run(self):
        new_params = self.update_params()

if __name__=='__main__':
    from example import Example
    pv = TreeDict.fromdict({'DopplerCooling.duration':U(5, 'us')})
    psw = pulse_sequence_wrapper(Example, pv)

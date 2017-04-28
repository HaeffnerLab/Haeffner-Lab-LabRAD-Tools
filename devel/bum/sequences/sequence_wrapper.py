"""
     Wrapper class for pulse sequences

Current idea:
pulse sequence is an xml file which gets parsed
by the wrapper class.

script scanner will generate a pulse_sequence_wrapper object
on the fly, passing the path to the pulse sequence definition file,
as well as the current parameter vault downloaded as a TreeDict

1. First parse which parameters are scannable out of the XML definition file
2. GUI takes these parameters to show

"""
import xml.etree.ElementTree as ET
from treedict import TreeDict
from labrad.units import WithUnit as U
from pulse_sequence import pulse_sequence

class pulse_sequence_wrapper(object):
    
    def __init__(self, path, pv_dict):  
        self.scannable_params = {}
        self.pv_dict = pv_dict
        self.scan = None
        self.seq = pulse_sequence()
        tree = ET.parse(path)
        self.parse_scannable_parameters(tree)
        
    def parse_scannable_parameters(self, tree):
        params = tree.find('params')
        for child in params:
            param_name = child.attrib['name']
            # remove all whitespace and split the items by commas
            minim, maxim, steps, unit = ''.join(child.text.split()).split(',')
            minim = float(minim)
            maxim = float(maxim)
            steps = int(steps)
            self.scannable_params[param_name] = (minim, maxim, steps, unit)
    
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
        seq = self.build_sequence()

if __name__=='__main__':
    pv = TreeDict.fromdict({'DopplerCooling.duration':U(5, 'us')})
    psw = pulse_sequence_wrapper('example.xml', pv)


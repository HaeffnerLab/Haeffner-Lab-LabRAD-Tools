import numpy as np
from pulse_sequences_config import dds_name_dictionary as dds_config
from labrad.units import WithUnit
from treedict import TreeDict
from scipy.optimize import curve_fit
import types

class pulse_sequence(object):
    '''
    Base class for all Pulse Sequences
    Version 2 -- made for new script scanner project
    '''
    
    is_2dimensional = False
    is_composite = False
    fixed_params = {}
    scannable_params = {}
    show_params = []
    
    def __init__(self, parameter_dict, start = WithUnit(0, 's')):
        if not type(parameter_dict) == TreeDict: raise Exception ("replacement_dict must be a TreeDict in sequence {0}".format(self.__class__.__name__))
        self.start = start
        self.end = start
        self._dds_pulses = []
        self._ttl_pulses = []
        self.replace = parameter_dict
        #self.parameters = self.fill_parameters(self.required_parameters , self.replace)
        self.parameters = parameter_dict
        pulse_sequence.parameters = parameter_dict
        self.sequence()
        
        
    def sequence(self):
        '''
        implemented by subclass
        '''
    
    def fill_parameters(self, params, replace):
        if not len(params) == len(set(params)):
            raise Exception ("Duplicate required parameters found in {0}".format(self.__class__.__name__))
        new_dict = TreeDict()
        for collection,parameter_name in params:
            treedict_key = '{0}.{1}'.format(collection,parameter_name)
            try:
                new_dict[treedict_key] = replace[treedict_key]
            except KeyError:
                raise Exception('{0} {1} value not provided for the {2} Pulse Sequence'.format(collection, parameter_name, self.__class__.__name__))
        return new_dict
    
    def addDDS(self, channel, start, duration, frequency, amplitude, phase = WithUnit(0, 'deg'), profile = 0):
        """
        add a dds pulse to the pulse sequence
        """
        #print "Profile: ", profile
        dds_channel = dds_config.get(channel, None)
        if dds_channel is not None:
            #additional configuration provided
            channel = dds_channel.name
            frequency = dds_channel.freq_conversion(frequency)
            amplitude = dds_channel.ampl_conversion(amplitude)
            phase = dds_channel.phase_conversion(phase)
        self._dds_pulses.append((channel, start, duration, frequency, amplitude, phase, profile))
    
    def addTTL(self, channel, start, duration):
        """
        add a ttl pulse to the pulse sequence
        """
        self._ttl_pulses.append((channel, start, duration))
    
    def addSequence(self, sequence, replacement_dict = TreeDict(), position = None):
        '''insert a subsequence, position is either time or None to insert at the end'''
        #if not type(replacement_dict) == TreeDict: raise Exception ("replacement_dict must be a TreeDict")
        if position is None:
            position = self.end
        #replacement conists of global replacement and keyword arguments
        replacement = TreeDict()
        replacement.update(self.replace)
        replacement.update(replacement_dict)
        seq = sequence(replacement, start = position)
        self._dds_pulses.extend( seq._dds_pulses )
        #print 'heres the seq pulses'
        #print seq._ttl_pulses
        self._ttl_pulses.extend( seq._ttl_pulses )
        self.end = max(self.end, seq.end)
    
    def programSequence(self, pulser):
        print "PROGRAM SEQUENCE"
        pulser.new_sequence()
        #print self._ttl_pulses
        pulser.add_ttl_pulses(self._ttl_pulses)
        pulser.add_dds_pulses(self._dds_pulses)
        pulser.program_sequence()

    def calc_freq(self, carrier='S-1/2D-1/2', sideband=None,order=0):
        '''calculates the frequency of the 729 DP drive from the carriers and sidebands
        in the parameter vault
        '''
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
        #print "230984", self.parameters.Carriers[carrier_translation[carrier]]
        #print carrier_translation[carrier]
        freq=self.parameters.Carriers[carrier_translation[carrier]]
        try: 
            freq=self.parameters.Carriers[carrier_translation[carrier]]
        except:
            raise Exception('carrier not found') 
        if order != 0 :
            try: 
                freq = freq+ 1.0*self.parameters.TrapFrequencies[sideband]*order
            except:
                raise Exception('sideband not found') 
        return freq

    # old parameter_vault version 
    def calc_freq_from_array(self, carrier='S-1/2D-1/2', sideband_selection=[0,0,0,0]):
        '''given calculates the frequency of the 729 DP drive from the carriers and sidebands
        in the parameter vault
        '''
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
#         print "230984", self.parameters.Carriers[carrier_translation[carrier]]
#         print carrier_translation[carrier]
        freq=self.parameters.Carriers[carrier_translation[carrier]]
        try: 
            freq=self.parameters.Carriers[carrier_translation[carrier]]
        except:
            raise Exception('carrier not found') 
        trapfreq = self.parameters.TrapFrequencies
        sideband_frequencies = [trapfreq.radial_frequency_1, trapfreq.radial_frequency_2, trapfreq.axial_frequency, trapfreq.rf_drive_frequency]
        for order,sideband_frequency in zip(sideband_selection, sideband_frequencies):
            freq += order * sideband_frequency
        return freq


    def get_params(self):
        return self.parameters    

    def get_dds(self):
        return self._dds_pulses

    def get_ttl(self):
        return self._ttl_pulses
    
    
    @classmethod
    def peak_guess(cls, f, p, force_guess = False):
        '''
        just take the point at the peak value
        '''
        max_index = np.where(p == p.max())[0][0]
        fmax = f[max_index]
        if (p.max() <= 0.15 and not force_guess):
            
            #raise Exception("Peak not found") Need to know how to implement this with the GUI
            return None
            
        else:
            # center, amplitude, width guesses
            return np.array([ fmax,  p.max(), 6e-3 ])
    
    
    @classmethod
    def gaussian_fit(cls, f, p, return_all_params = False, init_guess = None):
        if init_guess == "stop":
            return None

        model = lambda x, c0, a, w: a * np.exp(-( x - c0 )**2. / w**2.)
        force_guess = False
        if return_all_params: 
            force_guess = True
        if init_guess is None:
            guess = cls.peak_guess(f, p, force_guess)
            if guess is None:
                return None
                    
        else:
            guess = init_guess
        #print "1234"
        #print f,p, guess
        try:
            popt, copt = curve_fit(model, f, p, p0=guess)
            if return_all_params:
                return popt[0], popt[1], popt[2] # center value, amplitude, width
            else:
                return popt[0] # return only the center value
        except:
            print "problem with the fit"
            return None
        
        
    
    
    @classmethod
    def execute_external(cls, scan, fun = None):
        '''
        scan  = (scan_param, minim, maxim, seps, unit)
        fun = function to evaluate on the result of the scan 
        '''
        from common.devel.bum.scriptscanner2.sequence_wrapper import pulse_sequence_wrapper
        psw = pulse_sequence_wrapper(cls)
        scan_param, minim, maxim, steps, unit = scan
        psw.set_scan(scan_param, minim, maxim, steps, unit)
        psw.run(0)    
        
    @classmethod
    def get_scannable_parameters(cls):
        
        if not cls.is_composite and not cls.is_2dimensional:
            scan = cls.scannable_params.items()
            li = []
            for item in scan:
                s = item[1][0]
                s = (float(s[0]), float(s[1]), float(s[2]), s[3]) # this fixes a weird labrad bug
                li.append((item[0], s, cls.__name__))
            return li
        elif cls.is_composite and not cls.is_2dimensional:
            li = []
            for subcls in cls.sequences:
                if type(subcls) == tuple:
                    subcls = subcls[0]
            
                scan = subcls.scannable_params.items()
                for item in scan:
                    s = item[1][0]
                    s = (float(s[0]), float(s[1]), float(s[2]), s[3])
                    li.append((item[0], s, subcls.__name__))
            return li
        elif cls.is_2dimensional and not cls.is_composite:
            li = []
            scan = cls.scannable_params_1d.items()
            for item in scan:
                s = item[1][0]
                s = (float(s[0]), float(s[1]), float(s[2]), s[3])
                li.append((item[0], s, '1d'))
            scan = cls.scannable_params.items()
            for item in scan:
                s = item[1][0]
                s = (float(s[0]), float(s[1]), float(s[2]), s[3]) # this fixes a weird labrad bug
                li.append((item[0], s, cls.__name__))
            return li
        elif cls.is_2dimensional and cls.is_composite:
            li = []
            cls.loop_get_scan(li)
            return li

    @classmethod
    def loop_get_scan(cls, li):
        scan = cls.scannable_params.items()
        for item in scan:
            s = item[1][0]
            s = (float(s[0]), float(s[1]), float(s[2]), s[3]) # this fixes a weird labrad bug
            li.append((item[0], s, cls.__name__))
        try:
            if type(cls.sequence) == list:
                for subcls in cls.sequence:
                    if type(subcls) == tuple:
                        subcls = subcls[0]
                    subcls.loop_get_scan(li)
            elif type(cls.sequence) == type:
                cls.sequence.loop_get_scan(li)
        except:
            print "error with ", cls.__name__
            return




    

    @classmethod
    def run_initial(cls, cxn, parameters_dict):
        pass
    
    
    @classmethod
    def run_in_loop(cls, cxn, parameters_dict, data_so_far,data_x):
        return data_so_far, data_x
    
    
    @classmethod
    def run_finally(cls, cxn, parameters_dict, all_data, data_x):
        return all_data, data_x
        #print "646884:  This is the data we want", all_data

    @classmethod
    def final_data_process(cls, cxn, processed_data):
        pass
    
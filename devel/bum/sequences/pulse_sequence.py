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
    def calc_freq_from_array(self, carrier='S-1/2D-1/2', sideband_selection=[0,0,0,0,0]):
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
        #freq=self.parameters.Carriers[carrier_translation[carrier]]
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
        if (p.max() <= 0.1 and not force_guess):
            
            raise Exception("Peak not found") #Need to know how to implement this with the GUI
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
    def sin_fit(cls, phase, excitation, return_all_params = False, init_guess = None):
        if init_guess == "stop":
            return None

        model = lambda x, a, x0, c: a*np.sin((np.pi*x/180.)+x0) + c
        force_guess = False
        
        guess = [.5,np.pi/2.,.5]
        #print "1234"
        #print f,p, guess
        print phase,excitation
        try:
            popt, copt = curve_fit(model, phase, excitation, p0=guess,bounds=((0,-np.inf,-1),(1,np.inf,1)))
            print popt
            if return_all_params:
                return popt[0], popt[1], popt[2] # amplitude, phase offset, amplitude offset
            else:
                return popt[0] # return only the center value
        except:
            print "problem with the fit"
            return None

    @classmethod
    def rot_ramsey_fit(cls, phase, excitation, return_all_params = False, init_guess = None):
        if init_guess == "stop":
            return None

        force_guess = False
        
        guess = [60,10,5,0.845,100]
        #print "1234"
        #print f,p, guess
        print time,excitation
        try:
            popt, copt = curve_fit(self.rot_ramsey_decay, phase, excitation, p0=guess,bounds=((0,-np.inf,-1),(1,np.inf,1)))

            return popt[0], popt[1] # sigma_l, omega_khz, delta_kHz, _f_trap_MHz, f_rot_kHz

        except:
            print "problem with the fit"
            return None

    def rot_ramsey_decay(self, times_us, sigma_l, Omega_kHz, delta_kHz, f_trap_MHz, f_rot_kHz):
        # convert inputs to SI
        times = 1e-6 * times_us
        Omega = 1e3 * 2*np.pi * Omega_kHz
        delta = 1e3 * 2*np.pi * delta_kHz
        w_trap = 1e6 * 2*np.pi * f_trap_MHz
        w_rot = 1e3 * 2*np.pi * f_rot_kHz
        #fix parameters for diffusion measurment
        scale = 1
        Delta_l = 1
        # calculate moment of inertia
        m = 40*scc.atomic_mass
        r = 1/2.0 * (scc.e**2/(4*np.pi*scc.epsilon_0) * 2.0/(m*(w_trap**2 - w_rot**2)))**(1/3.0) #rotor radius
        I = 2*m*r**2  # moment of inertia

        # calculate l distribution and detunings
        l_0 = I*w_rot/scc.hbar
        ls = np.arange(int(l_0-3*sigma_l), int(l_0+3*sigma_l))
        c_ls_unnorm = np.exp(-(ls-l_0)**2/(4.0*sigma_l**2))
        c_ls = c_ls_unnorm/np.linalg.norm(c_ls_unnorm)
        delta_ls = scc.hbar*Delta_l/I*(l_0-ls) + delta

        def calc_ramsey_exc(c_ls, delta_ls, Omega, T):
            Omega_gens = np.sqrt(Omega**2 + delta_ls**2) #generalized Rabi frequency
            u1s = np.pi*Omega_gens/(4*Omega)
            u2s = delta_ls*T/2.0
            return sum(np.abs(c_ls)**2 * (2*Omega/Omega_gens**2*np.sin(u1s) * (Omega_gens*np.cos(u1s)*np.cos(u2s) - delta_ls*np.sin(u1s)*np.sin(u2s)))**2)
            

        return [scale * calc_ramsey_exc(c_ls, delta_ls, Omega, T) for T in times]

    @classmethod
    def rabi_fit(cls, time, excitation, trap_frequency_MHz, return_all_params = False, init_guess = None):
        if init_guess == "stop":
            return None

        import scipy.constants as scc
        from scipy.special.orthogonal import eval_genlaguerre as laguerre
        
        def rabi_model(times_us, Omega_kHz, delta_kHz, f_trap_MHz, nbar, scale):
            m = 40*scc.atomic_mass

            times = 1e-6 * times_us
            Omega = 1e3 * 2*np.pi * Omega_kHz
            delta = 1e3 * 2*np.pi * delta_kHz
            w_trap = 1e6 * 2*np.pi * f_trap_MHz


            eta = 2*np.pi/(729e-9)*np.sqrt(scc.hbar/(2*m*w_trap))

            nmax = 1000
            ns = np.arange(nmax)

            rabi_coupling = lambda n: np.exp(-1./2*eta**2) * laguerre(n, 0, eta**2)
            omega_n = Omega*rabi_coupling(ns)
            p_n = 1.0/ (nbar + 1.0) * (nbar / (nbar + 1.0))**ns
            exc_n = np.outer(p_n * omega_n**2/(omega_n**2+delta**2), np.ones_like(times)) * np.sin(np.outer(np.sqrt(omega_n**2 + delta**2), times/2.0))**2
            exc = scale * np.sum(exc_n, axis = 0)

            return exc

        def guess_omega_rabi(x, y):
            step = x[1] - x[0]
            mean = np.mean(y)
            for x0, y0 in zip(x,y):
                if y0 > mean: break
            t_2pi  = 4*(x0-step/2.0)
            return 1e3 * 1.0/(t_2pi)

        model = lambda t, Omega, nbar: rabi_model(t, Omega, 0.0, trap_frequency_MHz, nbar, 1.0)
        guess_Omega = guess_omega_rabi(time, excitation)
        guess_nbar = 20.0

        try:
            popt, copt = curve_fit(model, time, excitation, p0=(guess_Omega, guess_nbar))
            print popt
            if return_all_params:
                return popt[0], popt[1] # Omega, nbar
            else:
                return popt[1] # return only nbar
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
    def get_show_parameters(cls):
        show = []
        cls.loop_get_show(show)
        return show

    @classmethod
    def loop_get_show(cls, li):
        for item in cls.show_params:
            if item not in li:
                li.append(item)
        try:
            if type(cls.sequence) == list:
                for subcls in cls.sequence:
                    if type(subcls) == tuple:
                        subcls = subcls[0]
                    subcls.loop_get_show(li)
            elif type(cls.sequence) == type:
                cls.sequence.loop_get_show(li)
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

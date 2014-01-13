'''

Container class for a Rabi flop fit

'''

from datafit import DataFit
import numpy as np
import timeevolution as te
from labrad import units as U

class RabiFlop(DataFit):
    
    def __init__(self, raw):
        DataFit.__init__(self, raw)
        
        self.guess_dict = {'nbar': lambda: 5.0, 'f_rabi', self.guess_f_rabi,
                           'delta': lambda: 0.0, 'delta_fluctuations': lambda: 0.0,
                           'trap_freq': lambda: 1.0, 'sideband': lambda: 0.0,
                           'nmax': lambda: 1000, 'projection': np.pi/4}

        self.parameters = self.guess_dict.keys()

    def guess(self, param):
        return self.guess_dict[param]()
    
    def guess_f_rabi(self):
        # think about doing something more sophisticated

        return 5e3.
    
    def model(self, params, x):
        
        nbar = params['nbar'].value
        f_rabi = params['f_rabi'].value
        delta = params['delta'].value
        delta_fluct = params['delta_fluctuations'].value
        trap_freq = params['trap_freq'].value
        sideband = params['sideband'].value
        nmax = params['nmax'].value
        projection = params['projection'].value
        
        flop = te.time_evolution(trap_frequency = U.WithUnit(trap_freq, 'MHz'), projection = projection, 
                                 sideband_order = sideband, nmax = nmax)
        
        evolution = flop.state_evolution_fluc(x*10**-6, nbar, f_rabi, delta, delta_fluct, n_fluc = 5.0 )
        
        return evolution
        

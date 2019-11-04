# Fitter class for Rabi flops

from model import Model, ParameterInfo
from rabi.motional_distribution import motional_distribution as md
from rabi.rabi_coupling import rabi_coupling as rc

import numpy as np

class Rabi(Model):

    def __init__(self):
        self.parameters = {
            'omega_rabi': ParameterInfo('f_rabi', 0, self.guess_omega_rabi),
            'nbar': ParameterInfo('nbar', 1, lambda x, y: 5, True),
            'eta':ParameterInfo('eta', 2, lambda x, y: 0.05, vary=False),
            'delta': ParameterInfo('delta', 3, lambda x,y: 0, vary=False),
            'sideband_order': ParameterInfo('sideband_order', 4, lambda x, y: 0, vary = False),
            'excitation_scaling': ParameterInfo('excitation_scaling', 5, lambda x,y: 1.0, vary = False)
            }

    def model(self, x, p):

        omega_rabi = p[0]
        nbar = p[1]
        eta = p[2]
        delta = p[3]
        sideband_order = p[4]
        excitation_scaling = p[5]
        
        nmax = 1000

        omega = rc.compute_rabi_coupling(eta, sideband_order, nmax)
        ones = np.ones_like(x)
        p_n = md.thermal(nbar, nmax)
        if 1 - p_n.sum() > 1e-6:
            raise Exception ('Hilbert space too small, missing population')
        if delta == 0:
            #prevents division by zero if delta == 0, omega == 0
            effective_omega = 1.
        else:
            effective_omega = omega/np.sqrt(omega**2+delta**2)
        result = np.outer(p_n * effective_omega, ones) * (np.sin( np.outer( np.sqrt(omega**2+delta**2)*omega_rabi/2, x ))**2)
        result = np.sum(result, axis = 0)
        result = excitation_scaling * result
        return result

    def guess_omega_rabi(self, x, y):
        '''
        Take the first time the flop goes above the average excitation of the whole scan
        to be pi/4
        '''
        
        mean = np.mean(y)
        for x0, y0 in zip(x,y):
            if y0 > mean: break
        t_2pi  = 4*x0
        return 2*np.pi/(t_2pi)
        

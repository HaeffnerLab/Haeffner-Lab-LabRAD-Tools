"""
This class defines a Rabi Flop (arbitrary sideband) to fit and its parameters
"""
import numpy as np
from fitcurve import CurveFit
from scipy.special.orthogonal import eval_genlaguerre as laguer
from labrad import units as U

class rabi_flop():
    def __init__(self, trap_frequency, sideband_order,nmax = 1000):
        m = 40 * U.amu
        hbar = U.hbar
        wavelength= U.WithUnit(729,'nm')
        
        self.sideband_order = sideband_order #0 for carrier, 1 for 1st blue sideband etc
        self.n = np.linspace(0, nmax,nmax +1) #how many vibrational states to consider
        self.eta = 2.*np.cos(np.pi/4)*np.pi/wavelength['m']*np.sqrt(hbar['J*s']/(2.*m['kg']*2.*np.pi*trap_frequency['Hz']))
        self.rabi_coupling=self.rabi_coupling()
        
    def rabi_coupling(self):
        eta = self.eta
        n = self.n
        sideband=np.abs(self.sideband_order)
        x=1
        for k in np.linspace(1,sideband,sideband):
            x=x*(n+k)
        result = eta**sideband/2.*np.exp(-eta**2./2.)*laguer(n,sideband,eta**2.)/np.sqrt(x)
        return result
        
    def state_evolution(self, nbar, f_Rabi, t):
        sideband=self.sideband_order
        nplus=0
        if sideband<0:
            nplus=-sideband
        n = self.n
        #level population probability for a given nbar, see Leibfried 2003 (57)
        p = ((float(nbar)/(nbar+1.))**(n+nplus))/(nbar+1.)
        
        if np.abs(1-np.sum(p,axis=0))>0.00001:
            print 'Warning: nmax may not be high enough for chosen value of nbar\n missing probability = {0}'.format(1-np.sum(p,axis=0))

        ones = np.ones_like(t)
        rabi_coupling = self.rabi_coupling

        result = np.outer(p, ones) * np.sin( np.outer(2.*np.pi*f_Rabi*rabi_coupling, t ))**2
        result = np.sum(result, axis = 0)
        return result

class FitRabiflop(CurveFit):

    def __init__(self, parent):
        self.parent = parent
        self.curveName = 'Rabi Flop'
        self.parameterNames = ['Nbar', 'Rabi_Frequency']
   
    def fitFunc(self, x, p):
        """ 
            Lorentzian
            p = [gamma, center, I, offset]
        
        """   
        sideband_order=0
        nmax=1000
        trap_frequency=U.WithUnit(2.8, 'MHz') 
        flop = rabi_flop(nmax=nmax,trap_frequency = trap_frequency, sideband_order = sideband_order)        
        evolution = flop.state_evolution(p[0], p[1], x)
        return evolution
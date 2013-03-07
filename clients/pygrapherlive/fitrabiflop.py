"""
This class defines a Rabi Flop (arbitrary sideband) to fit and its parameters
"""
#import numpy as np
from fitcurve import CurveFit
from labrad import units as U
import timeevolution as te

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
        flop = te.time_evolution(nmax=nmax,trap_frequency = trap_frequency, sideband_order = sideband_order)        
        evolution = flop.state_evolution(p[0], p[1], x)
        return evolution
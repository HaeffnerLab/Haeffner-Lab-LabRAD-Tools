"""

This class defines a Lorentzian curve to fit and its parameters

"""
import numpy as np
from fitcurve import CurveFit

class FitLorentzian(CurveFit):

    def __init__(self, parent):
        self.parent = parent
        self.curveName = 'Lorentzian'
        self.parameterNames = ['Gamma', 'Center', 'I', 'Offset']
   
    # idk, something like this?
    def fitFunc(self, x, p):
        """ 
            Lorentzian
            p = [gamma, center, I, offset]
        
        """   
        curve = p[3] + p[2]*(p[0]**2/((x - p[1])**2 + p[0]**2))# Lorentzian
        return curve 
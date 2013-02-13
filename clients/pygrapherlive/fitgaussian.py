"""

This class defines a Gaussian curve to fit and its parameters

"""
import numpy as np
from fitcurve import CurveFit

class FitGaussian(CurveFit):

    def __init__(self, parent):
        self.parent = parent
        self.curveName = 'Gaussian'
        self.parameters = {
                           'Height':        2.0,
                           'Center':        2.0,
                           'Sigma':         2.0,
                           'Offset':        2.0,
                          }
   
    # idk, something like this?
    def fitFunc(self, x, p):
        """ 
            Gaussian
            p = [height, center, sigma, offset]
        
        """   
        curve = p[0]*np.exp(-(((x - p[1])/p[2])**2)/2) + p[3]# gaussian
        return curve    
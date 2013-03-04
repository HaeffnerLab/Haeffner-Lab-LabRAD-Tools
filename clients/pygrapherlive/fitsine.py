"""
This class defines a cosine function to fit and its parameters
"""
import numpy as np
from fitcurve import CurveFit

class FitCosine(CurveFit):

    def __init__(self, parent):
        self.parent = parent
        self.curveName = 'Cosine'
        self.parameterNames = [ 'Frequency','Phase','Contrast','Offset']
        self.parameterValues = [1.0, 0.0, 1.0, 0.0]
        
   
    def fitFunc(self, x, p):      
        evolution = p[2] / 2.0 * np.cos(2.*np.pi*p[0]*x+p[1]) + p[3] + 0.5 
        return evolution
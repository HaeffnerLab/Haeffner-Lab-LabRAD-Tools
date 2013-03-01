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
   
    def fitFunc(self, x, p):      
        evolution = p[2]*np.cos(2.*np.pi*p[0]*x+p[1])+p[3]
        return evolution
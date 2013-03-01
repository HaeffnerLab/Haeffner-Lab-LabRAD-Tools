"""
This class defines Ramsey Fringes to fit and its parameters
"""
import numpy as np
from fitcurve import CurveFit

class FitRamseyFringe(CurveFit):

    def __init__(self, parent):
        self.parent = parent
        self.curveName = 'Ramsey Fringes'
        self.parameterNames = [ 'Frequency','T2','Phase','Contrast','Offset']
   
    def fitFunc(self, x, p):      
        evolution = p[3]*np.exp(-x/p[1])*(np.cos(np.pi*p[0]*x+p[2])**2-.5)+.5+p[4]
        return evolution
"""

This class defines a line curve to fit and its parameters

"""
import numpy as np
from fitcurve import CurveFit

class FitLine(CurveFit):

    def __init__(self, parent):
        self.parent = parent
        self.curveName = 'Line'
        self.parameters = {
                           'Slope':      2.0,
                           'Offset':     2.0,
                          }

    # idk, something like this?
    def fitFunc(self, x, p):
        """ 
            Line
            p = [slope, offset]
        
        """   
        curve = fitFunc = p[0]*x + p[1] #line
        return curve    
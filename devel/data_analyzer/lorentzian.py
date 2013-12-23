'''

Container class for a Lorentzian fit

Classes which inherit from DataFit should implement 

1. a guess() function which takes the parameter name as an argument 
and returns an automized initial guess

2. a model() function containing the analytic form you would like to fit

3. Possibly other data processing functions? Not sure yet.

'''

from datafit import DataFit
import numpy as np

class Fittable(DataFit):

    def __init__(self, raw):
        super(DataFit, self).__init__(raw)

        self.guess_dict = {'FWHM':self.guess_hwhm, 'center':self.guess_center,
                           'height':self.guess_height, 'bgrnd':self.guess_bgrnd}

    def guess(self, param):
        return self.guess_dict[param](self.raw)

    def guess_fwhm(self):
        xmax = self.dataX.max()
        xmin = self.dataX.min()
        return (xmax - xmin)/6.0

    def guess_center(self):
        j = list(self.dataY).index( self.dataY.max() )
        return self.dataX[j]
    def guess_height(self):
        return self.dataY.max()
    def guess_bgrnd(self):
        return 0

    def model(params, x):

        bgrnd = params['bgrnd'].value
        fwhm = abs(params['FWHM'].value)
        center = params['center'].value
        height = params['height'].value

        gamma = fwhm/2.

        model = bgrnd + height*(gamma)**2/( (x - center)**2 + (gamma)**2)

        return model

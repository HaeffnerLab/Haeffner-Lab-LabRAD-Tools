# Fitter class for Gaussians

from model import Model, ParameterInfo
import numpy as np

class Gaussian(Model):

    def __init__(self):
        self.parameters = {
            'mean':ParameterInfo('mean', 0, self.guess_mean),
            'A': ParameterInfo('A', 1, self.guess_A),
            'sigma': ParameterInfo('sigma', 2, self.guess_sigma),
            'offset': ParameterInfo('offset', 3, self.guess_offset)
            }

    def model(self, x, p):

        '''
        Base Gaussian model defined as
        http://mathworld.wolfram.com/GaussianFunction.html

        without the normalization prefactor and adding
        a constant offset
        '''

        mu = p[0]; A = p[1]; sigma_squared = p[2]**2; b = p[3]
        return A*np.exp( -(x - mu)**2 / (2*sigma_squared) ) + b

    def guess_mean(self, x, y):
        max_index = np.argmax(y)
        return x[max_index]

    def guess_A(self, x, y):
        return max(y)

    def guess_sigma(self, x, y):
        return (max(x) - min(x))/6.0

    def guess_offset(self, x, y):
        return 0.0

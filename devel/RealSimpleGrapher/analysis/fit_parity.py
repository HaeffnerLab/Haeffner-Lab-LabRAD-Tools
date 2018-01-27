# Fitter class for Gaussians

from model import Model, ParameterInfo
import numpy as np

class Parity(Model):

    def __init__(self):
        self.parameters = {
            'amp': ParameterInfo('amp', 0, self.guess_amp),
            'phase': ParameterInfo('phase', 1, self.guess_phase),
            'offset': ParameterInfo('offset', 2, self.guess_offset)
            }

    def model(self, x, p):
        '''
        Sine fit

        '''
        a = p[0]
        b = p[1]
        c = p[2]
        return np.abs(a) * np.sin( np.deg2rad(2*x-b) ) + c

    def guess_amp(self, x, y):
        max_index = np.argmax(y)
        min_index = np.argmin(y)
        return x[max_index] - x[min_index]

    def guess_phase(self, x, y):
        return 0.0

    def guess_offset(self, x, y):
        return 0.0

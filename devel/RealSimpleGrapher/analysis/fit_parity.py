# Fitter class for Gaussians

from model import Model, ParameterInfo
import numpy as np

class Parity(Model):
    not_checkable = ["freq"]
    
    def __init__(self):
        self.parameters = {
            'amp': ParameterInfo('amp', 0, self.guess_amp),
            'phase': ParameterInfo('phase', 1, self.guess_phase),
            'offset': ParameterInfo('offset', 2, self.guess_offset),
            'freq': ParameterInfo('freq', 3, self.guess_freq),

            }

    def model(self, x, p):
        '''Sine fit'''
        a, b, c, d = p
        return np.abs(a) * np.sin(d * np.deg2rad(x - b)) + c

    def guess_amp(self, x, y):
        max_index = np.argmax(y)
        min_index = np.argmin(y)
        return x[max_index] - x[min_index]

    def guess_phase(self, x, y):
        return 0.0

    def guess_offset(self, x, y):
        return 0.0

    def guess_freq(self, x, y):
        return 2.0

# Fitter class for linear fits

from model import Model, ParameterInfo
import numpy as np

class Linear(Model):

    def __init__(self):
        self.parameters = {
            'm':ParameterInfo('m', 0, self.guess_m),
            'b':ParameterInfo('b', 1, self.guess_b)
            }

    def model(self, x, p):
        m = p[0]
        b = p[1]
        return m*x + b

    def guess_m(self, x, y):
        dx = x[-1] - x[0]
        dy = y[-1] - y[0]
        return dy/dx

    def guess_b(self, x, y):
        m = self.guess_m(x, y)
        ybar = np.mean(y)
        xbar = np.mean(x)
        return ybar - m*xbar

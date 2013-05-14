import numpy as np
import lmfit
import matplotlib
matplotlib.use('Qt4Agg')
from matplotlib import pyplot

'''
define the function
'''
def gaussian_model(params, x):
    amplitude = params['amplitude'].value
    background_level = params['background_level'].value
    center = params['center'].value
    sigma = params['sigma'].value
    model =  background_level + amplitude * np.exp( - (x - center)**2 / (2 * sigma**2))
    return model
'''
define how to compare data to the function
'''
def gaussian_fit(params , x, data):
    model = gaussian_model(params, x)
    return model - data
'''
generate some random data
'''
x_data = np.linspace(0, 100, 1000)
y_data = 10 + 5 * np.exp( - (x_data - 50)**2 / (2 * 10**2))
pyplot.plot(x_data, y_data, '+', markersize = 5.0, label = 'data')

'''
define the fitting parameters, with initial guesses. 
Here can also specify if some parameters are fixed, and the range of allowed values
'''
params = lmfit.Parameters()
params.add('amplitude', value = 10, max = 1000.0)
params.add('center', value = 1)
params.add('sigma', value = 1, min = 0.0)
params.add('background_level', value = 10, vary = False)
'''
run the fitting
'''
result = lmfit.minimize(gaussian_fit, params, args = (x_data, y_data))
'''
plot the result
'''
fit_values  = y_data + result.residual
pyplot.plot(x_data, fit_values, 'r', label = 'fitted')
'''
print out fitting summary
'''
lmfit.report_errors(params)

pyplot.legend()
pyplot.show()
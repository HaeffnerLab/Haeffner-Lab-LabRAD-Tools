from __future__ import division
import numpy as np
from matplotlib import pyplot
import matplotlib
from scipy.interpolate import interp1d

data = np.loadtxt("power_calibration_raw.csv", delimiter = ',')

python_power = data[:,0]
real_power = data[:,1]

## interpolation

y = python_power
x = real_power

## create interpolated function
f = interp1d(x,y)
f2 = interp1d(x,y, kind = 'cubic')

print f2(0)

x_new = np.linspace(x.min(),x.max(),num=1000)
 
pyplot.plot(real_power,python_power, 'o')
 
pyplot.plot(x_new, f(x_new))
pyplot.plot(x_new, f2(x_new))
pyplot.show()
import numpy as np
from scipy import optimize

def func(x, p):
    return p[0] * np.exp(-p[1] * x) + p[2]

xdata = np.linspace(0, 4, 50)
y = func(xdata, [2.5, 1.3, 0.5])
ydata = y + 0.2 * np.random.normal(size=len(xdata))

def residual(p):
    return ydata - func(xdata, p)

result = optimize.leastsq(residual, [2.5, 1.3, 0.5])
print result[0]

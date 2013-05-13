import matplotlib
matplotlib.use('Qt4Agg')
from matplotlib import pyplot

figure = pyplot.figure()
figure.clf()
pyplot.plot([1,2,3], [1,2,3])
pyplot.show()
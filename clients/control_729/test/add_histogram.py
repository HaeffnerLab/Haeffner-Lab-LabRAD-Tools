import numpy
import labrad
import time

cxn = labrad.connect()
dv = cxn.data_vault
totalReadouts = numpy.random.randint(50, 150, 200)
hist, bins = numpy.histogram(totalReadouts, 50)

dirappend = time.strftime("%Y%b%d_%H%M_%S",time.localtime())
directory = ['','Experiments', 'scan729DDS', dirappend]
dv.cd(directory ,True )

dv.new('Histogram',[('Counts', 'Arb')],[('Occurence','Arb','Arb')] )
dv.add(numpy.vstack((bins[0:-1],hist)).transpose())
dv.add_parameter('Histogram729', True)

print 'DONE Adding Histogram'
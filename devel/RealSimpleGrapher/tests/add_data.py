# adds random data to plot

import time
import labrad
import random

cxn = labrad.connect()
dv = cxn.data_vault
cxt = cxn.context()

localtime = time.localtime()
datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
dirappend = [ time.strftime("%Y%b%d",localtime) ,time.strftime("%H%M_%S", localtime)]
directory = ['','Experiments']
directory.extend(['TestData'])
directory.extend(dirappend)
dv.cd(directory ,True, context = cxt)
output_size = 2
dependents = [('Excitation','Ion {}'.format(ion),'Probability') for ion in range(output_size)]
ds = dv.new('Rabi Flopping {}'.format(datasetNameAppend),[('Excitation', 'us')], dependents , context = cxt)
dv.add_parameter('plotLive', True, context = cxt)
grapher = cxn.grapher
grapher.plot(ds, 'pmt', False)

i = 0
while True:
    submission = [i]
    submission.extend([random.random() for x in range(output_size)])
    dv.add(submission, context=cxt)
    i+=1
    time.sleep(0.01)

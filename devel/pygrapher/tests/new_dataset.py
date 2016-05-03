# add new data to the datavault to test listening
import time
import random
import labrad

cxn = labrad.connect()
context = cxn.context()
dv = cxn.data_vault
dir = ['', 'Test']

localtime = time.localtime()
datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
dirappend = [ time.strftime("%Y%b%d",localtime) ,time.strftime("%H%M_%S", localtime)]
dir.extend(dirappend)

dv.cd(dir, True, context = context)
dv.new('Random {}'.format(datasetNameAppend), [('Random', 'us')], [('Random', 'Arb', 'Arb')], context = context)
dv.add_parameter('plotLive', True, context = context)

for i in range(1000):
    dv.add((i, random.random()), context = context)
    time.sleep(0.5)

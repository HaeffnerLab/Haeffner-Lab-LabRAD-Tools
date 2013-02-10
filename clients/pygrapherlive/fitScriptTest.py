import labrad
import math
import time
from numpy import *

y1 = [None] * 200000
y2 = [None] * 200000
y3 = [None] * 200000


def generateData():
    for i in range(51):
        y1[i] = math.sin(i)+ 2
        y2[i] = math.cos(i)+ 32
        y3[i] = math.sin(i)+ 64
generateData()
cxn = labrad.connect()
cxn.server = cxn.data_vault
cxn.data_vault.cd('Sine Curves')
cxn.data_vault.new('Sine Curves', [('x', 'num')], [('y1','866 ON','num'),('y2','866 OFF','num'),('y3','Differential Signal','num')])
cxn.data_vault.add_parameter('Window', ['pmt'])
cxn.data_vault.add_parameter('plotLive', True)

i = 0
while (i < 40):
    cxn.data_vault.add([i, y1[i] + i, y2[i] + i, y3[i] + i])
    data = [i, y1[i], y2[i], y3[i]]
    print data
    time.sleep(.1)
    i = i + 1

cxn.data_vault.add_parameter('Fit', ['1', 'Lorentzian', '[-3220.213428227798, -440.65676408926481, -1586.420935896509, 3021.7453388352142]'])
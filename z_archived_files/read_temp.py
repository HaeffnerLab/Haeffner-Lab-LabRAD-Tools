import labrad
import time
import datetime
import numpy as np
from keithley_helper import voltage_conversion

vc = voltage_conversion()
import pylab as pl
#fname = 'c:/data_resonator/temperature.dat'
fname = 'Y:/resonator-cooling/Data/resonator_auto/temperature_cernox.dat'

cxn = labrad.connect()
k = cxn.keithley_2100_dmm()

k.select_device()
ll = []
while(True):
    a = k.get_dc_volts()
    ll.append(a)
    print vc.conversion(a)
    #pl.plot(ll)
#    pl.ion()
    #pl.show()
    #np.savetxt(fname,ll)
    time.sleep(60)
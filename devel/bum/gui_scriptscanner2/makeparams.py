import labrad
from labrad.units import WithUnit as U
cxn = labrad.connect()
sc =  cxn.scriptscanner

sc.new_parameter('RabiExcitation', 'frequency', ('parameter', [U(-30, 'kHz'), U(30, 'kHz'), U(0, 'kHz')]))
sc.new_parameter('RabiExcitation', 'duration', ('parameter', [U(0, 'us'), U(10000, 'us'), U(10, 'us')]))
sc.new_parameter('DopplerCooling', 'duration', ('parameter', [U(0, 'ms'), U(20, 'ms'), U(5, 'ms')]))

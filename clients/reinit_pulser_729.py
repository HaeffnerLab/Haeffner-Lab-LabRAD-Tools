import labrad

try:
    cxn = labrad.connect('192.168.169.49')
    cxn.pulser_729.reinitialize_dds()
except Exception as e:
    print e
print 'DONE'   
import labrad
cxn = labrad.connect()
cxnlab = labrad.connect('192.168.169.49')
dv = cxn.data_vault
pulser = cxn.pulser
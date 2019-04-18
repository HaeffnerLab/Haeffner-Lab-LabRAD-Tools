import labrad


cxn=labrad.connect()

dac = cxn.dac_server

channels = ['01','02','03','04','05','06','07','08','09','10','11']

for el in channels:
    dac.set_individual_analog_voltages([(el,float(el)/10.)])

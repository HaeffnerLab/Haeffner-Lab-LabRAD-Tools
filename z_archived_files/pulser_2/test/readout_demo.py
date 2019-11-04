import labrad
from labrad.units import WithUnit

with labrad.connect() as cxn:
    pulser = cxn.pulser
    pulser.new_sequence()
    pulser.add_ttl_pulse(('ReadoutCount', WithUnit(1, 'ms'), WithUnit(1000, 'ms')))
    pulser.program_sequence()
    pulser.start_number(10)
    pulser.wait_sequence_done()
    pulser.stop_sequence()
    readout = pulser.get_readout_counts().asarray
    print readout
    
#    timetags = pulser.get_timetags().asarray
#    print len(timetags)
#    print timetags
import labrad
from labrad.units import WithUnit

with labrad.connect() as cxn:
    pulser = cxn.pulser
    pulser.new_sequence()
    pulser.add_ttl_pulse(('TimetagCount', WithUnit(1, 'ms'), WithUnit(1000, 'ms')))
    pulser.program_sequence()
    pulser.start_number(1)
    pulser.wait_sequence_done()
    pulser.stop_sequence()
    timetags = pulser.get_timetags().asarray
    print len(timetags)
    print timetags
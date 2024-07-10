from servers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit
from treedict import TreeDict
from servers.pulser.pulse_sequences.plot_sequence import SequencePlotter
import labrad

### main code
cxn = labrad.connect() ##make labrad connection
p = cxn.pulser ## get the pulser server

p.new_sequence() ## initialize a new sequence

## add some ttl switching
p.add_ttl_pulse('ttl_0',WithUnit(0,'ms'),WithUnit(100,'ms'))
p.add_ttl_pulse('ttl_0',WithUnit(200,'ms'),WithUnit(100,'ms'))
p.add_ttl_pulse('ttl_0',WithUnit(400,'ms'),WithUnit(100,'ms'))

## add a list of DDS

amp1 = WithUnit(-20, 'dBm')
amp2 = WithUnit(-30, 'dBm')

# DDS = [('DDS_0', WithUnit(0.1, 'ms'), WithUnit(0.002, 'ms'), WithUnit(50.0, 'MHz'), WithUnit(-20.0, 'dBm'), WithUnit(0.0,'deg'),WithUnit(0,'MHz')),
#        ('DDS_0', WithUnit(0.102, 'ms'), WithUnit(0.001, 'ms'), WithUnit(50.0, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(0.0,'deg'),WithUnit(0,'MHz')),
#        ('DDS_0', WithUnit(0.104, 'ms'), WithUnit(0.002, 'ms'), WithUnit(50.0, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(0.0,'deg'),WithUnit(0,'MHz')),
#        ('DDS_0', WithUnit(0.106, 'ms'), WithUnit(0.002, 'ms'), WithUnit(10.0, 'MHz'), WithUnit(-20.0, 'dBm'), WithUnit(0.0,'deg'),WithUnit(0,'MHz'))
#        ]

DDS = [('DDS_0', WithUnit(0.1, 'ms'), WithUnit(0.002, 'ms'), WithUnit(2.0, 'MHz'), WithUnit(-20.0, 'dBm'), WithUnit(0.0,'deg'),WithUnit(0,'MHz')),
       ('DDS_0', WithUnit(0.102, 'ms'), WithUnit(5.0, 'ms'), WithUnit(5.0, 'MHz'), WithUnit(-20.0, 'dBm'), WithUnit(0.0,'deg'),WithUnit(0.6,'MHz')),
       ('DDS_0', WithUnit(5.102, 'ms'), WithUnit(0.002, 'ms'), WithUnit(5.0, 'MHz'), WithUnit(-20.0, 'dBm'), WithUnit(0.0,'deg'),WithUnit(0.0,'MHz')),
       ('DDS_0', WithUnit(5.104, 'ms'), WithUnit(5.0, 'ms'), WithUnit(2.0, 'MHz'), WithUnit(-20.0, 'dBm'), WithUnit(0.0,'deg'),WithUnit(1.5,'MHz'))
       ]

## program DDS
p.add_dds_pulses(DDS)

##program sequence
p.program_sequence()

##start once
p.start_number(2)

# ##wait until sequence is done
p.wait_sequence_done()
# 
# ## stop sequence
p.stop_sequence()
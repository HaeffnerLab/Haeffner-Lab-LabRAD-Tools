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

DDS = [('DDS_0', WithUnit(0.1, 'ms'), WithUnit(999.9, 'ms'), WithUnit(85.0, 'MHz'), WithUnit(-20.0, 'dBm'), WithUnit(0.0,'deg'),WithUnit(0,'MHz')),
       ('DDS_0', WithUnit(1000, 'ms'), WithUnit(6000, 'ms'), WithUnit(88.0, 'MHz'), WithUnit(-20.0, 'dBm'), WithUnit(0.0,'deg'),WithUnit(0.01,'MHz'))
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
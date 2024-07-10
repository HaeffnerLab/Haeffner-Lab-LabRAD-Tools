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

## add a list of DDS ##

amp1 = WithUnit(-30,'dBm')
amp2 = WithUnit(-40,'dBm')
no_amp_ramp = WithUnit(0,'dB')


DDS = [('DDS_0', WithUnit(0.1, 'ms'), WithUnit(199.9, 'ms'), WithUnit(88.0, 'MHz'), WithUnit(-63,'dBm'), WithUnit(0.0,'deg'),WithUnit(0.0, 'MHz'),no_amp_ramp),
       ('DDS_0', WithUnit(200.0, 'ms'), WithUnit(2300.0, 'ms'), WithUnit(92.0, 'MHz'), WithUnit(-20,'dBm'), WithUnit(0.0,'deg'),WithUnit(0.003, 'MHz'),WithUnit(0.05,'dB')),
       ('DDS_0', WithUnit(2500.0, 'ms'), WithUnit(2300.0, 'ms'), WithUnit(88.0, 'MHz'), WithUnit(-62,'dBm'), WithUnit(0.0,'deg'),WithUnit(0.003, 'MHz'),WithUnit(0.05,'dB')),
       ('DDS_1', WithUnit(0.1, 'ms'), WithUnit(199.9, 'ms'), WithUnit(86.0, 'MHz'), WithUnit(-63,'dBm'), WithUnit(0.0,'deg'),WithUnit(0.0, 'MHz'),no_amp_ramp),
       ('DDS_1', WithUnit(200.0, 'ms'), WithUnit(2300.0, 'ms'), WithUnit(82.0, 'MHz'), WithUnit(-20,'dBm'), WithUnit(0.0,'deg'),WithUnit(0.003, 'MHz'),WithUnit(0.05,'dB')),
       ('DDS_1', WithUnit(2500.0, 'ms'), WithUnit(2300.0, 'ms'), WithUnit(86.0, 'MHz'), WithUnit(-62,'dBm'), WithUnit(0.0,'deg'),WithUnit(0.003, 'MHz'),WithUnit(0.05,'dB'))
       ]

## program DDS
p.add_dds_pulses(DDS)

##program sequence##
p.program_sequence()

##start once
for i in range(1):
    #print i
    p.start_number(2)

# ##wait until sequence is done
    p.wait_sequence_done()
# 
# ## stop sequence
p.stop_sequence()
import labrad
import numpy
import time
cxn = labrad.connect()
pulser = cxn.pulser
#demo pulse sequence
pulser.new_sequence()
duration = .1
channels = pulser.get_channels()

for i in range(len(channels)):
    pulser.add_ttl_pulse(channels[i],  i * duration, duration)

pulser.program_sequence()
pulser.start_infinite()

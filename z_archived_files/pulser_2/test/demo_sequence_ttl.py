import labrad
from labrad.units import WithUnit
with labrad.connect() as cxn:
    duration = WithUnit(50, 'ms')
    pulser = cxn.pulser
    pulser.new_sequence()
    channels = pulser.get_channels()
    channel_names = [chan[0] for chan in channels]
    for i in range(len(channels)):
        start = i * duration
        pulser.add_ttl_pulse((channel_names[i],  start , duration))
    pulser.program_sequence()
    pulser.start_number(10)
    pulser.wait_sequence_done()
    pulser.stop_sequence()
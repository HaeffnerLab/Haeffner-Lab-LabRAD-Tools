import labrad
from labrad.units import WithUnit
with labrad.connect() as cxn:
    duration = WithUnit(100, 'ms')
    pulser = cxn.pulser
    pulser.new_sequence()
    channels = pulser.get_channels()
    channel_names = [chan[0] for chan in channels]
    
    #print channel_names
    
#     for i in range(len(channels)):
#         start = i * duration
#         pulser.add_ttl_pulse((channel_names[i],  start , duration))

    pulser.add_ttl_pulse('channel_0',WithUnit(0,'ms'),WithUnit(100,'ms'))
    pulser.add_ttl_pulse('channel_0',WithUnit(200,'ms'),WithUnit(100,'ms'))
    pulser.add_ttl_pulse('channel_0',WithUnit(400,'ms'),WithUnit(100,'ms'))
    
    pulser.add_ttl_pulse('AdvanceDDS',WithUnit(10,'ms'),WithUnit(1,'ms'))
    pulser.add_ttl_pulse('AdvanceDDS',WithUnit(20,'ms'),WithUnit(1,'ms'))
    pulser.add_ttl_pulse('AdvanceDDS',WithUnit(100,'ms'),WithUnit(1,'ms'))
    
    pulser.add_ttl_pulse('channel_1',WithUnit(0,'ms'),WithUnit(100,'ms'))
    pulser.add_ttl_pulse('channel_2',WithUnit(200,'ms'),WithUnit(100,'ms'))
    pulser.add_ttl_pulse('channel_3',WithUnit(400,'ms'),WithUnit(100,'ms'))
    
    pulser.add_ttl_pulse('ResetDDS',WithUnit(500,'ms'),WithUnit(1,'ms'))
    
    
#     pulser.program_sequence()
#     
#     ttl = cxn.pulser.human_readable_ttl()
#     sp = SequencePlotter(ttl.asarray,None, channels)
#     sp.makePlot()
        
    pulser.program_sequence()
    pulser.start_number(10)
    pulser.wait_sequence_done()
    pulser.stop_sequence()
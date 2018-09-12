from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

class turn_off_all(pulse_sequence):
    
    def sequence(self):
        self.start = WithUnit(10, 'us')
        dur = WithUnit(50, 'us')
        for channel in ['729global', '729local','397','854','866','radial']:
            self.addDDS(channel, self.start, dur, WithUnit(0, 'MHz'), WithUnit(-63., 'dBm') )
        self.end = self.start + dur
        

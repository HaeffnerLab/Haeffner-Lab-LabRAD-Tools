from common.okfpgaservers.pulser_2.pulse_sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

class sampleDDS(pulse_sequence):
    
    def sequence(self):
        start_first = WithUnit(10, 'us')
        on_time = WithUnit(500, 'ms')
        off_time = WithUnit(500, 'ms')
        start_second = start_first + on_time + off_time
        freq = WithUnit(110.0, 'MHz')
        ampl = WithUnit(-23.0, 'dBm')
        self.addDDS('110DP', start_first, on_time, freq, ampl)
        self.addDDS('110DP', start_second, on_time, freq, ampl)
 
if __name__ == '__main__':
    import labrad
    cxn = labrad.connect()
    cs = sampleDDS()
    cs.programSequence(cxn.pulser)
    cxn.pulser.start_number(10)
    cxn.pulser.wait_sequence_done()
    cxn.pulser.stop_sequence()
from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit
from treedict import TreeDict

class sampleDDS(pulse_sequence):
    
    def sequence(self):
        start_first = WithUnit(10, 'us')
        on_time = WithUnit(500, 'ms')
        off_time = WithUnit(500, 'ms')
        start_second = start_first + on_time + off_time
        freq = WithUnit(10.0, 'MHz')
        ampl = WithUnit(-23.0, 'dBm')
        self.addDDS('729DP', start_first, on_time, freq, ampl)
        self.addDDS('729DP', start_second, on_time, freq, ampl)
        
if __name__ == '__main__':
    import labrad
    cxn = labrad.connect()
    cs = sampleDDS(TreeDict())
    cs.programSequence(cxn.pulser)
    cxn.pulser.start_number(1)
    cxn.pulser.wait_sequence_done()
    cxn.pulser.stop_sequence()
    print 'DONE'
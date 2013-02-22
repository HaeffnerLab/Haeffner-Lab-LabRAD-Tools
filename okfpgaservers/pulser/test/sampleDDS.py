from PulseSequence import PulseSequence
from labrad.units import WithUnit

class sampleDDS(PulseSequence):
    #dictionary of variable: (type, min, max, default)
    def configuration(self):
        config = [
                  ]
        return config
    
    def sequence(self):
        start_first = WithUnit(10, 'us')
        on_time = WithUnit(500, 'ms')
        off_time = WithUnit(500, 'ms')
        start_second = start_first + on_time + off_time
        freq = WithUnit(200.0, 'MHz')
        ampl = WithUnit(-23.0, 'dBm')
        self.dds_pulses.append( ('729DP', start_first, on_time, freq, ampl) )
        self.dds_pulses.append( ('729DP', start_second, on_time, freq, ampl) )
        
if __name__ == '__main__':
    import labrad
    cxn = labrad.connect()
    cs = sampleDDS(**{})
    cs.programSequence(cxn.pulser)
    cxn.pulser.start_number(10)
    cxn.pulser.wait_sequence_done()
    cxn.pulser.stop_sequence()
    print 'DONE'
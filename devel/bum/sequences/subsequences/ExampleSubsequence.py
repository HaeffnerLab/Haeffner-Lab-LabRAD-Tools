from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U

class example(pulse_sequence):

    def sequence(self):
        #print self.parameters['DopplerCooling.duration']
        print self.parameters['RabiExcitation.duration']
        self.end = self.start + U(5, 'us')

from pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict

class Example(pulse_sequence):

    scannable_params = {
        'RabiExcitation.frequency': (-50, 50, 0, 'kHz'),
        'RabiExcitation.duration': (1, 1000., 10, 'us')
        }

    show_params= []

    def sequence(self):
        from subsequences.ExampleSubsequence import example
        self.addSequence(example)

if __name__=='__main__':
    pv = TreeDict.fromdict({'DopplerCooling.duration':U(5, 'us')})
    ex = Example(pv)
    #psw = pulse_sequence_wrapper('example.xml', pv)

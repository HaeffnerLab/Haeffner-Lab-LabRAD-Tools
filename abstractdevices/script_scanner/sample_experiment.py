import labrad
from scan_methods import experiment

class fft_spectrum(experiment):
    
    name = 'FFT Spectrum'
    required_parameters = [
                           ('Trap Frequencies','rf_drive_frequency')
                           ]
    
    def initialize(self, cxn, context, ident):
        print 'init'
        print self.rf_drive_frequency
        pass
        
    def run(self, cxn, context):
        print 'run'
        pass
            
    def finalize(self, cxn, context):
        print 'finalize'
        pass

class conflicting_experiment(fft_spectrum):
    
    name = 'conflicting_experiment'
        
class non_conflicting_experiment(fft_spectrum):
    
    name = 'non_conflicting_experiment'
        
class crashing_example(fft_spectrum):
    
    name = 'crashing_example'

    def initialize(self, cxn, context, ident):
        print 'in initialize', self.name(), ident
        raise Exception ("In a case of a crash, real message would follow")

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = fft_spectrum()
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
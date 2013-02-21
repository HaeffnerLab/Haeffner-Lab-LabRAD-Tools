import time
import labrad
from scan_methods import experiment

class fft_spectrum(experiment):
    
    name = 'FFT Spectrum'
    required_parameters = [
                           ('Trap Frequencies', 'rf_drive_frequency')
                           ]
   
    def initialize(self, cxn, context, ident):
        print 'in initialize', self.rf_drive_frequency
        
    def run(self, cxn, context):
        print 'in run'
            
    def finalize(self, cxn, context):
        print 'in finalize'

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = fft_spectrum()
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
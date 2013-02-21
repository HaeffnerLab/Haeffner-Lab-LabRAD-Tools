import time
import labrad
from scan_methods import experiment, repeat_reload

class sample_experiment(experiment):
    
    def __init__(self):
        self.param = 3.0
    
    @classmethod
    def name(cls):
        return 'sample_experiment'
    
    @classmethod
    def required_parameters(cls):
        return [('sample_experiment','parameter'),('trap_parameters','trap_drive_frequency')]
   
    def initialize(self, cxn, context, ident):
        pass
#        print 'in initialize', self.name(), ident
        
    def run(self, cxn, context):
#        print 'in running', self.name()
        for i in range(3):
            time.sleep(1)
            
    def finalize(self, cxn, context):
        pass
#        print 'exiting', self.name()

class conflicting_experiment(experiment):
    
    def __init__(self):
        self.param = 3.0
    
    @classmethod
    def name(cls):
        return 'conflicting_experiment'
    
    @classmethod
    def required_parameters(cls):
        return [('conflicting_experiment','parameter'),('conflicting_experiment','trap_drive_frequency')]
   
    def initialize(self, cxn, context, ident):
        pass
#        print 'in initialize', self.name(), ident
        
    def run(self, cxn, context):
#        print 'in running', self.name()
        for i in range(3):
            time.sleep(1)
            
    def finalize(self, cxn, context):
        pass
#        print 'exiting', self.name()
        
class non_conflicting_experiment(experiment):
    
    def __init__(self):
        self.param = 3.0
    
    @classmethod
    def name(cls):
        return 'non_conflicting_experiment'
    
    @classmethod
    def required_parameters(cls):
        return [('non_conflicting_experiment','parameter'),('non_conflicting_experiment','trap_drive_frequency')]
   
    def initialize(self, cxn, context, ident):
        pass
#        print 'in initialize', self.name(), ident
        
    def run(self, cxn, context):
#        print 'in running', self.name()
        for i in range(3):
            time.sleep(1)
            
    def finalize(self, cxn, context):
        pass
#        print 'exiting', self.name()
        
class crashing_example(experiment):
    
    def __init__(self):
        self.param = 3.0
    
    @classmethod
    def name(cls):
        return 'crashing_example'
    
    @classmethod
    def required_parameters(cls):
        return [('sample_experiment','parameter'),('trap_parameters','trap_drive_frequency')]
   
    def initialize(self, cxn, context, ident):
        print 'in initialize', self.name(), ident
        raise Exception ("In a case of a crash, real message would follow")
        
    def run(self, cxn, context):
        print 'in running', self.name()
        for i in range(5):
            print i
            time.sleep(1)
            
    def finalize(self, cxn, context):
        print 'exiting', self.name()

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    ident = scanner.register_external_launch(sample_experiment.name())
    exprt = repeat_reload(sample_experiment, 1000)
    exprt.execute(ident)
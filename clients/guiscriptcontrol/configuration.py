class config(object):
    
    
    #dictionary in the form semaphore_path: (import_part, name)
    ExperimentInfo = {
     ('Test', 'Exp1'):  ('common.clients.guiscriptcontrol.experiments.Test', 'Test'),
     ('Test', 'Exp2'):  ('common.clients.guiscriptcontrol.experiments.Test2', 'Test2'),
     ('Test', 'Exp3'):  ('common.clients.guiscriptcontrol.experiments.Test3', 'Test3'),
     ('729Experiments','Spectrum'):  ('cct.scripts.experiments.Experiments729.spectrum', 'spectrum'),
     ('729Experiments','RabiFlopping'):  ('cct.scripts.experiments.Experiments729.rabi_flopping', 'rabi_flopping'),
     }
    
    
    #conflicting experiments, every experiment conflicts with itself
    conflictingExperiments = {
    ('Test', 'Exp1'): [('Test', 'Exp1'), ('Test', 'Exp2')],
    ('Test', 'Exp2'): [('Test', 'Exp2')],
    ('Test', 'Exp3'): [('Test', 'Exp3')],
    ('SimpleMeasurements', 'ADCPowerMonitor'):  [('SimpleMeasurements', 'ADCPowerMonitor')],
    ('729Experiments','Spectrum'):  [('729Experiments','Spectrum')],
    ('729Experiments','RabiFlopping'):  [('729Experiments','RabiFlopping')],
    }
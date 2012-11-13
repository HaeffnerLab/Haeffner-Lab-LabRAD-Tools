class config(object):
    
    
    #dictionary in the form semaphore_path: (import_part, name)
    ExperimentInfo = {
     ('Test', 'Exp1'):  ('common.clients.guiscriptcontrol.experiments.Test', 'Test'),
     ('Test', 'Exp2'):  ('common.clients.guiscriptcontrol.experiments.Test2', 'Test2'),
     ('Test', 'Exp3'):  ('common.clients.guiscriptcontrol.experiments.Test3', 'Test3'),
     ('SimpleMeasurements', 'ADCPowerMonitor'):  ('lattice.scripts.simpleMeasurements.ADCpowerMonitor', 'ADCPowerMonitor'),
     ('729Experiments','Spectrum'):  ('lattice.scripts.experiments.Experiments729.spectrum', 'spectrum'),
     ('729Experiments','RabiFlopping'):  ('lattice.scripts.experiments.Experiments729.rabi_flopping', 'rabi_flopping'),
     ('729Experiments','BlueHeating'):  ('lattice.scripts.experiments.Experiments729.blue_heating_rabi_flopping', 'blue_heating_rabi_flopping'),
     ('BranchingRatio',):  ('lattice.scripts.experiments.BranchingRatio.branching_ratio', 'branching_ratio')
     }
    
    
    #conflicting experiments, every experiment conflicts with itself
    conflictingExperiments = {
    ('Test', 'Exp1'): [('Test', 'Exp1'), ('Test', 'Exp2')],
    ('Test', 'Exp2'): [('Test', 'Exp2')],
    ('Test', 'Exp3'): [('Test', 'Exp3')],
    ('SimpleMeasurements', 'ADCPowerMonitor'):  [('SimpleMeasurements', 'ADCPowerMonitor')],
    ('729Experiments','Spectrum'):  [('729Experiments','Spectrum')],
    ('729Experiments','RabiFlopping'):  [('729Experiments','RabiFlopping')],
    ('729Experiments','BlueHeating'):[('729Experiments','BlueHeating')],
    ('BranchingRatio',):[('BranchingRatio',)]
    }
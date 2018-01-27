class config(object):

    #list in the format (import_path, class_name)
    sequences = [
        #('common.devel.bum.sequences.example', 'Sequence'),
        ('lattice.PulseSequences2.RabiFlopping', 'RabiFlopping'),
        ('lattice.PulseSequences2.RabiFloppingManual', 'RabiFloppingManual'),
        ('lattice.PulseSequences2.Spectrum', 'Spectrum'),
        ('lattice.PulseSequences2.multispectrum', 'MultiSpectrum'),
        ('lattice.PulseSequences2.ReferenceImage', 'ReferenceImage'),
        ('lattice.PulseSequences2.CalibAllLines', 'CalibAllLines'),
        ('lattice.PulseSequences2.SidebandOptimization', 'SidebandOptimization'),
        ('lattice.PulseSequences2.AuxOpticalPumpingOptimization', 'AuxOpticalPumpingOptimization'),
        ('lattice.PulseSequences2.MolmerSorensenGate', 'MolmerSorensenGate'),
        ('lattice.PulseSequences2.Parity', 'Parity'),
        ('lattice.PulseSequences2.Ramsey', 'Ramsey'),
        ('lattice.PulseSequences2.RamseyLocal', 'RamseyLocal'),
        ('lattice.PulseSequences2.RamseyLocalHanEcho', 'RamseyLocalHanEcho'),
        ('lattice.PulseSequences2.LLI_StatePreparation', 'LLI_StatePreparation'),
        #('lattice.PulseSequences2.CalibAxialLines', 'CalibAxialLines'),
        ('lattice.PulseSequences2.DriftTrackerRamsey', 'DriftTrackerRamsey'),
        ('lattice.PulseSequences2.CalibRotation', 'CalibRotation'),
#         ('lattice.PulseSequences2.NotSureYet', 'NotSureYet'),
        ('lattice.PulseSequences2.LLI_PhaseMeasurement', 'LLI_PhaseMeasurement'),
        ('lattice.PulseSequences2.CompositeRabiFlopping', 'CompositeRabiFlopping'),
        
        
        ]
    
    global_show_params= ['ScanParam.shuffle',
                         'DopplerCooling.doppler_cooling_amplitude_397',
                         'DopplerCooling.doppler_cooling_frequency_397',
                         'DopplerCooling.doppler_cooling_duration',
                         'DopplerCooling.pre_duration',
                         
                         'Excitation_729.channel_729',
                         'Excitation_729.bichro',
                         
                         'OpticalPumping.line_selection',
                         
                         'OpticalPumpingAux.aux_op_line_selection',
                         
                         'Heating.background_heating_time',
                         
                         'SidebandCooling.selection_sideband',
                         'SidebandCooling.order',
                         'SidebandCooling.line_selection',
                         'SidebandCooling.sideband_cooling_amplitude_854',
                         
                         'SequentialSBCooling.channel_729',
                         'SequentialSBCooling.selection_sideband',                       
                         'SequentialSBCooling.order',
                         'SequentialSBCooling.enable',
                         
                         
                         'StatePreparation.channel_729',
                         'StatePreparation.aux_optical_pumping_enable',
                         'StatePreparation.optical_pumping_enable',
                         'StatePreparation.sideband_cooling_enable',

                         'StateReadout.readout_mode',
                         'StateReadout.state_readout_amplitude_397',
                         'StateReadout.state_readout_frequency_397',
                         'StateReadout.threshold_list',
                         #'StateReadout.use_camera_for_readout',
                         
                         'TrapFrequencies.aux_axial',
                         'TrapFrequencies.aux_radial',
                         'TrapFrequencies.axial_frequency',
                         'TrapFrequencies.radial_frequency_1',
                         'TrapFrequencies.radial_frequency_2',
                         'TrapFrequencies.rf_drive_frequency'
                                                  
                       ]


    allowed_concurrent = {
#        'fft_spectrum': ['non_conflicting_experiment'],
#        'non_conflicting_experiment' : ['fft_spectrum'],
    }
    
    launch_history = 1000               

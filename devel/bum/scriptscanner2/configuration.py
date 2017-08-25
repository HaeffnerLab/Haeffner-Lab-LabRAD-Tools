class config(object):

    #list in the format (import_path, class_name)
    sequences = [
        #('common.devel.bum.sequences.example', 'Sequence'),
        ('lattice.PulseSequences2.RabiFlopping', 'RabiFlopping'),
        ('lattice.PulseSequences2.RabiFloppingManual', 'RabiFloppingManual'),
        ('lattice.PulseSequences2.Spectrum', 'Spectrum'),
        ('lattice.PulseSequences2.multispectrum', 'MultiSpectrum'),
        ('lattice.PulseSequences2.ReferenceImage', 'ReferenceImage'),
            ]

    allowed_concurrent = {
#        'fft_spectrum': ['non_conflicting_experiment'],
#        'non_conflicting_experiment' : ['fft_spectrum'],
    }
    
    launch_history = 1000               

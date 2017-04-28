from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence 

class doppler_cooling(pulse_sequence):
    
    
    required_parameters = [
                           ('DopplerCooling','doppler_cooling_frequency_397'), 
                           ('DopplerCooling','doppler_cooling_amplitude_397'), 
                           ('DopplerCooling','doppler_cooling_frequency_866'), 
                           ('DopplerCooling','doppler_cooling_amplitude_866'), 
                           ('DopplerCooling','doppler_cooling_duration'),
                           ('DopplerCooling','doppler_cooling_repump_additional')
                           ]
    
    def sequence(self):
        p = self.parameters.DopplerCooling
        repump_duration = p.doppler_cooling_duration + p.doppler_cooling_repump_additional
        self.addDDS ('397',self.start, p.doppler_cooling_duration, p.doppler_cooling_frequency_397, p.doppler_cooling_amplitude_397)
        self.addDDS ('866',self.start, repump_duration, p.doppler_cooling_frequency_866, p.doppler_cooling_amplitude_866)
        self.end = self.start + repump_duration
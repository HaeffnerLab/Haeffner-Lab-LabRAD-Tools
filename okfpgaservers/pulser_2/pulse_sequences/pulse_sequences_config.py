from labrad.units import WithUnit

class dds_channel(object):
    def __init__(self, name):
        self.name = name
    
    def freq_conversion(self, freq):
        '''
        can be overwitten to provide a custom frequency conversion
        '''
        return freq
    
    def ampl_conversion(self, ampl):
        '''
        can be overwitten to provide a custom amplitude conversion
        '''
        return ampl
    
    def phase_conversion(self, phase):
        '''
        can be overwitten to provide a custom phase conversion
        '''
        return phase
        
class double_pass_729(dds_channel):
    def __init__(self, name):
        super(double_pass_729, self).__init__(name)
    
    def freq_conversion(self, freq):
        #converting real frequency to double pass frequency
        freq =  - 0.5 * freq + WithUnit(220.0, 'MHz')
        return freq
    
    def phase_conversion(self, phase):
        phase = phase['deg'] #in degrees
        phase = phase / 2.0 #double pass doubles the phase.
        phase = -phase #flip the phase such that DDS follows sin(w t - phi), see writeup on single qubit operations
        phase = phase % 360.0 #translates the specifies phase to be between 0 and 360
        phase  = WithUnit(phase, 'deg') #return in units
        return phase
        
#defining available dds channels
dds729DP = double_pass_729('729DP')
dds729DP_1 = double_pass_729('729DP_1')
dds110DP = dds_channel('110DP')
dds866DP = dds_channel('866DP')
dds854DP = dds_channel('854DP')

'''
channel_dictionary provides a translation between the channels of the pulse sequence
and the pulser dds channel names.  This allows to keep pulse sequences easier to read.
There can be multiple keys for the same value.
'''
    
dds_name_dictionary = {
                        '729':dds729DP,
                        '729DP':dds729DP,
                        '729_1':dds729DP_1,
                        '729DP_1':dds729DP_1,
                        '397':dds110DP,
                        '110DP':dds110DP,
                        '866':dds866DP,
                        '866DP':dds866DP,
                        '854':dds854DP,
                        '854DP':dds854DP,
                        }
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
    # f_shift is the shift applied to the single pass AOMs (relative to 80 MHz)
    
    def __init__(self, name, f_shift = WithUnit(0.0, 'MHz')):
        super(double_pass_729, self).__init__(name)
        self.f_shift = f_shift
    def freq_conversion(self, freq):
        #converting real frequency to double pass frequency
        freq =  - 0.5 * freq + WithUnit(220.0, 'MHz') - 0.5*self.f_shift
        return freq
    
    def phase_conversion(self, phase):
        phase = phase['deg'] #in degrees
        phase = phase / 2.0 #double pass doubles the phase.
        phase = -phase #flip the phase such that DDS follows sin(w t - phi), see writeup on single qubit operations
        phase = phase % 360.0 #translates the specifies phase to be between 0 and 360
        phase  = WithUnit(phase, 'deg') #return in units
        return phase
        
#defining available dds channels
#dds729DP = double_pass_729('729DP')
#dds729DP_1 = double_pass_729('729DP_1')

dds729global = double_pass_729('729global', f_shift = WithUnit(0.15, 'MHz'))
dds729global_1 = double_pass_729('729global_1', f_shift = WithUnit(0.15, 'MHz'))
dds729global_2 = double_pass_729('729global_2', f_shift = WithUnit(0.15, 'MHz'))
dds729global_3 = double_pass_729('729global_3', f_shift = WithUnit(0.15, 'MHz'))
dds729local = double_pass_729('729local', f_shift = WithUnit(-0.2, 'MHz'))

#dds729global = double_pass_729('729global', f_shift = WithUnit(0.0, 'MHz'))
#dds729local = double_pass_729('729local', f_shift = WithUnit(0.0, 'MHz'))

dds729DP_aux = double_pass_729('729DP_aux')
dds729DP_aux_1 = double_pass_729('729DP_aux_1')
global397 = dds_channel('global397')
#dds866DP = dds_channel('866DP')
dds854DP = dds_channel('854DP')

'''
channel_dictionary provides a translation between the channels of the pulse sequence
and the pulser dds channel names.  This allows to keep pulse sequences easier to read.
There can be multiple keys for the same value.
'''
    
dds_name_dictionary = {
                        '729':dds729global,
                        '729DP':dds729global,
                        '729_1':dds729local,
                        '729DP_1':dds729local,
                        '729global':dds729global,
                        '729global_1':dds729global_1,
                        '729global_2':dds729global_2,
                        '729global_3':dds729global_3,
                        '729local':dds729local,
                        '729_aux':dds729DP_aux,
                        '729DP_aux':dds729DP_aux,
                        '729_aux_1':dds729DP_aux_1,
                        '729DP_aux_1':dds729DP_aux_1,
                        '397':global397,
                        #'866':dds866DP,
                        #'866DP':dds866DP,
                        '854':dds854DP,
                        '854DP':dds854DP,
                        }
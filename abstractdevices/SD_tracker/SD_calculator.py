from fractions import Fraction
from labrad import units as U
from labrad.units import WithUnit
import numpy
from SD_tracker_config import config as conf
    
class EnergyLevel(object):
    
    spectoscopic_notation = {
                            'S': 0,
                            'P': 1, 
                            'D': 2,
                            }
    
    spectoscopic_notation_rev = {
                            0 : 'S',
                            1 : 'P',
                            2 : 'D',
                            }
    
    
    def __init__(self, angular_momentum_l, total_angular_momentum_j, spin_s = '1/2'):
        #convert spectroscopic notation to the spin number
        if type(angular_momentum_l) == str:
            angular_momentum_l = self.spectoscopic_notation[angular_momentum_l]
        total_angular_momentum_j = Fraction(total_angular_momentum_j)
        spin_s = Fraction(spin_s)
        S = spin_s
        self.L = L = angular_momentum_l
        J = total_angular_momentum_j
        lande_factor =  self.lande_factor(S, L, J)
        #sublevels are found, 2* self.J is always an integer, so can use numerator
        self.sublevels_m =  [-J + i for i in xrange( 1 + (2 * J).numerator)]
        self.energy_scale = (lande_factor * U.bohr_magneton / U.hplanck) #1.4 MHz / gauss
    
    def lande_factor(self, S, L ,J):
        '''computes the lande g factor'''
        g = Fraction(3,2) + Fraction( S * (S + 1) - L * (L + 1) ,  2 * J*(J + 1))
        return g
    
    def magnetic_to_energy(self, B):
        '''given the magnitude of the magnetic field, returns all energies of all zeeman sublevels'''
        energies = [(self.energy_scale * m * B).inUnitsOf('MHz') for m in self.sublevels_m]
        representations = [self.frac_to_string(m) for m in self.sublevels_m]
        return zip(self.sublevels_m,energies,representations)
    
    def frac_to_string(self, sublevel):
        #helper class for converting energy levels to strings
        sublevel = str(sublevel)
        if not sublevel.startswith('-'): 
            sublevel = '+' + sublevel
        together = self.spectoscopic_notation_rev[self.L] + sublevel
        return together

class Transitions_SD(object):
    
    S = EnergyLevel('S', '1/2')
    D = EnergyLevel('D', '5/2')
    allowed_transitions = [0,1,2]
    
    def transitions(self):
        transitions = []
        for m_s,E_s,repr_s in self.S.magnetic_to_energy(WithUnit(0, 'gauss')):
            for m_d,E_d,repr_d in self.D.magnetic_to_energy(WithUnit(0, 'gauss')):
                if abs(m_d-m_s) in self.allowed_transitions:
                    name = repr_s + repr_d
                    transitions.append(name)
        return transitions
    
    def get_transition_energies(self, B, zero_offset = WithUnit(0, 'MHz')):
        '''returns the transition enenrgies in MHz where zero_offset is the 0-field transition energy between S and D'''
        ans = []
        for m_s,E_s,repr_s in self.S.magnetic_to_energy(B):
            for m_d,E_d,repr_d in self.D.magnetic_to_energy(B):
                if abs(m_d-m_s) in self.allowed_transitions:
                    name = repr_s + repr_d
                    diff = E_d - E_s
                    diff+= zero_offset
                    ans.append((name, diff))
        return ans
    
    def energies_to_magnetic_field(self, transitions):
        #given two points in the form [(S-1/2D5+1/2, 1.0 MHz), (-1/2, 5+/2, 2.0 MHz)], calculates the magnetic field
        try:
            transition1, transition2 = transitions
        except ValueError:
            raise Exception ("Wrong number of inputs in energies_to_magnetic_field")
        ms1,md1 = self.str_to_fractions(transition1[0])
        ms2,md2 = self.str_to_fractions(transition2[0])
        en1,en2 = transition1[1], transition2[1]
        if abs(md1 - ms1) not in self.allowed_transitions or abs(md2 - ms2) not in self.allowed_transitions:
            raise Exception ("Such transitions are not allowed")
        s_scale = self.S.energy_scale
        d_scale = self.D.energy_scale
        B = (en2 - en1) / ( d_scale * ( md2 - md1) - s_scale * (ms2 - ms1) )
        B = B.inUnitsOf('gauss')
        offset = en1 - (md1 * d_scale - ms1 * s_scale) * B
        return B, offset
        
    def str_to_fractions(self, inp):
        #takes S-1/2D5+1/2 and converts to Fraction(-1/2), Fraction(1/2)
        return Fraction(inp[1:5]), Fraction(inp[6:10])

class double_pass(object):
    
    passes = conf.double_pass_passes
    direction = conf.double_pass_direction
    
    def reading_to_offset(self, dp_freq):
        #i.e dp_freq set to 220 mhz, -1 direction -> output is -440
        offset = self.direction * self.passes * dp_freq
        return offset
    
    def offset_to_reading(self, offset):
        #returns dp frequency corresponding to the offset
        freq = offset / float( self.direction * self.passes )
        return freq

class fitter(object):
    
    order = conf.fit_order
    
    def fit(self, x, y):
        '''given two inputs x and y returns a polynomail fit'''
        #if the length of inputs is not sufficient, will avoid erros by decreasing the order of fitting
        #returns highest order as first element
        fit_order = min(self.order, x.size - 1)
        fit = numpy.polyfit(x, y, deg = fit_order)
        ans = numpy.zeros(self.order + 1)
        ans[(self.order - fit_order):] = fit
        return ans
    
    def evaluate(self, x, fit):
        return numpy.polyval(fit, x)
    
if __name__ == '__main__':
    SD = Transitions_SD()
    dp = double_pass()
    fit = fitter()
 
#    result = SD.get_transition_energies(WithUnit(1.19, 'gauss'), WithUnit(0 ,'MHz'))
#    for name,freq in result:
#        print name,freq
#    print SD.energies_to_magnetic_field([('S+1/2D-3/2', WithUnit(-4.663544847990941, 'MHz')), ('S-1/2D-3/2', WithUnit(-1.33244138514, 'MHz'))])
#    
#    dp_offset = dp.reading_to_offset(WithUnit(227.257 ,'MHz'))
#    print dp_offset
#    result =  SD.get_transition_energies(WithUnit(1.19, 'gauss'), dp_offset)
#    for name,freq in result:
#        print name, dp.offset_to_reading(freq)
#    
#    b,freq = SD.energies_to_magnetic_field([('S-1/2D+3/2', WithUnit(dp.reading_to_offset(229.581), 'MHz')), ('S+1/2D+5/2', WithUnit(dp.reading_to_offset(228.917), 'MHz'))])
#    print b,dp.offset_to_reading(freq)
#    x = numpy.arange(1)
#    y = 2 * x + 1
#    fit.fit(x, y)
from labrad import units as U, types as T    
import numpy as np

class lamb_dicke(object):
    
    @classmethod
    def lamb_dicke(self, trap_frequency, projection_angle, laser_wavelength =  T.Value(729, 'nm'), amumass = 40):
        '''computes the lamb dicke parameter
        @var theta: angle between the laser and the mode of motion. 90 degrees is perpendicular
        @var laser_wavelength: laser wavelength
        @var trap_frequency: trap frequency
        @amumass particle mass in amu
        '''
        theta = projection_angle
        frequency = trap_frequency
        mass =  amumass * U.amu
        k = 2.*np.pi/laser_wavelength
        eta = k*(U.hbar/(2*mass*2*np.pi*frequency))**.5 * np.abs(np.cos(theta*2.*np.pi / 360.0))
        eta = eta.inBaseUnits().value
        return eta

if __name__ == '__main__':
    trap_frequency = T.Value(3.0, 'MHz')
    projection_angle = 45 #degrees
    eta = lamb_dicke.lamb_dicke(trap_frequency, projection_angle)
    print 'eta {}'.format(eta)
import numpy as np
from scipy.special.orthogonal import eval_genlaguerre as laguerre

class rabi_coupling(object):

    @classmethod
    def compute_rabi_coupling(cls, eta, sideband_order, nmax):
        '''
        Rabi couplings, see Leibfried (2003), eq:70
        '''
        if sideband_order == 0:
            coupling_func = lambda n: np.exp(-1./2*eta**2) * laguerre(n, 0, eta**2)
        elif sideband_order == 1:
            coupling_func = lambda n: np.exp(-1./2*eta**2) * eta**(1)*(1./(n+1.))**0.5 * laguerre(n, 1, eta**2)
        elif sideband_order == 2:
            coupling_func = lambda n: np.exp(-1./2*eta**2) * eta**(2)*(1./((n+1.)*(n+2)))**0.5 * laguerre(n, 2, eta**2)
        elif sideband_order == 3:
            coupling_func = lambda n: np.exp(-1./2*eta**2) * eta**(3)*(1./((n+1)*(n+2)*(n+3)))**0.5 * laguerre(n, 3 , eta**2) 
        elif sideband_order == 4:
            coupling_func = lambda n: np.exp(-1./2*eta**2) * eta**(4)*(1./((n+1)*(n+2)*(n+3)*(n+4)))**0.5 * laguerre(n, 4 , eta**2)
        elif sideband_order == 5:
            coupling_func = lambda n: np.exp(-1./2*eta**2) * eta**(5)*(1./((n+1)*(n+2)*(n+3)*(n+4)*(n+5)))**0.5 * laguerre(n, 5 , eta**2)      
        elif sideband_order == -1:
            coupling_func = lambda n: 0 if n == 0 else np.exp(-1./2*eta**2) * eta**(1)*(1./(n))**0.5 * laguerre(n - 1, 1, eta**2)
        elif sideband_order == -2:
            coupling_func = lambda n: 0 if n <= 1 else np.exp(-1./2*eta**2) * eta**(2)*(1./((n)*(n-1.)))**0.5 * laguerre(n - 2, 2, eta**2)
        elif sideband_order == -3:
            coupling_func = lambda n: 0 if n <= 2 else np.exp(-1./2*eta**2) * eta**(3)*(1./((n)*(n-1.)*(n-2)))**0.5 * laguerre(n -3, 3, eta**2)
        elif sideband_order == -4:
            coupling_func = lambda n: 0 if n <= 3 else np.exp(-1./2*eta**2) * eta**(4)*(1./((n)*(n-1.)*(n-2)*(n-3)))**0.5 * laguerre(n -4, 4, eta**2)
        elif sideband_order == -5:
            coupling_func = lambda n: 0 if n <= 4 else np.exp(-1./2*eta**2) * eta**(5)*(1./((n)*(n-1.)*(n-2)*(n-3)*(n-4)))**0.5 * laguerre(n -5, 5, eta**2)
        else:
            raise NotImplementedError("Can't calculate rabi couplings sideband order {}".format(sideband_order))
        return np.array([coupling_func(n) for n in range(nmax)])

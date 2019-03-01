#from PyQt4 import QtGui

import numpy as np

class pmt_simu():

    def __init__(self):
        print "Initializing pmt ..."
        self.state = 0
        self.mu_dark = 2
        self.mu_bright = 100

    def return_counts(self, number_of_repetitions): 
        
        #buf = "\x00" * ( 2 * 2 )


        counts = self.get_excitation()
       
        #print str(counts)
        #print str(number_of_repetitions)
        #print str(int(counts * number_of_repetitions))
        #print str(counts)

        s_dark = np.random.poisson(self.mu_dark, int(counts * number_of_repetitions))
        s_bright = np.random.poisson(self.mu_bright, int((1-counts) * number_of_repetitions))


        buf2 = ""
        for k in s_dark:
            buf2 += "\x00\x00"
            buf2 += chr(k)
            buf2 += "\x00"

        for k in s_bright:
            buf2 += "\x00\x00"
            buf2 += chr(k)
            buf2 += "\x00"

        self.state = self.state + 1
        #print "State: " + str(self.state)
        return buf2

    def get_excitation(self):

        t0 = 30.0
        w = 10.0

        t = float(self.state)

        excitation = np.exp( -(t - t0)**2/w**2 )
        excitation = w**2/( (t - t0)**2 + w**2 )

        if self.state == 2*t0:
            self.state = 0

        return excitation    

if __name__=="__main__":

    pmt_simu = pmt_simu()

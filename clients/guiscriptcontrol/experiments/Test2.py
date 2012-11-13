import labrad
import time
import numpy as np

class Test2():
    def __init__(self):
        self.experimentPath = ['Test', 'Exp2']
        print 'Initializing Test2'
       
    def run(self):
        #generate lorentzian data
        p = [.01, 25, .1, 0] #p = [gamma, center, I, offset]
        x = np.arange(24.9, 25.1, .005)
        y = p[3] + p[2]*(p[0]**2/((x - p[1])**2 + p[0]**2))# Lorentzian
        #add data to data vault
        self.cxn = labrad.connect()
        self.cxn.server = self.cxn.data_vault
        self.cxn.data_vault.cd('Sine Curves')
        self.cxn.data_vault.new('Lorentzian', [('x', 'num')], [('y1','Test-Spectrum','num')])
        self.cxn.data_vault.add_parameter('Window', ['Lorentzian'])
        self.cxn.data_vault.add_parameter('plotLive', True)
        self.cxn.data_vault.add(np.vstack((x,y)).transpose())
        time.sleep(1)
        self.cxn.data_vault.add_parameter('Fit', ['[]', 'Lorentzian', '[0.01, 25.0, 0.10000000000000001, 1.4901161193880158e-08]']) 
        #wait until the fit is accepted
        i = 0
        while(i < 200): # timeout
            try:
                Continue = self.cxn.data_vault.get_parameter('Accept-0')
            except:
                Continue = False
            if (Continue == True):
                self.doCalculation()
                break
            else:
                time.sleep(1.0)
            i += 1
        self.cleanUp()
        
    def doCalculation(self):
        print 'Accepted!, doing calculation....'
    
    def cleanUp(self):
        print 'why am i not cleaning up?'
        self.cxn.semaphore.finish_experiment(self.experimentPath)
        print 'all cleaned up boss'

if __name__ == '__main__':
    test2 = Test2()
    test2.run()
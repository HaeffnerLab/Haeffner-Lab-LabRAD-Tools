import time

class Test3():
    def __init__(self):
        self.experimentPath = ['Test', 'Exp3']
        print 'Initializing Test'
        self.iterations = 10
        self.progress = 0.0
            
    def pause(self, progress):
        Continue = self.cxn.semaphore.block_experiment(self.experimentPath, progress)
        if (Continue == True):
            self.parameters = self.cxn.semaphore.get_parameter_names(self.experimentPath)
            return True
        else:
            return False     
        
    def run(self):
        import labrad
        self.cxn = labrad.connect()
        for i in range(self.iterations):
            print 'Running Test 1, iteration {}'.format(i)
            self.progress = ((i)/float(self.iterations))*100
            Continue = self.pause(self.progress)
            if (Continue == False):
                self.cxn.semaphore.finish_experiment(self.experimentPath, self.progress)
                return        
            time.sleep(1)

        self.progress = 100.0   
        self.cleanUp()
        
    def cleanUp(self):
        self.cxn.semaphore.finish_experiment(self.experimentPath, self.progress)
        print 'all cleaned up boss'

if __name__ == '__main__':
    test = Test()
    test.run()
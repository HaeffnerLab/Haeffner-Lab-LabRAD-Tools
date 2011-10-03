class dataProcess():
    name  = None
    inputsRequired = None
    inputsOptional = None
    
    def __init__(self, inputs = None):        
        self.makeInputDict()
        self.setInputs(inputs)
        self.confirmHaveInputs()
        self.initialize()
            
    def makeInputDict(self):
        self.inputDict = dict(self.inputsOptional)
        for req in self.inputsRequired:
            self.inputDict[req] = None
    
    def setInputs(self, inputs):
        if inputs is None: return
        newdict = dict(inputs)
        for arg in self.inputDict.keys():
            if arg in newdict.keys(): self.inputDict[arg] = newdict[arg]
    
    def confirmHaveInputs(self):
        for req in self.inputsRequired:
            if self.inputDict[req] is None: raise("{} required input not set".format(req))
    
    def initialize(self):
        pass
    
    def processNewData(self):
        pass
    
    def getResult(self):
        pass
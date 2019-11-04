from labrad.wrappers import connectAsync
from common.devel.pygrapher.dataset import Dataset
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred

class Tester():
    def __init__(self):
        self.connectLabRAD()

    @inlineCallbacks
    def connectLabRAD(self):
        self.cxn = yield connectAsync()
        context = yield self.cxn.context()
        dir = ['', 'Test']
        dataset = 1
        datasetName = 'Rabi Flopping'
        reactor = None
        
        d = Dataset(self.cxn, context, dataset, dir, datasetName, reactor)

if __name__ == '__main__':
    t = Tester()


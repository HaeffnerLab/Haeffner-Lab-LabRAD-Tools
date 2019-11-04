from labrad.wrappers import connectAsync
from dataset import Dataset
from twisted.internet.defer import inlineCallbacks

class test(object):
    def __init__(self):
        pass
    @inlineCallbacks
    def test_dataset(self):
        cxn = yield connectAsync()
        context = yield cxn.context()
        dir = ['', 'Test']
        dataset = 1
        datasetName = 'Rabi Flopping'
        d = Dataset(cxn, context, dataset, dir, datasetName, None)
        d.openDataset()
        d.getData()

if __name__=="__main__":
    t = test()
    t.test_dataset()

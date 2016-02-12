from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui

class sampleWidget(QtGui.QWidget):
    def __init__(self, reactor, parent=None):
        super(sampleWidget, self).__init__(parent)
        self.reactor = reactor
        self.connect()

    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync()

    def closeEvent(self, x):
        self.reactor.stop()   

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = sampleWidget(reactor)
    widget.show()
    reactor.run()
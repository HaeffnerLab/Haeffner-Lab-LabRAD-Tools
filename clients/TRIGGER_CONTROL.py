from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks

SIGNALID = 378902

class triggerWidget(QtGui.QFrame):
    def __init__(self, reactor, parent=None):
        super(triggerWidget, self).__init__(parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.reactor = reactor
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync()
        self.server = yield self.cxn.trigger
        yield self.initializeGUI()
        yield self.setupListeners()
        
    @inlineCallbacks
    def initializeGUI(self):
        self.d = {'Switches':{},'Triggers':{}}
        #set layout
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        #get switch names and add them to the layout, and connect their function
        layout.addWidget(QtGui.QLabel('Switches'),0,0)
        switchNames = yield self.server.get_switching_channels()
        for order,name in enumerate(switchNames):
            button = QtGui.QPushButton(name)
            self.d['Switches'][name] = button
            button.setCheckable(True)
            initstate = yield self.server.get_state(name)
            button.setChecked(initstate)
            self.setButtonText(button, name)
            button.clicked.connect(self.buttonConnection(name, button))
            layout.addWidget(button,0,1 + order)
        #do same for trigger channels
        layout.addWidget(QtGui.QLabel('Triggers'),1,0)
        triggerNames = yield self.server.get_trigger_channels()
        for order,name in enumerate(triggerNames):
            button = QtGui.QPushButton(name)
            button.clicked.connect(self.triggerConnection(name))
            self.d['Triggers'][name] = button
            layout.addWidget(button,1,1 + order)
    
    def buttonConnection(self, name, button):
        @inlineCallbacks
        def func(state):
            yield self.server.switch(name, state)
            self.setButtonText(button, name)
        return func
    
    def triggerConnection(self, name):
        @inlineCallbacks
        def func(state):
            yield self.server.trigger(name)
        return func
    
    @inlineCallbacks
    def setupListeners(self):
        yield self.server.signal__switch_toggled(SIGNALID)
        yield self.server.addListener(listener = self.followSignal, source = None, ID = SIGNALID)
    
    def followSignal(self, x, (switchName, state)):
        button = self.d['Switches'][switchName]
        button.setChecked(state)
        self.setButtonText(button, switchName)
      
    def setButtonText(self, button, prefix):
        if button.isChecked():
            button.setText('{} is ON'.format(prefix))
        else:
             button.setText('{} is OFF'.format(prefix))
    
    def closeEvent(self, x):
        self.reactor.stop()
    
    def sizeHint(self):
        return QtCore.QSize(100,100)
            
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    triggerWidget = triggerWidget(reactor)
    triggerWidget.show()
    reactor.run()
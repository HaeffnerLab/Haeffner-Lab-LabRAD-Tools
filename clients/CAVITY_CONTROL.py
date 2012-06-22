from PyQt4 import QtGui, QtCore
from qtui.SliderSpin import SliderSpin
from twisted.internet.defer import inlineCallbacks, returnValue

UpdateTime = 100 #in ms, how often data is checked for communication with the server
SIGNALID = 187566

class widgetWrapper():
    def __init__(self, serverName, displayName, regName, globalRange, units = 'mV'):
        self.serverName = serverName
        self.displayName = displayName
        self.regName = regName
        self.units = units
        self.globalRange = globalRange
        self.range = None
        self.widget = None
        self.updated = False
        
    def makeWidget(self):
        self.widget = SliderSpin(self.displayName,self.units,self.range, self.globalRange) 
    
    def onUpdate(self):
        self.updated = True

class cavityWidget(QtGui.QWidget):
    def __init__(self, reactor, parent=None):
        super(cavityWidget, self).__init__(parent)
        self.reactor = reactor
        self.createDict()
        self.connect()
    
    def createDict(self):
        self.d = {}
        self.d['397'] = widgetWrapper( serverName = '397', displayName = '397 SHG Cavity', regName = 'range397', globalRange = (0,2500))
        self.d['866'] = widgetWrapper( serverName = '866', displayName = '866 Cavity', regName = 'range866', globalRange = (0,2500))
        self.d['422'] = widgetWrapper( serverName = '422', displayName = '422 Offset', regName = 'range422', globalRange = (0,2500))
        self.d['854'] = widgetWrapper( serverName = '854',displayName = '854 Cavity', regName = 'range854', globalRange = (0,2500))
        self.d['397D'] =  widgetWrapper( serverName = '397D', displayName = '397 Diode Cavity', regName = 'range397D', globalRange = (0,2500))
        
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        self.cxn = yield connectAsync('192.168.169.49')
        self.server = yield self.cxn.laserdac
        self.registry = yield self.cxn.registry
        yield self.loadDict()
        yield self.setupListeners()
        yield self.initializeGUI()
    
    @inlineCallbacks
    def loadDict(self):
        #sets the range and makes widgets
        for widgetWrapper in self.d.values():
            range = yield self.getRangefromReg( widgetWrapper.regName )
            widgetWrapper.range = range
            widgetWrapper.makeWidget()
    
    @inlineCallbacks
    def setupListeners(self):
        yield self.server.signal__channel_has_been_updated(SIGNALID)
        yield self.server.addListener(listener = self.followSignal, source = None, ID = SIGNALID)
    
    def followSignal(self, x, (chanName,voltage)):
        widget = self.d[chanName].widget
        widget.setValueNoSignal(voltage)
    
    def sizeHint(self):
        return QtCore.QSize(800,500)
    
    @inlineCallbacks
    def initializeGUI(self):
        #get voltages
        for chanName in self.d.keys():
            voltage =  yield self.server.getvoltage(chanName)
            self.d[chanName].widget.spin.setValue(voltage)
        #lay out the widget
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)
        for name in ['397','866','422','854','397D']: #sets the order of appearance
            layout.addWidget(self.d[name].widget)
        #connect functions
        for widgetWrapper in self.d.values():
            widgetWrapper.widget.spin.valueChanged.connect(widgetWrapper.onUpdate)
            widgetWrapper.widget.minrange.valueChanged.connect(self.saveNewRange)
            widgetWrapper.widget.maxrange.valueChanged.connect(self.saveNewRange)
        #start timer
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.sendToServer)
        self.timer.start(UpdateTime)
    
    @inlineCallbacks
    def saveNewRange(self, val):
        yield self.registry.cd(['','Clients','Cavity Control'],True)
        for widgetWrapper in self.d.values():
            widget = widgetWrapper.widget
            [min,max] = [widget.minrange.value(), widget.maxrange.value()]
            yield self.registry.set(widgetWrapper.regName, [min,max])
    
    @inlineCallbacks
    def getRangefromReg(self, rangeName):
        yield self.registry.cd(['','Clients','Cavity Control'],True)
        try:
            range = yield self.registry.get(rangeName)
            range = list(range)
        except:
            print 'problem with acquiring range from registry'
            range = [0,2500]
        returnValue( range )
    
    #if inputs are updated by user, send the values to server
    @inlineCallbacks
    def sendToServer(self):
        for widgetWrapper in self.d.values():
            if widgetWrapper.updated:
                yield self.server.setvoltage(widgetWrapper.serverName, widgetWrapper.widget.spin.value())
                widgetWrapper.updated = False

    def closeEvent(self, x):
        self.reactor.stop()  

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    cavityWidget = cavityWidget(reactor)
    cavityWidget.show()
    reactor.run()
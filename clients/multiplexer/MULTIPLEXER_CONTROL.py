from PyQt4 import QtGui, QtCore, uic
import os
import RGBconverter as RGB
from twisted.internet.defer import inlineCallbacks, returnValue

SIGNALID1 = 187567
SIGNALID2 = 187568
SIGNALID3 = 187569
SIGNALID4 = 187570

class widgetWrapper():
    def __init__(self, chanName, wavelength, hint):
        self.chanName = chanName
        self.wavelength = wavelength
        self.hint = hint
        self.widget = None
        self.codeDict = codeDict = {-3.0: 'UnderExposed', -4.0: 'OverExposed', -5.0: 'NeedStartWM', -6.0 :'NotMeasured'}
        self.widget = multiplexerChannel(self.wavelength, self.hint, self.chanName)           
        
    def setFreq(self, freq):
        if freq in self.codeDict.keys():
            text = self.codeDict[freq]
        else:
            text = '%.5f'%freq
        self.widget.freq.setText(text)            
            
    def setState(self, state, disableSignals = False):
        if disableSignals:
            self.widget.checkBox.blockSignals(True)
        self.widget.checkBox.setChecked(state)
        if disableSignals:
            self.widget.checkBox.blockSignals(False)
        
    def setExposure(self, exposure, disableSignals = False):
        if disableSignals:
            self.widget.checkBox.blockSignals(True)
        self.widget.spinBox.setValue(exposure)
        if disableSignals:
            self.widget.checkBox.blockSignals(False)
        
            
class multiplexerWidget(QtGui.QWidget):
    def __init__(self, reactor, parent = None):
        super(multiplexerWidget, self).__init__(parent)
        self.reactor = reactor
        basepath = os.environ.get('LABRADPATH',None)
        if not basepath:
            raise Exception('Please set your LABRADPATH environment variable')
        path = os.path.join(basepath,'clients/qtui/Multiplexer.ui')
        uic.loadUi(path,self)
        self.createDict()
        self.connect() 
    
    def createDict(self):
        self.d = {}
        self.d['397'] = widgetWrapper(chanName = '397',wavelength = '397', hint = '377.61131')
        self.d['866'] = widgetWrapper(chanName = '866',wavelength = '866', hint = '346.00002')
        self.d['422'] = widgetWrapper(chanName = '422',wavelength = '422', hint = '354.53921') 
        self.d['732'] = widgetWrapper(chanName = '732',wavelength = '732', hint = '409.09585') 
        self.d['397s'] = widgetWrapper(chanName = '397s',wavelength = '397', hint = '377.61131') 
        self.d['729'] = widgetWrapper(chanName = '729',wavelength = '729', hint = '411.04196') 
        self.d['397diode'] = widgetWrapper(chanName = '397diode',wavelength = '397', hint = '755.22262') 
        self.d['405'] = widgetWrapper(chanName = '405',wavelength = '405', hint = '405.00000') 
        self.d['397inject'] = widgetWrapper(chanName = '397diode',wavelength = '397', hint = '755.22262')
    
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        self.cxn = yield connectAsync()
        try:
            self.server = yield self.cxn.multiplexer_server
            yield self.initializeGUI()
            yield self.setupListeners()
        except:
            self.setEnabled(False)
        
    @inlineCallbacks
    def initializeGUI(self):
        #make sure channel names we have are found on the server
        availableNames = yield self.server.get_available_channels()
        for chanName in self.d.keys():
            if chanName not in availableNames:
                raise('Error chanName not found on the multiplexer server')
        #get initial values
        state = yield self.server.is_cycling()
        self.pushButton.setChecked(state)
        self.setButtonText()
        for name in self.d.keys():
            
            freq = yield self.server.get_frequency(name)
            self.d[name].setFreq(float(freq))
            exp = yield self.server.get_exposure(name)
            self.d[name].setExposure(exp)
            state = yield self.server.get_state(name)
            self.d[name].setState(state)
        #add items to grid layout
        self.grid.addWidget(self.d['397'].widget,0,0)
        self.grid.addWidget(self.d['866'].widget,1,0)
        self.grid.addWidget(self.d['422'].widget,0,1)
        self.grid.addWidget(self.d['732'].widget,1,1)
        self.grid.addWidget(self.d['397s'].widget,2,0)
        self.grid.addWidget(self.d['729'].widget,2,1)
        self.grid.addWidget(self.d['854'].widget,3,0)
        self.grid.addWidget(self.d['405'].widget,3,1)
        self.grid.addWidget(self.d['397diode'].widget,4,0)
        
        #connect functions
        self.pushButton.toggled.connect(self.setOnOff)
        for widgetWrapper in self.d.values():
            widget = widgetWrapper.widget
            name = widgetWrapper.chanName
            widget.checkBox.stateChanged.connect(self.setStateWrapper(name))
            widget.spinBox.valueChanged.connect(self.setExposureWrapper(name))
    
    @inlineCallbacks
    def setupListeners(self):
        yield self.server.signal__channel_toggled(SIGNALID1)
        yield self.server.addListener(listener = self.followNewState, source = None, ID = SIGNALID1)
        yield self.server.signal__new_exposure_set(SIGNALID2)
        yield self.server.addListener(listener = self.followNewExposure, source = None, ID = SIGNALID2)
        yield self.server.signal__new_frequency_measured(SIGNALID3)
        yield self.server.addListener(listener = self.followNewFreq, source = None, ID = SIGNALID3)
        yield self.server.signal__updated_whether_cycling(SIGNALID4)
        yield self.server.addListener(listener = self.followNewCycling, source = None, ID = SIGNALID4)
    
    def followNewState(self,x,(chanName,state)):
        self.d[chanName].setState(state, True)
        
    def followNewExposure(self, x, (chanName,exp)):
        self.d[chanName].setExposure(exp, True)
    
    def followNewFreq(self, x, (chanName, freq)):
        self.d[chanName].setFreq(freq)
    
    def followNewCycling(self, x, cycling):
        self.pushButton.blockSignals(True)
        self.pushButton.setChecked(cycling)
        self.pushButton.blockSignals(False)
        self.setButtonText()
    
    def setButtonText(self):
        if self.pushButton.isChecked():
            self.pushButton.setText('ON')
        else:
            self.pushButton.setText('OFF')
    
    @inlineCallbacks
    def setOnOff(self, pressed):
        if pressed:
            yield self.server.start_cycling()
        else:
            yield self.server.stop_cycling()
        self.setButtonText()
        
    def setStateWrapper(self, chanName):
        def func(state):
            self.setState(chanName, state)
        return func
    
    def setExposureWrapper(self, chanName):
        def func(state):
            self.setExposure(chanName, state)
        return func 
    
    @inlineCallbacks
    def setState(self, chanName, state):
        yield self.server.set_state(chanName,bool(state))
    
    @inlineCallbacks
    def setExposure(self, chanName, exp):
        yield self.server.set_exposure(chanName,exp)
    
    def closeEvent(self, x):
        self.reactor.stop()  

                
class multiplexerChannel(QtGui.QWidget):
    def __init__(self, wavelength, hint, name, parent=None):
        QtGui.QWidget.__init__(self, parent)
        basepath = os.environ.get('LABRADPATH',None)
        if not basepath:
            raise Exception('Please set your LABRADPATH environment variable')
        path = os.path.join(basepath,'clients/qtui/MultiplexerChannel.ui')
        uic.loadUi(path,self)
        self.RGBconverter = RGB.RGBconverter()
        self.setColor(wavelength)
        self.setHint(hint)
        self.setLabel(name)
        
    def setColor(self, wavelength):
        [r,g,b] = self.RGBconverter.wav2RGB(int(wavelength))
        self.label.setStyleSheet('color:rgb(%d,%d,%d)' %(r,g,b))
        
    def setLabel(self, name):
        self.label.setText(name)
    
    def setHint(self, hint):
        self.expectedfreq.setText(hint)

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    multiplexerWidget = multiplexerWidget(reactor)
    multiplexerWidget.show()
    reactor.run()
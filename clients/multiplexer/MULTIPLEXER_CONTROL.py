from PyQt4 import QtGui, uic
import os
import RGBconverter as RGB
from twisted.internet.defer import inlineCallbacks
from MULTIPLEXER_CONTROL_config import multiplexer_control_config as config

SIGNALID1 = 187567
SIGNALID2 = 187568
SIGNALID3 = 187569
SIGNALID4 = 187570

class widgetWrapper(object):
    def __init__(self, chanName, wavelength, hint):
        self.chanName = chanName
        self.wavelength = wavelength
        self.hint = hint
        self.widget = None
        self.codeDict = {-3.0: 'UnderExposed', -4.0: 'OverExposed', -5.0: 'NeedStartWM', -6.0 :'NotMeasured'}
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
        basepath =  os.path.dirname(__file__)
        path = os.path.join(basepath,'..','qtui','Multiplexer.ui')
        uic.loadUi(path,self)
        self.d = {}
        self.connect() 
    
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync('192.168.169.49')
        try:
            self.server = yield self.cxn.multiplexer_server
            yield self.initializeGUI()
            yield self.setupListeners()
        except:
            self.setEnabled(False)
        
    @inlineCallbacks
    def initializeGUI(self):
        #get initial values
        state = yield self.server.is_cycling()
        self.pushButton.setChecked(state)
        self.setButtonText()
        #fill out information in all available channels
        all_channels = yield self.server.get_available_channels()
        for name in all_channels:
            wavelength = yield self.server.get_wavelength_from_channel(name)
            widget_config = config.info.get(name, None)
            if widget_config is not None: 
                user_hint,  location = widget_config
            else:
                continue
            wrapper = widgetWrapper(name, wavelength, user_hint)
            freq = yield self.server.get_frequency(name)
            wrapper.setFreq(float(freq))
            exp = yield self.server.get_exposure(name)
            wrapper.setExposure(exp)
            state = yield self.server.get_state(name)
            wrapper.setState(state)
            self.grid.addWidget(wrapper.widget,location[0], location[1])
            #connect widgets
            wrapper.widget.checkBox.stateChanged.connect(self.setStateWrapper(name))
            wrapper.widget.spinBox.valueChanged.connect(self.setExposureWrapper(name))
            self.d[name] = wrapper
        #connect functions
        self.pushButton.toggled.connect(self.setOnOff)

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
        if chanName in self.d.keys():
            self.d[chanName].setState(state, True)
        
    def followNewExposure(self, x, (chanName,exp)):
        if chanName in self.d.keys():
            self.d[chanName].setExposure(exp, True)
    
    def followNewFreq(self, x, (chanName, freq)):
        if chanName in self.d.keys():
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
        basepath =  os.path.dirname(__file__)
        path = os.path.join(basepath,'..','qtui','MultiplexerChannel.ui')
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
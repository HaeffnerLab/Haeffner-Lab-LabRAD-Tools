from PyQt5 import QtGui, QtWidgets, uic
import os
from . import RGBconverter as RGB
from twisted.internet.defer import inlineCallbacks
from .MULTIPLEXER_CONTROL_config import multiplexer_control_config as config

SIGNALID1 = 187567
SIGNALID2 = 187568
SIGNALID3 = 187569
SIGNALID4 = 187570
SIGNALID5 = 187571 # for the new locked state signals

class widgetWrapper(object):
    def __init__(self, chanName, wavelength, hint):
        self.chanName = chanName
        self.wavelength = wavelength
        self.hint = hint
        self.widget = None
        self.codeDict = {-3.0: 'UnderExposed', -4.0: 'OverExposed', -5.0: 'NeedStartWM', -6.0 :'NotMeasured'}
        self.widget = multiplexerChannel(self.wavelength, self.hint, self.chanName)           
        
    def setFreq(self, freq):
        if freq in list(self.codeDict.keys()):
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
            
    def setLockedState(self, lockedState, laserlockOn): # for laserlock
        # lockedState, 0 or 1
        if laserlockOn:
            self.widget.setLCDDisplay(lockedState)
        else:
            self.widget.setLCDDisplay(-1)
            
class multiplexerWidget(QtWidgets.QWidget):
    def __init__(self, reactor, parent = None):
        super(multiplexerWidget, self).__init__(parent)
        self.reactor = reactor
        basepath =  os.path.dirname(__file__)
        path = os.path.join(basepath,'..','qtui','Multiplexer.ui')
        uic.loadUi(path,self)
        self.d = {}
        self.connect() 
        
        self.server_laserlock = None
    
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        try:
            self.cxn = yield connectAsync('192.168.169.49',password='lab',tls_mode='off')
        except:
            self.cxn = yield connectAsync('192.168.169.49',password='lab')
        try:
            self.server_laserlock = yield self.cxn.laserlock_server
            self.listenlock = True
        except:
            self.listenlock = False #tells server not to listen if can't connect to server
            print("Laserlock server not responding")
        try:
            self.server = yield self.cxn.multiplexer_server
            yield self.initializeGUI()
            yield self.setupListeners()
        except:
            self.setEnabled(False)
        
    @inlineCallbacks
    def initializeGUI(self):
        try:
            yield self.server_laserlock.start_cycling() # start the laserlock server
            #get initial values
        except:
            print("Laserlock Server not responding")
    
        state = yield self.server.is_cycling()
        self.pushButton.setChecked(state)
        self.setButtonText()
        #fill out information in all available channels
        all_channels = yield self.server.get_available_channels()
        print(all_channels)
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
            
            try:
                lockedState = yield self.server_laserlock.get_lockedstate(name) 
            except:
                lockedState = -3
                
            if lockedState == -1:
                print("Warning: Laser", name, "is not configured with the Laser Lock Detection box yet.")
            elif lockedState == -2:
                print('Warning: No laser of name ', name, 'in Laserlock_config.py.')
            wrapper.setLockedState(lockedState, True) # in the future, we should add an "enable alerts" feature
            
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
        if self.listenlock:
            yield self.server_laserlock.signal__new_lockedstate_measured(SIGNALID5) # for laserlock
            yield self.server_laserlock.addListener(listener = self.followNewLockedState, source = None, ID = SIGNALID5)
        else:
            None
    
    def followNewState(self,x, xxx_todo_changeme):
        (chanName,state) = xxx_todo_changeme
        if chanName in list(self.d.keys()):
            self.d[chanName].setState(state, True)
        
    def followNewExposure(self, x, xxx_todo_changeme1):
        (chanName,exp) = xxx_todo_changeme1
        if chanName in list(self.d.keys()):
            self.d[chanName].setExposure(exp, True)
    
    def followNewFreq(self, x, xxx_todo_changeme2):
        (chanName, freq) = xxx_todo_changeme2
        if chanName in list(self.d.keys()):
            self.d[chanName].setFreq(freq)

    def followNewLockedState(self, x, xxx_todo_changeme3): # for laserlock
        #laserlockOn = self.pushButton.isChecked() 
        (chanName, lockedState) = xxx_todo_changeme3
        laserlockOn = True #for now, always have laserlockOn == True
        if chanName in list(self.d.keys()):
            self.d[chanName].setLockedState(lockedState, laserlockOn)

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

class multiplexerChannel(QtWidgets.QWidget):
    def __init__(self, wavelength, hint, name, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
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
        
    def setLCDDisplay(self, lockedState): # for laserlock: the lcdNumber display widget
        '''
        Parameters: 
        #int laserNum: number from {1,2,3,...,7}
        int lockedState: 0 or 1 for a single laser, instead of for all 7;
            value to display in the LCD (either 0 or 1);  if -1, it means that laserlock widget is off
        '''
        colors = {0:'red', 1:'green'}
        if lockedState == -1: # means laserlockOn is false or this laser is not configured for the Laser Lock detection box yet
            self.lcdNumber.setStyleSheet("QWidget {background-color: white }")
            self.lcdNumber.display(-1)
        elif lockedState == -2: # laser's name is not in Laser_config.py
            self.lcdNumber.setStyleSheet("QWidget {background-color: white }")
            self.lcdNumber.display(-2)
        elif lockedState == -3: # laserlock server is not responding
            self.lcdNumber.setStyleSheet("QWidget {background-color: white }")
            self.lcdNumber.display(-3)
        elif lockedState == 0 or lockedState == 1: 
            self.lcdNumber.setStyleSheet("QWidget {background-color: " + colors[lockedState] + " }")
            self.lcdNumber.display(lockedState)
        else:
            print('Error: lockedState is something other than -1, 0, or 1.')

if __name__=="__main__":
    a = QtWidgets.QApplication( [] )
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    multiplexerWidget = multiplexerWidget(reactor)
    multiplexerWidget.show()
    reactor.run()

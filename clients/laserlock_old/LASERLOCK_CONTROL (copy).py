from PyQt4 import QtGui, uic
import os
import RGBconverter as RGB
from twisted.internet.defer import inlineCallbacks
from LASERLOCK_CONTROL_config import laserlock_control_config as config

SIGNALID1 = 187567 # @@@ Change?
SIGNALID2 = 187568 # @@@ Change?
SIGNALID3 = 187569 # @@@ Change?
SIGNALID4 = 187570 # @@@ Change?
 
class widgetWrapper(object): 
    def __init__(self, chanName):
        self.chanName = chanName
        #self.widget = None
        #self.codeDict = {-3.0: 'UnderExposed', -4.0: 'OverExposed', -5.0: 'NeedStartWM', -6.0 :'NotMeasured'}
        self.widget = laserlockChannel(self.chanName)           
        
    def setLockedState(self, lockedState, laserlockOn): # lockedState (ex: 1001101)
        
#         self.widget.lockedState.setText(lockedState) 
        self.widget.setLabel(str(lockedState))
        
        self.widget.setLCDDisplay(1, 1)
        self.widget.setLCDDisplay(2, 0)
        self.widget.setLCDDisplay(7, 1)
        
        if laserlockOn:
            state_L1 = (int(lockedState)) /1000000; # either a 1 or a 0
            state_L2 = (int(lockedState)) /100000 % 10;
            state_L3 = (int(lockedState)) /10000 % 10;
            state_L4 = (int(lockedState)) /1000 % 10;
            state_L5 = (int(lockedState)) /100 % 10;
            state_L6 = (int(lockedState)) /10 % 10;
            state_L7 = (int(lockedState)) /1 % 10;
            
            self.widget.setLCDDisplay(1, state_L1)
            self.widget.setLCDDisplay(2, state_L2)
            self.widget.setLCDDisplay(3, state_L3)
            self.widget.setLCDDisplay(4, state_L4)
            self.widget.setLCDDisplay(5, state_L5)
            self.widget.setLCDDisplay(6, state_L6)
            self.widget.setLCDDisplay(7, state_L7)
        else:
            self.widget.setLCDDisplay(1, -1)
            self.widget.setLCDDisplay(2, -1)
            self.widget.setLCDDisplay(3, -1)
            self.widget.setLCDDisplay(4, -1)
            self.widget.setLCDDisplay(5, -1)
            self.widget.setLCDDisplay(6, -1)
            self.widget.setLCDDisplay(7, -1)
            
    
    def setState(self, state, disableSignals = False):
        if disableSignals:
            self.widget.checkBox.blockSignals(True)
        self.widget.checkBox.setChecked(state)
        if disableSignals:
            self.widget.checkBox.blockSignals(False)
    """    
    def setExposure(self, exposure, disableSignals = False):
        if disableSignals:
            self.widget.checkBox.blockSignals(True)
        self.widget.spinBox.setValue(exposure)
        if disableSignals:
            self.widget.checkBox.blockSignals(False)
    """
            
class laserlockWidget(QtGui.QWidget):
    def __init__(self, reactor, parent = None):
        super(laserlockWidget, self).__init__(parent)
        self.reactor = reactor # reactor is the Twisted event handling system
        basepath =  os.path.dirname(__file__)
        path = os.path.join(basepath,'..','qtui','Laserlock.ui')
        uic.loadUi(path,self)
        self.d = {} # dictionary of all the widgetwrappers
        self.connect() 
    
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
#         self.cxn = yield connectAsync('192.168.169.49') # this is the ip address of the computer in the laser room
#         self.cxn = yield connectAsync('127.0.0.1') # this is the ip address of the spacetime computer, i think
        self.cxn = yield connectAsync('127.0.0.1')
#         import labrad
#         print '@@@10'
#         self.cxn = yield labrad.connect() # this line breaks the program, for some reason, so i commented it out
        try:
            self.server = yield self.cxn.laserlock_server
            yield self.initializeGUI()
            yield self.setupListeners()
        except:
            self.setEnabled(False)
        
    @inlineCallbacks
    def initializeGUI(self):
        #get initial values
        #yield self.server.start_cycling() # dont use this line. it makes the widget start up really slowly (~5sec)
        state = yield self.server.is_cycling()
        self.pushButton.setChecked(state)
        self.setButtonText()
        #fill out information in all available channels
        all_channels = yield self.server.get_available_channels()
        
        for name in all_channels:
            
            #wavelength = yield self.server.get_wavelength_from_channel(name)
            widget_config = config.info.get(name, None)
            if widget_config is not None: 
                user_hint, location = widget_config
            else:
                continue
            wrapper = widgetWrapper(name)
            lockedState = yield self.server.get_lockedstate(name)
            wrapper.setLockedState(lockedState, self.pushButton.isChecked())
            state = yield self.server.get_state(name)
            wrapper.setState(state)
            
            self.grid.addWidget(wrapper.widget,location[0], location[1])
            #connect widgets
            wrapper.widget.checkBox.stateChanged.connect(self.setStateWrapper(name))
            self.d[name] = wrapper
        #connect functions
        self.pushButton.toggled.connect(self.setOnOff)

    @inlineCallbacks
    def setupListeners(self):
        yield self.server.signal__channel_toggled(SIGNALID1)
        yield self.server.addListener(listener = self.followNewState, source = None, ID = SIGNALID1)
        #yield self.server.signal__new_exposure_set(SIGNALID2)
        #yield self.server.addListener(listener = self.followNewExposure, source = None, ID = SIGNALID2)
        yield self.server.signal__new_lockedstate_measured(SIGNALID3)
        yield self.server.addListener(listener = self.followNewLockedState, source = None, ID = SIGNALID3)
        yield self.server.signal__updated_whether_cycling(SIGNALID4)
        yield self.server.addListener(listener = self.followNewCycling, source = None, ID = SIGNALID4)
    
    def followNewState(self,x,(chanName,state)):
        if chanName in self.d.keys():
            self.d[chanName].setState(state, True)
            
    """  
    def followNewExposure(self, x, (chanName,exp)):
        if chanName in self.d.keys():
            self.d[chanName].setExposure(exp, True)
    """
    
    def followNewLockedState(self, x, (chanName, lockedState)):
        if chanName in self.d.keys():
            self.d[chanName].setLockedState(lockedState, self.pushButton.isChecked())
    
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
    
    '''
    def setExposureWrapper(self, chanName):
        def func(state):
            self.setExposure(chanName, state)
        return func 
    '''
    
    @inlineCallbacks
    def setState(self, chanName, state):
        yield self.server.set_state(chanName,bool(state))
    
    """
    @inlineCallbacks
    def setExposure(self, chanName, exp):
        yield self.server.set_exposure(chanName,exp)
    """
    
    def closeEvent(self, x):
        self.reactor.stop()  

class laserlockChannel(QtGui.QWidget): # this is a small widget. Each contains data for 1 channel 
    def __init__(self, name, parent=None):
        QtGui.QWidget.__init__(self, parent)
        basepath =  os.path.dirname(__file__)
        path = os.path.join(basepath,'..','qtui','LaserlockChannel.ui')
        uic.loadUi(path,self)
        #self.RGBconverter = RGB.RGBconverter()
        #self.setColor(wavelength)
        #self.setHint(hint)
        self.setLabel(name)
    
    """    
    def setColor(self, wavelength):
        [r,g,b] = self.RGBconverter.wav2RGB(int(wavelength))
        self.label.setStyleSheet('color:rgb(%d,%d,%d)' %(r,g,b))
    """
     
    def setLabel(self, name):
        self.label.setText(name)
        
    def setLCDDisplay(self, laserNum, state):
        '''
        Parameters: 
        int laserNum: number from {1,2,3,...,7}
        int state: value to display in the LCD (either 0 or 1),  if -1, it means that laserlock widget is off
        '''
        laserLabels = {1:self.label_3, 2:self.label_4, 3:self.label_5, 4:self.label_6, 5:self.label_7, 6:self.label_8, 7:self.label_9}
        laserLCDs = {1:self.lcdNumber, 2:self.lcdNumber_2, 3:self.lcdNumber_3, 4:self.lcdNumber_4, 5:self.lcdNumber_5, 6:self.lcdNumber_6, 7:self.lcdNumber_7}
        colors = {0:'red', 1:'green'}
        
        if state == -1:
            laserLCDs[laserNum].setStyleSheet("QWidget {background-color: white }")
            laserLCDs[laserNum].display(-1)
        else:
            laserLCDs[laserNum].setStyleSheet("QWidget {background-color: " + colors[state] + " }")
            laserLCDs[laserNum].display(state)
        
    
    
    """
    def setHint(self, hint):
        self.expectedfreq.setText(hint)
    """
    
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    laserlockWidget = laserlockWidget(reactor)
    laserlockWidget.show()
    reactor.run()
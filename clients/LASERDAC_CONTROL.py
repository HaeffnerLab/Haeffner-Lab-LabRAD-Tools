from PyQt4 import QtGui, QtCore, uic
from numpy import *
# from qtui.QCustomSpinBoxION import QCustomSpinBoxION
from .qtui.QCustomSpinBox import QCustomSpinBox
from twisted.internet.defer import inlineCallbacks, returnValue
import sys


try:
    from common.okfpgaservers.laserdac.DacConfiguration import hardwareConfiguration as hc
except:
    sys.path.append('c:\\Users\lab-user\LabRAD\common\okfpgaservers\laserdac')
    from DacConfiguration import hardwareConfiguration as hc

from .qtui.SliderSpin import SliderSpin

UpdateTime = 100 # ms
SIGNALID = 270836
SIGNALID2 = 270835


class CHANNEL_CONTROL (QtGui.QWidget):
    def __init__(self, reactor, parent=None):
        super(CHANNEL_CONTROL, self).__init__(parent)
        self.reactor = reactor
        self.makeGUI()
        self.connect()
     
    def makeGUI(self):
        self.dacDict = dict(list(hc.elec_dict.items()) + list(hc.sma_dict.items()))
        
        self.controls = {k: QCustomSpinBox(hc.channel_name_dict[k], self.dacDict[k].allowedVoltageRange) for k in list(self.dacDict.keys())}

        layout = QtGui.QGridLayout()
        elecBox = QtGui.QGroupBox('Laser Control')
        elecLayout = QtGui.QVBoxLayout()
        elecBox.setLayout(elecLayout)
        layout.addWidget(elecBox, 0, 1)

        elecList = list(hc.elec_dict.keys())
        elecList.sort()
        if bool(hc.centerElectrode):
            elecList.pop(hc.centerElectrode-1)
        for i,e in enumerate(elecList):
            if int(e) <= len(elecList)/2:
                elecLayout.addWidget(self.controls[e])
            elif int(e) > len(elecList)/2:
                elecLayout.addWidget(self.controls[e])

        spacer = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.MinimumExpanding)
      
        self.inputUpdated = False                
        self.timer = QtCore.QTimer(self)        
        self.timer.timeout.connect(self.sendToServer)
        self.timer.start(UpdateTime)
        
        for k in list(self.dacDict.keys()):
            self.controls[k].onNewValues.connect(self.inputHasUpdated(k))

        layout.setColumnStretch(1, 1)                   
        self.setLayout(layout)

    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        try:
            self.cxn = yield connectAsync('192.168.169.49',password='lab', tls_mode='off')
        except:
            self.cxn = yield connectAsync('192.168.169.49',password='lab')

        yield self.setupListeners()
        if self.initialized:
            yield self.followSignal(0, 0)

    def inputHasUpdated(self, name):
        def iu():
            self.inputUpdated = True
            self.changedChannel = name
        return iu

    def sendToServer(self):
        if self.inputUpdated:
            value = float(round(self.controls[self.changedChannel].spinLevel.value(), 3))
            self.dacserver.set_individual_analog_voltages([(self.changedChannel, value)])
            self.inputUpdated = False
            
    @inlineCallbacks    
    def setupListeners(self):
        try:
            self.dacserver = yield self.cxn['LASERDAC Server']
            yield self.dacserver.signal__ports_updated(SIGNALID2)
            yield self.dacserver.addListener(listener = self.followSignal, source = None, ID = SIGNALID2)
            self.initialized = True
            self.setEnabled(True)
        except:
            self.initialized = False
            self.setEnabled(False)

        # signal when server connects or disconnects
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989+1, True)
        yield self.cxn.manager.addListener(listener = self.followServerConnect, source = None, ID = 9898989)
        yield self.cxn.manager.addListener(listener = self.followServerDisconnect, source = None, ID = 9898989+1)    
        
    
    @inlineCallbacks
    def followSignal(self, x, s):
        print('notified here')
        av = yield self.dacserver.get_analog_voltages()
        for (c, v) in av:
            self.controls[c].setValueNoSignal(v)

    @inlineCallbacks
    def followServerConnect(self, cntx, server_name):
        server_name = server_name[1]
        if server_name == 'LASERDAC Server':
            self.dacserver = yield self.cxn['LASERDAC Server']
            yield self.dacserver.signal__ports_updated(SIGNALID2)
            yield self.dacserver.addListener(listener = self.followSignal, source = None, ID = SIGNALID2)
            self.initialized = True
            yield self.followSignal(0, 0)
            self.setEnabled(True)
        else:
            yield None

    @inlineCallbacks
    def followServerDisconnect(self, cntx, server_name):
        server_name = server_name[1]
        if server_name == 'LASERDAC Server':
            self.initialized = False
            self.setEnabled(False)
            yield None
        else:
            yield None

    def setEnabled(self, value):
        for key in list(self.controls.keys()):
            self.controls[key].spinLevel.setEnabled(value)

    def closeEvent(self, x):
        self.reactor.stop()        


class DAC_Control(QtGui.QMainWindow):
    def __init__(self, reactor, parent=None):
        super(DAC_Control, self).__init__(parent)
        self.reactor = reactor   

        channelControlTab = self.buildChannelControlTab()        
        # scanTab = self.buildScanTab()
        #tab = QtGui.QTabWidget()
        #tab.addTab(channelControlTab, '&Channels')
        self.setWindowTitle('Laser Control')
        #self.setCentralWidget(tab)
        self.setCentralWidget(channelControlTab)
    
    def buildChannelControlTab(self):
        widget = QtGui.QWidget()
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(CHANNEL_CONTROL(self.reactor),0,0)
        widget.setLayout(gridLayout)
        return widget
        
    def closeEvent(self, x):
        self.reactor.stop()  

if __name__ == "__main__":
    a = QtGui.QApplication( [] )
    from . import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    DAC_Control = DAC_Control(reactor)
    DAC_Control.show()
    reactor.run()

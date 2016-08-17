from PyQt4 import QtGui, QtCore, uic
from numpy import *
# from qtui.QCustomSpinBoxION import QCustomSpinBoxION
from qtui.QCustomSpinBox import QCustomSpinBox
from twisted.internet.defer import inlineCallbacks, returnValue
import sys

sys.path.append('c:\Users\lab-user\LabRAD\common\okfpgaservers\laserdac')

#from common.okfpgaservers.laserdac.DacConfiguration import hardwareConfiguration as hc
from DacConfiguration import hardwareConfiguration as hc

from qtui.SliderSpin import SliderSpin

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
        self.dacDict = dict(hc.elec_dict.items() + hc.sma_dict.items())
        
        self.controls = {k: QCustomSpinBox(hc.channel_name_dict[k], self.dacDict[k].allowedVoltageRange) for k in self.dacDict.keys()}

        layout = QtGui.QGridLayout()
        elecBox = QtGui.QGroupBox('Laser Control')
        elecLayout = QtGui.QVBoxLayout()
        elecBox.setLayout(elecLayout)
        layout.addWidget(elecBox, 0, 1)

        elecList = hc.elec_dict.keys()
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
        
        for k in self.dacDict.keys():
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

        self.dacserver = yield self.cxn.dac_server
        yield self.setupListeners()
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
        yield self.dacserver.signal__ports_updated(SIGNALID2)
        yield self.dacserver.addListener(listener = self.followSignal, source = None, ID = SIGNALID2)
    
    @inlineCallbacks
    def followSignal(self, x, s):
        print 'notified here'
        av = yield self.dacserver.get_analog_voltages()
        for (c, v) in av:
            self.controls[c].setValueNoSignal(v)

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
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    DAC_Control = DAC_Control(reactor)
    DAC_Control.show()
    reactor.run()

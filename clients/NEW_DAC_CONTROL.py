from PyQt5 import QtCore, QtGui, QtWidgets, uic
from numpy import *
# from qtui.QCustomSpinBoxION import QCustomSpinBoxION
from .qtui.QCustomSpinBox import QCustomSpinBox
from twisted.internet.defer import inlineCallbacks, returnValue
import sys
import time
# sys.path.append('/home/cct/LabRAD/common/abstractdevices')
from common.okfpgaservers.dacserver.DacConfiguration import hardwareConfiguration as hc
from common.clients.dac_scanner import scan_field


ScanWait = 45*1000 # ms
UpdateTime = 100 # ms
max = 2
min = -2
n = 3
SIGNALID = 270836
SIGNALID2 = 270835

class MULTIPOLE_CONTROL(QtWidgets.QWidget):
    def __init__(self, reactor, parent=None):
        super(MULTIPOLE_CONTROL, self).__init__(parent)
        self.updating = False
        self.reactor = reactor
        self.connect()
        
    @inlineCallbacks    
    def makeGUI(self):
        self.multipoles = yield self.dacserver.get_multipole_names()
        self.controls = {k: QCustomSpinBox(k, (-20.,20.),decimals=5,step_size=0.00001) for k in self.multipoles}
#        for i,el in self.controls:
#            el.spinLevel.setDecimals(4)
        self.multipoleValues = {k: 0.0 for k in self.multipoles}
        
        for k in self.multipoles:
            self.ctrlLayout.addWidget(self.controls[k])        
        self.multipoleFileSelectButton = QtWidgets.QPushButton('Set C File')
        self.ctrlLayout.addWidget(self.multipoleFileSelectButton)

        self.inputUpdated = False
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.sendToServer)
        self.timer.start(UpdateTime)   

        for k in self.multipoles:
            self.controls[k].onNewValues.connect(self.inputHasUpdated)
        self.multipoleFileSelectButton.released.connect(self.selectCFile)
        self.setLayout(self.ctrlLayout)
        yield self.followSignal(0, 0)    
        
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        self.cxn = yield connectAsync()
        self.dacserver  = yield self.cxn.dac_server
        yield self.setupListeners()
        self.ctrlLayout = QtWidgets.QVBoxLayout()
        yield self.makeGUI()
        
    def inputHasUpdated(self):
        self.inputUpdated = True
        for k in self.multipoles:
            self.multipoleValues[k] = round(self.controls[k].spinLevel.value(), 5)
        
    def sendToServer(self):
        if self.inputUpdated:
            self.dacserver.set_multipole_values(list(self.multipoleValues.items()))
            self.inputUpdated = False
    
    @inlineCallbacks        
    def selectCFile(self):
        fn = QtWidgets.QFileDialog().getOpenFileName()[0]
        self.updating = True
        yield self.dacserver.set_control_file(str(fn))
        for i in range(self.ctrlLayout.count()): self.ctrlLayout.itemAt(i).widget().close()
        self.updating = False
        yield self.makeGUI()
        self.inputHasUpdated()
        
    @inlineCallbacks    
    def setupListeners(self):
        yield self.dacserver.signal__ports_updated(SIGNALID)
        yield self.dacserver.addListener(listener = self.followSignal, source = None, ID = SIGNALID) 
        
    @inlineCallbacks
    def followSignal(self, x, s):
        if self.updating: return
        multipoles = yield self.dacserver.get_multipole_values()
        for (k,v) in multipoles:
            self.controls[k].setValueNoSignal(v)          

    def closeEvent(self, x):
        self.reactor.stop()  

class CHANNEL_CONTROL (QtWidgets.QWidget):
    def __init__(self, reactor, parent=None):
        super(CHANNEL_CONTROL, self).__init__(parent)
        self.reactor = reactor
        self.makeGUI()
        self.connect()
     
    def makeGUI(self):
        self.dacDict = dict(list(hc.elec_dict.items()) + list(hc.sma_dict.items()))
        self.controls = {k: QCustomSpinBox(k, self.dacDict[k].allowedVoltageRange) for k in list(self.dacDict.keys())}
        layout = QtWidgets.QGridLayout()
        if bool(hc.sma_dict):
            smaBox = QtWidgets.QGroupBox('SMA Out')
            smaLayout = QtWidgets.QVBoxLayout()
            smaBox.setLayout(smaLayout)
        elecBox = QtWidgets.QGroupBox('Electrodes')
        elecLayout = QtWidgets.QGridLayout()
        elecBox.setLayout(elecLayout)
        if bool(hc.sma_dict):
            layout.addWidget(smaBox, 0, 0)
        layout.addWidget(elecBox, 0, 1)

        for s in hc.sma_dict:
            smaLayout.addWidget(self.controls[s], alignment = QtCore.Qt.AlignRight)
        elecList = list(hc.elec_dict.keys())
        elecList.sort()
            
        elecListHALF=list(range(0,len(elecList)-2,2))

        for i in elecListHALF:
            layout.addWidget(self.controls[elecList[i]],i+1,2,1,1)
            layout.addWidget(self.controls[elecList[i+1]],i+1,3,1,1)
        layout.addWidget(self.controls['Q39'],11,1,1,1)
        layout.addWidget(self.controls['Q40'],11,4,1,1)
                        
        #elecLayout.addItem(QtGui.QLayoutItem.spacerItem(),1,0,1,8)    
        elecLayout.setRowMinimumHeight(0,20)
        elecLayout.setRowMinimumHeight(1,20)
        elecLayout.setRowMinimumHeight(2,10) 
        elecLayout.setRowMinimumHeight(3,20)
        elecLayout.setRowMinimumHeight(4,20)
        elecLayout.setColumnMinimumWidth(0,20)
        elecLayout.setColumnMinimumWidth(1,20)
        elecLayout.setColumnMinimumWidth(2,20)
        elecLayout.setColumnMinimumWidth(3,20)
        elecLayout.setColumnMinimumWidth(4,20)
        
       

        spacer = QtWidgets.QSpacerItem(20,40,QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.MinimumExpanding)
        if bool(hc.sma_dict):
            smaLayout.addItem(spacer)        
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
        self.cxn = yield connectAsync()
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
            self.dacserver.set_individual_analog_voltages([(self.changedChannel, round(self.controls[self.changedChannel].spinLevel.value(), 3))]*17)
            self.inputUpdated = False
            
    @inlineCallbacks    
    def setupListeners(self):
        yield self.dacserver.signal__ports_updated(SIGNALID2)
        yield self.dacserver.addListener(listener = self.followSignal, source = None, ID = SIGNALID2)
    
    @inlineCallbacks
    def followSignal(self, x, s):
     #   print 'notified here'
        av = yield self.dacserver.get_analog_voltages()
        for (c, v) in av:
            self.controls[c].setValueNoSignal(v)

    def closeEvent(self, x):
        self.reactor.stop() 

class MULTIPOLE_MONITOR(QtWidgets.QWidget):  #######################################################
    def __init__(self, reactor, parent=None):
        super(MULTIPOLE_MONITOR, self).__init__(parent)
        self.reactor = reactor        
        self.makeGUI()
        self.connect()


    def makeGUI(self): 
        
        self.multipolelist = hc.default_multipoles
        self.displays = {k: QtWidgets.QLCDNumber() for k in self.multipolelist}  
        layout = QtWidgets.QGridLayout()
        Multipolebox = QtWidgets.QGroupBox('Multipoles')
        multilayout = QtWidgets.QGridLayout()
        
        
        Multipolebox.setLayout(multilayout)
        layout.addWidget(Multipolebox,0,0)
        
        i = 0 
        for e in self.multipolelist:
            multilayout.addWidget(QtWidgets.QLabel(e),i,0)
            multilayout.addWidget(self.displays[e],i,1)
            i = i+1
        
        self.inputUpdated = False                
        
        self.setLayout(layout)      

    def inputHasUpdated(self):
        def iu():
            self.inputUpdated = True
        return iu
    
#######################################################

    @inlineCallbacks    
    def setmultipole(self, multipoles):    
        list1 = [('Ex',multipoles[0]),('Ey',multipoles[1]),('Ez',multipoles[2]),('U3',10)]
        print("setting multipoles")
        yield self.dacserver.set_multipole_values(list1)
        yield self.connect()
                     
            
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        self.cxn = yield connectAsync()
        self.dacserver = yield self.cxn.dac_server
        self.ionInfo = {}
        yield self.setupListeners()
        yield self.followSignal(0, 0)    
        for i in hc.notused_dict:        #Sets unused channels to about 0V
            yield self.dacserver.set_individual_digital_voltages_u([(i, 32768)])     

   
    @inlineCallbacks    
    def setupListeners(self):
        yield self.dacserver.signal__ports_updated(SIGNALID2)
        yield self.dacserver.addListener(listener = self.followSignal, source = None, ID = SIGNALID2)

    @inlineCallbacks
    def followSignal(self, x, s):        
        av = yield self.dacserver.get_multipole_values()
        brightness = 210
        darkness = 255 - brightness           
        for (k, v) in av:
            print(str(k)+", "+str(v))
            self.displays[k].display(float(v)) 

    def closeEvent(self, x):
        self.reactor.stop()       

class MULTIPOLE_MONITOR_SCAN(QtWidgets.QWidget):  #######################################################
    def __init__(self, reactor, parent=None):
        super(MULTIPOLE_MONITOR_SCAN, self).__init__(parent)
        self.reactor = reactor        
        self.makeGUI()
        self.connect()


    def makeGUI(self):
        
        self.scan = False
        self.counter = 0
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.scanner)
        self.timer.start(ScanWait)   
        
        self.multipolelist = hc.default_multipoles
        self.displays = {k: QtWidgets.QLCDNumber() for k in self.multipolelist}  
        layout = QtWidgets.QGridLayout()
        Multipolebox = QtWidgets.QGroupBox('Multipoles')
        multilayout = QtWidgets.QGridLayout()
        self.startscanbutton = QtWidgets.QPushButton('Start Scan')
        self.stopscanbutton = QtWidgets.QPushButton('Stop Scan')
        self.counterdisplay = QCustomSpinBox('counter',[0, n**3])
        
        
        Multipolebox.setLayout(multilayout)
        layout.addWidget(Multipolebox,0,0)
        
        i = 0 
        for e in self.multipolelist:
            multilayout.addWidget(QtWidgets.QLabel(e),i,0)
            multilayout.addWidget(self.displays[e],i,1)
            i = i+1
        multilayout.addWidget(self.startscanbutton,i,1)  
        multilayout.addWidget(self.stopscanbutton,i+1,1)  
        multilayout.addWidget(self.counterdisplay,i+2,1)
        self.startscanbutton.pressed.connect(self.startscan)
        self.stopscanbutton.pressed.connect(self.stopscan)
        
        self.inputUpdated = False                
        self.timer = QtCore.QTimer(self)        
        self.timer.timeout.connect(self.updateCounter)
        self.timer.start(ScanWait - 1)
        self.counterdisplay.onNewValues.connect(self.inputHasUpdated())
        
        self.setLayout(layout)      
        self.fields = scan_field(min,max,n)

    def inputHasUpdated(self):
        def iu():
            self.inputUpdated = True
            self.counter = int(round(self.counterdisplay.spinLevel.value()))
        return iu

    def updateCounter(self):
        if self.inputUpdated:            
            self.inputUpdated = False
        else:
            self.counterdisplay.setValues(self.counter)
    
    def startscan(self):
        self.scan = True
        

    def stopscan(self):
        self.scan = False
#######################################################
    
    @inlineCallbacks
    def scanner(self):
        if self.scan == True:
            el = self.fields[self.counter]
            yield self.setmultipole(el)
            self.counter = self.counter + 1
            print((str((n**3- self.counter)*ScanWait/1000/60) + ' minutes left'))
            if self.counter == len(self.fields):
                self.counter = 0
                self.scan = False
                print('scan done!')


    @inlineCallbacks    
    def setmultipole(self, multipoles):    
        list1 = [('Ex',multipoles[0]),('Ey',multipoles[1]),('Ez',multipoles[2]),('U3',10)]
        print("setting multipoles")
        yield self.dacserver.set_multipole_values(list1)
        yield self.connect()
                     
            
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        self.cxn = yield connectAsync()
        self.dacserver = yield self.cxn.dac_server
        self.ionInfo = {}
        yield self.setupListeners()
        yield self.followSignal(0, 0)    
        for i in hc.notused_dict:        #Sets unused channels to about 0V
            yield self.dacserver.set_individual_digital_voltages_u([(i, 32768)])     

   
    @inlineCallbacks    
    def setupListeners(self):
        yield self.dacserver.signal__ports_updated(SIGNALID2)
        yield self.dacserver.addListener(listener = self.followSignal, source = None, ID = SIGNALID2)

    @inlineCallbacks
    def followSignal(self, x, s):        
        av = yield self.dacserver.get_multipole_values()
        brightness = 210
        darkness = 255 - brightness           
        for (k, v) in av:
            print(str(k)+", "+str(v))
            self.displays[k].display(float(v)) 

    def closeEvent(self, x):
        self.reactor.stop()
        

class CHANNEL_MONITOR(QtWidgets.QWidget):  
    def __init__(self, reactor, parent=None):
        super(CHANNEL_MONITOR, self).__init__(parent)
        self.reactor = reactor        
        self.makeGUI()
        self.connect()
       
        
    def makeGUI(self):      
        self.dacDict = dict(list(hc.elec_dict.items()) + list(hc.sma_dict.items()))
        self.displays = {k: QtWidgets.QLCDNumber() for k in list(self.dacDict.keys())}               
        layout = QtWidgets.QGridLayout()
        if bool(hc.sma_dict):        
            smaBox = QtWidgets.QGroupBox('SMA Out')
            smaLayout = QtWidgets.QGridLayout()
            smaBox.setLayout(smaLayout)       
        elecBox = QtWidgets.QGroupBox('Electrodes')
        elecLayout = QtWidgets.QGridLayout()
    
    
        elecBox.setLayout(elecLayout)
        if bool(hc.sma_dict):
            layout.addWidget(smaBox, 0, 0)
        layout.addWidget(elecBox, 0, 1)
        
        if bool(hc.sma_dict):
            for k in hc.sma_dict:
                self.displays[k].setAutoFillBackground(True)
                smaLayout.addWidget(QtWidgets.QLabel(k), self.dacDict[k].smaOutNumber, 0)
                smaLayout.addWidget(self.displays[k], self.dacDict[k].smaOutNumber, 1)
                s = hc.sma_dict[k].smaOutNumber+1

        elecList = list(hc.elec_dict.keys())
        elecList.sort()

        elecListHALF=list(range(0,len(elecList)-2,2))

        for i in elecListHALF:
            elecLayout.addWidget(QtWidgets.QLabel(elecList[i]),i+1,3,1,1)
            elecLayout.addWidget(self.displays[elecList[i]],i+1,4,1,1)
            elecLayout.addWidget(QtWidgets.QLabel(elecList[i+1]),i+1,5,1,1)
            elecLayout.addWidget(self.displays[elecList[i+1]],i+1,6,1,1)
        elecLayout.addWidget(QtWidgets.QLabel('Q39'),11,1,1,1)
        elecLayout.addWidget(self.displays['Q39'],11,2,1,1)
        elecLayout.addWidget(QtWidgets.QLabel('Q40'),11,7,1,1)
        elecLayout.addWidget(self.displays['Q40'],11,8,1,1)

        #elecLayout.addItem(QtGui.QLayoutItem.spacerItem(),1,0,1,8)    
        elecLayout.setRowMinimumHeight(1,20)
        elecLayout.setRowMinimumHeight(3,20)
        elecLayout.setRowMinimumHeight(4,20) 
        elecLayout.setRowMinimumHeight(6,20)
        elecLayout.setColumnMinimumWidth(1,20)
        elecLayout.setColumnMinimumWidth(3,20)
        elecLayout.setColumnMinimumWidth(4,20)
        elecLayout.setColumnMinimumWidth(6,20)
        if bool(hc.sma_dict):
            spacer = QtWidgets.QSpacerItem(20,40,QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.MinimumExpanding)
            smaLayout.addItem(spacer, s, 0,10, 2)  

        self.setLayout(layout)  
                
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        self.cxn = yield connectAsync()
        self.dacserver = yield self.cxn.dac_server
        self.ionInfo = {}
        yield self.setupListeners()
        yield self.followSignal(0, 0)    
        for i in hc.notused_dict:        #Sets unused channels to about 0V
            yield self.dacserver.set_individual_digital_voltages_u([(i, 32768)])     

                  
    @inlineCallbacks    
    def setupListeners(self):
        yield self.dacserver.signal__ports_updated(SIGNALID2)
        yield self.dacserver.addListener(listener = self.followSignal, source = None, ID = SIGNALID2)
    
    @inlineCallbacks
    def followSignal(self, x, s):       
        av = yield self.dacserver.get_analog_voltages()
        brightness = 210
        darkness = 255 - brightness           
        for (k, v) in av:
            print(str(k)+", "+str(v))
            self.displays[k].display(float(v)) 
            if abs(v) > 30:
                self.displays[k].setStyleSheet("QWidget {background-color: orange }")
            else:
                R = int(brightness + v*darkness/30.)
                G = int(brightness - abs(v*darkness/30.))
                B = int(brightness - v*darkness/30.)
                hexclr = '#%02x%02x%02x' % (R, G, B)
                self.displays[k].setStyleSheet("QWidget {background-color: "+hexclr+" }")

    def closeEvent(self, x):
        self.reactor.stop()

class DAC_Control(QtWidgets.QMainWindow):
    def __init__(self, reactor, parent=None):
        super(DAC_Control, self).__init__(parent)
        self.reactor = reactor   

        channelControlTab = self.buildChannelControlTab()        
        multipoleControlTab = self.buildMultipoleControlTab()
        #multipoleScanTab = self.buildMultipoleScanTab()
        # scanTab = self.buildScanTab()
        tab = QtWidgets.QTabWidget()
        tab.addTab(multipoleControlTab,'&Multipoles')
        tab.addTab(channelControlTab, '&Channels')
        #tab.addTab(multipoleScanTab, '&Multipole Scan')
        # tab.addTab(scanTab, '&Scans')
        self.setWindowTitle('DAC Control')
        self.setCentralWidget(tab)
    
    def buildMultipoleControlTab(self):
        widget = QtWidgets.QWidget()
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.addWidget(CHANNEL_MONITOR(self.reactor),0,0)
        gridLayout.addWidget(MULTIPOLE_CONTROL(self.reactor),0,1)
        widget.setLayout(gridLayout)
        return widget

    def buildChannelControlTab(self):
        widget = QtWidgets.QWidget()
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.addWidget(CHANNEL_CONTROL(self.reactor),0,0)
        gridLayout.addWidget(MULTIPOLE_MONITOR(self.reactor),0,1)
        widget.setLayout(gridLayout)
        return widget
    
    def buildMultipoleScanTab(self):
        widget =QtWidgets.QWidget()
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.addWidget(CHANNEL_MONITOR(self.reactor),0,0)
        gridLayout.addWidget(MULTIPOLE_MONITOR_SCAN(self.reactor),0,1) ##WE MUST BUILD
        widget.setLayout(gridLayout)
        return widget    
        
    def buildScanTab(self):
        from SCAN_CONTROL import Scan_Control_Tickle
        widget = QtWidgets.QWidget()
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.addWidget(Scan_Control_Tickle(self.reactor, 'Ex1'), 0, 0)
        gridLayout.addWidget(Scan_Control_Tickle(self.reactor, 'Ey1'), 0, 1)
        widget.setLayout(gridLayout)
        return widget
    
    def closeEvent(self, x):
        self.reactor.stop()  
        

if __name__ == "__main__":
    a = QtWidgets.QApplication( [] )
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    DAC_Control = DAC_Control(reactor)
    DAC_Control.show()
    reactor.run()

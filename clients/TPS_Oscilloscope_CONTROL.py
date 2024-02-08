from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks

class TPSClient (QtGui.QWidget):
    def __init__(self, reactor, parent=None):
        QtGui.Qwidget.__init__(self)
        self.reactor = reactor
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync()
        self.server = yield self.cxn.TektronixTPS
        yield self.initializeGUI()
        
    @inlineCallbacks
    def initializeGUI(self):
        self.d = {}
        #set layout
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        self.setFrameStyle(0x0001 | 0x0030)
        #get switch names and add them to the layout, and connect their function
        layout.addWidget(QtGui.QLabel('Switches'),0,0)
        switchNames = yield self.server.get_channels()
        switchNames = [el[0] for el in switchNames] #picking first of the tuple
        if self.channels is not None:
            channels = [name for name in self.channels if name in switchNames]
        else:
            channels = switchNames
        for order,name in enumerate(channels):
            #setting up physical container
            groupBox = QtGui.QGroupBox(name) 
            groupBoxLayout = QtGui.QVBoxLayout()
            buttonOn = QtGui.QPushButton('ON')
            buttonOn.setAutoExclusive(True)
            buttonOn.setCheckable(True)
            buttonOff = QtGui.QPushButton('OFF')
            buttonOff.setCheckable(True)
            buttonOff.setAutoExclusive(True)
            buttonAuto = QtGui.QPushButton('Auto')
            buttonAuto.setCheckable(True)
            buttonAuto.setAutoExclusive(True)
            groupBoxLayout.addWidget(buttonOn)
            groupBoxLayout.addWidget(buttonOff)
            groupBoxLayout.addWidget(buttonAuto)
            groupBox.setLayout(groupBoxLayout)
            #setting initial state
            initstate = yield self.server.get_state(name)
            ismanual = initstate[0]
            manstate = initstate[1]
            if not ismanual:
                buttonAuto.setChecked(True)
            else:
                if manstate:
                    buttonOn.setChecked(True)
                else:
                    buttonOff.setChecked(True)
            #adding to dictionary for signal following
            self.d[name] = {}
            self.d[name]['ON'] = buttonOn
            self.d[name]['OFF'] = buttonOff
            self.d[name]['AUTO'] = buttonAuto
            buttonOn.clicked.connect(self.buttonConnectionManualOn(name))
            buttonOff.clicked.connect(self.buttonConnectionManualOff(name))
            buttonAuto.clicked.connect(self.buttonConnectionAuto(name))
            layout.addWidget(groupBox,0,1 + order)
        
        
        
# Soenke's commands.
import labrad
import numpy
import time

cxn = labrad.connect()
tps = cxn.tektronixtps_server()
tps.select_device()

while(1):
    optstr=input('taking data on pressing return, enter string to be added to filename:\n')
    answer=tps.getcurve()
    outstring = ''
    for x in range(len(answer)):
        outstring = outstring + str(( (answer[x])[0] ).value)
        outstring = outstring + ' '
        outstring = outstring + str(( (answer[x])[1] ).value )
        outstring = outstring + '\n'
    filename='data_resonator/curve_osci_'+time.strftime("%d%m%Y_%H%M_")+optstr+'.csv'
    #numpy.savetxt(filename,outstring)
    f = open(filename, 'w')
    f.write(outstring)
    f.close

    #time.sleep(60)

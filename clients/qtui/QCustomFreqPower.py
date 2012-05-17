import sys
from PyQt4 import QtGui
from PyQt4 import QtCore,uic
import os

class QCustomFreqPower(QtGui.QWidget):
    def __init__(self, title, parent=None):
        QtGui.QWidget.__init__(self, parent)
        basepath =  os.path.dirname(__file__)
        path = os.path.join(basepath, 'powerfreqspin.ui')
        uic.loadUi(path,self)
        self.title.setText(title)
        self.buttonSwitch.clicked.connect(self.setText)
        self.buttonSwitch.toggled.connect(self.setText)
    
    def setPowerRange(self, powerrange):
        self.spinPower.setRange(*powerrange)
    
    def setFreqRange(self, freqrange):
        self.spinFreq.setRange(*freqrange)
        
    def setPowerNoSignal(self, power):
        self.spinPower.blockSignals(True)
        self.spinPower.setValue(power)
        self.spinPower.blockSignals(False)
        
    def setFreqNoSignal(self, freq):
        self.spinFreq.blockSignals(True)
        self.spinFreq.setValue(freq)
        self.spinFreq.blockSignals(False)
    
    def setStateNoSignal(self, state):
        self.buttonSwitch.blockSignals(True)
        self.buttonSwitch.setChecked(state)
        self.setText(state)
        self.buttonSwitch.blockSignals(False)
        
    def setText(self, down):
        if down:
            self.buttonSwitch.setText('ON')
        else:
            self.buttonSwitch.setText('OFF')

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    icon = QCustomFreqPower('Control')
    icon.show()
    app.exec_()
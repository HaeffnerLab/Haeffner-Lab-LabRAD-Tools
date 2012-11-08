import sys
from PyQt4 import QtGui, QtCore

class TextChangingButton(QtGui.QPushButton):
    """Button that changes its text to ON or OFF and colors when it's pressed""" 
    def __init__(self, parent = None):
        super(TextChangingButton, self).__init__(parent)
        self.setCheckable(True)
        self.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=10))
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        #connect signal for appearance changing
        self.toggled.connect(self.setAppearance)
        self.setAppearance(self.isDown())
    
    def setAppearance(self, down):
        if down:
            self.setText('I')
            self.setPalette(QtGui.QPalette(QtCore.Qt.darkGreen))
        else:
            self.setText('O')
            self.setPalette(QtGui.QPalette(QtCore.Qt.black))
    
    def sizeHint(self):
        return QtCore.QSize(37, 26)

class QCustomFreqPower(QtGui.QFrame):
    def __init__(self, title, switchable = True, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(title, switchable)
    
    def makeLayout(self, title, switchable):
        layout = QtGui.QGridLayout()
        #labels
        title = QtGui.QLabel(title)
        title.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        title.setAlignment(QtCore.Qt.AlignCenter)
        freqlabel = QtGui.QLabel('Frequency (MHz)')
        powerlabel = QtGui.QLabel('Power (dBM)')
        if switchable:
            layout.addWidget(title,0, 0, 1, 3)
        else:
            layout.addWidget(title,0, 0, 1, 2)
        layout.addWidget(freqlabel,1, 0, 1, 1)
        layout.addWidget(powerlabel,1, 1, 1, 1)
        #editable fields
        self.spinFreq = QtGui.QDoubleSpinBox()
        self.spinFreq.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        self.spinFreq.setDecimals(3)
        self.spinFreq.setSingleStep(0.1)
        self.spinFreq.setRange(10.0,250.0)
        self.spinFreq.setKeyboardTracking(False)
        self.spinPower = QtGui.QDoubleSpinBox()
        self.spinPower.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        self.spinPower.setDecimals(2)
        self.spinPower.setSingleStep(0.1)
        self.spinPower.setRange(-145.0, 30.0)
        self.spinPower.setKeyboardTracking(False)
        layout.addWidget(self.spinFreq,     2, 0)
        layout.addWidget(self.spinPower,    2, 1)
        if switchable:
            self.buttonSwitch = TextChangingButton()
            layout.addWidget(self.buttonSwitch, 2, 2)
        self.setLayout(layout)
    
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
        self.buttonSwitch.setAppearance(state)
        self.buttonSwitch.blockSignals(False)

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    icon = QCustomFreqPower('Control')
    icon.show()
    app.exec_()
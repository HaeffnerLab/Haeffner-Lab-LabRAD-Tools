import sys
from PyQt5 import QtCore, QtGui, QtWidgets

class TextChangingButton(QtWidgets.QPushButton):
    """Button that changes its text to ON or OFF and colors when it's pressed""" 
    def __init__(self, parent = None):
        super(TextChangingButton, self).__init__(parent)
        self.setCheckable(True)
        self.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=10))
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
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

class QCustomFreqPower(QtWidgets.QFrame):
    def __init__(self, title, switchable = True, parent=None, stepSize = 0.1):
        QtWidgets.QWidget.__init__(self, parent)
        self.stepSize = stepSize
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(title, switchable)

    
    def makeLayout(self, title, switchable):
        layout = QtWidgets.QGridLayout()
        #labels
        title = QtWidgets.QLabel(title)
        title.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=12, weight=QtGui.QFont.Bold))
        title.setAlignment(QtCore.Qt.AlignCenter)
        freqlabel = QtWidgets.QLabel('Frequency (MHz)')
        powerlabel = QtWidgets.QLabel('Power (dBM)')
        if switchable:
            layout.addWidget(title,0, 0, 1, 3)
        else:
            layout.addWidget(title,0, 0, 1, 2)
        layout.addWidget(freqlabel,1, 0, 1, 1)
        layout.addWidget(powerlabel,1, 1, 1, 1)
        #editable fields
        self.spinFreq = QtWidgets.QDoubleSpinBox()
        self.spinFreq.setFont(QtGui.QFont('MS Shell Dlg 2', pointSize=13))
        self.spinFreq.setDecimals(3)
        self.spinFreq.setSingleStep(self.stepSize)
        self.spinFreq.setRange(10.0,250.0)
        self.spinFreq.setKeyboardTracking(False)
        self.spinPower = QtWidgets.QDoubleSpinBox()
        self.spinPower.setFont(QtGui.QFont('MS Shell Dlg 2', pointSize=13))
        self.spinPower.setDecimals(2)
        self.spinPower.setSingleStep(0.1)
        self.spinPower.setRange(-145.0, 30.0)
        self.spinPower.setKeyboardTracking(False)
        self.spinFreq.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.spinPower.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
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
        self.spinPower.setValue(power['dBm'])
        self.spinPower.blockSignals(False)
        
    def setFreqNoSignal(self, freq):
        self.spinFreq.blockSignals(True)
        self.spinFreq.setValue(freq['MHz'])
        self.spinFreq.blockSignals(False)
    
    def setStateNoSignal(self, state):
        self.buttonSwitch.blockSignals(True)
        self.buttonSwitch.setChecked(state)
        self.buttonSwitch.setAppearance(state)
        self.buttonSwitch.blockSignals(False)

if __name__=="__main__":
    app = QtWidgets.QApplication(sys.argv)
    icon = QCustomFreqPower('Control')
    icon.show()
    app.exec_()

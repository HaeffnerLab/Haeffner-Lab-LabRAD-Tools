import sys
from PyQt4 import QtGui
from PyQt4 import QtCore

class SliderSpin(QtGui.QFrame):
    def __init__(self, title, unit, initrange, absrange , parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.constructLayout(title, unit, initrange, absrange)
        self.connectWidgets()
    
    def constructLayout(self, titleName, unitName, initrange, absrange):
        #setting qframe properties
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setFrameShadow(QtGui.QFrame.Sunken)
        #title and unit
        titleFont = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        titleFont.setBold(True)
        title = QtGui.QLabel(titleName)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setFont(titleFont)
        unit = QtGui.QLabel(unitName)
        unit.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        #spin and slider
        self.spin = QtGui.QSpinBox()
        self.spin.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        self.spin.setMinimumWidth(75)
        self.spin.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.MinimumExpanding)
        self.spin.setRange(*initrange)
        self.spin.setKeyboardTracking(False)
        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(*initrange)
        self.slider.setMinimumWidth(250)
        #min and max ranges
        self.minrange = QtGui.QSpinBox()
        self.maxrange = QtGui.QSpinBox()
        for range in [self.minrange, self.maxrange]:
            range.setMinimumWidth(50)
            range.setRange(*absrange)
            range.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
            range.setKeyboardTracking(False)
        self.minrange.setValue(initrange[0])
        self.maxrange.setValue(initrange[1])
        #adding widgets to layout
        layout = QtGui.QGridLayout()
        layout.addWidget(title, 0, 0, 1, 3)
        layout.addWidget(unit, 0, 3)
        layout.addWidget(self.slider, 1, 0, 1, 3)
        layout.addWidget(self.spin, 1, 3, 2, 1)
        layout.addWidget(self.minrange, 2, 0)
        layout.addWidget(self.maxrange, 2, 2)
        self.setLayout(layout)
    
    def connectWidgets(self):
        self.minrange.valueChanged.connect(self.setRange)
        self.maxrange.valueChanged.connect(self.setRange)
        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)
           
    def setRange(self):
        minrange = self.minrange.value()
        maxrange = self.maxrange.value()
        self.spin.setRange(minrange,maxrange)
        self.slider.setRange(minrange,maxrange)

    def setValueNoSignal(self, value):
        self.spin.blockSignals(True)
        self.slider.blockSignals(True)
        self.spin.setValue(value)
        self.slider.setValue(value)
        self.spin.blockSignals(False)
        self.slider.blockSignals(False)        

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    icon = SliderSpin('Control','mV',(100,1100),(0,2500))
    icon.show()
    app.exec_()
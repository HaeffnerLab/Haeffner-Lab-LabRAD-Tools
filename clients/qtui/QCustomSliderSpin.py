import sys
from PyQt4 import QtGui
from PyQt4 import QtCore,uic
import os

class QCustomSliderSpin(QtGui.QWidget):
    def __init__(self, title, unit, initrange, absrange , parent=None):
        QtGui.QWidget.__init__(self, parent)
        basepath = os.environ.get('LABRADPATH',None)
        if not basepath:
            raise Exception('Please set your LABRADPATH environment variable')
        path = os.path.join(basepath,'lattice/clients/qtui/sliderspin.ui')
        uic.loadUi(path,self)
        self.title.setText(title)
        self.unit.setText(unit)
        self.minrange.setRange(*absrange)
        self.maxrange.setRange(*absrange)
        self.minrange.valueChanged.connect(self.setRange)
        self.maxrange.valueChanged.connect(self.setRange)
        self.minrange.setValue(initrange[0])
        self.maxrange.setValue(initrange[1])
	
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
    icon = QCustomSliderSpin('Control','mV',(100,900),(0,2500))
    icon.show()
    app.exec_()
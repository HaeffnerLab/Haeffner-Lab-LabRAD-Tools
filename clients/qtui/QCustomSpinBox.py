import sys
import os
from PyQt4 import QtGui
from PyQt4 import QtCore,uic

class QCustomSpinBox(QtGui.QWidget):
    onNewValues = QtCore.pyqtSignal()
    def __init__(self, title, levelRange, parent=None):
        QtGui.QWidget.__init__(self, parent)
	basepath = os.path.dirname(__file__)
        path = os.path.join(basepath,'titlespin.ui')
        uic.loadUi(path,self)
        self.title.setText(title)
        self.levelRange = levelRange
        self.spinLevel.setRange(*levelRange)
        self.spinLevel.setDecimals(3)
        self.level = 0
        self.spinLevel.valueChanged.connect(self.spinLevelChanged)

    def setValues(self, level):
        self.disconnectAll()
        self.spinLevel.setValue(level)
        self.level = level
        self.connectAll()
        
    def setStepSize(self, step):
        self.spinLevel.setSingleStep(step)
    
    def spinLevelChanged(self, newlevel):
        oldlevel = self.level
        withinRange = self.checkRange(newlevel)
        if withinRange:
            self.level = newlevel
            self.disconnectAll()
            self.onNewValues.emit()
            self.connectAll()
        else:
            suggestedLevel = self.suggestLevel(newlevel)
            self.spinLevel.setValue(suggestedLevel)
    
    def suggestLevel(self, level):
        #if spin box value selected too high, goes to the highest possible value
        if level < self.levelRange[0]:
            suggestion = self.levelRange[0]
        if level > self.levelRange[1]:
            suggestion = self.levelRange[1]
        return suggestion
    
    def checkRange(self,val):
        if self.levelRange[0] <= val <= self.levelRange[1]:
            return True
        else:
            return False
    
    def checkBounds(self, val):
    	if val < self.levelRange[0]:
    	      output = self.levelRange[0]
    	elif val > self.levelRange[1]:
    	      output = self.levelRange[1]
    	else:
    	      output = val
    	return output
	
    def disconnectAll(self):
        self.spinLevel.blockSignals(True)
    
    def connectAll(self):
        self.spinLevel.blockSignals(False)
        
    def setValueNoSignal(self, value):
        self.spinLevel.blockSignals(True)
        self.spinLevel.setValue(value)
        self.spinLevel.blockSignals(False)
        
if __name__=='__main__':
	app = QtGui.QApplication(sys.argv)
	icon = QCustomLevelSpin('Control',(0.0,100.0))
	icon.show()
	app.exec_()

 

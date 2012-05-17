import sys
import os
from PyQt4 import QtGui
from PyQt4 import QtCore,uic
import math

class QCustomLevelTilt(QtGui.QWidget):
    onNewValues = QtCore.pyqtSignal()
    def __init__(self, title,channelNames, levelRange, parent=None):
        QtGui.QWidget.__init__(self, parent)
        basepath =  os.path.dirname(__file__)
        path = os.path.join(basepath, 'leveltiltslider.ui')
        uic.loadUi(path,self)
        #set widget properties
        self.title.setText(title)
        self.labelLeft.setText(channelNames[0])
        self.labelRight.setText(channelNames[1])
        self.levelRange = levelRange
        #set ranges
        self.setRange(levelRange)
        self.dict = {'level':0, 'tilt':0}
        #connect functions
        self.sliderLevel.valueChanged.connect(self.sliderLevelChanged)
        self.sliderTilt.valueChanged.connect(self.sliderTiltChanged)
        self.spinLevel.valueChanged.connect(self.spinLevelChanged)
        self.spinTilt.valueChanged.connect(self.spinTiltChanged)
        self.valueLeft.valueChanged.connect(self.outputChanged)
        self.valueRight.valueChanged.connect(self.outputChanged)

    def setRange(self, levelRange):
        maxDifference = abs(levelRange[1] - levelRange[0])
        self.spinLevel.setRange(*levelRange)
        self.sliderLevel.setRange(100.*levelRange[0],100.*levelRange[1])
        self.spinTilt.setRange(-maxDifference,maxDifference)
        self.sliderTilt.setRange(-100.*maxDifference,100.*maxDifference)
        self.valueLeft.setRange(*levelRange)
        self.valueRight.setRange(*levelRange)
        
    def setValues(self, one, two):
        self.disconnectAll()
        one = self.checkBounds(one)
        two = self.checkBounds(two)
        self.valueLeft.setValue(one)
        self.valueRight.setValue(two)
        [level, tilt] = self.OutputToLeveLTilt(one,two)
        self.spinLevel.setValue(level)
        self.sliderLevel.setValue(100*level)
        self.spinTilt.setValue(tilt)
        self.sliderTilt.setValue(100*tilt)
        self.dict['level'] = level
        self.dict['tilt'] = tilt
        self.connectAll()
        
    def setStepSize(self, step):
        self.spinLevel.setSingleStep(step)
        self.spinTilt.setSingleStep(step)
        self.valueLeft.setSingleStep(step)
        self.valueRight.setSingleStep(step)

    def sliderLevelChanged(self,newlevel):
        #if the change results in outputs not within range then don't perform
        oldlevel = self.dict['level']
        withinRange = self.checkLevelTilt(newlevel/100., self.dict['tilt'])
        if withinRange:
            self.dict['level'] = newlevel/100.
            self.disconnectAll()
            self.spinLevel.setValue(newlevel/100.)
            self.updateOutputs()
            self.connectAll()
        else:
            self.sliderLevel.setValue(oldlevel*100.)
    
    def spinLevelChanged(self, newlevel):
        oldlevel = self.dict['level']
        withinRange = self.checkLevelTilt(newlevel, self.dict['tilt'])
        if withinRange:
            self.dict['level'] = newlevel
            self.disconnectAll()
            self.sliderLevel.setValue(newlevel*100)
            self.updateOutputs()
            self.connectAll()
        else:
            suggestedLevel = self.suggestLevel(newlevel)
            self.spinLevel.setValue(suggestedLevel)
    
    def suggestLevel(self, level):
        #if spin box value selected too high, goes to the highest possible value
        [one,two] = self.LevelTiltToOutput(level, self.dict['tilt'])
        if one > self.levelRange[1]:
            s = self.levelRange[1] + self.dict['tilt']/2.
            suggestion = math.floor(100 * s) / 100. #way to round down the 4th digit i.e 12.305 to 12.30
        elif two > self.levelRange[1]:
            s = self.levelRange[1] - self.dict['tilt']/2.
            suggestion = math.floor(100 * s) / 100.
        elif one < self.levelRange[0]:
            s = self.levelRange[0] + self.dict['tilt']/2.
            suggestion = math.ceil(100 * s) / 100.
        elif two < self.levelRange[0]:
            s = self.levelRange[0] - self.dict['tilt']/2.
            suggestion = math.ceil(100 * s) / 100.
        return suggestion
      
    def sliderTiltChanged(self, newtilt):
        oldtilt = self.dict['tilt']
        withinRange = self.checkLevelTilt(self.dict['level'], newtilt/100.)
        if withinRange:
            self.dict['tilt'] = newtilt/100.
            self.disconnectAll()
            self.spinTilt.setValue(newtilt/100.)
            self.updateOutputs()
            self.connectAll()
        else:
            self.sliderTilt.setValue(oldtilt*100.)
    
    def spinTiltChanged(self,newtilt):
        oldtilt = self.dict['tilt']
        withinRange = self.checkLevelTilt(self.dict['level'], newtilt)
        if withinRange:
            self.dict['tilt'] = newtilt
            self.disconnectAll()
            self.sliderTilt.setValue(newtilt*100.)
            self.updateOutputs()
            self.connectAll()
        else:
            suggestedTilt = self.suggestTilt(newtilt)
            self.spinTilt.setValue(suggestedTilt)
            
    def suggestTilt(self, tilt):
        [one,two] = self.LevelTiltToOutput(self.dict['level'], tilt)
        if one > self.levelRange[1]:
            s = -(self.levelRange[1] - self.dict['level']) * 2
            suggestion = math.ceil(100 * s) / 100.
        elif two > self.levelRange[1]:
            s = (self.levelRange[1] - self.dict['level']) * 2
            suggestion = math.floor(100 * s) / 100.
        elif one < self.levelRange[0]:
            s = -(self.levelRange[0] - self.dict['level']) * 2
            suggestion = math.floor(100 * s) / 100.
        elif two < self.levelRange[0]:
            s = (self.levelRange[0] - self.dict['level']) * 2
            suggestion = math.ceil(100 * s) / 100.
        return suggestion

    def outputChanged(self):
        one = self.valueLeft.value()
        two = self.valueRight.value()
        [level, tilt] = self.OutputToLeveLTilt(one,two)
        self.disconnectAll()
        self.spinLevel.setValue(level)
        self.sliderLevel.setValue(100*level)
        self.spinTilt.setValue(tilt)
        self.sliderTilt.setValue(100*tilt)
        self.dict['level'] = level
        self.dict['tilt'] = tilt
        self.connectAll()
        self.onNewValues.emit()
        
    def updateOutputs(self):
        level = self.dict['level']
        tilt = self.dict['tilt']
        [one,two] = self.LevelTiltToOutput(level,tilt)
    	one = self.checkBounds(one)
    	two = self.checkBounds(two)
        self.valueLeft.setValue(one)
        self.valueRight.setValue(two)
        self.onNewValues.emit()

    def LevelTiltToOutput(self, level, tilt):
        one = level - tilt/2.
        two = level + tilt/2.
        return [one,two]
    
    def checkLevelTilt(self, level, tilt):
        [one,two] = self.LevelTiltToOutput(level,tilt)
        withinRange = self.checkRange(one) and self.checkRange(two)
        return withinRange
    
    def OutputToLeveLTilt(self, one, two):
        level = ( one + two )/2.
        tilt = two - one
        return [level,tilt]
    
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
        self.sliderLevel.blockSignals(True)
        self.sliderTilt.blockSignals(True)
        self.spinLevel.blockSignals(True)
        self.spinTilt.blockSignals(True)
        self.valueLeft.blockSignals(True)
        self.valueRight.blockSignals(True)
    
    def connectAll(self):
        self.sliderLevel.blockSignals(False)
        self.sliderTilt.blockSignals(False)
        self.spinLevel.blockSignals(False)
        self.spinTilt.blockSignals(False)
        self.valueLeft.blockSignals(False)
        self.valueRight.blockSignals(False)
    
        
if __name__=='__main__':
	app = QtGui.QApplication(sys.argv)
	icon = QCustomLevelTilt('Control',['A','B'],(0.0,100.0))
	icon.show()
	app.exec_()

 

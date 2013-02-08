'''
Analysis Window
'''

from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks
import numpy as np
from scipy import optimize

from fitgaussian import FitGaussian
from fitline import FitLine
from fitlorentzian import FitLorentzian
from fitparabola import FitParabola

class AnalysisWindow(QtGui.QWidget):
    
    def __init__(self, parent, text):
        super(AnalysisWindow, self).__init__()
        self.text = text
        self.parent = parent     
        self.cxn = self.parent.parent.parent.cxn
        self.createContext()
        self.parameterSpinBoxes = {}
        self.parameterLabels = {} 

        self.fitLine = FitLine(self)
        self.fitGaussian = FitGaussian(self)
        self.fitLorentzian = FitLorentzian(self)
        self.fitParabola = FitParabola(self)
        self.fitCurveDictionary = {self.fitLine.curveName: self.fitLine,
                                   self.fitGaussian.curveName: self.fitGaussian,
                                   self.fitLorentzian.curveName: self.fitLorentzian,
                                   self.fitParabola.curveName: self.fitParabola
                                   }           
 
        
        self.initUI()
        
    def initUI(self):      

        self.setWindowTitle(self.text)

        self.combo = QtGui.QComboBox(self)
        for curveName in self.fitCurveDictionary.keys():
            self.combo.addItem(curveName)
            self.combo.itemText(1)

#        self.lbl = QtGui.QLabel(self.combo.itemText(0), self)
#        self.hello1 = QtGui.QLabel('hi1', self)
#        self.hello2 = QtGui.QLabel('hi2', self)
#        self.hello3 = QtGui.QLabel('hi3', self)

        self.combo.move(50, 50)
#        self.lbl.move(50, 150)

        self.combo.activated[str].connect(self.onActivated)        
         
#        self.setGeometry(300, 300, 300, 200)

        self.parameterTable = QtGui.QTableWidget()
        self.parameterTable.setColumnCount(3)

        self.mainLayout = QtGui.QVBoxLayout()
        self.parameterLayout = QtGui.QHBoxLayout()
        
        
       
        self.setLayout(self.mainLayout)
        self.mainLayout.addLayout(self.parameterLayout)
        self.parameterLayout.addWidget(self.combo)
        self.parameterLayout.addWidget(self.parameterTable)
#        self.grid.addWidget(self.combo, 0, 0, QtCore.Qt.AlignCenter)
        self.setupParameterTable(self.combo.itemText(0))
        
        fitButton = QtGui.QPushButton("Fit", self)
        fitButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        self.mainLayout.addWidget(fitButton)
        
        self.show()

    def setupParameterTable(self, curveName):
        curveName = str(curveName)
        
        # clear the existing widgets      
        self.parameterTable.clear()
        self.parameterLabels = {}
        self.parameterSpinBoxes = {}
        self.parameterTable.setRowCount(len(self.fitCurveDictionary[curveName].parameterNames))
#        self.parameterTable.setRowCount(5)
        for parameterName in self.fitCurveDictionary[curveName].parameterNames:
            # Create things
            self.parameterLabels[parameterName] = QtGui.QLabel(parameterName)
            self.parameterSpinBoxes[parameterName] = QtGui.QDoubleSpinBox()
            self.parameterSpinBoxes[parameterName].setDecimals(6)
            self.parameterSpinBoxes[parameterName].setRange(-1000000000, 1000000000)
            self.parameterSpinBoxes[parameterName].setValue(1)
            self.parameterSpinBoxes[parameterName].setSingleStep(.1)
            self.parameterSpinBoxes[parameterName].setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
            self.parameterSpinBoxes[parameterName].setKeyboardTracking(False)
#            self.connect(self.parameterSpinBoxes[curveName], QtCore.SIGNAL('valueChanged(double)'), self.parent.parent.drawCurvesSignal)

        for i in range(len(self.parameterLabels.values())):
            print i
            self.parameterTable.setCellWidget(i, 0, self.parameterLabels.values()[i])

        for i in range(len(self.parameterSpinBoxes.values())):
            self.parameterTable.setCellWidget(i, 1, self.parameterSpinBoxes.values()[i])
        
    def onActivated(self, text):
        # this is where we remake the grid, yea just remake it, let's make a function
      
        self.setupParameterTable(self.combo.currentText()) 
        print 'hello asshole'    

    @inlineCallbacks
    def createContext(self):
        self.context = yield self.cxn.context()
       
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
    
    def __init__(self, parent, text, ident):
        super(AnalysisWindow, self).__init__()
        self.text = text
        self.dataset, self.directory, self.index = ident
        self.parent = parent     
        self.cxn = self.parent.parent.parent.cxn
        self.createContext()
        self.parameterSpinBoxes = {}
        self.parameterLabels = {} 
        self.solutionsDictionary = {}

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
         
#        self.setGeometry(300, 300, 500, 300)
        
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
        
        self.fitButton = QtGui.QPushButton("Fit", self)
        self.fitButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        self.fitButton.clicked.connect(self.fitCurveSignal)        

        self.mainLayout.addWidget(self.fitButton)
        
        self.show()

    def setupParameterTable(self, curveName):
        self.curveName = str(curveName)
        
        # clear the existing widgets      
        self.parameterTable.clear()
        self.parameterLabels = {}
        self.parameterSpinBoxes = {}
        self.parameterTable.setRowCount(len(self.fitCurveDictionary[self.curveName].parameterNames))
#        self.parameterTable.setRowCount(5)
        for parameterName in self.fitCurveDictionary[self.curveName].parameterNames:
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
            self.parameterTable.setCellWidget(i, 0, self.parameterLabels.values()[i])

        for i in range(len(self.parameterSpinBoxes.values())):
            self.parameterTable.setCellWidget(i, 1, self.parameterSpinBoxes.values()[i])
            
        self.resizeWindow()
       
        
    def onActivated(self, text):
        # this is where we remake the grid, yea just remake it, let's make a function
      
        self.setupParameterTable(self.combo.currentText()) 
        
    def fitCurveSignal(self, evt):
        self.fitCurves()
        
    def drawCurvesSignal(self, evt):
        self.fitCurves(drawCurves = True)

    def fitCurves(self, parameters = None, drawCurves = False):
        labels = self.parent.parent.qmc.datasetLabelsDict[self.dataset, self.directory]
        self.fitCurveDictionary[self.curveName].fitCurve(self.dataset, self.directory, self.index, labels[self.index], parameters, drawCurves)
        # now the solutions (dictionary) should be set, so we use them to fill the 3rd column
        i = 0
        for solution in self.solutionsDictionary[self.dataset, self.directory, self.index, self.curveName]:
            item = QtGui.QTableWidgetItem()
            item.setText(str(solution))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.parameterTable.setItem(i, 2, item)
            i += 1

        self.resizeWindow()
        
    @inlineCallbacks
    def createContext(self):
        self.context = yield self.cxn.context()
       
    def resizeWindow(self):
        self.parameterTable.resizeColumnsToContents()
        self.parameterTable.resizeRowsToContents()
        self.resize(self.sizeHint())
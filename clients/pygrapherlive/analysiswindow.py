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
        self.parameterSpinBoxDict = {}

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
#        self.parameterTable.setHorizontalHeaderLabels(QtCore.QStringList(['Parameters','Manual','Fitted']))
        self.parameterTable.setHorizontalHeaderItem(0, QtGui.QTableWidgetItem('Parameters'))
        self.parameterTable.horizontalHeader().setStretchLastSection(True)
#        self.horizontalHeader.setStretchLastSection(True)
        self.parameterTable.verticalHeader().setVisible(False)

        self.mainLayout = QtGui.QVBoxLayout()
        self.parameterLayout = QtGui.QHBoxLayout()
        self.buttonLayout = QtGui.QHBoxLayout()
       
        self.setLayout(self.mainLayout)
        self.mainLayout.addLayout(self.parameterLayout)
        self.mainLayout.addLayout(self.buttonLayout)
        self.parameterLayout.addWidget(self.combo)
        self.parameterLayout.addWidget(self.parameterTable)
#        self.grid.addWidget(self.combo, 0, 0, QtCore.Qt.AlignCenter)
        
        self.fitButton = QtGui.QPushButton("Fit", self)
        self.fitButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        self.fitButton.clicked.connect(self.fitCurveSignal)        

        self.acceptManualButton = QtGui.QPushButton("Accept Manual", self)
        self.acceptManualButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        self.acceptManualButton.clicked.connect(self.acceptManualSignal) 
        
        self.acceptFittedButton = QtGui.QPushButton("Accept Fitted", self)
        self.acceptFittedButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        self.acceptFittedButton.clicked.connect(self.acceptFittedSignal)   

        self.setRanges()

        self.buttonLayout.addWidget(self.fitButton)
        self.buttonLayout.addWidget(self.acceptManualButton)
        self.buttonLayout.addWidget(self.acceptFittedButton)
        
        self.manualTextLayout = QtGui.QHBoxLayout()
        manualLabel = QtGui.QLabel("Manual values: ")
        self.manualTextBox = QtGui.QLineEdit(readOnly=True)
        self.manualTextLayout.addWidget(manualLabel)
        self.manualTextLayout.addWidget(self.manualTextBox)
        self.mainLayout.addLayout(self.manualTextLayout)

        self.fittedTextLayout = QtGui.QHBoxLayout()
        fittedLabel = QtGui.QLabel("Fitted values: ")
        self.fittedTextBox = QtGui.QLineEdit(readOnly=True)
        self.fittedTextLayout.addWidget(fittedLabel)
        self.fittedTextLayout.addWidget(self.fittedTextBox)
        self.mainLayout.addLayout(self.fittedTextLayout)      
        
        self.setupParameterTable(self.combo.itemText(0))
 
        
        self.show()

    def setRanges(self):
        xmin, xmax = self.parent.parent.qmc.getDataXLimits()
        fitRangeLabel = QtGui.QLabel('Fit Range: ')
        self.minRange = QtGui.QDoubleSpinBox()
        self.minRange.setDecimals(6)
        self.minRange.setRange(xmin, xmax)
        self.minRange.setValue(xmin)
        self.minRange.setSingleStep(.1)
        self.minRange.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.minRange.setKeyboardTracking(False)
        self.connect(self.minRange, QtCore.SIGNAL('valueChanged(double)'), self.minRangeSignal)
        self.maxRange = QtGui.QDoubleSpinBox()
        self.maxRange = QtGui.QDoubleSpinBox()
        self.maxRange.setDecimals(6)
        self.maxRange.setRange(xmin, xmax)
        self.maxRange.setValue(xmax)
        self.maxRange.setSingleStep(.1)
        self.maxRange.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.maxRange.setKeyboardTracking(False)  
        self.connect(self.maxRange, QtCore.SIGNAL('valueChanged(double)'), self.maxRangeSignal)
        
        self.buttonLayout.addWidget(fitRangeLabel)
        self.buttonLayout.addWidget(self.minRange)
        self.buttonLayout.addWidget(self.maxRange)
        
    def minRangeSignal(self, evt):
        self.minRange.setRange(self.minRange.minimum(), self.maxRange.value())
    def maxRangeSignal(self, evt):
        self.maxRange.setRange(self.minRange.value(), self.maxRange.maximum())


    def setupParameterTable(self, curveName):
        self.curveName = str(curveName)
        
        # clear the existing widgets      
        self.parameterTable.clear()
        self.parameterTable.setHorizontalHeaderLabels(QtCore.QStringList(['Parameters','Manual','Fitted']))
#        self.parameterTable.setHorizontalHeaderItem(0, QtGui.QTableWidgetItem('Parameters'))
#        self.horizontalHeader = self.parameterTable.horizontalHeader()
        
        self.parameterLabels = {}
        self.parameterSpinBoxes = {}
        self.parameterTable.setRowCount(len(self.fitCurveDictionary[self.curveName].parameterNames))
#        self.parameterTable.setRowCount(5)

        try:
            test = self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName]
        except:
            # no previously saved parameters, create them
            self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName] = [{}, {}]
            for parameterName in self.fitCurveDictionary[self.curveName].parameterNames:
                 self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][0][parameterName] = 1.0
                 self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][1][parameterName] = 1.0

        i = 0
        for parameterName in self.fitCurveDictionary[self.curveName].parameterNames:
            # Create things
            self.parameterLabels[parameterName] = QtGui.QLabel(parameterName)
            self.parameterLabels[parameterName].setAlignment(QtCore.Qt.AlignCenter)
            self.parameterSpinBoxes[parameterName] = QtGui.QDoubleSpinBox()
            self.parameterSpinBoxDict[self.parameterSpinBoxes[parameterName]] = parameterName
            self.parameterSpinBoxes[parameterName].setDecimals(6)
            self.parameterSpinBoxes[parameterName].setRange(-1000000000, 1000000000)
            self.parameterSpinBoxes[parameterName].setValue(self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][0][parameterName])                
            self.parameterSpinBoxes[parameterName].setSingleStep(.1)
            self.parameterSpinBoxes[parameterName].setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
            self.parameterSpinBoxes[parameterName].setKeyboardTracking(False)
            self.connect(self.parameterSpinBoxes[parameterName], QtCore.SIGNAL('valueChanged(double)'), self.drawCurvesSignal)
            
            self.parameterTable.setCellWidget(i, 0, self.parameterLabels[parameterName])
            self.parameterTable.setCellWidget(i, 1, self.parameterSpinBoxes[parameterName])
            item = QtGui.QTableWidgetItem()
            item.setText(str(self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][1][parameterName]))
            item.setFlags(QtCore.Qt.ItemIsEditable)
            self.parameterTable.setItem(i, 2, item)

            i += 1
        
        
        self.manualTextBox.setText('\'Fit\', [\''+str(self.index)+'\', \''+ self.curveName + '\', ' + '\'' + str(self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][0].values()) + '\']')
        self.fittedTextBox.setText('\'Fit\', [\''+str(self.index)+'\', \''+ self.curveName + '\', ' + '\'' + str(self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][1].values()) + '\']')

#        self.resize(self.sizeHint())
        self.resizeWindow()
#        self.adjustSize()      
        
    def onActivated(self, text):
        # this is where we remake the grid, yea just remake it, let's make a function
      
        self.setupParameterTable(self.combo.currentText()) 
        
    def fitCurveSignal(self, evt):
        self.fitCurves()
        
    def drawCurvesSignal(self, evt):
        sender = self.sender()
        self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][0][self.parameterSpinBoxDict[sender]] = sender.value()
        self.manualTextBox.setText('\'Fit\', [\''+str(self.index)+'\', \''+ self.curveName + '\', ' + '\'' + str(self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][0].values()) + '\']')
        self.fitCurves(drawCurves = True)

    def fitCurves(self, parameters = None, drawCurves = False):
        labels = self.parent.parent.qmc.datasetLabelsDict[self.dataset, self.directory]
        self.fitCurveDictionary[self.curveName].fitCurve(self.dataset, self.directory, self.index, labels[self.index], parameters, drawCurves)
        # now the solutions (dictionary) should be set, so we use them to fill the 3rd column
        if (drawCurves == False):
            i = 0
            for solution in self.solutionsDictionary[self.dataset, self.directory, self.index, self.curveName]:
                item = QtGui.QTableWidgetItem()
                item.setText(str(solution))
                item.setFlags(QtCore.Qt.ItemIsEditable)
                self.parameterTable.setItem(i, 2, item)
                i += 1
            i = 0
            for parameterName in self.fitCurveDictionary[self.curveName].parameterNames:
                self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][1][parameterName] = self.solutionsDictionary[self.dataset, self.directory, self.index, self.curveName][i]
                i += 1
            self.fittedTextBox.setText('\'Fit\', [\''+str(self.index)+'\', \''+ self.curveName + '\', ' + '\'' + str(self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][1].values()) + '\']')
            
        self.resizeWindow()
        
    @inlineCallbacks
    def createContext(self):
        self.context = yield self.cxn.context()


    @inlineCallbacks
    def acceptManualSignal(self, evt):
        yield self.parent.parent.parent.cxn.data_vault.cd(self.directory, context = self.context)
        yield self.parent.parent.parent.cxn.data_vault.open(self.dataset, context = self.context)
        yield self.parent.parent.parent.cxn.data_vault.add_parameter_over_write('Accept-' + str(self.index), True, context = self.context)
        # the fitted solutions are already in data vault, this would overwrite them with the manual
        solutions = []
        for c in range(self.parameterTable.rowCount()):
            solutions.append(self.parameterTable.cellWidget(c, 1).value())
        yield self.parent.parent.parent.cxn.data_vault.add_parameter_over_write('Solutions'+'-'+str(self.index)+'-'+self.curveName, solutions, context = self.context)
        self.close()

    @inlineCallbacks
    def acceptFittedSignal(self, evt):
        yield self.parent.parent.parent.cxn.data_vault.cd(self.directory, context = self.context)
        yield self.parent.parent.parent.cxn.data_vault.open(self.dataset, context = self.context)
        yield self.parent.parent.parent.cxn.data_vault.add_parameter_over_write('Accept-' + str(self.index), True, context = self.context)
        self.close()
        
       
    def resizeWindow(self):
        oldSize = self.parameterTable.sizeHint() # qsize
#        print 'old: ', oldSize
        self.parameterTable.resizeColumnsToContents()
        self.parameterTable.resizeRowsToContents()
        w = 0
        for c in range(self.parameterTable.columnCount()):
            w = w + self.parameterTable.columnWidth(c)
        w = w + self.parameterTable.verticalHeader().width() + self.parameterTable.autoScrollMargin()
        h = 0
        for c in range(self.parameterTable.rowCount()):
            h = h + self.parameterTable.rowHeight(c)
        h = h + self.parameterTable.horizontalHeader().height() + 5
        
#        print 'new w and h: ', w, h
        finalSize = QtCore.QSize()
        sizeHint = self.sizeHint()
        sizeW = sizeHint.width()
        sizeH = sizeHint.height()

#        print 'hint: ', sizeHint
        finalSize.setWidth(sizeW + (w - oldSize.width()))
        finalSize.setHeight(sizeH + (h - oldSize.height()))
#        print 'final: ', finalSize
        self.resize(finalSize)
        
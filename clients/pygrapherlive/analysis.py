'''
Analysis Widget
'''
from PyQt4 import QtCore, QtGui
from twisted.internet.defer import inlineCallbacks
import numpy as np
from scipy import optimize

class AnalysisWidget(QtGui.QWidget):
    """Creates the window for the new plot"""
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)  
        self.parent = parent     
        self.cxn = self.parent.parent.cxn
        self.createContext()
        self.parameterWindow = ParameterWindow(self)
        self.analysisCheckboxes = {}      
        self.fitCurveDictionary = {'Line': self.fitLine,
                                   'Gaussian': self.fitGaussian,
                                   'Lorentzian': self.fitLorentzian,
                                   'Parabola': self.fitParabola
                                   }   
        self.solutionsDictionary = {}
        self.setMaximumWidth(180)

        mainLayout = QtGui.QVBoxLayout()
                
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(5)
        
        title = QtGui.QLabel()
        title.setText('Analysis')
              
        dummyLayout = QtGui.QHBoxLayout()
        mainLayout.addLayout(dummyLayout)
        dummyLayout.addWidget(title, QtCore.Qt.AlignCenter)

        self.analysisCheckboxes['Gaussian'] = QtGui.QCheckBox('Gaussian', self)
        self.analysisCheckboxes['Lorentzian'] = QtGui.QCheckBox('Lorentzian', self)
        self.analysisCheckboxes['Parabola'] = QtGui.QCheckBox('Parabola', self)
        self.analysisCheckboxes['Line'] = QtGui.QCheckBox('Line', self)
               
        self.grid.addWidget(self.analysisCheckboxes['Gaussian'], 1, 0, QtCore.Qt.AlignLeft)
        self.grid.addWidget(self.analysisCheckboxes['Lorentzian'], 1, 1, QtCore.Qt.AlignLeft)
        self.grid.addWidget(self.analysisCheckboxes['Parabola'], 2, 0, QtCore.Qt.AlignLeft)
        self.grid.addWidget(self.analysisCheckboxes['Line'], 2, 1, QtCore.Qt.AlignLeft)       
        
        mainLayout.addLayout(self.grid)
        
        # Layout for keeping track of datasets on a graph and analysis
        self.datasetCheckboxListWidget = QtGui.QListWidget()
        self.datasetCheckboxListWidget.setMaximumWidth(180)
        self.datasetCheckboxListWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        mainLayout.addWidget(self.datasetCheckboxListWidget)

        # button to fit data on screen
        parametersButton = QtGui.QPushButton("Parameters", self)
        parametersButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        parametersButton.clicked.connect(self.setParameters)        
        mainLayout.addWidget(parametersButton)
        
        # button to fit data on screen
        fitButton = QtGui.QPushButton("Fit Curves", self)
        fitButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        fitButton.clicked.connect(self.fitCurvesSignal)        
        mainLayout.addWidget(fitButton)
        
        # button to fit data on screen
        drawButton = QtGui.QPushButton("Draw Curves", self)
        drawButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        drawButton.clicked.connect(self.drawCurvesSignal)        
        mainLayout.addWidget(drawButton)        
        
        # button to fit data on screen
        togglePointsButton = QtGui.QPushButton("Toggle Points", self)
        togglePointsButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        togglePointsButton.clicked.connect(self.togglePointsSignal)        
        mainLayout.addWidget(togglePointsButton)        
        
        self.setLayout(mainLayout)        

    @inlineCallbacks
    def createContext(self):
        self.context = yield self.cxn.context()

    def setParameters(self, evt):
        self.parameterWindow.show()
        # create the parameter window upstairs, spinboxes will be part of it

    def togglePointsSignal(self, evt):
        for dataset,directory,index in self.parent.datasetAnalysisCheckboxes.keys():
            # if dataset is intended to be drawn (a checkbox governs this)
            if self.parent.datasetAnalysisCheckboxes[dataset, directory, index].isChecked():
                self.parent.qmc.togglePoints(dataset, directory, index)
            else:
                self.parent.qmc.toggleLine(dataset, directory, index)
            
                
                    
    def fitCurvesSignal(self, evt):
        self.fitCurves()
        
    def drawCurvesSignal(self, evt):
        self.fitCurves(drawCurves = True)

    def fitCurves(self, parameters = None, drawCurves = False):
        self.solutionsDictionary = {}
        for dataset,directory,index in self.parent.datasetAnalysisCheckboxes.keys():
            # if dataset is intended to be drawn (a checkbox governs this)
            if self.parent.datasetAnalysisCheckboxes[dataset, directory, index].isChecked():
                for key in self.analysisCheckboxes.keys():
                    if self.analysisCheckboxes[key].isChecked():
                        labels = self.parent.qmc.datasetLabelsDict[dataset, directory]
#                        print dataset, directory, index, key
                        # MULTIPLE LINES IN THE SAME DATASET!!!!
                        fitFunction = self.fitCurveDictionary[key]
                        fitFunction(dataset, directory, index, labels[index], parameters, drawCurves)
        if (drawCurves == False):                        
            self.solutionsWindow = SolutionsWindow(self, self.context, self.solutionsDictionary)
            self.solutionsWindow.show()

    @inlineCallbacks
    def fitGaussian(self, dataset, directory, index, label, parameters, drawCurves):
        dataX, dataY = self.parent.qmc.plotDict[dataset, directory][index].get_data() # dependent variable
        dataX = np.array(dataX)
        xmin, xmax = self.parent.qmc.ax.get_xlim()
        selectedXValues = np.where((dataX >= xmin) & (dataX <= xmax))[0]
        dataX = dataX[(dataX >= xmin) & (dataX <= xmax)]
        newYData = np.zeros(len(dataX))
        j = 0
        for i in selectedXValues:
            newYData[j] = dataY[i]
            j += 1
               
#        xValues = np.arange(len(dataY))
#        center = np.sum(xValues*dataY)/np.sum(dataY)
#        sigma = np.abs(np.sum((xValues - center)**2*dataY/np.sum(dataY)))
#        height = np.max(dataY)
#        offset = np.min(dataY)
        
        if (parameters == None): 
            height = self.parameterWindow.gaussianHeightDoubleSpinBox.value()
            center = self.parameterWindow.gaussianCenterDoubleSpinBox.value()
            sigma =  self.parameterWindow.gaussianSigmaDoubleSpinBox.value()
            offset = self.parameterWindow.gaussianOffsetDoubleSpinBox.value()
        else:
            height = parameters[0]
            center = parameters[1]
            sigma =  parameters[2]
            offset = parameters[3]
            
        if (drawCurves == False):
              
            height, center, sigma, offset = self.fit(self.fitFuncGaussian, [height, center, sigma, offset], newYData, dataX)
            
            self.solutionsDictionary[dataset, directory, label, 'Gaussian', '[Height, Center, Sigma, Offset]', index] = [height, center, sigma, offset]
    
            yield self.cxn.data_vault.cd(directory, context = self.context)
            yield self.cxn.data_vault.open(dataset, context = self.context)
            yield self.cxn.data_vault.add_parameter_over_write('Solutions'+'-'+str(index)+'-'+'Gaussian', [height, center, sigma, offset], context = self.context)        
               
        modelX = np.linspace(dataX[0], dataX[-1], len(dataX)*4)
        modelY = self.fitFuncGaussian(modelX, [height, center, sigma, offset])
        plotData = np.vstack((modelX, modelY)).transpose()
        
        directory = list(directory)
        directory[-1] += ' - '
        directory[-1] += label
        directory[-1] += ' - '
        directory[-1] += 'Gaussian Model'
        directory = tuple(directory)
        
        self.parent.qmc.initializeDataset(dataset, directory, (label + ' Gaussian Model',))
        self.parent.qmc.setPlotData(dataset, directory, plotData)
    
    def fitFuncGaussian(self, x, p):
        """ 
            Gaussian
            p = [height, center, sigma, offset]
        
        """   
        fitFunc = p[0]*np.exp(-(((x - p[1])/p[2])**2)/2) + p[3]# gaussian
        return fitFunc

    @inlineCallbacks
    def fitLorentzian(self, dataset, directory, index, label, parameters, drawCurves):
        dataX, dataY = self.parent.qmc.plotDict[dataset, directory][index].get_data() # dependent variable
        dataX = np.array(dataX)
        xmin, xmax = self.parent.qmc.ax.get_xlim()
        selectedXValues = np.where((dataX >= xmin) & (dataX <= xmax))[0]
        dataX = dataX[(dataX >= xmin) & (dataX <= xmax)]
        newYData = np.zeros(len(dataX))
        j = 0
        for i in selectedXValues:
            newYData[j] = dataY[i]
            j += 1        
        
#        xValues = np.arange(len(dataY))
#        print len(dataY)
#        center = dataX[np.sum(xValues*dataY)/np.sum(dataY)]
#        offset = np.min(dataY)
#        gamma = 10
#        I = np.max(dataY) - np.min(dataY)
        
        if (parameters == None):
            gamma = self.parameterWindow.lorentzianGammaDoubleSpinBox.value()
            center = self.parameterWindow.lorentzianCenterDoubleSpinBox.value()
            I = self.parameterWindow.lorentzianIDoubleSpinBox.value()
            offset = self.parameterWindow.lorentzianOffsetDoubleSpinBox.value()
        else:
            gamma = parameters[0]
            center = parameters[1]
            I = parameters[2]
            offset = parameters[3]
           
        if (drawCurves == False):
        
            gamma, center, I, offset = self.fit(self.fitFuncLorentzian, [gamma, center, I, offset], newYData, dataX)
            
            self.solutionsDictionary[dataset, directory, label, 'Lorentzian', '[Gamma, Center, I, Offset]', index] = [gamma, center, I, offset] 
                   
            yield self.cxn.data_vault.cd(directory, context = self.context)
            yield self.cxn.data_vault.open(dataset, context = self.context)
            yield self.cxn.data_vault.add_parameter_over_write('Solutions'+'-'+str(index)+'-'+'Lorentzian', [gamma, center, I, offset], context = self.context)        
        
        modelX = np.linspace(dataX[0], dataX[-1], len(dataX)*4)
        modelY = self.fitFuncLorentzian(modelX, [gamma, center, I, offset])
        plotData = np.vstack((modelX, modelY)).transpose()
        
        directory = list(directory)
        directory[-1] += ' - '
        directory[-1] += label
        directory[-1] += ' - '
        directory[-1] += 'Lorentzian Model'
        directory = tuple(directory)
        
        self.parent.qmc.initializeDataset(dataset, directory, (label + ' Lorentzian Model',))
        self.parent.qmc.setPlotData(dataset, directory, plotData)
    
    def fitFuncLorentzian(self, x, p):
        """ 
            Lorentzian
            p = [gamma, center, I, offset]
        
        """   
        fitFunc = p[3] + p[2]*(p[0]**2/((x - p[1])**2 + p[0]**2))# Lorentzian
        return fitFunc

    @inlineCallbacks
    def fitLine(self, dataset, directory, index, label, parameters, drawCurves):
        dataX, dataY = self.parent.qmc.plotDict[dataset, directory][index].get_data() # dependent variable
        dataX = np.array(dataX)
        xmin, xmax = self.parent.qmc.ax.get_xlim()
        selectedXValues = np.where((dataX >= xmin) & (dataX <= xmax))[0]
        dataX = dataX[(dataX >= xmin) & (dataX <= xmax)]
        newYData = np.zeros(len(dataX))
        j = 0
        for i in selectedXValues:
            newYData[j] = dataY[i]
            j += 1        
#        slope = (np.max(dataY) - np.min(dataY))/(np.max(dataX) - np.min(dataX))
#        offset = np.min(dataY)
        
        if (parameters == None):
            slope = self.parameterWindow.lineSlopeDoubleSpinBox.value()
            offset = self.parameterWindow.lineOffsetDoubleSpinBox.value()
        else:
            slope = parameters[0]
            offset = parameters[1]

        if (drawCurves == False):
            
            slope, offset = self.fit(self.fitFuncLine, [slope, offset], newYData, dataX)
            
            self.solutionsDictionary[dataset, directory, label, 'Line', '[Slope, Offset]', index] = [slope, offset] 
            
            yield self.cxn.data_vault.cd(directory, context = self.context)
            yield self.cxn.data_vault.open(dataset, context = self.context)
            yield self.cxn.data_vault.add_parameter_over_write('Solutions'+'-'+str(index)+'-'+'Line', [slope, offset], context = self.context)        
        
        
        modelX = np.linspace(dataX[0], dataX[-1], len(dataX)*4)
        modelY = self.fitFuncLine(modelX, [slope, offset])
        plotData = np.vstack((modelX, modelY)).transpose()
        
        directory = list(directory)
        directory[-1] += ' - '
        directory[-1] += label
        directory[-1] += ' - '
        directory[-1] += 'Line Model'
        directory = tuple(directory)
        
        self.parent.qmc.initializeDataset(dataset, directory, (label + ' Line Model',))
        self.parent.qmc.setPlotData(dataset, directory, plotData)
    
    def fitFuncLine(self, x, p):
        """ 
            Line
            p = [slope, offset]
        """   
        fitFunc = p[0]*x + p[1]
        return fitFunc
    
    @inlineCallbacks
    def fitParabola(self, dataset, directory, index, label, parameters, drawCurves):
        dataX, dataY = self.parent.qmc.plotDict[dataset, directory][index].get_data() # dependent variable
        dataX = np.array(dataX)
        xmin, xmax = self.parent.qmc.ax.get_xlim()
        selectedXValues = np.where((dataX >= xmin) & (dataX <= xmax))[0]
        dataX = dataX[(dataX >= xmin) & (dataX <= xmax)]
        newYData = np.zeros(len(dataX))
        j = 0
        for i in selectedXValues:
            newYData[j] = dataY[i]
            j += 1        
#        A = 5
#        B = (np.max(dataY) - np.min(dataY))/(np.max(dataX) - np.min(dataX))
#        C = np.min(dataY)

        if (parameters == None):
            A = self.parameterWindow.parabolaADoubleSpinBox.value()
            B = self.parameterWindow.parabolaBDoubleSpinBox.value()
            C = self.parameterWindow.parabolaCDoubleSpinBox.value()
        else:
            A = parameters[0]
            B = parameters[1]
            C = parameters[2]

        if (drawCurves == False):
            
            A, B, C = self.fit(self.fitFuncParabola, [A, B, C], newYData, dataX)
            
            self.solutionsDictionary[dataset, directory, label, 'Parabola', '[A, B, C]', index] = [A, B, C] 
            
            yield self.cxn.data_vault.cd(directory, context = self.context)
            yield self.cxn.data_vault.open(dataset, context = self.context)
            yield self.cxn.data_vault.add_parameter_over_write('Solutions'+'-'+str(index)+'-'+'Parabola', [A, B, C], context = self.context)               
        
        modelX = np.linspace(dataX[0], dataX[-1], len(dataX)*4)
        modelY = self.fitFuncParabola(modelX, [A, B, C])
        plotData = np.vstack((modelX, modelY)).transpose()
        
        directory = list(directory)
        directory[-1] += ' - '
        directory[-1] += label
        directory[-1] += ' - '
        directory[-1] += 'Parabola Model'
        directory = tuple(directory)
        
        self.parent.qmc.initializeDataset(dataset, directory, (label + ' Parabola Model',))
        self.parent.qmc.setPlotData(dataset, directory, plotData)
    
    def fitFuncParabola(self, x, p):
        """ 
            Parabola
            A*x**2 + B*x + C
            p = [A, B, C]
        """   
        fitFunc = p[0]*x**2 + p[1]*x + p[2]
        return fitFunc
    
    def fit(self, function, parameters, y, x = None):  
        solutions = [None]*len(parameters)
        def f(params):
            i = 0
            for p in params:
                solutions[i] = p
                i += 1
            return (y - function(x, params))
        if x is None: x = np.arange(y.shape[0])
        optimize.leastsq(f, parameters)
        return solutions

class ParameterWindow(QtGui.QWidget):
    """Creates the fitting parameter window"""

    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.setWindowTitle('Analysis Parameters')
        self.setupUI()
    
    def setupUI(self):
        # Title Labels
        gaussianLabel = QtGui.QLabel('Gaussian:  Height*exp(-(((x - center)/Sigma)**2)/2) + Offset')
        lorentzianLabel = QtGui.QLabel('Lorentzian: Offset + I*(Gamma**2/((x - Center)**2 + Gamma**2))')
        lineLabel = QtGui.QLabel('Line: Slope*x + Offset')
        parabolaLabel = QtGui.QLabel('Parabola: A*x**2 + B*x + C ')

        # Gaussian

        gaussianHeightLabel = QtGui.QLabel('Height')
        self.gaussianHeightDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.gaussianHeightDoubleSpinBox.setDecimals(6)
        self.gaussianHeightDoubleSpinBox.setRange(-1000000000, 1000000000)
        self.gaussianHeightDoubleSpinBox.setValue(1)
        self.gaussianHeightDoubleSpinBox.setSingleStep(.1)
        self.gaussianHeightDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.gaussianHeightDoubleSpinBox.setKeyboardTracking(False)
        self.connect(self.gaussianHeightDoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)
        
        gaussianCenterLabel = QtGui.QLabel('Center')
        self.gaussianCenterDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.gaussianCenterDoubleSpinBox.setDecimals(6)
        self.gaussianCenterDoubleSpinBox.setRange(-1000000000, 1000000000)
        self.gaussianCenterDoubleSpinBox.setValue(1)
        self.gaussianCenterDoubleSpinBox.setSingleStep(.1)
        self.gaussianCenterDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.gaussianCenterDoubleSpinBox.setKeyboardTracking(False)
        self.connect(self.gaussianCenterDoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)
          
        gaussianSigmaLabel = QtGui.QLabel('Sigma')
        self.gaussianSigmaDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.gaussianSigmaDoubleSpinBox.setDecimals(6)
        self.gaussianSigmaDoubleSpinBox.setRange(-1000000000, 1000000000)
        self.gaussianSigmaDoubleSpinBox.setValue(1)
        self.gaussianSigmaDoubleSpinBox.setSingleStep(.1)
        self.gaussianSigmaDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.gaussianSigmaDoubleSpinBox.setKeyboardTracking(False)
        self.connect(self.gaussianSigmaDoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)
 
        gaussianOffsetLabel = QtGui.QLabel('Offset')
        self.gaussianOffsetDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.gaussianOffsetDoubleSpinBox.setDecimals(6)
        self.gaussianOffsetDoubleSpinBox.setRange(-1000000000, 1000000000)
        self.gaussianOffsetDoubleSpinBox.setValue(1)
        self.gaussianOffsetDoubleSpinBox.setSingleStep(.1)
        self.gaussianOffsetDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.gaussianOffsetDoubleSpinBox.setKeyboardTracking(False)
        self.connect(self.gaussianOffsetDoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)
 
        # Lorentzian

        lorentzianGammaLabel = QtGui.QLabel('Gamma')
        self.lorentzianGammaDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.lorentzianGammaDoubleSpinBox.setDecimals(6)
        self.lorentzianGammaDoubleSpinBox.setRange(-1000000000, 1000000000)
        self.lorentzianGammaDoubleSpinBox.setValue(1)
        self.lorentzianGammaDoubleSpinBox.setSingleStep(.1)
        self.lorentzianGammaDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.lorentzianGammaDoubleSpinBox.setKeyboardTracking(False)
        self.connect(self.lorentzianGammaDoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)
        
        lorentzianCenterLabel = QtGui.QLabel('Center')
        self.lorentzianCenterDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.lorentzianCenterDoubleSpinBox.setDecimals(6)
        self.lorentzianCenterDoubleSpinBox.setRange(-1000000000, 1000000000)
        self.lorentzianCenterDoubleSpinBox.setValue(1)
        self.lorentzianCenterDoubleSpinBox.setSingleStep(.1)
        self.lorentzianCenterDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.lorentzianCenterDoubleSpinBox.setKeyboardTracking(False)
        self.connect(self.lorentzianCenterDoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)
         
        lorentzianILabel = QtGui.QLabel('I')
        self.lorentzianIDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.lorentzianIDoubleSpinBox.setDecimals(6)
        self.lorentzianIDoubleSpinBox.setRange(-1000000000, 1000000000)
        self.lorentzianIDoubleSpinBox.setValue(1)
        self.lorentzianIDoubleSpinBox.setSingleStep(.1)
        self.lorentzianIDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.lorentzianIDoubleSpinBox.setKeyboardTracking(False)
        self.connect(self.lorentzianIDoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)

        lorentzianOffsetLabel = QtGui.QLabel('Offset')
        self.lorentzianOffsetDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.lorentzianOffsetDoubleSpinBox.setDecimals(6)
        self.lorentzianOffsetDoubleSpinBox.setRange(-1000000000, 1000000000)
        self.lorentzianOffsetDoubleSpinBox.setValue(1)
        self.lorentzianOffsetDoubleSpinBox.setSingleStep(.1)
        self.lorentzianOffsetDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.lorentzianOffsetDoubleSpinBox.setKeyboardTracking(False)
        self.connect(self.lorentzianOffsetDoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)

        # Line

        lineSlopeLabel = QtGui.QLabel('Slope')
        self.lineSlopeDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.lineSlopeDoubleSpinBox.setDecimals(6)
        self.lineSlopeDoubleSpinBox.setRange(-1000000000, 1000000000)
        self.lineSlopeDoubleSpinBox.setValue(1)
        self.lineSlopeDoubleSpinBox.setSingleStep(.1)
        self.lineSlopeDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.lineSlopeDoubleSpinBox.setKeyboardTracking(False)
        self.connect(self.lineSlopeDoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)
        
        lineOffsetLabel = QtGui.QLabel('Offset')
        self.lineOffsetDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.lineOffsetDoubleSpinBox.setDecimals(6)
        self.lineOffsetDoubleSpinBox.setRange(-1000000000, 1000000000)
        self.lineOffsetDoubleSpinBox.setValue(1)
        self.lineOffsetDoubleSpinBox.setSingleStep(.1)
        self.lineOffsetDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.lineOffsetDoubleSpinBox.setKeyboardTracking(False)
        self.connect(self.lineOffsetDoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)

        # Parabola

        parabolaALabel = QtGui.QLabel('A')
        self.parabolaADoubleSpinBox = QtGui.QDoubleSpinBox()
        self.parabolaADoubleSpinBox.setDecimals(6)
        self.parabolaADoubleSpinBox.setRange(-1000000000, 1000000000)
        self.parabolaADoubleSpinBox.setValue(1)
        self.parabolaADoubleSpinBox.setSingleStep(.1)
        self.parabolaADoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.parabolaADoubleSpinBox.setKeyboardTracking(False)
        self.connect(self.parabolaADoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)
        
        parabolaBLabel = QtGui.QLabel('B')
        self.parabolaBDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.parabolaBDoubleSpinBox.setDecimals(6)
        self.parabolaBDoubleSpinBox.setRange(-1000000000, 1000000000)
        self.parabolaBDoubleSpinBox.setValue(1)
        self.parabolaBDoubleSpinBox.setSingleStep(.1)
        self.parabolaBDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.parabolaBDoubleSpinBox.setKeyboardTracking(False)
        self.connect(self.parabolaBDoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)

        parabolaCLabel = QtGui.QLabel('C')
        self.parabolaCDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.parabolaCDoubleSpinBox.setDecimals(6)
        self.parabolaCDoubleSpinBox.setRange(-1000000000, 1000000000)
        self.parabolaCDoubleSpinBox.setValue(1)
        self.parabolaCDoubleSpinBox.setSingleStep(.1)
        self.parabolaCDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.parabolaCDoubleSpinBox.setKeyboardTracking(False)
        self.connect(self.parabolaCDoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)

        # Layout
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self.grid.setSpacing(5)
        
        # Gaussian
        self.grid.addWidget(gaussianLabel, 1, 0, QtCore.Qt.AlignCenter)
        self.grid.addWidget(gaussianHeightLabel, 1, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.gaussianHeightDoubleSpinBox, 1, 2, QtCore.Qt.AlignCenter)
        self.grid.addWidget(gaussianCenterLabel, 1, 3, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.gaussianCenterDoubleSpinBox, 1, 4, QtCore.Qt.AlignCenter)
        self.grid.addWidget(gaussianSigmaLabel, 1, 5, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.gaussianSigmaDoubleSpinBox, 1, 6, QtCore.Qt.AlignCenter)
        self.grid.addWidget(gaussianOffsetLabel, 1, 7, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.gaussianOffsetDoubleSpinBox, 1, 8, QtCore.Qt.AlignCenter)
 
        # Lorentzian
        self.grid.addWidget(lorentzianLabel, 3, 0, QtCore.Qt.AlignCenter)
        self.grid.addWidget(lorentzianGammaLabel, 3, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.lorentzianGammaDoubleSpinBox, 3, 2, QtCore.Qt.AlignCenter)
        self.grid.addWidget(lorentzianCenterLabel, 3, 3, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.lorentzianCenterDoubleSpinBox, 3, 4, QtCore.Qt.AlignCenter)
        self.grid.addWidget(lorentzianILabel, 3, 5, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.lorentzianIDoubleSpinBox, 3, 6, QtCore.Qt.AlignCenter)
        self.grid.addWidget(lorentzianOffsetLabel, 3, 7, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.lorentzianOffsetDoubleSpinBox, 3, 8, QtCore.Qt.AlignCenter)

        # Line
        self.grid.addWidget(lineLabel, 5, 0, QtCore.Qt.AlignCenter)
        self.grid.addWidget(lineSlopeLabel, 5, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.lineSlopeDoubleSpinBox, 5, 2, QtCore.Qt.AlignCenter)
        self.grid.addWidget(lineOffsetLabel, 5, 3, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.lineOffsetDoubleSpinBox, 5, 4, QtCore.Qt.AlignCenter)
 
        # Parabola
        self.grid.addWidget(parabolaLabel, 7, 0, QtCore.Qt.AlignCenter)
        self.grid.addWidget(parabolaALabel, 7, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.parabolaADoubleSpinBox, 7, 2, QtCore.Qt.AlignCenter)
        self.grid.addWidget(parabolaBLabel, 7, 3, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.parabolaBDoubleSpinBox, 7, 4, QtCore.Qt.AlignCenter)
        self.grid.addWidget(parabolaCLabel, 7, 5, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.parabolaCDoubleSpinBox, 7, 6, QtCore.Qt.AlignCenter)
        
        self.setFixedSize(1000, 200)


    def closeEvent(self, evt):
        self.hide()        

class SolutionsWindow(QtGui.QWidget):
    """Creates the fitting parameter window"""

    def __init__(self, parent, context, solutionsDictionary):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.context = context
        self.solutionsDictionary = solutionsDictionary
        self.labels = []
        self.textBoxes = []
        self.refitButtons = []
        self.acceptButtons = []
        self.setWindowTitle('Solutions')
        self.buttonIndexDict = {}
        self.refitButtonIndexDict = {}
        self.setupUI()
   
    def setupUI(self):
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(5)        
        
        for dataset, directory, label, curve, parameters, index in self.solutionsDictionary.keys():
            datasetLabel = QtGui.QLabel(str(dataset) + ' - ' + str(directory[-1]) + ' - ' + label)
            self.labels.append(datasetLabel)
            textBox = QtGui.QLineEdit(readOnly=True)
            textBox.setText('\'Fit\', [\'['+str(index)+']\', \''+ str(curve) + '\', ' + '\'' + str(self.solutionsDictionary[dataset, directory, label, curve, parameters, index]) + '\']')
            textBox.setMinimumWidth(550)
            self.textBoxes.append(textBox)
            refitButton = QtGui.QPushButton("Refit Curve", self)
            refitButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
            refitButton.clicked.connect(self.refitSignal)    
            self.refitButtons.append(refitButton)
            self.refitButtonIndexDict[refitButton] = [dataset, directory, index, curve, str(self.solutionsDictionary[dataset, directory, label, curve, parameters, index])]        
            acceptButton = QtGui.QPushButton("Accept", self)
            acceptButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
            acceptButton.clicked.connect(self.acceptSignal)  
            self.acceptButtons.append(acceptButton)          
            self.buttonIndexDict[acceptButton] = [directory, dataset, index]
        
        for i in range(len(self.labels)):
            self.grid.addWidget(self.labels[i], i, 0, QtCore.Qt.AlignCenter)
            self.grid.addWidget(self.textBoxes[i], i, 1, QtCore.Qt.AlignCenter)
            self.grid.addWidget(self.refitButtons[i], i, 2, QtCore.Qt.AlignCenter)
            self.grid.addWidget(self.acceptButtons[i], i, 3, QtCore.Qt.AlignCenter)

        self.setLayout(self.grid)
        self.show()
    
    @inlineCallbacks
    def acceptSignal(self, evt):
        directory, dataset, index = self.buttonIndexDict[self.sender()]
        yield self.parent.cxn.data_vault.cd(directory, context = self.context)
        yield self.parent.cxn.data_vault.open(dataset, context = self.context)
        yield self.parent.cxn.data_vault.add_parameter_over_write('Accept-' + str(index), True, context = self.context)        
        
    def refitSignal(self, evt):
        dataset, directory, index, curve, parameters = self.refitButtonIndexDict[self.sender()]
        scriptParameters = [str('['+str(index+1)+']'), str(curve), parameters]
        print scriptParameters
        self.parent.parent.fitFromScript(dataset, directory, 1, scriptParameters, True)
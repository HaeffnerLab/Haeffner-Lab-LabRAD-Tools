'''
The plot and all relevant plot options are managed by the Grapher Window.
'''

from PyQt4 import QtGui, QtCore
from canvas import Qt4MplCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from datavault import DataVaultWidget
from analysis import AnalysisWidget
import time

class GrapherWindow(QtGui.QWidget):
    """Creates the window for the new plot"""
    def __init__(self, parent, context, windowName):
#    def __init__(self, parent, context):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.context = context
        self.windowName = windowName
        self.parameterWindows = {}
        self.datasetCheckboxes = {}
        self.datasetAnalysisCheckboxes = {}
        self.datasetCheckboxCounter = 0
        self.datasetCheckboxPositionDict = {}
        self.datasetAnalysisCheckboxCounter = 0
        self.manuallyLoaded = True
        self.setWindowTitle(self.windowName)
   
        # create a vertical box layout widget
        grapherLayout = QtGui.QVBoxLayout()
        # instantiate our Matplotlib canvas widget
        self.qmc = Qt4MplCanvas(self)
        # instantiate the navigation toolbar
        ntb = NavigationToolbar(self.qmc, self)

        # Layout that involves the canvas, toolbar, graph options...etc.
        grapherLayout.addWidget(ntb)
        grapherLayout.addWidget(self.qmc)

        # Main horizontal layout
        mainLayout = QtGui.QHBoxLayout()
        # Layout that controls datasets
        datasetLayout = QtGui.QVBoxLayout() 

        mainLayout.addLayout(datasetLayout)
        mainLayout.addLayout(grapherLayout)
        
        # Layout for keeping track of datasets on a graph and analysis
        self.datasetCheckboxListWidget = DatasetCheckBoxListWidget(self)#QtGui.QListWidget()
        self.datasetCheckboxListWidget.setMaximumWidth(180)
        self.datasetCheckboxListWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        datasetLayout.addWidget(self.datasetCheckboxListWidget)
        self.analysisWidget = AnalysisWidget(self)
        datasetLayout.addWidget(self.analysisWidget)
        
        

        self.setLayout(mainLayout)

        # checkbox to change boundaries
        self.cb1 = QtGui.QCheckBox('AutoScroll', self)
        #self.cb1.move(290, 23)
        self.cb1.clicked.connect(self.autoscrollSignal) 
        # checkbox to overlay new dataset
        self.cb2 = QtGui.QCheckBox('Overlay', self)
        #self.cb2.move(500, 35)
        # checkbox to toggle AutoFit
        self.cb3 = QtGui.QCheckBox('AutoFit', self)
        #self.cb3.move(290, 39)
#        self.cb3.toggle()
        self.cb3.clicked.connect(self.autofitSignal) 
        # button to fit data on screen
        fitButton = QtGui.QPushButton("Fit", self)
        fitButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        fitButton.clicked.connect(self.fitDataSignal)
        
        windowNameButton = QtGui.QPushButton("Change Window Name", self)
        windowNameButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        windowNameButton.clicked.connect(self.changeWindowName)
        
        
        
        # Layout that controls graph options
        buttonBox = QtGui.QHBoxLayout()
        buttonBox.addWidget(self.cb1) 
        buttonBox.addWidget(self.cb3)
        buttonBox.addWidget(self.cb2)  
        buttonBox.addWidget(fitButton)
        buttonBox.addWidget(windowNameButton) 
        
        grapherLayout.addLayout(buttonBox)

    # adds a checkbox when a new dataset is overlaid on the graph
    def createDatasetCheckbox(self, dataset, directory, label, index):
        datasetCheckbox = QtGui.QCheckBox(str(dataset) + ' - ' + str(directory[-1]) + ' - ' + label, self)
#        datasetCheckbox = QtGui.QCheckBox(str(dataset) + ' - ' + label, self)
        datasetCheckbox.toggle()
        datasetCheckbox.clicked.connect(self.datasetCheckboxSignal)
        try:
            #This if statement should fail if no model exists.
            if (self.datasetCheckboxes[dataset, directory, index] != None):
                # if the checkbox does exist, then just reassign it.
                self.datasetCheckboxes[dataset, directory, index] = datasetCheckbox
                self.datasetCheckboxListWidget.setItemWidget(self.datasetCheckboxListWidget.item(self.datasetCheckboxPositionDict[dataset, directory]), datasetCheckbox)
        except:
            self.datasetCheckboxes[dataset, directory, index] = datasetCheckbox
            # The trick here is to create an item with enough text to activate the scrollbar, and then hide the text.
            # This must be done because a checkbox, even with a lot of text, does not activate the scroll bar horizontally
            item = QtGui.QListWidgetItem()
            item.setText('     ' + str(dataset) + ' - ' + str(directory[-1]) + ' - ' + label)
            item.setTextColor(QtGui.QColor(255, 255, 255))
            self.datasetCheckboxListWidget.addItem(item)
    #        self.datasetCheckboxListWidget.addItem(str(dataset) + ' ' + str(directory[-1]))
            self.datasetCheckboxListWidget.setItemWidget(self.datasetCheckboxListWidget.item(self.datasetCheckboxCounter), datasetCheckbox)
            self.datasetCheckboxPositionDict[dataset, directory, index] = self.datasetCheckboxCounter
            self.datasetCheckboxCounter = self.datasetCheckboxCounter + 1

    # adds a checkbox when a new dataset is overlaid on the graph
    def createDatasetAnalysisCheckbox(self, dataset, directory, label, index):
#        datasetAnalysisCheckbox = QtGui.QCheckBox(str(dataset) + ' ' + str(directory[-1]) + ' ' + label, self)
        datasetAnalysisCheckbox = QtGui.QCheckBox(str(dataset) + ' - ' + str(directory[-1]) + ' - ' + label, self)
        self.datasetAnalysisCheckboxes[dataset, directory, index] = datasetAnalysisCheckbox
        # The trick here is to create an item with enough text to activate the scrollbar, and then hide the text.
        # This must be done because a checkbox, even with a lot of text, does not activate the scroll bar horizontally
        item = QtGui.QListWidgetItem()
        item.setText('     ' + str(dataset) + ' - ' + str(directory[-1]) + ' - ' + label)
        item.setTextColor(QtGui.QColor(255, 255, 255))
        #self.analysisWidget.datasetCheckboxListWidget.addItem(str(dataset) + ' - ' + label)
        self.analysisWidget.datasetCheckboxListWidget.addItem(item)
        self.analysisWidget.datasetCheckboxListWidget.setItemWidget(self.analysisWidget.datasetCheckboxListWidget.item(self.datasetAnalysisCheckboxCounter), datasetAnalysisCheckbox)
        self.datasetAnalysisCheckboxCounter = self.datasetAnalysisCheckboxCounter + 1

    def fitFromScript(self, dataset, directory, numberDependentVariables, scriptParameters, fitOverride = None):
        datasetsToFit = eval(scriptParameters[0])
        curveToFit = scriptParameters[1]
        curveParameters = eval(scriptParameters[2])
        
        # if no selection of datasets, fit all of them
        if (len(datasetsToFit) == 0):
            datasetsToFit = range(numberDependentVariables)
        else:
            # naming convention. Dataset 1, for purposes is this program, has an index of 0, not 1. Ex: datasetsToFit = [1, 2, 3] -> [0, 1, 2] 
            for i in range(len(datasetsToFit)):
                datasetsToFit[i] = datasetsToFit[i] - 1
        
        # cycle through all the dataset checkboxes and uncheck them.
        for checkBoxDataset, checkBoxDirectory, checkBoxIndex in self.datasetAnalysisCheckboxes.keys():
            if self.datasetAnalysisCheckboxes[checkBoxDataset, checkBoxDirectory, checkBoxIndex].isChecked():
                 self.datasetAnalysisCheckboxes[checkBoxDataset, checkBoxDirectory, checkBoxIndex].toggle()
        
        # toggle the datasets we care about
        for datasetToFit in datasetsToFit:
            for checkBoxDataset, checkBoxDirectory, checkBoxIndex in self.datasetAnalysisCheckboxes.keys():
                if (dataset == checkBoxDataset and directory == checkBoxDirectory and datasetToFit == checkBoxIndex):
                    self.datasetAnalysisCheckboxes[dataset, directory, datasetToFit].toggle()
                    
        # cycle through the curves checkboxes and uncheck them.
        for curve in self.analysisWidget.analysisCheckboxes.keys():
            if self.analysisWidget.analysisCheckboxes[curve].isChecked():
                self.analysisWidget.analysisCheckboxes[curve].toggle()
        
        # toggle the curve we care about
        for curve in self.analysisWidget.analysisCheckboxes.keys():
            if (curve == curveToFit):
                self.analysisWidget.analysisCheckboxes[curveToFit].toggle()

        # everything is now set up to fit, so call fitCurves and pass in the parameters
        if (fitOverride == None): 
            self.qmc.fitData()        
        self.analysisWidget.fitCurves(curveParameters)

    def datasetCheckboxSignal(self):
        self.qmc.drawLegend()
        self.qmc.draw()

    # when the autoFit button is checked, it will uncheck the autoscroll button
    def autofitSignal(self):
        if (self.cb1.isChecked()):
            self.cb1.toggle()
    
    # when the autoscroll button is checked, it will uncheck the autoFit button        
    def autoscrollSignal(self):
        if (self.cb3.isChecked()):
            self.cb3.toggle()

    # instructs the graph to update the boundaries to fit all the data
    def fitDataSignal(self):
        if (self.cb1.isChecked()): # makes sure autoscroll is off otherwise it will undo this operation
            self.cb1.toggle()
        elif (self.cb3.isChecked()): # makes sure autoFit is off otherwise it will undo this operation
            self.cb3.toggle()
        self.qmc.fitData()
    
    def changeWindowName(self):
        text, ok = QtGui.QInputDialog.getText(self, 'Change Window Name', 'Enter a name:')        
        if ok:
            text = str(text)
            self.parent.changeWindowName(self.windowName, text)
            self.setWindowTitle(text)
            self.windowName = text
    
    def newParameterWindow(self, dataset, directory):
        win = ParameterWindow(self, dataset, directory)
        win.show()
        self.parameterWindows[dataset, directory] = win

    def getParameters(self, dataset, directory):
        parameters = self.parent.getParameters(dataset, directory)
        return parameters                   
     
    def fileQuit(self):
        self.close()
        
    def closeEvent(self, event):
        self.qmc.endTimer()
        if (self.cb2.isChecked()):
            # "uncheck" the overlay checkbox
            self.cb2.toggle()
        # Remove this window from the dictionary so that no datasets...
        # ... are drawn to this window
        self.parent.removeWindowFromDictionary(self)
        self.parent.removeWindowFromWinDict(self.windowName)
#        self.parent.removeWindowFromWinList(self)
        self.parent.cleanUp()
        self.fileQuit()


class FirstWindow(QtGui.QWidget):
    """Creates the opening window"""
    def __init__(self, parent, context, reactor):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.context = context
        self.reactor = reactor
        self.parameterWindows = {}
        self.manuallyLoaded = True
        self.setWindowTitle("Live Grapher!")
        hbl = QtGui.QHBoxLayout()
        self.setLayout(hbl)
        self.datavaultwidget = DataVaultWidget(self, context)
        self.datavaultwidget.populateList()
        #self.datavaultwidget.show()
        hbl.addWidget(self.datavaultwidget)
        
    def newParameterWindow(self, dataset, directory):
        win = ParameterWindow(self, dataset, directory)
        win.show()
        self.parameterWindows[dataset, directory] = win

    def getParameters(self, dataset, directory):
        parameters = self.parent.getParameters(dataset, directory)
        return parameters
    
    def closeEvent(self, event):
        self.reactor.stop()                   


class ParameterWindow(QtGui.QWidget):
    """Creates the dataset-specific parameter window"""

    def __init__(self, parent, dataset, directory):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.dataset = dataset
        self.directory = directory
        self.setWindowTitle(str(dataset) + " " + str(directory))
        mainLayout = QtGui.QVBoxLayout() 
        self.parameterListWidget = QtGui.QListWidget()
        mainLayout.addWidget(self.parameterListWidget)
        self.populateList()
        self.startTimer(30000)
        self.setLayout(mainLayout)

    
    def timerEvent(self, evt):
        self.populateList()
        tstartupdate = time.clock()
    
    def populateList(self):
        self.parameters = self.parent.getParameters(self.dataset, self.directory)
        self.parameterListWidget.clear()
        if (self.parameters):
            for i in self.parameters:
                self.parameterListWidget.addItem(str(i))

class DatasetCheckBoxListWidget(QtGui.QListWidget):
    def __init__(self, parent):
        QtGui.QListWidget.__init__(self)
        self.parent = parent
        
    def mousePressEvent(self, event):
        """
        mouse clicks events
        """
        button = event.button()
        item = self.itemAt(event.x(), event.y())
        if item:
            item.setSelected(True)
    
    
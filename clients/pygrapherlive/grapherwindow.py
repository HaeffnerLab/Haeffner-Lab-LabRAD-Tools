'''
The plot and all relevant plot options are managed by the Grapher Window.
'''

from PyQt4 import QtGui, QtCore
from canvas import Qt4MplCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from datavault import DataVaultWidget
from analysis import AnalysisWidget
from analysiswindow import AnalysisWindow
import time
from twisted.internet.defer import inlineCallbacks, returnValue

# added 8/13/14 by William for publish option
import pylab
import os
import pyperclip


class GrapherWindow(QtGui.QWidget):
    """Creates the window for the new plot"""
    def __init__(self, parent, context, windowName):
#    def __init__(self, parent, context):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.context = context
        self.windowName = windowName
        self.parameterWindows = {}
        self.publishWindows = {} # new
        self.datasetCheckboxes = {}
        self.datasetCheckboxesItems = {}
        self.datasetAnalysisCheckboxes = {}
        self.datasetCheckboxCounter = 0
        self.datasetCheckboxPositionDict = {} # [dataset, directory, index], integer
        self.itemDatasetCheckboxPositionDict = {} # item: integer
        self.toggleDict = {} # dataset, directory, index: 0 off, 1 on
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
        
               
#        self.analysisWidget = AnalysisWidget(self)
#        datasetLayout.addWidget(self.analysisWidget)
        
        

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
                self.datasetCheckboxListWidget.setItemWidget(self.datasetCheckboxListWidget.item(self.datasetCheckboxPositionDict[dataset, directory, index]), datasetCheckbox)
        except:
            self.datasetCheckboxes[dataset, directory, index] = datasetCheckbox
            # The trick here is to create an item with enough text to activate the scrollbar, and then hide the text.
            # This must be done because a checkbox, even with a lot of text, does not activate the scroll bar horizontally
            item = QtGui.QListWidgetItem()
            self.datasetCheckboxesItems[item] = [dataset, directory, index]
            item.setText('        ' + str(dataset) + ' - ' + str(directory[-1]) + ' - ' + label)
            item.setTextColor(QtGui.QColor(255, 255, 255))
            self.datasetCheckboxListWidget.addItem(item)
            self.itemDatasetCheckboxPositionDict[item] = self.datasetCheckboxCounter
            self.datasetCheckboxListWidget.setItemWidget(self.datasetCheckboxListWidget.item(self.datasetCheckboxCounter), datasetCheckbox)
            self.datasetCheckboxPositionDict[dataset, directory, index] = self.datasetCheckboxCounter
            self.datasetCheckboxCounter = self.datasetCheckboxCounter + 1
            self.toggleDict[dataset, directory, index] = 1

#    # adds a checkbox when a new dataset is overlaid on the graph
#    def createDatasetAnalysisCheckbox(self, dataset, directory, label, index):
##        datasetAnalysisCheckbox = QtGui.QCheckBox(str(dataset) + ' ' + str(directory[-1]) + ' ' + label, self)
#        datasetAnalysisCheckbox = QtGui.QCheckBox(str(dataset) + ' - ' + str(directory[-1]) + ' - ' + label, self)
#        self.datasetAnalysisCheckboxes[dataset, directory, index] = datasetAnalysisCheckbox
#        # The trick here is to create an item with enough text to activate the scrollbar, and then hide the text.
#        # This must be done because a checkbox, even with a lot of text, does not activate the scroll bar horizontally
#        item = QtGui.QListWidgetItem()
#        item.setText('     ' + str(dataset) + ' - ' + str(directory[-1]) + ' - ' + label)
#        item.setTextColor(QtGui.QColor(255, 255, 255))
#        #self.analysisWidget.datasetCheckboxListWidget.addItem(str(dataset) + ' - ' + label)
#        self.analysisWidget.datasetCheckboxListWidget.addItem(item)
#        self.analysisWidget.datasetCheckboxListWidget.setItemWidget(self.analysisWidget.datasetCheckboxListWidget.item(self.datasetAnalysisCheckboxCounter), datasetAnalysisCheckbox)
#        self.datasetAnalysisCheckboxCounter = self.datasetAnalysisCheckboxCounter + 1

    def fitFromScript(self, dataset, directory, numberDependentVariables, scriptParameters, fitOverride = None):
        index = int(scriptParameters[0]) # index
        curveName = scriptParameters[1] # curveName
        parameters = eval(scriptParameters[2]) #parameters
        
#        # if no selection of datasets, fit all of them
#        if (len(datasetsToFit) == 0):
#            datasetsToFit = range(numberDependentVariables)
#        else:
#            # naming convention. Dataset 1, for purposes is this program, has an index of 0, not 1. Ex: datasetsToFit = [1, 2, 3] -> [0, 1, 2] 
#            for i in range(len(datasetsToFit)):
#                datasetsToFit[i] = datasetsToFit[i] - 1
        

        # everything is now set up to fit, so call fitCurves and pass in the parameters
#        if (fitOverride == None): 
#            self.qmc.fitData()        
        
        # need to open the correct analysis window and call fitcurves
        self.datasetCheckboxListWidget.fitFromScript(dataset, directory, index, curveName, parameters)       

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
    
    def newPublishWindow(self, dataset, directory):
        win = PublishWindow(self, dataset, directory)
        win.show()
        self.publishWindows[dataset, directory] = win

    @inlineCallbacks
    def getParameters(self, dataset, directory):
        parameters = yield self.parent.getParameters(dataset, directory)
        returnValue( parameters )                   
     
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
        for window in self.datasetCheckboxListWidget.analysisWindows.keys():
            try:
                self.datasetCheckboxListWidget.analysisWindows[window].close()
            except:
                pass
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
        self.setLayout(mainLayout)
    
    @inlineCallbacks
    def populateList(self):
        parameters = yield self.parent.getParameters(self.dataset, self.directory)
        self.parameterListWidget.clear()
        self.parameterListWidget.addItems([str(x) for x in sorted(parameters)])
        
class PublishWindow(QtGui.QWidget):
    """Creates the dataset-specific parameter window - with checkboxes.
    Then it lets you submit the selected data to the clipboard."""
    def __init__(self, parent, dataset, directory):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.dataset = dataset
        self.directory = directory
        self.setWindowTitle('Select parameters to copy')
        self.paramStrList = []
        self.all = '' # will become a string of all parameters in selectAll
        self.resize(200, 250) # arbitrary
        self.scrollbar()
        #self.populate()
        
    def addParam(self, state):
        sender =  self.sender()
        if state == QtCore.Qt.Checked:
            self.paramStrList.append(sender.text())
        else:
            count = 0
            for elem in self.paramStrList:
                if elem == sender.text():
                        self.paramStrList.pop(count)
                        count += 1
    
    def clipboard(self):
        string = ''
        for elem in self.paramStrList:
            string += elem+', '
        pyperclip.copy(string)
        self.close()
        self.webblog()
    
    def selectAll(self):
        pyperclip.copy(self.all)
        self.close()
        self.webblog()
    
    def webblog(self):
        #os.system(r"C:\Users\Admin\Documents\GitHub\Haeffner-Lab-LabRAD-Tools\Zoundry Raven\Zoundry Raven.exe")
        if os.name == 'nt':
            os.system(r'"C:\Program Files\BlogDesk\BlogDesk.exe"')
        elif os.name == 'something else':
            os.system(r'"path to the appropriate webblog client"')
        else: 
            print 'The webblog client options are currently unavailable for your operating system.'

    @inlineCallbacks
    def scrollbar(self):
        l=QtGui.QVBoxLayout(self)
        parameters = yield self.parent.getParameters(self.dataset, self.directory) # this must be done here
        s=QtGui.QScrollArea()
        l.addWidget(s)
 
        w=QtGui.QWidget(self)        
        vbox=QtGui.QVBoxLayout(w)
        
        allb = QtGui.QPushButton('Submit All') 
        allb.clicked.connect(self.selectAll)
        vbox.addWidget(allb)
         
        subb = QtGui.QPushButton('Submit Selected')
        subb.clicked.connect(self.clipboard)
        vbox.addWidget(subb)
        
        title = str(self.dataset)+'_'+str(self.directory)+', ' # include the title by default
        self.all += title
        
        tOpt = QtGui.QCheckBox(title)
        tOpt.stateChanged.connect(self.addParam)
        vbox.addWidget(tOpt)
        
        for x in sorted(parameters):
            _l=QtGui.QHBoxLayout()
            pw = QtGui.QCheckBox(str(x))
            _l.addWidget(pw)
            pw.stateChanged.connect(self.addParam)
            self.all += str(x)+', '
            vbox.addLayout(_l)

        s.setWidget(w)

    @inlineCallbacks
    def populate(self): # not presently in use
   
        mainLayout = QtGui.QVBoxLayout()

        allb = QtGui.QPushButton('Submit All') 
        allb.clicked.connect(self.selectAll)
        mainLayout.addWidget(allb)
         
        subb = QtGui.QPushButton('Submit Selected')
        subb.clicked.connect(self.clipboard)
        mainLayout.addWidget(subb)
         
        parameters = yield self.parent.getParameters(self.dataset, self.directory)
        print sorted(parameters)
        for x in sorted(parameters):
            parameterWidget = QtGui.QCheckBox(str(x)) 
            #parameterWidget.toggle() # in case you want all selected by default
            parameterWidget.stateChanged.connect(self.addParam)
            mainLayout.addWidget(parameterWidget)
            self.all += str(x)+', '
        self.setLayout(mainLayout)
        

class DatasetCheckBoxListWidget(QtGui.QListWidget):
    def __init__(self, parent):
        QtGui.QListWidget.__init__(self)
        self.parent = parent
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.popup)
        self.savedAnalysisParameters = {}        
        self.analysisWindows = {}  

    def mousePressEvent(self, event):
        """
        mouse clicks events
        """
        button = event.button()       
        item = self.itemAt(event.x(), event.y())
        if item:
            item.setSelected(True)

    def popup(self, pos):
        menu = QtGui.QMenu()
#        fitAction = menu.addAction("Fit")
#        removeAction = menu.addAction("Remove")
        item = self.itemAt(pos)
        if (item == None):
            pass # no item
        elif (item.text()[-5:] == 'Model'):
            removeAction = menu.addAction("Remove") # we're not going to fit to a model
            action = menu.exec_(self.mapToGlobal(pos))
            toggleAction = menu.addAction("Toggle Points")
            if action == removeAction:
                self.removeItem(item, pos)
            elif action == toggleAction:
                self.togglePoints(pos)

        else:
            publishAction = menu.addAction("Publish") # displayed at top of list
            fitAction = menu.addAction("Fit")
            removeAction = menu.addAction("Remove")
            toggleAction = menu.addAction("Toggle Points")
            parametersAction = menu.addAction("Parameters")
            action = menu.exec_(self.mapToGlobal(pos))
            if action == fitAction:
                # item = self.item(self.count() - 1)  
                dataset, directory,index = self.parent.datasetCheckboxesItems[item]              
                try:
                    test = self.analysisWindows[dataset, directory, index]
                except: # prevent the same window from reopening!
                    self.analysisWindows[dataset, directory,index] = AnalysisWindow(self, self.parent.datasetCheckboxesItems[item])
            elif action == removeAction:
                self.removeItem(item, pos)
            elif action == toggleAction:
                self.togglePoints(pos)
            elif action == parametersAction:
                dataset, directory,index = self.parent.datasetCheckboxesItems[item]
                self.parent.newParameterWindow(dataset, directory)

            elif action == publishAction:
                dataset, directory,index = self.parent.datasetCheckboxesItems[item] 
                dataX,dataY = self.parent.qmc.plotDict[dataset, directory][index].get_data()
                fig = pylab.figure()
                pylab.plot(dataX,dataY)
                #fig.savefig(str(dataset)+str(directory)+'.png') # names picture specifically, unlike following line
                fig.savefig('publication.png') # save figure as default name to avoid confusion
                publishWindow = self.parent.newPublishWindow(dataset, directory) # create a publish window

    def removeItem(self, item, pos):
        itemNumberToRemove = self.parent.itemDatasetCheckboxPositionDict[self.itemAt(pos)]
        # now clean up the mess you made
        for item in self.parent.itemDatasetCheckboxPositionDict.keys():
            if (self.parent.itemDatasetCheckboxPositionDict[item] == itemNumberToRemove):
                self.parent.itemDatasetCheckboxPositionDict.pop(item)
            elif (self.parent.itemDatasetCheckboxPositionDict[item] > itemNumberToRemove):
                self.parent.itemDatasetCheckboxPositionDict[item] -= 1

        for dataset, directory, index in self.parent.datasetCheckboxPositionDict.keys():
            if (self.parent.datasetCheckboxPositionDict[dataset, directory, index] == itemNumberToRemove):
                self.parent.datasetCheckboxPositionDict.pop((dataset, directory, index))
                self.parent.datasetCheckboxes.pop((dataset, directory, index))
            elif (self.parent.datasetCheckboxPositionDict[dataset, directory, index] > itemNumberToRemove):
                self.parent.datasetCheckboxPositionDict[dataset, directory, index] -= 1
                
        self.takeItem(itemNumberToRemove) 
        self.parent.datasetCheckboxCounter -= 1
        self.parent.qmc.drawLegend()
        self.parent.qmc.draw()

    def togglePoints(self, pos):
        dataset, directory, index = self.parent.datasetCheckboxesItems[self.itemAt(pos)]
        if self.parent.toggleDict[dataset, directory, index] == 1:
            self.parent.qmc.toggleLine(dataset, directory, index)
            self.parent.toggleDict[dataset, directory, index] = 0
        elif self.parent.toggleDict[dataset, directory, index] == 0:
            self.parent.qmc.togglePoints(dataset, directory, index)
            self.parent.toggleDict[dataset, directory, index] = 1         
        
    def fitFromScript(self, dataset, directory, index, curveName, parameters):
        try:
            test = self.analysisWindows[dataset, directory, index]
        except: # prevent the same window from reopening!
            self.analysisWindows[dataset, directory, index] = AnalysisWindow(self, [dataset, directory, index])
            self.analysisWindows[dataset, directory, index].combo.setCurrentIndex(self.analysisWindows[dataset, directory, index].curveComboIndexDict[curveName])
            self.analysisWindows[dataset, directory, index].onActivated()
            self.analysisWindows[dataset, directory, index].fitCurves(parameters)
        

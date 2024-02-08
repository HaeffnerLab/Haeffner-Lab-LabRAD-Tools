'''
The plot and all relevant plot options are managed by the Grapher Window.
'''

from PyQt4 import QtGui, QtCore
from .canvas import Qt4MplCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from .datavault import DataVaultWidget
from .analysis import AnalysisWidget
from .analysiswindow import AnalysisWindow
import time
from twisted.internet.defer import inlineCallbacks, returnValue

# added 8/13/14 by William for publish option
import pylab
#import pyperperclip
import xmlrpc.client 
from . import publish_parameters as pp
import os
try: 
    import paramiko
except:
    print("paramiko not installed")
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

        self.cb4 = QtGui.QCheckBox('Probability mode', self)

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
        buttonBox.addWidget(self.cb4)
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
        for window in list(self.datasetCheckboxListWidget.analysisWindows.keys()):
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
        self.title = str(self.dataset)+str(self.directory)
        self.content = '' # will become the final string sent to the blog body
        self.imagePath = r'<img alt="title" src="http://research.physics.berkeley.edu/haeffner/wp-blog/wp-content/uploads/2014/07/'+ self.title +'.png"/>'
        self.paramStrList = []
        self.all = '' # will become a string of all parameters in selectAll
        self.resize(210, 250) # arbitrary
        self.buildLayout()
        
    def addDialog(self):
        text, ok = QtGui.QInputDialog.getText(self, 'Input Dialog','Enter your comment:')
        # note that text is not a true string yet
        if ok:
            self.content = str(text)+' ~ '
     
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
            string += str(elem)+', '
        string += self.imagePath
        self.content += string
        pyperclip.copy(string)
        self.close()
        self.webblog()
    
    def selectAll(self):
        self.all += self.imagePath
        self.content = self.content+self.all
        pyperclip.copy(self.all)
        self.close()
        self.webblog()
    
    def webblog(self):
        # this section must be set to fit the computer during installation? needs path and default tags
        wp_url = pp.wp_url
        wp_username = pp.wp_username
        wp_password = pp.wp_password
        wp_blogid = "1"
        status_draft = 0
        status_published = 1 
        server = xmlrpc.client.ServerProxy(wp_url) 
        title = self.title
        content = self.content
        # later add in an option for the user to add comments and tags
        categories = pp.categories
        tags = pp.tags
        data = {'title': title, 'description': content,'categories': categories, 'mt_keywords': tags} 
        post_id = server.metaWeblog.newPost(wp_blogid, wp_username, wp_password, data, status_published)
        print('Content published successfully.')

    @inlineCallbacks
    def buildLayout(self):
        # create general layout
        l=QtGui.QVBoxLayout(self)
        parameters = yield self.parent.getParameters(self.dataset, self.directory) # this must be done here
        s=QtGui.QScrollArea()
        l.addWidget(s)
 
        # add secondary layout for scrolling capabilities
        w=QtGui.QWidget(self)        
        vbox=QtGui.QVBoxLayout(w)
        
        # button to add a comment, repetition replaces
        dialog = QtGui.QPushButton('Add Comment', self)
        dialog.clicked.connect(self.addDialog)  
        vbox.addWidget(dialog)
        
        # button to select all parameters
        allb = QtGui.QPushButton('Submit All') 
        allb.clicked.connect(self.selectAll)
        vbox.addWidget(allb)
         
        # button to only submit the selected parameters only
        subb = QtGui.QPushButton('Submit Selected')
        subb.clicked.connect(self.clipboard)
        vbox.addWidget(subb)
        self.all += self.title + ': '

        # options to add each individual parameter
        for x in sorted(parameters):
            _l=QtGui.QHBoxLayout()
            pw = QtGui.QCheckBox(str(x))
            _l.addWidget(pw)
            pw.stateChanged.connect(self.addParam)
            self.all += str(x)+', '
            vbox.addLayout(_l)
            
        # set the layout as a widget
        s.setWidget(w)
    
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
                
                title = str(dataset)+str(directory)
                imageLoc = pp.imagePath+title+'.png'
                fig.savefig(imageLoc) # save figure as default name to avoid confusion

                privatekeyfile = os.path.expanduser(pp.pw)
                mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
                username = pp.un
                transport = paramiko.Transport((pp.host, 22))
                transport.connect(username = username, pkey = mykey)
                sftp = paramiko.SFTPClient.from_transport(transport)
                sftp.chdir(pp.blogPath)
                sftp.put(imageLoc,title+'.png')
                sftp.close()
                transport.close()
                
                publishWindow = self.parent.newPublishWindow(dataset, directory) # create a publish window

    def removeItem(self, item, pos):
        itemNumberToRemove = self.parent.itemDatasetCheckboxPositionDict[self.itemAt(pos)]
        # now clean up the mess you made
        for item in list(self.parent.itemDatasetCheckboxPositionDict.keys()):
            if (self.parent.itemDatasetCheckboxPositionDict[item] == itemNumberToRemove):
                self.parent.itemDatasetCheckboxPositionDict.pop(item)
            elif (self.parent.itemDatasetCheckboxPositionDict[item] > itemNumberToRemove):
                self.parent.itemDatasetCheckboxPositionDict[item] -= 1

        for dataset, directory, index in list(self.parent.datasetCheckboxPositionDict.keys()):
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
        

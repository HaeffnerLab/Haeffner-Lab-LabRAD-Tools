from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks

class StatusWidget(QtGui.QWidget):
    def __init__(self, parent, experimentPath, context):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.context = context
        self.experimentPath = experimentPath
        
        self.mainLayout = QtGui.QVBoxLayout()
        
        self.controlLayout = QtGui.QHBoxLayout()
        
        self.createStatusLabel(experimentPath)
        
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.mainLayout.addLayout(self.controlLayout)
        self.setLayout(self.mainLayout)
    
    @inlineCallbacks
    def createStatusLabel(self, experimentPath):
        self.experimentPath = experimentPath
        
        if (tuple(self.experimentPath) in self.parent.experiments.keys()):
            
            status = yield self.parent.server.get_parameter(self.experimentPath + ['Semaphore', 'Status'])
            
            self.startButton = QtGui.QPushButton("New", self)
            self.startButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
            self.startButton.clicked.connect(self.startButtonSignal)
            self.controlLayout.addWidget(self.startButton)
                    
            self.pauseContinueButton = QtGui.QPushButton("Pause", self)
            self.pauseContinueButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
            self.pauseContinueButton.clicked.connect(self.pauseContinueButtonSignal)
            self.controlLayout.addWidget(self.pauseContinueButton)
            
            self.stopButton = QtGui.QPushButton("Stop", self)
            self.stopButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
            self.stopButton.clicked.connect(self.stopButtonSignal)
            self.controlLayout.addWidget(self.stopButton)
            
            self.statusLabel = QtGui.QLabel(status)
            self.statusLabel.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
            self.mainLayout.addWidget(self.statusLabel)
            if (self.statusLabel.text() == 'Paused'):
                self.startButton.setDisabled(True)
                self.pauseContinueButton.setEnabled(True)
                self.stopButton.setEnabled(True)
                self.pauseContinueButton.setText('Continue')
            elif (self.statusLabel.text() == 'Running'):            
                self.startButton.setDisabled(True)
                self.stopButton.setEnabled(True)
                self.pauseContinueButton.setEnabled(True)
                self.pauseContinueButton.setText('Pause')
            elif(self.statusLabel.text() == 'Pausing'):
                self.startButton.setDisabled(True)
                self.pauseContinueButton.setEnabled(True)
                self.stopButton.setEnabled(True)
                self.pauseContinueButton.setText('Continue')              
            elif (status == 'Stopping'):
                self.startButton.setDisabled(True)                
                self.pauseContinueButton.setDisabled(True)    
                self.stopButton.setDisabled(True)
            else:
                self.pauseContinueButton.setDisabled(True)    
                self.stopButton.setDisabled(True)
                self.startButton.setEnabled(True)

            self.pbar = QtGui.QProgressBar()
            self.pbar.setValue(self.parent.experimentProgressDict[tuple(self.experimentPath)])
            self.mainLayout.addWidget(self.pbar)   
            
            self.experimentLabel = QtGui.QLabel(self.experimentPath[-1])
            self.experimentLabel.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
            self.mainLayout.addWidget(self.experimentLabel)
            
            self.setupStatusListener()               

        else:
            self.statusLabel = QtGui.QLabel('No Script Loaded For This Experiment')
            self.mainLayout.addWidget(self.statusLabel)
        
        self.mainLayout.setAlignment(self.statusLabel, QtCore.Qt.AlignCenter)
        self.mainLayout.setAlignment(self.experimentLabel, QtCore.Qt.AlignCenter)
        
        self.createStatusLabel = self.refreshStatus

    @inlineCallbacks
    def refreshStatus(self, experimentPath):
        self.experimentPath = experimentPath
        self.experimentLabel.setText(self.experimentPath[-1])
        
        if (tuple(self.experimentPath) in self.parent.experiments.keys()):
            
            status = yield self.parent.server.get_parameter(self.experimentPath + ['Semaphore', 'Status'])
            
            self.statusLabel.setText(status)

            if (self.statusLabel.text() == 'Paused'):
                self.startButton.setDisabled(True)
                self.pauseContinueButton.setEnabled(True)
                self.stopButton.setEnabled(True)
                self.pauseContinueButton.setText('Continue')
            elif (self.statusLabel.text() == 'Running'):            
                self.startButton.setDisabled(True)
                self.stopButton.setEnabled(True)
                self.pauseContinueButton.setEnabled(True)
                self.pauseContinueButton.setText('Pause')
            elif(self.statusLabel.text() == 'Pausing'):
                self.startButton.setDisabled(True)
                self.pauseContinueButton.setEnabled(True)
                self.stopButton.setEnabled(True)
                self.pauseContinueButton.setText('Continue')              
            elif (status == 'Stopping'):
                self.startButton.setDisabled(True)                
                self.pauseContinueButton.setDisabled(True)    
                self.stopButton.setDisabled(True)
            else:
                self.pauseContinueButton.setDisabled(True)    
                self.stopButton.setDisabled(True)
                self.startButton.setEnabled(True)   

            self.pbar.setValue(self.parent.experimentProgressDict[tuple(self.experimentPath)])
                     

                            
    @inlineCallbacks
    def setupStatusListener(self):
        yield self.parent.server.signal__parameter_change(11111, context = self.context)
        yield self.parent.server.addListener(listener = self.updateStatus, source = None, ID = 11111, context = self.context)

    @inlineCallbacks
    def refreshStatusListener(self):
        yield self.parent.server.signal__parameter_change(11111, context = self.context)

    @inlineCallbacks
    def updateStatus(self, target, message):
        name, value = message
#        print name,value
#        print name[:-2]
        if (name[:-2] == self.experimentPath):
            #current experiment
            if (name[-1] == 'Status'):
                parameter = yield self.parent.server.get_parameter(self.experimentPath + ['Semaphore', 'Status'] , context = self.context)
                if (parameter == 'Finished' or parameter == 'Stopped'):
                    self.statusLabel.setText(value)
                    self.stopButton.setDisabled(True)
                    self.startButton.setEnabled(True)    
                    self.pauseContinueButton.setDisabled(True)
                    self.pauseContinueButton.setText('Pause')
                    yield self.parent.server.set_parameter(self.experimentPath + ['Semaphore', 'Continue'], True, context = self.context)
                    self.parent.activeExperimentListWidget.removeExperiment(self.experimentPath)
                elif (parameter == 'Paused'):
                    self.statusLabel.setText(parameter)
            elif (name[-1] == 'Progress'):
                self.parent.experimentProgressDict[tuple(self.experimentPath)] = value
                self.pbar.setValue(value)
        else:
            # Because global parameters don't have semaphore! duh!
            if (tuple(name[:-2]) in self.parent.experiments.keys()):
                parameter = yield self.parent.server.get_parameter(name[:-2] + ['Semaphore', 'Status'] , context = self.context)
                if (parameter == 'Finished' or parameter == 'Stopped'):
                    self.parent.activeExperimentListWidget.removeExperiment(name[:-2])
                elif (parameter == 'Progress'):
                    self.parent.experimentProgressDict[tuple(self.experimentPath)] = value
        yield None
    
    @inlineCallbacks
    def startButtonSignal(self, evt):
        self.startButton.setDisabled(True)
        self.stopButton.setEnabled(True)  
        self.pauseContinueButton.setEnabled(True)      
        yield self.parent.server.set_parameter(self.experimentPath + ['Semaphore', 'Continue'], True, context = self.context)
        yield self.parent.server.set_parameter(self.experimentPath + ['Semaphore', 'Block'], False, context = self.context)
        yield self.parent.server.set_parameter(self.experimentPath + ['Semaphore', 'Status'], 'Running', context = self.context)
        self.statusLabel.setText('Running')
        self.parent.startExperiment(tuple(self.experimentPath))
        self.parent.activeExperimentListWidget.addExperiment(self.experimentPath)
        
    @inlineCallbacks
    def pauseContinueButtonSignal(self, evt):
        status = yield self.parent.server.get_parameter(self.experimentPath + ['Semaphore', 'Status'])
        if (status == 'Running'):
            yield self.parent.server.set_parameter(self.experimentPath + ['Semaphore', 'Status'], 'Pausing', context = self.context)
#            yield self.parent.server.set_parameter(self.experimentPath + ['Semaphore', 'Block'], True, context = self.context)
            self.pauseContinueButton.setText('Continue')
            self.statusLabel.setText('Pausing')
        elif (status == 'Paused' or status == 'Pausing'):
            yield self.parent.server.set_parameter(self.experimentPath + ['Semaphore', 'Block'], False, context = self.context)
            yield self.parent.server.set_parameter(self.experimentPath + ['Semaphore', 'Status'], 'Running', context = self.context)
            self.pauseContinueButton.setText('Pause')
            self.statusLabel.setText('Running')

    @inlineCallbacks
    def stopButtonSignal(self, evt):
        self.stopButton.setDisabled(True)
        self.startButton.setDisabled(True)    
        self.pauseContinueButton.setDisabled(True)    
        status = yield self.parent.server.get_parameter(self.experimentPath + ['Semaphore', 'Status'])
        if (status == 'Paused' or status == 'Pausing'):
            yield self.parent.server.set_parameter(self.experimentPath + ['Semaphore', 'Block'], False, context = self.context)
        yield self.parent.server.set_parameter(self.experimentPath + ['Semaphore', 'Continue'], False, context = self.context)
        yield self.parent.server.set_parameter(self.experimentPath + ['Semaphore', 'Status'], 'Stopping', context = self.context)
        self.pauseContinueButton.setText('Pause')
        self.statusLabel.setText('Stopping')  
    
    def handleScriptError(self, e=None):
        self.stopButton.setDisabled(True)
        self.startButton.setEnabled(True)    
        self.pauseContinueButton.setDisabled(True)    
        self.pauseContinueButton.setText('Pause')
        self.statusLabel.setText('Error')
        if (e != None):
            print 'Error in script: ', self.experimentPath[-1], ' - ', e
        self.parent.activeExperimentListWidget.removeExperiment(self.experimentPath)
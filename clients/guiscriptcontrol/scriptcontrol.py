from twisted.internet.defer import inlineCallbacks, DeferredList
from twisted.internet.threads import deferToThread
from PyQt4 import QtGui, QtCore
import re
from experimentlist import ExperimentListWidget
from status import StatusWidget
from activeexperimentslist import ActiveExperimentsListWidget
from parameterswidget import ParametersWidget
from scheduler import Scheduler
from queuedexperimentslist import QueuedExperimentsListWidget
from configuration import config as c
import sys
import reloader


class ScriptControl(QtGui.QWidget):
    def __init__(self, reactor, parent):
        QtGui.QWidget.__init__(self)
        self.reactor = reactor
        self.parent = parent
        #import all experiments
        reloader.enable(blacklist=['labrad', 'labrad.units', 'numpy','matplotlib'])
        self.experiments = {}
        for semaphore_path,value in c.ExperimentInfo.iteritems():
            local_path,name = value
            try:
                __import__(local_path)
            except ImportError as e:
                print 'Script Control Error importing: ', e
            else:
                self.experiments[semaphore_path] = (local_path, name)
        
        self.setupExperimentProgressDict() #MR, is this dictionary necessary or is it enough to use semaphore?
        self.connect()
        self.experimentParametersWidget = ParametersWidget(self)
        self.schedulerWidget = Scheduler(self, c.conflictingExperiments)
        self.setupMainWidget()

    def getWidgets(self):
        return self, self.experimentParametersWidget         
        
    def setupExperimentProgressDict(self):
        self.experimentProgressDict = self.experiments.copy()
        for key in self.experimentProgressDict.keys():
            self.experimentProgressDict[key] = 0.0
        
    # Connect to LabRAD
    @inlineCallbacks
    def connect(self):        
        from connection import connection
        self.cxn = connection()
        yield self.cxn.connect()
        self.cxn.on_connect['Semaphore'].append( self.reinitialize_semaphore)
        self.cxn.on_disconnect['Semaphore'].append( self.disable)        
        try:
            self.server = self.cxn.servers['Semaphore']
            test = yield self.cxn.servers['Semaphore'].test_connection() #MR: why this is necessary?
            self.createContexts()
        except Exception, e:
            print 'Not Initially Connected to Semaphore', e
            self.setDisabled(True)
            self.experimentParametersWidget.setDisabled(True)

            
    @inlineCallbacks
    def reinitialize_semaphore(self):
        self.setEnabled(True)
        try:
            self.experimentParametersWidget.setEnabled(True)
            self.experimentParametersWidget.setupExperimentGrid(self.experimentParametersWidget.globalGrid.experimentPath)
            self.experimentParametersWidget.setupGlobalGrid(self.experimentParametersWidget.globalGrid.experimentPath)
            self.experimentParametersWidget.experimentGrid.refreshParameterListener()
            self.experimentParametersWidget.globalGrid.refreshParameterListener()
            self.setupStatusWidget(self.statusWidget.experimentPath)
            self.statusWidget.refreshStatusListener()
            self.schedulerWidget.reinitializeListener()
        #MR not sure why this is necessary
        except AttributeError: # happens when server wasn't on from the beginning. Warning, this might catch unrelated errors, although the original er
            self.server = self.cxn.servers['Semaphore']
            self.createContexts()
        yield None

        
    @inlineCallbacks
    def disable(self):
        self.setDisabled(True)
        self.experimentParametersWidget.setDisabled(True)
        yield None

    
    # Setup the main layout
    def setupMainWidget(self):    
        # contexts

        
        self.mainLayout = QtGui.QVBoxLayout()
        
        self.widgetLayout = QtGui.QHBoxLayout()
               
        # mainGrid is in mainLayout that way its size can be controlled.
        self.mainGrid = QtGui.QGridLayout()
        self.mainGrid.setSpacing(5)
        
        # Labels
        font = QtGui.QFont('MS Shell Dlg 2',pointSize=14)
        font.setUnderline(True)
        self.experimentListLabel = QtGui.QLabel('Experiment Navigation')
        self.experimentListLabel.setFont(font)
        self.activeExperimentListLabel = QtGui.QLabel('Active Experiments')
        self.activeExperimentListLabel.setFont(font)  
        self.queuedExperimentListLabel = QtGui.QLabel('Queued Experiments')
        self.queuedExperimentListLabel.setFont(font)     
        self.schedulerLabel = QtGui.QLabel('Scheduler')
        self.schedulerLabel.setFont(font)        

#        self.experimentParametersLabel = QtGui.QLabel('Experiment Parameters')
#        self.experimentParametersLabel.setFont(font)
#        self.globalParametersLabel = QtGui.QLabel('Global Parameters')
#        self.globalParametersLabel.setFont(font)
#        self.controlLabel = QtGui.QLabel('Control')
#        self.controlLabel.setFont(font)
                     
        self.experimentListLayout = QtGui.QVBoxLayout()
               
        # Setup Experiment List Widget
        self.experimentListWidget = ExperimentListWidget(self)
        self.experimentListWidget.show()
        
        self.activeExperimentListWidget = ActiveExperimentsListWidget(self)
        self.activeExperimentListWidget.show()
        
        self.queuedExperimentsListWidget = QueuedExperimentsListWidget(self)
        self.queuedExperimentsListWidget.show()
        
#        self.schedulerWidget = Scheduler(self)
        self.schedulerWidget.show()
        
        self.experimentListLayout.addWidget(self.experimentListLabel)
        self.experimentListLayout.setAlignment(self.experimentListLabel, QtCore.Qt.AlignCenter)
        self.experimentListLayout.setStretchFactor(self.experimentListLabel, 0)
        self.experimentListLayout.addWidget(self.experimentListWidget)
        self.experimentListLayout.addWidget(self.schedulerLabel)
        self.experimentListLayout.setAlignment(self.schedulerLabel, QtCore.Qt.AlignCenter)
        self.experimentListLayout.setStretchFactor(self.schedulerLabel, 0)        
        self.experimentListLayout.addWidget(self.schedulerWidget)               
        self.experimentListLayout.addWidget(self.activeExperimentListLabel)
        self.experimentListLayout.setAlignment(self.activeExperimentListLabel, QtCore.Qt.AlignCenter)
        self.experimentListLayout.setStretchFactor(self.activeExperimentListLabel, 0)        
        self.experimentListLayout.addWidget(self.activeExperimentListWidget)    
        self.experimentListLayout.addWidget(self.queuedExperimentListLabel)
        self.experimentListLayout.setAlignment(self.queuedExperimentListLabel, QtCore.Qt.AlignCenter)
        self.experimentListLayout.setStretchFactor(self.queuedExperimentListLabel, 0)        
        self.experimentListLayout.addWidget(self.queuedExperimentsListWidget)         
        
        self.experimentListLayout.setStretchFactor(self.experimentListWidget, 0)
        self.experimentListLayout.setStretchFactor(self.schedulerWidget, 0)
        self.experimentListLayout.setStretchFactor(self.activeExperimentListWidget, 0)
                
        # Setup Experiment Parameter Widget
#        yield deferToThread(time.sleep, .05) # necessary delay. Qt issue.
#        self.experimentGridLayout = QtGui.QVBoxLayout()
#        self.setupExperimentGrid(['Test', 'Exp1']) # the experiment to start with
        # Setup Global Parameter Widget
#        self.globalGridLayout = QtGui.QVBoxLayout()      
#        self.setupGlobalGrid(['Test', 'Exp1']) # the experiment to start with
        # Setup Status Widget
#        self.setupStatusWidget(['Test', 'Exp1']) # the experiment to start with

        self.widgetLayout.addLayout(self.experimentListLayout)
#        self.widgetLayout.addLayout(self.experimentGridLayout)
#        self.widgetLayout.addLayout(self.globalGridLayout)
#        self.widgetLayout.addLayout(self.statusLayout)

#        parameterLimitsButton = QtGui.QPushButton("Parameter Limits", self)
#        parameterLimitsButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
#        parameterLimitsButton.clicked.connect(self.parameterLimitsWindowEvent)
#        self.miscLayout.addWidget(parameterLimitsButton)       

        self.mainLayout.addLayout(self.widgetLayout)       
#        self.mainLayout.addLayout(self.miscLayout)
        self.setLayout(self.mainLayout)
        self.show()
#        self.experimentParametersWidget = ParametersWidget(self, self.experimentContext, self.globalContext)
 
    @inlineCallbacks
    def createContexts(self):
        self.experimentListWidget.populateList([])
        self.experimentContext = yield self.cxn.context()
        self.globalContext = yield self.cxn.context()
        self.statusContext = yield self.cxn.context()
        self.schedulerContext = yield self.cxn.context()
        self.experimentParametersWidget.setContexts(self.experimentContext, self.globalContext)
        self.setupStatusWidget(['Test', 'Exp1']) # the experiment to start with ####shouldn't be manually written
        self.schedulerWidget.setContext(self.schedulerContext)

    def setupStatusWidget(self, experiment):
        self.statusWidget = StatusWidget(self, experiment, self.statusContext)
        self.experimentListLayout.addWidget(self.statusWidget)
        self.experimentListLayout.setAlignment(self.statusWidget, QtCore.Qt.AlignCenter)
        self.statusWidget.show()
        self.setupStatusWidget = self.setupStatusWidgetSubsequent 
        
#        try:
#            self.statusWidget.disconnectSignal()
#            self.statusWidget.hide()
#            del self.statusWidget
#        except:
#            # First time
#            pass

    def setupStatusWidgetSubsequent(self, experiment):
        self.statusWidget.createStatusLabel(experiment)

        
    # Returns a different widget depending on the type of value provided by the semaphore 
    def typeCheckerWidget(self, Value):
        # boolean
        t = type(Value)
        if t == bool:
            checkbox = QtGui.QCheckBox()
            checkbox.setChecked(Value)
            return checkbox
        elif t == str:
            lineEdit = QtGui.QLineEdit()       
            lineEdit.setText(Value)
            return lineEdit
        else:
            value = Value.aslist
        from labrad.units import Value as labradValue
        if ((type(value) == list) and (len(value) == 3) and (type(value[2]) == labradValue)):
            doubleSpinBox = QtGui.QDoubleSpinBox()
            doubleSpinBox.setRange(value[0], value[1])
            number_dec = len(str(value[2].value-int(value[2].value))[2:])
            doubleSpinBox.setDecimals(number_dec + 1)
            doubleSpinBox.setValue(value[2])
            doubleSpinBox.setSuffix(' ' + value[2].units)
            doubleSpinBox.setSingleStep(.1)
            doubleSpinBox.setKeyboardTracking(False)
            doubleSpinBox.setMouseTracking(False)
            return doubleSpinBox
        # list with more or less than 3 values
        else:
            lineEdit = QtGui.QLineEdit()       
            text = str(value)
            text = re.sub('Value', '', text)
            lineEdit.setText(text)
            return lineEdit
    
    @inlineCallbacks
    def startExperiment(self, experiment):
        try:
            local_path, name = self.experiments[experiment]
            module = sys.modules[local_path]
            reloader.reload(module)
            experiment = getattr(module, name)
            instance = experiment()
            yield deferToThread(instance.run)
        except Exception as e:
            raise
            print e
            self.statusWidget.handleScriptError(e)
        except:
            print sys.exc_info()
            self.statusWidget.handleScriptError()
        
    def saveParametersToRegistry(self, res):
        return self.server.save_parameters_to_registry()
       
    def exitProcedure(self, x):
        dl = [self.server.set_parameter(list(experiment) + ['Semaphore', 'Status'], 'Stopped', context = self.statusContext) for experiment in self.experiments.keys()]
        dl = DeferredList(dl)
        dl.addCallback(self.saveParametersToRegistry)
        return dl

    def closeEvent(self, res):
        self.reactor.stop()
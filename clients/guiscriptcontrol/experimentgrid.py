from PyQt4 import QtGui
from twisted.internet.defer import inlineCallbacks
import re

class ExperimentGrid(QtGui.QTableWidget):
    def __init__(self, parent, experimentPath, context):
        QtGui.QTableWidget.__init__(self)
        self.parent = parent
        self.context = context
        self.experimentPath = experimentPath
#        self.parent.setWindowTitle(experimentPath[-1])
        self.setupExperimentGrid(self.experimentPath)
        self.setupExperimentParameterListener()

    @inlineCallbacks
    def setupExperimentGrid(self, experimentPath):
        self.parent.setWindowTitle(experimentPath[-1])
        self.experimentPath = experimentPath
        self.setColumnCount(2)

        self.checkBoxParameterDict = {}
        self.parameterCheckBoxDict = {}
        
        self.doubleSpinBoxParameterDict = {}
        self.parameterDoubleSpinBoxDict = {}

        self.lineEditParameterDict = {}
        self.parameterLineEditDict = {}        
        
        expParams = yield self.parent.parent.server.get_parameter_names(self.experimentPath)      
        expParamNames = expParams.aslist        
        expParamNames.sort()
        
        self.setRowCount(len(expParamNames))
        
        Row = 0
        for parameter in expParamNames:
            item = QtGui.QTableWidgetItem(parameter)
            self.setItem(Row, 1, item)
            value = yield self.parent.parent.server.get_parameter(self.experimentPath + [parameter])
            widget = self.parent.parent.typeCheckerWidget(value)
            widgetType = type(widget)
            if (widgetType == QtGui.QCheckBox):
                self.checkBoxParameterDict[widget] = parameter
                self.parameterCheckBoxDict[parameter] = widget
                widget.stateChanged.connect(self.updateCheckBoxStateToSemaphore)   
                self.setCellWidget(Row, 0, widget)        
            elif (widgetType == QtGui.QDoubleSpinBox):
                self.doubleSpinBoxParameterDict[widget] = parameter
                self.parameterDoubleSpinBoxDict[parameter] = widget 
                widget.valueChanged.connect(self.updateSpinBoxValueToSemaphore)
                self.setCellWidget(Row, 0, widget)
            elif(widgetType == QtGui.QLineEdit):
                self.lineEditParameterDict[widget] = parameter
                self.parameterLineEditDict[parameter] = widget
                widget.editingFinished.connect(self.updateLineEditValueToSemaphore)                  
                self.setCellWidget(Row, 0, widget)

            
            Row += 1

#        self.resizeColumnsToContents()  
#        self.setColumnWidth(0, self.columnWidth(0) + 10)
#        self.setColumnWidth(1, self.columnWidth(1) + 20)
#        width = self.columnWidth(0) + self.columnWidth(1)      
#        self.setMinimumWidth(width*1.5)
        self.horizontalHeader().setStretchLastSection(True)
    
    @inlineCallbacks
    def setupExperimentParameterListener(self):
        yield self.parent.parent.server.signal__parameter_change(22222, context = self.context)
        yield self.parent.parent.server.addListener(listener = self.updateExperimentParameter, source = None, ID = 22222, context = self.context)  
    
    def updateExperimentParameter(self, x, y):
        # check to see if this is an experiment parameter
        if (y[0][:-1] == self.experimentPath):
            # begin typecheckin 
            if (type(y[1]) == bool):
                self.parameterCheckBoxDict[y[0][-1]].blockSignals(True)
                self.parameterCheckBoxDict[y[0][-1]].setChecked(y[1])
                self.parameterCheckBoxDict[y[0][-1]].blockSignals(False)
            # it's a list
            else:
                value = y[1].aslist
                if (type(value[0]) == str):
                    self.parameterLineEditDict[y[0][-1]].blockSignals(True)
                    self.parameterLineEditDict[y[0][-1]].setText(str(y[1]))
                    self.parameterLineEditDict[y[0][-1]].blockSignals(False)                    
                elif (len(value) == 3):
                    try:
                        self.parameterDoubleSpinBoxDict[y[0][-1]].blockSignals(True)
                        self.parameterDoubleSpinBoxDict[y[0][-1]].setValue(value[2])
                        self.parameterDoubleSpinBoxDict[y[0][-1]].blockSignals(False)
                        self.parameterDoubleSpinBoxDict[y[0][-1]].setEnabled(True)
                    except KeyError:
                        self.parameterLineEditDict[y[0][-1]].setDisabled(True)
                # lineEdit        
                else: 
                    text = str(value)
                    text = re.sub('Value', '', text)
                    try:
                        self.parameterLineEditDict[y[0][-1]].blockSignals(True)
                        self.parameterLineEditDict[y[0][-1]].setText(text)
                        self.parameterLineEditDict[y[0][-1]].blockSignals(False)
                        self.parameterLineEditDict[y[0][-1]].setEnabled(True)
                    # list turned into a spinbox!
                    except KeyError:
                        self.parameterDoubleSpinBoxDict[y[0][-1]].setDisabled(True)
    

    @inlineCallbacks
    def updateCheckBoxStateToSemaphore(self, evt):
        yield self.parent.parent.server.set_parameter(self.experimentPath + [self.checkBoxParameterDict[self.sender()]], bool(evt), context = self.context)
        
    @inlineCallbacks
    def updateSpinBoxValueToSemaphore(self, parameterValue):
        from labrad import types as T
        yield self.parent.parent.server.set_parameter(self.experimentPath + [self.doubleSpinBoxParameterDict[self.sender()]], [T.Value(self.sender().minimum(), str(self.sender().suffix()[1:])), T.Value(self.sender().maximum(), str(self.sender().suffix()[1:])), T.Value(parameterValue, str(self.sender().suffix()[1:]))], context = self.context)
        
    @inlineCallbacks
    def updateLineEditValueToSemaphore(self):
        from labrad import types as T
        # two types....tuples [(value, unit)] or tuples of strings and values [(string, (value, unit))]
        value = eval(str(self.sender().text()))
        print 'Value!: ', value
        typeFirstElement = type(value[0])
        typeSecondElement = type(value[0][1])
        # normal list of labrad values
        if (typeFirstElement == str):
            pass        
        elif (typeSecondElement == str):
            # build a list of labrad values
            for i in range(len(value)):
                value[i] = T.Value(value[i][0], value[i][1])
        elif (typeSecondElement == type(None)):
            # build a list of labrad values
            for i in range(len(value)):
                value[i] = value[i][0]                
        elif (typeSecondElement == tuple):
            for i in range(len(value)):
                value[i] = (value[i][0], T.Value[value[i][1][0]], value[i][1][1])
        yield self.parent.parent.server.set_parameter(self.experimentPath + [self.lineEditParameterDict[self.sender()]], value, context = self.context)

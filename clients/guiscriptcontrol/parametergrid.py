from PyQt4 import QtGui
from twisted.internet.defer import inlineCallbacks
import re

class ParameterGrid(QtGui.QTableWidget):
    def __init__(self, parent, experimentPath, context, globalParams = False):
        QtGui.QTableWidget.__init__(self)
        self.parent = parent
        self.context = context
        self.experimentPath = experimentPath
        self.globalParams = globalParams
#        self.parent.setWindowTitle(experimentPath[-1])
        self.setupParameterGrid(self.experimentPath)
        self.setupParameterListener()

    @inlineCallbacks
    def setupParameterGrid(self, experimentPath):
        self.experimentPath = experimentPath
        self.setColumnCount(2)

        self.checkBoxParameterDict = {}
        self.parameterCheckBoxDict = {}
        
        self.doubleSpinBoxParameterDict = {}
        self.parameterDoubleSpinBoxDict = {}

        self.lineEditParameterDict = {}
        self.parameterLineEditDict = {}    
        
        if (self.globalParams == True):
            self.globalParameterDict = {}
            
            numParams = 0
            path = self.experimentPath
            for i in range(len(self.experimentPath)):
                path = path[:-1]
                paramNames = yield self.parent.parent.server.get_parameter_names(path)
                numParams += len(paramNames)
                for paramName in paramNames:
                    self.globalParameterDict[paramName] = path + [paramName]
            
            self.setRowCount(numParams)
            
            parameterNames = self.globalParameterDict.keys()      
            parameterNames.sort()          

        else:  

            expParams = yield self.parent.parent.server.get_parameter_names(self.experimentPath)      
            parameterNames = expParams.aslist        
            parameterNames.sort()
            
            self.setRowCount(len(parameterNames))
        
        Row = 0
        for parameter in parameterNames:
            item = QtGui.QTableWidgetItem(parameter)
            self.setItem(Row, 1, item)
            if (self.globalParams == True):
                value = yield self.parent.parent.server.get_parameter(self.globalParameterDict[parameter])
            else:
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
    def setupParameterListener(self):
        yield self.parent.parent.server.signal__parameter_change(22222, context = self.context)
        yield self.parent.parent.server.addListener(listener = self.checkParameter, source = None, ID = 22222, context = self.context)  
    
    @inlineCallbacks
    def refreshParameterListener(self):
        yield self.parent.parent.server.signal__parameter_change(22222, context = self.context)
    
    def checkParameter(self, x, y):
        if (self.globalParams == True):
            if (y[0][-1] in self.globalParameterDict.keys()):
                self.updateParameter(x, y)
        else:
            if ((y[0][:-1] == self.experimentPath)):
                self.updateParameter(x, y)
    
    def updateParameter(self, x, y):
        # check to see if this is an experiment parameter
       
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
        if (self.globalParams == True):
            yield self.parent.parent.server.set_parameter(self.globalParameterDict[self.checkBoxParameterDict[self.sender()]], bool(evt), context = self.context)
        else:
            yield self.parent.parent.server.set_parameter(self.experimentPath + [self.checkBoxParameterDict[self.sender()]], bool(evt), context = self.context)
        
    @inlineCallbacks
    def updateSpinBoxValueToSemaphore(self, parameterValue):
        from labrad import types as T
        if (self.globalParams == True):
            yield self.parent.parent.server.set_parameter(self.globalParameterDict[self.doubleSpinBoxParameterDict[self.sender()]], [T.Value(self.sender().minimum(), str(self.sender().suffix()[1:])), T.Value(self.sender().maximum(), str(self.sender().suffix()[1:])), T.Value(parameterValue, str(self.sender().suffix()[1:]))], context = self.context)
        else:
            yield self.parent.parent.server.set_parameter(self.experimentPath + [self.doubleSpinBoxParameterDict[self.sender()]], [T.Value(self.sender().minimum(), str(self.sender().suffix()[1:])), T.Value(self.sender().maximum(), str(self.sender().suffix()[1:])), T.Value(parameterValue, str(self.sender().suffix()[1:]))], context = self.context)
        
    @inlineCallbacks
    def updateLineEditValueToSemaphore(self):
        from labrad import types as T
        # two types....tuples [(value, unit)] or tuples of strings and values [(string, (value, unit))]
        value = eval(str(self.sender().text()))
#        print 'Value!: ', value
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
        if (self.globalParams == True):
            yield self.parent.parent.server.set_parameter(self.globalParameterDict[self.lineEditParameterDict[self.sender()]], value, context = self.context)
        else:
            yield self.parent.parent.server.set_parameter(self.experimentPath + [self.lineEditParameterDict[self.sender()]], value, context = self.context)

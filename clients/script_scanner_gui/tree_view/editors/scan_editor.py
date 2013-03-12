from PyQt4 import QtCore, QtGui, uic
from numpy import linspace
import os

basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"..","..","Views", "ScanEditor.ui")
scanBase, scanForm = uic.loadUiType(path)

class scan_delegate(QtGui.QAbstractItemDelegate):
    def __init__(self, parent):
        super(scan_delegate, self).__init__()
        self.parent = parent
        self.parent.on_new_scan.connect(self.set_scan_data)
        self.parent.uiMin.editingFinished.connect(self.on_new_min)
        self.parent.uiMax.editingFinished.connect(self.on_new_max)
   
    def setEditorData(self, editor, index):
        node = index.internalPointer()
        if editor == self.parent.uiName or editor == self.parent.uiCollection:
            editor.setText(node.data(index.column()))
        elif editor == self.parent.uiStart or editor == self.parent.uiStop:
            editor.setValue(node.data(index.column()))
            self.parent.onNewStartStop(emit = False)
        elif editor == self.parent.uiSteps:
            editor.setValue(node.data(index.column()))
            self.parent.onNewSteps(emit = False)
        elif editor == self.parent.uiMin:
            editor.setValue(node.data(index.column()))
            self.parent.set_minimum(node.data(index.column()))
        elif editor == self.parent.uiMax:
            editor.setValue(node.data(index.column()))
            self.parent.set_maximum(node.data(index.column()))
        elif index.column() == 8:
            self.parent.set_suffix(node.data(index.column()))
    
    def set_scan_data(self, x, y, z):
        self.commitData.emit(self.parent.uiStart)
        self.commitData.emit(self.parent.uiStop)
        self.commitData.emit(self.parent.uiSteps)
    
    def on_new_min(self):
        self.commitData.emit(self.parent.uiMin)
    
    def on_new_max(self):
        self.commitData.emit(self.parent.uiMax)
        
    def setModelData(self, editor, model, index):
        if index.column() == 8:
            return
        elif isinstance(editor, QtGui.QLineEdit):
            value = editor.text()
        else:
            value = editor.value()
        model.setData(index, QtCore.QVariant(value))

class ScanWidget(scanBase, scanForm):
    
    on_new_scan = QtCore.pyqtSignal(float,float,int)
    
    def __init__(self, parent=None):
        super(ScanWidget, self).__init__(parent)
        self.setupUi(self)
        self.connect_signals()
    
    def connect_signals(self):
        self.uiDecimals.valueChanged.connect(self.on_new_decimals)
        self.uiStart.editingFinished.connect(self.onNewStartStop)
        self.uiStop.editingFinished.connect(self.onNewStartStop)
        self.uiSetResolution.editingFinished.connect(self.onNewResolution)
        self.uiSteps.editingFinished.connect(self.onNewSteps)
        self.uiSpan.editingFinished.connect(self.onNewCenterSpan)
        self.uiCenter.editingFinished.connect(self.onNewCenterSpan)
    
    def on_new_decimals(self, decimals):
        for widget in [self.uiMin, self.uiMax, self.uiStart, self.uiStop, self.uiCenter, self.uiSpan,
                       self.uiSetResolution, self.uiActualResolution]:
            widget.setSingleStep(10**-decimals)
            widget.setDecimals(decimals)
    
    def set_suffix(self, suffix):
        for widget in [self.uiMin, self.uiMax, self.uiStart, self.uiStop, self.uiCenter, self.uiSpan,
                       self.uiSetResolution, self.uiActualResolution]:
            widget.setSuffix(suffix)
    
    def set_minimum(self, value):
        for widget in [self.uiStart, self.uiStop, self.uiCenter]:
            widget.setMinimum(value)
    
    def set_maximum(self, value):
        for widget in [self.uiStart, self.uiStop, self.uiCenter]:
            widget.setMaximum(value)

    def onNewCenterSpan(self, emit = True):
        center = self.uiCenter.value()
        span = self.uiSpan.value()
        start = center - span / 2.0
        stop = center + span/2.0
        self.uiStart.setValue(start)
        self.uiStop.setValue(stop)
        self.updateResolutionSteps(emit)

    def onNewStartStop(self, emit = True):
        start = self.uiStart.value()
        stop = self.uiStop.value()
        self.uiCenter.setValue((start + stop)/2.0)
        self.uiSpan.setValue(stop - start)
        self.updateResolutionSteps(emit)

    def updateResolutionSteps(self, emit = True):
        '''calculate and update the resolution or the steps depending on which is locked'''
        if self.uiLockSteps.isChecked():
            self.onNewSteps(emit)
        else:
            self.onNewResolution(emit)
            
    def updateActualResolution(self, val):
        self.uiActualResolution.setValue(val)

    def onNewSteps(self, emit = True):
        steps = self.uiSteps.value()
        start = self.uiStart.value()
        stop = self.uiStop.value()
        res = self._resolution_from_steps(start, stop, steps)
        self.uiSetResolution.setValue(res)
        self.updateActualResolution(res)
        if emit:
            self.on_new_scan.emit(start, stop, steps)
    
    def onNewResolution(self, emit = True):
        '''called when resolution is updated'''
        res = self.uiSetResolution.value()
        start = self.uiStart.value()
        stop = self.uiStop.value()
        steps = self._steps_from_resolution(start, stop, res)
        self.uiSteps.setValue(steps)
        final_res = self._resolution_from_steps(start, stop, steps)
        self.updateActualResolution(final_res)
        if emit:
            self.on_new_scan.emit(start, stop, steps)

    def _resolution_from_steps(self, start, stop, steps):
        '''computes the resolution given the number of steps'''
        if steps > 1:
            res = linspace(start, stop, steps, endpoint = True, retstep = True)[1]
        else:
            res = stop - start
        return res

    def _steps_from_resolution(self, start, stop, res):
        '''computes the number of steps given the resolution'''
        try:
            steps = int(round( (stop - start) / res))
        except ZeroDivisionError:
            steps = 0                                
        steps = 1 +  max(0, steps) #make sure at least 1
        return steps

class ScanEditor(ScanWidget):
    def __init__(self, parent=None):
        super(ScanEditor, self).__init__(parent)
        self._dataMapper = QtGui.QDataWidgetMapper(self)
        self._dataMapper.setItemDelegate(scan_delegate(self))

    def setModel(self, proxyModel):
        self._proxyModel = proxyModel
        self._dataMapper.setModel(proxyModel.sourceModel())
        self._dataMapper.addMapping(self.uiName, 0)
        self._dataMapper.addMapping(self.uiCollection, 2)
        self._dataMapper.addMapping(self.uiMin, 3)
        self._dataMapper.addMapping(self.uiMax, 4)
        self._dataMapper.addMapping(self.uiStart, 5)
        self._dataMapper.addMapping(self.uiStop, 6)
        self._dataMapper.addMapping(self.uiSteps, 7)
        self._dataMapper.addMapping(QtGui.QWidget(self), 8)
     
    def setSelection(self, current):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current)
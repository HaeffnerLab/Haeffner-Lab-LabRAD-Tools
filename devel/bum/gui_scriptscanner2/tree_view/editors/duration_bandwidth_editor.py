from PyQt4 import QtCore, QtGui, uic
import numpy as np
import os

basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"..","..","Views", "DurationBandwidthEditor.ui")
base, form = uic.loadUiType(path)

class parameter_delegate(QtGui.QAbstractItemDelegate):
    def __init__(self, parent):
        super(parameter_delegate, self).__init__()
        self.parent = parent
        self.parent.uiValue.editingFinished.connect(self.on_new_value)
        self.parent.uiMin.editingFinished.connect(self.on_new_min)
        self.parent.uiMax.editingFinished.connect(self.on_new_max)
        
    def setEditorData(self, editor, index):
        node = index.internalPointer()
        if editor == self.parent.uiName or editor == self.parent.uiCollection:
            editor.setText(node.data(index.column()))
        elif editor == self.parent.uiValue:
            self.parent.on_new_duration()        
            editor.setValue(node.data(index.column()))
        elif editor == self.parent.uiMin:
            editor.setValue(node.data(index.column()))
            self.parent.uiValue.setMinimum(node.data(index.column()))
        elif editor == self.parent.uiMax:
            editor.setValue(node.data(index.column()))
            self.parent.uiValue.setMaximum(node.data(index.column()))
        elif index.column() == 6:
            suffix = node.data(index.column())
            self.parent.uiValue.setSuffix(suffix)
            self.parent.uiMin.setSuffix(suffix)
            self.parent.uiMax.setSuffix(suffix)
            self.parent.on_new_duration()
    
    def on_new_value(self):
        self.commitData.emit(self.parent.uiValue)
    
    def on_new_min(self):
        self.commitData.emit(self.parent.uiMin)
    
    def on_new_max(self):
        self.commitData.emit(self.parent.uiMax)
    
    def setModelData(self, editor, model, index):
        if index.column() == 6:
            return
        elif isinstance(editor, QtGui.QLineEdit):
            value = editor.text()
        else:
            value = editor.value()
        model.setData(index, QtCore.QVariant(value))

class DurationBandwidthEditor(base, form):
    
    max_columns = 10
    
    def __init__(self, parent=None):
        super(DurationBandwidthEditor, self).__init__(parent)
        from labrad.units import WithUnit
        self.WithUnit = WithUnit
        
        self.setupUi(self)
        self._dataMapper = QtGui.QDataWidgetMapper(self)
        self._dataMapper.setItemDelegate(parameter_delegate(self))
        self.connect_signals()
    
    def connect_signals(self):
        self.uiDecimals.valueChanged.connect(self.on_new_decimals)
        self.uiValue.editingFinished.connect(self.on_new_duration)
    
    def on_new_duration(self):
        try:
            duration = self.uiValue.value()
            duration = self.WithUnit(duration, str(self.uiValue.suffix()))
            bandwidth = 1.0 / ( 2.0 * np.pi * duration)
        except ZeroDivisionError:
            pass
        else:
            self.uiBandwidth.setValue(bandwidth[str(self.uiBandwidth.suffix())])

    
    def on_new_decimals(self, decimals):
        for widget in [self.uiMin, self.uiMax, self.uiValue, self.uiBandwidth]:
            widget.setSingleStep(10**-decimals)
            widget.setDecimals(decimals)

    def setModel(self, proxyModel):
        self._proxyModel = proxyModel
        self._dataMapper.setModel(proxyModel.sourceModel())
        self._dataMapper.addMapping(self.uiName, 0)
        self._dataMapper.addMapping(self.uiCollection, 2)
        self._dataMapper.addMapping(self.uiMin, 3)
        self._dataMapper.addMapping(self.uiMax, 4)
        self._dataMapper.addMapping(self.uiValue, 5)
        self._dataMapper.addMapping(QtGui.QWidget(self), 6)
     
    def setSelection(self, current):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current)
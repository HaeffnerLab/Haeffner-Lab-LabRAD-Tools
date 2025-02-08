from PyQt5 import QtCore, QtGui, QtWidgets, uic
from common.abstractdevices.script_scanner2.gui_scriptscanner2.sideband_config import sidebands
import os

basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"..","..","Views", "SidebandSelectionV2Editor.ui")
base, form = uic.loadUiType(path)

class simple_selection_delegate(QtWidgets.QAbstractItemDelegate):
    def __init__(self, parent):
        super(simple_selection_delegate, self).__init__()
        self.parent = parent
        self.parent.uiSelectedMode.activated.connect(self.on_new_index)
        
    def setEditorData(self, editor, index):
        node = index.internalPointer()
        if editor == self.parent.uiName or editor == self.parent.uiCollection:
            editor.setText(node.data(index.column()))
        if index.column() == 3:
            for item in sidebands:
                if self.parent.uiSelectedMode.findText(item) == -1:
                    self.parent.uiSelectedMode.addItem(item)
            index = self.parent.uiSelectedMode.findText(node.data(index.column()))
            self.parent.uiSelectedMode.setCurrentIndex(index)
    
    def on_new_index(self, text):
        self.commitData.emit(self.parent.uiSelectedMode)
    
    def setModelData(self, editor, model, index):
        if index.column() == 3:
            model.setData(index, QtCore.QVariant(self.parent.uiSelectedMode.currentText()))

class sideband_selection_v2_editor(base, form):
    def __init__(self, parent=None):
        super(sideband_selection_v2_editor, self).__init__(parent)
        self.setupUi(self)
        self._dataMapper = QtWidgets.QDataWidgetMapper(self)
        self._dataMapper.setItemDelegate(simple_selection_delegate(self))

    def setModel(self, proxyModel):
        self._proxyModel = proxyModel
        self._dataMapper.setModel(proxyModel.sourceModel())
        self._dataMapper.addMapping(self.uiName, 0)
        self._dataMapper.addMapping(self.uiCollection, 2)
        self._dataMapper.addMapping(self.uiSelectedMode, 3)
        self._dataMapper.addMapping(self.uiOrder, 4)
    
    def setSelection(self, current):
        #self.uiValue.clear()
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current)

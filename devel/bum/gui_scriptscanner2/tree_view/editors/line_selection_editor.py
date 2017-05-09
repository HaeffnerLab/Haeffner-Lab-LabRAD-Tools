from PyQt4 import QtGui, QtCore, uic
import os

basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"..","..","Views", "SelectionEditor.ui")
base, form = uic.loadUiType(path)

class line_selection_delegate(QtGui.QAbstractItemDelegate):
    def __init__(self, parent):
        super(line_selection_delegate, self).__init__()
        self.parent = parent
        self.parent.uiValue.activated.connect(self.on_new_index)
        
    def setEditorData(self, editor, index):
        node = index.internalPointer()
        if editor == self.parent.uiName or editor == self.parent.uiCollection:
            editor.setText(node.data(index.column()))
        if index.column() == 3:
            for data,display in node.data(4).iteritems():
                if self.parent.uiValue.findText(display) == -1:
                    self.parent.uiValue.addItem(display, userData = data)
            index = self.parent.uiValue.findData(node.data(index.column()))
            self.parent.uiValue.setCurrentIndex(index)
    
    def on_new_index(self, text):
        self.commitData.emit(self.parent.uiValue)
    
    def setModelData(self, editor, model, index):
        if index.column() == 3:
            data = self.parent.uiValue.itemData(self.parent.uiValue.currentIndex() )
            model.setData(index, QtCore.QVariant(data.toString()))

class line_selection_editor(base, form):
    def __init__(self, parent=None):
        super(line_selection_editor, self).__init__(parent)
        self.setupUi(self)
        self._dataMapper = QtGui.QDataWidgetMapper(self)
        self._dataMapper.setItemDelegate(line_selection_delegate(self))

    def setModel(self, proxyModel):
        self._proxyModel = proxyModel
        self._dataMapper.setModel(proxyModel.sourceModel())
        self._dataMapper.addMapping(self.uiName, 0)
        self._dataMapper.addMapping(self.uiCollection, 2)
        self._dataMapper.addMapping(self.uiValue, 3)

    def setSelection(self, current):
        self.uiValue.clear()
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current)
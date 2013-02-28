from PyQt4 import QtGui, uic
import os

basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"..","..","Views", "SidebandSelectionEditor.ui")
base, form = uic.loadUiType(path)

class sideband_selection_editor(base, form):
    def __init__(self, parent=None):
        super(sideband_selection_editor, self).__init__(parent)
        self.setupUi(self)
        self._dataMapper = QtGui.QDataWidgetMapper(self)

    def setModel(self, proxyModel):
        self._proxyModel = proxyModel
        self._dataMapper.setModel(proxyModel.sourceModel())
        self._dataMapper.addMapping(self.uiName, 0)
        self._dataMapper.addMapping(self.uiCollection, 2)
        self._dataMapper.addMapping(self.uiRadial1, 3)
        self._dataMapper.addMapping(self.uiRadial2, 4)
        self._dataMapper.addMapping(self.uiAxial, 5)
        self._dataMapper.addMapping(self.uiMicromotion, 6)

    def setSelection(self, current):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current)
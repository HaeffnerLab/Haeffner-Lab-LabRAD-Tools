from PyQt4 import QtCore, QtGui, uic
from Data import ParameterNode, ScanNode
from editors.parameter_editor import ParameterEditor
from editors.scan_editor import ScanEditor
import os

basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"..","Views", "Editors.ui")
propBase, propForm = uic.loadUiType(path)

class PropertiesEditor(propBase, propForm):
    
    def __init__(self, parent = None):
        super(propBase, self).__init__(parent)
        self.setupUi(self)

        self._proxyModel = None
        #create the edtiors
        self._parametersEditor = ParameterEditor(self)
        self._scanEditor = ScanEditor(self)
        #add editors to layout
        self.layoutSpecs.addWidget(self._parametersEditor)
        #hide the edtiors
        self._parametersEditor.setVisible(False)
        self._scanEditor.setVisible(False)
               
    def setSelection(self, current, old):
        current = self._proxyModel.mapToSource(current)
        node = current.internalPointer()
        if isinstance(node, ParameterNode):
            self._parametersEditor.setVisible(True)
            self._scanEditor.setVisible(False)
            self._parametersEditor.setSelection(current)
        elif isinstance(node, ScanNode):
            self._parametersEditor.setVisible(False)
            self._scanEditor.setVisible(True)
            self._scanEditor.setSelection(current)
        else:
            self._parametersEditor.setVisible(False)
            self._scanEditor.setVisible(False)
            
    def setModel(self, proxyModel):
        '''
        sets the model for all the editors
        '''
        self._proxyModel = proxyModel
        self._parametersEditor.setModel(proxyModel)
        self._scanEditor.setModel(proxyModel)
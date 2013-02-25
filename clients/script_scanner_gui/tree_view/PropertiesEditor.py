from PyQt4 import QtCore, QtGui, uic
from Data import ParameterNode, ScanNode, BoolNode, StringNode
from editors.parameter_editor import ParameterEditor
from editors.scan_editor import ScanEditor
from editors.bool_editor import BoolEditor
from editors.string_editor import StringEditor
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
        self._boolEditor = BoolEditor(self)
        self._stringEditor = StringEditor(self)
        self._editors = [self._parametersEditor, self._scanEditor, self._stringEditor, self._boolEditor]
        #add editors to layout
        self.layoutSpecs.addWidget(self._parametersEditor)
        #hide the edtiors
        for edit in self._editors:
            edit.setVisible(False)
               
    def setSelection(self, current, old):
        current = self._proxyModel.mapToSource(current)
        node = current.internalPointer()
        if isinstance(node, ParameterNode):
            self.show_only_editor(self._parametersEditor, current)
        elif isinstance(node, ScanNode):
            self.show_only_editor(self._scanEditor, current)
        elif isinstance(node, BoolNode):
            self.show_only_editor(self._boolEditor, current)
        elif isinstance(node, StringNode):
            self.show_only_editor(self._stringEditor, current)    
        else:
            for edit in self._editors:
                edit.setVisible(False)
    
    def show_only_editor(self, only_editor, current_selection):
        for edit in self._editors:
            if only_editor == edit:
                only_editor.setVisible(True)
                only_editor.setSelection(current_selection)
            else:
                edit.setVisible(False) 
        
    def setModel(self, proxyModel):
        '''
        sets the model for all the editors
        '''
        self._proxyModel = proxyModel
        for edit in self._editors:
            edit.setModel(proxyModel)
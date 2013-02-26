from PyQt4 import  uic
from Data import ParameterNode, ScanNode, BoolNode, StringNode, SelectionSimpleNode, LineSelectionNode
from Data import SidebandElectorNode, DurationBandwidthNode, SpectrumSensitivityNode
from editors.parameter_editor import ParameterEditor
from editors.scan_editor import ScanEditor
from editors.bool_editor import BoolEditor
from editors.string_editor import StringEditor
from editors.selection_editor import SelectionSimpleEditor
from editors.line_selection_editor import line_selection_editor
from editors.sideband_selection_editor import sideband_selection_editor
from editors.duration_bandwidth_editor import DurationBandwidthEditor
from editors.spectrum_sensitivity_editor import spectrum_sensitivity_editor

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
        self._selectionSimpleEditor = SelectionSimpleEditor(self)
        self._lineSelectionEdtior = line_selection_editor(self)
        self._sideband_selection_editor = sideband_selection_editor(self)
        self._DurationBandwidthEditor = DurationBandwidthEditor(self)
        self._spectrum_sensitivity_editor = spectrum_sensitivity_editor(self)
        self._editors = [self._parametersEditor, self._scanEditor, self._stringEditor, 
                         self._boolEditor, self._selectionSimpleEditor, self._lineSelectionEdtior,
                         self._sideband_selection_editor, self._DurationBandwidthEditor, self._spectrum_sensitivity_editor
                         ]
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
        elif isinstance(node, SelectionSimpleNode):
            self.show_only_editor(self._selectionSimpleEditor, current)    
        elif isinstance(node, LineSelectionNode):
            self.show_only_editor(self._lineSelectionEdtior, current)    
        elif isinstance(node, SidebandElectorNode):
            self.show_only_editor(self._sideband_selection_editor, current)
        elif isinstance(node, DurationBandwidthNode):
            self.show_only_editor(self._DurationBandwidthEditor, current)
        elif isinstance(node, SpectrumSensitivityNode):
            self.show_only_editor(self._spectrum_sensitivity_editor, current)
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
from PyQt4 import  uic
from twisted.internet.defer import inlineCallbacks
from editors.parameterEditor import ParameterEditor
from editors.boolEditor import BoolEditor

import os
basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"editors", "Editors.ui")
propBase, propForm = uic.loadUiType(path)

class ParameterImportWidget(propBase, propForm):
    types = [
        'parameter',
        'scan',
        'line_selection',
        'sideband_selection',
        'string',
        'bool',
        'duration_bandwidth',
        'spectrum_sensitivity'
        ]

    def __init__(self, parent = None):
        super(propBase, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)

        self.current_collection = None
        self.current_parameter = None

        for t in self.types:
            self.uiTypeSelect.addItem(t)

        self._editors = {
            'parameter': ParameterEditor(self),
            'bool': BoolEditor(self),
            }

        for e in self._editors.keys():
            w = self._editors[e]
            self.stackedWidget.addWidget(w)

        self.connect_layout()
        self.show_only_editor('parameter')

    def connect_layout(self):
        self.uiTypeSelect.currentIndexChanged.connect(self.on_selection_change)
        self.uiSubmit.clicked.connect(self.submit)

    def show_only_editor(self, editor):
        self.current_editor = self._editors[editor]
        self.stackedWidget.setCurrentWidget(self.current_editor)
        self.current_editor.guess()

    def on_selection_change(self, index):
        new_editor = self.uiTypeSelect.currentText()
        self.show_only_editor(str(new_editor))        

    def show_none(self):
        for editor in self._editors.keys():
            self._editors[editor].setVisible(False)

    def new_parameter(self, collection, parameter):
        '''
        A new parameter is selected in the list view.
        Called from the parent class
        '''
        self.current_collection = str(collection)
        self.current_parameter = str(parameter)
        name_string = collection + ', ' + parameter
        self.uiParameterName.setText(name_string)
        self.guess(str(parameter))

    def guess(self, parameter):
        '''
        Guess which parameter to show based on the parameter name
        '''

        if 'enable' in parameter:
            index = self.uiTypeSelect.findText('bool')
            self.uiTypeSelect.setCurrentIndex(index)
            self.show_only_editor('bool')
        else:
            index = self.uiTypeSelect.findText('parameter')
            self.uiTypeSelect.setCurrentIndex(index)

    @inlineCallbacks
    def submit(self, args):
        pv = yield self.parent.parent.cxn.get_server('ParameterVault')
        editor = self.current_editor
        full_info =  editor.full_info()
        col = self.current_collection
        par = self.current_parameter

        if (col is not None) and (par is not None):
            pv.new_parameter(col, par, full_info)
            self.parent.removeCurrentRow()

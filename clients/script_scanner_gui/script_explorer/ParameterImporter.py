from PyQt4 import  uic
#from editors.newParameterEditor import newParameterEditor
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

        self._parameterEditor = ParameterEditor(self)
        self._boolEditor = BoolEditor(self)
        self._editors = {
            'parameter': self._parameterEditor,
            'bool': self._boolEditor,
            }

        self.stackedWidget.addWidget(self._parameterEditor)
        self.stackedWidget.addWidget(self._boolEditor)
        self.stackedWidget.setCurrentWidget(self._parameterEditor)
        self.connect_layout()
        self.show_only_editor('parameter')

    def connect_layout(self):
        self.uiTypeSelect.currentIndexChanged.connect(self.on_selection_change)

    def show_only_editor(self, editor):
        self.current_editor = self._editors[editor]
        self.stackedWidget.setCurrentWidget(self.current_editor)
        self.current_editor.guess()

    def on_selection_change(self, index):
        new_editor = self.uiTypeSelect.currentText()
        self.show_only_editor(str(new_editor))
        #try:
        #    self.show_only_editor(new_editor)
        #except Error as e:
        #    print e
        #    print "Editor not implemented: {}".format(new_editor)
        

    def show_none(self):
        for editor in self._editors.keys():
            self._editors[editor].setVisible(False)

    def new_parameter(self, collection, parameter):
        self.current_collection = collection
        self.current_parameter = parameter
        name_string = collection + ', ' + parameter
        self.uiParameterName.setText(name_string)

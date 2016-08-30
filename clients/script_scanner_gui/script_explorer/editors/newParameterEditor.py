# new paramter editor

from PyQt4 import QtGui, QtCore

class newParameterEditor(QtGui.QWidget):

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
        

    def __init__(self, parent):
        super(newParameterEditor, self).__init__(parent)
        self.parent = parent
        self.setupLayout()

    def setupLayout(self):

        layout = QtGui.QVBoxLayout()

        self.select = QtGui.QComboBox()
        for t in self.types:
            self.select.addItem(t)

        layout.addWidget(self.select)
        self.setLayout(layout)
        
        

    

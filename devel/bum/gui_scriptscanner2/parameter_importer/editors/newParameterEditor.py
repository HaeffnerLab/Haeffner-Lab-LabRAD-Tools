# new paramter editor

from PyQt5 import QtCore, QtGui, QtWidgets

class newParameterEditor(QtWidgets.QWidget):

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

        layout = QtWidgets.QVBoxLayout()

        self.select = QtWidgets.QComboBox()
        for t in self.types:
            self.select.addItem(t)

        layout.addWidget(self.select)
        self.setLayout(layout)
        
        

    

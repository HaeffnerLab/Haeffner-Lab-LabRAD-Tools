import sys
from PyQt4 import QtGui

class TraceList(QtGui.QWidget):
    
    def __init__(self):
        super(TraceList, self).__init__()
        self.initUI()

    def initUI(self):
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.trace_dict = {}

    def addTrace(self, ident):

        cb = QtGui.QCheckBox(ident, self)
        cb.setChecked(True)
        self.trace_dict[ident] = cb
        self.layout.addWidget(cb)

    def removeTrace(self, ident):
        
        widget = self.trace_dict[ident]
        self.layout.removeWidget(widget)
        widget.deleteLater()
        widget = None

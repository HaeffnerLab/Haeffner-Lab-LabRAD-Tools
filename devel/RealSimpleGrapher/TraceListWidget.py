import sys
from PyQt4 import QtGui
from PyQt4 import QtCore

class TraceList(QtGui.QListWidget):
    def __init__(self):
        super(TraceList, self).__init__()
        self.initUI()

    def initUI(self):
        self.trace_dict = {}
        item = QtGui.QListWidgetItem('Traces')
        item.setCheckState(QtCore.Qt.Checked)

    def addTrace(self, ident):
        item = QtGui.QListWidgetItem(ident)
        item.setCheckState(QtCore.Qt.Checked)
        self.addItem(item)
        self.trace_dict[ident] = item

    def removeTrace(self, ident):
        item  = self.trace_dict[ident]
        row = self.row(item)
        self.takeItem(row)
        item = None


'''
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
'''

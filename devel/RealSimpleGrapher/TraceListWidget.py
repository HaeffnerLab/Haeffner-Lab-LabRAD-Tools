from PyQt4 import QtGui
from PyQt4 import QtCore
from ParameterListWidget import ParameterList

class TraceList(QtGui.QListWidget):
    def __init__(self, parent):
        super(TraceList, self).__init__()
        self.parent = parent
        self.windows = []
        self.initUI()

    def initUI(self):
        self.trace_dict = {}
        item = QtGui.QListWidgetItem('Traces')
        item.setCheckState(QtCore.Qt.Checked)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.popupMenu)

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

    def popupMenu(self, pos):
        menu = QtGui.QMenu()
        item = self.itemAt(pos)
        if (item == None): pass # didn't click on anything
        else:
            ident = str(item.text())
            parametersAction = menu.addAction('Parameters')
            action = menu.exec_(self.mapToGlobal(pos))
            
            if action == parametersAction:
                dataset = self.parent.artists[ident].dataset
                pl = ParameterList(dataset)
                self.windows.append(pl)
                pl.show()

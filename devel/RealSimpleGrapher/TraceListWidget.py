from PyQt4 import QtGui
from PyQt4 import QtCore
from ParameterListWidget import ParameterList
from DataVaultListWidget import DataVaultList
from GUIConfig import traceListConfig

class TraceList(QtGui.QListWidget):
    def __init__(self, parent):
        super(TraceList, self).__init__()
        self.parent = parent
        self.windows = []
        self.config = traceListConfig()
        self.setStyleSheet("background-color:%s;" % self.config.background_color)
	self.name = 'pmt'
        self.initUI()

    def initUI(self):
        self.trace_dict = {}
        item = QtGui.QListWidgetItem('Traces')
        item.setCheckState(QtCore.Qt.Checked)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.popupMenu)

    def addTrace(self, ident):
        item = QtGui.QListWidgetItem(ident)

        item.setForeground(QtGui.QColor(255, 255, 255))
        item.setBackground(QtGui.QColor(0, 0, 0))

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
        if (item == None): 
	    dataaddAction = menu.addAction('Add Data Set')
	    
	    action = menu.exec_(self.mapToGlobal(pos))
	    if action == dataaddAction:
		dvlist = DataVaultList(self.parent.name)
		self.windows.append(dvlist)
		dvlist.show()

        else:
	    ident = str(item.text())
            parametersAction = menu.addAction('Parameters')
            togglecolorsAction = menu.addAction('Toggle colors')

            action = menu.exec_(self.mapToGlobal(pos))
            
            if action == parametersAction:
                # option to show parameters in separate window
                dataset = self.parent.artists[ident].dataset
                pl = ParameterList(dataset)
                self.windows.append(pl)
                pl.show()

            if action == togglecolorsAction:               
                # option to change color of line
                new_color = self.parent.colorChooser.next()
                #self.parent.artists[ident].artist.setData(color = new_color, symbolBrush = new_color)
                if self.parent.show_points:
                    self.parent.artists[ident].artist.setData(pen = new_color, symbolBrush = new_color)
                else:
                    self.parent.artists[ident].artist.setData(pen = new_color)

                
               

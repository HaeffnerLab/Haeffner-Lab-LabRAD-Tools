from PyQt4 import QtGui, QtCore
from helper_widgets import dropdown

class table_dropdowns_with_entry(QtGui.QTableWidget):
    """
    this widgets consists of rows where each row is a frequency dropdown and an editable frequency field
    this is used for entering frequences of 729 lines into the drift tracker
    """
    def __init__(self, reactor, limits = (0,500), sig_figs = 4, names = [], entries = 2, suffix = '', favorites = {}, parent=None):
        super(table_dropdowns_with_entry, self).__init__(parent)
        self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.limits = limits
        self.favorites = favorites
        self.sig_figs = sig_figs
        self.names = names
        self.entries = entries
        self.suffix = suffix
        self.reactor = reactor
        self.initializeGUI()
        
    def initializeGUI(self):
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setColumnCount(2)
        self.setRowCount(self.entries)
        self.fill_out()
    
    def fill_out(self, names = None):
        if names is not None:
            self.names = names
        for i in range(self.entries):
            drop = dropdown(self.reactor, names = self.names, font=self.font, favorites = self.favorites)
            self.setCellWidget(i ,0 , drop)
            sample = QtGui.QDoubleSpinBox()
            sample.setFont(self.font)
            sample.setRange(*self.limits)
            sample.setDecimals(self.sig_figs)
            sample.setSingleStep(10**-self.sig_figs)
            sample.setSuffix(self.suffix)
            self.setCellWidget(i, 1, sample)
        for col in range(self.columnCount()):
            self.resizeColumnToContents(col)
        
    def resizeEvent(self, event):
        for col in range(self.columnCount()):
            self.resizeColumnToContents(col)

    def get_info(self):
        info = []
        for i in range(self.entries):
            dropdown = self.cellWidget(i, 0)
            index = dropdown.currentIndex()
            text = str(dropdown.itemData(index).toString())
            spin =  self.cellWidget( i, 1)
            val = spin.value()
            info.append((text, val))
        return info

    def closeEvent(self, x):
        self.reactor.stop()
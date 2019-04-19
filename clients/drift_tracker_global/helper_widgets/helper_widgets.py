from PyQt5 import QtWidgets, QtCore

class dropdown(QtGui.QComboBox):

    '''
    dropdown is a QComboBox used for selecting of 729 line names

    @param favorites: favorite is an optical parameter that's a replacement ditionary of the names that should be displayed
    i.e favorites = {'S-1/2D-1/2': 'best'} will show 'best' in the dropdown menu instead of 'S-1/2D-1/2'.
    '''

    new_selection = QtCore.pyqtSignal(str)

    def __init__(self, reactor, font = None, names = [], favorites = {}, initial_selection = None, info_position = None, only_show_favorites = False, parent = None ):
        super(dropdown, self).__init__(parent)
        self.reactor = reactor
        self.info_position = info_position
        self.selected = None
        self.favorites = favorites
        self.only_show_favorites = only_show_favorites
        self.initial_selection = initial_selection
        if font is not None:
            self.setFont(font)
        self.setInsertPolicy(QtGui.QComboBox.InsertAlphabetically)
        self.SizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.set_dropdown(names)
        self.currentIndexChanged[int].connect(self.on_user_selection)
        #select the item set in the config file
        if initial_selection is not None:
            self.set_selected(initial_selection)

    def set_selected(self, linename):
        '''
        set the selection by finding the entry where linename is saved as the stored data
        '''
        self.selected = linename
        index = self.findData(linename)
        #if the returned index is -1, then calling setCurrentIndex(-1) selects no items.
        self.blockSignals(True)
        self.setCurrentIndex(index)
        self.blockSignals(False)

    def set_favorites(self, favorites):
        self.favorites = favorites

    def on_user_selection(self,index):
        text = self.itemData(index).toString()
        self.selected = text
        self.new_selection.emit(text)

    def set_dropdown(self, info):
        self.blockSignals(True)
        for values in info:
            if self.info_position is not None:
                linename = values[self.info_position]
            else:
                linename = values
            display_name = self.favorites.get(linename, linename)
            #the name to be display is provided through the dictionary of favorites. if not in the dictionary display the name of the line.
            if not linename in self.favorites.keys() and self.only_show_favorites:
                #if linename was not in the favorites, and we are only showing the favorites, don't add the item
                pass
            else:
                #avoid dupilcates by checking if display_name is alrady in the dropdwon
                if self.findText(display_name) == -1:
                    self.addItem(display_name, userData = linename)
        if self.selected is not None:
            self.set_selected(self.selected)
        elif self.count():
            self.selected = self.itemData(1).toString()
        self.blockSignals(False)


class saved_frequencies_table(QtGui.QTableWidget):
    def __init__(self, reactor, sig_figs = 4, suffix = '', parent=None):
        super(saved_frequencies_table, self).__init__(parent)
        self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.sig_figs = sig_figs
        self.suffix = suffix
        self.reactor = reactor
        self.initializeGUI()

    def initializeGUI(self):
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setColumnCount(2)

    def fill_out_widget(self, info):
        self.setRowCount(len(info))
        form = '{' + '0:.{}f'.format(self.sig_figs) + '}' + ' {}'.format( self.suffix)
        for enum,tup in enumerate(info):
            name,val = tup
            val_name = form.format(val['MHz'])
            try:
                label = self.cellWidget(enum, 0)
                label.setText(name)
                sample = self.cellWidget(enum, 1)
                sample.setText(val_name)
            except AttributeError:
                label = QtGui.QTableWidgetItem(name)
                label.setFont(self.font)
                self.setItem(enum , 0 , label)
                sample = QtGui.QTableWidgetItem(val_name)
                sample.setFont(self.font)
                self.setItem(enum , 1 , sample)
        for col in range(self.columnCount()):
            self.resizeColumnToContents(col)

    def resizeEvent(self, event):
        for col in range(self.columnCount()):
            self.resizeColumnToContents(col)

    def closeEvent(self, x):
        self.reactor.stop()

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    from common.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = saved_frequencies_table(reactor)
    widget.show()
    reactor.run()

from PyQt4 import QtGui, QtCore
from common.clients.control_729 import qt4reactor
from helper_widgets import dropdown
   
class line_selector_table(QtGui.QTableWidget):
    
    line_selector_new_selection = QtCore.pyqtSignal(list)
    
    def __init__(self, reactor, sideband_titles = ['radial 1','radial 2', 'axial', 'micromotion'], max_sideband_input = 3, max_rows = 1, input_font = None, only_show_favorites = False, parent = None):
        super(line_selector_table, self).__init__(parent)
        self.reactor = reactor
        self.only_show_favorites = only_show_favorites
        self.max_rows = max_rows
        self.setColumnCount(len(sideband_titles) + 1)
        self.sideband_titles = sideband_titles
        self.max_sideband_input = max_sideband_input
        self.d = {} #dictionary in the form (row , sideband_name) : combobox
        self.input_font = input_font
        if self.input_font is None:
            self.input_font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.sideband_count = None
        self.favorites = None
        self.dropdown_info = None
        self.setup_layout()

    def setup_layout(self):
        self.verticalHeader().hide()
        labels = ['line']
        labels.extend(self.sideband_titles)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.setHorizontalHeaderLabels(labels)
        self.setShowGrid(False)   

    def do_add_row(self):
        if self.rowCount() > self.max_rows + 1:
                message = QtGui.QMessageBox()
                message.setText("Too many rows")
                message.exec_()
                return
        self.setRowCount(self.rowCount()  + 1)
        line_dropdown = dropdown(self.reactor, font = self.input_font, info_position = 0, only_show_favorites = self.only_show_favorites)
        line_dropdown.new_selection.connect(self.on_user_modified)
        if self.favorites is not None:
            line_dropdown.set_favorites(self.favorites)
        if self.dropdown_info is not None:
            line_dropdown.set_dropdown(self.dropdown_info)
        self.setCellWidget(self.rowCount() - 1, 0, line_dropdown)
        for num,title in enumerate(self.sideband_titles):
            combo = QtGui.QComboBox()
            self.d[self.rowCount() - 1, title] = combo
            combo.setFont(self.input_font)
            for i in range(-self.max_sideband_input, self.max_sideband_input + 1):
                entry_text = self.number_formatter(i)
                combo.addItem(entry_text)
                combo.setCurrentIndex(self.max_sideband_input) #setting active entry to '0'
            self.setCellWidget(self.rowCount() - 1, num + 1, combo)
            combo.currentIndexChanged.connect(self.on_user_modified)
        self.adjustSize()
        self.resizeColumnsToContents()

    
    def add_row(self):
        self.do_add_row()
        self.on_user_modified(None)
    
    def remove_row(self):
        row_count = self.rowCount()
        if row_count > 1:
            self.removeRow(row_count-1)
            self.on_user_modified(None)
    
    def sizeHint(self):
        width = 0
        for i in range(self.columnCount()):
            width += self.columnWidth(i)
        height = 0
        for i in range(self.rowCount()):
            height += 50
        return QtCore.QSize(width, height)
    
    def on_user_modified(self, x):
        info = self.get_info()
        self.line_selector_new_selection.emit(info)
    
    def get_info(self):
        '''
        reconstructs the current settings in a format that can be saved
        '''
        info = []
        for row in range(self.rowCount()):
            value = self.cellWidget(row, 0).selected
            info.append(('line',str(value)))
            for col in range(1, self.columnCount()):
                name = self.horizontalHeaderItem(col).text()
                value = self.cellWidget(row, col).currentText()
                info.append((str(name),int(value)))
        return info
        
    def number_formatter(self, num):
        if num < 0:
            fmt = '{0}'
        elif num > 0:
            fmt = '+{0}'
        else:
            fmt = '0'
        return fmt.format(num)
    
    def set_favorites(self, favortes):
        '''
        set favorites for every existing row
        '''
        for row in range(self.rowCount()):
            if row > self.rowCount():
                self.add_row()
            widget = self.cellWidget(row, 0)
            widget.set_favorites(favortes)
        self.favorites = favortes
    
    def set_dropdown_lines(self, info):
        for row in range(self.rowCount()):
            if row > self.rowCount():
                self.add_row()
            widget = self.cellWidget(row, 0)
            widget.set_dropdown(info)
        self.dropdown_info = info
    
    def set_selected(self, info):
        row = -1
        for name,value in info:
            if name == 'line':
                row += 1
                column  = 1
                if row + 1 >  self.rowCount():
                    self.do_add_row()
                self.cellWidget(row, 0).set_selected(value)
            else:
                self.select_sideband_dropdown(row, column, value)
                column += 1
        if row + 1 < self.rowCount():
            self.removeRow(self.rowCount()-1)
    
    def select_sideband_dropdown(self, row, col, value):
        sideband_dropdown = self.cellWidget(row, col)
        index = sideband_dropdown.findText(self.number_formatter(value))
        sideband_dropdown.blockSignals(True)
        sideband_dropdown.setCurrentIndex(index)
        sideband_dropdown.blockSignals(False)
    
    def closeEvent(self, x):
        self.reactor.stop()

class line_selector_widget(QtGui.QWidget):
    
    on_user_modified = QtCore.pyqtSignal(list)
    
    def __init__(self, reactor, expandable = False, input_font = None, only_show_favorites = False):
        super(line_selector_widget, self).__init__()
        self.reactor = reactor
        self.only_show_favorites = only_show_favorites
        self.input_font = input_font
        if self.input_font is None:
            self.input_font = QtGui.QFont('MS Shell Dlg 2',pointSize=10)
        self.expandable = expandable
        self.setup_layout()
        self.connect_layout()
        
    def setup_layout(self):
        layout = QtGui.QGridLayout()
        self.table = line_selector_table(self.reactor, only_show_favorites = self.only_show_favorites)
        layout.addWidget(self.table, 0, 0, 2, 1)
        if self.expandable:
            add_button = QtGui.QPushButton('Add')
            add_button.setFont(self.input_font)
            remove_button = QtGui.QPushButton('Remove')
            remove_button.setFont(self.input_font)
            add_button.pressed.connect(self.table.add_row)
            remove_button.pressed.connect(self.table.remove_row)
            layout.addWidget(add_button, 0, 1, 1, 1)
            layout.addWidget(remove_button, 1, 1, 1, 1)
        self.setLayout(layout)
    
    def connect_layout(self):
        self.table.line_selector_new_selection.connect(self.on_user_modified.emit)
    
    def set_favorites(self, favorites):
        self.table.set_favorites(favorites)
    
    def set_dropdown(self, lineinfo):
        self.table.set_dropdown_lines(lineinfo)
    
    def set_selected(self, info):
        self.table.set_selected(info)
        
    def closeEvent(self, x):
        self.reactor.stop()
    
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    qt4reactor.install()
    from twisted.internet import reactor
    widget = line_selector_widget(reactor, 3)
    widget.show()
    reactor.run()
from PyQt4 import QtGui, QtCore
 
class progress_bar(QtGui.QProgressBar):
    def __init__(self, reactor, parent=None):
        super(progress_bar, self).__init__(parent)
        self.reactor = reactor
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.set_status('', 0.0)
    
    def set_status(self, status_name, percentage):
        self.setValue(percentage)
        self.setFormat('{0} %p%'.format(status_name))

    def closeEvent(self, x):
        self.reactor.stop()

class fixed_width_button(QtGui.QPushButton):
    def __init__(self, text, size):
        super(fixed_width_button, self).__init__(text)
        self.size = size
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
    
    def sizeHint(self):
        return QtCore.QSize(*self.size)
        
class script_status_widget(QtGui.QWidget):
    
    on_pause = QtCore.pyqtSignal()
    on_continue = QtCore.pyqtSignal()
    on_stop = QtCore.pyqtSignal()
    
    def __init__(self, reactor, ident, name , font = None, parent = None):
        super(script_status_widget, self).__init__(parent)
        self.reactor = reactor
        self.ident = ident
        self.name = name
        self.parent = parent
        self.font = QtGui.QFont(self.font().family(), pointSize=10)
        if self.font is None:
            self.font = QtGui.QFont()
        self.setup_layout()
        self.connect_layout()
        self.finished = False
    
    def setup_layout(self):
        layout = QtGui.QHBoxLayout()
        self.id_label = QtGui.QLabel('{0}'.format(self.ident))
        self.id_label.setFont(self.font)
        self.id_label.setMinimumWidth(30)
        self.id_label.setAlignment(QtCore.Qt.AlignCenter)
        self.id_label.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.name_label = QtGui.QLabel(self.name)
        self.name_label.setFont(self.font)
        self.name_label.setAlignment(QtCore.Qt.AlignLeft)
        self.name_label.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        self.name_label.setMinimumWidth(150)
        self.progress_bar = progress_bar(self.reactor, self.parent)
        self.pause_button = fixed_width_button("Pause", (75,23))
        self.stop_button = fixed_width_button("Stop", (75,23))
        layout.addWidget(self.id_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)
    
    def connect_layout(self):
        self.stop_button.pressed.connect(self.on_user_stop)
        self.pause_button.pressed.connect(self.on_user_pause)
        
    def on_user_pause(self):
        if self.pause_button.text() == 'Pause':
            self.on_pause.emit()
        else:
            self.on_continue.emit()
    
    def on_user_stop(self):
        self.on_stop.emit()
    
    def set_paused(self, is_paused):
        if is_paused:
            self.pause_button.setText('Continue')
        else:
            self.pause_button.setText('Pause')
    
    def set_status(self, status, percentage):
        self.progress_bar.set_status(status, percentage)
        
    def closeEvent(self, x):
        self.reactor.stop()

class running_scans_list(QtGui.QTableWidget):
    
    on_pause = QtCore.pyqtSignal(int, bool)
    on_stop = QtCore.pyqtSignal(int)
    
    def __init__(self, reactor, font = None, parent = None):
        super(running_scans_list, self).__init__(parent)
        self.reactor = reactor
        self.parent = parent
        self.font = font
        if self.font is None:
            self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.setupLayout()
        self.d = {}
        self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.mapper_pause = QtCore.QSignalMapper()
        self.mapper_pause.mapped.connect(self.emit_pause)
        self.mapper_continue = QtCore.QSignalMapper()
        self.mapper_continue.mapped.connect(self.emit_continue)
        self.mapper_stop = QtCore.QSignalMapper()
        self.mapper_stop.mapped.connect(self.on_stop.emit)
    
    def emit_pause(self, ident):
        self.on_pause.emit(ident, True)
    
    def emit_continue(self, ident):
        self.on_pause.emit(ident, False)
    
    def setupLayout(self):
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.setColumnCount(1)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
    
    def add(self, ident, name):
        ident = int(ident)
        row_count = self.rowCount()
        self.setRowCount(row_count + 1)
        widget = script_status_widget(self.reactor, parent = self.parent, ident = ident, name = name)
        #set up signal mapping
        self.mapper_continue.setMapping(widget, ident)
        widget.on_continue.connect(self.mapper_continue.map)
        self.mapper_stop.setMapping(widget, ident)
        widget.on_stop.connect(self.mapper_stop.map)
        self.mapper_pause.setMapping(widget, ident)
        widget.on_pause.connect(self.mapper_pause.map)
        #insert widget
        self.setCellWidget(row_count, 0, widget)
        self.resizeColumnsToContents()
        self.d[ident] = widget
    
    def set_status(self, ident, status, percentage):
        try:
            widget = self.d[ident]
        except KeyError:
            print "trying set status of experiment that's not there"
        else:
            widget.set_status(status, percentage)
    
    def set_paused(self, ident, is_paused):
        try:
            widget = self.d[ident]
        except KeyError:
            print "trying set pause experiment that's not there"
        else:
            widget.set_paused(is_paused)
            
    def remove(self, ident):
        widget = self.d[ident]
        for row in range(self.rowCount()):
            if self.cellWidget(row, 0) == widget:
                del self.d[ident]
                self.removeRow(row)
    
    def sizeHint(self):
        width = 0
        for i in range(self.columnCount()):
            width += self.columnWidth(i)
        height = 0
        for i in range(self.rowCount()):
            height += self.rowHeight(i)
        return QtCore.QSize(width, height)

    def finish(self, ident):
        try:
            self.remove(ident)
        except KeyError:
            print "trying remove experiment {0} that's not there".format(ident)
                  
    def closeEvent(self, x):
        self.reactor.stop()
        
class running_combined(QtGui.QWidget):
    def __init__(self, reactor, font = None, parent = None):
        super(running_combined, self).__init__(parent)
        self.reactor = reactor
        self.parent = parent
        self.font = font
        if self.font is None:
            self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.setupLayout()

    def clear_all(self):
        self.scans_list.clear()
    
    def setupLayout(self):
        layout = QtGui.QGridLayout()
        title = QtGui.QLabel("Running", font = self.font)
        title.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        title.setAlignment(QtCore.Qt.AlignLeft)
        self.scans_list = running_scans_list(self.reactor, self.parent)
        layout.addWidget(title, 0, 0, 1, 3 )
        layout.addWidget(self.scans_list, 1, 0, 3, 3 )
        self.setLayout(layout)
    
    def add(self, ident, name):
        self.scans_list.add(ident, name)
    
    def set_status(self, ident, status, percentage):
        self.scans_list.set_status(ident, status, percentage)
    
    def paused(self, ident, is_paused):
        self.scans_list.set_paused(ident, is_paused)
    
    def finish(self, ident):
        self.scans_list.finish(ident)
    
    def closeEvent(self, x):
        self.reactor.stop()
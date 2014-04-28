from PyQt4 import QtCore, QtGui, uic
import os

basepath =  os.path.dirname(__file__)
path = os.path.join(basepath, "qtui","plot_window.ui")
base, form = uic.loadUiType(path)

class DatasetList(base, form):
    '''
    class for keeping track of the list of plotted datasets
    '''
    on_dataset_checked = QtCore.pyqtSignal(str, bool)
    on_context_menu_selected = QtCore.pyqtSignal(str, int)
    
    removeDataset = 0
    changeColor = 1
    showParameters = 2
    doFit = 3
    moveWindow = 4
    
    def __init__(self):
        super(DatasetList, self).__init__()
        self.setupUi(self)
        self.check_mapper = QtCore.QSignalMapper()
        self.selection_widget.setColumnCount(2)
        self.selection_widget.setRowCount(0)
        self.selection_widget.setColumnWidth(0,25)
        self.selection_widget.setColumnWidth(1,300)
        self.connect_layout()
    
    def connect_layout(self):
        self.check_mapper.mapped.connect(self._dataset_checked)
    
    def _dataset_checked(self, row):
        name = self.selection_widget.cellWidget(row, 1).text()
        state = self.selection_widget.cellWidget(row, 0).isChecked()
        self.on_dataset_checked.emit(name, state)

    def add_dataset(self, dataset):
        '''
        appends the new dataset to the list
        '''
        name = dataset.datasetName
        row = self.selection_widget.rowCount()
        self.selection_widget.setRowCount(row + 1)
        widget = QtGui.QCheckBox()
        widget.setCheckable(True)
        widget.setChecked(True)
        self.check_mapper.setMapping(widget, row)
        widget.stateChanged.connect(self.check_mapper.map)
        self.selection_widget.setRowHeight(row, 20)
        self.selection_widget.setCellWidget(row, 0, widget)
        label = context_menu_label(name)
        self.selection_widget.setCellWidget(row, 1, label)
        label.context_menu_selected.connect(self.on_context_menu_selected.emit)
    
class context_menu_label(QtGui.QLabel):
    
    context_menu_selected = QtCore.pyqtSignal(str, int)
    
    def __init__(self, name):
        super(context_menu_label, self).__init__(name)
        self.name = name
        self.setAlignment(QtCore.Qt.AlignLeft)
        
    def contextMenuEvent(self, event):
        menu = QtGui.QMenu()
        remove = menu.addAction('Remove')
        change_color = menu.addAction('Change Color')
        show_params = menu.addAction('Show Parameters')
        fit = menu.addAction('Fit')
        move = menu.addAction('Move')
        action = menu.exec_(self.mapToGlobal(QtCore.QPoint(0,20)))
        if action == remove:
            self.context_menu_selected.emit(self.name, DatasetList.removeDataset)
        elif action == change_color:
            self.context_menu_selected.emit(self.name, DatasetList.changeColor)
        elif action == show_params:
            self.context_menu_selected.emit(self.name, DatasetList.showParameters)
        elif action == fit:
            self.context_menu_selected.emit(self.name, DatasetList.doFit)
        elif action == move:
            self.context_menu_selected.emit(DatasetList.moveWindow)

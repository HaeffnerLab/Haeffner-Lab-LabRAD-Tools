from PyQt4 import QtCore, QtGui, uic
import sys
from Data import Node, ParameterNode, CollectionNode, ScanNode
from Models import ParametersTreeModel
from PropertiesEditor import PropertiesEditor
import os

basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"..","Views", "ParametersEditor.ui")
base, form = uic.loadUiType(path)

class ParametersEditor(base, form):
    
    on_parameter_change = QtCore.pyqtSignal(tuple, tuple)
    
    def __init__(self, reactor, parent=None):
        super(base, self).__init__(parent)
        self.reactor = reactor
        self.setupUi(self)
        self._rootNode = None
        self.setup_model()
        self.connect_layout()
        self._collection = {}
        self._parameter = {}
        self._hidden = []
    
    def clear_all(self):
        'clears all parameters'
        self._model.clear_model()
        self._collection = {}
        self._parameter = {}
        self._hidden = []
    
    def add_collection_node(self, name):
        node = self._model.insert_collection(name)
        self._collection[name] = node
    
    def add_parameter(self, collection_name, parameter_name, value):
        value_type = value[0]
        info = value[1]
        if value_type == 'parameter':
            collection_node = self._collection[collection_name]
            node = self._model.insert_parameter(parameter_name, info, collection_node)
            self._parameter[collection_name, parameter_name]= node
        elif value_type == 'scan':
            collection_node = self._collection[collection_name]
            node = self._model.insert_scan(parameter_name, info, collection_node)
            self._parameter[collection_name, parameter_name]= node
        else:
            print 'unknown value type', value_type
    
    def set_parameter(self, collection, name, full_info):
        '''set value of a parameter stores in the model'''
        index =  self._parameter[collection,name]
        self._model.set_parameter(index, full_info[1])
    
    def show_only(self, show):
        ''' set all parameters hidden except for the ones provided in show'''
        self.show_all()
        for collection, collection_index in self._collection.iteritems():
            keepCollection = False
            collection_node = collection_index.internalPointer()
            for row in range(collection_node.childCount()):
                child = collection_node.child(row)
                parameter = child.name()
                if not (collection, parameter) in show:
                    parameter_index = self._model.index(row, 0, collection_index )
                    parent_index = self._proxyModel.mapFromSource(collection_index)
                    parameter_index_proxy = self._proxyModel.mapFromSource(parameter_index)
                    self.uiTree.setRowHidden(parameter_index_proxy.row() ,parent_index, True)
                    self._hidden.append((parameter_index_proxy.row(), parent_index))
                else:
                    keepCollection = True
            if not keepCollection:
                #hiding the collection too
                parent_index = self._proxyModel.mapFromSource(collection_index.parent())
                row = collection_index.internalPointer().row()
                collection_index = self._model.index(row, 0, collection_index.parent())
                collection_indexx_proxy = self._proxyModel.mapFromSource(collection_index)
                self.uiTree.setRowHidden(collection_indexx_proxy.row() ,parent_index, True)
                self._hidden.append((collection_indexx_proxy.row(), parent_index))
        self.uiTree.expandAll()
        
    def show_all(self):
        '''show all hidden parameters'''
        while True:
            try:
                row, parent_index = self._hidden.pop()
            except IndexError:
                return
            else:
                self.uiTree.setRowHidden(row ,parent_index, False)
    
    def setup_model(self): 
        self._rootNode   = Node("Root")
        self._proxyModel = QtGui.QSortFilterProxyModel(self)
        self._model = ParametersTreeModel(self._rootNode, self)
        self._proxyModel.setSourceModel(self._model)
        #filtering
        self._proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._proxyModel.setFilterRole(ParametersTreeModel.filterRole)
        self._proxyModel.setFilterKeyColumn(-1) #look at all columns while filtering
        #sorting
        self.uiTree.setSortingEnabled(True)
        self._proxyModel.setDynamicSortFilter(True)
        self._proxyModel.setSortRole(QtCore.Qt.DisplayRole)
        self._proxyModel.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.uiTree.sortByColumn(0, QtCore.Qt.AscendingOrder)
        #making and setting model
        self.uiTree.setModel(self._proxyModel)
        self._propEditor = PropertiesEditor(self)
        self.layout().addWidget(self._propEditor)
        self._propEditor.setModel(self._proxyModel)
    
    def connect_layout(self):
        self.uiFilter.textChanged.connect(self._proxyModel.setFilterRegExp)
        self.uiTree.selectionModel().currentChanged.connect(self._propEditor.setSelection)
        self._model.on_new_parameter.connect(self.on_parameter_change.emit)

    def closeEvent(self, event):
        try:
            self.on_parameter_change.disconnect()
        except TypeError:
            pass
        self.reactor.stop()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wnd = ParametersEditor()
    wnd.show()
    sys.exit(app.exec_())
from PyQt4 import QtCore, QtGui, uic
import sys
from Data import Node, ParameterNode, CollectionNode, ScanNode
from Models import ParametersTreeModel
from PropertiesEditor import PropertiesEditor
    
base, form = uic.loadUiType("Views/ParametersEditor.ui")

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
        index =  self._parameter[collection,name]
        self._model.set_parameter(index, full_info[1])
#        self.uiTree.expandAll()
#        self.uiTree.selectionModel().select(self._proxyModel.mapFromSource(index), self.uiTree.selectionModel().Select)
    
    def setup_model(self): 
#        self.uiTree.setSortingEnabled(True)
        self._rootNode   = Node("Root")
        self._proxyModel = QtGui.QSortFilterProxyModel(self)
        self._model = ParametersTreeModel(self._rootNode, self)
        self._proxyModel.setSourceModel(self._model)
        self._proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._proxyModel.setFilterRole(ParametersTreeModel.filterRole)
        self._proxyModel.setFilterKeyColumn(-1) #look at all columns while filtering
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
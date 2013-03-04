from PyQt4 import QtCore, uic
from Data import Node, ParameterNode, CollectionNode, ScanNode, SidebandElectorNode
from FilterModel import FilterModel
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
        self._scannable_parameter = {}
        self._parameter = {}
    
    def clear_all(self):
        'clears all parameters'
        self._model.clear_model()
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
            self._scannable_parameter[collection_name, parameter_name] = node
        elif value_type == 'scan':
            collection_node = self._collection[collection_name]
            node = self._model.insert_scan(parameter_name, info, collection_node)
            self._parameter[collection_name, parameter_name]= node
        elif value_type == 'bool':
            collection_node = self._collection[collection_name]
            node = self._model.insert_bool(parameter_name, info, collection_node)
            self._parameter[collection_name, parameter_name]= node
        elif value_type == 'string':
            collection_node = self._collection[collection_name]
            node = self._model.insert_string(parameter_name, info, collection_node)
            self._parameter[collection_name, parameter_name]= node
        elif value_type == 'selection_simple':
            collection_node = self._collection[collection_name]
            node = self._model.insert_selection_simple(parameter_name, info, collection_node)
            self._parameter[collection_name, parameter_name]= node
        elif value_type == 'line_selection':
            collection_node = self._collection[collection_name]
            node = self._model.insert_line_selection(parameter_name, info, collection_node)
            self._parameter[collection_name, parameter_name]= node
        elif value_type == 'sideband_selection':
            collection_node = self._collection[collection_name]
            node = self._model.insert_sideband_selection(parameter_name, info, collection_node)
            self._parameter[collection_name, parameter_name]= node
        elif value_type == 'duration_bandwidth':
            collection_node = self._collection[collection_name]
            node = self._model.insert_duration_bandwidth(parameter_name, info, collection_node)
            self._parameter[collection_name, parameter_name]= node
        elif value_type == 'spectrum_sensitivity':
            collection_node = self._collection[collection_name]
            node = self._model.insert_spectrum_sensitivity(parameter_name, info, collection_node)
            self._parameter[collection_name, parameter_name]= node
        else:
            print 'unknown value type', value_type, collection_name, parameter_name
    
    def set_parameter(self, collection, name, full_info):
        '''set value of a parameter stores in the model'''
        index =  self._parameter[collection,name]
        self._model.set_parameter(index, full_info[1])
    
    def show_only(self, show):
        ''' set all parameters hidden except for the ones provided in show'''
        self._proxyModel.show_only(show)
    
    def show_all(self):
        '''show all hidden parameters'''
        self._proxyModel.show_all()

    def get_scannable_parameters(self):
        scannable = []
        for (collection,param), index in self._scannable_parameter.iteritems():
            if (collection,param) in self._proxyModel.shown():
                parameter_node = index.internalPointer()
                minim = parameter_node.data(3)
                maxim = parameter_node.data(4)
                units = parameter_node.data(6)
                scannable.append((collection,param, minim, maxim, units))
        return scannable
    
    def setup_model(self): 
        self._rootNode   = Node("Root")
        self._proxyModel = FilterModel(self)
        self._model = ParametersTreeModel(self._rootNode, self)
        self._proxyModel.setSourceModel(self._model)
        self._proxyModel.setFilterRole(ParametersTreeModel.filterRole)
        self._proxyModel.setSortRole(QtCore.Qt.DisplayRole)
        self.uiTree.setSortingEnabled(True)
        self.uiTree.sortByColumn(0, QtCore.Qt.AscendingOrder)
        #making and setting model
        self.uiTree.setModel(self._proxyModel)
        self._propEditor = PropertiesEditor(self)
        self.layout().addWidget(self._propEditor)
        self._propEditor.setModel(self._proxyModel)
    
    def connect_layout(self):
        self.uiFilter.textChanged.connect(self._proxyModel.setFilterWildcard)
        self.uiTree.selectionModel().currentChanged.connect(self._propEditor.setSelection)
        self._model.on_new_parameter.connect(self.on_parameter_change.emit)

    def closeEvent(self, event):
        try:
            self.on_parameter_change.disconnect()
        except TypeError:
            pass
        self.reactor.stop()
from PyQt5 import QtCore
from .Data import ParameterNode, CollectionNode, ScanNode, BoolNode
from .Data import StringNode, SelectionSimpleNode, LineSelectionNode, SidebandElectorNode, SidebandElectorSpacetimeNode, SidebandElectorSpacetime2Node
from .Data import DurationBandwidthNode, SpectrumSensitivityNode
from .Data import UndefinedParameterNode

class ParametersTreeModel(QtCore.QAbstractItemModel):
    
    filterRole  = QtCore.Qt.UserRole
    on_new_parameter = QtCore.pyqtSignal(tuple, tuple)
    
    def __init__(self, root, parent=None):
        super(ParametersTreeModel, self).__init__(parent)
        self._rootNode = root
        
    def rowCount(self, parent):
        '''
        returns the count
        '''
        if not parent.isValid():
            parentNode = self._rootNode
        else:
            parentNode = parent.internalPointer()
        return parentNode.childCount()

    def columnCount(self, parent):
        return 2
        
    def data(self, index, role):
        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return node.data(index.column())
        
        if role == ParametersTreeModel.filterRole:
            return node.filter_text()

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if index.isValid():
            node = index.internalPointer()
            if role == QtCore.Qt.EditRole:
                node.setData(index.column(), value)
                textIndex = self.createIndex(index.row(), 1, index.internalPointer())
                self.dataChanged.emit(index, index)
                self.dataChanged.emit(textIndex, textIndex)
                if not isinstance(node, CollectionNode):
                    self.on_new_parameter.emit(node.path(), node.full_parameter())
                return True
        return False

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if section == 0:
                return "Collection"
            else:
                return "Value"

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def parent(self, index):      
        '''
        returns the index of the parent of the node at the given index
        '''
        node = self.getNode(index)
        parentNode = node.parent()
        if parentNode == self._rootNode:
            return QtCore.QModelIndex()
        return self.createIndex(parentNode.row(), 0, parentNode)
        
    def index(self, row, column, parent): 
        '''
        returns the index for the given parent, row and column
        '''
        parentNode = self.getNode(parent)
        childItem = parentNode.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def getNode(self, index):
        '''
        returns node of the given index
        '''
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node            
        return self._rootNode

    def insert_collection(self, name, parent_index=QtCore.QModelIndex()):
        parentNode = self.getNode(parent_index)
        row_count = self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = CollectionNode(name, parentNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_parameter(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = ParameterNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index

    def insert_scan(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = ScanNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_bool(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = BoolNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_string(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = StringNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_selection_simple(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = SelectionSimpleNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_line_selection(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = LineSelectionNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index

    def insert_sideband_selection(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = SidebandElectorNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_sideband_selection_spacetime(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = SidebandElectorSpacetimeNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_sideband_selection_spacetime_2(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = SidebandElectorSpacetime2Node(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index

    def insert_duration_bandwidth(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = DurationBandwidthNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_spectrum_sensitivity(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = SpectrumSensitivityNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_undefined_parameter(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = UndefinedParameterNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index

    def set_parameter(self, index, info):
        node = index.internalPointer()
        node.set_full_info(info)
        self.dataChanged.emit(index, index)
#        NOTICE: Below is original function definition. (index, max_index) changed to (index, index). This results in speed-up.
#           If you ever feel that the GUI is out of control and it starting to lie to you about parameters, it is probably
#           because of this.
#
#    def set_parameter(self, index, info):
#        node = index.internalPointer()
#        node.set_full_info(info)
#        #refresh all columns
#        max_index= self.createIndex(index.row(), node.columns, index.internalPointer())
#        t0 = time.time()
#        self.dataChanged.emit(index, max_index) #THIS LINE IS THE CULPRIT
#        t1 = time.time()
#        print('{:.3g} s to set parameter'.format(t1-t0))

    def clear_model(self):
        rows = self._rootNode.childCount()
        self.beginRemoveRows(QtCore.QModelIndex(), 0, rows)
        self._rootNode.clear_data()
        self.endRemoveRows()

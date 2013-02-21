from PyQt4 import QtCore, QtGui
from Data import ParameterNode, CollectionNode, ScanNode

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
                print 'in setting data'
                if not isinstance(node, CollectionNode):
                    print 'emitting signal out'
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

    def insert_collection(self, name, parent=QtCore.QModelIndex()):
        parentNode = self.getNode(parent)
        self.beginInsertRows(parent, 0, 0)
        childNode = CollectionNode(name)
        parentNode.insertChild(0, childNode)
        self.endInsertRows()
        #get index of the newly inserted collection and return it
        index = self.index(0, 0, parent)
        return index
    
    def insert_parameter(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        self.beginInsertRows(parent_index, 0, 0)
        childNode = ParameterNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(0, 0, parent_index)
        return index

    def insert_scan(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        self.beginInsertRows(parent_index, 0, 0)
        childNode = ScanNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(0, 0, parent_index)
        return index
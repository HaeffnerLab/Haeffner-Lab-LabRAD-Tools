class Node(object):
    def __init__(self, name, parent=None): 
        super(Node, self).__init__()
        from labrad.units import WithUnit
        self.WithUnit = WithUnit
        self._name = name
        self._children = []
        self._parent = parent
        if parent is not None:
            parent.addChild(self)

    def addChild(self, child):
        self._children.append(child)
        child._parent = self

    def insertChild(self, position, child):
        if position < 0 or position > len(self._children):
            return False
        
        self._children.insert(position, child)
        child._parent = self
        return True

    def removeChild(self, position):
        if position < 0 or position > len(self._children):
            return False
        child = self._children.pop(position)
        child._parent = None
        return True

    def name(self):
        return self._name
    
    def filter_text(self):
        return self.name()

    def child(self, row):
        try:
            return self._children[row]
        except IndexError:
            return None
    
    def childCount(self):
        return len(self._children)

    def parent(self):
        return self._parent
    
    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)

    def data(self, column):
        if column is 0: return self.name()
    
    def setData(self, column, value):
        pass

class CollectionNode(Node):
    def __init__(self, name, parent = None):
        super(CollectionNode, self).__init__(name, parent)
    
class ParameterNode(Node):
    
    columns = 6
    
    def __init__(self, name, info, parent=None):
        super(ParameterNode, self).__init__(name, parent)
        self._collection = parent.name()
        self.set_full_info(info)
        
    def set_full_info(self, info):
        self._units = info[2].units
        self._min = info[0][self._units]
        self._max = info[1][self._units]
        self._value = info[2][self._units]
    
    def path(self):
        return (self._collection, self.name())

    def full_parameter(self):
        WithUnit = self.WithUnit
        return ('parameter', [WithUnit(self._min, self._units), WithUnit(self._max, self._units), WithUnit(self._value, self._units)])
    
    def data(self, column):
        if column < 1:
            return super(ParameterNode, self).data(column)
        elif column == 1:
            return self.string_format()
        elif column == 2:
            return self._collection
        elif column == 3:
            return self._min
        elif column == 4:
            return self._max
        elif column == 5:
            return self._value
        elif column == 6:
            return self._units
    
    def filter_text(self):
        return self.parent().name() + self.name()
    
    def string_format(self):
        return '{0} {1}'.format(self._value, self._units)
        
    def setData(self, column, value):
        value = value.toPyObject()
        if column == 3:
            self._min = value
        elif column == 4:
            self._max = value
        elif column == 5:
            self._value = value
        elif column == 6:
            self._units = value

class ScanNode(Node):
    
    columns = 8
    
    def __init__(self, name, info, parent=None):
        super(ScanNode, self).__init__(name, parent)
        self._collection = parent.name()
        self.set_full_info(info)
    
    def set_full_info(self, info):
        limit_info, scan_info = info
        self._units = limit_info[0].units
        self._min = limit_info[0][self._units]
        self._max = limit_info[1][self._units]
        self._scan_start = scan_info[0][self._units]
        self._scan_stop = scan_info[1][self._units]
        self._scan_points = scan_info[2]
    
    def path(self):
        return (self._collection, self.name())
    
    def full_parameter(self):
        WithUnit = self.WithUnit
        return ('scan', ([WithUnit(self._min, self._units), WithUnit(self._max, self._units) ],
                         (WithUnit(self._scan_start, self._units), WithUnit(self._scan_stop, self._units), self._scan_points)
                         ))    
    def data(self, column):
        if column < 1:
            return super(ScanNode, self).data(column)
        elif column == 1:
            return self.string_format()
        elif column == 2:
            return self._collection
        elif column == 3:
            return self._min
        elif column == 4:
            return self._max
        elif column == 5:
            return self._scan_start
        elif column == 6:
            return self._scan_stop
        elif column == 7:
            return self._scan_points
        elif column == 8:
            return self._units

    def filter_text(self):
        return self.parent().name() + self.name()
    
    def string_format(self):
        return 'Scan {0} {3} to {1} {3} in {2} steps'.format(self._scan_start, self._scan_stop, self._scan_points, self._units)
        
    def setData(self, column, value):
        value = value.toPyObject()
        if column == 3:
            self._min = value
        elif column == 4:
            self._max = value
        elif column == 5:
            self._scan_start = value
        elif column == 6:
            self._scan_stop = value
        elif column == 7:
            self._scan_points = value
        elif column == 8:
            self._units = value
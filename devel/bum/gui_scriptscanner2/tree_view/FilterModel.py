from PyQt5 import QtCore

try:
    QString = unicode
except NameError:
    # Python 3
    QString = str

class FilterModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent):
        super(FilterModel, self).__init__(parent)
        #filtering
        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setFilterKeyColumn(-1) #look at all columns while filtering
        #sorting
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._show_only = []
    
    def filterAcceptsRow(self, row, index):
        model_index = self.sourceModel().index(row, 0, index)
        filter_text = QString(self.sourceModel().data(model_index, self.filterRole()))
        contains_filter = self.filterRegExp().pattern() in filter_text #old python2 code for this line: contains_filter = filter_text.contains(self.filterRegExp())
        in_show_only = self._is_in_show_only(filter_text)
        return contains_filter and in_show_only
    
    def _is_in_show_only(self, filter_text):
        if not len(self._show_only): return True
        for collection,parameter in self._show_only:
            if collection+parameter in filter_text: return True #old python2 code for this line: if filter_text.contains(collection+parameter): return True 
        return False
    
    def filterAcceptsColumn(self, column, index):
        return True
    
    def show_only(self, show):
        self._show_only = show
        self.invalidateFilter()
        
    def show_all(self):
        self._show_only = []
        self.invalidateFilter()
    
    def shown(self):
        return self._show_only

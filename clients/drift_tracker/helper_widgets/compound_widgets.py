from PyQt4 import QtGui, QtCore
from helper_widgets import dropdown
from line_selector_widget import line_selector_widget

class table_dropdowns_with_entry(QtGui.QTableWidget):
    """
    this widgets consists of rows where each row is a frequency dropdown and an editable frequency field
    this is used for entering frequences of 729 lines into the drift tracker
    """
    def __init__(self, reactor, limits = (0,500), sig_figs = 4, names = [], entries = 2, suffix = '', favorites = {}, parent=None):
        super(table_dropdowns_with_entry, self).__init__(parent)
        self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.limits = limits
        self.favorites = favorites
        self.sig_figs = sig_figs
        self.names = names
        self.entries = entries
        self.suffix = suffix
        self.reactor = reactor
        self.initializeGUI()
        
    def initializeGUI(self):
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setColumnCount(2)
        self.setRowCount(self.entries)
        self.fill_out()
    
    def fill_out(self, names = None):
        if names is not None:
            self.names = names
        for i in range(self.entries):
            drop = dropdown(self.reactor, names = self.names, font=self.font, favorites = self.favorites)
            self.setCellWidget(i ,0 , drop)
            sample = QtGui.QDoubleSpinBox()
            sample.setFont(self.font)
            sample.setRange(*self.limits)
            sample.setDecimals(self.sig_figs)
            sample.setSingleStep(10**-self.sig_figs)
            sample.setSuffix(self.suffix)
            self.setCellWidget(i, 1, sample)
        for col in range(self.columnCount()):
            self.resizeColumnToContents(col)
        
    def resizeEvent(self, event):
        for col in range(self.columnCount()):
            self.resizeColumnToContents(col)

    def get_info(self):
        info = []
        for i in range(self.entries):
            dropdown = self.cellWidget(i, 0)
            index = dropdown.currentIndex()
            text = str(dropdown.itemData(index).toString())
            spin =  self.cellWidget( i, 1)
            val = spin.value()
            info.append((text, val))
        return info

    def closeEvent(self, x):
        self.reactor.stop()
        
class frequency_wth_dropdown(QtGui.QWidget):
    
    """
    this widget consists of a dropdown with known entries and a separate manual entry field. the user has the option of using either.
    """
    
    valueChanged = QtCore.pyqtSignal(float)
    useSaved = QtCore.pyqtSignal(bool)
    useSavedLine = QtCore.pyqtSignal(str)
    
    def __init__(self, reactor, limits = (0,500), parameter_name = 'Frequency', sig_figs = 4, names = [], suffix = ' MHz', font = None, only_show_favorites = False, parent=None):
        super(frequency_wth_dropdown, self).__init__(parent)  
        self.reactor = reactor
        self.parameter_name = parameter_name
        self.only_show_favorites = only_show_favorites
        self.limits = limits
        self.sig_figs =  sig_figs
        self.names = names
        self.suffix = suffix
        self.font = font
        self.selected = None
        if self.font is None:
            self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.initializeGUI()
        self.connect_layout()

    def initializeGUI(self):  
        layout = QtGui.QGridLayout()
        #frequency spin box  
        self.freq = QtGui.QDoubleSpinBox()
        self.freq.setKeyboardTracking(False)
        self.freq.setSuffix(self.suffix)
        self.freq.setDecimals(self.sig_figs)
        self.freq.setSingleStep(10**-self.sig_figs)
        self.freq.setRange(*self.limits)
        self.freq.setFont(self.font)
        #toggle button group
        self.select_freq = QtGui.QRadioButton()
        self.select_line = QtGui.QRadioButton()
        bg = QtGui.QButtonGroup()
        bg.setExclusive(True)
        bg.addButton(self.select_freq)
        bg.addButton(self.select_line)
        self.select_line.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.select_freq.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        layout.addWidget(self.select_freq, 1, 0)
        layout.addWidget(self.select_line, 1, 2)
        self.dropdown = dropdown(self.reactor, font = self.font, names = self.names, info_position = 0, only_show_favorites = self.only_show_favorites)
        label = QtGui.QLabel(self.parameter_name)
        label.setFont(self.font)
        label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        layout.addWidget(label,0, 1)
        layout.addWidget(self.freq, 1, 1)
        label = QtGui.QLabel('Saved Line')
        label.setFont(self.font)
        label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        layout.addWidget(label, 0, 3)
        layout.addWidget(self.dropdown, 1, 3)
        self.setLayout(layout)
    
    def connect_layout(self):
        self.freq.valueChanged.connect(self.valueChanged.emit)
        self.select_line.toggled.connect(self.useSaved.emit)
        self.dropdown.new_selection.connect(self.useSavedLine)
        
    def set_selected(self, text):
        self.dropdown.set_selected(text)
        
    def set_freq_value_no_signals(self, value):
        self.freq.blockSignals(True)
        self.freq.setValue(value)
        self.freq.blockSignals(False)
    
    def should_use_saved(self, val):
        self.select_line.setChecked(val)
        self.select_freq.setChecked(not val)
    
    def set_dropdown(self, names):
        self.dropdown.set_dropdown(names)
    
    def set_favorites(self, favorites):
        self.dropdown.set_favorites(favorites)
    
    def setRange(self, r_min, r_max):
        self.freq.setRange(r_min,r_max)
    
    def closeEvent(self, x):
        self.reactor.stop()

class frequency_wth_selector(QtGui.QWidget):
    
    """
    this widget consists of a manual entry field along with an a series of choices for line and sideband selection
    """
    
    manual_entry_value_changed = QtCore.pyqtSignal(float)
    on_new_selection = QtCore.pyqtSignal(list)
    use_selector = QtCore.pyqtSignal(bool)
    
    def __init__(self, reactor, limits = (0,500), parameter_name = 'Frequency', sig_figs = 4, names = [], suffix = ' MHz', font = None, only_show_favorites = False, expandable = False, parent=None):
        super(frequency_wth_selector, self).__init__(parent)  
        self.reactor = reactor
        self.parameter_name = parameter_name
        self.only_show_favorites = only_show_favorites
        self.limits = limits
        self.sig_figs =  sig_figs
        self.names = names
        self.suffix = suffix
        self.expandable = expandable
        self.font = font
        self.selected = None
        if self.font is None:
            self.font = QtGui.QFont('MS Shell Dlg 2',pointSize=12)
        self.initializeGUI()
        self.connect_layout()

    def initializeGUI(self):  
        layout = QtGui.QGridLayout()
        #frequency spin box  
        self.freq = QtGui.QDoubleSpinBox()
        self.freq.setKeyboardTracking(False)
        self.freq.setSuffix(self.suffix)
        self.freq.setDecimals(self.sig_figs)
        self.freq.setSingleStep(10**-self.sig_figs)
        self.freq.setRange(*self.limits)
        self.freq.setFont(self.font)
        #toggle button group
        self.select_freq = QtGui.QRadioButton()
        self.select_line = QtGui.QRadioButton()
        bg = QtGui.QButtonGroup()
        bg.setExclusive(True)
        bg.addButton(self.select_freq)
        bg.addButton(self.select_line)
        self.select_line.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.select_freq.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        layout.addWidget(self.select_freq, 1, 0)
        layout.addWidget(self.select_line, 1, 2)
        self.selector = line_selector_widget(self.reactor, input_font = self.font, only_show_favorites = self.only_show_favorites, expandable = self.expandable)
        label = QtGui.QLabel(self.parameter_name)
        label.setFont(self.font)
        label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        layout.addWidget(label,0, 1)
        layout.addWidget(self.freq, 1, 1)
        label = QtGui.QLabel('Saved Line')
        label.setFont(self.font)
        label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        layout.addWidget(label, 0, 3)
        layout.addWidget(self.selector, 1, 3)
        self.setLayout(layout)
    
    def connect_layout(self):
        self.freq.valueChanged.connect(self.manual_entry_value_changed.emit)
        self.select_line.toggled.connect(self.use_selector.emit)
        self.selector.on_user_modified.connect(self.on_new_selection.emit)
        
    def set_selection(self, info):
        self.selector.set_selected(info)
        
    def set_freq_value_no_signals(self, value):
        self.freq.blockSignals(True)
        self.freq.setValue(value)
        self.freq.blockSignals(False)
    
    def should_use_saved(self, val):
        self.select_line.setChecked(val)
        self.select_freq.setChecked(not val)
    
    def set_dropdown(self, names):
        self.selector.set_dropdown(names)
    
    def set_favorites(self, favorites):
        self.selector.set_favorites(favorites)
    
    def setRange(self, r_min, r_max):
        self.freq.setRange(r_min,r_max)
    
    def closeEvent(self, x):
        self.reactor.stop()
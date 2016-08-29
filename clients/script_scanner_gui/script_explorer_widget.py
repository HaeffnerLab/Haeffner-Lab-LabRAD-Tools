from PyQt4 import QtGui, QtCore
from experiment_selector_widget import experiment_selector_widget

class script_explorer_widget(QtGui.QWidget):

    def __init__(self, reactor, parent, font = None):
        super(script_explorer_widget, self).__init__(parent)
        self.font = font
        self.reactor = reactor
        self.experiments = []
        if self.font is None:
            self.font = QtGui.QFont('MS Shell Dlg 2', pointSize=12)
        self.setupLayout()

    def setupLayout(self):

        layout = QtGui.QGridLayout()
        label = QtGui.QLabel('Experiment', font = self.font)
        self.dropdown = QtGui.QComboBox()
        self.dropdown.setMaxVisibleItems(30)
        self.dropdown.addItem('')#add empty item for no selection state    
        #enable sorting
        sorting_model = QtGui.QSortFilterProxyModel(self.dropdown)
        sorting_model.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        sorting_model.setSourceModel(self.dropdown.model())
        self.dropdown.model().setParent(sorting_model)

        tree_view = QtGui.QTreeView()
        tree_model = QtGui.QStandardItemModel()
        tree_view.setModel(tree_model)

        parent = QtGui.QStandardItem('Collection')
        child = QtGui.QStandardItem('Child')
        parent.appendRow([child])
        tree_model.appendRow(parent)

        layout.addWidget(label, 0, 0, 1, 1)
        layout.addWidget(self.dropdown, 0, 1, 1, 2)
        layout.addWidget(tree_view, 1, 1, 2, 1)
        self.setLayout(layout)

    def addExperiment(self, experiment):
        self.dropdown.addItem(experiment)
        self.dropdown.model().sort(0)
        self.experiments.append(experiment)

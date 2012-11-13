from PyQt4 import QtGui, QtCore
from readout_histogram import readout_histgram
from scans import scans_connection
from state_preparation import state_preparation_connection
from drift_tracker import drift_tracker
from twisted.internet.defer import inlineCallbacks
from state_readout_parameters import general_parameters_connection

class control_729(QtGui.QWidget):
    def __init__(self, reactor, cxn = None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.reactor = reactor
        self.cxn = cxn
        self.connect_labrad()

    @inlineCallbacks
    def connect_labrad(self):
        if self.cxn is None:
            from connection import connection
            self.cxn = connection()
            yield self.cxn.connect()
        self.create_layout()
        self.connect_tab_signals()
        
    def create_layout(self):
        layout = QtGui.QGridLayout()
        self.tab = tab = QtGui.QTabWidget()
        histogram_tab = QtGui.QWidget()
        histogram_layout = QtGui.QVBoxLayout() 
        histogram_layout.addWidget(readout_histgram(self.reactor, self.cxn))
        histogram_layout.addWidget(general_parameters_connection(self.reactor, self.cxn))
        histogram_tab.setLayout(histogram_layout)
        self.state_preparation_tab = state_preparation_connection(self.reactor, self.cxn)
        scans_tab =  scans_connection(self.reactor, self.cxn)
        tab.addTab(histogram_tab, 'State Readout')
        self.state_prep_index = tab.addTab(self.state_preparation_tab, 'State Preparation')
        tab.addTab(scans_tab, 'Scans')
        drift_tracker_tab = drift_tracker(self.reactor, self.cxn)
        tab.addTab(drift_tracker_tab, 'Drift Tracker')
        layout.addWidget(tab)
        self.setLayout(layout)
    
    def connect_tab_signals(self):
        pumping_enable = self.state_preparation_tab.optical_pumping_frame.enable
        pumping_enable.stateChanged.connect(self.change_color(self.state_prep_index))
        self.change_color(self.state_prep_index)(pumping_enable.isChecked())
            
    def change_color(self, index):
        def func(selected):
            if selected:
                color = QtCore.Qt.darkGreen
            else:
                color = QtCore.Qt.black
            self.tab.tabBar().setTabTextColor(index, color)    
        return func

    def closeEvent(self, x):
        self.reactor.stop()
    
if __name__=="__main__":
    a = QtGui.QApplication( ['Control 729'] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = control_729(reactor)
    widget.show()
    reactor.run()
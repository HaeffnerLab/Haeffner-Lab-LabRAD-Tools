from PyQt4 import QtGui, QtCore
from analyzerWindow import AnalyzerWindow

class analyzerWindow729(AnalyzerWindow):
       
    def __init__(self, fitting_parameters, auto_accept, interface):
        super(analyzerWindow729, self).__init__(fitting_parameters, auto_accept, interface)
        
    def perform_customization(self):
        self.axes.set_ylim([0,1])
        custom_steps = [('Center', 2e-3), ('Background', 1e-2)]
        self.axes.set_xlabel('MHz')
        self.update_steps(custom_steps)
        
class analyzerWindowPowerFlop(AnalyzerWindow):
       
    def __init__(self, fitting_parameters, auto_accept, interface):
        super(analyzerWindowPowerFlop, self).__init__(fitting_parameters, auto_accept, interface)
        
    def perform_customization(self):
        self.axes.set_ylim([0,1])
        self.axes.set_xlabel('dBm')
import sys
from tree_view.Controllers import ParametersEditor
from PyQt4 import QtCore, QtGui, uic

class ScanItem(QtGui.QWidget):
    """ Item for parameter scanning """
    def __init__(self, p, parent):
        super(ScanItem, self).__init__(parent)
        self.parent = parent
        parameter, minim, maxim, steps, unit = p
        self.parameter = parameter
        self.makeLayout(p)
        self.connect_layout()

    def makeLayout(self, p):
        parameter, minim, maxim, steps, unit = p
        self.unit = unit
        layout = QtGui.QHBoxLayout()

        self.select = QtGui.QCheckBox()
        layout.addWidget(self.select)
        label = QtGui.QLabel(parameter)
        layout.addWidget(label)
        self.minim = QtGui.QDoubleSpinBox()
        self.maxim = QtGui.QDoubleSpinBox()
        self.steps = QtGui.QSpinBox()

        self.minim.setValue(minim)
        self.maxim.setValue(maxim)
        self.steps.setValue(steps)

        layout.addWidget(self.minim)
        layout.addWidget(self.maxim)
        layout.addWidget(self.steps)
        unitLabel = QtGui.QLabel(unit)
        layout.addWidget(unitLabel)
        self.setLayout(layout)

    def connect_layout(self):
        self.select.stateChanged.connect(self.checkbox_changed)
    
    def checkbox_changed(self):
        selection = self.select.isChecked()
        if selection: # this parameter is selected to scan
            self.parent.set_scan_parameter(self.parameter)
        else:
            self.parent.set_scan_none()

    def uncheck_no_signal(self):
        """
        We need to block signals from the checkbox
        so that when we uncheck a box it does not
        set the scan parameter to None via the
        connection to checkbox_changed()
        """
        self.select.blockSignals(True)
        self.select.setChecked(False)
        self.select.blockSignals(False)

    def get_scan_settings(self):
        """
        Get the scan settings (min, max, steps, unit)
        from this ScanItem
        """
        mn = self.minim.value()
        mx = self.maxim.value()
        steps = int(self.steps.value())
        return (mn, mx, steps, self.unit)

class sequence_widget(QtGui.QWidget):
    def __init__(self, params, editor):
        super(sequence_widget, self).__init__()
        self.parameters = {}
        self.makeLayout(params, editor)
        self.scan_parameter = None

    def makeLayout(self, params, editor):
        layout = QtGui.QVBoxLayout()
        for par, x in params:
            minim, maxim, steps, unit = x
            p = (par, minim, maxim, steps, unit)
            self.parameters[par] = ScanItem(p, self)
            layout.addWidget(self.parameters[par])
        layout.addWidget(editor)
        self.setLayout(layout)

    def set_scan_parameter(self, parameter):
        """
        Set the scan parameter and uncheck
        all of the other options in the GUI
        """
        self.scan_parameter = parameter
        for par in self.parameters.keys():
            if par != parameter:
                self.parameters[par].uncheck_no_signal()

    def set_scan_none(self):
        self.scan_parameter = None

    def get_scan_parameter(self):
        return self.scan_parameter
        
class scan_widget(QtGui.QStackedWidget):

    def __init__(self, reactor, parent):
        super(scan_widget, self).__init__()
        self.parent = parent
        self.setupLayout()
        self.reactor = reactor
        self.PreferredParameters = ParametersEditor(self.reactor)
        self.widgets = {} # dictionary of widgets to show
        self.preferreds = {}

    def setupLayout(self):
        pass

    def buildSequenceWidget(self, experiment, params):
        '''
        params = [par, ( min, max, steps, unit)]
        '''
        sw = sequence_widget(params, self.PreferredParameters)
        self.addWidget(sw)
        self.widgets[experiment] = sw
        self.show_none()

        self.preferreds[experiment] = [x[0].split('.') for x in params]

        #self.setCurrentWidget(sw)

    def set_preferred_parameters(self, experiment, params):
        self.preferreds[experiment].extend([x.split('.') for x in params])

    def get_scan_settings(self, experiment):
        """
        Return the scan settings (parameter to scan, min, max, steps, unit)
        or None for the requested sequence
        """
        scan_parameter = self.widgets[experiment].get_scan_parameter()
    
        if scan_parameter is None:
            return None
        else:
            mn, mx, steps, unit = self.widgets[experiment].parameters[scan_parameter].get_scan_settings()
            return (scan_parameter, mn, mx, steps, unit)
        

    def select(self, experiment):
        '''
        Select experiment to show
        '''
        try:
            self.widgets[experiment].setVisible(True)
            self.setCurrentWidget(self.widgets[experiment])
            #elf.PreferredParameters.show_only(self.preferreds[experiment])
            #elf.PreferredParameters.show_only([('DopplerCooling','duration'), ('DopplerCooling', 'duration')])
        except KeyError: # no experiment selected
            self.show_none()


    def show_none(self):
        for exp in self.widgets.keys():
            self.widgets[exp].setVisible(False)


if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    params = [(0, 6, 2, 'kHz'), ('p2', 0, 8, 2, 'us')]
    #icon = sequence_widget(params)
    icon = scan_widget(None)
    icon.buildSequenceWidget('exp', params)
    icon.show()
    app.exec_()

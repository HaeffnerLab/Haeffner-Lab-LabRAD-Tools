import sys
from tree_view.Controllers import ParametersEditor
from PyQt4 import QtCore, QtGui, uic

class ScanItem(QtGui.QWidget):
    """ Item for parameter scanning """
    def __init__(self, p, sequence_name, parent):
        super(ScanItem, self).__init__(parent)
        self.parent = parent
        parameter, minim, maxim, steps, unit = p
        self.parameter = parameter
        self.makeLayout(p, sequence_name)
        self.connect_layout()

    def makeLayout(self, p, sequence_name):
        parameter, minim, maxim, steps, unit = p
        self.unit = unit
        layout = QtGui.QHBoxLayout()

        self.select = QtGui.QCheckBox()
        layout.addWidget(self.select)
        label = QtGui.QLabel(parameter.split(".")[-1])
        layout.addWidget(label)
        self.minim = QtGui.QDoubleSpinBox()
        self.maxim = QtGui.QDoubleSpinBox()
        self.steps = QtGui.QDoubleSpinBox()
        
        self.minim.setRange(-1e6, 1e6)
        self.maxim.setRange(-1e6, 1e6)
        self.steps.setRange(-1e6, 1e6)
        
        self.minim.setValue(minim)
        self.maxim.setValue(maxim)
        self.steps.setValue(steps) 
    

        layout.addWidget(self.minim)
        layout.addWidget(self.maxim)
        layout.addWidget(self.steps)
        unitLabel = QtGui.QLabel(unit)
        layout.addWidget(unitLabel)
        layout.addWidget( QtGui.QLabel(sequence_name))
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
    def __init__(self, params, seq, single_seq = True):
        super(sequence_widget, self).__init__()
        self.parameters = {}
        self.makeLayout(params, single_seq)
        self.scan_parameter = None
        self.sequence_name = seq # name of the sequence this sequence widget refers to

    def makeLayout(self, params, single_seq = True):
        layout = QtGui.QVBoxLayout()
        
        # Run until stopped checkbox
        if single_seq:
            layout.addWidget(QtGui.QCheckBox("run until stopped"))
        
        for par, x, sequence_name in params:
            minim, maxim, steps, unit = x
            p = (par, minim, maxim, steps, unit)
            self.parameters[par] = ScanItem(p, sequence_name, self)
            layout.addWidget(self.parameters[par])
        #layout.addWidget(editor)
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
    
    def get_sequence_name(self):
        return self.sequence_name
    
    def get_scan_settings(self, scan):
        return self.parameters[scan].get_scan_settings()
    
class multi_sequence_widget(QtGui.QWidget):
    def __init__(self, widgets):
        super(multi_sequence_widget, self).__init__()
        layout = QtGui.QVBoxLayout()
        self.widgets = widgets
        for widget in widgets:
            layout.addWidget(widget)
        self.setLayout(layout)
        
    def get_scan_parameter(self):
        return [(w.get_sequence_name(), w.get_scan_parameter()) for w in self.widgets]
    
    def get_scan_settings(self, sequence_name, scan_parameter):
        for w in self.widgets:
            if w.sequence_name == sequence_name:
                return w.get_scan_settings(scan_parameter)
        raise Exception('sequence name not found')
        
    
class scan_box(QtGui.QStackedWidget):
    def __init__(self):
        super(scan_box, self).__init__()
        
class scan_widget(QtGui.QWidget):

    def __init__(self, reactor, parent):
        super(scan_widget, self).__init__()
        self.parent = parent
        self.scan_box = scan_box()
        self.reactor = reactor
        self.PreferredParameters = ParametersEditor(self.reactor)
        self.setupLayout()
        self.widgets = {} # dictionary of widgets to show
        self.preferreds = {}

    def setupLayout(self):
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.scan_box)
        layout.addWidget(self.PreferredParameters)
        self.setLayout(layout)
        
    def buildSequenceWidget(self, experiment, params):
        '''
        params = [(par, ( min, max, steps, unit), sequence)]
        '''
        
        sequences = list(set([p[2] for p in params])) # individual sequences
        sequences_dict = {}
        
        if len(sequences) == 1:
            seq = sequences[0]
            sequence_params = [x for x in params if x[2] == seq]
            sequences_dict[seq] = sequence_widget(sequence_params, seq, single_seq=True)
        
        else:
            for seq in sequences[::-1]:
                sequence_params = [x for x in params if x[2] == seq]
                sequences_dict[seq] = sequence_widget(sequence_params, seq, single_seq=False)
        
        multi = multi_sequence_widget(sequences_dict.values())
        
        #self.scan_box.addWidget(sw)
        #self.widgets[experiment] = sw
        self.scan_box.addWidget(multi)
        self.widgets[experiment] = multi
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
        scan_parameter_list = self.widgets[experiment].get_scan_parameter() # [(seq name, scan parameter)]
        
        settings_list = []
        for sequence_name, scan_parameter in scan_parameter_list:
            if scan_parameter is None:
                settings_list.append((sequence_name, None))
            else:
                #mn, mx, steps, unit = self.widgets[experiment].parameters[scan_parameter].get_scan_settings()
                mn, mx, steps, unit = self.widgets[experiment].get_scan_settings(sequence_name, scan_parameter)
                settings_list.append(( sequence_name, (scan_parameter, mn, mx, float(steps), unit) ))
        return settings_list # settings_list = [(seq name, ( param,  min, max, steps, unit)]
        

    def select(self, experiment):
        '''
        Select experiment to show
        '''
        try:
            self.widgets[experiment].setVisible(True)
            self.scan_box.setCurrentWidget(self.widgets[experiment])
            self.PreferredParameters.show_only(self.preferreds[experiment])
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

# import qt4reactor
# qt4reactor.install()
from PyQt5 import QtCore, QtGui, QtWidgets
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from fractions import Fraction
# from labrad import units as U
# from labrad.units import WithUnit
import numpy as np
# from common.abstractdevices.SD_tracker.SD_calculator import Transitions_SD as tracker 

QStringList = list

class ParamInfo():
    '''
    Container for the widgets with
    each row in the parameters table
    '''
    def __init__(self, value):
        self.value = value

class PredictSpectrum(QtWidgets.QWidget):

    def __init__(self, parent):
        super(PredictSpectrum, self).__init__()
        # self.reactor=reactor
        self.parent = parent
        self.value_dict = {}
        self.ident = 'Predicted Spectrum'
        self.Ca_data = Transitions_SD()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.ident)
        mainLayout = QtWidgets.QVBoxLayout()
        buttons = QtWidgets.QHBoxLayout()

        self.parameterTable = QtWidgets.QTableWidget()
        self.parameterTable.setColumnCount(2)

        self.plotButton = QtWidgets.QPushButton('Plot', self)

        mainLayout.addWidget(self.parameterTable)
        mainLayout.addLayout(buttons)
        buttons.addWidget(self.plotButton)

        self.OPpos = QtWidgets.QCheckBox("Positive Manifold")
        self.OPpos.setChecked(True)
        mainLayout.addWidget(self.OPpos)
        self.OPneg = QtWidgets.QCheckBox("Negative Manifold")
        self.OPneg.setChecked(True)
        mainLayout.addWidget(self.OPneg)
        self.deltam0 = QtWidgets.QCheckBox("Delta m=0")
        self.deltam0.setChecked(True)
        mainLayout.addWidget(self.deltam0)
        self.deltam1 = QtWidgets.QCheckBox("Delta m=1")
        self.deltam1.setChecked(True)
        mainLayout.addWidget(self.deltam1)
        self.deltam2 = QtWidgets.QCheckBox("Delta m=2")
        self.deltam2.setChecked(True)
        mainLayout.addWidget(self.deltam2)

        self.plotButton.clicked.connect(self.onPlot)

        self.setupParameterTable()
        self.setLayout(mainLayout)
        self.show()

    def setupParameterTable(self):

        self.parameterTable.clear()
        
        headerLabels = QStringList(['Parameter', 'Value'])
        self.parameterTable.setHorizontalHeaderLabels(headerLabels)
        self.parameterTable.horizontalHeader().setStretchLastSection(True)

        params = ['B Field', 'Line Center','Mode 1 Freq', 'Orders1', 'Mode 2 Freq', 'Orders2', 'Mode 3 Freq', 'Orders3', 'Micromotion', 'Drive Frequency']
        self.parameterTable.setRowCount(len(params))
        for i,p in enumerate(params):

            label = QtWidgets.QLabel(p)
            value = QtWidgets.QDoubleSpinBox()

            self.value_dict[p] = ParamInfo(value)

            value.setDecimals(3)
            value.setRange(-100, 100)
            value.setValue(0)

            self.parameterTable.setCellWidget(i, 0, label)
            self.parameterTable.setCellWidget(i, 1, value)   

    def generate_spectrum(self):  
            ##must be in gauss and MHz!!
            b_field = self.value_dict['B Field'].value.value()
            line_center = self.value_dict['Line Center'].value.value()
            mode_1 = self.value_dict['Mode 1 Freq'].value.value()
            order1 = int(self.value_dict['Orders1'].value.value())
            mode_2 = self.value_dict['Mode 2 Freq'].value.value()
            order2 = int(self.value_dict['Orders2'].value.value())
            mode_3 = self.value_dict['Mode 3 Freq'].value.value()
            order3 = int(self.value_dict['Orders3'].value.value())
            drive_freq = self.value_dict['Drive Frequency'].value.value()
            micromotion = int(self.value_dict['Micromotion'].value.value())

            all_carriers = self.Ca_data.get_transition_energies(b_field*1e-4,line_center) #to Tesla and MHz

            print(all_carriers)

            #choose which carriers to include
            included_lines = []
            if self.OPneg.isChecked() == True:
                included_lines.extend([el for el in all_carriers if el[0][1] == '-'])
            if self.OPpos.isChecked() == True:
                included_lines.extend([el for el in all_carriers if el[0][1] == '+'])

            final_lines =[]
            if self.deltam0.isChecked() == True:
                final_lines.extend([el for el in included_lines if np.abs(float(el[0][1:3])-float(el[0][6:8])) == 0])
            if self.deltam1.isChecked() == True:
                final_lines.extend([el for el in included_lines if np.abs(float(el[0][1:3])-float(el[0][6:8])) == 2])
            if self.deltam2.isChecked() == True:
                final_lines.extend([el for el in included_lines if np.abs(float(el[0][1:3])-float(el[0][6:8])) == 4])

            carriers = [carrier[1] for carrier in final_lines]
            sideband_orders = [[i,j,k] for i in range(-order1,order1+1) for j in range(-order2,order2+1) for k in range(-order3,order3+1)]
            sideband_freqs = [mode_1,mode_2,mode_3]


            #add all secular sidebands
            all_lines = []
            for freq in carriers:
                for el in sideband_orders:
                    all_lines.append(((freq + sum(np.multiply(el,sideband_freqs))),sum(np.abs(el))))

            #add driven sidebands
            if micromotion:
                micro_lines = []
                for el in all_lines:
                    freq,order = el
                    micro_lines.append((freq+drive_freq,0.5+order))
                    micro_lines.append((freq-drive_freq,0.5+order))
                all_lines.extend(micro_lines)

            freqs = np.arange(-50,50,0.005)
            spec = np.zeros_like(freqs)
            for line in all_lines:
                spec = np.add(spec,self.make_gaussian(line[0],freqs,line[1]))
            data = np.zeros((len(freqs), 2))
            data[:,0] = freqs
            data[:,1] = spec
            
            return data

    def make_gaussian(self,center,freqs,amplitude):
        #takes a center and makes a guassian around that point
        gauss = (0.5**amplitude)*np.exp(-(freqs-center)**2/(0.010**2))
        return gauss

    def onPlot(self):
        '''
        Plot the manual parameters. See documentation
        for plotFit()
        '''

        class dataset():
            def __init__(self, data):
                self.data = data
                self.updateCounter = 1

        data = self.generate_spectrum()   ####Ths is where we add the lorenzians
        ds = dataset(data)
        try:
            # remove the previous plot
            self.parent.parent.remove_artist(self.ident)
            self.parent.parent.add_artist(self.ident, ds, 0, no_points = False)
        except:
            self.parent.parent.add_artist(self.ident, ds, 0, no_points = False)


    def closeEvent(self, event):
        self.parent.parent.remove_artist(self.ident)



#everything must be in Gauss and MHz. Copied from SD scanner
class EnergyLevel(object):
    
    spectoscopic_notation = {
                            'S': 0,
                            'P': 1, 
                            'D': 2,
                            }
    
    spectoscopic_notation_rev = {
                            0 : 'S',
                            1 : 'P',
                            2 : 'D',
                            }
    
    
    def __init__(self, angular_momentum_l, total_angular_momentum_j, spin_s = '1/2'):
        #convert spectroscopic notation to the spin number
        if type(angular_momentum_l) == str:
            angular_momentum_l = self.spectoscopic_notation[angular_momentum_l]
        total_angular_momentum_j = Fraction(total_angular_momentum_j)
        spin_s = Fraction(spin_s)
        S = spin_s
        self.L = L = angular_momentum_l
        J = total_angular_momentum_j
        lande_factor =  self.lande_factor(S, L, J)
        #sublevels are found, 2* self.J is always an integer, so can use numerator
        self.sublevels_m =  [-J + i for i in range( 1 + (2 * J).numerator)]
        self.energy_scale = (lande_factor * 9.274e-24 / 6.626e-34) #1.4 MHz / gauss
    
    def lande_factor(self, S, L ,J):
        '''computes the lande g factor'''
        g = Fraction(3,2) + Fraction( S * (S + 1) - L * (L + 1) ,  2 * J*(J + 1))
        return g
    
    def magnetic_to_energy(self, B):
        '''given the magnitude of the magnetic field, returns all energies of all zeeman sublevels'''
        energies = [(self.energy_scale * m * B) *1e-6 for m in self.sublevels_m] #put in MHz
        representations = [self.frac_to_string(m) for m in self.sublevels_m]
        return list(zip(self.sublevels_m,energies,representations))
    
    def frac_to_string(self, sublevel):
        #helper class for converting energy levels to strings
        sublevel = str(sublevel)
        if not sublevel.startswith('-'): 
            sublevel = '+' + sublevel
        together = self.spectoscopic_notation_rev[self.L] + sublevel
        return together

class EnergyLevel_CA_ion(EnergyLevel):
    '''
    Class for describing the energy levels of Calcium Ions. This is specific to Ca+ because it uses
    precisely measured g factors of the S and D states in the calculations.
    '''
    
    def lande_factor(self, S, L, J):
        g_factor_S = 2.00225664 #Eur Phys JD 25 113-125
        g_factor_D = 1.2003340  #PRL 102, 023002 (2009)
        if S == Fraction('1/2') and L == Fraction('0') and J == Fraction('1/2'):
            g = g_factor_S
        elif S == Fraction('1/2') and L == Fraction('2') and J == Fraction('5/2'):
            g = g_factor_D
        return g

class Transitions_SD(object):
    
    S = EnergyLevel_CA_ion('S', '1/2')
    D = EnergyLevel_CA_ion('D', '5/2')
    allowed_transitions = [0,1,2]
    
    def transitions(self):
        transitions = []
        for m_s,E_s,repr_s in self.S.magnetic_to_energy(0):
            for m_d,E_d,repr_d in self.D.magnetic_to_energy(0):
                if abs(m_d-m_s) in self.allowed_transitions:
                    name = repr_s + repr_d
                    transitions.append(name)
        return transitions
    
    def get_transition_energies(self, B, zero_offset = 0.):
        '''returns the transition enenrgies in MHz where zero_offset is the 0-field transition energy between S and D'''
        ans = []
        for m_s,E_s,repr_s in self.S.magnetic_to_energy(B):
            for m_d,E_d,repr_d in self.D.magnetic_to_energy(B):
                if abs(m_d-m_s) in self.allowed_transitions:
                    name = repr_s + repr_d
                    diff = E_d - E_s
                    diff+= zero_offset
                    ans.append((name, diff))
        return ans
    
    def energies_to_magnetic_field(self, transitions):
        #given two points in the form [(S-1/2D5+1/2, 1.0 MHz), (-1/2, 5+/2, 2.0 MHz)], calculates the magnetic field
        try:
            transition1, transition2 = transitions
        except ValueError:
            raise Exception ("Wrong number of inputs in energies_to_magnetic_field")
        ms1,md1 = self.str_to_fractions(transition1[0])
        ms2,md2 = self.str_to_fractions(transition2[0])
        en1,en2 = transition1[1], transition2[1]
        if abs(md1 - ms1) not in self.allowed_transitions or abs(md2 - ms2) not in self.allowed_transitions:
            raise Exception ("Such transitions are not allowed")
        s_scale = self.S.energy_scale
        d_scale = self.D.energy_scale
        B = (en2 - en1) / ( d_scale * ( md2 - md1) - s_scale * (ms2 - ms1) )
        B = B *1e4 #(to guass from tesla)
        offset = en1 - (md1 * d_scale - ms1 * s_scale) * B
        return B, offset
        
    def str_to_fractions(self, inp):
        #takes S-1/2D5+1/2 and converts to Fraction(-1/2), Fraction(1/2)
        return Fraction(inp[1:5]), Fraction(inp[6:10])

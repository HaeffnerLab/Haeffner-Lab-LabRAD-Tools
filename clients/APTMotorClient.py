from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks, returnValue

BLOCKSIGNAL = 1

class DevicePanel(QtGui.QWidget):
    def __init__(self, parent, cxn, context, deviceName):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.cxn = cxn
        self.context = context
        self.deviceName = deviceName
        self.setSerialNumber()
        self.parameterWindowExists = False
        self.setupUI()
        self.getPositionLimits()
        self.getPositionSignal(BLOCKSIGNAL)
        self.setupListeners()
           
    def setupUI(self):
        # Labels
        position = QtGui.QLabel()
        position.setText(position.tr('Position (\265m)'))
        deviceName = QtGui.QLabel(self.deviceName)
        deviceName.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        stepSize = QtGui.QLabel('Step Size (\265m)')
        # Buttons
        
        setVelParamsButton = QtGui.QPushButton("Parameters", self)
        setVelParamsButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        setVelParamsButton.clicked.connect(self.parametersSignal)
        setVelParamsButton.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        
        stepLeftButton = QtGui.QPushButton("<", self)
        stepLeftButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        stepLeftButton.clicked.connect(self.moveRelativeLeftSignal)
        stepLeftButton.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        
        stepRightButton = QtGui.QPushButton(">", self)
        stepRightButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        stepRightButton.clicked.connect(self.moveRelativeRightSignal)
        stepRightButton.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
               
        self.positionDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.connect(self.positionDoubleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.moveAbsoluteSignal)
        
        self.positionDoubleSpinBox.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        self.positionDoubleSpinBox.setDecimals(1)
        self.positionDoubleSpinBox.setSingleStep(1)
        self.positionDoubleSpinBox.setMinimum(-6500)
        self.positionDoubleSpinBox.setMaximum(6500)
        self.positionDoubleSpinBox.setKeyboardTracking(False)
        self.positionDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        self.stepSizeDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.stepSizeDoubleSpinBox.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        self.stepSizeDoubleSpinBox.setDecimals(1)
        self.stepSizeDoubleSpinBox.setSingleStep(1)
        self.stepSizeDoubleSpinBox.setMinimum(0)
        self.stepSizeDoubleSpinBox.setKeyboardTracking(False)
        self.stepSizeDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        # Layout
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(5)
        

        self.grid.addWidget(deviceName, 1, 0, QtCore.Qt.AlignCenter)
        self.grid.addWidget(setVelParamsButton, 4, 2, QtCore.Qt.AlignCenter)

        self.grid.addWidget(self.positionDoubleSpinBox, 4, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(position, 4, 0, QtCore.Qt.AlignCenter)

        self.grid.addWidget(stepLeftButton, 2, 0, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.stepSizeDoubleSpinBox, 2, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(stepRightButton, 2, 2, QtCore.Qt.AlignCenter)
        self.grid.addWidget(stepSize, 1, 1)

        self.setLayout(self.grid)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.show()
        
    @inlineCallbacks
    def getPositionLimits(self):
        stageAxisInformation = yield self.parent.server.get_stage_axis_information(context = self.context)
        self.minimumPosition = stageAxisInformation[0] * 1000
        self.maximumPosition = stageAxisInformation[1] * 1000

    @inlineCallbacks
    def setSerialNumber(self):
        self.serialNumber = yield self.parent.server.get_serial_number(context = self.context)
        serialNumberLabel = QtGui.QLabel("ID: " + str(self.serialNumber))
        self.grid.addWidget(serialNumberLabel, 1, 2, QtCore.Qt.AlignCenter)
        
    @inlineCallbacks
    def setVelParamsSignal(self, evt):
        ok = yield self.parent.server.set_velocity_parameters(float(self.getSetVelParams1Edit.text()), float(self.getSetVelParams2Edit.text()), float(self.getSetVelParams3Edit.text()), context = self.context)

    def parametersSignal(self, evt):
        if (self.parameterWindowExists == False):
            self.parameterWindowExists = True
            self.parameterWindow = ParameterWindow(self, self.deviceName, self.context)
            self.parameterWindow.show()
        else:
            self.parameterWindow.show()

    @inlineCallbacks
    def getVelParamLimitsSignal(self, evt):
        velParamLimits = yield self.parent.server.get_velocity_parameter_limits(context = self.context)
        self.getVelParamLimits1Edit.setText(str(round(velParamLimits[0], 4)))
        self.getVelParamLimits2Edit.setText(str(round(velParamLimits[1], 4)))

    @inlineCallbacks
    def moveRelativeLeftSignal(self, evt):
        newvalmm = (self.positionDoubleSpinBox.value() - self.stepSizeDoubleSpinBox.value()) / 1000.0
        if (newvalmm > self.minimumPosition):
            relmm = self.stepSizeDoubleSpinBox.value() / 1000.0
            ok = yield self.parent.server.move_relative(-relmm, context = self.context)
            if (ok == True):
                self.getPositionSignal(BLOCKSIGNAL)
        else:
            print "The specified move is outside the current limits."

    @inlineCallbacks
    def moveRelativeRightSignal(self, evt):
        newvalmm = (self.positionDoubleSpinBox.value() + self.stepSizeDoubleSpinBox.value()) / 1000.0
        if (newvalmm < self.maximumPosition):
            relmm = self.stepSizeDoubleSpinBox.value() / 1000.0
            ok = yield self.parent.server.move_relative(relmm, context = self.context)
            if (ok == True):
                self.getPositionSignal(BLOCKSIGNAL)
        else:
            print "The specified move is outside the current limits."
    
    @inlineCallbacks
    def moveAbsoluteSignal(self, evt):
        self.positionDoubleSpinBox.blockSignals(True)
        valmm = self.positionDoubleSpinBox.value() / 1000.0
        ok = yield self.parent.server.move_absolute(valmm, context = self.context)
        if (ok == True):
            self.getPositionSignal(BLOCKSIGNAL)

    @inlineCallbacks
    def identifySignal(self, evt):
        ok = yield self.parent.server.identify(context = self.context)


    @inlineCallbacks
    def getVelParamsSignal(self, evt):
        velParams = yield self.parent.server.get_velocity_parameters(context = self.context)
        self.getSetVelParams1Edit.setText(str(round(velParams[0], 4)))
        self.getSetVelParams2Edit.setText(str(round(velParams[1], 4)))
        self.getSetVelParams3Edit.setText(str(round(velParams[2], 4)))

    @inlineCallbacks
    def getPositionSignal(self, evt):
        if (evt == BLOCKSIGNAL):
            self.positionDoubleSpinBox.blockSignals(True)
        position = yield self.parent.server.get_position(context = self.context)
        self.positionDoubleSpinBox.setValue(position * 1000)
        self.positionDoubleSpinBox.blockSignals(False)

    @inlineCallbacks
    def setupListeners(self):
        yield self.parent.server.signal__position_change(88888, context = self.context)
        yield self.parent.server.addListener(listener = self.positionChange, source = None, ID = 88888)

    def positionChange(self, x, y):
        self.getPositionSignal(1)

class ParameterWindow(QtGui.QWidget):
    """Creates the device parameter window"""

    def __init__(self, parent, deviceName, context):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.deviceName = deviceName
        self.context = context
        self.setWindowTitle(str(self.deviceName) + " " + 'Velocity Parameters')
        self.setupUI()
        self.getInitialValues()
    
    def setupUI(self):
        # Labels
        minVelocity = QtGui.QLabel('Min Velocity')
        acceleration = QtGui.QLabel('Acceleration')
        maxVelocity = QtGui.QLabel('Max Velocity')
        
        hardwareModel = QtGui.QLabel('Hardware Model')
        softwareVersion = QtGui.QLabel('Software Version')
        hardwareNotes = QtGui.QLabel('Hardware Notes')
        
        parameterLimits = QtGui.QLabel('Max Limits')
        accLimit = QtGui.QLabel('Max Acceleration')
        velocityLimit = QtGui.QLabel('Max Velocity')

        # Buttons
        setVelParamsButton = QtGui.QPushButton("Set Velocity Parameters", self)
        setVelParamsButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        setVelParamsButton.clicked.connect(self.setVelParamsSignal)
        setVelParamsButton.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        
        # Spin Boxes
        self.minVelocityDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.minVelocityDoubleSpinBox.setDecimals(4)
        self.minVelocityDoubleSpinBox.setMinimum(0)
        self.minVelocityDoubleSpinBox.setSingleStep(.01)
        self.minVelocityDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.accDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.accDoubleSpinBox.setDecimals(4)
        self.accDoubleSpinBox.setMinimum(0)
        self.accDoubleSpinBox.setSingleStep(.01)
        self.accDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.maxVelocityDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.maxVelocityDoubleSpinBox.setDecimals(4)
        self.maxVelocityDoubleSpinBox.setMinimum(0)
        self.maxVelocityDoubleSpinBox.setSingleStep(.01)
        self.maxVelocityDoubleSpinBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        
        # Text boxes
        self.hardwareModelEdit = QtGui.QLineEdit(readOnly=True)
        self.softwareVersionEdit = QtGui.QLineEdit(readOnly=True)
        self.hardwareNotesEdit = QtGui.QLineEdit(readOnly=True)

        self.accLimitEdit = QtGui.QLineEdit(readOnly=True)
        self.velocityLimitEdit = QtGui.QLineEdit(readOnly=True)

        # Layout
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self.grid.setSpacing(5)
        
        self.grid.addWidget(setVelParamsButton, 0, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(minVelocity, 1, 0, QtCore.Qt.AlignCenter)
        self.grid.addWidget(acceleration, 1, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(maxVelocity, 1, 2, QtCore.Qt.AlignCenter)
        
        self.grid.addWidget(self.minVelocityDoubleSpinBox, 2, 0, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.accDoubleSpinBox, 2, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.maxVelocityDoubleSpinBox, 2, 2, QtCore.Qt.AlignCenter)
        
        self.grid.addWidget(hardwareModel, 3, 0, QtCore.Qt.AlignCenter)
        self.grid.addWidget(softwareVersion, 3, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(hardwareNotes, 3, 2, QtCore.Qt.AlignCenter)
        
        self.grid.addWidget(self.hardwareModelEdit, 4, 0, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.softwareVersionEdit, 4, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.hardwareNotesEdit, 4, 2, QtCore.Qt.AlignCenter)
        
        self.grid.addWidget(accLimit, 5, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(velocityLimit, 5, 2, QtCore.Qt.AlignCenter)
        
        self.grid.addWidget(parameterLimits, 6, 0, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.accLimitEdit, 6, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.velocityLimitEdit, 6, 2, QtCore.Qt.AlignCenter)
        
    def getInitialValues(self):
        self.getVelParams()
        self.getHardwareInfo()
        self.getVelocityParameterLimits()

    @inlineCallbacks
    def setVelParamsSignal(self, evt):
        if (self.minVelocityDoubleSpinBox.value() > self.maxVelocityDoubleSpinBox.value()):
            print 'Minimum velocity exceeds maximum velocity!'
        else:
            ok = yield self.parent.parent.server.set_velocity_parameters(self.minVelocityDoubleSpinBox.value(),self.accDoubleSpinBox.value(), self.maxVelocityDoubleSpinBox.value(), context = self.context)
    
    @inlineCallbacks
    def getVelParams(self):
        velParams = yield self.parent.parent.server.get_velocity_parameters(context = self.context)
        self.minVelocityDoubleSpinBox.setValue(velParams[0])
        self.accDoubleSpinBox.setValue(velParams[1])
        self.maxVelocityDoubleSpinBox.setValue(velParams[2])
    
    @inlineCallbacks
    def getHardwareInfo(self):
        hwInfo = yield self.parent.parent.server.get_device_information(context = self.context)
        self.hardwareModelEdit.setText(str(hwInfo[0]))
        self.softwareVersionEdit.setText(str(hwInfo[1]))
        self.hardwareNotesEdit.setText(str(hwInfo[2]))
 
    @inlineCallbacks
    def getVelocityParameterLimits(self):
        paramLimits = yield self.parent.parent.server.get_velocity_parameter_limits(context = self.context)
        self.accLimitEdit.setText(str(paramLimits[0]))
        self.velocityLimitEdit.setText(str(paramLimits[1]))
        self.minVelocityDoubleSpinBox.setMaximum(paramLimits[1])
        self.accDoubleSpinBox.setMaximum(paramLimits[0])
        self.maxVelocityDoubleSpinBox.setMaximum(paramLimits[1])
        
    def closeEvent(self, evt):
        self.hide()
        
class APTMotorClient(QtGui.QWidget):
    def __init__(self, reactor):
        QtGui.QWidget.__init__(self)
        self.reactor = reactor
        self.devDict = {}
        try:
            self.connect()
        except Exception:
            print 'excepting'
            self.setDisabled(True)
        
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        self.cxn = yield connectAsync()
        try:
            self.server = yield self.cxn.apt_motor_server
            availableDevices = yield self.server.get_available_devices()
        except Exception ,e:
            print 'server not connected: {}'.format(e)
            availableDevices = []
        self.setupUI(availableDevices)

    @inlineCallbacks
    def setupUI(self, availableDevices):
        self.setWindowTitle("APT Motor Control Panel")
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
        self.setLayout(grid)

        numDevices = len(availableDevices)

        for i in range(numDevices):
            context = yield self.cxn.context()
            self.server.select_device(availableDevices[i], context = context)
            devPanel = DevicePanel(self, self.cxn, context, availableDevices[i])
            self.devDict[i] = devPanel
            if (i % 2 == 0): #even
                grid.addWidget(devPanel, (i / 2) , 0)
            else:
                grid.addWidget(devPanel, ((i - 1) / 2) , 1)
        self.show()
        
    def closeEvent(self, evt):
        self.reactor.stop()
            
    
if __name__ == "__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    mainPanel = APTMotorClient(reactor)
    reactor.run()
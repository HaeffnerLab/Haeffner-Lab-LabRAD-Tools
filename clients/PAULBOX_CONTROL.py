import sys
from PyQt4 import QtGui, QtCore
import labrad

class script():
    def __init__(self, name):
        self.name = name
        self.floatDict = {}
        self.boolDict = {}
    
    def addFloat(self, name, value, min, max):
        self.floatDict[name] = [value, min, max]

class floatLayout():
    def __init__(self):
        self.NUM_ENTRIES = 10
        self.d = {}
        self.makeLayout()
        
    def makeLayout(self):
        self.layout = QtGui.QGridLayout()
        for entry in range(self.NUM_ENTRIES):
            name = QtGui.QLineEdit()
            val = QtGui.QDoubleSpinBox()
            val.setMinimum(0.0)
            val.setMaximum(100000000.0)
            min = QtGui.QLineEdit()
            max = QtGui.QLineEdit()           
            self.layout.addWidget(name, entry, 0)
            self.layout.addWidget(val, entry, 1)
            self.layout.addWidget(min, entry, 2)
            self.layout.addWidget(max, entry, 3)
            self.d[entry] = [name, val, min, max]
            
    def getLayout(self):
        return self.layout
    
    def setFloats(self, script):
        for position,name in enumerate(script.floatDict.keys()):
            [value, min, max] = script.floatDict[name]
            [nameWidget, valWidget, minWidget, maxWidget] = self.d[position]
            nameWidget.setText(name)
            valWidget.setValue(float(value))
            minWidget.setText(min)
            maxWidget.setText(max)
        for position in range(position+1, self.NUM_ENTRIES): #clear the rest
            self.clearEntry(position)
    
    def clearEntry(self, position):
        for widget in self.d[position]:
            widget.clear()
    
    def getFloats(self):
        list = []
        for entry in self.d.itervalues():
            name = entry[0].text()
            value = entry[1].value()
            if name.length():
                list.append(['FLOAT',str(name),str(value)])
        return list

class PAULBOX_CONTROL( QtGui.QWidget ):
    def __init__( self, server, parent = None ):
        QtGui.QWidget.__init__( self, parent )
        self.pbox = server
        self.script = script
        self.scriptDict = {}
        self.floatLayout = floatLayout()
        self.createLayout()
        self.loadScriptNames()
        self.loadIntoLayout()

    def createLayout(self):
        def makeTitle():
            title = QtGui.QLabel("Paul\'s Box Control")
            title.setAlignment(QtCore.Qt.AlignHCenter)
            title.setFont(QtGui.QFont("MS Shell Dlg",12, 75))
            return title
        
        def makeSubTitle():
            subtitle = QtGui.QHBoxLayout()
            label = QtGui.QLabel("Script")
            scriptbox = QtGui.QComboBox()
            scriptbox.setFont(QtGui.QFont("MS Shell Dlg",10))
            execute = QtGui.QPushButton("Execute")
            refresh = QtGui.QPushButton("Refresh")
            for widget in [label, scriptbox, execute, refresh]:
                subtitle.addWidget(widget)
            #connect functions
            scriptbox.currentIndexChanged.connect(self.scriptSelected)
            execute.clicked.connect(self.executeScript)
            refresh.clicked.connect(self.reloadScripts)
            self.scriptBox = scriptbox
            return subtitle
        
        layout = QtGui.QVBoxLayout()
        title = makeTitle()
        subtitle = makeSubTitle()
        layout.addWidget(title)
        layout.addLayout(subtitle)
        fl = self.floatLayout.getLayout()
        layout.addLayout(fl)
        self.setLayout(layout)

    def loadScriptNames( self ):
        self.pbox.reload_scripts()
        for scriptname in self.pbox.get_available_scripts():
            script = self.script(scriptname)
            varlist = self.pbox.get_variable_list( scriptname )
            for entry in varlist:
                if entry[1] =='float':
                    floatname = entry[0]
                    value = entry[2]
                    min = entry[3]
                    max = entry[4]
                    script.addFloat(floatname, value, min, max)
            self.scriptDict[scriptname]=script
        
    def loadIntoLayout(self):
        names = self.scriptDict.keys()
        names.sort()
        for name in names:
            self.scriptBox.addItem(name, name)
    
    def reloadScripts(self):
        for item in self.scriptDict.itervalues():
            del(item)
        self.scriptBox.clear()
        self.scriptDict = {}
        self.loadScriptNames()
        self.loadIntoLayout()

    def scriptSelected( self, item ):
        name = str(self.scriptBox.itemData(item).toString())
        if name in self.scriptDict.keys():
            script = self.scriptDict[name]
            self.floatLayout.setFloats(script)
                
    def executeScript( self ):
        item = self.scriptBox.currentIndex() 
        name = str(self.scriptBox.itemData(item).toString())
        floatlist = self.floatLayout.getFloats()
        self.pbox.send_command( name, floatlist )

if __name__=='__main__':
    cxn = labrad.connect()
    server = cxn.paul_box
    app = QtGui.QApplication( sys.argv )
    icon = PAULBOX_CONTROL(server)
    icon.show()
    app.exec_()

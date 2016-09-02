# Config Editor
from PyQt4 import QtGui, QtCore, uic
import sys
import os
import subprocess
from functools import partial
from CONFIG_EDITOR_config import labrad_folders

class CONFIG_EDITOR(QtGui.QMainWindow):

    def __init__(self, reactor, clipboard = None, cxn = None, parent=None):
        super(CONFIG_EDITOR, self).__init__(parent)

	self.reactor = reactor

        self.current_file = None
        self.get_config_files(labrad_folders)
        self.initUI()


    def get_config_files(self, folders = '.'):
        # finds all config files in folder
        self.config_path_list = []
        self.config_file_list = []
        
        for folder in folders:
		for (paths, dirs, files) in os.walk(folder):
	            for file in files:
	                if      'config' in file \
			    and '.py' in file \
	                    and 'example' not in file \
	                    and 'sample' not in file \
	                    and '.pyc' not in file \
	                    and '.jar' not in file \
	                    and '.py~' not in file \
	                    and '.swp' not in file \
	                    and '.git' not in paths: # check if filename contains string 'config'

	                    self.config_path_list.append(paths)
	                    self.config_file_list.append(file)

    def initUI(self):
        newAction = QtGui.QPushButton('New')
        #newAction.setShortcut('Ctrl+N')
        #newAction.setStatusTip('Create new file')
        #newAction.triggered.connect(self.newFile)
        newAction.pressed.connect(self.newFile)

        saveAction = QtGui.QPushButton('Save')
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save current file')
        saveAction.pressed.connect(self.saveFile)

        openAction = QtGui.QPushButton('Open')
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open a file')
        openAction.pressed.connect(partial(self.openFile, None))

	buttonWidget = QtGui.QWidget()
	buttons_layout = QtGui.QHBoxLayout()
	buttons_layout.addWidget(newAction)
	buttons_layout.addWidget(saveAction)
	buttons_layout.addWidget(openAction)
	buttonWidget.setLayout(buttons_layout)

	comboBoxWidget = QtGui.QComboBox()
	self.file_actions = []
        for k, path in sorted(zip(self.config_file_list, self.config_path_list)):
            hlp = path.split('/')
            #self.file_actions.append(QtGui.QAction(hlp[-1] + '/' + k, self))
            #self.file_actions[-1].triggered.connect(partial(self.open_config_file, k, path))
            #fileMenu.addAction(self.file_actions[-1])
	    comboBoxWidget.addItem(hlp[-1] + '/' + k)

	self.text = QtGui.QTextEdit(self)
        #self.setCentralWidget(self.text)
        self.setGeometry(300,300,800,600)
        self.setWindowTitle('Notepad')

	centralWidget = QtGui.QWidget()
	mylayout = QtGui.QVBoxLayout()
	mylayout.addWidget(buttonWidget)
	mylayout.addWidget(comboBoxWidget)
	mylayout.addWidget(self.text)
	centralWidget.setLayout(mylayout)

	self.setCentralWidget(centralWidget)

        #self.show()
	return

        

    def open_config_file(self, filename, path):
        full_filename = os.path.join(path, filename)
        self.openFile(full_filename)
        self.current_file = full_filename

    def newFile(self):
        self.text.clear()
        self.current_file = None

    def saveFile(self):
        if self.current_file is None:
            # dialog appears only for non-config files
            filename = QtGui.QFileDialog.getSaveFileName(self, 'Save File', os.getenv('HOME'))

        to_save_filename = self.current_file
        f = open(to_save_filename, 'w')
        filedata = self.text.toPlainText()
        f.write(filedata)
        f.close()

    def openFile(self, filename = None):
        if filename is None:
            filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File', os.getenv('HOME'))

        try:
            f = open(filename, 'r')
            filedata = f.read()
            self.text.setText(filedata)
            f.close()            
        except:
            return
         
    def closeEvent(self, x):
        self.reactor.stop()  



         

if __name__ == '__main__':

    a = QtGui.QApplication( [] )
    clipboard = a.clipboard()
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    CONFIG_EDITOR = CONFIG_EDITOR(reactor, clipboard)
    CONFIG_EDITOR.show()
    reactor.run()


# Config Editor
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import sys
import os
import subprocess
from functools import partial
from .CONFIG_EDITOR_config import labrad_folders

from . import syntax

class CONFIG_EDITOR(QtWidgets.QMainWindow):

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
                        if      ('config' in file or 'Config' in file or 'CONFIG' in file) \
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
        newAction = QtWidgets.QPushButton('New')
        newAction.setShortcut('Ctrl+N')
        newAction.setStatusTip('Create new file')
        newAction.pressed.connect(self.newFile)

        saveAction = QtWidgets.QPushButton('Save')
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save current file')
        saveAction.pressed.connect(self.saveFile)
        
        openAction = QtWidgets.QPushButton('Open')
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open a file')
        openAction.pressed.connect(partial(self.openFile, None))
        
        buttonWidget = QtWidgets.QWidget()
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(newAction)
        buttons_layout.addWidget(saveAction)
        buttons_layout.addWidget(openAction)
        buttonWidget.setLayout(buttons_layout)
        
        self.comboBoxWidget = QtWidgets.QComboBox()
        self.comboBoxWidget.addItem('Choose a file')
        for k, path in sorted(zip(self.config_file_list, self.config_path_list)):
            self.comboBoxWidget.addItem(os.path.join(path, k))

        self.comboBoxWidget.currentIndexChanged.connect(self.open_config_file)

        #self.text = QtGui.QTextEdit(self)
        self.text = QtWidgets.QPlainTextEdit(self)

        self.setGeometry(300,300,800,600)
        self.setWindowTitle('Config Editor')
        
        centralWidget = QtWidgets.QWidget()
        mylayout = QtWidgets.QVBoxLayout()
        mylayout.addWidget(buttonWidget)
        mylayout.addWidget(self.comboBoxWidget)
        mylayout.addWidget(self.text)
        centralWidget.setLayout(mylayout)
        
        self.setCentralWidget(centralWidget)

        return
        

    def open_config_file(self, current_index):
        full_filename = self.comboBoxWidget.currentText()
        #full_filename = os.path.join(path, filename)
        self.openFile(full_filename)

    def newFile(self):
        self.text.clear()
        self.current_file = None
        self.comboBoxWidget.setCurrentIndex(0)

    def saveFile(self):
        if self.current_file is None:
            # dialog appears only for non-config files
            filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', os.getenv('HOME'))[0]

        to_save_filename = self.current_file
        f = open(to_save_filename, 'w')
        filedata = self.text.toPlainText()
        f.write(filedata)
        f.close()

    def openFile(self, filename = None):
        if filename == "Choose a file":
            self.current_file = None
            self.text.clear()
            return
        if filename is None:
            filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', os.getenv('HOME'))[0]

        try:
            f = open(filename, 'r')
            filedata = f.read()
            highlight = syntax.PythonHighlighter(self.text.document())
            self.text.setPlainText(filedata)
            self.text.show()

            self.current_file = filename
            f.close()            
        except:
            return
         
    def closeEvent(self, x):
        self.reactor.stop()  



         

if __name__ == '__main__':

    a = QtWidgets.QApplication( [] )
    clipboard = a.clipboard()
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    CONFIG_EDITOR = CONFIG_EDITOR(reactor, clipboard)
    CONFIG_EDITOR.show()
    reactor.run()


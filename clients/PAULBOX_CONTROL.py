import sys
from PyQt4 import QtGui
from PyQt4 import QtCore, uic
import os
import labrad

NUM_ENTRIES = 7

class PAULBOX_CONTROL( QtGui.QWidget ):
    def __init__( self,server, parent = None ):
        QtGui.QWidget.__init__( self, parent )
        basepath = os.environ.get('LABRADPATH',None)
        if not basepath:
            raise Exception('Please set your LABRADPATH environment variable')
        path = os.path.join(basepath,'lattice/clients/qtui/paulboxfrontend.ui')
        uic.loadUi(path,self)
        self.pbox = server
        self.floatnames = [''] * NUM_ENTRIES
        self.floatval = [''] * NUM_ENTRIES
        self.minfloatval = [''] * NUM_ENTRIES
        self.maxfloatval = [''] * NUM_ENTRIES
        self.floatnameledits = [self.fnamelineEdit_1, self.fnamelineEdit_2, self.fnamelineEdit_3, self.fnamelineEdit_4, self.fnamelineEdit_5, self.fnamelineEdit_6, self.fnamelineEdit_7]
        self.floatvalsbox = [self.fvaldoubleSpinBox_1, self.fvaldoubleSpinBox_2, self.fvaldoubleSpinBox_3, self.fvaldoubleSpinBox_4, self.fvaldoubleSpinBox_5, self.fvaldoubleSpinBox_6, self.fvaldoubleSpinBox_7]
        self.minfloatvalledits = [self.minlineEdit_1, self.minlineEdit_2, self.minlineEdit_3, self.minlineEdit_4, self.minlineEdit_5, self.minlineEdit_6, self.minlineEdit_7]
        self.maxfloatvalledits = [self.maxlineEdit_1, self.maxlineEdit_2, self.maxlineEdit_3, self.maxlineEdit_4, self.maxlineEdit_5, self.maxlineEdit_6, self.maxlineEdit_7]
        #also do above for boolean names and default values
	    #connect functions
        self.connect( self.scriptBox, QtCore.SIGNAL( 'currentIndexChanged(int)' ), self.scriptSelected )
        self.connect( self.execButton, QtCore.SIGNAL( 'clicked()' ), self.executeScript )
        self.loadscriptnames()

    def loadscriptnames( self ):
        for name in self.pbox.get_available_scripts():
            self.scriptBox.addItem( name )

    #once the user select the script, fills in the floatnames/floatval... data structure with variables
    #pertaining to that script
    def scriptSelected( self, item ):
        selectedname = str( self.scriptBox.itemText( item ) )
        varlist = self.pbox.get_variable_list( selectedname )
        #clears existing information
        self.floatnames = [''] * NUM_ENTRIES
        self.floatval = [''] * NUM_ENTRIES
        self.minfloatval = [''] * NUM_ENTRIES
        self.maxfloatval = [''] * NUM_ENTRIES
        currentfloat = 0#determines how many fields have been filled so far
        currentbool = 0
        for setting in varlist:
            if setting:#fix to make sure empty sequences are displayed
                varname = setting[0]
                vartype = setting[1]
                defvalue = setting[2]
                if len( setting ) > 3:
                    minvalue = setting[3]
                    maxvalue = setting[4]
                else:
                    minvalue = ''
                    maxvalue = ''
                if vartype == 'float':
                    self.floatnames[currentfloat] = varname
                    self.floatval[currentfloat] = defvalue
                    self.minfloatval[currentfloat] = minvalue
                    self.maxfloatval[currentfloat] = maxvalue
                    currentfloat = currentfloat + 1
                elif vartype == 'bool':
                    pass #populate booleans
        self.drawValues()

    def drawValues( self ):
        for i in range( NUM_ENTRIES ):
            #add names
            name = self.floatnames[i]
            if name != '':
                self.floatnameledits[i].setEnabled( True )
                self.floatnameledits[i].setText( name )
            else:
                self.floatnameledits[i].setEnabled( False )
                self.floatnameledits[i].setText( '' )
            #add min/max
            min = self.minfloatval[i]
            if min != '':
                self.minfloatvalledits[i].setEnabled( True )
                self.minfloatvalledits[i].setText( min )
            else:
                self.minfloatvalledits[i].setEnabled( False )
                self.minfloatvalledits[i].setText( '' )
            max = self.maxfloatval[i]
            if max != '':
                self.maxfloatvalledits[i].setEnabled( True )
                self.maxfloatvalledits[i].setText( max )
            else:
                self.maxfloatvalledits[i].setEnabled( False )
                self.maxfloatvalledits[i].setText( '' )
            val = self.floatval[i]
            if val != '':
                self.floatvalsbox[i].setEnabled( True )
                self.floatvalsbox[i].setValue( float( val ) )
            else:
                self.floatvalsbox[i].setValue( 0 )
                self.floatvalsbox[i].setEnabled( False )
    def executeScript( self ):
        #TODO in the future, add support for booleans by also reading them out
        name = str( self.scriptBox.currentText() )
        varlist = []
        for i in range( NUM_ENTRIES ):
            if self.floatnameledits[i].isEnabled():
                varname = str( self.floatnameledits[i].text() )
                varvalue = str( self.floatvalsbox[i].value() )
                varlist.append( ['FLOAT', varname, varvalue] )
        self.pbox.send_command( name, varlist )
        print 'Paul Box Script Sent'

if __name__=='__main__':
    cxn = labrad.connect()
    server = cxn.paul_box
    app = QtGui.QApplication( sys.argv )
    icon = PAULBOX_CONTROL(server)
    icon.show()
    app.exec_()

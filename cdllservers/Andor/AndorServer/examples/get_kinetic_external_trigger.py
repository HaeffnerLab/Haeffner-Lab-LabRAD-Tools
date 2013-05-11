import labrad
from labrad.units import WithUnit
import numpy as np
import pyqtgraph
import time
from PyQt4 import QtGui

kinetic_number = 5
identify_exposure = WithUnit(0.005, 's')
stop_x = 50
stop_y = 100
image_region = (1,1,1,stop_x,1,stop_y)


cxn = labrad.connect()
cam = cxn.andor_server

cam.abort_acquisition()
initial_exposure = cam.get_exposure_time()
cam.set_exposure_time(identify_exposure)
initial_region = cam.get_image_region()
initial_trigger_mode = cam.get_trigger_mode()
cam.set_image_region(*image_region)
cam.set_acquisition_mode('Kinetics')
cam.set_number_kinetics(kinetic_number)


cam.set_trigger_mode('External')
cam.start_acquisition()
print 'waiting, needs to get TTLs to proceed with each image'

proceed = cam.wait_for_kinetic()
while not proceed:
    proceed = cam.wait_for_kinetic()

image = cam.get_acquired_data(kinetic_number).asarray
image = np.reshape(image, (kinetic_number, stop_x, stop_y))
pyqtgraph.image(image)


cam.set_exposure_time(initial_exposure)
cam.set_image_region(initial_region)
cam.set_trigger_mode(initial_trigger_mode)
cam.start_live_display()

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
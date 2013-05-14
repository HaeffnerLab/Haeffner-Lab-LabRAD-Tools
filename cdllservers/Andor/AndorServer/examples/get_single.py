import labrad
from labrad.units import WithUnit
import numpy as np
import pyqtgraph
import time
from PyQt4 import QtGui

identify_exposure = WithUnit(0.5, 's')
stop_x = 658
stop_y = 496
image_region = (1,1,1,stop_x,1,stop_y)


cxn = labrad.connect()
cam = cxn.andor_server




cam.abort_acquisition()
initial_exposure = cam.get_exposure_time()
cam.set_exposure_time(identify_exposure)
initial_region = cam.get_image_region()
cam.set_image_region(*image_region)
cam.set_acquisition_mode('Single Scan')
cam.start_acquisition()
cam.wait_for_acquisition()
image = cam.get_acquired_data().asarray
np.save('sample', image)


image = np.reshape(image, (stop_x, stop_y))

pyqtgraph.image(image)


cam.set_exposure_time(initial_exposure)
cam.set_image_region(initial_region)
cam.start_live_display()

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
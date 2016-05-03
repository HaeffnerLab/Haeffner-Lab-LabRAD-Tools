
import pyqtgraph as pg
import numpy as np
pg.mkQApp()
w = pg.GraphicsLayoutWidget()
w.show()
vb = w.addViewBox()
img = pg.ImageItem(np.random.normal(size=(100,100)))
vb.addItem(img)
def mouseMoved(pos):
    print "Image position:", img.mapFromScene(pos)
    
w.scene().sigMouseMoved.connect(mouseMoved)

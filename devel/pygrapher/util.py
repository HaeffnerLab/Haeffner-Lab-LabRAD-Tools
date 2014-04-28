# 'import pyqtgraph as pg'

class color_chooser(object):
    
    colors = ['b','g','r','c','m','k']
        
    def __init__(self):
        self.index = 0
    
    def next_color(self):
        color_char = self.colors[self.index]
        self.index  = (self.index + 1) % len(self.colors)
        color = pg.mkColor(color_char)
        return color
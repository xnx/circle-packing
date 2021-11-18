# -*- coding: utf-8 -*-

import numpy as np
from pack_circles import pack_circles, svg_circles
from itertools import chain

def make_pattern(txt, fontdict = {'size':35,'weight':'bold'}, radius=0.45, size=(1.0,1.0), dpi=300):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.patches import Circle
    gray = lambda x: (x,x,x)
    #figure, with size and background color
    fig = Figure(size,dpi,facecolor=gray(0))
    #the canvas is what converts the figure to a bitmap
    canvas = FigureCanvas(fig)
    #add the dot, centered
    fig.add_artist(Circle((0.5,0.5),radius,color=gray(0.5)))
    #add the text, centered
    fig.text(0.5,0.5, txt, fontdict, color=gray(1.0), ha = 'center', va = 'center')
    #convert to a bitmap
    canvas.draw()
    #read the canvas as a numpy array
    w,h = canvas.get_width_height()
    img = np.frombuffer(canvas.buffer_rgba(), 'u1').reshape((h,w,4))
    #take just the red channel, and convert the values to their ordinal
    img = np.array(img[...,0])
    #undo the anti-aliasing by getting which target value each pixel is closest to
    values = np.array([0.0, 0.5, 1.0])*255
    img = np.argmin(np.abs(img[...,None] - values), axis=-1)
    return img


def ishihara(txt, colors):
    #generate pattern
    pattern = make_pattern(txt, dpi=600)
    h,w = pattern.shape
    #pack circles
    circles = pack_circles(pattern, radius_range=(0.002,0.02),greedy=False,n=2000,margin=1)
        
    #convert colors to index into a palette
    palette = np.unique(list(chain(*colors)))
    palette_map = dict((c,i) for i,c in enumerate(palette))
    colors = [[palette_map[c] for c in cc] for cc in colors]
    
    rand_color = lambda v: np.random.choice(colors[v-1])
    #pick colors for each circle based on which region they're centered on
    circles = [(y,x,r, rand_color(v)) for y,x,r,v in circles ]
        
    return circles, palette, (h,w)
    

if __name__ == '__main__':
    
    #colors
    distractor = ['#cf5826','#fca961','#fb8544']
    digit = ['#669f6c','#2a8263','#6a742e','#a0a352']
    colors = [distractor, digit]
    
    circles, palette, (h,w) = ishihara('74', colors)
    
    with open('74.svg','w') as out:
        out.write(svg_circles(circles, w, h, palette))
    
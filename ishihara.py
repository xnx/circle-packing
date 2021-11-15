# -*- coding: utf-8 -*-

import imageio as io
import numpy as np
from pack_circles import pack_circles, svg_circles
from itertools import chain

def ishihara(pattern, colors):
    #pack circles
    circles = pack_circles(pattern, radius_range=(0.002,0.02),greedy=False,n=2000,margin=1)
        
    #convert colors to index into a palette
    palette = np.unique(list(chain(*colors)))
    palette_map = dict((c,i) for i,c in enumerate(palette))
    colors = [[palette_map[c] for c in cc] for cc in colors]
    
    rand_color = lambda v: np.random.choice(colors[v-1])
    #pick colors for each circle based on which region they're centered on
    circles = [(y,x,r, rand_color(v)) for y,x,r,v in circles ]
        
    return circles, palette
    

if __name__ == '__main__':
    pattern = io.imread('74.png')
    #replace values with their (sorted) index
    for i, v in enumerate(np.unique(pattern)):
        pattern[pattern == v] = i
    #colors
    digit = ['#669f6c','#2a8263','#6a742e','#a0a352']
    distractor = ['#cf5826','#fca961','#fb8544']
    colors = [digit, distractor]
    
    circles, palette = ishihara(pattern, colors)
    h, w = pattern.shape
    with open('74.svg','w') as out:
        out.write(svg_circles(circles, w, h, palette))
    

import warnings

import numpy as np
import sys
from scipy.ndimage import distance_transform_edt

def pack_circles(mask, *, radii = None, n : int = None, margin : float = 1.0, radius_range : tuple[float,float] = (0.005, 0.05), greedy : bool = True, return_dists : bool = False):
    """
    Parameters
    ----------
    mask : array_like[(N,M), int]
        Circles will be packed into non-zero regions of mask of sufficient 
        size. Each circle's value will be taken from the pixel of mask it is
        centered on.
    
    radii : array_like[K, float], optional
        If not None: greedy mode is disabled, n and radius_range are ignored.
        The circles' radii will be set from this in reverse sorted order 
        (largest first).
    n : int, optional
        The maximum number of circles to pack.
        Ignored if radii is given.
        The default is None (unlimited).
    margin : float, optional
        The space between circles, in pixels.
        The default is 1.0.
    radius_range : tuple[int, int], optional
        The minimum and maximum circle radius, as a fraction of the shortest 
        edge of mask. Ignored if radii is given.
        The default is (0.005, 0.05).
    greedy : bool, optional
        Enable greedy mode: as many as n circles are placed randomly,
        starting from largest (radius_range[1]) to smallest (radius_range[0]).
        The default is True.
    return_dists : bool, optional
        Return a copy of mask populated with the distance to the closest 
        circle. Pixels within circles will have negative distance.
        The default is False.

    Raises
    ------
    ValueError
        
    Returns
    -------
    circles : list[tuple[int, int, float, int]]
        (y, x, radius, mask[y,x]) for each placed circle
    dists : array_like[(N,M), float]
        A copy of mask with the distance to the closest circle in each pixel.
        Pixels within circles will have negative distance.
    """
    mask = np.asarray(mask)
    if len(mask.shape) != 2:
        raise ValueError("mask must be 2D")
    
    if not greedy and radii is None and n is None:
        raise ValueError('Must specify either radii or n if not using greedy mode')
    
    if radii is not None:
        greedy = False
        radii = np.asarray(radii)
        if len(radii.shape) != 1:
            raise ValueError('radii must be None or 1D')
    
    min_dim = np.min(mask.shape)
    Rmin, Rmax = radius_range
    Rmin *= min_dim
    Rmax *= min_dim
    
    if greedy:
        #prepare for greedy mode
        if n is None:
            n = sys.maxsize #maximum list size -- essentially unbounded
    else:
        #not greedy mode
        if radii is None:
            radii = Rmin + (Rmax - Rmin)*np.random.beta(0.5, 1, size=n)
        radii.sort()
        Rmin = radii[0]
        Rmax = radii[-1]
    
    if Rmin < 1:
        warnings.warn(f'minimum circle radius less than 1 pixel ({Rmin}), setting to 1.')
        Rmin = 1
        
    # generate a radius mask, to track the maximum radius circle that may be
    # placed at each pixel
    Rmask = mask > 0
    #remove edges
    Rmask[0,:] = False
    Rmask[-1,:] = False
    Rmask[:,0] = False
    Rmask[:,-1] = False
    #calculate distance of each valid pixel from the nearest boundary
    Rmask = distance_transform_edt(Rmask)  
        
    Rmask_max = Rmask.max()
    if Rmask_max < Rmin:
        warnings.warn(f'mask max span ({Rmask_max}) less than min radius ({Rmin}): Impossible to place any circles')
        return []
    elif Rmask_max < Rmax:
        warnings.warn(f'mask max span ({Rmask_max}) less than max radius ({Rmax}): Reducing Rmax')
        Rmax = Rmask_max
    else:
        #this limits the number of pixels we have to update with each circle placement
        Rmask[Rmask > Rmax] = Rmax
    
    def insert_circle(r):
        #get all of the candidate locations for this radius, in flat coordinates
        locs = np.flatnonzero(Rmask >= r + margin)
        if locs.size == 0:
            return False
        
        #select a location at random
        loc = np.random.choice(locs)
        #convert back to image coordinates
        y,x = np.unravel_index(loc, mask.shape)
        circles.append((y,x,r,mask.flat[loc]))
        
        #update Rmask
        mask_r = int(np.ceil(r + Rmax))
        erosion_mask = np.ones( (1 + 2*mask_r,)*2 )
        erosion_mask[mask_r, mask_r] = 0
        erosion_mask = distance_transform_edt(erosion_mask) - r
        #indexing to deal with edge cases
        i0, j0 = 0,0
        i1, j1 = erosion_mask.shape
        y0, x0 = y - mask_r, x - mask_r
        y1, x1 = y + mask_r + 1, x + mask_r + 1
        if y0 < 0:
            i0 -= y0
            y0 = 0
        if y1 > Rmask.shape[0]:
            i1 -= (y1 - Rmask.shape[0])
            y1 = Rmask.shape[0]
        if x0 < 0:
            j0 -= x0
            x0 = 0
        if x1 > Rmask.shape[1]:
            j1 -= (x1 - Rmask.shape[1])
            x1 = Rmask.shape[1]
        # the pixels new distance will be to whichever circle it's closest to
        Rmask[y0:y1, x0:x1] = np.minimum(Rmask[y0:y1, x0:x1], erosion_mask[i0:i1,j0:j1])
        return True
        
    #generate circles, starting with the largest
    circles = []
    if greedy:
        #insert circles as long as there's space
        while Rmin + margin <= Rmax:
            #try to insert as many circle as possible at this size
            while insert_circle(Rmax - margin):
                pass
            Rmax = Rmask.max()
    else:
        #just pack the given radii into the space
        for r in radii[::-1]:
            #are we done?
            if Rmin + margin > Rmax:
                break
            #is there any chance of inserting this circle?
            if r + margin > Rmax:
                if radii[0] + margin > Rmax:
                    #there are no possible spots left
                    break
                else:
                    continue
            
            if not insert_circle(r):
                #update Rmax 
                Rmax = Rmask.max()
    
    if return_dists:
        return circles, Rmask
    else:
        return circles

def svg_circles(circles, width, height, palette):
    from textwrap import dedent
    svg = dedent(f'''\
        <?xml version="1.0" encoding="utf-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
            width="{width}" height="{height}" >
        <defs>
        <style type="text/css"><![CDATA[
            circle {{stroke: none; }}\n''')
    for i,c in enumerate(palette):
        svg += f'    .c{i} {{fill: {c};}}\n'
    svg += dedent('''\
                  ]]></style>
                  </defs>\n''')
    for y,x,r,v in circles:
        svg += f'<circle cx="{x}" cy="{y}" r="{r:0.4}" class="c{v}" />\n'
    svg += '</svg>\n'
    return svg

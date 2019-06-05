from PIL import Image
import numpy as np
from circles import Circle, Circles

class ShapeFill(Circles):
    """A class for filling a shape with circles."""

    def __init__(self, img_name, *args, **kwargs):
        """Initialize the class with an image specified by filename.

        The image should be black on a white background.

        The maximum and minimum circle sizes are given by rho_min and rho_max
        which are proportions of the minimum image dimension.
        The maximum number of circles to pack is given by n
        colours is a list of SVG fill colour specifiers (a default palette is
        used if this argument is not provided).

        """

        self.img_name = img_name
        # Read the image and set the image dimensions; hand off to the
        # superclass for other initialization.
        self.read_image(img_name)
        dim = min(self.width, self.height)
        super().__init__(self.width, self.height, dim, *args, **kwargs)

    def read_image(self, img_name):
        """Read the image into a NumPy array and invert it."""

        img = Image.open(img_name).convert('1')
        self.width, self.height = img.width, img.height
        self.img = 255 - np.array(img.getdata()).reshape(img.height, img.width)
        self.img = self.img.T

    def _circle_fits(self, icx, icy, r):
        """If I fits, I sits."""

        if icx-r < 0 or icy-r < 0:
            return False
        if icx+r >= self.width or icy+r >= self.height:
            return False

        if not all((self.img[icx-r,icy], self.img[icx+r,icy],
                self.img[icx,icy-r], self.img[icx,icy+r])):
            return False
        return True

    def apply_circle_mask(self, icx, icy, r):
        """Zero all elements of self.img in circle at (icx, icy), radius r."""

        x, y = np.ogrid[0:self.width, 0:self.height]
        r2 = (r+1)**2
        mask = (x-icx)**2 + (y-icy)**2 <= r2
        self.img[mask] = 0

    def _place_circle(self, r, c_idx=None):
        """Attempt to place a circle of radius r within the image figure.
 
        c_idx is a list of indexes into the self.colours list, from which
        the circle's colour will be chosen. If None, use all colours.

        """

        if not c_idx:
            c_idx = range(len(self.colours))

        # Get the coordinates of all non-zero image pixels
        img_coords = np.nonzero(self.img)
        if not img_coords:
            return False

        # The guard number: if we don't place a circle within this number
        # of trials, we give up.
        guard = self.guard
        # For this method, r must be an integer. Ensure that it's at least 1.
        r = max(1, int(r))
        while guard:
            # Pick a random candidate pixel...
            i = np.random.randint(len(img_coords[0]))
            icx, icy = img_coords[0][i], img_coords[1][i]
            # ... and see if the circle fits there
            if self._circle_fits(icx, icy, r):
                self.apply_circle_mask(icx, icy, r)
                circle = Circle(icx, icy, r, icolour=np.random.choice(c_idx))
                self.circles.append(circle)
                return True
            guard -= 1
        print('guard reached.')
        return False

if __name__ == '__main__':
    # Land colours, sea colours.
    c1 = ['#b6950c', '#9d150b']
    c2 = ['#173f5f', '#20639b', '#3caea3']

    # First fill the land silhouette.
    shape = ShapeFill('uk.png', n=3000, rho_max=0.01, colours=c1+c2)
    shape.guard = 1000
    shape.make_circles(c_idx=range(len(c1)))
    shape.make_svg('uk-1.svg')

    # Now load the image again, invert it and fill the sea with circles.
    shape.read_image('uk.png')
    shape.img = 255 - shape.img
    shape.n = 5000
    shape.make_circles(c_idx=[len(c1)+i for i in range(len(c2))])
    shape.make_svg('uk-2.svg')
    

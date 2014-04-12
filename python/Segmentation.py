from PIL import Image
from numpy import *
from pylab import *
from scipy.ndimage import filters

class SegmentationData:
    _template = (0,0,0,0)
    _imageFilename = ""
    _boxes = []
    _currentBox = None

    def newBox(self):
        self._currentBox = (0,0,0,0)

    def goodBox(self):
        if self._currentBox != None:
            self._boxes.append(self._currentBox)

    def cancelBox(self):
        self._currentBox = None

    def resetTemplate(self):
        self._template = (0,0,0,0)

    def template(self, tplate=None):
        if tplate != None:
            self._template = tplate
        else:
            return self._template

    def loadImage(self, fname):
        self._imageFilename = fname
        self.template((0,0,0,0))
        self._boxes = []
        self._currentBox = None

        self._image = array(Image.open(fname).convert('L'))
        im1 = filters.gaussian_filter(self._image, 1)
        im2 = filters.gaussian_filter(self._image, 2)
        im4 = filters.gaussian_filter(self._image, 4)
        im8 = filters.gaussian_filter(self._image, 8)
        self._features = []
        self._features.append(im1)
        self._features.append(im2)
        self._features.append(im4)
        self._features.append(im8)
        self._features.append(filters.gaussian_laplace(self._image, 1))
        self._features.append(filters.gaussian_laplace(self._image, 2))
        self._features.append(filters.gaussian_laplace(self._image, 4))
        self._features.append(filters.gaussian_laplace(self._image, 8))

    def boxes(self):
        return self._boxes

    def getCurrentBox(self):
        return self._currentBox

    def currentBugClickAt(self, mx, my):
        (x1,y1,x2,y2) = self.template()
        w = x2-x1
        h = y2-y1
        self._currentBox = (int(mx-w/2), int(my-h/2),
                            int(mx+w/2), int(my+h/2))

    def random(self):
        print "fff"
        Image.fromarray(self._features[0]).save('g05.jpg')
        Image.fromarray(self._features[1]).save('g10.jpg')
        Image.fromarray(self._features[2]).save('g15.jpg')
        Image.fromarray(self._features[3]).save('g20.jpg')

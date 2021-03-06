# Class to process specemin template and specemin selection to determine
# best location for bounding boxes
#
# Technology for Nature. British Natural History Museum insect specimen
# segmentation project.
#
# Copyright (C) 2014    Syed Zahir Bokhari, Prof. Michael Terry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

from PIL import Image
from numpy import *
from pylab import *
from scipy.ndimage import filters
from math import *
import logging
import random

class SegmentationData:
    _imageFilename = ""
    _imageSize = (0,0)
    _boxes = []
    _boxCount = 0
    _currentBox = None
    _currentBoxId = -1

    _templateBox = (0,0,0,0)
    _template = []
    _templatePositions = []

    pcount = 100
    stepx = 15
    stepy = 15
    scales = [0.75, 1.0, 1.25, 1.5]

    def __init__(self, logfile=None):
        if logfile:
            logging.basicConfig(filename=logfile, level=logging.DEBUG, format="- %(message)s")

        logging.info("Using logfile %s" % logfile)

    def newBox(self):
        self._currentBox = (0,0,0,0)
        self._currentBoxId = self._boxCount

    def goodBox(self):
        if self._currentBox != None:
            self._boxes.append((self._currentBoxId, self._currentBox))
            (x1,y1,x2,y2) = self._currentBox
            logging.debug("Place box #%s on specemin at (%d,%d,%d,%d)"
                % (self._currentBoxId, x1,y1,x2,y2))
            self._boxCount += 1
            self._currentBox = None
            self._currentBoxId = -1

    def cancelBox(self):
        self._currentBox = None
        logging.debug("Delete active box #%d" % self._currentBoxId)

    def resetTemplate(self):
        self._templateBox = (0,0,0,0)
        logging.debug("Reset Template")

    def templateBox(self, tplate=None):
        if tplate != None:
            self._templateBox = tplate
        else:
            return self._templateBox

    def confirmTemplate(self):
        self._template = []
        self._templatePositions = []
        (x1,y1,x2,y2) = self._templateBox
        self._templateBox = (min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2))
        (x1,y1,x2,y2) = self._templateBox
        logging.debug("New template at (%d,%d,%d,%d)" % self._templateBox)
        w = int(x2-x1)/2
        h = int(y2-y1)/2
        for i in range(self.pcount):
            rx = int(random.randrange(-w,w))
            ry = int(random.randrange(-h,h))
            self._templatePositions.append((rx,ry))
            self._template.append(self._features[ry+y1+h,rx+x1+w,:])

        self._template = dstack(self._template)

    def loadImage(self, fname):
        self._imageFilename = fname
        self.templateBox((0,0,0,0))
        self._boxes = []
        self._currentBox = None
        logging.info("Load image %s" % fname)

        self._image = array(Image.open(fname).convert('L'), dtype='f')/255
        (h,w) = shape(self._image)
        self._imageSize = (w,h)
        im1 = filters.gaussian_filter(self._image, 2)
        im2 = filters.gaussian_filter(self._image, 3)
        im4 = filters.gaussian_filter(self._image, 4)
        im8 = filters.gaussian_filter(self._image, 5)

        features = []
        features.append(im1)
        features.append(im2)
        features.append(im4)
        features.append(im8)
        features.append(filters.gaussian_laplace(self._image, 2))
        features.append(filters.gaussian_laplace(self._image, 3))
        features.append(filters.gaussian_laplace(self._image, 4))
        features.append(filters.gaussian_laplace(self._image, 5))
        features.append(filters.sobel(im4, 0))
        features.append(filters.sobel(im8, 0))
        features.append(filters.sobel(im4, 1))
        features.append(filters.sobel(im8, 1))
        self._features = dstack(features)

    def saveCSV(self, fname):
        f = open(fname, 'w')
        f.write("\"Source Image\", %s\n" % self._imageFilename)

        for (i, (x1,y1,x2,y2)) in self._boxes:
            f.write("\"Box %d\", %d, %d, %d, %d\n" % (i,x1,y1,x2,y2))

        (x1,y1,x2,y2) = self._templateBox
        f.write("\"Temp\", %d, %d, %d, %d\n" % (x1,y1,x2,y2))

        logging.info("Saving CSV %s" % fname)

    def boxes(self):
        return self._boxes

    def getCurrentBox(self):
        return self._currentBox

    def currentBugClickAt(self, mx, my):
        logging.debug("New specemin click at (%d, %d)" % (mx, my))
        (x1,y1,x2,y2) = self.templateBox()
        tw = int((x2-x1)/2)
        th = int((y2-y1)/2)
        (width, height) = self._imageSize
        scores = []
        for iy in range(-th/2, th/2+self.stepy, self.stepy):
            for ix in range(-tw/2, tw/2+self.stepx, self.stepx):
                for s in self.scales:
                    if not ((mx+ix-tw*s < 0) or (my+iy-th*s < 0) or
                            (mx+ix+tw*s > width) or (my+iy+th*s > height)):
                        target = []
                        for i in range(self.pcount):
                            (px,py) = self._templatePositions[i]
                            target.append(self._features[my+iy+int(py*s),mx+ix+int(px*s),:])
                        target = dstack(target)
                        diff = target - self._template
                        scores.append((sum(diff*diff), s,  mx+ix, my+iy))
        (_, s, bestx, besty) = min(scores)
        self._currentBox = (bestx-tw*s, besty-th*s, bestx+tw*s, besty+th*s)
        logging.debug("Box placed automatically at (%d, %d, %d, %d)"
            % self._currentBox)

    def chooseBox(self,pos):
        (mx,my) = pos

        if self._currentBox != None and self._currentBox != (0,0,0,0):
            self._boxes.append((self._currentBoxId, self._currentBox))

        for i in range(len(self._boxes)):
            (j, (x1,y1,x2,y2)) = self._boxes[i]
            if mx > x1 and mx < x2 and my > y1 and my < y2:
                self._currentBox = (x1,y1,x2,y2)
                self._currentBoxId = j
                logging.debug("User selected box #%d" % j)
                del self._boxes[i]
                break

    def startCBPan(self, mx, my):
        if self._currentBox != None and self._currentBox != (0,0,0,0):
            self._oldPos = (mx,my)
            logging.debug("Pan box #%d" % self._currentBoxId)

    def doCBPan(self, mx,my):
        if self._currentBox != None and self._currentBox != (0,0,0,0):
            (ox,oy) = self._oldPos
            dx = mx - ox
            dy = my - oy
            (x1,y1,x2,y2) = self._currentBox
            self._currentBox = (x1+dx,y1+dy,x2+dx,y2+dy)
            self._oldPos = (mx,my)

    def endCBPan(self):
        self._oldPos = None

    def startCBResize(self, mx, my, kind):
        if self._currentBox != None and self._currentBox != (0,0,0,0):
            self._oldPos = (mx,my)
            self._resizeKind = kind
            logging.debug("Resize box #%d" % self._currentBoxId)

    def doCBResize(self, mx,my):
        if self._currentBox != None and self._currentBox != (0,0,0,0):
            (ox,oy) = self._oldPos
            dx = mx - ox
            dy = my - oy
            (x1,y1,x2,y2) = self._currentBox
            if self._resizeKind == 0:
                self._currentBox = (x1+dx,y1+dy,x2,y2)
            elif self._resizeKind == 1:
                self._currentBox = (x1,y1,x2+dx,y2+dy)
            elif self._resizeKind == 2:
                self._currentBox = (x1,y1+dy,x2+dx,y2)
            elif self._resizeKind == 3:
                self._currentBox = (x1+dx,y1,x2,y2+dy)
            elif self._resizeKind == 4:
                self._currentBox = (x1,y1+dy,x2,y2)
            elif self._resizeKind == 5:
                self._currentBox = (x1,y1,x2,y2+dy)
            elif self._resizeKind == 6:
                self._currentBox = (x1+dx,y1,x2,y2)
            elif self._resizeKind == 7:
                self._currentBox = (x1,y1,x2+dx,y2)

            self._oldPos = (mx,my)

    def endCBResize(self):
        self._oldPos = None

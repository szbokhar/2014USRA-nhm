# Class for image interaction display in the python segmentation program
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

from PySide import QtGui, QtCore
from ToolPanel import *
from Segmentation import *

class ImagePanel(QtGui.QLabel):

    # Enum for interaction modes
    Nothing, TemplateSelect, SpeciminSelect, BoxSelect, PanCB, ResizeCB = range(6)

    # Current intercation mode
    _paneMode = Nothing

    # Signals emitted by the image panel
    sigTemplate = QtCore.Signal(str)
    sigBugSelection = QtCore.Signal(str)
    sigBoxSelection = QtCore.Signal(str)

    # Image Scale
    _imageScale = 1

    def __init__(self, segData, parent=None):
        super(ImagePanel, self).__init__(parent)
        self.setMaximumSize(924,720)
        self.show()
        self.data = segData
        self.setMouseTracking(True)
        self._resizeCursorH = QtGui.QCursor(QtCore.Qt.SizeHorCursor)
        self._resizeCursorV = QtGui.QCursor(QtCore.Qt.SizeVerCursor)
        self._resizeCursorB = QtGui.QCursor(QtCore.Qt.SizeBDiagCursor)
        self._resizeCursorF = QtGui.QCursor(QtCore.Qt.SizeFDiagCursor)
        self._panCursor = QtGui.QCursor(QtCore.Qt.CrossCursor)
        self._normalCursor = QtGui.QCursor(QtCore.Qt.ArrowCursor)


    # Connect slots to Image Panel signals
    def setToolPane(self, tp):
        tp.sigOpenFile.connect(self.loadImage)
        tp.btnNextBug.clicked.connect(self.selectNewSpecimin)
        tp.btnCancelBug.clicked.connect(self.cancelNewSpecimin)
        tp.btnSelectTemplate.clicked.connect(self.selectNewTemplate)
        tp.btnSelectBox.clicked.connect(self.toggleSelectBox)

    # --------------------------------
    # Slots
    def selectNewTemplate(self):
        if self._paneMode == ImagePanel.Nothing:
            self._paneMode = ImagePanel.TemplateSelect
            self.data.resetTemplate()
            self.repaint()
            self.sigTemplate.emit("ButtonPressed")
            self.setMouseTracking(False)

    def loadImage(self, fname):
        sz = self.size()
        self.pix = QtGui.QPixmap(fname)
        iw = float(self.pix.width())

        self.pix = self.pix.scaled(sz.width(), sz.height(), QtCore.Qt.KeepAspectRatio)
        self.setAlignment(QtCore.Qt.AlignTop)
        self.setPixmap(self.pix)
        lw = float(self.pix.width())

        self.repaint()
        self.data.loadImage(fname)
        self._imageScale = iw/lw

    def selectNewSpecimin(self):
        if self._paneMode == self.Nothing:
            self._paneMode = self.SpeciminSelect
            self.data.newBox()
            self.sigBugSelection.emit("Start")
            self.repaint()
        elif self._paneMode == self.SpeciminSelect:
            self.data.goodBox()
            self.data.newBox()
            self.sigBugSelection.emit("Confirmed")
            self.repaint()

        self.repaint()

    def cancelNewSpecimin(self):
        if self._paneMode == self.SpeciminSelect:
            self._paneMode = self.Nothing
            self.data.cancelBox()
            self.repaint()
            self.sigBugSelection.emit("Cancelled")
        elif self._paneMode == self.BoxSelect:
            self.data.cancelBox()
            self.repaint()

    def toggleSelectBox(self):
        if self._paneMode == self.Nothing:
            self._paneMode = self.BoxSelect
            self.sigBoxSelection.emit("BoxSelectOn")
        elif self._paneMode == self.BoxSelect:
            self._paneMode = self.Nothing
            self.sigBoxSelection.emit("BoxSelectOff")
            self.data.goodBox()
            self.repaint()

    # -----------------------------------------
    # Virtual methods
    def mousePressEvent(self, ev):
        s = self._imageScale
        mx = s*ev.x()
        my = s*ev.y()
        c = 10
        if self.data.getCurrentBox() != None and isPointInBox(mx,my,c,self.data.getCurrentBox()):
            (x1,y1,x2,y2) = self.data.getCurrentBox()
            self._oldPaneMode = self._paneMode

            if isPointIn(mx,my,x1-c,y1-c,x1+c,y1+c):
                self._paneMode = ImagePanel.ResizeCB
                self.data.startCBResize(s*ev.x(), s*ev.y(),0)
            if isPointIn(mx,my,x2-c,y2-c,x2+c,y2+c):
                self._paneMode = ImagePanel.ResizeCB
                self.data.startCBResize(s*ev.x(), s*ev.y(),1)

            elif isPointIn(mx,my,x2-c,y1-c,x2+c,y1+c):
                self._paneMode = ImagePanel.ResizeCB
                self.data.startCBResize(s*ev.x(), s*ev.y(),2)
            elif isPointIn(mx,my,x1-c,y2-c,x1+c,y2+c):
                self._paneMode = ImagePanel.ResizeCB
                self.data.startCBResize(s*ev.x(), s*ev.y(),3)

            elif isPointIn(mx,my,x1+c,y1-c,x2-c,y1+c):
                self._paneMode = ImagePanel.ResizeCB
                self.data.startCBResize(s*ev.x(), s*ev.y(),4)
            elif isPointIn(mx,my,x1+c,y2-c,x2-c,y2+c):
                self._paneMode = ImagePanel.ResizeCB
                self.data.startCBResize(s*ev.x(), s*ev.y(),5)

            elif isPointIn(mx,my,x1-c,y1+c,x1+c,y2-c):
                self._paneMode = ImagePanel.ResizeCB
                self.data.startCBResize(s*ev.x(), s*ev.y(),6)
            elif isPointIn(mx,my,x2-c,y1+c,x2+c,y2-c):
                self._paneMode = ImagePanel.ResizeCB
                self.data.startCBResize(s*ev.x(), s*ev.y(),7)

            elif isPointIn(mx,my,x1+c,y1+c,x2-c,y2-c):
                self._paneMode = ImagePanel.PanCB
                self.data.startCBPan(s*ev.x(), s*ev.y())

        elif self._paneMode == ImagePanel.TemplateSelect:
            (x1,y1,x2,y2) = self.data.templateBox()
            self.data.templateBox((s*ev.x(), s*ev.y(), x2, y2))
            self.setMouseTracking(False)
        elif self._paneMode == ImagePanel.SpeciminSelect:
            self.data.goodBox()
            self.sigBugSelection.emit("Confirmed")
            self.data.newBox()
            self.data.currentBugClickAt(s*ev.x(), s*ev.y())
            self.repaint()
        elif self._paneMode == ImagePanel.BoxSelect:
            self.data.chooseBox((s*ev.x(), s*ev.y()))
            self.repaint()

    def mouseReleaseEvent(self, ev):
        s = self._imageScale
        if self._paneMode == ImagePanel.TemplateSelect:
            (x1,y1,x2,y2) = self.data.templateBox()
            self.data.templateBox((x1, y1, s*ev.x(), s*ev.y()))
            self._paneMode = ImagePanel.Nothing
            self.sigTemplate.emit("TemplateSelected")
            self.data.confirmTemplate()
            self.setMouseTracking(True)
        elif self._paneMode == ImagePanel.PanCB:
            self._paneMode = self._oldPaneMode
            self.data.endCBPan()
        elif self._paneMode == ImagePanel.ResizeCB:
            self._paneMode = self._oldPaneMode
            self.data.endCBResize()

    def mouseMoveEvent(self, ev):
        s = self._imageScale
        if self._paneMode == ImagePanel.PanCB:
            self.data.doCBPan(s*ev.x(), s*ev.y())
            self.repaint()
        if self._paneMode == ImagePanel.ResizeCB:
            self.data.doCBResize(s*ev.x(), s*ev.y())
            self.repaint()
        elif self._paneMode == ImagePanel.TemplateSelect:
            (x1,y1,x2,y2) = self.data.templateBox()
            self.data.templateBox((x1, y1, s*ev.x(), s*ev.y()))
            self.repaint()
        elif self.data.getCurrentBox() != None:
            mx = s*ev.x()
            my = s*ev.y()
            (x1,y1,x2,y2) = self.data.getCurrentBox()
            c = 10
            if isPointIn(mx,my,x1-c,y1-c,x2+c,y2+c):
                if isPointIn(mx,my,x1-c,y1-c,x1+c,y1+c) or isPointIn(mx,my,x2-c,y2-c,x2+c,y2+c):
                    self.setCursor(self._resizeCursorF)
                elif isPointIn(mx,my,x2-c,y1-c,x2+c,y1+c) or isPointIn(mx,my,x1-c,y2-c,x1+c,y2+c):
                    self.setCursor(self._resizeCursorB)
                elif isPointIn(mx,my,x1+c,y1-c,x2-c,y1+c) or isPointIn(mx,my,x1+c,y2-c,x2-c,y2+c):
                    self.setCursor(self._resizeCursorV)
                elif isPointIn(mx,my,x1-c,y1+c,x1+c,y2-c) or isPointIn(mx,my,x2-c,y1+c,x2+c,y2-c):
                    self.setCursor(self._resizeCursorH)
                else:
                    self.setCursor(self._panCursor)
            else:
                self.setCursor(self._normalCursor)

    def paintEvent(self, ev):
        super(ImagePanel, self).paintEvent(ev)

        s = 1/self._imageScale

        qp = QtGui.QPainter()
        qp.begin(self)

        qp.setPen(QtGui.QColor(255,0,0))
        (x1,y1,x2,y2) = self.data.templateBox()
        qp.drawRect(s*x1,s*y1,s*(x2-x1), s*(y2-y1))

        qp.setPen(QtGui.QColor(0,0,255))

        for box in self.data.boxes():
            (_, (x1,y1,x2,y2)) = box
            qp.drawRect(s*x1,s*y1,s*(x2-x1), s*(y2-y1))

        qp.setPen(QtGui.QColor(0,255,0))
        if self.data.getCurrentBox() != None:
            (x1,y1,x2,y2) = self.data.getCurrentBox()
            qp.drawRect(s*x1,s*y1,s*(x2-x1), s*(y2-y1))

        qp.end()

def isPointIn(x,y,x1,y1,x2,y2):
    return x > x1 and x < x2 and y > y1 and y < y2

def isPointInBox(x,y,pad,box):
    (x1,y1,x2,y2) = box
    return isPointIn(x,y,x1-pad,y1-pad,x2+pad,y2+pad)

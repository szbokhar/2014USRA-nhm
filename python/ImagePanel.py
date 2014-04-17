from PySide import QtGui, QtCore
from ToolPanel import *
from Segmentation import *

class ImagePanel(QtGui.QLabel):

    # Enum for interaction modes
    Nothing, TemplateSelect, SpeciminSelect, BoxSelect = range(4)

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
        if self._paneMode == ImagePanel.TemplateSelect:
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

    def mouseMoveEvent(self, ev):
        s = self._imageScale
        if self._paneMode == ImagePanel.TemplateSelect:
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
            (x1,y1,x2,y2) = box
            qp.drawRect(s*x1,s*y1,s*(x2-x1), s*(y2-y1))

        qp.setPen(QtGui.QColor(0,255,0))
        if self.data.getCurrentBox() != None:
            (x1,y1,x2,y2) = self.data.getCurrentBox()
            qp.drawRect(s*x1,s*y1,s*(x2-x1), s*(y2-y1))

        qp.end()

def isPointIn(x,y,x1,y1,x2,y2):
    return x > x1 and x < x2 and y > y1 and y < y2

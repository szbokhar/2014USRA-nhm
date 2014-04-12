from PySide import QtGui, QtCore
from ToolPanel import *
from Segmentation import *

class ImagePanel(QtGui.QLabel):

    # Enum for interaction modes
    Nothing, TemplateSelect, SpeciminSelect, SpeciminSelected= range(4)

    # Current intercation mode
    _paneMode = Nothing

    # Signals emitted by the image panel
    sigNewTemplate = QtCore.Signal(str)
    sigBugSelection = QtCore.Signal(str)

    # Image Scale
    _imageScale = 1

    def __init__(self, segData, parent=None):
        super(ImagePanel, self).__init__(parent)
        self.setMaximumSize(924,720)
        self.show()
        self.data = segData

    # Connect slots to Image Panel signals
    def setToolPane(self, tp):
        tp.sigOpenFile.connect(self.loadImage)
        tp.btnNextBug.clicked.connect(self.selectNewSpecimin)
        tp.btnCancelBug.clicked.connect(self.cancelNewSpecimin)
        tp.btnSelectTemplate.clicked.connect(self.selectNewTemplate)

    # --------------------------------
    # Slots
    def selectNewTemplate(self):
        self._paneMode = ImagePanel.TemplateSelect
        self.data.resetTemplate()
        self.repaint()

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

    # -----------------------------------------
    # Virtual methods
    def mousePressEvent(self, ev):
        s = self._imageScale
        if self._paneMode == ImagePanel.TemplateSelect:
            (x1,y1,x2,y2) = self.data.template()
            self.data.template((s*ev.x(), s*ev.y(), x2, y2))
        elif self._paneMode == ImagePanel.SpeciminSelect:
            self.data.currentBugClickAt(s*ev.x(), s*ev.y())
            self.repaint()

    def mouseReleaseEvent(self, ev):
        s = self._imageScale
        if self._paneMode == ImagePanel.TemplateSelect:
            (x1,y1,x2,y2) = self.data.template()
            self.data.template((x1, y1, s*ev.x(), s*ev.y()))
            self._paneMode = ImagePanel.Nothing
            self.sigNewTemplate.emit("New template selected")

    def mouseMoveEvent(self, ev):
        s = self._imageScale
        if self._paneMode == ImagePanel.TemplateSelect:
            (x1,y1,x2,y2) = self.data.template()
            self.data.template((x1, y1, s*ev.x(), s*ev.y()))
            self.repaint()

    def paintEvent(self, ev):
        super(ImagePanel, self).paintEvent(ev)

        s = 1/self._imageScale

        qp = QtGui.QPainter()
        qp.begin(self)

        qp.setPen(QtGui.QColor(255,0,0))
        (x1,y1,x2,y2) = self.data.template()
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

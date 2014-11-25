from PySide import QtCore, QtGui
import cv2
import numpy as np

from AppData import *
from Util import *
from Pt import *


class ControlPanel(QtGui.QFrame):
    """A QtWidget that holds all the control buttons for the application."""

    # Signals emmited by the control panel

    def __init__(self, data, parent=None):
        super(ControlPanel, self).__init__(parent)
        self.data = data
        self.initUI()

    def initUI(self):
        # Setup the panel and layout
        panelLayout = QtGui.QVBoxLayout(self)
        self.setLayout(panelLayout)

        # Create the Textbox label
        self.lblTextLabel = QtGui.QLabel()
        self.lblTextLabel.setText('ID:')

        # Create the Barcode label
        self.txtBarcode = QtGui.QLineEdit()
        self.txtBarcode.setText('')
        self.txtBarcode.setMinimumWidth(100)
        self.txtBarcode.setEnabled(False)

        # Create frame to hold label and textbox side by side
        self.pnlBarcode = QtGui.QFrame()
        barcodePanelLayout = QtGui.QHBoxLayout(self)
        self.pnlBarcode.setLayout(barcodePanelLayout)

        # Place all buttons and labels on the panel
        barcodePanelLayout.addWidget(self.lblTextLabel)
        barcodePanelLayout.addWidget(self.txtBarcode)
        panelLayout.addStretch(1)
        panelLayout.addWidget(self.pnlBarcode)
        panelLayout.addStretch(1)

        # Connect slots for the buttion actions
        self.txtBarcode.textEdited.connect(self.data.newBugIdEntered)

    def setCurrentBugId(self, string):
        self.txtBarcode.setText(string)
        self.txtBarcode.selectAll()
        self.txtBarcode.setFocus(QtCore.Qt.OtherFocusReason)


class BigLabel(QtGui.QLabel):
    """The large sized label with convienence function for displaying images
    in numpy arrays, as well as signals for mouse events"""

    originalSize = (640, 360)
    resizeScale = (1.0, 1.0)

    sigMousePress = QtCore.Signal(QtGui.QMouseEvent, float)
    sigMouseMove = QtCore.Signal(QtGui.QMouseEvent, float)
    sigMouseRelease = QtCore.Signal(QtGui.QMouseEvent, float)
    sigScroll = QtCore.Signal(QtGui.QWheelEvent, float)

    def __init__(self, data, parent=None):
        super(BigLabel, self).__init__(parent)
        self.data = data
        self.initUI()
        self.setMouseTracking(True)
        self.imageScaleRatio = 1
        # self.setPixmap(QtGui.QPixmap(self.originalSize[0], self.originalSize[1]))
        self.generateInitialImage()

    def initUI(self):
        self.setAlignment(QtCore.Qt.AlignTop)

    def setImage(self, cvImage):
        if cvImage.ndim == 2:
            cvImage = cv2.cvtColor(cvImage, cv2.cv.CV_GRAY2BGRA)
        else:
            cvImage = cv2.cvtColor(cvImage, cv2.cv.CV_BGR2BGRA)
        originalSize = (cvImage.shape[1], cvImage.shape[0])
        (w, h, rat) = computeImageScaleFactor(originalSize, self.getCurrentSize())
        self.imageScaleRatio = rat
        cvImage = cv2.resize(cvImage, (w, h))
        img = QtGui.QImage(cvImage, cvImage.shape[1], cvImage.shape[0],
                           cvImage.strides[0], QtGui.QImage.Format_ARGB32)

        self.setPixmap(QtGui.QPixmap.fromImage(img))

    def mousePressEvent(self, ev):
        self.sigMousePress.emit(ev, self.imageScaleRatio)

    def mouseMoveEvent(self, ev):
        self.sigMouseMove.emit(ev, self.imageScaleRatio)

    def mouseReleaseEvent(self, ev):
        self.sigMouseRelease.emit(ev, self.imageScaleRatio)

    def wheelEvent(self, ev):
        self.sigScroll.emit(ev, self.imageScaleRatio)

    def newResizeScale(self, scale):
        self.resizeScale = scale
        (sx, sy) = scale
        (w, h) = self.originalSize
        self.resize(int(w*sx), int(h*sy))

    def getCurrentSize(self):
        (sx, sy) = self.resizeScale
        (w, h) = self.originalSize
        return (w*sx, h*sy)

    def generateInitialImage(self):
        (w,h) = self.originalSize
        img = np.zeros((h, w, 4), np.uint8)
        s = w/(2*20+1)
        for i in range(0,w+100,s)[0::2]:
            cv2.rectangle(img, (i,0), (i+s, 2), (0,0,0,128), -1)
            cv2.rectangle(img, (i,h-1), (i+s, h-3), (0,0,0,128), -1)
        s = h/(2*10+1)
        for i in range(0,h+100,s)[0::2]:
            cv2.rectangle(img, (0,i), (2,i+s), (0,0,0,128), -1)
            cv2.rectangle(img, (w-1,i), (w-3,i+s), (0,0,0,128), -1)

        b = 4*h/10
        for text in ['Drag and Drop tray scan image file here',
                     'or load it from the File menu']:
            ((tw,th), _) = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 1)
            cv2.putText(img, text, ((w-tw)/2, b), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0,255), 2)
            b += th + 10
        self.setImage(img)


class SmallLabel(QtGui.QLabel):
    """The small sized label with convienence function for displaying images
    in numpy arrays"""

    originalSize = (320, 180)
    resizeScale = (1.0, 1.0)

    def __init__(self, data, parent=None):
        super(SmallLabel, self).__init__(parent)
        self.data = data
        self.initUI()
        self.imageScaleRatio = 1
        # self.setPixmap(QtGui.QPixmap(self.originalSize[0], self.originalSize[1]))
        self.generateInitialImage()

    def initUI(self):
        self.setAlignment(QtCore.Qt.AlignTop)

    def setImage(self, cvImage):
        if cvImage.ndim == 2:
            cvImage = cv2.cvtColor(cvImage, cv2.cv.CV_GRAY2BGRA)
        else:
            cvImage = cv2.cvtColor(cvImage, cv2.cv.CV_BGR2BGRA)
        originalSize = (cvImage.shape[1], cvImage.shape[0])
        (w, h, rat) = computeImageScaleFactor(originalSize, self.getCurrentSize())
        self.imageScaleRatio = rat
        cvImage = cv2.resize(cvImage, (w, h))
        img = QtGui.QImage(cvImage, cvImage.shape[1], cvImage.shape[0],
                           cvImage.strides[0], QtGui.QImage.Format_ARGB32)

        self.setPixmap(QtGui.QPixmap.fromImage(img))

    def newResizeScale(self, scale):
        self.resizeScale = scale
        (sx, sy) = scale
        (w, h) = self.originalSize
        self.resize(int(w*sx), int(h*sy))

    def getCurrentSize(self):
        (sx, sy) = self.resizeScale
        (w, h) = self.originalSize
        return (w*sx, h*sy)

    def generateInitialImage(self):
        (w,h) = self.originalSize
        img = np.zeros((h, w, 4), np.uint8)
        img[:,:,:] = [128,128,128,128]
        self.setImage(img)

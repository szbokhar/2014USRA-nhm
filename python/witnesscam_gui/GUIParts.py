from PySide import QtCore, QtGui
from os import listdir
from mimetypes import guess_type
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

class FileBrowser(QtGui.QFrame):

    sigFileSelected = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(FileBrowser, self).__init__(parent)
        self.initUI()

        self.currentItem = None
        self.currentPath = None
        self.imageFilename = None

    def initUI(self):
        panelLayout = QtGui.QVBoxLayout(self)
        self.setLayout(panelLayout)

        bottomPanel = QtGui.QFrame(self)
        bottomLayout = QtGui.QHBoxLayout(self)
        bottomPanel.setLayout(bottomLayout)

        self.treeFileBrowser = QtGui.QTreeWidget(self)
        self.treeFileBrowser.setHeaderItem(QtGui.QTreeWidgetItem(['Filename','# Bugs']))
        self.btnNext = QtGui.QPushButton('>>')
        self.btnNext.setEnabled(False)
        self.btnPrevious = QtGui.QPushButton('<<')
        self.btnPrevious.setEnabled(False)

        bottomLayout.addStretch(1)
        bottomLayout.addWidget(self.btnPrevious)
        bottomLayout.addStretch(1)
        bottomLayout.addWidget(self.btnNext)
        bottomLayout.addStretch(1)
        panelLayout.addWidget(self.treeFileBrowser)
        panelLayout.addWidget(bottomPanel)

        self.treeFileBrowser.itemDoubleClicked.connect(self.doubleClicked)
        self.btnNext.clicked.connect(self.nextClicked)
        self.btnPrevious.clicked.connect(self.previousClicked)

    def refresh(self, currentPath, imageFilename):
        self.currentPath = currentPath
        self.imageFilename = imageFilename

        images = [(f, guess_type(f)) for f in listdir(currentPath) if os.path.isfile(f)]
        images = [f for (f,(t,e)) in images if t is not None and len(t) > 5 and t[0:5] == 'image']

        model = self.treeFileBrowser.model()
        for _ in range(model.rowCount()):
            model.removeRow(0)

        for f in images:
            csvfile = currentPath+"/"+changeExtension(f, 'csv')
            count = 'n/a'

            if os.path.isfile(csvfile):
                count = 0
                with open(csvfile) as data:
                    reader = csv.reader(data)
                    for i, l in enumerate(reader):
                        pass
                    count = i
            count = str(count)

            item = QtGui.QTreeWidgetItem([f, count])
            self.treeFileBrowser.addTopLevelItem(item)
            if f==imageFilename:
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
                item.setFont(1, font)
                self.treeFileBrowser.setItemSelected(item, True)
                self.currentItem = item

        self.treeFileBrowser.resizeColumnToContents(0)
        self.treeFileBrowser.resizeColumnToContents(1)

        if self.treeFileBrowser.itemBelow(self.currentItem) is None:
            self.btnNext.setEnabled(False)
        else:
            self.btnNext.setEnabled(True)
        if self.treeFileBrowser.itemAbove(self.currentItem) is None:
            self.btnPrevious.setEnabled(False)
        else:
            self.btnPrevious.setEnabled(True)

    def doubleClicked(self, i, c):
        if self.currentItem is not i:
            self.sigFileSelected.emit("%s/%s" % (self.currentPath,i.text(0)))

    def nextClicked(self):
        i = self.treeFileBrowser.itemBelow(self.currentItem)
        self.sigFileSelected.emit("%s/%s" % (self.currentPath,i.text(0)))

    def previousClicked(self):
        i = self.treeFileBrowser.itemAbove(self.currentItem)
        self.sigFileSelected.emit("%s/%s" % (self.currentPath,i.text(0)))


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

        b = 4*h/10
        for text in ['Drag and Drop tray scan image file here',
                     'or load it from the File menu']:
            ((tw,th), _) = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 1)
            cv2.putText(img, text, ((w-tw)/2, b), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0,255), 2)
            b += th + 10
        cv2.GaussianBlur(img, (3,3), 0.5, img)

        s = w/(2*20+1)
        for i in range(0,w+100,s)[0::2]:
            cv2.rectangle(img, (i,0), (i+s, 2), (0,0,0,128), -1)
            cv2.rectangle(img, (i,h-1), (i+s, h-3), (0,0,0,128), -1)
        s = h/(2*10+1)
        for i in range(0,h+100,s)[0::2]:
            cv2.rectangle(img, (0,i), (2,i+s), (0,0,0,128), -1)
            cv2.rectangle(img, (w-1,i), (w-3,i+s), (0,0,0,128), -1)
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

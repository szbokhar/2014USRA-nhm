from PySide import QtCore, QtGui

from AppData import *
from Util import *
from Pt import *


class ControlPanel(QtGui.QFrame):
    """A QtWidget that holds all the control buttons for the application."""

    # Signals emmited by the control panel
    sigLoadTrayImage = QtCore.Signal(str, str)

    def __init__(self, data, parent=None):
        super(ControlPanel, self).__init__(parent)
        self.data = data
        self.initUI()

    def initUI(self):
        # Setup the panel and layout
        panelLayout = QtGui.QHBoxLayout(self)
        self.setLayout(panelLayout)

        # Create the Load Tray buttion
        self.btnLoadTray = QtGui.QPushButton("Load Tray Scan")
        self.btnLoadTray.setMinimumHeight(50)
        self.btnLoadTray.setStatusTip("Load Tray Scan")

        # Create the Refresh Camera buttion
        self.btnRefreshCamera = QtGui.QPushButton("Refresh camera")
        self.btnRefreshCamera.setMinimumHeight(50)
        self.btnRefreshCamera.setStatusTip("Refresh Camera")
        self.btnRefreshCamera.setEnabled(False)

        # Create the Export to CSV buttion
        self.btnExport = QtGui.QPushButton("Export CSV")
        self.btnExport.setMinimumHeight(50)
        self.btnExport.setStatusTip("Export CSV")

        # Create the Quit buttion
        self.btnQuit = QtGui.QPushButton("Quit")
        self.btnQuit.setMinimumHeight(50)
        self.btnQuit.setStatusTip("Quit")

        # Create the Textbox label
        self.lblTextLabel = QtGui.QLabel()
        self.lblTextLabel.setText('ID:')

        # Create the Barcode label
        self.txtBarcode = QtGui.QLineEdit()
        self.txtBarcode.setText('')
        self.txtBarcode.setMinimumWidth(100)
        self.txtBarcode.setEnabled(False)

        # Place all buttons and labels on the panel
        panelLayout.addWidget(self.btnLoadTray)
        panelLayout.addWidget(self.btnRefreshCamera)
        panelLayout.addWidget(self.btnExport)
        panelLayout.addWidget(self.btnQuit)
        panelLayout.addStretch(1)
        panelLayout.addWidget(self.lblTextLabel)
        panelLayout.addWidget(self.txtBarcode)
        panelLayout.addStretch(1)

        # Connect slots for the buttion actions
        self.btnLoadTray.clicked.connect(self.selectTrayImage)
        self.btnExport.clicked.connect(self.data.exportToCSV)
        self.btnQuit.clicked.connect(self.quit)
        self.btnRefreshCamera.clicked.connect(self.data.refreshCameraButton)
        self.txtBarcode.textEdited.connect(self.data.newBugIdEntered)

        self.sigLoadTrayImage.connect(self.data.setTrayScan)

    def selectTrayImage(self):
        fname, _ = QtGui.QFileDialog.getOpenFileName(
            self, "Open Specimin File", ".")

        if fname != "":
            fpath = fname.split("/")
            self.currentPath = "/".join(fpath[0:-1])
            csvfile = fpath[-1].split('.')
            csvfile[1] = "csv"
            csvfile = '.'.join(csvfile)
            csvfile = self.currentPath+"/"+csvfile
            self.sigLoadTrayImage.emit(fname, csvfile)

    def setCurrentBugId(self, string):
        self.txtBarcode.setText(string)
        self.txtBarcode.selectAll()

    def quit(self):
        self.data.exportToCSV()
        QtCore.QCoreApplication.instance().quit()

class BigLabel(QtGui.QLabel):
    """The large sized label with convienence function for displaying images
    in numpy arrays, as well as signals for mouse events"""

    originalSize = (640, 480)
    resizeScale = (1.0, 1.0)

    sigMousePress = QtCore.Signal(QtGui.QMouseEvent, float)
    sigMouseMove = QtCore.Signal(QtGui.QMouseEvent, float)
    sigMouseRelease = QtCore.Signal(QtGui.QMouseEvent)

    def __init__(self, data, parent=None):
        super(BigLabel, self).__init__(parent)
        self.data = data
        self.initUI()
        self.setMouseTracking(True)
        self.imageScaleRatio = 1

    def initUI(self):
        self.setAlignment(QtCore.Qt.AlignTop)

    def setImage(self, cvImage):
        cvImage = cv2.cvtColor(cvImage, cv2.cv.CV_BGR2RGB)
        originalSize = (cvImage.shape[1], cvImage.shape[0])
        (w, h, rat) = computeImageScaleFactor(originalSize, self.getCurrentSize())
        self.imageScaleRatio = rat
        cvImage = cv2.resize(cvImage, (w, h))
        img = QtGui.QImage(cvImage, cvImage.shape[1], cvImage.shape[0],
                           cvImage.strides[0], QtGui.QImage.Format_RGB888)

        self.setPixmap(QtGui.QPixmap.fromImage(img))

    def mousePressEvent(self, ev):
        self.sigMousePress.emit(ev, self.imageScaleRatio)

    def mouseMoveEvent(self, ev):
        self.sigMouseMove.emit(ev, self.imageScaleRatio)

    def mouseReleaseEvent(self, ev):
        self.sigMouseRelease.emit(ev)

    def newResizeScale(self, scale):
        self.resizeScale = scale
        (sx, sy) = scale
        (w, h) = self.originalSize
        self.resize(int(w*sx), int(h*sy))

    def getCurrentSize(self):
        (sx, sy) = self.resizeScale
        (w, h) = self.originalSize
        return (w*sx, h*sy)


class SmallLabel(QtGui.QLabel):
    """The small sized label with convienence function for displaying images
    in numpy arrays"""

    originalSize = (300, 200)
    resizeScale = (1.0, 1.0)

    def __init__(self, data, parent=None):
        super(SmallLabel, self).__init__(parent)
        self.data = data
        self.initUI()
        self.imageScaleRatio = 1

    def initUI(self):
        self.setAlignment(QtCore.Qt.AlignTop)

    def setImage(self, cvImage):
        if cvImage.ndim == 2:
            cvImage = cv2.cvtColor(cvImage, cv2.cv.CV_GRAY2RGB)
        else:
            cvImage = cv2.cvtColor(cvImage, cv2.cv.CV_BGR2RGB)
        originalSize = (cvImage.shape[1], cvImage.shape[0])
        (w, h, rat) = computeImageScaleFactor(originalSize, self.getCurrentSize())
        self.imageScaleRatio = rat
        cvImage = cv2.resize(cvImage, (w, h))
        img = QtGui.QImage(cvImage, cvImage.shape[1], cvImage.shape[0],
                           cvImage.strides[0], QtGui.QImage.Format_RGB888)

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

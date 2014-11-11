from PySide import QtCore, QtGui

from AppData import *
from Util import *
from Pt import *

class ControlPanel(QtGui.QFrame):
    """A QtWidget that holds all the control buttons for the application."""

    # Signals emmited by the control panel
    sigLoadTrayImage = QtCore.Signal(str)

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

        # Create the Start Scanning buttion
        self.btnStartScanning = QtGui.QPushButton("Start Barcode Scanning")
        self.btnStartScanning.setMinimumHeight(50)
        self.btnStartScanning.setStatusTip("Start Barcode Scanning")
        self.btnStartScanning.setEnabled(False)

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

        # Place all buttons and labels on the panel
        panelLayout.addWidget(self.btnLoadTray)
        panelLayout.addWidget(self.btnStartScanning)
        panelLayout.addWidget(self.btnRefreshCamera)
        panelLayout.addWidget(self.btnExport)
        panelLayout.addWidget(self.btnQuit)
        panelLayout.addStretch(1)
        panelLayout.addWidget(self.lblTextLabel)
        panelLayout.addWidget(self.txtBarcode)
        panelLayout.addStretch(1)

        # Connect slots for the buttion actions
        self.btnLoadTray.clicked.connect(self.selectTrayImage)
        self.btnStartScanning.clicked.connect(self.data.toggleScanningMode)
        self.btnExport.clicked.connect(self.data.exportToCSV)
        self.btnQuit.clicked.connect(QtCore.QCoreApplication.instance().quit)
        self.btnRefreshCamera.clicked.connect(self.data.refreshCameraButton)
        self.txtBarcode.textEdited.connect(self.data.newBugIdEntered)

        self.sigLoadTrayImage.connect(self.data.setTrayScan)

    def selectTrayImage(self):
        fname, _ = QtGui.QFileDialog.getOpenFileName(self,
                "Open Specimin File", ".")

        if fname != "":
            fpath = fname.split("/")
            self.currentPath = "/".join(fpath[0:-1])
            self.sigLoadTrayImage.emit(fname)

    def scanningModeToggled(self, newphase):
        if newphase == AppData.EDIT_MODE:
            self.btnStartScanning.setText("Start Barcode Scanning")
            self.btnRefreshCamera.setEnabled(False)
        elif newphase == AppData.SCANNING_MODE:
            self.btnStartScanning.setText("Stop Barcode Scanning")
            self.btnRefreshCamera.setEnabled(True)


    def setCurrentBugId(self, string):
        self.txtBarcode.setText(string)
        self.txtBarcode.selectAll()

class BigLabel(QtGui.QLabel):
    """The large sized label with convienence function for displaying images
    in numpy arrays, as well as signals for mouse events"""

    labelSize = (640, 480)

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
        self.setFixedSize(QtCore.QSize(self.labelSize[0], self.labelSize[1]))
        self.setAlignment(QtCore.Qt.AlignTop)

    def setImage(self, cvImage):
        cvImage = cv2.cvtColor(cvImage, cv2.cv.CV_BGR2RGB)
        originalSize = (cvImage.shape[1], cvImage.shape[0])
        (w,h,rat) = computeImageScaleFactor(originalSize, self.labelSize)
        self.imageScaleRatio = rat
        cvImage = cv2.resize(cvImage, (w,h))
        img = QtGui.QImage(cvImage, cvImage.shape[1], cvImage.shape[0],
                cvImage.strides[0], QtGui.QImage.Format_RGB888)

        self.setPixmap(QtGui.QPixmap.fromImage(img))

    def mousePressEvent(self, ev):
        self.sigMousePress.emit(ev, self.imageScaleRatio)

    def mouseMoveEvent(self, ev):
        self.sigMouseMove.emit(ev, self.imageScaleRatio)

    def mouseReleaseEvent(self, ev):
        self.sigMouseRelease.emit(ev)


class SmallLabel(QtGui.QLabel):
    """The small sized label with convienence function for displaying images
    in numpy arrays"""

    labelSize = (300, 200)

    def __init__(self, data, parent=None):
        super(SmallLabel, self).__init__(parent)
        self.data = data
        self.initUI()
        self.imageScaleRatio = 1

    def initUI(self):
        self.setFixedSize(QtCore.QSize(self.labelSize[0], self.labelSize[1]))
        self.setAlignment(QtCore.Qt.AlignTop)

    def setImage(self, cvImage):
        if cvImage.ndim == 2:
            cvImage = cv2.cvtColor(cvImage, cv2.cv.CV_GRAY2RGB)
        else:
            cvImage = cv2.cvtColor(cvImage, cv2.cv.CV_BGR2RGB)
        originalSize = (cvImage.shape[1], cvImage.shape[0])
        (w,h,rat) = computeImageScaleFactor(originalSize, self.labelSize)
        self.imageScaleRatio = rat
        cvImage = cv2.resize(cvImage, (w,h))
        img = QtGui.QImage(cvImage, cvImage.shape[1], cvImage.shape[0],
                cvImage.strides[0], QtGui.QImage.Format_RGB888)

        self.setPixmap(QtGui.QPixmap.fromImage(img))

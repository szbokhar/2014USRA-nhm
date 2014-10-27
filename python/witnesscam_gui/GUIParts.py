from PySide import QtCore, QtGui

from AppData import *
from Util import *
from Pt import *

class ControlPanel(QtGui.QFrame):

    # Signals emmited by the control panel
    sigLoadTrayImage = QtCore.Signal(str)

    def __init__(self, data, parent=None):
        super(ControlPanel, self).__init__(parent)
        self.data = data
        self.initUI()

    def initUI(self):
        panelLayout = QtGui.QHBoxLayout(self)
        self.setLayout(panelLayout)

        self.btnLoadTray = QtGui.QPushButton("Load Tray Scan")
        self.btnLoadTray.setMinimumHeight(50)
        self.btnLoadTray.setStatusTip("Load Tray Scan")

        self.btnRefreshCamera = QtGui.QPushButton("Refresh camera")
        self.btnRefreshCamera.setMinimumHeight(50)
        self.btnRefreshCamera.setStatusTip("Refresh Camera")
        self.btnRefreshCamera.setEnabled(False)

        self.btnQuit = QtGui.QPushButton("Quit")
        self.btnQuit.setMinimumHeight(50)
        self.btnQuit.setStatusTip("Quit")

        self.lblBarcode = QtGui.QLabel()
        self.lblBarcode.setText('Hoaaaaa')

        panelLayout.addWidget(self.btnLoadTray)
        panelLayout.addWidget(self.btnRefreshCamera)
        panelLayout.addWidget(self.btnQuit)
        panelLayout.addWidget(self.lblBarcode)
        panelLayout.addStretch(1)

        self.btnLoadTray.clicked.connect(self.selectTrayImage)
        self.btnQuit.clicked.connect(QtCore.QCoreApplication.instance().quit)
        self.btnRefreshCamera.clicked.connect(self.data.refreshCameraButton)

    def selectTrayImage(self):
        fname, _ = QtGui.QFileDialog.getOpenFileName(self,
                "Open Specimin File", ".")

        if fname != "":
            fpath = fname.split("/")
            self.currentPath = "/".join(fpath[0:-1])
            self.sigLoadTrayImage.emit(fname)

    def setLabelText(self, string):
        self.lblBarcode.setText(string)

class BigLabel(QtGui.QLabel):

    labelSize = (640, 480)

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
        (w,h,rat) = keepAspectRatio(originalSize, self.labelSize)
        self.imageScaleRatio = rat
        cvImage = cv2.resize(cvImage, (w,h))
        img = QtGui.QImage(cvImage, cvImage.shape[1], cvImage.shape[0],
                cvImage.strides[0], QtGui.QImage.Format_RGB888)

        self.setPixmap(QtGui.QPixmap.fromImage(img))

    def mousePressEvent(self, ev):
        if self.data.phase == AppData.SELECT_POLYGON:
            self.data.polyboxProgress += 1
            self.data.polyPoints.append(
                    Pt(int(ev.pos().x()/self.imageScaleRatio),
                    int(ev.pos().y()/self.imageScaleRatio)))

        if self.data.polyboxProgress == 4:
            self.data.gotBox()

    def mouseMoveEvent(self, ev):
        self.data.setMousepos(int(ev.pos().x()/self.imageScaleRatio),
                int(ev.pos().y()/self.imageScaleRatio))


class SmallLabel(QtGui.QLabel):

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
        if self.data.phase == AppData.ACTIVE_MODE:
            cvImage = cv2.cvtColor(cvImage, cv2.cv.CV_GRAY2RGB)
        else:
            cvImage = cv2.cvtColor(cvImage, cv2.cv.CV_BGR2RGB)
        originalSize = (cvImage.shape[1], cvImage.shape[0])
        (w,h,rat) = keepAspectRatio(originalSize, self.labelSize)
        self.imageScaleRatio = rat
        cvImage = cv2.resize(cvImage, (w,h))
        img = QtGui.QImage(cvImage, cvImage.shape[1], cvImage.shape[0],
                cvImage.strides[0], QtGui.QImage.Format_RGB888)

        self.setPixmap(QtGui.QPixmap.fromImage(img))


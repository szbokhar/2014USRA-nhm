from PySide import QtCore, QtGui
from Pt import *
import cv2
import sys
import numpy as np

class MainWindow(QtGui.QMainWindow):

    def __init__(self, fname=None):
        super(MainWindow, self).__init__()
        self.initUI(fname)

    def initUI(self, fname=None):
        # Setup main content area
        mainWidget = QtGui.QFrame(self)
        mainContent = QtGui.QVBoxLayout(self)

        # Setup Gui Elements
        self.data = AppData()
        self.controlPanel = ControlPanel(self.data)
        self.lblBig = BigLabel(self.data)
        self.lblsmall = SmallLabel(self.data)
        self.data.setGuiElements(self.controlPanel, self.lblBig, self.lblsmall)

        self.topPanel = QtGui.QFrame()
        self.topContent = QtGui.QHBoxLayout(self)

        # Add GUI elements to window
        mainWidget.setLayout(mainContent)
        self.topPanel.setLayout(self.topContent)
        self.setCentralWidget(mainWidget)

        mainContent.addWidget(self.topPanel)
        mainContent.addWidget(self.controlPanel)
        self.topContent.addWidget(self.lblBig)
        self.topContent.addWidget(self.lblsmall)

        # Finish up window
        self.statusBar().showMessage("Ready")
        self.setGeometry(0, 0, 1024, 720)
        self.setFixedSize(self.size())
        self.setWindowTitle('Insect Segmentation')
        self.show()


class AppData:

    LOAD_FILE, SELECT_POLYGON, ACTIVE_MODE = range(3)

    def __init__(self):
        self.camOn = False
        self.cameraLabel = None
        self.staticLabel = None

        self.bigMPos = (0,0)

        self.phase = AppData.LOAD_FILE
        self.polyboxProgress = 0
        self.polyPoints = []

    def setGuiElements(self, control, big, small):
        self.controlPanel = control
        self.lblBig = big
        self.lblSmall = small

        self.controlPanel.sigLoadTrayImage.connect(self.setTrayScan)

        self.cameraLabel = self.lblBig
        self.staticLabel = self.lblSmall

    def setTrayScan(self, fname):
        self.trayPath = fname
        self.trayImage = cv2.imread(self.trayPath, cv2.IMREAD_COLOR)
        self.trayImage = cv2.pyrDown(self.trayImage)
        self.staticLabel.setImage(self.trayImage)
        self.startCameraFeed()
        self.phase = AppData.SELECT_POLYGON

    def startCameraFeed(self):
        if not self.camOn:
            self.capture = cv2.VideoCapture(0)

            self.frameTimer = QtCore.QTimer()
            self.frameTimer.timeout.connect(self.getNewCameraFrame)
            self.frameTimer.start(30)
            self.camOn = True

    def getNewCameraFrame(self):
        _, cameraImage = self.capture.read()
        self.cameraImage = cv2.pyrDown(cameraImage)
        self.cameraImage = cv2.pyrDown(self.cameraImage)
        self.cameraImage = cv2.pyrDown(self.cameraImage)
        staticImage = np.copy(self.trayImage)
        (cameraFrame, staticFrame) = self.amendFrame(self.cameraImage, staticImage)

        self.cameraLabel.setImage(cameraFrame)
        self.staticLabel.setImage(staticFrame)

    def setMousepos(self, x, y):
        self.bigMPos = (x,y)

    def amendFrame(self, cameraFrame, staticFrame):
        (mx, my) = self.bigMPos
        cv2.line(cameraFrame, (mx-10, my), (mx+10, my), (255,0,0), 1)
        cv2.line(cameraFrame, (mx, my-10), (mx, my+10), (255,0,0), 1)

        if self.phase == AppData.SELECT_POLYGON:
            for p in self.polyPoints:
                cv2.circle(cameraFrame, (p.x, p.y), 5, (0,255,0))
        elif self.phase == AppData.ACTIVE_MODE:
            for i in range(4):
                p1 = self.polyPoints[i]
                p2 = self.polyPoints[(i+1)%4]
                cv2.line(cameraFrame, (p1.x, p1.y), (p2.x, p2.y), (255,0,0), 1)

            camPoint = self.getCameraPoint()
            (trayHeight, trayWidth, _) = self.trayImage.shape
            (u,v) = compute_mapvals(self.polyPoints, trayWidth, trayHeight, camPoint)

            cv2.line(staticFrame, (u-20, v), (u+20, v), (0,0,255), 5)
            cv2.line(staticFrame, (u, v-20), (u, v+20), (0,0,255), 5)

            cameraFrame = np.uint8(np.add.reduce(np.absolute(np.subtract(np.float32(cameraFrame), np.float32(self.camBackground))), 2))

        return (cameraFrame, staticFrame)

    def gotBox(self):
        self.camBackground = np.copy(self.cameraImage)

        self.phase = AppData.ACTIVE_MODE

        tmp = self.cameraLabel
        self.cameraLabel = self.staticLabel
        self.staticLabel = tmp

    def getCameraPoint(self):
        return Pt(10, 10)

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

        self.btnQuit = QtGui.QPushButton("Quit")
        self.btnQuit.setMinimumHeight(50)
        self.btnQuit.setStatusTip("Quit")

        panelLayout.addWidget(self.btnLoadTray)
        panelLayout.addWidget(self.btnQuit)
        panelLayout.addStretch(1)

        self.btnLoadTray.clicked.connect(self.selectTrayImage)
        self.btnQuit.clicked.connect(QtCore.QCoreApplication.instance().quit)

    def selectTrayImage(self):
        fname, _ = QtGui.QFileDialog.getOpenFileName(self,
                "Open Specimin File", ".")

        if fname != "":
            fpath = fname.split("/")
            self.currentPath = "/".join(fpath[0:-1])
            self.sigLoadTrayImage.emit(fname)

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


def keepAspectRatio(original, box):
    (bW, bH) = box
    (w, h) = original
    rat = min(float(bW)/w, float(bH)/h)
    return (int(w*rat), int(h*rat), rat)

def compute_mapvals(points, scalex, scaley, pos):
    [p0, p1, p2, p3] = points
    [p00, p01, p02, p03] = [p0-p0, p1-p0, p2-p0, p3-p0]
    (x,y) = (pos.x-p0.x, pos.y-p0.y)

    C = 0
    F = 0
    den2 = float(((p2-p1).x*(p2-p3).y-(p2-p1).y*(p2-p3).x))
    numG = float(((p2-p0).x*(p2-p3).y-(p2-p0).y*(p2-p3).x))
    numH = float(((p2-p1).x*(p2-p0).y-(p2-p1).y*(p2-p0).x))
    GG = numG/den2
    HH = numH/den2
    A = GG*(p1-p0).x
    D = GG*(p1-p0).y
    B = HH*(p3-p0).x
    E = HH*(p3-p0).y
    G = GG-1
    H = HH-1
    v = (-A*F+A*y+C*D-C*G*y-D*x+F*G*x)/(A*E-A*H*y-B*D+B*G*y+D*H*x-E*G*x)
    u = (-C-B*v+x+H*v*x)/(A-G*x)

    return (int(u*scalex), int(v*scaley))


def main():
    logfile = None
    if len(sys.argv) > 1:
        logfile = sys.argv[1]

    app = QtGui.QApplication(sys.argv)
    ex = MainWindow(logfile)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()


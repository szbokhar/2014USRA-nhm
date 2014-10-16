from PySide import QtCore, QtGui
from Pt import *
import cv2
import sys
import numpy as np
import os.path
import csv

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
        self.selection_boundingbox = None
        self.activeFrameLastDiff = None
        self.activeFrameSmoothDelta = None
        self.stableRun = 0
        self.stableAverage = 0
        self.lastStableAverage = 0

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
        oH = self.trayImage.shape[0]
        self.trayImage = cv2.pyrDown(self.trayImage)
        self.trayImageScale = float(self.trayImage.shape[0])/oH
        self.staticLabel.setImage(self.trayImage)

        csvFname = list(os.path.splitext(fname))
        csvFname[-1] = '.csv'
        csvFname = ''.join(csvFname)
        self.CSVPath = csvFname
        self.loadCSVFile(self.CSVPath)

        self.startCameraFeed()
        self.phase = AppData.SELECT_POLYGON

    def loadCSVFile(self, fname):
        self.bugBoxes = []
        with open(fname, 'rb') as csvfile:
            boxes = csv.reader(csvfile, delimiter=',')
            for b in boxes:
                if len(b) >= 5:
                    self.bugBoxes.append([int(i) for i in b[1],b[2],b[3],b[4]])


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
        #self.cameraImage = cv2.pyrDown(self.cameraImage)
        staticImage = np.copy(self.trayImage)
        (cameraFrame, staticFrame) = self.amendFrame(self.cameraImage, staticImage)

        self.cameraLabel.setImage(cameraFrame)
        self.staticLabel.setImage(staticFrame)

    def setMousepos(self, x, y):
        self.bigMPos = (x,y)

    def amendFrame(self, cameraFrame, staticFrame):
        cameraFrame = np.copy(cameraFrame)
        staticFrame = np.copy(staticFrame)

        (mx, my) = self.bigMPos

        if self.phase == AppData.SELECT_POLYGON:
            cv2.line(cameraFrame, (mx-10, my), (mx+10, my), (255,0,0), 1)
            cv2.line(cameraFrame, (mx, my-10), (mx, my+10), (255,0,0), 1)
            for p in self.polyPoints:
                cv2.circle(cameraFrame, (p.x, p.y), 5, (0,255,0))
        elif self.phase == AppData.ACTIVE_MODE:
            """
            for i in range(4):
                p1 = self.polyPoints[i]
                p2 = self.polyPoints[(i+1)%4]
                cv2.line(cameraFrame, (p1.x, p1.y), (p2.x, p2.y), (255,0,0), 1)

            camPoint = self.getCameraPoint()
            (trayHeight, trayWidth, _) = self.trayImage.shape
            (u,v) = compute_mapvals(self.polyPoints, trayWidth, trayHeight, camPoint)

            cv2.line(staticFrame, (u-20, v), (u+20, v), (0,0,255), 5)
            cv2.line(staticFrame, (u, v-20), (u, v+20), (0,0,255), 5)
            """

            (cf, cPt) = self.getCameraPoint(cameraFrame)
            if cPt != None:
                cv2.line(cf, (cPt.x-10, cPt.y), (cPt.x+10, cPt.y), (255,255,255), 1)
                cv2.line(cf, (cPt.x, cPt.y-10), (cPt.x, cPt.y+10), (255,255,255), 1)
                cv2.line(cf, (cPt.x-10, cPt.y-10), (cPt.x+10, cPt.y+10), (0,0,0), 1)
                cv2.line(cf, (cPt.x+10, cPt.y-10), (cPt.x-10, cPt.y+10), (0,0,0), 1)
                (trayHeight, trayWidth, _) = self.trayImage.shape
                (u,v) = compute_mapvals(self.polyPoints, trayWidth, trayHeight, cPt)
                cv2.line(staticFrame, (u-10, v), (u+10, v), (0,0,255), 5)
                cv2.line(staticFrame, (u, v-10), (u, v+10), (0,0,255), 5)

                r = self.trayImageScale
                for b in self.bugBoxes:
                    if (u > b[0]*r and u < b[2]*r and v > b[1]*r and v < b[3]*r):
                        q0 = (int(b[0]*r), int(b[1]*r))
                        q1 = (int(b[2]*r), int(b[1]*r))
                        q2 = (int(b[2]*r), int(b[3]*r))
                        q3 = (int(b[0]*r), int(b[3]*r))
                        cv2.line(staticFrame, q0, q1, (0,0,255), 2)
                        cv2.line(staticFrame, q1, q2, (0,0,255), 2)
                        cv2.line(staticFrame, q2, q3, (0,0,255), 2)
                        cv2.line(staticFrame, q3, q0, (0,0,255), 2)
                        break
            return (cf, staticFrame)

        return (cameraFrame, staticFrame)

    def gotBox(self):
        self.camBackground = np.copy(self.cameraImage)

        self.phase = AppData.ACTIVE_MODE

        tmp = self.cameraLabel
        self.cameraLabel = self.staticLabel
        self.staticLabel = tmp

        (minx, miny, maxx, maxy) = (1000, 1000, 0, 0)
        for p in self.polyPoints:
            minx = p.x if p.x < minx else minx
            miny = p.y if p.y < miny else miny
            maxx = p.x if p.x > maxx else maxx
            maxy = p.y if p.y > maxy else maxy
        self.selection_boundingbox = [Pt(minx,miny), Pt(maxx, maxy)]

        self.controlPanel.btnRefreshCamera.setEnabled(True)

    def getCameraPoint(self, cameraFrame):
        frame = np.absolute(np.subtract(self.camBackground.astype(int),
                cameraFrame.astype(int))).astype(np.uint8)
        (h,w,d) = frame.shape
        polygon_mask = np.zeros((h,w,d), np.uint8)
        poly = np.array([[p.x, p.y] for p in self.polyPoints],
                dtype=np.int32)
        cv2.drawContours(polygon_mask, [poly], 0, (1,1,1), -1)
        frame = np.add.reduce(np.square(np.multiply(
                np.float32(frame), polygon_mask)), 2)
        frame = np.sqrt(frame)
        frame = cv2.GaussianBlur(frame, (5,5), 0)
        frame[frame < 12] = 0
        tframe = np.copy(frame)

        medpos = None
        if self.activeFrameLastDiff != None:
            a = 1.0
            activeFrameCurrentDiff = np.sum(tframe)
            delta = activeFrameCurrentDiff - self.activeFrameLastDiff
            self.activeFrameSmoothDelta = (1-a)*self.activeFrameSmoothDelta + a*delta
            self.activeFrameLastDiff = activeFrameCurrentDiff
            if abs(self.activeFrameSmoothDelta) < 25000:
                self.stableRun += 1
            else:
                if self.stableRun > 15:
                    self.lastStableAverage = self.stableAverage
                    self.stableAverage = 0
                self.stableRun = 0

            if self.stableRun == 15:
                self.stableAverage = activeFrameCurrentDiff
            elif self.stableRun > 15:
                b = 0.5
                self.stableAverage = (1-b)*self.stableAverage + b*activeFrameCurrentDiff

                medpos = get_median_position(tframe, self.selection_boundingbox)
                if self.lastStableAverage > self.stableAverage:
                    medpos = None
                    if self.lastStableAverage * 1.1 > self.stableAverage:
                        self.refreshCamera()

        else:
            self.activeFrameLastDiff = np.sum(tframe)
            self.activeFrameSmoothDelta = 0

        frame = np.uint8(frame)
        return (frame, medpos)

    def refreshCamera(self):
        self.camBackground = np.copy(self.cameraImage)
        self.stableRun = 0
        self.stableAverage = 0
        self.lastStableAverage = 0

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

        panelLayout.addWidget(self.btnLoadTray)
        panelLayout.addWidget(self.btnRefreshCamera)
        panelLayout.addWidget(self.btnQuit)
        panelLayout.addStretch(1)

        self.btnLoadTray.clicked.connect(self.selectTrayImage)
        self.btnQuit.clicked.connect(QtCore.QCoreApplication.instance().quit)
        self.btnRefreshCamera.clicked.connect(self.data.refreshCamera)

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

def get_median_position(difference_mask, selection_boundingbox):
    c = 0.0
    p = Pt(0,0)
    xlist = []
    ylist = []
    for x in range(selection_boundingbox[0].x, selection_boundingbox[1].x, 5):
        for y in range(selection_boundingbox[0].y, selection_boundingbox[1].y,
                5):
            if difference_mask[y,x] > 0:
                c += difference_mask[y,x]
                xlist.append((x, difference_mask[y,x]))
                ylist.append((y, difference_mask[y,x]))
                p += Pt(x*difference_mask[y,x],y*difference_mask[y,x])

    if xlist:
        return Pt(median_pos(xlist), median_pos(ylist))

    return None

def median_pos(lst):
    lst.sort()
    for i in range(1,len(lst)):
        (cord, weight) = lst[i]
        (_, pweight) = lst[i-1]
        lst[i] = (cord, weight+pweight)

    if lst:
        xmed = lst[-1][1]/2
        low = 0
        high = len(lst)-1
        while (high-low > 1):
            check = int(math.floor((high+low)/2))
            (v, w) = lst[check]
            if w > xmed:
                high = check
            elif w < xmed:
                low = check
            else:
                low = check
                high = check
                break
        return lst[high][0]

def main():
    logfile = None
    if len(sys.argv) > 1:
        logfile = sys.argv[1]

    app = QtGui.QApplication(sys.argv)
    ex = MainWindow(logfile)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()


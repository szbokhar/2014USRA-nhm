from PySide import QtCore, QtGui
import cv2
import numpy as np
import os.path
import sys

from Util import *
from Pt import *

class AppData:

    LOAD_FILE, SELECT_POLYGON, ACTIVE_MODE = range(3)
    ACTION_DELAY = 15

    def __init__(self):
        self.camOn = False
        self.cameraLabel = None
        self.staticLabel = None

        self.bigMPos = (0,0)

        self.phase = AppData.LOAD_FILE
        self.polyboxProgress = 0
        self.polyPoints = []
        self.polygonModel = None
        self.selection_boundingbox = None
        self.activeFrameCurrentDiff = None
        self.activeFrameLastDiff = None
        self.activeFrameSmoothDelta = None
        self.stableRun = 0
        self.stableAverage = 0
        self.lastStableAverage = 0
        self.removedBug = -1
        self.frameCount = 0
        self.currentSelectionBox = None
        self.placedBoxes = []
        self.stableBoxRun = 0
        self.stableBox = None

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

            (cf, cPt) = self.getCameraPoint(cameraFrame)
            if cPt != None:
                if self.removedBug != -1 and self.activeFrameCurrentDiff > 30 and self.stableRun >= 2*AppData.ACTION_DELAY:
                    self.removedBug = -1
                    self.currentSelectionBox = None
                    self.refreshCamera()
                """
                cv2.line(cf, (cPt.x-10, cPt.y), (cPt.x+10, cPt.y), (255,255,255), 1)
                cv2.line(cf, (cPt.x, cPt.y-10), (cPt.x, cPt.y+10), (255,255,255), 1)
                cv2.line(cf, (cPt.x-10, cPt.y-10), (cPt.x+10, cPt.y+10), (0,0,0), 1)
                cv2.line(cf, (cPt.x+10, cPt.y-10), (cPt.x-10, cPt.y+10), (0,0,0), 1)
                """

            for ((b, _), _) in self.placedBoxes:
                cv2.rectangle(staticFrame, b[0:2], b[2:4], (0, 255, 0), 2)

            if self.currentSelectionBox == None and self.stableRun >= AppData.ACTION_DELAY:
                (cf, staticFrame) = self.findCorrectBox(cPt, cf, staticFrame)
            elif self.currentSelectionBox != None:
                cv2.rectangle(staticFrame, self.currentSelectionBox[0][0:2], self.currentSelectionBox[0][2:4], (0, 0, 255), 2)

            """
            if self.removedBug != -1:
                (h, w, _) = cameraFrame.shape
                midx = w/2
                midy = h/2
                cv2.line(cameraFrame, (midx-50, midy-50), (midx+50, midy-50), (255, 0, 0), 2)
                cv2.line(cameraFrame, (midx+50, midy-50), (midx+50, midy+50), (255, 0, 0), 2)
                cv2.line(cameraFrame, (midx+50, midy+50), (midx-50, midy+50), (255, 0, 0), 2)
                cv2.line(cameraFrame, (midx-50, midy+50), (midx-50, midy-50), (255, 0, 0), 2)

                if self.frameCount % 15 == 0:
                    barcode = cameraFrame[midy-50:midy+50,midx-50:midx+50,:]
                    img = Image.fromarray(np.uint8(barcode))
                    dm_read = DataMatrix()
                    dm_read.decode(img.size[0], img.size[1], buffer(img.tostring()))
                    if dm_read.count() > 0:
                        self.boxLabels[self.removedBug] = dm_read.message(1)
                        self.controlPanel.setLabelText(dm_read.message(1))
                        """
            cf[cf > 0] = 255

            return (cf, staticFrame)

        return (cameraFrame, staticFrame)

    def findCorrectBox(self, live_pt, live_frame, static_frame):
        if live_pt != None:
            (trayHeight, trayWidth, _) = self.trayImage.shape
            (u,v) = poly2square(self.polygon_model, trayWidth, trayHeight, live_pt)
            cv2.line(static_frame, (u-10, v), (u+10, v), (0,0,255), 5)
            cv2.line(static_frame, (u, v-10), (u, v+10), (0,0,255), 5)
            r = self.trayImageScale

            (life_frame, static_box, live_box) = self.floodFillBox(live_pt, live_frame)
            if static_box != None:

                if self.stableBox == None:
                    self.stableBox = (static_box, live_box)
                else:
                    ((x1,y1,x2,y2), _) = self.stableBox
                    (x3,y3,x4,y4) = static_box
                    w = x2-x1
                    h = y2-y1
                    eps = 0.05
                    if (abs(x3-x1) < w*eps and abs(y3-y1) < h*eps and abs(x4-x2) < w*eps and abs(y4-y2) < h*eps):
                        a = 1.0
                        self.stableBoxRun += 1
                        self.stableBox = ((int(a*x3+(1-a)*x1), int(a*y3+(1-a)*y1), int(a*x4+(1-a)*x2), int(a*y4+(1-a)*y2)), live_box)
                    else:
                        self.stableBoxRun = 0
                        self.stableBox = (static_box, live_box)

                if self.stableBoxRun >= AppData.ACTION_DELAY:

                    (i, overlapped) = getOverlappingBox(self.placedBoxes, self.stableBox)
                    if overlapped == None:
                        self.currentSelectionBox = self.stableBox
                        self.placedBoxes.append((self.stableBox, "Box " + str(len(self.placedBoxes))))
                        self.removedBug = len(self.placedBoxes)-1
                        self.refreshCamera()
                    else:
                        self.currentSelectionBox = overlapped
                        self.removedBug = i
                        self.refreshCamera()



            """
            box = -1
            for b in self.bugBoxes:
                box += 1
                if (u > b[0]*r and u < b[2]*r and v > b[1]*r and v < b[3]*r):
                    self.drawLiveAndStaticBoxes(live_frame, static_frame, b)
                    break

            if self.stableRun == 2*AppData.ACTION_DELAY and self.removedBug == -1:
                self.removedBug = box
                self.frameCounter = 1
                self.refreshCamera()
                self.controlPanel.setLabelText(self.boxLabels[box])
            elif self.stableRun >= AppData.ACTION_DELAY and self.removedBug != -1 and self.activeFrameLastDiff > 50:
                self.frameCounter = 0
                self.removedBug = -1
                self.refreshCamera()
                self.controlPanel.setLabelText('')

        if self.removedBug >= 0:
            self.drawLiveAndStaticBoxes(live_frame, static_frame, self.bugBoxes[self.removedBug])
            """
        return (live_frame, static_frame)

    def floodFillBox(self, p, frameOrig):
        frame = np.copy(frameOrig)
        frame[frame > 12] = 1

        conts, hir = cv2.findContours(frame, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        staticContour = []
        for i in range(len(conts)):
            if cv2.pointPolygonTest(conts[i], p.t(), True) >= 0:
                cv2.drawContours(frame, conts, i, (255, 255, 255))
                (trayHeight, trayWidth, _) = self.trayImage.shape
                (sx1, sy1, sx2, sy2) = (trayWidth,trayHeight,0,0)
                (lx1, ly1, lx2, ly2) = (trayWidth,trayHeight,0,0)
                for q in conts[i]:
                    (lx,ly) = q[0]
                    (sx,sy) = poly2square(self.polygon_model, trayWidth, trayHeight, Pt(q[0,0],q[0,1]))
                    sx1 = min(sx1,sx)
                    sy1 = min(sy1,sy)
                    sx2 = max(sx2,sx)
                    sy2 = max(sy2,sy)
                    lx1 = min(lx1,lx)
                    ly1 = min(ly1,ly)
                    lx2 = max(lx2,lx)
                    ly2 = max(ly2,ly)
                    staticContour.append((sx,sy))
                return (frameOrig, (sx1, sy1, sx2, sy2), (lx1, ly1, lx2, ly2))

        return (frameOrig, None, None)

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
        self.polygon_model = compute_polygon_model(self.polyPoints)

        self.controlPanel.btnRefreshCamera.setEnabled(True)

    def getCameraPoint(self, cameraFrame):
        frame = np.absolute(np.subtract(self.camBackground.astype(int),
                cameraFrame.astype(int))).astype(np.uint8)
        (h,w,d) = frame.shape
        polygon_mask = np.zeros((h,w,d), np.uint8)

        poly = None
        polyArea = -1
        if self.removedBug == -1:
            poly = np.array([[p.x, p.y] for p in self.polyPoints],
                    dtype=np.int32)
            polyArea = area_of_quadrilateral([(p.x,p.y) for p in self.polyPoints])
        else:
            b = self.currentSelectionBox[1]
            q0 = (int(b[0]), int(b[1]))
            q1 = (int(b[2]), int(b[1]))
            q2 = (int(b[2]), int(b[3]))
            q3 = (int(b[0]), int(b[3]))
            poly = np.array([q0, q1, q2, q3], dtype=np.int32)
            polyArea = area_of_quadrilateral([q0, q1, q2, q3])

        cv2.drawContours(polygon_mask, [poly], 0, (1,1,1), -1)
        frame = np.add.reduce(np.square(np.multiply(
                np.float32(frame), polygon_mask)), 2)
        frame = np.sqrt(frame)
        frame = cv2.GaussianBlur(frame, (5,5), 0)
        frame = frame*0.70
        frame[frame < 12] = 0
        tframe = np.copy(frame)

        medpos = None
        if self.activeFrameLastDiff != None:
            a = 1.0
            self.activeFrameCurrentDiff = np.sum(tframe)/polyArea
            delta = self.activeFrameCurrentDiff - self.activeFrameLastDiff
            self.activeFrameSmoothDelta = (1-a)*self.activeFrameSmoothDelta + a*delta
            self.activeFrameLastDiff = self.activeFrameCurrentDiff

            if abs(self.activeFrameSmoothDelta) < 0.3:
                self.stableRun += 1
            else:
                self.stableRun = 0

            if self.stableRun > AppData.ACTION_DELAY:
                medpos = get_median_position(tframe, self.selection_boundingbox)

            if self.removedBug != -1:
                self.frameCount += 1

        else:
            self.activeFrameLastDiff = np.sum(tframe)/polyArea
            self.activeFrameSmoothDelta = 0

        frame = np.uint8(frame)
        return (frame, medpos)

    def refreshCamera(self):
        self.camBackground = np.copy(self.cameraImage)
        self.stableRun = 0

    def refreshCameraButton(self):
        self.refreshCamera()
        self.removedBug = -1
        self.currentSelectionBox = None

    def exportToCSV(self):
        fname, _ = QtGui.QFileDialog.getSaveFileName()
        print(fname)

        f = open(fname, 'w')
        for ((b, _), code) in self.placedBoxes:
            f.write(code + ", " + str(b) + '\n')



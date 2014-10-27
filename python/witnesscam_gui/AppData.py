from PySide import QtCore, QtGui
import csv
import cv2
import numpy as np
import os.path
import sys

from Util import *
from Pt import *

class AppData:

    LOAD_FILE, SELECT_POLYGON, ACTIVE_MODE = range(3)
    ACTION_DELAY = 25

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
        self.activeFrameLastDiff = None
        self.activeFrameSmoothDelta = None
        self.stableRun = 0
        self.stableAverage = 0
        self.lastStableAverage = 0
        self.removedBug = -1
        self.frameCount = 0
        self.boxLabels = []

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
            j = 1
            for b in boxes:
                if len(b) >= 5:
                    self.bugBoxes.append([int(i) for i in b[1],b[2],b[3],b[4]])
                    self.boxLabels.append('Bug #' + str(j))
                    j += 1


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
                cv2.line(cf, (cPt.x-10, cPt.y), (cPt.x+10, cPt.y), (255,255,255), 1)
                cv2.line(cf, (cPt.x, cPt.y-10), (cPt.x, cPt.y+10), (255,255,255), 1)
                cv2.line(cf, (cPt.x-10, cPt.y-10), (cPt.x+10, cPt.y+10), (0,0,0), 1)
                cv2.line(cf, (cPt.x+10, cPt.y-10), (cPt.x-10, cPt.y+10), (0,0,0), 1)

            self.findCorrectBox(cPt, cf, staticFrame)

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

            return (cf, staticFrame)

        return (cameraFrame, staticFrame)

    def findCorrectBox(self, live_pt, live_frame, static_frame):
        if live_pt != None:
            (trayHeight, trayWidth, _) = self.trayImage.shape
            (u,v) = poly2square(self.polygon_model, trayWidth, trayHeight, live_pt)
            cv2.line(static_frame, (u-10, v), (u+10, v), (0,0,255), 5)
            cv2.line(static_frame, (u, v-10), (u, v+10), (0,0,255), 5)
            r = self.trayImageScale
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

    def drawLiveAndStaticBoxes(self, live_frame, static_frame, box_coords):
        b = box_coords
        (trayHeight, trayWidth, _) = self.trayImage.shape
        r = self.trayImageScale
        q0 = Pt(int(b[0]*r), int(b[1]*r))
        q1 = Pt(int(b[2]*r), int(b[1]*r))
        q2 = Pt(int(b[2]*r), int(b[3]*r))
        q3 = Pt(int(b[0]*r), int(b[3]*r))
        cv2.line(static_frame, q0.t(), q1.t(), (0,0,255), 2)
        cv2.line(static_frame, q1.t(), q2.t(), (0,0,255), 2)
        cv2.line(static_frame, q2.t(), q3.t(), (0,0,255), 2)
        cv2.line(static_frame, q3.t(), q0.t(), (0,0,255), 2)
        p0 = square2poly(self.polygon_model, trayWidth, trayHeight, q0)
        p1 = square2poly(self.polygon_model, trayWidth, trayHeight, q1)
        p2 = square2poly(self.polygon_model, trayWidth, trayHeight, q2)
        p3 = square2poly(self.polygon_model, trayWidth, trayHeight, q3)
        cv2.line(live_frame, p0, p1, (255,255,255), 2)
        cv2.line(live_frame, p1, p2, (255,255,255), 2)
        cv2.line(live_frame, p2, p3, (255,255,255), 2)
        cv2.line(live_frame, p3, p0, (255,255,255), 2)

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
            b = self.bugBoxes[self.removedBug]
            (trayHeight, trayWidth, _) = self.trayImage.shape
            r = self.trayImageScale
            q0 = Pt(int(b[0]*r), int(b[1]*r))
            q1 = Pt(int(b[2]*r), int(b[1]*r))
            q2 = Pt(int(b[2]*r), int(b[3]*r))
            q3 = Pt(int(b[0]*r), int(b[3]*r))
            p0 = square2poly(self.polygon_model, trayWidth, trayHeight, q0)
            p1 = square2poly(self.polygon_model, trayWidth, trayHeight, q1)
            p2 = square2poly(self.polygon_model, trayWidth, trayHeight, q2)
            p3 = square2poly(self.polygon_model, trayWidth, trayHeight, q3)
            poly = np.array([p0, p1, p2, p3], dtype=np.int32)
            polyArea = area_of_quadrilateral([p0, p1, p2, p3])

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
            activeFrameCurrentDiff = np.sum(tframe)/polyArea
            delta = activeFrameCurrentDiff - self.activeFrameLastDiff
            self.activeFrameSmoothDelta = (1-a)*self.activeFrameSmoothDelta + a*delta
            self.activeFrameLastDiff = activeFrameCurrentDiff

            if abs(self.activeFrameSmoothDelta) < 1:
                self.stableRun += 1
            else:
                self.stableRun = 0

            if self.stableRun > AppData.ACTION_DELAY:
                medpos = get_median_position(tframe, self.selection_boundingbox)

            if self.removedBug != -1:
                self.frameCount += 1
                print(self.frameCount)

        else:
            self.activeFrameLastDiff = np.sum(tframe)/polyArea
            self.activeFrameSmoothDelta = 0

        frame = np.uint8(frame)
        # medpos = get_median_position(tframe, self.selection_boundingbox)
        return (frame, medpos)

    def refreshCamera(self):
        self.camBackground = np.copy(self.cameraImage)
        self.stableRun = 0

    def refreshCameraButton(self):
        self.refreshCamera()
        self.removedBug = -1


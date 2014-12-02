from PySide import QtCore, QtGui
from functools import partial
import numpy as np
import cv2

from Pt import *
from Util import *
import Hints

BLUE = (255, 0, 0)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
CYAN = (255, 255, 0)

class WitnessCam(QtCore.QObject):

    sigScanningModeOn = QtCore.Signal(bool)
    sigRemovedBug = QtCore.Signal(int)
    sigShowHint = QtCore.Signal(str)

    # States/Phases the application can be in
    SELECT_POLYGON, CALIBRATION, SCANNING_MODE = range(3)

    DRAW_DELTA = 10
    ACTION_DELAY = 25
    BOX_ERROR_TOLERANCE = 0.1
    BOX_BLENDING_FACTOR = 0.9
    GRAY_THRESHOLD = 20
    FRAME_DELTA_BLENDING_FACTOR = 1.0
    STABLE_FRAME_DELTA_THRESHOLD = 0.4
    STABLE_FRAME_ACTION_THRESHOLD = 0.5

    def __init__(self, logger):
        super(WitnessCam, self).__init__()

        self.logger = logger
        self.mainWindow = None
        self.reset()

    def setMainWindow(self, win):
        self.mainWindow = win

    def reset(self):
        self.phase = WitnessCam.SELECT_POLYGON
        self.polyPoints = []
        self.polyPointsRedo = []
        self.polygon_model = None
        self.rescalePlacedBoxes = True
        self.mouse_position_big_label = (0, 0)
        self.camBackground = None
        self.removedBug = -1
        self.currentSelectionBox = None
        self.calibrate = None

        # Variables used to fin the removed bug
        self.activeFrameCurrentDiff = None
        self.activeFrameLastDiff = None
        self.activeFrameSmoothDelta = None
        self.stableRun = 0
        self.stableBoxRun = 0
        self.stableAverage = 0
        self.lastStableAverage = 0
        self.lastMedpos = None

        self.camera_image = None
        self.logger.log('INIT WitnessCam class', 0)

    def amendFrame(self, camera_frame, static_frame, big_scale, small_scale,
                   placed_boxes):
        """Takes the raw (resized) camera frame, and the plain tray image and
        modifies it for display to the user, as well as updating the internal
        state of the program.

        Keywords Arguments:
        camera_frame -- image from camera as numpy array
        static_frame -- loaded tray scan image

        Return: (camera_frame, static_frame)
        camera_frame -- the processed frame from the camera view
        static_frame -- the amended tray image"""

        self.camera_image = camera_frame

        camera_frame_algo = np.copy(camera_frame)
        camera_frame_show = np.copy(camera_frame)
        static_frame = np.copy(static_frame)

        (mx, my) = self.mouse_position_big_label
        dB = int(WitnessCam.DRAW_DELTA/big_scale)
        dS = int(WitnessCam.DRAW_DELTA/small_scale)

        if self.phase == WitnessCam.SELECT_POLYGON:
            # Draw the cursor on the image
            cv2.line(camera_frame_show, (mx-dB, my), (mx+dB, my), BLUE, max(int(dB/5), 1))
            cv2.line(camera_frame_show, (mx, my-dB), (mx, my+dB), BLUE, max(int(dB/5), 1))

            # Draw the circles for the placed points
            for p in self.polyPoints:
                cv2.circle(camera_frame_show, (p.x, p.y), int(dB*0.6), GREEN)

            return (camera_frame_show, static_frame, placed_boxes)

        elif self.phase == WitnessCam.SCANNING_MODE:

            if self.rescalePlacedBoxes:
                for i in range(len(placed_boxes)):
                    (x, y) = placed_boxes[i].point
                    (x1, y1, x2, y2) = placed_boxes[i].static

                    (h, w, _) = static_frame.shape
                    p1 = square2poly(self.polygon_model, w, h, Pt(x1, y1))
                    p2 = square2poly(self.polygon_model, w, h, Pt(x1, y2))
                    p3 = square2poly(self.polygon_model, w, h, Pt(x2, y2))
                    p4 = square2poly(self.polygon_model, w, h, Pt(x2, y1))
                    x1 = min(p1.x, p2.x, p3.x, p4.x)
                    x2 = max(p1.x, p2.x, p3.x, p4.x)
                    y1 = min(p1.y, p2.y, p3.y, p4.y)
                    y2 = max(p1.y, p2.y, p3.y, p4.y)
                    placed_boxes[i].live = (x1, y1, x2, y2)

            self.rescalePlacedBoxes = False

            # Check if an insect has been moved from/to the tray, and get its
            # position in the camera frame
            (camera_frame_algo, centroid) =\
                self.getFrameDifferenceCentroid(camera_frame_algo)
            if centroid is not None:

                # If an insect has been removed, find the corresponding insect
                # in the tray image, and mark it
                (trayHeight, trayWidth, _) = static_frame.shape
                (u, v) = poly2square(self.polygon_model, trayWidth, trayHeight,
                                     centroid).t()
                cv2.line(static_frame, (u-dB, v), (u+dB, v), RED, max(int(dB/5), 1))
                cv2.line(static_frame, (u, v-dB), (u, v+dB), RED, max(int(dB/5), 1))


            # Draw all the boxes that have already been placed
            self.drawPlacedBoxes(static_frame, placed_boxes, GREEN, RED, BLUE, dB)

            # Once the camera view has been stable for a while, try to find box
            if self.stableRun >= WitnessCam.ACTION_DELAY:
                self.findCorrectBox(centroid, camera_frame_algo, static_frame, placed_boxes, dB)

            self.drawTrayArea(camera_frame_show, dS)
            return (static_frame, camera_frame_show, placed_boxes)

        elif self.phase == WitnessCam.CALIBRATION:
            (camera_frame_algo, centroid) =\
                self.getFrameDifferenceCentroid(camera_frame_algo)
            return (static_frame, camera_frame_algo, placed_boxes)

    def allowEditing(self):
        return self.phase == WitnessCam.SCANNING_MODE

    def mousePress(self, ev, scale):
        if self.phase == WitnessCam.SELECT_POLYGON:
            point = Pt(int(ev.pos().x()/scale), int(ev.pos().y()/scale))

            if any(map(lambda p: p==point, self.polyPoints)):
                self.sigShowHint.emit(Hints.HINT_TRAYAREA_BADPOINT)
            else:
                self.polyPoints.append(point)
                self.sigShowHint.emit(Hints.HINT_TRAYAREA_234)

                if len(self.polyPoints) == 4:
                    self.gotTrayArea()

                self.polyPointRedo = []

    def mouseMove(self, ev, scale):
        self.mouse_position_big_label = \
            (int(ev.pos().x()/scale), int(ev.pos().y()/scale))

    def mouseRelease(self, ev, scale):
        None

    def mouseScroll(self, ev, scale):
        None

    def getFrameDifferenceCentroid(self, frame):
        """Given the difference between teh current camera frame and the saved
        background image of the camera, find the point that represents the
        center of the difference.

        Keyword Arguments:
        frame -- the current camera frame

        Return: (frame, centroid)
        frame -- processed grayscale frame
        centroid -- center of difference"""

        # Setup a mask to block off certain parts of the difference image
        (h, w, d) = frame.shape
        polygon_mask = np.zeros((h, w, d), np.uint8)

        poly = None
        polyArea = -1
        poly = np.array([[p.x, p.y] for p in self.polyPoints],
                        dtype=np.int32)

        # Block off the area outside the tray
        polyArea = quadrilateralArea([(p.x, p.y) for p in self.polyPoints])
        cv2.drawContours(polygon_mask, [poly], 0, (1, 1, 1), -1)

        # Block off the box containing the removed insect
        if self.currentSelectionBox is not None:
            b = self.currentSelectionBox.live
            q0 = (int(b[0]), int(b[1]))
            q1 = (int(b[2]), int(b[1]))
            q2 = (int(b[2]), int(b[3]))
            q3 = (int(b[0]), int(b[3]))
            poly = np.array([q0, q1, q2, q3], dtype=np.int32)
            polyArea = polyArea - quadrilateralArea([q0, q1, q2, q3])
            cv2.drawContours(polygon_mask, [poly], 0, (0, 0, 0), -1)

        # Convert color image for current frame to grayscale image difference
        # and apply the mask to block off certain areas
        frame = cv2.cvtColor(frame, cv2.cv.CV_BGR2Lab)
        frame = np.absolute(np.subtract(self.camBackground.astype(int),
                            frame.astype(int))).astype(np.uint8)
        frame = np.add.reduce(np.square(np.multiply(
                              np.float32(frame), polygon_mask)), 2)
        frame = np.sqrt(frame)
        frame = cv2.GaussianBlur(frame, (5, 5), 0)
        frame = frame / math.sqrt(3)
        frame[frame < WitnessCam.GRAY_THRESHOLD] = 0
        tframe = np.copy(frame)

        # Use the processed image difference frame to find the center of the
        # difference
        medpos = None
        if self.activeFrameLastDiff is not None:

            # Compute the total difference of this frame, and the change from
            # last frame to this one
            a = WitnessCam.FRAME_DELTA_BLENDING_FACTOR
            self.activeFrameCurrentDiff = np.sum(tframe)/polyArea
            delta = self.activeFrameCurrentDiff - self.activeFrameLastDiff
            self.activeFrameSmoothDelta = \
                (1-a)*self.activeFrameSmoothDelta + a*delta
            self.activeFrameLastDiff = self.activeFrameCurrentDiff

            # If the change in difference from last frame to this one is small
            # consider it stable and increment the stable counter
            if abs(self.activeFrameSmoothDelta) \
                    < WitnessCam.STABLE_FRAME_DELTA_THRESHOLD:
                self.stableRun += 1
            else:
                self.stableRun = 0
                self.stableBoxRun = 0
                self.stableBox = None

            self.calibrate.updateValues(self.activeFrameCurrentDiff, self.activeFrameSmoothDelta)

            # If the frame has been stable for long enough, then
            if self.phase is not WitnessCam.CALIBRATION and \
                    self.stableRun > WitnessCam.ACTION_DELAY and \
                    self.activeFrameCurrentDiff \
                    > WitnessCam.STABLE_FRAME_ACTION_THRESHOLD:
                medpos = findWeightedMedianPoint2D(
                    tframe, self.trayBoundingBox)

                if self.lastMedpos is not None and medpos is not None:
                    (x0, y0) = self.lastMedpos.t()
                    (x, y) = medpos.t()
                    if (x0-x) != 0 or (y0-y) != 0:
                        self.stableRun = 0
                        self.stableBoxRun = 0
                        self.stableBox = None

        else:
            self.activeFrameLastDiff = np.sum(tframe)/polyArea
            self.activeFrameSmoothDelta = 0

        self.lastMedpos = medpos
        frame = np.uint8(frame)
        return (frame, medpos)

    def drawPlacedBoxes(self, image, boxes, regular, selected, active, a):
        """Given an input image, draw all of the generated boxes on the image.
        Optional colour paramaters can also be supplied.

        Keyword Arguments:
        image -- the numpy array image that the boxes will be drawn on
        regular -- the colour of the boxes
        selected -- the colour of the selected box
        """

        if self.phase == WitnessCam.SCANNING_MODE:
            for i in range(len(boxes)):

                b = boxes[i].static
                (px, py) = boxes[i].point
                t = max(int(a/5), 1)
                col = None

                if i == self.removedBug:
                    col = active
                    ((_,h),_) = cv2.getTextSize(boxes[i].name, cv2.FONT_HERSHEY_SIMPLEX, a/18.0, t)
                    cv2.putText(image, boxes[i].name, (b[0]-int(a/2), b[3]+h), cv2.FONT_HERSHEY_SIMPLEX, a/18.0, WHITE, t)
                    cv2.rectangle(image, b[0:2], b[2:4], active, t)
                else:
                    col = regular

                cv2.line(image, (px, py-a), (px, py+a), col, t)
                cv2.line(image, (px+a, py), (px-a, py), col, t)
                cv2.circle(image, (px, py), a, col, t)

    def findCorrectBox(self, live_pt, live_frame, static_frame, placed_boxes, big_draw):
        """Finds the correct place to create a box once an insect has been
        removed from the draw, or selects an exsisting box.

        Keyword Arguments:
        live_pt -- a point on the live frame representing the location of the
            insect
        live_frame -- grayscale difference map of the current camera frame"""

        if live_pt is not None:
            # Generate a box on the camera image that contains the live point
            (static_box, live_box) = self.floodFillBox(live_pt, live_frame, static_frame)

            if static_box is not None:
                (trayHeight, trayWidth, _) = static_frame.shape
                static_pt = poly2square(self.polygon_model, trayWidth,
                                        trayHeight, live_pt)

                # Determine whether this box is stable (not jumping around and
                # wildly changing)
                if self.stableBox is None:
                    # If no stable box has been set, set one
                    self.stableBox = (static_box, live_box, static_pt)
                else:

                    # Compare the new box to the stable one
                    (x1, y1, x2, y2) = self.stableBox[0]
                    (x3, y3, x4, y4) = static_box
                    t = max(big_draw/5, 1)
                    cv2.rectangle(static_frame, (x1, y1), (x2, y2), CYAN, t)
                    cv2.rectangle(static_frame, (x3, y3), (x4, y4), WHITE, t)
                    w = x2-x1
                    h = y2-y1
                    eps = WitnessCam.BOX_ERROR_TOLERANCE
                    if (abs(x3-x1) < w*eps and abs(y3-y1) < h*eps and
                            abs(x4-x2) < w*eps and abs(y4-y2) < h*eps):
                        # If the new box is close enough to the stable one,
                        # keep it
                        a = WitnessCam.BOX_BLENDING_FACTOR
                        self.stableBoxRun += 1
                        self.stableBox = ((int(a*x3+(1-a)*x1),
                                           int(a*y3+(1-a)*y1),
                                           int(a*x4+(1-a)*x2),
                                           int(a*y4+(1-a)*y2)),
                                          live_box,
                                          static_pt.t())
                    else:
                        # If the new box is too different, the reset the stable
                        # counter and the stable box
                        self.stableBoxRun = 0
                        self.stableBox = (static_box, live_box, static_pt)

                # If the box has been stable for long enough, accept it
                if self.stableBoxRun >= WitnessCam.ACTION_DELAY:

                    # If the new box significantly overlaps an exsisting box,
                    # use the exsisting box instead
                    i = getOverlappingBox([b.static for b in placed_boxes],
                                          self.stableBox[0])
                    if i == -1:
                        box = BugBox("Box " + str(len(placed_boxes)),
                                     self.stableBox[1],
                                     self.stableBox[0],
                                     self.stableBox[2])
                        placed_boxes.newBox(box)
                        self.setCurrentSelectionBox(placed_boxes, len(placed_boxes)-1)
                        self.refreshCamera()
                    else:
                        self.setCurrentSelectionBox(placed_boxes, i)
                        self.refreshCamera()

                    self.sigShowHint.emit(Hints.HINT_ENTERBARCODE)

    def gotTrayArea(self):
        """Called when the user has selected the four points that represent
        the corners of the insect tray in the camera view."""

        # Get the axis aligned bounding box for the tray area selection
        (minx, miny, maxx, maxy) = \
            (self.polyPoints[0].x, self.polyPoints[0].y, 0, 0)
        for p in self.polyPoints:
            minx = p.x if p.x < minx else minx
            miny = p.y if p.y < miny else miny
            maxx = p.x if p.x > maxx else maxx
            maxy = p.y if p.y > maxy else maxy

        self.trayBoundingBox = [Pt(minx, miny), Pt(maxx, maxy)]
        self.polygon_model = buildPolygonSquareModel(self.polyPoints)

        self.sigScanningModeOn.emit(True)

        if self.calibrate is None:
            self.phase = WitnessCam.CALIBRATION
            self.showCalibrationWindow()
            self.sigShowHint.emit(Hints.HINT_CALIBRATE)
        else:
            self.phase = WitnessCam.SCANNING_MODE
            self.sigShowHint.emit(Hints.HINT_REMOVE_OR_EDIT)

        # Save the current view of the camera
        self.refreshCamera()


    def showCalibrationWindow(self):
        self.calibrate = WitnessCam.CalibrationWindow(self)

    def floodFillBox(self, p, camera_mask, static_frame):
        """Given a grayscale image and a point, return a bounding box
        encompassing all the non-zero elements of the image connected to the
        point. It returns the box dimensions on the camera frame, as well as
        the static frame.

        Keyword Arguments:
        p -- the point on the camera image
        camera_mask -- the grayscale camera image difference

        Return: (live_box, static_box)
        live_box -- the dimensions of the box (x1,y1,x2,y2) on the live frame
        static_ box -- the dimensions of the box (x1,y1,x2,y2) on the static
            frame"""

        # Convert grayscale image to binary mask
        frame = np.copy(camera_mask)
        frame[frame > WitnessCam.GRAY_THRESHOLD] = 1

        # Find countours in image
        staticContour = []
        conts, hir = cv2.findContours(frame, cv2.RETR_LIST,
                                      cv2.CHAIN_APPROX_NONE)

        # Find contour that encases the point
        for i in range(len(conts)):
            if cv2.pointPolygonTest(conts[i], p.t(), True) >= 0:
                (trayHeight, trayWidth, _) = static_frame.shape
                (sx1, sy1, sx2, sy2) = (trayWidth, trayHeight, 0, 0)
                (lx1, ly1, lx2, ly2) = (trayWidth, trayHeight, 0, 0)

                # Generate the box that encases the contour in both the live
                # and static image
                for q in conts[i]:
                    (lx, ly) = q[0]
                    (sx, sy) = poly2square(
                        self.polygon_model, trayWidth, trayHeight,
                        Pt(q[0, 0], q[0, 1])).t()
                    sx1 = min(sx1, sx)
                    sy1 = min(sy1, sy)
                    sx2 = max(sx2, sx)
                    sy2 = max(sy2, sy)
                    lx1 = min(lx1, lx)
                    ly1 = min(ly1, ly)
                    lx2 = max(lx2, lx)
                    ly2 = max(ly2, ly)
                    staticContour.append((sx, sy))
                return ((sx1, sy1, sx2, sy2), (lx1, ly1, lx2, ly2))

        return (None, None)


    def resetTrayArea(self):
        self.phase = WitnessCam.SELECT_POLYGON

        self.polyPoints = []

        self.trayBoundingBox = None
        self.polygonModel = None
        self.sigScanningModeOn.emit(False)

        self.setCurrentSelectionBox(None, -1)

        self.rescalePlacedBoxes = True

        self.sigShowHint.emit(Hints.HINT_TRAYAREA_1)

    def drawTrayArea(self, image, a):
        for i in range(len(self.polyPoints)):
            p1 = self.polyPoints[i].t()
            p2 = self.polyPoints[(i+1)%len(self.polyPoints)].t()
            cv2.line(image, p1, p2, BLUE, max(a/5, 1))

    def refreshCamera(self):
        """Save the current camera view as the background, and reset some
        counters"""
        if self.phase is WitnessCam.SCANNING_MODE or self.phase is WitnessCam.CALIBRATION:
            self.camBackground = np.copy(self.camera_image)
            self.camBackground = cv2.cvtColor(self.camBackground,
                                              cv2.cv.CV_BGR2Lab)
            self.stableRun = 0
            self.stableRunBox = 0

    def setCurrentSelectionBox(self, boxes, i=-1):
        if boxes is not None and i != -1:
            self.currentSelectionBox = boxes[i]
            self.sigShowHint.emit(Hints.HINT_ENTERBARCODE)
        else:
            self.currentSelectionBox = None

        self.removedBug = i
        self.sigRemovedBug.emit(i)

    def onEditBoxSelected(self, i):
        self.refreshCamera()
        self.setCurrentSelectionBox(None, -1)

    def onEditBoxDeleted(self, i):
        self.refreshCamera()

    def undo(self):
        if self.phase == WitnessCam.SELECT_POLYGON and len(self.polyPoints) > 0:
            self.polyPointsRedo.append(self.polyPoints[-1])
            del self.polyPoints[-1]
            return True
        else:
            return False

    def redo(self):
        if self.phase == WitnessCam.SELECT_POLYGON and len(self.polyPointsRedo) > 0:
            self.polyPoints.append(self.polyPointsRedo[-1])
            del self.polyPointsRedo[-1]
            return True
        else:
            return False

    class CalibrationWindow(QtGui.QWidget):
        def __init__(self, data, parent=None):
            super(WitnessCam.CalibrationWindow, self).__init__(parent)
            self.initUI()

            self.calibrationStage = 0
            self.data = data
            self.diffValues = []
            self.deltaValues = []

        def initUI(self):
            mainContent = QtGui.QGridLayout(self)

            self.btnNext = QtGui.QPushButton('Make sure the camera is perfectly still, and has a clear view of the tray. \n\
Then Click Here')

            self.lblActDelay = QtGui.QLabel('ACTION_DELAY: ')
            self.txtActDelayVal = QtGui.QLineEdit(str(WitnessCam.ACTION_DELAY))
            self.txtActDelayVal.setValidator(QtGui.QIntValidator())
            self.txtActDelayVal.setEnabled(False)

            self.lblDelta = QtGui.QLabel('STABLE_FRAME_DELTA_THRESHOLD: ')
            self.txtDeltaVal = QtGui.QLineEdit(str(WitnessCam.STABLE_FRAME_DELTA_THRESHOLD))
            self.txtDeltaVal.setValidator(QtGui.QDoubleValidator())
            self.txtDeltaVal.setEnabled(False)

            self.lblAction = QtGui.QLabel('STABLE_FRAME_ACTION_THRESHOLD: ')
            self.txtActionVal = QtGui.QLineEdit(str(WitnessCam.STABLE_FRAME_ACTION_THRESHOLD))
            self.txtActionVal.setValidator(QtGui.QDoubleValidator())
            self.txtActionVal.setEnabled(False)

            mainContent.addWidget(self.lblActDelay, 1, 0)
            mainContent.addWidget(self.txtActDelayVal, 1, 1)
            mainContent.addWidget(self.lblDelta, 2, 0)
            mainContent.addWidget(self.txtDeltaVal, 2, 1)
            mainContent.addWidget(self.lblAction, 3, 0)
            mainContent.addWidget(self.txtActionVal, 3, 1)
            mainContent.addWidget(self.btnNext, 0, 0, 1, 2)

            self.setLayout(mainContent)

            self.btnNext.clicked.connect(self.nextStep)
            self.txtActDelayVal.textChanged.connect(partial(self.textChanged, 0))
            self.txtDeltaVal.textChanged.connect(partial(self.textChanged, 1))
            self.txtActionVal.textChanged.connect(partial(self.textChanged, 2))

            self.resize(250, 150)
            self.setWindowTitle('Calibration')
            self.show()

        def closeEvent(self, event):
            event.ignore()

        def nextStep(self):
            self.calibrationStage += 1
            if self.calibrationStage == 1:
                self.btnNext.setText('Wait about 5 seconds without disturbing the camera view,\nthen Click Here again.')
                self.diffValues = []
                self.deltaValues = []
            elif self.calibrationStage == 2:
                self.btnNext.setText('Remove any insect from the tray\nthen Click Here.')
                self.delay = len(self.diffValues)/5
                self.diff = sum(self.diffValues) / len(self.diffValues)
                self.delta = sum(map(abs, self.deltaValues)) / len(self.deltaValues)
            elif self.calibrationStage == 3:
                self.btnNext.setText('Wait about 5 seconds without disturbing the camera view,\nthen Click Here again.')
                self.diffValues = []
                self.deltaValues = []
            elif self.calibrationStage == 4:
                self.btnNext.setText('Replace the insect on the tray then\nClick Here.')
                self.delay = len(self.diffValues)/5
                self.diff = sum(self.diffValues) / len(self.diffValues)
                self.delta = sum(map(abs, self.deltaValues)) / len(self.deltaValues)
                print(self.delay, self.diff/10, self.delta*20)
                self.txtActDelayVal.setText(str(int(self.delay)))
                self.txtDeltaVal.setText(str(self.delta*20))
                self.txtActionVal.setText(str(self.diff/10))
            elif self.calibrationStage == 5:
                self.btnNext.setText('Calibration Done. Config values chosen.\nIf ever editing the below values, be sure all insects are on the tray')
                self.data.sigShowHint.emit(Hints.HINT_REMOVEBUG_OR_EDIT)
                self.data.phase = WitnessCam.SCANNING_MODE
                self.data.refreshCamera()
                self.btnNext.setEnabled(False)
                self.txtActDelayVal.setEnabled(True)
                self.txtDeltaVal.setEnabled(True)
                self.txtActionVal.setEnabled(True)
                self.data.mainWindow.raise_()

        def updateValues(self, diff, delta):
            self.diffValues.append(diff)
            self.deltaValues.append(delta)

        def textChanged(self, config, val):
            self.data.refreshCamera()
            if config == 0:
                WitnessCam.ACTION_DELAY = int(val)
            elif config == 1:
                WitnessCam.STABLE_FRAME_DELTA_THRESHOLD = float(val)
            elif config == 2:
                WitnessCam.STABLE_FRAME_ACTION_THRESHOLD = float(val)

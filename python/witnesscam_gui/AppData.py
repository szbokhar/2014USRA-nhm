from PySide import QtCore, QtGui
import cv2
import csv
import numpy as np
import os.path
import sys

from Util import *
from Pt import *

BLUE = (255, 0, 0)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
CYAN = (255, 255, 0)


class AppData:
    """Main logic controler for the digitization gui"""

    # States/Phases the application can be in
    LOAD_FILE, SELECT_POLYGON, SCANNING_MODE = range(3)

    # Types of editing actions for boxes
    NO_ACTION, DG_NW, DG_N, DG_NE, DG_E, DG_SE, DG_S, DG_SW, DG_W, PAN = \
        range(10)

    # Number of stable frames to wait before performing certain actions
    DRAW_DELTA = 10
    ACTION_DELAY = 25
    BOX_ERROR_TOLERANCE = 0.1
    BOX_BLENDING_FACTOR = 0.9
    GRAY_THRESHOLD = 20
    FRAME_DELTA_BLENDING_FACTOR = 1.0
    STABLE_FRAME_DELTA_THRESHOLD = 0.4
    STABLE_FRAME_ACTION_THRESHOLD = 0.5

    def __init__(self):
        """Initializes a bunch of member variables for use in later
        functions"""

        # Labels for displaying images
        self.cameraLabel = None
        self.staticLabel = None
        self.controlPanel = None
        self.lblBig = None
        self.lblSmall = None

        # Whether the camera has been turned on yet
        self.camOn = False

        # Mouse cursors used when editing boxes
        self.resizeCursorH = QtGui.QCursor(QtCore.Qt.SizeHorCursor)
        self.resizeCursorV = QtGui.QCursor(QtCore.Qt.SizeVerCursor)
        self.resizeCursorB = QtGui.QCursor(QtCore.Qt.SizeBDiagCursor)
        self.resizeCursorF = QtGui.QCursor(QtCore.Qt.SizeFDiagCursor)
        self.prepanCursor = QtGui.QCursor(QtCore.Qt.OpenHandCursor)
        self.midpanCursor = QtGui.QCursor(QtCore.Qt.ClosedHandCursor)
        self.selectCursor = QtGui.QCursor(QtCore.Qt.CrossCursor)
        self.normalCursor = QtGui.QCursor(QtCore.Qt.ArrowCursor)

        self.reset()

    def reset(self):
        # Set labes
        self.cameraLabel = self.lblBig
        self.staticLabel = self.lblSmall

        # Mouse position (current and last) on the big label
        self.bigMPos = (0, 0)
        self.bigMLastPos = (0, 0)

        # The phase the application is in
        self.phase = AppData.LOAD_FILE

        # Variables storing info about the quadrilateral containing the tray
        self.polyPoints = []
        self.polygonModel = None
        self.trayBoundingBox = None

        # Variables used to fin the removed bug
        self.activeFrameCurrentDiff = None
        self.activeFrameLastDiff = None
        self.activeFrameSmoothDelta = None
        self.stableRun = 0
        self.stableAverage = 0
        self.lastStableAverage = 0
        self.removedBug = -1
        self.frameCount = 0
        self.lastMedpos = None

        # Variables used in keeping track of the placed boxes
        self.currentSelectionBox = None
        self.placedBoxes = []
        self.stableBoxRun = 0
        self.stableBox = None
        self.rescalePlacedboxes = False

        # Variables used for editing the boxes
        self.selectedEditBox = None
        self.editAction = AppData.NO_ACTION

    def setGuiElements(self, control, big, small):
        """Associate the elements of the gui with the application data.

        Keyword Arguments:
        control -- a ControlPanel instance
        big -- a BigLabel instance
        small -- a SmallLabel instance"""

        # Assign gui elements
        self.controlPanel = control
        self.lblBig = big
        self.lblSmall = small

        # Connect signals and slots
        self.lblBig.sigMousePress.connect(self.bigLabelMousePress)
        self.lblBig.sigMouseMove.connect(self.bigLabelMouseMove)
        self.lblBig.sigMouseRelease.connect(self.bigLabelMouseRelease)

        # Have members to remember which label is showing what
        self.cameraLabel = self.lblBig
        self.staticLabel = self.lblSmall

    def setTrayScan(self, image_fname, csv_fname):
        """Load the tray scan image and activate the camera.

        Keyword Arguments:
        image_fname -- the string filepath of the tray scan image"""

        # Load the image
        self.trayPath = image_fname
        self.trayImage = cv2.imread(self.trayPath, cv2.IMREAD_COLOR)

        # Load csv file
        if os.path.isfile(csv_fname):
            with open(csv_fname) as csvfile:
                reader = csv.reader(csvfile)
                self.placedBoxes = []
                for b in reader:
                    box = BugBox(b[0], None, (int(b[1]), int(b[2]), int(b[3]),
                                 int(b[4])), (int(b[5]), int(b[6])))
                    self.placedBoxes.append(box)

                self.rescalePlacedBoxes = True

        # Downscale the image
        height = self.trayImage.shape[0]
        self.trayImage = cv2.pyrDown(self.trayImage)
        self.trayImageScale = float(self.trayImage.shape[0])/height

        # Display the image
        self.staticLabel.setImage(self.trayImage)

        # Clear data
        self.reset()

        # Start the camera loop
        self.startCameraFeed()
        self.phase = AppData.SELECT_POLYGON

    def startCameraFeed(self):
        """Begin the camera feed and set up the timer loop."""

        if not self.camOn:
            self.capture = cv2.VideoCapture(0)

            self.frameTimer = QtCore.QTimer()
            self.frameTimer.timeout.connect(self.getNewCameraFrame)
            self.frameTimer.start(30)
            self.camOn = True

    def getNewCameraFrame(self):
        """This function is called by the timer 30 times a second to fetch a new
        frame from the camera, have it processed, and display the final result
        to on screen."""

        # Get new camera frame and reload fresh static frame
        _, cameraImage = self.capture.read()
        self.cameraImage = cv2.pyrDown(cameraImage)
        self.cameraImage = cv2.pyrDown(self.cameraImage)

        # Process and modify the camera and static frames
        (cameraFrame, staticFrame) = self.amendFrame(self.cameraImage,
                                                     self.trayImage)

        # Display the modified frame to the user
        self.cameraLabel.setImage(cameraFrame)
        self.staticLabel.setImage(staticFrame)

    def setMousepos(self, x, y):
        """Update the current mouse position"""

        self.bigMPos = (x, y)

    def amendFrame(self, camera_frame, static_frame):
        """Takes the raw (resized) camera frame, and the plain tray image and
        modifies it for display to the user, as well as updating the internal
        state of the program.

        Keywords Arguments:
        camera_frame -- image from camera as numpy array
        static_frame -- loaded tray scan image

        Return: (camera_frame, static_frame)
        camera_frame -- the processed frame from the camera view
        static_frame -- the amended tray image"""

        camera_frame = np.copy(camera_frame)
        static_frame = np.copy(static_frame)

        (mx, my) = self.bigMPos
        d = AppData.DRAW_DELTA

        if self.phase == AppData.SELECT_POLYGON:
            # Draw the cursor on the image
            cv2.line(camera_frame, (mx-d, my), (mx+d, my), BLUE, 1)
            cv2.line(camera_frame, (mx, my-d), (mx, my+d), BLUE, 1)

            # Draw the circles for the placed points
            for p in self.polyPoints:
                cv2.circle(camera_frame, (p.x, p.y), 5, GREEN)

        elif self.phase == AppData.SCANNING_MODE:

            # Check if an insect has been moved from/to the tray, and get its
            # position in the camera frame
            (camera_frame, centroid) =\
                self.getFrameDifferenceCentroid(camera_frame)
            if centroid is not None:

                # If an insect has been removed, find the corresponding insect
                # in the tray image, and mark it
                (trayHeight, trayWidth, _) = self.trayImage.shape
                (u, v) = poly2square(self.polygon_model, trayWidth, trayHeight,
                                     centroid).t()
                cv2.line(static_frame, (u-d, v), (u+d, v), RED, 5)
                cv2.line(static_frame, (u, v-d), (u, v+d), RED, 5)

            # Draw all the boxes that have already been placed
            self.drawPlacedBoxes(static_frame, GREEN, RED, BLUE)

            # Once the camera view has been stable for a while, try to find box
            if self.stableRun >= AppData.ACTION_DELAY:
                self.findCorrectBox(centroid, camera_frame, static_frame)

        return (camera_frame, static_frame)

    def drawPlacedBoxes(self, image, regular, selected, active):
        """Given an input image, draw all of the generated boxes on the image.
        Optional colour paramaters can also be supplied.

        Keyword Arguments:
        image -- the numpy array image that the boxes will be drawn on
        regular -- the colour of the boxes
        selected -- the colour of the selected box
        """

        for i in range(len(self.placedBoxes)):
            if self.rescalePlacedBoxes:
                s = self.trayImageScale
                (x, y) = self.placedBoxes[i].point
                self.placedBoxes[i].point = (int(x*s), int(y*s))
                (x1, y1, x2, y2) = self.placedBoxes[i].static
                self.placedBoxes[i].static =\
                    (int(x1*s), int(y1*s), int(x2*s), int(y2*s))
                (x1, y1, x2, y2) = self.placedBoxes[i].static

                (h, w, _) = self.trayImage.shape
                p1 = square2poly(self.polygon_model, w, h, Pt(x1, y1))
                p2 = square2poly(self.polygon_model, w, h, Pt(x1, y2))
                p3 = square2poly(self.polygon_model, w, h, Pt(x2, y2))
                p4 = square2poly(self.polygon_model, w, h, Pt(x2, y1))
                x1 = min(p1.x, p2.x, p3.x, p4.x)
                x2 = max(p1.x, p2.x, p3.x, p4.x)
                y1 = min(p1.y, p2.y, p3.y, p4.y)
                y2 = max(p1.y, p2.y, p3.y, p4.y)
                self.placedBoxes[i].live = (x1, y1, x2, y2)

            b = self.placedBoxes[i].static
            (px, py) = self.placedBoxes[i].point
            a = AppData.DRAW_DELTA*2
            col = None

            if i == self.selectedEditBox:
                cv2.rectangle(image, b[0:2], b[2:4], selected, 2)
                col = selected

            if i == self.removedBug:
                col = active

            if i != self.removedBug and i != self.selectedEditBox:
                col = regular

            cv2.line(image, (px-a, py-a), (px+a, py+a), col, 2)
            cv2.line(image, (px+a, py-a), (px-a, py+a), col, 2)
            cv2.circle(image, (px, py), int(math.sqrt(2)*a), col, 2)

        self.rescalePlacedBoxes = False

    def findCorrectBox(self, live_pt, live_frame, static_frame):
        """Finds the correct place to create a box once an insect has been
        removed from the draw, or selects an exsisting box.

        Keyword Arguments:
        live_pt -- a point on the live frame representing the location of the
            insect
        live_frame -- grayscale difference map of the current camera frame"""

        if live_pt is not None:
            r = self.trayImageScale

            # Generate a box on the camera image that contains the live point
            (static_box, live_box) = self.floodFillBox(live_pt, live_frame)

            if static_box is not None:
                (trayHeight, trayWidth, _) = self.trayImage.shape
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
                    cv2.rectangle(static_frame, (x1, y1), (x2, y2), CYAN, 2)
                    cv2.rectangle(static_frame, (x3, y3), (x4, y4), WHITE, 2)
                    w = x2-x1
                    h = y2-y1
                    eps = AppData.BOX_ERROR_TOLERANCE
                    if (abs(x3-x1) < w*eps and abs(y3-y1) < h*eps and
                            abs(x4-x2) < w*eps and abs(y4-y2) < h*eps):
                        # If the new box is close enough to the stable one,
                        # keep it
                        a = AppData.BOX_BLENDING_FACTOR
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
                if self.stableBoxRun >= AppData.ACTION_DELAY:

                    # If the new box significantly overlaps an exsisting box,
                    # use the exsisting box instead
                    i = getOverlappingBox([b.static for b in self.placedBoxes],
                                          self.stableBox[0])
                    if i == -1:
                        box = BugBox("Box " + str(len(self.placedBoxes)),
                                     self.stableBox[1],
                                     self.stableBox[0],
                                     self.stableBox[2])
                        self.placedBoxes.append(box)
                        self.setCurrentSelectionBox(len(self.placedBoxes)-1)
                        self.refreshCamera()
                    else:
                        self.setCurrentSelectionBox(i)
                        self.refreshCamera()

    def floodFillBox(self, p, camera_mask):
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
        frame[frame > AppData.GRAY_THRESHOLD] = 1

        # Find countours in image
        staticContour = []
        conts, hir = cv2.findContours(frame, cv2.RETR_LIST,
                                      cv2.CHAIN_APPROX_NONE)

        # Find contour that encases the point
        for i in range(len(conts)):
            if cv2.pointPolygonTest(conts[i], p.t(), True) >= 0:
                (trayHeight, trayWidth, _) = self.trayImage.shape
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

    def gotTrayArea(self):
        """Called when the user has selected the four points that represent
        the corners of the insect tray in the camera view."""

        # Save the current view of the camera
        self.refreshCamera()

        # Change phase to scanning mode
        self.phase = AppData.SCANNING_MODE

        # Swap the labels to place the insect tray image in the bigger label
        tmp = self.cameraLabel
        self.cameraLabel = self.staticLabel
        self.staticLabel = tmp

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

        self.controlPanel.btnRefreshCamera.setEnabled(True)

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
        frame[frame < AppData.GRAY_THRESHOLD] = 0
        tframe = np.copy(frame)

        # Use the processed image difference frame to find the center of the
        # difference
        medpos = None
        if self.activeFrameLastDiff is not None:

            # Compute the total difference of this frame, and the change from
            # last frame to this one
            a = AppData.FRAME_DELTA_BLENDING_FACTOR
            self.activeFrameCurrentDiff = np.sum(tframe)/polyArea
            delta = self.activeFrameCurrentDiff - self.activeFrameLastDiff
            self.activeFrameSmoothDelta = \
                (1-a)*self.activeFrameSmoothDelta + a*delta
            self.activeFrameLastDiff = self.activeFrameCurrentDiff

            # If the cchange in difference from last frame to this one is small
            # consider it stable and increment the stable counter
            if abs(self.activeFrameSmoothDelta) \
                    < AppData.STABLE_FRAME_DELTA_THRESHOLD:
                self.stableRun += 1
            else:
                self.stableRun = 0
                self.stableBoxRun = 0
                self.stableBox = None

            # If the frame has been stable for long enough, then
            if self.stableRun > AppData.ACTION_DELAY and \
                    self.activeFrameCurrentDiff \
                    > AppData.STABLE_FRAME_ACTION_THRESHOLD:
                medpos = findWeightedMedianPoint2D(
                    tframe, self.trayBoundingBox)

                if self.lastMedpos is not None and medpos is not None:
                    (x0, y0) = self.lastMedpos.t()
                    (x, y) = medpos.t()
                    if (x0-x) != 0 or (y0-y) != 0:
                        self.stableRun = 0
                        self.stableBoxRun = 0
                        self.stableBox = None

            # Overall frame count
            if self.removedBug != -1:
                self.frameCount += 1

        else:
            self.activeFrameLastDiff = np.sum(tframe)/polyArea
            self.activeFrameSmoothDelta = 0

        self.lastMedpos = medpos
        frame = np.uint8(frame)
        return (frame, medpos)

    def refreshCamera(self):
        """Save the current camera view as the background, and reset some
        counters"""
        self.camBackground = np.copy(self.cameraImage)
        self.camBackground = cv2.cvtColor(self.camBackground,
                                          cv2.cv.CV_BGR2Lab)
        self.stableRun = 0

    def refreshCameraButton(self):
        """When the refresh camer button is pressed"""
        self.refreshCamera()
        self.setCurrentSelectionBox(-1)

    def exportToCSV(self):
        """Called when the Export to CSV button is pressed"""
        fname, _ = QtGui.QFileDialog.getSaveFileName()

        f = open(fname, 'w')
        for b in self.placedBoxes:
            f.write(b.name + ", " +
                    str(b.getStaticBox(1/self.trayImageScale))[1:-1] + ', ' +
                    str(b.getPoint(1/self.trayImageScale))[1:-1] + '\n')

    def bigLabelMousePress(self, ev, scale):
        """When the mouse is clicked on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object
        scale -- scale constant between the size of the label and the size
            of the big label"""
        if self.phase == AppData.SELECT_POLYGON:
            self.polyPoints.append(
                Pt(int(ev.pos().x()/scale),
                   int(ev.pos().y()/scale)))

            if len(self.polyPoints) == 4:
                self.gotTrayArea()

        elif self.phase == AppData.SCANNING_MODE:
            self.editMousePress(ev)

    def bigLabelMouseMove(self, ev, scale):
        """When the mouse is clicked on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object
        scale -- scale constant between the size of the label and the size
            of the big label"""
        self.setMousepos(int(ev.pos().x()/scale),
                         int(ev.pos().y()/scale))

        if self.phase == AppData.SCANNING_MODE:
            self.editMouseMove()

    def bigLabelMouseRelease(self, ev):
        """When the mouse is clicked on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object"""
        if self.phase == AppData.SCANNING_MODE:
            self.editMouseRelease()

    def editMousePress(self, ev):
        """Called when the application is in edit mode and the mouse is clicked
        on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object"""

        (mx, my) = self.bigMPos
        c = 15

        if self.selectedEditBox is not None:
            # If a box is selected, check for clicking on an editable point
            # (e. corners for resizing, center for panning)
            p = self.bigMPos
            (x1, y1, x2, y2) = self.placedBoxes[self.selectedEditBox].static
            if ev.button() == QtCore.Qt.MouseButton.LeftButton:
                # Process left click
                if pointInBox(p, (x1-c, y1-c, x1+c, y1+c)):
                    self.editAction = AppData.DG_NW
                elif pointInBox(p, (x2-c, y2-c, x2+c, y2+c)):
                    self.editAction = AppData.DG_SE
                elif pointInBox(p, (x1-c, y2-c, x1+c, y2+c)):
                    self.editAction = AppData.DG_SW
                elif pointInBox(p, (x2-c, y1-c, x2+c, y1+c)):
                    self.editAction = AppData.DG_NE
                elif pointInBox(p, (x1+c, y1-c, x2-c, y1+c)):
                    self.editAction = AppData.DG_N
                elif pointInBox(p, (x1+c, y2-c, x2-c, y2+c)):
                    self.editAction = AppData.DG_S
                elif pointInBox(p, (x1-c, y1+c, x1+c, y2-c)):
                    self.editAction = AppData.DG_W
                elif pointInBox(p, (x2-c, y1+c, x2+c, y2-c)):
                    self.editAction = AppData.DG_E
                elif pointInBox(p, (x1+c, y1+c, x2-c, y2-c)):
                    self.editAction = AppData.PAN

                if self.editAction != AppData.NO_ACTION:
                    return
            elif ev.button() == QtCore.Qt.MouseButton.RightButton:
                # Process right click
                if pointInBox(p, (x1, y1, x2, y2)):
                    if self.removedBug == self.selectedEditBox:
                        self.setCurrentSelectionBox(-1)
                        self.refreshCamera()
                    del self.placedBoxes[self.selectedEditBox]
                    self.selectedEditBox = None

                    self.refreshCamera()

                    return

        # If a box is not selected, check for clicking on a box to
        # to select it
        clickedOn = False
        for i in range(len(self.placedBoxes)):
            (x1, y1, x2, y2) = self.placedBoxes[i].static
            if pointInBox((mx, my), (x1-c, y1-c, x2+c, y2+c)):
                clickedOn = True
                self.selectedEditBox = i
                self.controlPanel.setCurrentBugId(self.placedBoxes[i].name)
                self.setCurrentSelectionBox(-1)
                self.refreshCamera()

        # Check for deselect of box
        if not clickedOn:
            self.selectedEditBox = None

    def editMouseMove(self):
        """Called when the application is in edit mode and the mouse is moved
        on the big label."""

        p = self.bigMPos

        # Show box select cursor if hovered over box
        self.staticLabel.setCursor(self.normalCursor)
        for b in self.placedBoxes:
            if pointInBox(p, b.static):
                self.staticLabel.setCursor(self.selectCursor)

        # If box is selected, show various cursors for editing functions
        if self.selectedEditBox is not None:
            if self.editAction == AppData.NO_ACTION:
                c = 15
                (x1, y1, x2, y2) =\
                    self.placedBoxes[self.selectedEditBox].static
                if pointInBox(p, (x1-c, y1-c, x1+c, y1+c)):
                    self.staticLabel.setCursor(self.resizeCursorF)
                elif pointInBox(p, (x2-c, y2-c, x2+c, y2+c)):
                    self.staticLabel.setCursor(self.resizeCursorF)
                elif pointInBox(p, (x1-c, y2-c, x1+c, y2+c)):
                    self.staticLabel.setCursor(self.resizeCursorB)
                elif pointInBox(p, (x2-c, y1-c, x2+c, y1+c)):
                    self.staticLabel.setCursor(self.resizeCursorB)
                elif pointInBox(p, (x1+c, y1-c, x2-c, y1+c)):
                    self.staticLabel.setCursor(self.resizeCursorV)
                elif pointInBox(p, (x1+c, y2-c, x2-c, y2+c)):
                    self.staticLabel.setCursor(self.resizeCursorV)
                elif pointInBox(p, (x1-c, y1+c, x1+c, y2-c)):
                    self.staticLabel.setCursor(self.resizeCursorH)
                elif pointInBox(p, (x2-c, y1+c, x2+c, y2-c)):
                    self.staticLabel.setCursor(self.resizeCursorH)
                elif pointInBox(p, (x1+c, y1+c, x2-c, y2-c)):
                    self.staticLabel.setCursor(self.prepanCursor)
            else:
                (dx, dy) = (self.bigMPos[0] - self.bigMLastPos[0],
                            self.bigMPos[1] - self.bigMLastPos[1])
                b = self.placedBoxes[self.selectedEditBox]
                (x1, y1, x2, y2) = b.static
                newBox = b.static
                (px, py) = b.point
                newPoint = b.point
                if self.editAction == AppData.DG_NW:
                    newBox = (x1+dx, y1+dy, x2, y2)
                    self.staticLabel.setCursor(self.resizeCursorF)
                elif self.editAction == AppData.DG_N:
                    newBox = (x1, y1+dy, x2, y2)
                    self.staticLabel.setCursor(self.resizeCursorV)
                elif self.editAction == AppData.DG_NE:
                    newBox = (x1, y1+dy, x2+dx, y2)
                    self.staticLabel.setCursor(self.resizeCursorB)
                elif self.editAction == AppData.DG_E:
                    newBox = (x1, y1, x2+dx, y2)
                    self.staticLabel.setCursor(self.resizeCursorH)
                elif self.editAction == AppData.DG_SE:
                    newBox = (x1, y1, x2+dx, y2+dy)
                    self.staticLabel.setCursor(self.resizeCursorF)
                elif self.editAction == AppData.DG_S:
                    newBox = (x1, y1, x2, y2+dy)
                    self.staticLabel.setCursor(self.resizeCursorV)
                elif self.editAction == AppData.DG_SW:
                    newBox = (x1+dx, y1, x2, y2+dy)
                    self.staticLabel.setCursor(self.resizeCursorB)
                elif self.editAction == AppData.DG_W:
                    newBox = (x1+dx, y1, x2, y2)
                    self.staticLabel.setCursor(self.resizeCursorH)
                elif self.editAction == AppData.PAN:
                    newBox = (x1+dx, y1+dy, x2+dx, y2+dy)
                    newPoint = (px + dx, py + dy)
                    self.staticLabel.setCursor(self.midpanCursor)

                b.static = newBox
                b.point = newPoint

        self.bigMLastPos = self.bigMPos

    def editMouseRelease(self):
        """Called when the application is in edit mode and the mouse is released
        on the big label."""
        self.editAction = AppData.NO_ACTION

    def newBugIdEntered(self, bid):
        if self.currentSelectionBox is not None:
            self.currentSelectionBox.name = bid
        elif self.selectedEditBox != -1:
            self.placedBoxes[self.selectedEditBox].name = bid

    def setCurrentSelectionBox(self, i=-1):
        if self.removedBug != -1:
            del self.placedBoxes[self.removedBug]
            self.placedBoxes.insert(self.removedBug, self.currentSelectionBox)

        if i != -1:
            self.currentSelectionBox = self.placedBoxes[i]
            self.controlPanel.setCurrentBugId(self.placedBoxes[i].name)
            self.selectedEditBox = None
        else:
            self.currentSelectionBox = None

        self.removedBug = i

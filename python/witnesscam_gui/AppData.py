from PySide import QtCore, QtGui
import cv2
import numpy as np
import os.path
import sys

from Util import *
from Pt import *

class AppData:
    """Main logic controler for the digitization gui"""

    # States/Phases the application can be in
    LOAD_FILE, SELECT_POLYGON, EDIT_MODE, SCANNING_MODE = range(4)

    # Types of editing actions for boxes
    NO_ACTION, DG_NW, DG_N, DG_NE, DG_E, DG_SE, DG_S, DG_SW, DG_W, PAN = range(10)

    # Number of stable frames to wait before performing certain actions
    ACTION_DELAY = 15

    def __init__(self):
        """Initializes a bunch of member variables for use in later functions"""

        # Labels for displaying images
        self.cameraLabel = None
        self.staticLabel = None

        # Whether the camera has been turned on yet
        self.camOn = False

        # Mouse position (current and last) on the big label
        self.bigMPos = (0,0)
        self.bigMLastPos = (0,0)

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

        # Variables used in keeping track of the placed boxes
        self.currentSelectionBox = None
        self.placedBoxes = []
        self.stableBoxRun = 0
        self.stableBox = None

        # Variables used for editing the boxes
        self.selectedEditBox = None
        self.editAction = AppData.NO_ACTION

        # Mouse cursors used when editing boxes
        self.resizeCursorH = QtGui.QCursor(QtCore.Qt.SizeHorCursor)
        self.resizeCursorV = QtGui.QCursor(QtCore.Qt.SizeVerCursor)
        self.resizeCursorB = QtGui.QCursor(QtCore.Qt.SizeBDiagCursor)
        self.resizeCursorF = QtGui.QCursor(QtCore.Qt.SizeFDiagCursor)
        self.prepanCursor = QtGui.QCursor(QtCore.Qt.OpenHandCursor)
        self.midpanCursor = QtGui.QCursor(QtCore.Qt.ClosedHandCursor)
        self.selectCursor = QtGui.QCursor(QtCore.Qt.CrossCursor)
        self.normalCursor = QtGui.QCursor(QtCore.Qt.ArrowCursor)

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

    def setTrayScan(self, fname):
        """Load the tray scan image and activate the camera.

        Keyword Arguments:
        fname -- the string filepath of the tray scan image"""

        # Load the image
        self.trayPath = fname
        self.trayImage = cv2.imread(self.trayPath, cv2.IMREAD_COLOR)

        # Downscale the image
        height = self.trayImage.shape[0]
        self.trayImage = cv2.pyrDown(self.trayImage)
        self.trayImageScale = float(self.trayImage.shape[0])/height

        # Display the image
        self.staticLabel.setImage(self.trayImage)

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
        (cameraFrame, staticFrame) = self.amendFrame(self.cameraImage, self.trayImage)

        # Display the modified frame to the user
        self.cameraLabel.setImage(cameraFrame)
        self.staticLabel.setImage(staticFrame)

    def setMousepos(self, x, y):
        """Update the current mouse position"""

        self.bigMPos = (x,y)

    def amendFrame(self, cameraFrame, staticFrame):
        """Takes the raw (resized) camera frame, and the plain tray image and
        modifies it for display to the user, as well as updating the internal
        state of the program.

        Keywords Arguments:
        cameraFrame -- image from camera as numpy array
        staticFrame -- loaded tray scan image"""

        cameraFrame = np.copy(cameraFrame)
        staticFrame = np.copy(staticFrame)

        (mx, my) = self.bigMPos

        if self.phase == AppData.SELECT_POLYGON:
            # Draw the cursor on the image
            cv2.line(cameraFrame, (mx-10, my), (mx+10, my), (255,0,0), 1)
            cv2.line(cameraFrame, (mx, my-10), (mx, my+10), (255,0,0), 1)

            # Draw the circles for the placed points
            for p in self.polyPoints:
                cv2.circle(cameraFrame, (p.x, p.y), 5, (0,255,0))

        elif self.phase == AppData.SCANNING_MODE:

            # Check if an insect has been moved from/to the tray, and get its
            # position in the camera frame
            (cameraFrame, centroid) = self.getFrameDifferenceCentroid(cameraFrame)
            if centroid != None:

                # If an insect has been removed, find the corresponding insect
                # in the tray image, and mark it
                (trayHeight, trayWidth, _) = self.trayImage.shape
                (u,v) = poly2square(self.polygon_model, trayWidth, trayHeight, centroid).t()
                cv2.line(staticFrame, (u-10, v), (u+10, v), (0,0,255), 5)
                cv2.line(staticFrame, (u, v-10), (u, v+10), (0,0,255), 5)

            # Draw all the boxes that have already been placed
            self.drawPlacedBoxes(staticFrame)

            # Draw the currently selected box a different colour
            if self.currentSelectionBox != None:
                cv2.rectangle(staticFrame, self.currentSelectionBox[0][0:2], self.currentSelectionBox[0][2:4], (0, 0, 255), 2)

            # Once the camera view has been stable for a while, try to find box
            if self.stableRun >= AppData.ACTION_DELAY:
                (cameraFrame, staticFrame) = self.findCorrectBox(centroid, cameraFrame, staticFrame)

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

        elif self.phase == AppData.EDIT_MODE:

            # When editing, draw the boxes
            self.drawPlacedBoxes(staticFrame)

        return (cameraFrame, staticFrame)

    def drawPlacedBoxes(self, image, regular=(0,255,0), selected=(255,0,0)):
        """Given an input image, draw all of the generated boxes on the image.
        Optional colour paramaters can also be supplied.

        Keyword Arguments:
        image -- the numpy array image that the boxes will be drawn on
        regular -- the colour of the boxes
        selected -- the colour of the selected box
        """

        for i in range(len(self.placedBoxes)):
            ((b, _), _) = self.placedBoxes[i]
            if i == self.selectedEditBox:
                cv2.rectangle(image, b[0:2], b[2:4], selected, 2)
            else:
                cv2.rectangle(image, b[0:2], b[2:4], regular, 2)


    def findCorrectBox(self, live_pt, live_frame, static_frame):
        """Finds the correct place to create a box once an insect has been
        removed from the draw, or selects an exsisting box.

        Keyword Arguments:
        live_pt -- a point on the live frame representing the location of the
            insect
        live_frame -- grayscale difference map of the current camera frame
        static_frame -- the static tray image"""

        if live_pt != None:
            r = self.trayImageScale

            # Generate a box on the camera image that contains the live point
            (static_box, live_box) = self.floodFillBox(live_pt, live_frame)

            if static_box != None:

                # Determine whether this box is stable (not jumping around and
                # wildly changing)
                if self.stableBox == None:
                    # If no stable box has been set, set one
                    self.stableBox = (static_box, live_box)
                else:
                    # Compare the new box to the stable one
                    ((x1,y1,x2,y2), _) = self.stableBox
                    (x3,y3,x4,y4) = static_box
                    w = x2-x1
                    h = y2-y1
                    eps = 0.05
                    if (abs(x3-x1) < w*eps and abs(y3-y1) < h*eps and abs(x4-x2) < w*eps and abs(y4-y2) < h*eps):
                        # if the new box is close enough to the stable one,
                        # keep it
                        a = 0.9
                        self.stableBoxRun += 1
                        self.stableBox = ((int(a*x3+(1-a)*x1), int(a*y3+(1-a)*y1), int(a*x4+(1-a)*x2), int(a*y4+(1-a)*y2)), live_box)
                    else:
                        # If the new box is too different, the reset the stable
                        # counter and the stable box
                        self.stableBoxRun = 0
                        self.stableBox = (static_box, live_box)

                # If the box has been stable for long enough, accept it
                if self.stableBoxRun >= AppData.ACTION_DELAY:

                    # If the new box significantly overlaps an exsisting box,
                    # use the exsisting box instead
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

        return (live_frame, static_frame)

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
        frame[frame > 12] = 1

        # Find countours in image
        conts, hir = cv2.findContours(frame, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        staticContour = []

        # Find contour that encases the point
        for i in range(len(conts)):
            if cv2.pointPolygonTest(conts[i], p.t(), True) >= 0:
                (trayHeight, trayWidth, _) = self.trayImage.shape
                (sx1, sy1, sx2, sy2) = (trayWidth,trayHeight,0,0)
                (lx1, ly1, lx2, ly2) = (trayWidth,trayHeight,0,0)

                # Generate the box that encases the contour in both the live and
                # static image
                for q in conts[i]:
                    (lx,ly) = q[0]
                    (sx,sy) = poly2square(self.polygon_model, trayWidth, trayHeight, Pt(q[0,0],q[0,1])).t()
                    sx1 = min(sx1,sx)
                    sy1 = min(sy1,sy)
                    sx2 = max(sx2,sx)
                    sy2 = max(sy2,sy)
                    lx1 = min(lx1,lx)
                    ly1 = min(ly1,ly)
                    lx2 = max(lx2,lx)
                    ly2 = max(ly2,ly)
                    staticContour.append((sx,sy))
                return ((sx1, sy1, sx2, sy2), (lx1, ly1, lx2, ly2))

        return (None, None)

    def gotTrayArea(self):
        """Called when the user has selected the four points that represent
        the corners of the insect tray in the camera view."""

        # Save the current view of the camera
        self.camBackground = np.copy(self.cameraImage)

        # Change phase to edit mode
        self.phase = AppData.EDIT_MODE

        # Swap the labels to place the insect tray image in the bigger label
        tmp = self.cameraLabel
        self.cameraLabel = self.staticLabel
        self.staticLabel = tmp

        # Get the axis aligned bounding box for the tray area selection
        (minx, miny, maxx, maxy) = (1000, 1000, 0, 0)
        for p in self.polyPoints:
            minx = p.x if p.x < minx else minx
            miny = p.y if p.y < miny else miny
            maxx = p.x if p.x > maxx else maxx
            maxy = p.y if p.y > maxy else maxy

        self.trayBoundingBox = [Pt(minx,miny), Pt(maxx, maxy)]
        self.polygon_model = buildPolygonSquareModel(self.polyPoints)

        self.controlPanel.btnStartScanning.setEnabled(True)

    def getFrameDifferenceCentroid(self, camera_frame):
        """Given the difference between teh current camera frame and the saved
        background image of the camera, find the point that represents the
        center of the difference.

        Keyword Arguments:
        camera_frame -- the current camera frame"""

        # Setup a mask to block off certain parts of the difference image
        (h,w,d) = camera_frame.shape
        polygon_mask = np.zeros((h,w,d), np.uint8)

        poly = None
        polyArea = -1
        poly = np.array([[p.x, p.y] for p in self.polyPoints],
                dtype=np.int32)

        # Block off the area outside the tray
        polyArea = quadrilateralArea([(p.x,p.y) for p in self.polyPoints])
        cv2.drawContours(polygon_mask, [poly], 0, (1,1,1), -1)

        # Block off the box containing the removed insect
        if self.currentSelectionBox != None:
            b = self.currentSelectionBox[1]
            q0 = (int(b[0]), int(b[1]))
            q1 = (int(b[2]), int(b[1]))
            q2 = (int(b[2]), int(b[3]))
            q3 = (int(b[0]), int(b[3]))
            poly = np.array([q0, q1, q2, q3], dtype=np.int32)
            polyArea = polyArea - quadrilateralArea([q0, q1, q2, q3])
            cv2.drawContours(polygon_mask, [poly], 0, (0,0,0), -1)

        # Convert color image for current frame to grayscale image difference
        # and apply the mask to block off certain areas
        frame = np.absolute(np.subtract(self.camBackground.astype(int),
                camera_frame.astype(int))).astype(np.uint8)
        frame = np.add.reduce(np.square(np.multiply(
                np.float32(frame), polygon_mask)), 2)
        frame = np.sqrt(frame)
        frame = cv2.GaussianBlur(frame, (5,5), 0)
        frame[frame < 12] = 0
        tframe = np.copy(frame)

        # Use the processed image difference frame to find the center of the
        # difference
        medpos = None
        if self.activeFrameLastDiff != None:

            # Compute the total difference of this frame, and the change from
            # last frame to this one
            a = 1.0
            self.activeFrameCurrentDiff = np.sum(tframe)/polyArea
            delta = self.activeFrameCurrentDiff - self.activeFrameLastDiff
            self.activeFrameSmoothDelta = (1-a)*self.activeFrameSmoothDelta + a*delta
            self.activeFrameLastDiff = self.activeFrameCurrentDiff

            # If the cchange in difference from last frame to this one is small
            # consider it stable and increment the stable counter
            if abs(self.activeFrameSmoothDelta) < 0.1:
                self.stableRun += 1
            else:
                self.stableRun = 0

            # If the frame has been stable for long enough, then
            if self.stableRun > AppData.ACTION_DELAY:
                medpos = findWeightedMedianPoint2D(tframe, self.trayBoundingBox)

            # Overall frame count
            if self.removedBug != -1:
                self.frameCount += 1

        else:
            self.activeFrameLastDiff = np.sum(tframe)/polyArea
            self.activeFrameSmoothDelta = 0

        frame = np.uint8(frame)
        return (frame, medpos)

    def refreshCamera(self):
        """Save the current camera view as the background, and reset some
        counters"""
        self.camBackground = np.copy(self.cameraImage)
        self.stableRun = 0

    def refreshCameraButton(self):
        """When the refresh camer button is pressed"""
        self.refreshCamera()
        self.removedBug = -1
        self.currentSelectionBox = None

    def toggleScanningMode(self):
        """Called when the Start/Stop Barcode Scanning button is pressed"""
        if self.phase == AppData.SCANNING_MODE:
            self.phase = AppData.EDIT_MODE
        elif self.phase == AppData.EDIT_MODE:
            self.phase = AppData.SCANNING_MODE
            self.refreshCameraButton()
            self.currentSelectionBox = None
            self.selectedEditBox = None

        self.controlPanel.scanningModeToggled(self.phase)

    def exportToCSV(self):
        """Called when the Export to CSV button is pressed"""
        fname, _ = QtGui.QFileDialog.getSaveFileName()
        print(fname)

        f = open(fname, 'w')
        for ((b, _), code) in self.placedBoxes:
            f.write(code + ", " + str(b) + '\n')

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

        elif self.phase == AppData.EDIT_MODE:
            self.editMousePress(ev)

    def bigLabelMouseMove(self, ev, scale):
        """When the mouse is clicked on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object
        scale -- scale constant between the size of the label and the size
            of the big label"""
        self.setMousepos(int(ev.pos().x()/scale),
                int(ev.pos().y()/scale))

        if self.phase == AppData.EDIT_MODE:
            self.editMouseMove()

    def bigLabelMouseRelease(self, ev):
        """When the mouse is clicked on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object"""
        if self.phase == AppData.EDIT_MODE:
            self.editMouseRelease()

    def editMousePress(self, ev):
        """Called when the application is in edit mode and the mouse is clicked
        on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object"""

        (mx, my) = self.bigMPos
        c = 15

        if self.selectedEditBox != None:
            # If a box is selected, check for clicking on an editable point
            # (e. corners for resizing, center for panning)
            p = self.bigMPos
            (((x1,y1,x2,y2), _), _) = self.placedBoxes[self.selectedEditBox]
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
                if pointInBox(p, (x1,y1,x2,y2)):
                    del self.placedBoxes[self.selectedEditBox]
                    self.selectedEditBox = None

                    return

        # If a box is not selected, check for clicking on a box to
        # to select it
        clickedOn = False
        for i in range(len(self.placedBoxes)):
            (((x1,y1,x2,y2), _), _) = self.placedBoxes[i]
            if pointInBox((mx, my), (x1-c,y1-c,x2+c,y2+c)):
                clickedOn = True
                self.selectedEditBox = i

        # Check for deselect of box
        if not clickedOn:
            self.selectedEditBox = None


    def editMouseMove(self):
        """Called when the application is in edit mode and the mouse is moved
        on the big label."""

        p = self.bigMPos

        # Show box select cursor if hovered over box
        self.staticLabel.setCursor(self.normalCursor)
        for ((b, _), _) in self.placedBoxes:
            if pointInBox(p, b):
                self.staticLabel.setCursor(self.selectCursor)

        # If box is selected, show various cursors for editing functions
        if self.selectedEditBox != None:
            if self.editAction == AppData.NO_ACTION:
                c = 15
                (((x1,y1,x2,y2), _), _) = self.placedBoxes[self.selectedEditBox]
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
                (dx, dy) = (self.bigMPos[0] - self.bigMLastPos[0], self.bigMPos[1] - self.bigMLastPos[1])
                (((x1,y1,x2,y2), a), b) = self.placedBoxes[self.selectedEditBox]
                newBox = (x1,y1,x2,y2)
                if self.editAction == AppData.DG_NW:
                    newBox = (x1+dx,y1+dy,x2,y2)
                    self.staticLabel.setCursor(self.resizeCursorF)
                elif self.editAction == AppData.DG_N:
                    newBox = (x1,y1+dy,x2,y2)
                    self.staticLabel.setCursor(self.resizeCursorV)
                elif self.editAction == AppData.DG_NE:
                    newBox = (x1,y1+dy,x2+dx,y2)
                    self.staticLabel.setCursor(self.resizeCursorB)
                elif self.editAction == AppData.DG_E:
                    newBox = (x1,y1,x2+dx,y2)
                    self.staticLabel.setCursor(self.resizeCursorH)
                elif self.editAction == AppData.DG_SE:
                    newBox = (x1,y1,x2+dx,y2+dy)
                    self.staticLabel.setCursor(self.resizeCursorF)
                elif self.editAction == AppData.DG_S:
                    newBox = (x1,y1,x2,y2+dy)
                    self.staticLabel.setCursor(self.resizeCursorV)
                elif self.editAction == AppData.DG_SW:
                    newBox = (x1+dx,y1,x2,y2+dy)
                    self.staticLabel.setCursor(self.resizeCursorB)
                elif self.editAction == AppData.DG_W:
                    newBox = (x1+dx,y1,x2,y2)
                    self.staticLabel.setCursor(self.resizeCursorH)
                elif self.editAction == AppData.PAN:
                    newBox = (x1+dx,y1+dy,x2+dx,y2+dy)
                    self.staticLabel.setCursor(self.midpanCursor)

                self.placedBoxes[self.selectedEditBox] = ((newBox, a), b)


        self.bigMLastPos = self.bigMPos


    def editMouseRelease(self):
        """Called when the application is in edit mode and the mouse is released
        on the big label."""
        self.editAction = AppData.NO_ACTION

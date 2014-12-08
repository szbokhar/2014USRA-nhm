# Other gui widgets used in the main window
#
# Technology for Nature. British Natural History Museum insect specimen
# digitization project.
#
# Copyright (C) 2014    Syed Zahir Bokhari, Prof. Michael Terry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

from PySide import QtCore, QtGui
from os import listdir
from mimetypes import guess_type
import cv2
import numpy as np

from AppData import *
from Util import *
from Pt import *
import Constants as C


class BarcodeEntry(QtGui.QFrame):
    """A QtWidget that holds takes the barcode entry"""

    # Signals emmited by the control panel

    def __init__(self, data, parent=None):
        super(BarcodeEntry, self).__init__(parent)
        self.data = data
        self.initUI()

    def initUI(self):
        # Setup the panel and layout
        panelLayout = QtGui.QHBoxLayout()
        self.setLayout(panelLayout)

        # Create the Textbox label
        self.lblTextLabel = QtGui.QLabel()
        self.lblTextLabel.setText(C.BARCODE_LABEL_TEXT)

        # Create the Barcode label
        self.txtBarcode = QtGui.QLineEdit()
        self.txtBarcode.setText('')
        self.txtBarcode.setMinimumWidth(100)
        self.txtBarcode.setEnabled(False)

        # Place all buttons and labels on the panel
        panelLayout.addWidget(self.lblTextLabel)
        panelLayout.addWidget(self.txtBarcode)

        # Connect slots for the buttion actions
        self.txtBarcode.textEdited.connect(self.data.newBugIdEntered)

    def setCurrentBugId(self, string):
        self.txtBarcode.setText(string)
        self.txtBarcode.selectAll()
        self.txtBarcode.setFocus(QtCore.Qt.OtherFocusReason)


class FileBrowser(QtGui.QFrame):
    """A QWidget that build the file browser"""

    sigFileSelected = QtCore.Signal(str)

    def __init__(self, parent=None):
        """Object constructor"""

        super(FileBrowser, self).__init__(parent)
        self.initUI()

        self.currentItem = None
        self.currentPath = None
        self.imageFilename = None

    def initUI(self):
        """Initialize widget components"""

        panelLayout = QtGui.QVBoxLayout()
        self.setLayout(panelLayout)

        # Setup the bottom panel to contain the prev/next buttons
        bottomPanel = QtGui.QFrame(self)
        bottomLayout = QtGui.QHBoxLayout()
        bottomPanel.setLayout(bottomLayout)

        # Setup the tree widget to contain the files
        self.treeFileBrowser = QtGui.QTreeWidget(self)
        self.treeFileBrowser.setHeaderItem(
            QtGui.QTreeWidgetItem(C.FILEBROWSER_COLUMNS))
        self.btnNext = QtGui.QPushButton(C.FILEBROWSER_NEXT_TEXT)
        self.btnNext.setEnabled(False)
        self.btnPrevious = QtGui.QPushButton(C.FILEBROWSER_PREV_TEXT)
        self.btnPrevious.setEnabled(False)

        # Put components into the layouts
        bottomLayout.addStretch(1)
        bottomLayout.addWidget(self.btnPrevious)
        bottomLayout.addStretch(1)
        bottomLayout.addWidget(self.btnNext)
        bottomLayout.addStretch(1)
        panelLayout.addWidget(self.treeFileBrowser)
        panelLayout.addWidget(bottomPanel)

        # Connect signals to slots
        self.treeFileBrowser.itemDoubleClicked.connect(self.doubleClicked)
        self.btnNext.clicked.connect(self.nextClicked)
        self.btnPrevious.clicked.connect(self.previousClicked)

    def refresh(self, current_path, image_filename):
        """Populate the files displayed inside the file browser.

        Keyword Arguments:
        current_path -- path of the directory to display in the file browser
        image_filename -- filename of the currently loaded image"""

        self.current_path = current_path
        self.image_filename = image_filename

        # Build list of image files in the directory
        images = [(f, guess_type(f))
                  for f in listdir(current_path) if os.path.isfile(f)]
        images = [f
                  for (f, (t, e)) in images
                  if t is not None and len(t) > 5 and t[0:5] == 'image']

        # Clear contents of tree widget
        model = self.treeFileBrowser.model()
        for _ in range(model.rowCount()):
            model.removeRow(0)

        # Populate tree widget with new contents
        for f in images:
            csvfile = current_path+"/"+changeExtension(f, 'csv')
            count = 'n/a'

            if os.path.isfile(csvfile):
                count = 0
                with open(csvfile) as data:
                    reader = csv.reader(data)
                    for i, l in enumerate(reader):
                        pass
                    count = i
            count = str(count)

            item = QtGui.QTreeWidgetItem([f, count])
            self.treeFileBrowser.addTopLevelItem(item)

            # Highlight the currently loaded image
            if f == image_filename:
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
                item.setFont(1, font)
                self.treeFileBrowser.setItemSelected(item, True)
                self.currentItem = item

        # Autosize the columns
        self.treeFileBrowser.resizeColumnToContents(0)
        self.treeFileBrowser.resizeColumnToContents(1)

        # Enables next and prev buttons if next and prev exist
        if self.treeFileBrowser.itemBelow(self.currentItem) is None:
            self.btnNext.setEnabled(False)
        else:
            self.btnNext.setEnabled(True)
        if self.treeFileBrowser.itemAbove(self.currentItem) is None:
            self.btnPrevious.setEnabled(False)
        else:
            self.btnPrevious.setEnabled(True)

    @QtCore.Slot()
    def doubleClicked(self, i, c):
        """Called when the user double clicks an entry in the file browser"""

        if self.currentItem is not i:
            self.sigFileSelected.emit("%s/%s" % (self.currentPath, i.text(0)))

    @QtCore.Slot()
    def nextClicked(self):
        """Called when the user clicks the next button under the filebrowser"""

        i = self.treeFileBrowser.itemBelow(self.currentItem)
        self.sigFileSelected.emit("%s/%s" % (self.currentPath, i.text(0)))

    @QtCore.Slot()
    def previousClicked(self):
        """Called when the user clicks the prev button under the filebrowser"""

        i = self.treeFileBrowser.itemAbove(self.currentItem)
        self.sigFileSelected.emit("%s/%s" % (self.currentPath, i.text(0)))


class BigLabel(QtGui.QLabel):
    """The large sized label with convienence function for displaying images
    in numpy arrays, as well as signals for mouse events"""

    originalSize = (640, 360)
    resizeScale = (1.0, 1.0)

    sigMousePress = QtCore.Signal(QtGui.QMouseEvent, float)
    sigMouseMove = QtCore.Signal(QtGui.QMouseEvent, float)
    sigMouseRelease = QtCore.Signal(QtGui.QMouseEvent, float)
    sigScroll = QtCore.Signal(QtGui.QWheelEvent, float)

    def __init__(self, data, parent=None):
        """Object constructor

        Keyword Arguments
        data -- AppData instance"""

        super(BigLabel, self).__init__(parent)
        self.data = data
        self.initUI()
        self.setMouseTracking(True)
        self.imageScaleRatio = 1
        # self.setPixmap(QtGui.QPixmap(self.originalSize[0],
        #                              self.originalSize[1]))
        self.generateInitialImage()

    def initUI(self):
        self.setAlignment(QtCore.Qt.AlignTop)

    def setImage(self, cv_image):
        """Displays an image in the label.

        Keyword Arguments:
        cv_image -- OpenCV2 image, represented as a numpy array"""

        # Handle grayscale and color images
        if cv_image.ndim == 2:
            cv_image = cv2.cvtColor(cv_image, cv2.cv.CV_GRAY2BGRA)
        else:
            cv_image = cv2.cvtColor(cv_image, cv2.cv.CV_BGR2BGRA)

        # Scale image to fit in label
        originalSize = (cv_image.shape[1], cv_image.shape[0])
        (w, h, rat) = computeImageScaleFactor(
            originalSize, self.getCurrentSize())
        self.imageScaleRatio = rat

        # Convert opencv image to pyside Pixmap for display in label
        cv_image = cv2.resize(cv_image, (w, h))
        img = QtGui.QImage(cv_image, cv_image.shape[1], cv_image.shape[0],
                           cv_image.strides[0], QtGui.QImage.Format_ARGB32)
        self.setPixmap(QtGui.QPixmap.fromImage(img))

    def mousePressEvent(self, ev):
        """Invoked when the user presses the mouse on the label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent"""

        self.sigMousePress.emit(ev, self.imageScaleRatio)

    def mouseMoveEvent(self, ev):
        """Invoked when the user moved the mouse on the label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent"""

        self.sigMouseMove.emit(ev, self.imageScaleRatio)

    def mouseReleaseEvent(self, ev):
        """Invoked when the user releases the mouse on the label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent"""

        self.sigMouseRelease.emit(ev, self.imageScaleRatio)

    def wheelEvent(self, ev):
        """Invoked when the user scrolls the mouse on the label.

        Keyword Arguments:
        ev -- PySide.QtGui.QWheelEvent"""

        self.sigScroll.emit(ev, self.imageScaleRatio)

    def newResizeScale(self, scale):
        """Notifies the label that it should resize.

        Keyword Arguments:
        scale -- float scale of the original size"""

        self.resizeScale = scale
        (sx, sy) = scale
        (w, h) = self.originalSize
        self.resize(int(w*sx), int(h*sy))

    def getCurrentSize(self):
        """Get the current size of the label contents"""

        (sx, sy) = self.resizeScale
        (w, h) = self.originalSize
        return (w*sx, h*sy)

    def generateInitialImage(self):
        """Geneate the image to be displayed when the label is created. For the
        big label, this is a dashed border with a message to drag and drop a
        file to load it."""

        (w, h) = self.originalSize
        img = np.zeros((h, w, 4), np.uint8)

        # Write the text on the label
        b = 4*h/10
        for text in C.INITIAL_BIGLABEL_TEXT:
            ((tw, th), _) = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX,
                                            0.8, 1)
            cv2.putText(img, text, ((w-tw)/2, b), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 0, 0, 255), 2)
            b += th + 10
        cv2.GaussianBlur(img, (3, 3), 0.5, img)

        # Draw the dashed line along the border
        s = w/(2*20+1)
        for i in range(0, w+100, s)[0::2]:
            cv2.rectangle(img, (i, 0), (i+s, 2), (0, 0, 0, 128), -1)
            cv2.rectangle(img, (i, h-1), (i+s, h-3), (0, 0, 0, 128), -1)
        s = h/(2*10+1)
        for i in range(0, h+100, s)[0::2]:
            cv2.rectangle(img, (0, i), (2, i+s), (0, 0, 0, 128), -1)
            cv2.rectangle(img, (w-1, i), (w-3, i+s), (0, 0, 0, 128), -1)
        self.setImage(img)


class SmallLabel(QtGui.QLabel):
    """The small sized label with convienence function for displaying images
    in numpy arrays"""

    originalSize = (320, 180)
    resizeScale = (1.0, 1.0)

    def __init__(self, data, parent=None):
        """Constructor for the object.

        Keyword Arguments:
        data -- AppData instance"""

        super(SmallLabel, self).__init__(parent)
        self.data = data
        self.initUI()
        self.imageScaleRatio = 1
        # self.setPixmap(QtGui.QPixmap(self.originalSize[0],
        #                              self.originalSize[1]))
        self.generateInitialImage()

    def initUI(self):
        self.setAlignment(QtCore.Qt.AlignTop)

    def setImage(self, cv_image):
        """Displays an image in the label.

        Keyword Arguments:
        cv_image -- OpenCV2 image, represented as a numpy array"""

        if cv_image.ndim == 2:
            cv_image = cv2.cvtColor(cv_image, cv2.cv.CV_GRAY2BGRA)
        else:
            cv_image = cv2.cvtColor(cv_image, cv2.cv.CV_BGR2BGRA)
        originalSize = (cv_image.shape[1], cv_image.shape[0])
        (w, h, rat) = computeImageScaleFactor(
            originalSize, self.getCurrentSize())
        self.imageScaleRatio = rat
        cv_image = cv2.resize(cv_image, (w, h))
        img = QtGui.QImage(cv_image, cv_image.shape[1], cv_image.shape[0],
                           cv_image.strides[0], QtGui.QImage.Format_ARGB32)

        self.setPixmap(QtGui.QPixmap.fromImage(img))

    def newResizeScale(self, scale):
        """Notifies the label that it should resize.

        Keyword Arguments:
        scale -- float scale of the original size"""

        self.resizeScale = scale
        (sx, sy) = scale
        (w, h) = self.originalSize
        self.resize(int(w*sx), int(h*sy))

    def getCurrentSize(self):
        """Get the current size of the label contents"""

        (sx, sy) = self.resizeScale
        (w, h) = self.originalSize
        return (w*sx, h*sy)

    def generateInitialImage(self):
        """Geneate the image to be displayed when the label is created. For the
        big label, this is a dashed border with a message to drag and drop a
        file to load it."""

        (w, h) = self.originalSize
        img = np.zeros((h, w, 4), np.uint8)
        img[:, :, :] = [128, 128, 128, 128]
        self.setImage(img)

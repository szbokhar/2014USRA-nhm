# Main pyside window for the application
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
from functools import partial
import csv

from AppData import *
from GUIParts import *
from Util import *


class MainWindow(QtGui.QMainWindow):

    originalSize = (964, 486)
    sigLoadTrayImage = QtCore.Signal(str, str)
    sigUndoAction = QtCore.Signal()
    sigRedoAction = QtCore.Signal()
    sigQuitAction = QtCore.Signal()

    def __init__(self, cv_impl, logger, testdata):
        """Main window constructor.

        Keyword Arguments:
        cv_impl -- Class conforming to the vision implementation interface
        logger -- InteractionLogger instance"""

        super(MainWindow, self).__init__()
        self.logger = logger
        self.testdata = testdata
        self.cvImpl = cv_impl
        cv_impl.setMainWindow(self)
        self.initUI(cv_impl)

        # Initialize cursors that will be used
        self.normalCursor = QtGui.QCursor(QtCore.Qt.ArrowCursor)
        self.dragCursor = QtGui.QCursor(QtCore.Qt.DragLinkCursor)

    def initUI(self, cv_impl):
        """Setup the UI for the window.

        Keyword Arguments:
        cv_impl -- Class conforming to the vision implementation interface"""

        # Setup main content area
        mainWidget = QtGui.QFrame(self)
        interactionWidget = QtGui.QFrame(mainWidget)
        mainContent = QtGui.QHBoxLayout()
        interactionContent = QtGui.QVBoxLayout()

        # Setup Gui Elements
        self.data = AppData(self, cv_impl, self.logger, self.testdata)
        self.controlPanel = BarcodeEntry(self.data)
        self.lblBig = BigLabel(self.data, self.logger)
        self.lblSmall = SmallLabel(self.data)
        self.data.setGuiElements(self.controlPanel, self.lblBig, self.lblSmall)
        self.controlPanel.txtBarcode.installEventFilter(self)
        self.fileBrowser = FileBrowser()

        self.lblHint = QtGui.QLabel('')
        self.lblHint.setAlignment(QtCore.Qt.AlignHCenter)
        self.lblHint.setWordWrap(True)
        self.lblHint.setFixedHeight(50)

        self.topPanel = QtGui.QFrame()
        self.topContent = QtGui.QHBoxLayout()
        self.bottomPanel = QtGui.QFrame()
        self.bottomContent = QtGui.QHBoxLayout()

        # Add GUI elements to window
        mainWidget.setLayout(mainContent)
        interactionWidget.setLayout(interactionContent)
        self.bottomPanel.setLayout(self.bottomContent)
        self.topPanel.setLayout(self.topContent)
        self.setCentralWidget(mainWidget)

        interactionContent.addWidget(self.topPanel)
        interactionContent.addWidget(self.lblHint)
        interactionContent.addWidget(self.bottomPanel)
        self.topContent.addStretch(1)
        self.topContent.addWidget(self.lblBig)
        self.topContent.addStretch(1)
        self.bottomContent.addWidget(self.lblSmall)
        self.bottomContent.addWidget(self.controlPanel)
        mainContent.addWidget(interactionWidget)
        mainContent.addWidget(self.fileBrowser)

        # Setup menu bar
        self.buildMenubar(cv_impl)

        # Wire up signals and slots
        self.sigLoadTrayImage.connect(self.data.loadTrayImage)
        self.sigQuitAction.connect(self.data.quit)
        self.sigUndoAction.connect(self.data.undoAction)
        self.sigRedoAction.connect(self.data.redoAction)

        cv_impl.sigScanningModeOn.connect(
            self.controlPanel.txtBarcode.setEnabled)
        cv_impl.sigScanningModeOn.connect(self.actResyncCamera.setEnabled)
        cv_impl.sigRemovedBug.connect(self.data.onBugRemoved)
        cv_impl.sigShowHint.connect(self.lblHint.setText)

        self.data.sigSelectedBox.connect(cv_impl.onEditBoxSelected)
        self.data.sigDeletedBox.connect(cv_impl.onEditBoxDeleted)
        self.data.sigShowHint.connect(self.lblHint.setText)

        self.fileBrowser.sigFileSelected.connect(self.selectTrayImage)

        self.lblBig.sigMousePress.connect(self.data.mousePress)
        self.lblBig.sigMouseMove.connect(self.data.mouseMove)
        self.lblBig.sigMouseRelease.connect(self.data.mouseRelease)
        self.lblBig.sigScroll.connect(self.data.mouseScroll)

        # Finish up window
        self.setAcceptDrops(True)
        self.statusBar().showMessage(C.WINDOW_STATUS_READY)
        self.setGeometry(100, 100, self.originalSize[0], self.originalSize[1])
        self.setWindowTitle(C.WINDOW_TITLE)
        self.show()
        self.raise_()

    def buildMenubar(self, cv_impl):
        """Build the application menus.

        cv_impl -- vision implementation"""

        menubar = QtGui.QMenuBar()

        # File menu
        fileMenu = QtGui.QMenu(menubar)
        fileMenu.setTitle(C.MENU_TEXT[0][0])
        fileMenu.addAction(
            C.MENU_TEXT[0][1][0],
            self.selectTrayImage).setShortcut(QtGui.QKeySequence.Open)

        # Recent files submenu
        recentMenu = fileMenu.addMenu(C.MENU_TEXT[0][1][1])
        if os.path.isfile(C.FILENAME_RECENT_LOADS):
            with open(C.FILENAME_RECENT_LOADS, 'r') as recent_file:
                for path in recent_file.readlines():
                    fname = os.path.split(path)[1]
                    recentMenu.addAction(
                        fname, partial(self.selectTrayImage, path[0:-1]))
        fileMenu.addSeparator()

        # Save and Quit
        fileMenu.addAction(
            C.MENU_TEXT[0][1][2],
            self.data.exportToCSV).setShortcut(QtGui.QKeySequence.Save)
        fileMenu.addAction(
            C.MENU_TEXT[0][1][3],
            self.sigQuitAction.emit).setShortcut(QtGui.QKeySequence.Quit)

        # Edit menu
        editMenu = QtGui.QMenu(menubar)
        editMenu.setTitle(C.MENU_TEXT[1][0])
        editMenu.addAction(
            C.MENU_TEXT[1][1][0],
            self.sigUndoAction.emit).setShortcut(QtGui.QKeySequence.Undo)
        editMenu.addAction(
            C.MENU_TEXT[1][1][1],
            self.sigRedoAction.emit).setShortcut(QtGui.QKeySequence.Redo)

        # Image menu
        imageMenu = QtGui.QMenu(menubar)
        imageMenu.setTitle(C.MENU_TEXT[2][0])
        imageMenu.addAction(C.MENU_TEXT[2][1][0], cv_impl.resetTrayArea)
        self.actResyncCamera = imageMenu.addAction(
            C.MENU_TEXT[2][1][1], cv_impl.refreshCamera)
        self.actResyncCamera.setDisabled(True)

        # Finish set up
        menubar.addMenu(fileMenu)
        menubar.addMenu(editMenu)
        menubar.addMenu(imageMenu)
        self.setMenuBar(menubar)

    def resizeEvent(self, ev):
        """Called when the window is resized.

        Keyword Arguments:
        ev -- PySIde.QtGui.QResizeEvent"""

        h = ev.size().height()
        w = ev.size().width()
        self.logger.log('WINDOW resized to (%d, %d)' % (w, h), 1)
        (oldW, oldH) = self.originalSize
        scale = (float(w)/oldW, float(h)/oldH)
        # self.lblBig.newResizeScale(scale)
        # self.lblSmall.newResizeScale(scale)

    def closeEvent(self, event):
        """Called when someone tries to quit the application.

        Keyword Arguments:
        event -- PySide.QtGui.QCloseEvent"""

        self.data.quit()

    @QtCore.Slot()
    def selectTrayImage(self, fname=None):
        """Load the tray image.

        Keyword Arguments:
        fname -- path of the file to load. If not specified then a file load
            dialog is shows to the user"""

        # If no filename provided, show file load dialog
        if fname is None:
            fname, _ = QtGui.QFileDialog.getOpenFileName(
                self, C.OPENDIALOG_TITLE, '.')

        # Extract filename, directory path, and associated csv filename
        if fname != '':
            self.logger.log('LOAD by File menu', 1)
            (self.currentPath, self.imageFilename) = os.path.split(fname)
            csvfile = changeExtension(self.imageFilename, 'csv')
            csvfile = os.path.join(self.currentPath, csvfile)

            # Boradcast that user has loaded a file
            self.sigLoadTrayImage.emit(fname, csvfile)

            # Update recent files data
            recent_files = []
            if os.path.isfile(C.FILENAME_RECENT_LOADS):
                with open(C.FILENAME_RECENT_LOADS, 'r') as recent_file:
                    for line in recent_file.readlines():
                        recent_files.append(line[0:-1])

            recent_files.insert(0, fname)
            recent_files = dedup_list(recent_files)

            with open(C.FILENAME_RECENT_LOADS, 'w') as recent_file:
                for f in recent_files:
                    recent_file.write(f+'\n')

            # Reload file browser
            self.fileBrowser.refresh(self.currentPath, self.imageFilename)

    def dragEnterEvent(self, ev):
        """Called when the user drags something into the window.

        Keyword Arguments:
        ev -- PySide.QtGui.QDragEnterEvent"""

        if ev.mimeData().hasUrls():
            ev.accept()
            self.setCursor(self.dragCursor)

    def dragLeaveEvent(self, ev):
        """Called when the user drags something out of the window.

        Keyword Arguments:
        ev -- PySide.QtGui.QDragLeaveEvent"""

        self.setCursor(self.normalCursor)

    def dropEvent(self, ev):
        """Called when the user drags and drops something into the window.

        Keyword Arguments:
        ev -- PySide.QtGui.QDropEvent"""

        self.setCursor(self.normalCursor)

        # If the mimetype is correct, try to load the image
        if ev.mimeData().hasUrls():
            self.logger.log('LOAD by drag and drop', 1)
            self.selectTrayImage(ev.mimeData().urls()[0].toLocalFile())

    def eventFilter(self, obj, event):
        """Event filter designed to capture undo events directed towards the
        barcode QLineEdit, and redirect it to the entire window.

        Keyword Arguments:
        obj -- PySide.QtCore.QObject
        event -- PySide.QtCore.QEvent"""

        if obj == self.controlPanel.txtBarcode\
                and event.type() == QtCore.QEvent.Type.ShortcutOverride:
            if event.matches(QtGui.QKeySequence.Undo) or\
                    event.matches(QtGui.QKeySequence.Redo):
                self.logger.log('KEY capture undo/redo from txtBarcode', 1)
                return True
        return QtGui.QMainWindow.eventFilter(self, obj, event)

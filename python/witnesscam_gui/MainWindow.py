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

    def __init__(self, cv_impl, logger):
        super(MainWindow, self).__init__()
        self.logger = logger
        cv_impl.setMainWindow(self)
        self.initUI(cv_impl)


    def initUI(self, cv_impl):
        # Setup main content area
        mainWidget = QtGui.QFrame(self)
        interactionWidget = QtGui.QFrame(mainWidget)
        mainContent = QtGui.QHBoxLayout(self)
        interactionContent = QtGui.QVBoxLayout(self)

        # Setup Gui Elements
        self.data = AppData(self, cv_impl, self.logger)
        self.controlPanel = ControlPanel(self.data)
        self.lblBig = BigLabel(self.data)
        self.lblSmall = SmallLabel(self.data)
        self.data.setGuiElements(self.controlPanel, self.lblBig, self.lblSmall)
        self.controlPanel.txtBarcode.installEventFilter(self)
        self.fileBrowser = FileBrowser()

        self.lblHint = QtGui.QLabel('')
        self.lblHint.setAlignment(QtCore.Qt.AlignHCenter)
        self.lblHint.setWordWrap(True)
        self.lblHint.setFixedHeight(50)


        self.topPanel = QtGui.QFrame()
        self.topContent = QtGui.QHBoxLayout(self)
        self.bottomPanel = QtGui.QFrame()
        self.bottomContent = QtGui.QHBoxLayout(self)

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

        self.normalCursor = QtGui.QCursor(QtCore.Qt.ArrowCursor)
        self.dragCursor = QtGui.QCursor(QtCore.Qt.DragLinkCursor)

        # Wire up signals and slots
        self.sigLoadTrayImage.connect(self.data.setTrayScan)
        self.sigQuitAction.connect(self.data.quit)
        self.sigUndoAction.connect(self.data.undoAction)
        self.sigRedoAction.connect(self.data.redoAction)
        cv_impl.sigScanningModeOn.connect(self.controlPanel.txtBarcode.setEnabled)
        cv_impl.sigScanningModeOn.connect(self.actResyncCamera.setEnabled)
        cv_impl.sigRemovedBug.connect(self.data.onBugRemoved)
        cv_impl.sigShowHint.connect(self.lblHint.setText)
        self.data.sigSelectedBox.connect(cv_impl.onEditBoxSelected)
        self.data.sigDeletedBox.connect(cv_impl.onEditBoxDeleted)
        self.data.sigShowHint.connect(self.lblHint.setText)
        self.fileBrowser.sigFileSelected.connect(self.selectTrayImage)

        # Finish up window
        self.setAcceptDrops(True)
        self.statusBar().showMessage("Ready")
        self.setGeometry(0, 0, self.originalSize[0], self.originalSize[1])
        self.setWindowTitle('Insect Segmentation')
        self.show()
        self.raise_()

    def buildMenubar(self, cv_impl):
        menubar = QtGui.QMenuBar()

        fileMenu = QtGui.QMenu(menubar)
        fileMenu.setTitle('File')
        fileMenu.addAction('Open Tray Image', self.selectTrayImage).setShortcut(QtGui.QKeySequence.Open)

        recentMenu = fileMenu.addMenu('Open Recent Tray Scans')
        if os.path.isfile('.recentScans.dat'):
            with open('.recentScans.dat', 'r') as recent_file:
                for path in recent_file.readlines():
                    fname = path.split('/')[-1]
                    recentMenu.addAction(fname, partial(self.selectTrayImage, path[0:-1]))
        fileMenu.addSeparator()
        fileMenu.addAction('Export to CSV', self.data.exportToCSV).setShortcut(QtGui.QKeySequence.Save)
        fileMenu.addAction('Quit', self.sigQuitAction.emit).setShortcut(QtGui.QKeySequence.Quit)

        editMenu = QtGui.QMenu(menubar)
        editMenu.setTitle(' Edit')
        editMenu.addAction('Undo', self.sigUndoAction.emit).setShortcut(QtGui.QKeySequence.Undo)
        editMenu.addAction('Redo', self.sigRedoAction.emit).setShortcut(QtGui.QKeySequence.Redo)

        imageMenu = QtGui.QMenu(menubar)
        imageMenu.setTitle('Image')
        imageMenu.addAction('Retrace tray area', cv_impl.resetTrayArea)
        self.actResyncCamera = imageMenu.addAction('Resync Camera', cv_impl.refreshCamera)
        self.actResyncCamera.setDisabled(True)

        menubar.addMenu(fileMenu)
        menubar.addMenu(editMenu)
        menubar.addMenu(imageMenu)

        self.setMenuBar(menubar)

    def resizeEvent(self, ev):
        h = ev.size().height()
        w = ev.size().width()
        self.logger.log('WINDOW resized to (%d, %d)' % (w,h), 1)
        (oldW, oldH) = self.originalSize
        scale = (float(w)/oldW, float(h)/oldH)
        # self.lblBig.newResizeScale(scale)
        # self.lblSmall.newResizeScale(scale)

    def closeEvent(self, event):
        self.data.quit()

    def selectTrayImage(self, fname=None):
        if fname is None:
            fname, _ = QtGui.QFileDialog.getOpenFileName(
                self, "Open Specimin File", ".")

        if fname != "":
            self.logger.log('LOAD by File menu', 1)
            fpath = fname.split("/")
            self.currentPath = "/".join(fpath[0:-1])
            csvfile = changeExtension(fpath[-1], 'csv')
            csvfile = self.currentPath+"/"+csvfile
            self.imageFilename = fpath[-1]
            self.sigLoadTrayImage.emit(fname, csvfile)

            recent_files = []
            if os.path.isfile('.recentScans.dat'):
                with open('.recentScans.dat', 'r') as recent_file:
                    for line in recent_file.readlines():
                        recent_files.append(line[0:-1])

            recent_files.insert(0, fname)
            recent_files = dedup_list(recent_files)

            with open('.recentScans.dat', 'w') as recent_file:
                for f in recent_files:
                    recent_file.write(f+'\n')

            self.fileBrowser.refresh(self.currentPath, self.imageFilename)


    def dragEnterEvent(self, ev):
        if ev.mimeData().hasUrls():
            ev.accept()
            self.setCursor(self.dragCursor)

    def dragLeaveEvent(self, ev):
        self.setCursor(self.normalCursor)

    def dropEvent(self, ev):
        self.setCursor(self.normalCursor)

        if ev.mimeData().hasUrls():
            self.logger.log('LOAD by drag and drop', 1)
            self.selectTrayImage(ev.mimeData().urls()[0].path())

    def eventFilter(self, obj, event):
        if obj == self.controlPanel.txtBarcode and event.type() == QtCore.QEvent.Type.ShortcutOverride:
            if event.matches(QtGui.QKeySequence.Undo) or\
                    event.matches(QtGui.QKeySequence.Redo):
                self.logger.log('KEY capture undo/redo from txtBarcode', 1)
                return True
        return QtGui.QMainWindow.eventFilter(self, obj, event)

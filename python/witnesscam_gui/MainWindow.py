from PySide import QtCore, QtGui

from AppData import *
from GUIParts import *


class MainWindow(QtGui.QMainWindow):

    originalSize = (800, 600)
    sigLoadTrayImage = QtCore.Signal(str, str)

    def __init__(self, cv_impl, fname=None):
        super(MainWindow, self).__init__()
        self.initUI(cv_impl, fname)


    def initUI(self, cv_impl, fname=None):
        # Setup main content area
        mainWidget = QtGui.QFrame(self)
        mainContent = QtGui.QVBoxLayout(self)

        # Setup Gui Elements
        self.data = AppData(self, cv_impl)
        self.controlPanel = ControlPanel(self.data)
        self.lblBig = BigLabel(self.data)
        self.lblSmall = SmallLabel(self.data)
        self.data.setGuiElements(self.controlPanel, self.lblBig, self.lblSmall)

        self.sidePanel = QtGui.QFrame()
        self.sideContent = QtGui.QHBoxLayout(self)

        # Add GUI elements to window
        mainWidget.setLayout(mainContent)
        self.sidePanel.setLayout(self.sideContent)
        self.setCentralWidget(mainWidget)

        mainContent.addWidget(self.lblBig)
        mainContent.addWidget(self.sidePanel)
        self.sideContent.addWidget(self.lblSmall)
        self.sideContent.addWidget(self.controlPanel)

        # Setup menu bar
        self.buildMenubar()

        self.normalCursor = QtGui.QCursor(QtCore.Qt.ArrowCursor)
        self.dragCursor = QtGui.QCursor(QtCore.Qt.DragLinkCursor)

        # Wire up signals and slots
        self.sigLoadTrayImage.connect(self.data.setTrayScan)
        cv_impl.sigScanningModeOn.connect(self.controlPanel.btnRefreshCamera.setEnabled)
        cv_impl.sigScanningModeOn.connect(self.controlPanel.txtBarcode.setEnabled)
        cv_impl.sigScanningModeOn.connect(self.actResyncCamera.setEnabled)
        cv_impl.sigRemovedBug.connect(self.data.onBugRemoved)

        # Finish up window
        self.setAcceptDrops(True)
        self.statusBar().showMessage("Ready")
        self.setGeometry(0, 0, self.originalSize[0], self.originalSize[1])
        self.setWindowTitle('Insect Segmentation')
        self.show()
        self.raise_()

    def buildMenubar(self):
        menubar = QtGui.QMenuBar()

        fileMenu = QtGui.QMenu(menubar)
        fileMenu.setTitle('File')
        fileMenu.addAction('Load Tray Image', self.selectTrayImage)
        fileMenu.addAction('Export to CSV', self.data.exportToCSV)
        fileMenu.addAction('Exit', self.data.quit)

        imageMenu = QtGui.QMenu(menubar)
        imageMenu.setTitle('Image')
        imageMenu.addAction('Retrace tray area',
            self.data.implementation.resetTrayArea)
        self.actResyncCamera = imageMenu.addAction('Resync Camera', self.data.refreshCameraButton)
        self.actResyncCamera.setDisabled(True)

        menubar.addMenu(fileMenu)
        menubar.addMenu(imageMenu)

        self.setMenuBar(menubar)

    def resizeEvent(self, ev):
        h = ev.size().height()
        w = ev.size().width()
        (oldW, oldH) = self.originalSize
        scale = (float(w)/oldW, float(h)/oldH)
        self.lblBig.newResizeScale(scale)
        self.lblSmall.newResizeScale(scale)

    def closeEvent(self, event):
        self.data.quit()

    def selectTrayImage(self, fname=None):
        if fname is None:
            fname, _ = QtGui.QFileDialog.getOpenFileName(
                self, "Open Specimin File", ".")

        if fname != "":
            fpath = fname.split("/")
            self.currentPath = "/".join(fpath[0:-1])
            csvfile = fpath[-1].split('.')
            csvfile[1] = "csv"
            csvfile = '.'.join(csvfile)
            csvfile = self.currentPath+"/"+csvfile
            self.sigLoadTrayImage.emit(fname, csvfile)

    def dragEnterEvent(self, ev):
        if ev.mimeData().hasUrls():
            ev.accept()
            self.setCursor(self.dragCursor)

    def dragLeaveEvent(self, ev):
        self.setCursor(self.normalCursor)

    def dropEvent(self, ev):
        self.setCursor(self.normalCursor)

        if ev.mimeData().hasUrls():
            self.selectTrayImage(ev.mimeData().urls()[0].path())

from PySide import QtCore, QtGui
from functools import partial

from AppData import *
from GUIParts import *
from Util import *


class MainWindow(QtGui.QMainWindow):

    originalSize = (864, 486)
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
        self.bottomPanel.setLayout(self.bottomContent)
        self.topPanel.setLayout(self.topContent)
        self.setCentralWidget(mainWidget)

        mainContent.addWidget(self.topPanel)
        mainContent.addWidget(self.lblHint)
        mainContent.addWidget(self.bottomPanel)
        self.topContent.addStretch(1)
        self.topContent.addWidget(self.lblBig)
        self.topContent.addStretch(1)
        self.bottomContent.addWidget(self.lblSmall)
        self.bottomContent.addWidget(self.controlPanel)

        # Setup menu bar
        self.buildMenubar(cv_impl)

        self.normalCursor = QtGui.QCursor(QtCore.Qt.ArrowCursor)
        self.dragCursor = QtGui.QCursor(QtCore.Qt.DragLinkCursor)

        # Wire up signals and slots
        self.sigLoadTrayImage.connect(self.data.setTrayScan)
        cv_impl.sigScanningModeOn.connect(self.controlPanel.txtBarcode.setEnabled)
        cv_impl.sigScanningModeOn.connect(self.actResyncCamera.setEnabled)
        cv_impl.sigRemovedBug.connect(self.data.onBugRemoved)
        cv_impl.sigShowHint.connect(self.lblHint.setText)
        self.data.sigSelectedBox.connect(cv_impl.onEditBoxSelected)
        self.data.sigDeletedBox.connect(cv_impl.onEditBoxDeleted)
        self.data.sigShowHint.connect(self.lblHint.setText)

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
        fileMenu.addAction('Open Tray Image', self.selectTrayImage)

        recentMenu = fileMenu.addMenu('Open Recent Tray Scans')
        if os.path.isfile('.recentScans.dat'):
            with open('.recentScans.dat', 'r') as recent_file:
                for path in recent_file.readlines():
                    fname = path.split('/')[-1]
                    recentMenu.addAction(fname, partial(self.selectTrayImage, path[0:-1]))
        fileMenu.addSeparator()
        fileMenu.addAction('Export to CSV', self.data.exportToCSV)
        fileMenu.addAction('Quit', self.data.quit)


        imageMenu = QtGui.QMenu(menubar)
        imageMenu.setTitle('Image')
        imageMenu.addAction('Retrace tray area', cv_impl.resetTrayArea)
        self.actResyncCamera = imageMenu.addAction('Resync Camera', cv_impl.refreshCamera)
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
            print(fname)

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

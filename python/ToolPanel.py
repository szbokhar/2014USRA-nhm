from PySide import QtGui, QtCore
from ImagePanel import *

class ToolPanel(QtGui.QFrame):

    # Signals emitted by the tool pane
    sigOpenFile = QtCore.Signal(str)
    sigClearTemplate = QtCore.Signal()

    def __init__(self, segData, parent=None):
        super(ToolPanel, self).__init__(parent)
        self.currentPath = "."
        self.initUI()
        self.data = segData

    # Setup Tool Pane gui
    def initUI(self):
        # Setup Buttons
        self.btnOpenImage = QtGui.QPushButton("Open Image")
        self.btnOpenImage.setMinimumHeight(50)
        self.btnOpenImage.setStatusTip("Open a new image of specimines")

        self.btnSelectTemplate = QtGui.QPushButton("Select Template")
        self.btnSelectTemplate.setMinimumHeight(50)
        self.btnSelectTemplate.setStatusTip("Make a new template selection")

        self.btnNextBug = QtGui.QPushButton("Select\nBug")
        self.btnNextBug.setMinimumHeight(50)
        self.btnNextBug.setStatusTip("Specify the next bug")

        self.btnCancelBug = QtGui.QPushButton("Cancel\nSelection")
        self.btnCancelBug.setMinimumHeight(50)
        self.btnCancelBug.setStatusTip("Cancel bug selection")
        self.btnCancelBug.setEnabled(False)

        self.btnOther = QtGui.QPushButton("Other")
        self.btnOther.setMinimumHeight(50)

        # Empty Space
        frmEmpty = QtGui.QFrame(self)

        # Add button to panel
        content = QtGui.QGridLayout()
        content.addWidget(self.btnOpenImage, 0, 0, 1, 2)
        content.addWidget(self.btnSelectTemplate, 1, 0, 1, 2)
        content.addWidget(self.btnNextBug, 2, 0)
        content.addWidget(self.btnCancelBug, 2, 1)
        content.addWidget(self.btnOther, 3, 0, 1, 2)
        content.addWidget(frmEmpty, 4, 0, 1, 2)

        # Finish up pane
        self.setLayout(content)
        self.show()

    # Setup slots for signals from the image pane
    def setImagePane(self, img):
        self.btnOpenImage.clicked.connect(self.openFile)
        img.sigNewTemplate.connect(self.newTemplateSelected)
        img.sigBugSelection.connect(self.bugSelection)
        self.btnOther.clicked.connect(self.notifyData)

    # Open a new image file
    def openFile(self):
        fname, _ = QtGui.QFileDialog.getOpenFileName(self, "Open Specimin File",
                        self.currentPath)

        if fname != "":
            fpath = fname.split("/")
            self.currentPath = "/".join(fpath[0:-1])
            self.sigOpenFile.emit(fname)

    # Called when the user has finished selecting a new template
    def newTemplateSelected(self, ev):
        self.btnSelectTemplate.setText("Reset Template")

    def bugSelection(self, result):
        if result == "Confirmed":
            self.btnCancelBug.setEnabled(True)
            self.btnNextBug.setText("Next\nBug")
        elif result == "Cancelled":
            self.btnCancelBug.setEnabled(False)
            self.btnNextBug.setText("Select\nBug")
        elif result == "Start":
            self.btnCancelBug.setEnabled(True)
            self.btnNextBug.setText("Next\nBug")

    def notifyData(self):
        self.data.random()

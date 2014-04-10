import sys
from PySide import QtGui, QtCore

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.initUI()

    def initUI(self):

        mainWidget = QtGui.QFrame(self)
        mainContent = QtGui.QHBoxLayout(self)

        toolPane = ToolPanel()

        imagePane = QtGui.QFrame(self)
        imagePane.setFrameShape(QtGui.QFrame.StyledPanel)

        splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter1.addWidget(toolPane)
        splitter1.addWidget(imagePane)
        splitter1.setSizes([1,500])

        mainContent.addWidget(splitter1)
        mainWidget.setLayout(mainContent)
        self.setCentralWidget(mainWidget)

        self.statusBar().showMessage("Ready")
        self.setGeometry(0, 0, 1024, 720)
        self.setWindowTitle('Insect Segmentation')
        self.show()


class ToolPanel(QtGui.QFrame):

    def __init__(self):
        super(ToolPanel, self).__init__()
        self.initUI()

    def initUI(self):

        btnOpenImage = QtGui.QPushButton("Open Image")
        btnOpenImage.setMinimumHeight(50)
        btnOpenImage.setStatusTip("Open a new image of specimines")

        btnSelectTemplate = QtGui.QPushButton("Select Template")
        btnSelectTemplate.setMinimumHeight(50)
        btnSelectTemplate.setStatusTip("Make a new template selection")

        btnNextBug = QtGui.QPushButton("Next\nBug")
        btnNextBug.setMinimumHeight(50)
        btnNextBug.setStatusTip("Specify the next bug")

        btnCancelBug = QtGui.QPushButton("Cancel\nSelection")
        btnCancelBug.setMinimumHeight(50)
        btnCancelBug.setStatusTip("Cancel bug selection")

        emptyFrame = QtGui.QFrame(self)


        content = QtGui.QGridLayout()
        content.addWidget(btnOpenImage, 0, 0, 1, 2)
        content.addWidget(btnSelectTemplate, 1, 0, 1, 2)
        content.addWidget(btnNextBug, 2, 0)
        content.addWidget(btnCancelBug, 2, 1)
        content.addWidget(emptyFrame, 3, 0, 1, 2)

        self.setLayout(content)
        self.show()

def main():

    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

import sys
from PySide import QtGui, QtCore

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.initUI()

    def initUI(self):

        mainWidget = QtGui.QFrame(self)
        mainContent = QtGui.QHBoxLayout(self)

        imagePane = ImagePanel()

        toolPane = ToolPanel(self, imagePane)

        splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter1.addWidget(toolPane)
        splitter1.addWidget(imagePane)
        splitter1.setSizes([1,500])

        mainContent.addWidget(splitter1)
        mainWidget.setLayout(mainContent)
        self.setCentralWidget(mainWidget)

        self.statusBar().showMessage("Ready")
        self.setGeometry(0, 0, 1024, 720)
        self.setFixedSize(self.size())
        self.setWindowTitle('Insect Segmentation')
        self.show()


class ToolPanel(QtGui.QFrame):

    def __init__(self, window, img):
        super(ToolPanel, self).__init__()
        self.pnlImg = img
        self.currentPath = "."
        self.initUI()

    def initUI(self):

        self.btnOpenImage = QtGui.QPushButton("Open Image")
        self.btnOpenImage.setMinimumHeight(50)
        self.btnOpenImage.setStatusTip("Open a new image of specimines")
        self.btnOpenImage.clicked.connect(self.openFile)

        self.btnSelectTemplate = QtGui.QPushButton("Select Template")
        self.btnSelectTemplate.setMinimumHeight(50)
        self.btnSelectTemplate.setStatusTip("Make a new template selection")
        self.btnSelectTemplate.clicked.connect(self.selectTemplate)

        self.btnNextBug = QtGui.QPushButton("Next\nBug")
        self.btnNextBug.setMinimumHeight(50)
        self.btnNextBug.setStatusTip("Specify the next bug")

        self.btnCancelBug = QtGui.QPushButton("Cancel\nSelection")
        self.btnCancelBug.setMinimumHeight(50)
        self.btnCancelBug.setStatusTip("Cancel bug selection")

        self.pnlImg.newTemplateSignal.connect(self.newTemplateSelected)

        frmEmpty = QtGui.QFrame(self)


        content = QtGui.QGridLayout()
        content.addWidget(self.btnOpenImage, 0, 0, 1, 2)
        content.addWidget(self.btnSelectTemplate, 1, 0, 1, 2)
        content.addWidget(self.btnNextBug, 2, 0)
        content.addWidget(self.btnCancelBug, 2, 1)
        content.addWidget(frmEmpty, 3, 0, 1, 2)

        self.setLayout(content)
        self.show()

    def openFile(self):
        fname, _ = QtGui.QFileDialog.getOpenFileName(self, "Open Specimin File",
                        self.currentPath)

        if fname != "":
            fpath = fname.split("/")
            self.currentPath = "/".join(fpath[0:-1])
            self.pnlImg.loadImage(fname)

    def selectTemplate(self):
        self.pnlImg.selectNewTemplate()

    def newTemplateSelected(self, ev):
        self.btnSelectTemplate.setText("Reset Template")

class ImagePanel(QtGui.QLabel):

    templateSel = 0
    template = (0,0,0,0)

    newTemplateSignal = QtCore.Signal(str)

    def __init__(self):
        super(ImagePanel, self).__init__()
        self.setMaximumSize(924,720)
        self.show()

    def loadImage(self, fname):
        sz = self.size()
        self.pix = QtGui.QPixmap(fname)
        self.pix = self.pix.scaled(sz.width(), sz.height(), QtCore.Qt.KeepAspectRatio)
        self.setPixmap(self.pix)

    def selectNewTemplate(self):
        self.templateSel = 1
        template = (0,0,0,0)
        self.repaint()

    def mousePressEvent(self, ev):
        if self.templateSel:
            (x1,y1,x2,y2) = self.template
            self.template = (ev.x(), ev.y(), x2, y2)

    def mouseReleaseEvent(self, ev):
        if self.templateSel:
            (x1,y1,x2,y2) = self.template
            self.template = (x1, y1, ev.x(), ev.y())
            self.templateSel = 0
            self.newTemplateSignal.emit("New template selected")

    def mouseMoveEvent(self, ev):
        if self.templateSel:
            (x1,y1,x2,y2) = self.template
            self.template = (x1, y1, ev.x(), ev.y())
            self.repaint()

    def paintEvent(self, ev):
        super(ImagePanel, self).paintEvent(ev)

        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setPen(QtGui.QColor(255,0,0))
        (x1,y1,x2,y2) = self.template
        qp.drawRect(x1,y1,x2-x1, y2-y1)
        qp.end()

def main():

    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

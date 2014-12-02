from MainWindow import *
from WitnessCam import *
from Util import InteractionLogger

def main():
    logfile = None
    if len(sys.argv) > 1:
        logfile = sys.argv[1]

    logger = InteractionLogger(logfile)
    logger.start()
    app = QtGui.QApplication(sys.argv)
    wc = WitnessCam(logger)
    ex = MainWindow(wc, logger)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

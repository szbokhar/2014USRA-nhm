# Main python program
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

import sys

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

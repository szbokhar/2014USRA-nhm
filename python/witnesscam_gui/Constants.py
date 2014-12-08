# Hint text constants
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

# Color Constants
BLUE = (255, 0, 0)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
CYAN = (255, 255, 0)

# Next step hints displayed to the user
HINT_LOADFILE = "Load a tray scan image by draggging a file here or using the \
file menu"
HINT_TRAYAREA_1 = "Click on the top left corner of the tray in the scanned \
image in the live camera view"
HINT_TRAYAREA_234 = "Now click on the next corner clockwise"
HINT_TRAYAREA_BADPOINT = "Please place that point again. You cannot have two \
points at the same location."
HINT_REMOVEBUG_OR_EDIT = "Remove an insect from the tray and wait for it to \
be marked with a blue circle, or click a green marker to edit"
HINT_REMOVEBUG = "Remove an insect from the tray and wait for it to be marked \
with a blue circle"
HINT_ENTERBARCODE = "Scan the barcode for this insect"
HINT_REPLACE_CONTINUE = "Once the barcode is entered correctly, replace the \
bug and remove the next one"
HINT_EDITBOX = "Drag box to move. Scroll to resize. Click X to delete. Click \
another marker to edit it. Remove insect to continue with scanning"
HINT_CALIBRATE = "Follow the directions on the Calibration window"

# Dialog text shown to the user when Closing the app or loading a new file
DIALOG_OVERWRITE = "File %s already exists. Would you like to overwrite it?"
DIALOG_SAVE = "Would you like to save changes to %s?"

# Prompts during the calibraion stage
CALIBRATION_STAGE1 = "Make sure the camera is perfectly still, and has a \
clear view of the tray. \nThen Click Here"
CALIBRATION_STAGE2 = "Wait about 5 seconds without disturbing the camera \
view,\nthen Click Here again."
CALIBRATION_STAGE3 = "Remove the smallest insect from the tray\
\nthen Click Here."
CALIBRATION_STAGE4 = "Wait about 5 seconds without disturbing the camera view,\
\nthen Click Here again."
CALIBRATION_STAGE5 = "Replace the insect on the tray then\nClick Here."
CALIBRATION_STAGE6 = "Calibration Done. Config values chosen.\nIf ever \
editing the below values, be sure all insects are on the tray"


# UI Text
INITIAL_BIGLABEL_TEXT = ["Drag and Drop tray scan image file here",
                         "or load it from the File menu"]
BARCODE_LABEL_TEXT = "ID: "
FILEBROWSER_COLUMNS = ["Filename", "# Bugs"]
FILEBROWSER_NEXT_TEXT = ">>"
FILEBROWSER_PREV_TEXT = "<<"

WINDOW_TITLE = "Insect Barcode Scanning"
WINDOW_STATUS_READY = "Ready"
FILENAME_RECENT_LOADS = ".recentScans.dat"
MENU_TEXT = [
    ("File", ["Open Tray Image",
              "Open Recent Tray Scans",
              "Export to CSV",
              "Quit"]),
    (" Edit", ["Undo",
              "Redo"]),
    ("Image", ["Retrace tray area",
               "Resync camera"])]

OPENDIALOG_TITLE = "Open Tray Image"

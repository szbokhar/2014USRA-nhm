Insect Digitization Witness Cam App
===================================

This application hopes to make the process of attaching a barcode to pinned
insect specimens and associating them with a digital image as easy as possible.
This README will describe how to use the application, and some configuration
options. I have only tested this on Mac OS 10.9, with packages installed with
MacPorts, but it should also work on Ubuntu or other Linux distributions.

Setup Instructions
------------------
This application runs with python 2.7, and requires numpy, pyside, and OpenCV
for Python. The reason we use python2.7 is because OpenCV does not currently
support Python3.

- Python: [https://www.python.org/](https://www.python.org/)
- Numpy: [http://www.numpy.org/](http://www.numpy.org/)
- PySide: [http://qt-project.org/wiki/PySideDocumentation](
  http://qt-project.org/wiki/PySideDocumentation)
- OpenCV: [http://www.scipy.org/](http://www.scipy.org/)


On Mac these can be installed using MacPorts:
```bash
$ sudo port install python27 py27-numpy py27-pyside
$ sudo port install opencv +python27
```
- MacPorts (for OSX): [https://www.macports.org/](https://www.macports.org/)

On most linux distros, these packages should be available through the package
manager, though the commands and package names will differ.


How to use
----------

Start the application by executing:
```bash
$ python2.7 main.py
```

### Load tray scan and setup
Click the **Load Tray Scan** button to open an image of a tray. This will also
start the witness camera. Be sure that the witness camera is set as the default
system camera, so that the application will automatically use the witness
camera.

The camera view will be displayed in the big box. Position the actual insect
tray (corresponding to the loaded image) in clear view of the camera. Now click
on the four corners of the tray in the camera view starting from the top left
corner of the tray in the scanned image. This is very important (Include
image). Upon each click a small circle will be placed at each corner.

Once all four corners are clicked, the scan of the tray will be placed in the
big box, and the camera view will be moved to the small box, and turn black.


### Scanning process
When the tray scan is shown on in the big view, the scanning process has
started. When you remove an insect from the tray and completely out of view of
the camera, the system will determine which insect was removed, and mark it
with a blue circle and X. This indicates that this is the removed insect. When
this happens, you can modify the **ID** in the text box, and the changes will
automatically be applied to that insect. 

If the barcode scanner is plugged in and can act as a keyboard device, then
simply scanning the barcode will be enough. The **ID** text box should
automatically focus every time a bug is removed.

Once the barcode has been entered, attach the barcode to the pin, and replace
the insect back on the try where it was before.

Now this process can be repeated for each insect.


### Editing the insect locations
Sometimes the locations of the insect markers will be a bit off. It is possible
to edit the markers that were placed down.

First make sure all the insects are back at their places on the tray. Then you
can click on any of the markers. When selected, they will turn red, and a box
will be placed approximately around the insect.

The following editing options are supported:

- **Move**: The marker and box can be moved by dragging from the inside of the
  box
- **Resize**: The box can be resized by dragging the corners or edges of the
  box
- **Delete**: The box and marker can be deleted by right clicking on the
  selected marker
- **Change ID**: The ID of the selected bug/marker is displayed in the **ID**
  text box. Changing the contained text will change the ID associated with that
  marker


### Fixing witness-cam errors
Sometimes the witness-cam will mis-recognize something, or some other error may
occur. This can usually be fixed by deleting the misplaced marker (see previous
section).

Another option to fix recognition errors is to make sure all bugs are back on
the tray, and make sure nothing is obscuring the view of the tray. Then click
the **Refresh Camera** button. This will recalibrate the background, and
hopefully fix any errors.

### Exporting the scanning data
The data from the scanning process can be exported at any time. By clicking the
**Export CSV**, a csv (comma separated value) file can be written. It could
look something like this:

```
BB 10011, 195, 397, 445, 975, 323, 681
BB 10021, 225, 1067, 447, 1545, 325, 1297
BB 10031, 789, 1117, 949, 1499, 853, 1293
BB 10041, 811, 397, 1007, 789, 911, 603
BB 10051, 1275, 413, 1469, 815, 1359, 591
...
```

Each row corresponds to an individual bug/marker.

Column 1 is the Barcode ID of the insect. This can be any string. Columns 2, 3,
4, and 5 represent the (x1, y1, x2, y2) positions of the box encasing the
insect. (x1, y1) is the pixel position of the top left of the box in the tray
scan image. (x2, y2) is the bottom right corner of the box. Columns 6 and 7 are
the (x, y) pixel position of the marker for the insect.

**NOTE:** When saving partial work, if you give the CSV file the same name as
they tray scan image (but with the extension *.csv*) and place it in the same
folder, it will be automatically loaded when the tray scan image is loaded, so
you can continue the work.

Implementation Configuration
----------------------------
This should only be done if the application is routinely under performing, such
as mis-recognizing operators hand's for removed bugs, or if the camera is
particularly noisy and a bug is never recognized as being removed.

In **AppData.py** starting at line 30, there are several constants used in the
vision process. These control aspects such as error tolerance and waiting time.

- **ACTION_DELAY**: (integer greater than 1) The number of camera frames with
  no motion the algorithm waits for before taking the next action
- **BOX_ERROR_TOLERANCE**: (float greater than 0) When estimating a bounding
  box for the insect, if the current bounding box guess is very different from
  the running guess, restart the wait counter. Only when the box has remained
  the same (within BOX_ERROR_TOLERANCE) for ACTION_DELAY number of frames is
  the bounding box accepted.
- **BOX_BLENDING_FACTOR**: (float from 0 to 1) If the box estimate for the
  current frame is the same (within error) as the running estimate, then blend
  the coordinates of the new guess with the running guess with this blending
  factor
- **GRAY_THRESHOLD**: (float greater than 0) To detect a removed bug, the
  system maintains a shot of the camera when all the bugs are present. So when
  one is removed, the current frame can be compared to the saved image, and a
  difference image is produced. The difference image is a grayscale image where
  each pixel is the magnitude of the difference pixel (eg. If the saved pixel
  is `(r0, g0, b0)` and the new one is `(r, g, b)`, then in the difference
  image the grayscale value for this pixel will be
  `sqrt((r-r0)^2+(g-g0)^2+(b-b0)^2)`. To reduce the effect of noise, any pixel
  with a value less than GRAY_THRESHOLD is made to be 0, so only the bug
  differences are considered.
- **FRAME_DELTA_BLENDING_FACTOR**: (float between 0 and 1) To determine if
  there is any motion in the camera view, the we take the sum of all the values
  in the difference image. This is recorded for each frame, as well as the
  delta (difference) between each frame. To smooth these values, we take the
  weighted average of the current delta value and the last delta value, with
  FRAME_DELTA_BLENDING_FACTOR as the weight.
- **STABLE_FRAME_DELTA_THRESHOLD**: (float greater than 0) If the current frame
  delta value is less than STABLE_FRAME_DELTA_THRESHOLD for ACTION_DELAY
  frames, then the view in the camera is considered to have not changed, and it
  is safe to refresh the camera, or take an action. Generally no actions are
  taken while the camera view is changing.
- **STABLE_FRAME_ACTION_THRESHOLD**: (float greater than 0) If the total
  difference in the frame is less than STABLE_FRAME_ACTION_THRESHOLD, then
  don't take any action. That small difference is just considered to be noise.

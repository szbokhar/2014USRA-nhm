Insect Digitization Witness Cam App
===================================

This application hopes to make the process of attaching a barcode to pinned insect specemines and associating them with a digital image as easy as possible. This readme will describe how to use the application, and some configuration options. I have only tested this on Mac OS 10.9, with packages installed with MacPorts, but it should also work on Ubuntu or other Linux distributions.

Setup Instructions
------------------
This application runs with python 2.7, and requires numpy, pyside, and OpenCV for Python. The reason we use python2.7 is because opencv does not currently support Python3.

- Python: [https://www.python.org/](https://www.python.org/)
- Numpy: [http://www.numpy.org/](http://www.numpy.org/)
- PySide: [http://qt-project.org/wiki/PySideDocumentation](http://qt-project.org/wiki/PySideDocumentation)
- OpenCV: [http://www.scipy.org/](http://www.scipy.org/)


On Mac these can be installed using MacPorts:
```bash
$ sudo port install python27 py27-numpy py27-pyside
$ sudo port install opencv +python27
```
- MacPorts (for OSX): [https://www.macports.org/](https://www.macports.org/)

On most linux distros, these packages should be availabe through the package manager, though the commands and package names will differ.


How to use
----------

Start the application by executing:
```bash
$ python2.7 main.py
```

### Load tray scan and setup
Click the **Load Tray Scan** button to open an image of a tray. This will also start the witness camera. Be sure that the witness camera is set as the default system camera, so that the application will automatically use the witness camera.

The camera view will be displayed in the big box. Position the actual insect tray (corresponding to the loaded image) in clear view of the camera. Now click on the four corners of the tray in the camera view starting from the top left corner of the tray in the scanned image. This is very important (Include image). Upon each click a small circle will be placed at each corner.

Once all four corners are clicked, the scan of the tray will be placed in the big box, and the camera view will be moved to the small box, and turn black.

### Scanning process
When the tray scan is shown on in the big view, the scanning process has started. When you remove an insect from the tray and completly out of view of the camera, the system will determine which insect was removed, and mark it with a blue circle and X. This indicates that this is the removed insect. When this happens, you can modify the **ID** in the textbox, and the changes will automatically be applied to that insect. 

If the barcode scanner is plugged in and can act as a keyboard device, then simply scanning the barcode will be enough. The **ID** textbox should automatically focus every time a bug is removed.

Once the barcode has been entered, attach the barcode to the pin, and replace the insect back on the try where it was before.

Now this process can be repeated for each insect.

### Editing the insect locations
Sometimes the locations of the insect markers will be a bit off. It is possible to edit the markers that were placed down.

First make sure all the insects are back at their places on the tray. Then you can click on any of the markers. When selected, they will turn red, and a box will be placed approximatly around the insect.

With a marker selected, you can drag from the center of the marker to move it. The box can be resized by 

# Natural History Museum Application #

## Automatic Cropping of Specimens ##

This is just a repo to hold the experimental code for the attempt at cropping out the insect specimens from the Natural History Museum data. Currently this repo contains the beetle images, as well as some other images test images.

It also contains the MATLAB script `selectTwoPoints.m` which attempts to produce one image for each insect by asking the user to click twice (first on the background, then on an insect).

These is also two python implementations of the MATLAB script. One implemented using `OpenCV`'s highgui library for gui, the other using `Tkinter` for gui. These will end up being replaced by a python implementation using `PyQt`.


#### Running MATLAB Script ###
- Startup MATLAB in the same directory as `selectTwoPoints.m`
- Run `selectTwoPoints(fname, samplesize, i, j)` where `fname` is the path to the image file, `samplesize` is the size of the box around the user clicks, and `i` and `j` specify the to save an individual file for the bugs from `i` to `j`
- On running the command, the image will be shown. First click somewhere on the background, then somewhere on the foreground (a bug). Then press `<enter>`
- The range of bugs specified by `i` and `j` will be saved in separate files

#### Running the Python Scripts ####
- On the commandline, run `python selectTwoPoints.py <fname>` or `python testtkinter.py <fname>` where `<fname>` is the path to the input image.
- The image will be shown, and ask the user to click on the background then the foreground. This script currently does not save the final cropped versions of the insects, but stops at the thresholding step.
- **NOTE:** these scripts require `NumPy`, `SciPy`, and `OpenCV` for python to be installed

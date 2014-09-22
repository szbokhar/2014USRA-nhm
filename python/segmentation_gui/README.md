seg.py README
=============

Requirements: pyside, numpy, scipy, PIL
Tested with python2.7

To run: `python seg.py <logfile>`

`<logfile>`: optional parameter to specify path to interactions log file


How to use:
----------
1. Click __Open Image__ to open the image file containing the specimens
2. Click __Select Template__ then place a red box around a type of specimen you
would like to crop. The box should contain the entire specimen, and have a good
padding between edge of the bug, and the border of the box.
3. Click __Select Bug__ then click on a specimen in the image to place a box on
it. The program will place the best box it can. The current box is highlighted
in green, and can be moved and resized to make more precise. When happy with
this box, either click __Confirm Bug__ or click the next specimen in the image.
4. When done selecting specimens, __Cancel Selection__ will end the specimen
selection mode.
5. If you wish to modify already placed boxes, click __Select Existing Box__
then click on the box you wish to modify. The current box is highlighted green,
and can be moved and resized. Clicking __Delete Box__ will remove the box. To
exit selection mode, click __Cancel Selection__.
6. Once all the insects are selected with a box, click __Save Boxes to File__
to save the boxes to a CSV file.

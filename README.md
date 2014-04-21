README
======

This project contains my work with Prof. Michael Terry during my Winter 2014
Undergraduate Research Assistantship.

The goal of this project was to design an easy to use system for automatically
cropping insect specimens in large images containing ~10-100 insects, and
eventually output several images, each one containing one only one specimen.


MATLAB Folder
-------------

This folder contains 2 different variations of the segmentation algorithm.
`random_template_scale.m` has the user select one example, and tests the
template over the entire image, then selects the "best" responses.
`random_template_interact.m` has the user select one example, and has the user
click on the other specimens and selects the best box to place on each specimen
clicked.


Python folder
-------------

This folder contains a user friendly GUI application to crop the insects in the
loaded image. It implements the variation of the algorithm that has the user
select one example, and click on every other insect.

Start the program with `python seg.py <logfile>`

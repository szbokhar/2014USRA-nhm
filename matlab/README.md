MATLAB README
=============

This folder contains 2 different variations of the segmentation algorithm.
`random_template_scale.m` has the user select one example, and tests the
template over the entire image, then selects the "best" responses.
`random_template_interact.m` has the user select one example, and has the user
click on the other specimens and selects the best box to place on each specimen
clicked.

Segmentation Algorithm
----------------------
First the algorithm loads the image and converts it to grayscale. Then it
applies a variety of filters to build an 11 dimensional feature vector for each
pixel (called the pixel-vector). The filters used are: gaussian filter with 3
different sigmas, lacplacian filter with 4 different sigmas, sobel filter (x
and y directions) with 2 different sigmas. The responses for each of these
filters are then normalized, so each element in a vector for a certain pixel
has range 0-1.

Now the user is asked to select a training example. The user places a box
around a single specimen. Then the algorithm creates a feature vector by
generating _n_ random 2D points inside the box (_n_ is typically 100-500),
called the template. A feature vector for the template is made from the
pixel-vectors for the _n_ points that were randomly generated. For convenience,
the template points are normalized (the x and y components are random values
from 0-1), so that the template can be rescaled when matching to different
areas on the image.

We match the template F to another box in the image by finding the
corresponding template points on the new region, and constructing a feature
vector for that region T. Both feature vectors are essentially an 11x_n_
matrix. The distance between the two feature vectors is the sum of the squares
of all the elements of F-T. The score is the computed using the distance, so
that a distance of 0 corresponds to a score of 1, and a large distance
corresponds to a 0.

In the interactive mode implemented in `random_template_interact.m` will ask
the user to click on another specimen, and find the template score target boxes
cantered at grid points in the neighborhood of the click. For better results,
multiple boxes of different scales (with respect to the size of the original
template box) are tested with each point. Then the point and scale with the
highest score is chosen to be the best box, and displayed to the user. (This is
the implementation in the python gui).

The automatic mode implemented in `random_template_scale.m` will apply the
template to specific grid points all over the image, as well as different
scales. Then the algorithm seeks to find the _best_ scores. It does so by first
setting all scores that are not the max of all their neighbors to 0. This leave
only the points that are local maximums left. Then it takes all of the
remaining responses and thresholds them to throw away the lower ones, leaving
only the highest ones. These are all displayed to the user.

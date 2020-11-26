from scipy import ndimage as ndi

from skimage.segmentation import  watershed
from skimage.feature import peak_local_max, canny
from skimage.measure import regionprops, block_reduce
from skimage.filters import  gaussian
from skimage.transform import hough_circle


import numpy as np
import cv2


def getCells(image):
    r,g,b = cropCircleROI(image, additionalCut = 50)

    # only use blue and green channel, substract red to avoid reflections
    BGdata = b.astype(int)+g.astype(int)-0.5*r.astype(int)

    threshold = 150

    BGdata = np.ma.filled(BGdata, 0)

    cells = getCellsFromMask(BGdata > threshold, image = BGdata)

    return [(int(cell[1]),int(cell[0])) for cell in cells]





def cropCircleROI(image, additionalCut = 5):
    """Return array masked outside circle with most dominant edges.
    :returny list[array]: masked arrays split by channels"""
    Rmin = np.min(image.shape[:-1])/3
    Rmin = 1250 / 3040 * image.shape[0]
    Rmax = 1400 / 3040 * image.shape[0]

    #downscale image for better performance
    reduceFactor = 5 # squared
    hough_radii = np.arange(Rmin/reduceFactor, Rmax/reduceFactor, dtype = int)

    downSampledImage = block_reduce(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), block_size = (reduceFactor, reduceFactor), func = np.max)
    downSampledEdges = canny(downSampledImage, sigma=3, low_threshold=5, high_threshold=10)

    hough_res = hough_circle(downSampledEdges, hough_radii)
    downSampledCircle = np.unravel_index(np.argmax(hough_res, axis=None), hough_res.shape)
    circle = np.array([downSampledCircle[1], downSampledCircle[2], hough_radii[downSampledCircle[0]]])*reduceFactor

    circleMask_ = cv2.circle(np.ones(image.shape[:-1],dtype = "uint8"), (circle[1], circle[0]), circle[2]-additionalCut, 0, thickness = -1)

    return [np.ma.array(image[:,:,i], mask = circleMask_) for i in range (image.shape[2])]







def getCellsFromMask(mask, image = None, returnLabels = False):


    data1 = gaussian(ndi.distance_transform_edt(mask), sigma = 4, preserve_range = True) 
    data2 = gaussian(image, sigma = 8, preserve_range = True)

    data = data1/np.max(data1) + data2/np.max(data2) 


    local_maxi = peak_local_max(data, indices=False, min_distance=10)
    markers = ndi.label(local_maxi)[0]
    labels = watershed(-data, markers, mask= mask)

    connectedRegions = regionprops(labels)

    # shape filter
    connectedRegions_shapeFiltered = [reg for reg in connectedRegions if reg.major_axis_length < 3 * reg.minor_axis_length]
    # area filter
    filteredRegions = [reg for reg in connectedRegions_shapeFiltered if reg.area > 1000 and reg.area < 1e5]

    cells = [reg.centroid for reg in filteredRegions]

    if returnLabels:
        return cells, labels
    return cells


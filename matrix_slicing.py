'''
Created on Jan 25, 2016

@author: alberts
'''

import numpy as np
from segmentation.utilities import own_itk as oitk

def get_slice(im_array,
              boundaries=None,
              visual_center=None,
              axis=0):
    '''Select a slice from a 3D volume.

    Given an ndarray, a slice is fetched at the coordinates
    specified in visual_center along the specified axis.

    If boundaries is given, the slice will not contain zero rows or zero
    columns. (Visual_center is given in the entire volume of im_array,
    not in the sub-volume specified with boundaries!)

    '''

    # get data, check dimensions
    im_array = get_array(im_array)
    if im_array is None:
        return None

    if len(im_array.shape) > 3:
        err = 'Function only valid for 3D arrays'
        raise AttributeError(err)
    if len(im_array.shape) <= axis:
        raise AttributeError('Nonvalid axis')

    # Adapt image and visual_center if boundaries are specified
    if boundaries is not None:
        im_array = remove_boundaries(im_array, boundaries)
        # change visual_center in coordinates of cropped image
        if visual_center is not None:
            visual_center = in_boundaries(visual_center,
                                          axis,
                                          boundaries)
            if visual_center is None:
                err = 'Supplied visual center is outside the boundaries!'
                raise RuntimeError(err)

    DIM = im_array.shape
    if len(DIM) == 2:
        return im_array

    # Get center and axis parameters
    if visual_center is None:
        # DIM already has removed boundaries!
        slice_index = default_visual_center(DIM,
                                            axis=axis)
    else:
        if isinstance(visual_center, (int, long, float)):
            slice_index = int(visual_center)
        else:
            slice_index = int(visual_center[axis])

    # Get the slice
    if axis == 0:
        im_slice = im_array[slice_index]
    elif axis == 1:
        im_slice = im_array[:, slice_index]
    elif axis == 2:
        im_slice = im_array[:, :, slice_index]

    return im_slice

def default_visual_center(dim, axis=0):
    """ Get default visual center for an image of given dimension. """

    return int(np.floor(dim[axis] / float(2)))

def get_bounded_dim(boundaries):
    """ Get the dimensions of the image bounded by these boundaries. """

    return tuple([boundaries[i][1] - boundaries[i][0] + 1
                  for i in range(3)])

def get_boundaries(im_array):
    """Get boundaries outside which the given array contains only zeros.

    Parameters
    ----------
    im_array : path to image, itk image or ndarray
        the array for which to calculate boundaries

    Returns
    -------
    boundaries : list of pairs
        each pair gives lower and upper boundary indices for every axis
        of im_array

    """

    im_array = get_array(im_array)
    if im_array is None:
        return None

    # set background value to the border values
    bg_values = np.unique(get_slice(im_array,
                                    visual_center=0,
                                    axis=0))
    if len(bg_values) == 1:
        bg = bg_values[0]
        if bg != 0:
            print 'Non-zero background value: ' + str(bg)
    else:
        bg = 0

    boundaries = []
    for ax in range(len(im_array.shape)):
        under = 0
        upper = im_array.shape[ax] - 1

        zeros = True
        while zeros and under <= upper:
            if not np.all(get_slice(im_array,
                                    visual_center=under,
                                    axis=ax)
                          == bg):
                zeros = False
            else:
                under += 1

        zeros = True
        while zeros and upper >= under:
            if not np.all(get_slice(im_array,
                                    visual_center=upper,
                                    axis=ax)
                          == bg):
                zeros = False
            else:
                upper -= 1
        boundaries.append([under, upper])
        
    return boundaries

def get_boundaries_series(arr):
    """Get boundaries for a series of 3d volumes such that in every 3d
    volume all nonzero values are included in the boundaries.

    Parameters
    ----------
    arr : list of imagelike
    """

    if not equal_shapes(arr):
        print 'Carefull!! You are looking for boundaries ' + \
                        'across images with different shapes!'

    bound = None

    for im_arr in arr:
        
        if isinstance(im_arr, list):
            
            new_bound = get_boundaries_series(im_arr)
            
        else:

            array = get_array(im_arr)
            if array is None:
                continue
    
            new_bound = get_boundaries(array)
            
        if bound is None:
            bound = new_bound
        else:
            bound = union_boundaries(bound, new_bound)

    return bound

def equal_shapes(arr):
    """ Return whether all images in arr are of equal shape.

    Parameters:
    -----------
    arr : list of imagelike
        the arrays to be checked for equal shapes.
    """

    this_shape = None
    for im_arr in arr:

        if isinstance(im_arr, list):
            if not equal_shapes(im_arr):
                return False

        else:
            array = get_array(im_arr)
            if array is None:
                continue
    
            if this_shape is None:
                this_shape = array.shape
            else:
                if array.shape != this_shape:
                    return False

    return True

def remove_boundaries(im_arr,
                      boundaries=None):
    """ Remove boundaries from the im_arr. Return None if the given
    boundaries are not compatible. """

    if boundaries is None:
        boundaries = get_boundaries(im_arr)

    # Check dimensions of the boundaries
    if len(boundaries) != len(im_arr.shape):
        err = 'Boundaries are of different dimension as array'
        raise RuntimeError(err)
    for ax in range(len(boundaries)):
        for lim in range(2):
            # Dimensions should not exceed array shape
            if boundaries[ax][lim] > im_arr.shape[ax]:
                err = 'Noncompatible boundaries given for this image'
                raise RuntimeError(err)

    if len(im_arr.shape) == 2:
        im_box = im_arr[boundaries[0][0]:boundaries[0][1] + 1,
                        boundaries[1][0]:boundaries[1][1] + 1]

    if len(im_arr.shape) == 3:
        im_box = im_arr[boundaries[0][0]:boundaries[0][1] + 1,
                        boundaries[1][0]:boundaries[1][1] + 1,
                        boundaries[2][0]:boundaries[2][1] + 1]

    return im_box

def union_boundaries(boundaries, other_boundaries):
    """Set boundaries to include the other_boundaries. In other words,
    the box enclosed by boundaries will grow larger or stay stable, it
    will in no case grow smaller.

    """

    if boundaries is None:
        return other_boundaries
    if other_boundaries is None:
        return boundaries
    if len(boundaries) != len(other_boundaries):
        err = 'Boundaries not of same dimension'
        raise ValueError(err)

    for i in range(len(boundaries)):
        if other_boundaries[i][0] < boundaries[i][0]:
            boundaries[i][0] = other_boundaries[i][0]
        if other_boundaries[i][1] > boundaries[i][1]:
            boundaries[i][1] = other_boundaries[i][1]

    return boundaries

def in_boundaries(visual_center, axis, boundaries):
    """Adapt the visual_center for a volume where the boundaries have
    been removed by `boundaries`. Return None if visual_center is
    outside the boundaries.

    """

    # Get center and axis parameters
    if visual_center is None:
        return None
    else:
        if isinstance(visual_center, int):
            slice_index = visual_center
        else:
            slice_index = visual_center[axis]

    # return None if visual_center outside boundaries
    if slice_index > boundaries[axis][1]:
        return None
    if slice_index < boundaries[axis][0]:
        return None

    new_index = slice_index - boundaries[axis][0]

    return new_index

def get_array(arr):
    """ Get the image (np.ndarray), if no image is found, return None,
    if an invalid path is given, raise an error. """

    # Check if array is None to begin with
    no_image = arr is None
    # if arr is a string, check if it is empty
    if isinstance(arr, str):
        no_image = arr == ''

    if no_image:
        return None

    array = oitk.get_itk_array(arr)
    return array

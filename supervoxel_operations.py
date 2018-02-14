'''
Created on Oct 24, 2017

@author: alberts
'''

'''
Created on May 8, 2017

@author: alberts
'''

import os
import numpy as np
import SimpleITK as sitk

import own_itk as oitk

#### borders

def get_borders(supervoxels):
    """ Get supervoxel borders as a binary array. Voxels on the edge of each 
    nonzero-labeled object are 1, all others are set to 0. 
    
    Parameters
    ----------
    supervoxels : np.ndarray
        integer mask of the supervoxels
    
    Returns
    -------
    border_arr : np.ndarray
        array of the same shape as supervoxels, with voxels on the edge of non-zero
        supervoxels set to 1 and all others to zero.
    """
    
    border_im = sitk.LabelContour(oitk.make_itk_image(supervoxels, verbose=False))
    border_arr = oitk.get_itk_array(border_im)
    border_arr = border_arr > 0
    
    return border_arr

def adapt_borders(hard_map, slic_map):
    """ Change slic_map such that every supervoxel has 
    only one value in hard_map. """ 
            
    # Get supervoxels which have multiple labels
    slics_to_split = \
        get_non_uniform_supervoxels(slic_map, hard_map)
        
    if len(slics_to_split) == 0:
        return slic_map
    
    print 'We need to split '+str(len(slics_to_split))+' supervoxels'
    
    new_slic_int = np.max(slic_map) + 1
            
    for slic_int in slics_to_split:
        
        labels_present = np.unique(hard_map[slic_map == slic_int])
        assert len(labels_present) > 1 #otherwise slic_to_split not correct
#         if len(labels_present) > 2:
#             print labels_present
        for label in labels_present[1:]:
            check_max_value(new_slic_int, slic_map)
            indices = np.logical_and(slic_map == slic_int,
                                     hard_map == label)
            slic_map[indices] = new_slic_int
            new_slic_int += 1
            
    slics_to_split = get_non_uniform_supervoxels(slic_map, hard_map)
    if not len(slics_to_split) == 0:
        err = 'This didnt work, still %d supervoxels to split' % len(slics_to_split)
        raise RuntimeError(err)
            
    return slic_map

def check_max_value(new_max_int, arr):
    """ Check whether this value is lower than the maximum allowed value
    of the arr.dtype. """
    
    try:
        max_allowed = np.iinfo(arr.dtype).max
    except:
        max_allowed = np.finfo(arr.dtype).max
    # TODO: Throw a specific error related to datatype
    if new_max_int > max_allowed:
        err = 'This new maximum value exceeds the image type maximum value'
        raise RuntimeError(err)

def get_non_uniform_supervoxels(slic_im, hard_map):
    """ Get supervoxel indices of supervoxels in slic_im 
    which have multiple values in hard_map. """
    
    # Quick check
    slic_ints = np.unique(slic_im[hard_map != 0])
    a = sitk.LabelStatisticsImageFilter()
    a.Execute(oitk.make_itk_image(hard_map, verbose=False),
              oitk.make_itk_image(slic_im, verbose=False))
    slics_to_split = [i for i in slic_ints \
                      if a.GetSigma(int(i))>0] 
    
    return slics_to_split


#### miscellanous

def get_bool_indices(im, values):
    """ Get the indices of the elements in im with a value in values. 
    
    Parameters
    ----------
    im : array_like
        The input image
    values : (M,) array_like
        The values of the elements for which the indices 
        need to be returned.
        
    Returns
    -------
    ind3d : array_like
        bool indices in the shape of im, indicating the elements in im 
        with a value in values.
        
    """
    
    dim = im.shape
    ind1d = np.in1d(im.flatten(), values)
    ind3d = np.reshape(ind1d, dim)
    
    return ind3d

################# Segmentation-related

def write_separate_labels(hard_segmentation_path):
    """ Write binary arrays for each of the labels separately. """
    
    # construct the binary arrays
    
    hard_map = oitk.get_itk_array(hard_segmentation_path)
    
    enhanced = (hard_map == 1).astype('uint8')
    tumor_core = (np.logical_and(enhanced, hard_map == 2)).astype('uint8')
    whole_tumor = (hard_map > 0).astype('uint8')
    
    # get the paths to write the arrays to
    
    dirname = os.path.dirname(hard_segmentation_path)
    enhanced_path = os.path.join(dirname, 'enhanced.nii.gz')
    tumor_core_path = os.path.join(dirname, 'tumor_core.nii.gz')
    whole_tumor_path = os.path.join(dirname, 'whole_tumor.nii.gz')
    
    # write
    
    itk_proto = oitk.get_itk_image(hard_segmentation_path)
    oitk.write_itk_image(oitk.make_itk_image(enhanced, itk_proto), enhanced_path)
    oitk.write_itk_image(oitk.make_itk_image(tumor_core, itk_proto), tumor_core_path)
    oitk.write_itk_image(oitk.make_itk_image(whole_tumor, itk_proto), whole_tumor_path)
    
def get_separate_labels(segmentation_image, length=None):
    """ Separate each labels as binary array"""
    
    if length is None:
        length = np.max(segmentation_image)
    list_of_bin_segm = []
    for i in range(1, length+1):
        list_of_bin_segm.append((segmentation_image == i).astype('uint8'))
    
    #Order is important to display the types
    return list_of_bin_segm

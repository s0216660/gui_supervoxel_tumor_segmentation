'''
Created on Oct 19, 2017

@author: alberts
'''

import numpy as np
import time

from skimage.segmentation import slic as skimage_slic

from ..utilities import own_itk as oitk

############################

PARAM = {}
PARAM['flair'] = {"n_segments": 15000,
                   "compactness":0.1}
PARAM['t1'] = {"n_segments": 15000,
                "compactness":0.1}
PARAM['t1c'] = {"n_segments": 15000,
                 "compactness":0.1}
PARAM['t2'] = {"n_segments": 15000,
                "compactness":0.1}
PARAM['all'] = {"n_segments": 15000,
                "compactness":0.1}

############################

def get_supervoxels(im_arrs, param=None):
    """ If an image is provided, get its supervoxel segmentation, if 
    multiple images are provided, get their multimodal supervoxel
    segmentation. 
    
    Parameters
    ----------
    im_arrs : image_like, list of image like
        one or multiple images provided as paths to images, itk images
        or raw 2D or 3D numpy arrays
    param : dict of str to float
        'n_segments' : int
            approximate number of supervoxels to be segmented
            see skimage.segmentation.slic()
        'compactness' : float
            see skimage.segmentation.slic()
 
    Returns
    -------
    int_mask : np.ndarray
        2D or 3D integer mask with the supervoxel segmentation
    """
    
    if param is None:
        param = PARAM['all']
    
    # read images if paths are given
    im_arrs = list(im_arrs)
    im_arrs = oitk.load_arr_from_paths(im_arrs)
    im_arrs = np.asarray(im_arrs)
                    
    multi_modal = False
    if len(im_arrs.shape) == 4:
        multi_modal = True
    elif len(im_arrs.shape) != 3:
        err = 'unrecognized image array!'
        raise RuntimeError(err)
        
    if multi_modal:
        slic_im = _multi_modal_slic(im_arrs, 
                                    n_segments=param['n_segments'], 
                                    compactness=param['compactness'])
    else:
        slic_im = _slic(im_arrs, 
                        n_segments=param['n_segments'], 
                        compactness=param['compactness'])
            
    return slic_im

def _slic(image,
         n_segments=15000,
         compactness=0.1,
         verbose=True):
    """ Perform slic supervoxel segmentation on the input image.
 
    Parameters
    ----------
    image : np.ndarray
        2D, 3D or 4D grayscale input image
        note: only 4D input image will be interpreted as multichannel
        input.
    n_segments : int
        approximate number of supervoxels to be segmented
        see skimage.segmentation.slic()
    compactness : float
        see skimage.segmentation.slic()
    verbose : bool
        print parameters and execution time
 
    Returns
    -------
    int_mask : np.ndarray
        2D or 3D integer mask with the supervoxel segmentation
    """
    
    if len(image.shape) > 4:
        err = 'Sorry, 2D 3D or 4D numpy array expected!'
        raise RuntimeError(err)
    if len(image.shape) == 4:
        if verbose:
            print 'Multi-modal supervoxel calculation!'
        
    start = time.time()
    min_size_factor = 0.5
    int_mask = skimage_slic(image,
                            n_segments=n_segments,
                            compactness=compactness,
                            multichannel=False,
                            min_size_factor=min_size_factor)
    # within slic, multichannel will automatically be set to True
    # if 4D input
 
    if verbose:
        print 'SLIC RAN w PARAMS: '
        print '\t compactness ' + str(compactness)
        print '\t n_segments ' + str(n_segments)
        print '\t segmented areas ' + str(np.max(int_mask))
        print '\t computation time: ' + str(time.time() - start)
 
    int_max = np.max(int_mask)
    while int_max > 10 * n_segments:
        if verbose:
            print 'Too many supervoxels, increasing min_size_factor...'
        min_size_factor *= 10
        int_mask = skimage_slic(image,
                                n_segments=n_segments,
                                compactness=compactness,
                                multichannel=False,
                                min_size_factor=min_size_factor)

        int_max = np.max(int_mask)
        
    if int_max < n_segments / 2.:
        err = 'Supervoxel calculation problem here...'
        raise RuntimeError(err)
 
    return int_mask

def _multi_modal_slic(mod_maps,
                      n_segments=15000,
                      compactness=0.1,
                      verbose=True):
    """ Perform slic on all the modality images with the given parameters.

    Parameters
    ----------
    mod_maps : list of np.ndarray
        input images
    param : dict (str : (int or float) )
        containing "n_segments" and "compactness" parameters

    Returns
    -------
    int_mask : np.ndarray
        2D or 3D integer mask with the supervoxel segmentation
    """
    
    _mod_maps_np = np.asarray(mod_maps)
    if len(_mod_maps_np.shape) != 4:
        err = 'Sorry, 4D array expected!'
        raise ValueError(err) 

    _mod_maps_np = np.swapaxes(_mod_maps_np, 0, 3)
    _mod_maps_np = np.swapaxes(_mod_maps_np, 0, 2)
    mod_maps_np = np.swapaxes(_mod_maps_np, 0, 1)

    int_mask = _slic(mod_maps_np.astype(np.float),
                     n_segments=n_segments,
                     compactness=compactness,
                     verbose=verbose)
    return int_mask

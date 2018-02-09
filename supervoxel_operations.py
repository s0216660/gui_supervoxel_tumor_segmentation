'''
Created on Oct 24, 2017

@author: alberts
'''

'''
Created on May 8, 2017

@author: alberts
'''
import numpy as np
import itertools
import SimpleITK as sitk
import scipy.ndimage as spim
from collections import Counter

from ..utilities import own_itk as oitk

class Supervoxels():
    """ Create an instance of a supervoxel integer array, defined 
    over a region of interest (i.e. given as the mask). The class 
    allows to calculate features for each of the supervoxels over
    supplied images or integer masks. It allows to convert supervoxel
    integer arrays. """
            
    def __init__(self, supervoxels, mask=None):
        """ Supply a supervoxel integer array and a binary mask with the
        region of itnerest. """
        
        if not isinstance(supervoxels, np.ndarray):
            raise ValueError('Please supply supervoxel np.ndarray.')
        if mask is None:
            mask = np.ones_like(supervoxels)
        else:
            mask = oitk.get_itk_array(mask)
            if not np.all(np.logical_or(mask==0,mask==1)):
                err = 'Binary 0-1 mask expected!'
                raise ValueError(err)
        self.mask = mask
        
        # convert supervoxel type
        new_supervoxels = supervoxels.astype(np.uint32)
        if np.any(supervoxels-new_supervoxels > 0):
            err = 'Either you are working with WAY TOO MANY supervoxels, '
            err += 'or these supervoxels are not an integer mask.'
            raise ValueError(err)
        supervoxels = new_supervoxels
        
        # make sure no 0-valued supervoxel is present within the mask
        if 0 in supervoxels[mask!=0]:
            max_slic_int = np.max(supervoxels) + 1
            check_max_value(max_slic_int, supervoxels)
            supervoxels[supervoxels==0] = max_slic_int
        # set all pixels in the supervoxel image outside the mask to 0
        supervoxels[mask==0] = 0
        
        self.slic_arr = supervoxels
        self._set_instance_variables()
        
    def _set_instance_variables(self):
        """ Set the list of supervoxel integers, indicating the order
        in which supervoxels will be evaluated. """
        
        self.slic_ints = np.unique(self.slic_arr[self.mask != 0])
        self.slic_im = oitk.make_itk_image(self.slic_arr, verbose=False)
            
    def get_slic_means(self, mod_maps):
        """ Get mean intensity in the mod_maps per slic region in the mask."""
        
        mod_maps = np.asarray(mod_maps)
        if len(mod_maps.shape) == len(self.slic_arr.shape):
            mod_maps = np.asarray([mod_maps])
        elif len(mod_maps.shape) != len(self.slic_arr.shape) + 1:
            err = 'mod_maps of unrecognized dimension'
            raise ValueError(err)
        if False in [self.slic_arr.shape == arr.shape
                     for arr in mod_maps]:
            raise ValueError('mod_maps of unexpected shape')
        
        slic_means = []

        for arr in mod_maps:
            a = sitk.LabelStatisticsImageFilter()
            a.Execute(oitk.make_itk_image(arr, verbose=False),
                      self.slic_im)
            means = [a.GetMean(int(i)) for i in self.slic_ints]
            slic_means.append(np.asarray(means))
    
        slic_means = np.asarray(slic_means).T
        
        return slic_means
    
    def get_slic_most_common(self, segm):
        """ Get most common gt label for each supervoxel.
        
        For each supervoxel integer in slic_inds get the supervoxel region in 
        slic_arr and get the main gt label for this region in gt.
        """
        
        if self.slic_arr.shape != segm.shape:
            raise ValueError('gt of unexpected shape')
        
        # if every supervoxel has only one label.
        if len(get_non_uniform_supervoxels(self.slic_arr, segm))==0:
            
            # for each supervoxel, get label in hard_map
            a = sitk.LabelStatisticsImageFilter()
            a.Execute(oitk.make_itk_image(segm, verbose=False),
                      self.slic_im)    
            slic_labels = np.asarray([a.GetMean(int(i)) for i in self.slic_ints])
            
            assert np.all(slic_labels-slic_labels.astype('uint8') == 0)
            return slic_labels
    
        # if some supervoxels have several labels.
        slic_labels = [None for i in self.slic_ints] # label per supervoxel
        slic_max_counts = [0 for i in self.slic_ints] # label count per supervoxel
        
        slic_indices = get_bool_indices(self.slic_arr, self.slic_ints)
        segm_labels = np.unique(segm[slic_indices])
        
        for label in segm_labels:
            # frequency of the label in each supervoxel
            slic_hits = Counter(self.slic_arr[segm == label]) 
            slic_label_counts = [slic_hits[i] if i in slic_hits else 0 \
                                 for i in self.slic_ints]
            
            # update label and frequency of the label in each supervoxel
            update = [[label, slic_label_counts[i]] \
                      if slic_label_counts[i] > slic_max_counts[i] \
                      else [slic_labels[i], slic_max_counts[i]] \
                      for i in range(len(self.slic_ints))]
            update = np.asarray(update)
            slic_labels = update[:, 0]
            slic_max_counts = update[:, 1]
    
        return slic_labels
        
    def get_slic_label_distance(self, soft_maps=None, cumulative=False):
        """ For each supervoxel, get the distance to the COM of each
        map in soft_maps. 
        
        The COM is weighted by the volume of the connected components, 
        as an attempt to make it more robust against small noisy spots.
        
        Returns an array of shape (len(supervoxels), len(labels)), where default
        labels are the unique integers in the hard_map for the mask region,
        excluding the zero label.  
        """
        
        # for each supervoxel get distance to com of each label 
        # (normalized by label volume)
        distance_to_label = []
        cum_map = np.zeros_like(soft_maps[0])
        for soft_map in soft_maps:
            if cumulative:
                this_map = soft_map + cum_map
                cum_map = this_map
            else:
                this_map = soft_map
            label_dist = self.get_slic_distance(soft_map)
            distance_to_label.append(label_dist)
            
        distance_to_label = np.asarray(distance_to_label)
        distance_to_label = distance_to_label.T
        
        return distance_to_label
    
    def get_slic_distance(self, soft_map):
        """ For each supervoxel, get the distance to the COM of the
        nonzero label in hard_map. 
        
        The COM is weighted by the volume of the connected components, 
        as an attempt to make it more robust against small noisy spots.
        
        If a zeros-only image is supplied, a nan-vector is returned. 
        """
        
        if self.slic_arr.shape != soft_map.shape:
            raise ValueError('bin_map of unexpected shape')
            
        component_threshold = 0.1
        if np.all(soft_map <= component_threshold):
            print 'Calculating distances to empty label... Returning Nan.'
            distance_to_label = [np.nan for _ in self.slic_ints]
            distance_to_label = np.asarray(distance_to_label)
            return distance_to_label 
        
        # get radius of label volume
        volume = np.count_nonzero(soft_map)
        radius = ( 0.75 * volume / np.pi)**(1/float(3))   

        # get connected components
        im = oitk.make_itk_image(soft_map, verbose=False)
        im = sitk.BinaryThreshold(im, 
                                  lowerThreshold=component_threshold, 
                                  upperThreshold=np.max(soft_map))
        cim = sitk.ConnectedComponent(im)
        carr = oitk.get_itk_array(cim)
        
        # get label com weighted by component volume
        vol_arr = np.zeros_like(carr, dtype=np.float)
        for i in np.unique(carr):
            if i == 0:
                continue
            vol = np.sum(carr==i)
            vol_arr[carr==i] = soft_map[carr==i] * (np.float(vol)**2)
            
        if np.all(vol_arr == 0):
            print 'Wasnt able to calculate COM... Returning Nan.'
            distance_to_label = [np.nan for _ in self.slic_ints]
            distance_to_label = np.asarray(distance_to_label)
            return distance_to_label 
        
        com = spim.measurements.center_of_mass(vol_arr)
        assert np.all(np.isfinite(com))
        
        # get distance to com for the whole image grid
        x,y,z = np.indices(self.slic_arr.shape)
        x_dist, y_dist, z_dist = x-com[0], y-com[1], z-com[2]
        dist = np.sqrt((x_dist**2) + (y_dist**2) + (z_dist**2))
        dist_norm = dist / float(radius) # normalize by label volume
            
        # for each supervoxel, get average distance to label com        
        a = sitk.LabelStatisticsImageFilter()
        a.Execute(oitk.make_itk_image(dist_norm, verbose=False), 
                  self.slic_im)
        distance_to_label = [a.GetMean(int(i)) for i in self.slic_ints]
        distance_to_label = np.asarray(distance_to_label)
        
        return distance_to_label
            
    def get_slic_neighbours(self, soft_maps):
        """ For each supervoxel, get the sum of the neighbours for each
        map in osft_maps. 
        
        Returns an array of shape (len(supervoxels), len(labels)), where default
        labels are the unique integers in the hard_map for the mask region. """
        
        if False in [self.slic_arr.shape == soft_map.shape for soft_map in soft_maps]:
            print 'Softmap shapes: %s' % str([soft_map.shape for soft_map in soft_maps])
            print 'Slic array shape: %s' % str(self.slic_arr.shape)
            raise ValueError('soft_maps of unexpected shape')
            
        # for each supervoxel get nb of neighbours of each label
        # (normalized by number of neighbours)
        labels = range(len(soft_maps))
            
        label_neighbours = np.zeros((len(labels), len(self.slic_ints)))
        shifts = itertools.product([-1,0,1], repeat=3)
        for shift in shifts:
            
            # shift the supervoxel image
            if np.all(shift==0):
                continue
            shifted_slic = np.copy(self.slic_arr)
            for axis in range(len(shift)):
                if shift[axis] != 0:
                    shifted_slic = np.roll(shifted_slic, 
                                               shift[axis], 
                                               axis=axis)
                    
            # set pixels shifted within own supervoxels to zero
            internal_shifts = shifted_slic == self.slic_arr
            shifted_slic[internal_shifts] = 0
            
            a = sitk.LabelStatisticsImageFilter()
            for label_ind in labels:
                a.Execute(oitk.make_itk_image(soft_maps[label_ind],verbose=False),
                          oitk.make_itk_image(shifted_slic,verbose=False))
                sums = [a.GetSum(int(i)) for i in self.slic_ints]
                label_neighbours[label_ind] += np.asarray(sums)
           
        sum_label_neighbours = np.sum(label_neighbours, axis=0)
        if np.any(sum_label_neighbours == 0):
            nb_isolated_supervoxels = np.count_nonzero(sum_label_neighbours==0)
            mask_components = oitk.get_itk_array(\
                                sitk.ConnectedComponent(\
                                    oitk.make_itk_image(self.mask)))
            nb_mask_components = np.max(mask_components) - 1 # substract main brain
            print '%d supervoxels with zero neighbours' % (\
                            nb_isolated_supervoxels)
            print '%d connected components outside main brain mask (>=%d)' % (\
                            nb_mask_components, nb_isolated_supervoxels)
            soft_sums = np.sum(np.asarray(soft_maps),axis=0)[self.mask>0]
            print 'Minimum sum of probabilities within mask (1.): %.5f' % (\
                            np.min(soft_sums))
            print 'Nb of zero sum probabilities within mask (0): %d' % (\
                            np.count_nonzero(soft_sums==0))
            sum_label_neighbours = np.fmax(sum_label_neighbours, np.finfo(np.float).eps)
            
        label_neighbours /= sum_label_neighbours
        label_neighbours = label_neighbours.T                    
                
        return label_neighbours
    
    def map_supervoxel_integers(self, new_slic_values):
        """ In the supervoxel image, change pixels with values in 
        slic_ints to the values in new_slic_valuse. """
        
        if len(set(self.slic_ints)) != len(self.slic_ints):
            err = 'There are duplicates in slic_ints. '
            raise ValueError(err)
    
        new_slic_im = np.zeros(self.slic_arr.shape)
        unique_new_values = np.unique(new_slic_values)
        if len(unique_new_values) > 500:
            print 'Hm this might take a long time... Try quantizing.'
        for new_value in unique_new_values:
            if new_value == 0:
                continue
            this_slic_ints = self.slic_ints[new_slic_values == new_value]
            slic_indices = get_bool_indices(self.slic_arr, this_slic_ints)
            
            if np.any(new_slic_im[slic_indices]!=0):
                err = 'Hm, some of these pixels have alread been set...'
                raise RuntimeError(err)
            
            new_slic_im[slic_indices] = new_value
        
        return new_slic_im

################# Supervoxel-related

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
    
def get_separate_labels(segmentation_image):
    """ Separate each labels as binary array"""
    #label is the type of pixel 0 - background, 1 - edema, 2 - Necrotic tumor and 3 - Active tumor
    edema = (segmentation_image == 1).astype('uint8')
    necrotic_tumor = (segmentation_image == 2).astype('uint8')
    active_tumor = (segmentation_image == 3).astype('uint8')
    
    #Order is important to display the types
    return [active_tumor, necrotic_tumor, edema]

def get_separate_labels_for_display(segmentation_image):
    """ Separate each labels as binary array"""
    #label is the type of pixel 0 - background, 1 - edema, 2 - Necrotic tumor and 3 - Active tumor
    edema = (segmentation_image == 1).astype('uint8')
    necrotic_tumor = (segmentation_image == 2).astype('uint8')
    active_tumor = (segmentation_image == 3).astype('uint8')
    selected = (segmentation_image == 4).astype('uint8')
    
    #Order is important to display the types
    return [active_tumor, necrotic_tumor, edema, selected]

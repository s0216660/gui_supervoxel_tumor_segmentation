'''
Created on Feb 9, 2018

@author: alberts
'''

import numpy as np
from PIL import Image as ImagePIL

def set_color_empty(color, segm_im):

    new_color = np.minimum(np.array(color),
                           np.array(segm_im)).astype('uint8')

    return ImagePIL.fromarray(new_color,
                              mode='L')

def set_color_custom(segm_im, color, rgb=None):
    """ Set pixels where segm_im == 255 to the specified color. """
    
    channels = []
    for i in range(len(color)):
        if rgb is None:
            pix = np.where(np.array(segm_im) == 255, color[i], np.array(rgb[i]))
        else:
            pix = np.where(np.array(segm_im) == 255, color[i], 0)
        channels[i] = ImagePIL.fromarray(pix, mode='L')

    return channels

def get_image_pil(pix, image_scale, return_image_size=False):
    """get the ImagePIL format from a 2d numpy array"""

    # normalize array between 0 and 255
    pix = pix - pix.min()
    max_int = float(pix.max())
    if max_int == 0:
        max_int = 0.00001
    pix_normalized = pix * 255. / max_int
    # reshape the array to fit the current image size
    pix_ratio = pix.shape[1] / np.floor(pix.shape[0])
    image_size = (int(image_scale * pix_ratio), image_scale)

    temp_im = ImagePIL.fromarray(pix_normalized)\
                        .resize(image_size, ImagePIL.NEAREST)

    if return_image_size:
        return temp_im, image_size
    return temp_im
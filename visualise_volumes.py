'''
Created on Apr 26, 2016

@author: alberts
'''

import os

from Tkinter import FLAT
from Tkinter import HORIZONTAL
from Tkinter import END
from Tkinter import IntVar
from Tkinter import Menu

from ttk import Frame
from ttk import Button
from ttk import Label
from ttk import Entry
from ttk import Style
from ttk import Scale
from ttk import Checkbutton

from tkFileDialog import askopenfilename
from tkFileDialog import asksaveasfilename

import numpy as np

import SimpleITK as sitk

from PIL import ImageTk
from PIL import ImageFilter
from PIL import Image as ImagePIL

from my_frame import MyFrame
import LinkedScrollBar as lsb
import matrix_slicing as ms
import own_itk as oitk
import image_pil as pil
import supervoxel_operations as utils

######################################################################

labels = ['Enhanced','Non-active tumor','Edema']
yellow = (205, 190, 35)
green = (100, 165, 50)
red = (220, 50, 0)
label_colors = [red, green, yellow]
label_colors_d = ['red','green','yellow']
selected = (0, 0, 255)

######################################################################

class VisualVolumes(MyFrame):
    #Paths need to be changed when used in a different environment
    #Also segmentation accepts only one file now!
    
    def __init__(self,
                 image_paths=None,
                 segm_path=None,
                 supervoxel_id_path=None,
                 topframe=None):

        MyFrame.__init__(self,
                         topframe=None)
        Style().theme_use('clam')
        self.set_title('Visualise Volumes')


        self.set_variables(image_paths,
                           segm_path=segm_path,
                           supervoxel_id_path=supervoxel_id_path)

        self.create_ui(image_paths=image_paths,
                       supervoxel_id_path=supervoxel_id_path)


    ########## variable setting ###########################F

    def set_variables(self,
                      image_paths,
                      segm_path=None,
                      supervoxel_id_path=None):
        """Set initial alpha for opacity, boundaries, undo-redo stacks,
        and paths for modalities, segmentation and supervoxels"""

        #Alpha value for opacity initialization
        self.alpha = 0.3

        self._axis = 0

        self.show_supervoxels = True

        self._set_images(segm_path, image_paths, supervoxel_id_path)

        # set boundaries for all images:
        self.boundaries = ms.get_boundaries_series(image_paths)

        # set stacks for CTRL+Z and CTRL+Y
        # CTRL+Z to undo
        # CTRL+Y to redo
        self.undo_stack = []
        self.redo_stack = []
        self.image_nb = len(image_paths)
        self.selected_id_list = []
        #Keybindings for undo and redo actions
        self.bind('<Control-z>', self.undo_action)
        self.bind('<Control-y>', self.redo_action)
#         self.bind('<Control-a>', self.all_image)        
        self.focus_set()

    def _set_images(self, segm_path, image_paths, supervoxel_id_path):
        """ Set and check image and segmentation arrays and dimensions. """

        # Shapes for all modalities
        shapes = [oitk.get_itk_array(path).shape \
                  for path in image_paths]
        if len(set(shapes)) != 1:
            err = 'Images are not of same dimension'
            raise  ValueError(err)
        self.dim = shapes[0]

        # set the images and the image paths
        self.images = [oitk.get_itk_array(path) \
                       for path in image_paths]
        self.images_original = np.copy(self.images)

        # Get segmentation from segmentation path if given
        self.segm = None
        self.segm_path = None
        if segm_path is not None:
            self.segm = oitk.get_itk_array(segm_path)
            self.segm_path = segm_path

        # Get supervoxels from supervoxel path if given
        self.supervoxel_border = None
        self.supervoxel_id = None
        if supervoxel_id_path is not None:

            # get supervoxels and adapt if segmentation is at hand
            self.supervoxel_id = oitk.get_itk_array(supervoxel_id_path)
            if self.segm is not None:
                self.supervoxel_id = utils.adapt_borders(self.segm, 
                                                         self.supervoxel_id)

            # get borders of the supervoxels
            self.supervoxel_border = utils.get_borders(self.supervoxel_id)

    ########## Frame setting ############

    def create_ui(self, image_paths, supervoxel_id_path):
        """This function creates the UI elements."""

        sub_frame = Frame(self)
        sub_frame.grid(column=1,
                       row=0,
                       columnspan=self.image_nb)

        # create a sub frame to select the image slices that are displayed
        slice_frame = Frame(sub_frame)
        slice_frame.grid(column=0,
                         row=1,
                         columnspan=self.image_nb)

        pic_frame = Frame(sub_frame)
        pic_frame.grid(column=0,
                       row=0,
                       columnspan=self.image_nb)

        self.configure_images(pic_frame, image_paths)
        self.add_slice_bar(slice_frame)
        self.set_optional_buttons(supervoxel_id_path)


    def configure_images(self,
                         pic_frame,
                         image_paths):
        """Create widgets to place images, descriptions and slice scrollers."""

        # create a sub frame to display the images
        self._imagelabel = [None for _ in range(self.image_nb)]
        self._image_view = [None for _ in range(self.image_nb)]
        _descrlabel = [None for _ in range(self.image_nb)]

        # descriptions of the images defaults to their path basenames
        descriptions = [os.path.basename(image_paths[i]) 
                        for i in range(self.image_nb)]

        self.histogram_sliders = []
        for i in range(self.image_nb):

            _sub_pic_frame = Frame(pic_frame)
            _sub_pic_frame.grid(column=int(i%2),
                                row=int(i/2),
                                pady=5)

            # set Label for a description above the images
            _descrlabel[i] = Label(_sub_pic_frame,
                                   text=descriptions[i])
            _descrlabel[i].grid(column=0, row=0)


            # set Label to depict the images
            self._imagelabel[i] = Label(_sub_pic_frame)
            self._imagelabel[i].grid(column=0, row=1)


            # set Scales for the intensity slides
            _sub_sub_frame = Frame(_sub_pic_frame)
            _sub_sub_frame.grid(column=0,
                                row=2)

            min_val = np.min(self.images_original[i])
            max_val = np.max(self.images_original[i])

            intensity_scale1 = Scale(_sub_sub_frame,
                                     from_=min_val,
                                     to=max_val/2,
                                     orient=HORIZONTAL)
            intensity_scale1.set(min_val)
            intensity_scale1.grid(column=0,
                                  row=0,
                                  sticky=['e', 'w', 's'])

            intensity_scale2 = Scale(_sub_sub_frame,
                                     from_=max_val/2,
                                     to=max_val,
                                     orient=HORIZONTAL)
            intensity_scale2.set(max_val)
            intensity_scale2.grid(column=1,
                                  row=0,
                                  sticky=['e', 'w', 's'])

            self.histogram_sliders.append(intensity_scale1)
            self.histogram_sliders.append(intensity_scale2)
            intensity_scale1.bind("<B1-Motion>", self.change_intensity)
            intensity_scale2.bind("<B1-Motion>", self.change_intensity)

            # Attach commands to the image frames
            self._imagelabel[i].bind("<Button-1>", self.click_image)
            self._imagelabel[i].bind("<Button-3>", self.label_change)
            self._imagelabel[i].bind("<Button 4>", self.slice_up)
            self._imagelabel[i].bind("<Button 5>", self.slice_down)
            self._imagelabel[i].bind("<B1-Motion>", self.motion_image)
            self._imagelabel[i].bind("<Double-Button-1>", self.select_connected)

    def add_slice_bar(self, slice_frame):
        """Add a slice selection options to slice_frame.

        Returns
        -------
        this_slice_label_number : Label
            the field displaying the current slice number
        this_new_slice : Entry
            the field allowing the user to fill in a slice number
        new_value : int
            the initial slice number to be set

        """

        # Have a line displaying slice number
        _slice_label = Label(slice_frame, text='Slice displayed : ')
        _slice_label.grid(column=0, row=0, sticky=['w', 'e'])
        this_slice_label_number = Label(slice_frame)
        this_slice_label_number.grid(column=1, row=0,
                                     sticky=['w', 'e'])

        # Allow to change slice number
        _goto = Label(slice_frame, text=' - go to slice :')
        _goto.grid(column=2, row=0, sticky=['w', 'e'])

        this_new_slice = Entry(slice_frame, width=6)
        this_new_slice.bind('<Return>', self.goto_slice)
        this_new_slice.bind('<KP_Enter>', self.goto_slice)
        this_new_slice.grid(column=3, row=0, sticky=['w', 'e'])

        self.image_scale = (self.screen_width - 200) / 4

        # Allow to scroll through the slices
        self._slice_scroll = lsb.LinkedScrollBar(master=slice_frame,
                                                 command=self.disp_im,
                                                 minVal=self._get_min_slice(),
                                                 maxVal=self._get_max_slice(),
                                                 step=1,
                                                 orient='horizontal')
        self._slice_scroll.grid(column=0,
                                row=1,
                                columnspan=self.image_nb,
                                sticky=['e', 'w', 's'])


        self._slice_label_number = this_slice_label_number
        self._new_slice = this_new_slice
        self.reset_slice_scroll()

    ##### allow to show segmentations, change axis and quit #########

    def set_optional_buttons(self, supervoxel_id_path=None):
        """ Set bottoms to quit, change axis, show and hide segmentation, ...
        at the upper row of the main frame.
        """

        _sub_frame1 = Frame(self)
        _sub_frame1.grid(column=0,
                         row=0,
                         padx=10,
                         sticky=['n', 'e', 'w'])

        _sub_sub_frame1 = Frame(_sub_frame1)
        _sub_sub_frame1.grid(column=0,
                             row=0,
                             sticky=['e', 'w'],
                             pady=10)

        ind = 0
        self.button_axis = Button(_sub_sub_frame1,
                                  text="Change axis",
                                  command=self.change_axis)
        self.button_axis.grid(column=0, row=ind, pady=3)
        
        ind += 1
        self.button_axis = Button(_sub_sub_frame1,
                                  text="Mirror Images",
                                  command=self.mirror_image)
        self.button_axis.grid(column=0, row=ind, pady=3)

        ind = 0
        if self.segm is not None:

            _sub_sub_frame2 = Frame(_sub_frame1)
            _sub_sub_frame2.grid(column=0,
                                 row=1,
                                 sticky=['e', 'w'],
                                 pady=10)

            _sub_sub_frame3 = Frame(_sub_frame1)
            _sub_sub_frame3.grid(column=0,
                                 row=2,
                                 sticky=['e', 'w'],
                                 pady=10)

            self.button_supervoxels = Button(_sub_sub_frame2,
                                             text="Show/Hide supervoxels",
                                             command=self.change_supervoxels)
            self.button_supervoxels.grid(column=0,
                                         row=ind,
                                         sticky=['w', 'n', 'e'])

            if supervoxel_id_path is None:
                self.button_supervoxels['state'] = 'disabled'
            ind += 1

            self.tumor_checkbox_label = Label(_sub_sub_frame2,
                                              text="Display tumor type: ",
                                              relief=FLAT)
            self.tumor_checkbox_label.grid(column=0, row=ind)

            ind += 1
            self.cb1_var = IntVar()
            self.cb_1 = Checkbutton(_sub_sub_frame2,
                                    text='%s (%s)' % (labels[0], label_colors_d[0]),
                                    variable=self.cb1_var,
                                    command=lambda : self.change_segm(0))
            self.cb_1.grid(column=0,
                                          row=ind,
                                          sticky=['w', 'n', 'e'])
            ind += 1
            self.cb2_var = IntVar()
            self.cb_2 = Checkbutton(_sub_sub_frame2,
                                    text='%s (%s)' % (labels[1], label_colors_d[1]),
                                    variable=self.cb2_var,
                                    command=lambda : self.change_segm(1))
            self.cb_2.grid(column=0,
                                          row=ind,
                                          sticky=['w', 'n', 'e'])
            ind += 1
            self.cb3_var = IntVar()
            self.cb_3 = Checkbutton(_sub_sub_frame2,
                                    text='%s (%s)' % (labels[2], label_colors_d[2]),
                                    variable=self.cb3_var,
                                    command=lambda : self.change_segm(2))
            self.cb_3.grid(column=0,
                                         row=ind,
                                         sticky=['w', 'n', 'e'])
            ind += 1
            self.cb4_var = IntVar()
            self.cb_4 = Checkbutton(_sub_sub_frame2,
                                    text="All tumors",
                                    variable=self.cb4_var,
                                    command=lambda : self.change_segm(3))
            self.cb_4.grid(column=0,
            		   row=ind,
                           sticky=['w', 'n', 'e'])

            ind += 1
            self.cb5_var = IntVar()
            self.cb_5 = Checkbutton(_sub_sub_frame2,
                                    text="No tumors",
                                    variable=self.cb5_var,
                                    command=lambda : self.change_segm(4))
            self.cb_5.grid(column=0,
                           row=ind,
                           sticky=['w', 'n', 'e'])
            #print self.cb_4
            #self.bind('<a>', self.cb_4.toggle)
            #self.bind('<s>', self.cb_5.toggle)

            ind += 1
            alpha_label = Label(_sub_sub_frame2, text="Opacity:")
            alpha_label.grid(column=0, row=ind)
            self.alpha_scale = Scale(_sub_sub_frame2,
                                     from_=0.0,
                                     to=1.0,
                                     command=self.set_alpha,
                                     orient=HORIZONTAL)
            ind += 1
            self.alpha_scale.set(self.alpha)
            self.alpha_scale.grid(column=0,
                                  row=ind,
                                  columnspan=self.image_nb,
                                  sticky=['w', 'n', 'e'])

            ind = 0
            self.button_save_segm = Button(_sub_sub_frame3,
                                           text="Save segmentation",
                                           command=self.save_segm)
            self.button_save_segm.grid(column=0, row=ind, sticky=['w', 'n', 'e'])

            ind += 1
            self.button_open_segm = Button(_sub_sub_frame3,
                                           text="Open segmentation",
                                           command=self.open_segm)
            self.button_open_segm.grid(column=0, row=ind, sticky=['w', 'n', 'e'])


    #################### Display images ###########################

    def disp_im(self):
        """use the size, slice and zoom to display the image"""
        self.focus_set()
        slice_index = int(self._slice_scroll.val)

        for i in range(self.image_nb):
            pix = np.array(\
                    ms.get_slice(self.images[i],
                                 boundaries=self.boundaries,
                                 visual_center=slice_index,
                                 axis=self._axis),
                    dtype='float')

            temp_im, im_size = pil.get_image_pil(pix, 
                                                 self.image_scale, 
                                                 return_image_size=True)
            self.image_size = im_size
            temp_im = temp_im.convert('RGB')

            if self.segm is not None:
                temp_im = self.add_segmentation(temp_im, slice_index)
                
            if self.show_supervoxels and type(self.supervoxel_border) is np.ndarray:
                temp_im = self.add_supervoxels(temp_im, slice_index)

            # create the 2d view with or without the bounding box
            self._image_view[i] = ImageTk.PhotoImage(temp_im)
            self._imagelabel[i]['image'] = self._image_view[i]

        # update slice label
        self._slice_label_number['text'] = str(int(self._slice_scroll.val))

    def add_segmentation(self, image, slice_ind=None):
        """ Add a segmentation to the image (colors will be overlaid). """

        #Segmentation is separated into binary segmentations
        #Also, segm contains 3 binary segmentations
        if len(self.selected_id_list) > 0:
            segm = utils.get_separate_labels_for_display(self.segm_disp)
        else:
            segm = utils.get_separate_labels(self.segm)
        r, g, b = image.convert('RGB').split()
        rgb = [r, g, b]

        #Variable that contains selected colors
        colors = [None for _ in range(len(segm))]

        #Add edema if check box selected
        if hasattr(self, 'cb1_var') and self.cb1_var.get() == 1:
            colors[0] = label_colors[0]

        #Add non active tumor if check box selected
        if hasattr(self, 'cb2_var') and self.cb2_var.get() == 1:
            colors[1] = label_colors[1]

        #Add active tumor if check box selected
        if hasattr(self, 'cb3_var') and self.cb3_var.get() == 1:
            colors[2] = label_colors[2]
        
        if len(colors)==4:
            colors[3] = selected

        #Do the painting with respect to colors variable
        for i in range(len(segm)):
            if colors[i] is None:
                continue
            pix = np.array(ms.get_slice(segm[i],
                                        boundaries=self.boundaries,
                                        visual_center=slice_ind,
                                        axis=self._axis))
            pix[pix > 0.5] = 1
            pix = pix.astype('uint8')

            if np.any(pix):
                color_region = pil.get_image_pil(pix, self.image_scale)
                rgb = pil.set_color_custom(color_region, colors[i], rgb=rgb)

        #Merge operation for all
        segm_im = ImagePIL.merge("RGB", rgb)
        return ImagePIL.blend(image, segm_im, self.alpha)
    
    def add_supervoxels(self, image, slice_ind=None):
        """ Add supervoxels to the image (boundaries will be drawn)."""

        r, g, b = image.convert('RGB').split()
        pix = np.array(ms.get_slice(self.supervoxel_id,
                                    boundaries=self.boundaries,
                                    visual_center=slice_ind,
                                    axis=self._axis))

        self.supervoxel_id_slice = pix

        if np.any(pix):
            pix = pix *50000

        #Get image with supervoxels that has borders calculated with contours
        sup_im = pil.get_image_pil(pix, self.image_scale)\
                        .convert("RGB")\
                         .filter(ImageFilter.CONTOUR)\
                         .filter(ImageFilter.EDGE_ENHANCE_MORE)\
                         .filter(ImageFilter.EDGE_ENHANCE_MORE)

        r_border, g_border, b_border = sup_im.split()
        r = pil.set_color_empty(r, r_border)
        g = pil.set_color_empty(g, g_border)
        b = pil.set_color_empty(b, b_border)

        #Merge operation for all colors
        sup_im = ImagePIL.merge("RGB", (r, g, b))
        return ImagePIL.blend(image, sup_im, self.alpha)

    #################### EVENTS: Change slice ######################
        
    def reset_slice_scroll(self):

        max_slice = self._get_max_slice()
        min_slice = self._get_min_slice()
        diff = max_slice - min_slice
        new_value = int(min_slice + np.floor(diff / 2))
        self._slice_scroll.set_value(new_value)
        
    def slice_up(self, *args):
        """increase slice number"""
        new_value = self._slice_scroll.val + 1
        if new_value <= self._get_max_slice(in_boundaries=True):
            self._slice_scroll.set_value(new_value)

    def slice_down(self, *args):
        """decrease slice number"""
        new_value = self._slice_scroll.val - 1
        if new_value >= self._get_min_slice(in_boundaries=True):
            self._slice_scroll.set_value(new_value)

    def _get_max_slice(self, in_boundaries=True):
        """Gets the maximum slice of the numpy array."""
        if in_boundaries:
            return self.boundaries[self._axis][1]
        else:
            return self.dim[self._axis] - 1

    def _get_min_slice(self, in_boundaries=True):
        """Gets the minimum slice of the numpy array."""
        if in_boundaries:
            return self.boundaries[self._axis][0]
        else:
            return 0
        
    def change_axis(self):
        """It changes the axis of the image."""
        self._axis = (self._axis + 1) % 3
        self.reset_slice_scroll()
        self.disp_im()

    def mirror_image(self):
        """It mirrors the image."""
        for i in range(self.image_nb):
            self.images[i] = np.flip(self.images[i], axis=(self._axis + 1) % 3)
            self.images_original[i] = np.flip(self.images_original[i], axis=(self._axis + 1) % 3)
        if self.segm is not None:
            self.segm = np.flip(self.segm, axis=(self._axis + 1) % 3)

        if self.show_supervoxels and type(self.supervoxel_border) is np.ndarray:
            self.supervoxel_id = np.flip(self.supervoxel_id, axis=(self._axis + 1) % 3)
            self.boundaries = ms.get_boundaries_series(self.images)
        self.disp_im()
        
    def goto_slice(self, *args):
        """moves to the desired slice"""

        z = self._new_slice.get()
        max_valid_z = self._get_max_slice(in_boundaries=True)
        min_valid_z = self._get_min_slice(in_boundaries=True)
        # if not an integer
        try:
            z = int(z)
            # if out of range
            if z < 0:
                msg = 'Please select a positive slice index. ' +\
                        'Lowest non-zero slice is shown.'
                self._slice_scroll.set_value(min_valid_z)
                self._new_slice.delete(0, END)
            elif z < min_valid_z:
                msg = 'Slice %d has only zeros. ' % z
                msg += 'Lowest non-zero slice is shown.'
                self._slice_scroll.set_value(min_valid_z)
                self._new_slice.delete(0, END)
            elif z > self._get_max_slice(in_boundaries=False):
                msg = 'Slice %d exceeds the image dimension. ' % z
                msg += 'Highest non-zero slice is shown.'
                self._slice_scroll.set_value(max_valid_z)
                self._new_slice.delete(0, END)
            elif z > max_valid_z:
                msg = 'Slice %d consists of zeros. ' % z
                msg += 'Highest non-zero slice is shown.'
                self._slice_scroll.set_value(max_valid_z)
                self._new_slice.delete(0, END)
            else:
                self._slice_scroll.set_value(z)
                self._new_slice.delete(0, END)
        except ValueError as e:
            print e
            self._new_slice.delete(0, END)   
            
    ############### EVENTS : select and change #########################
    
    def click_image(self, event):
        """ Select a supervoxel and color it in blue. 
        Called when clicked on an image. """
        
        supervoxel_id = self._get_supervoxel_id(event.x, event.y)
        self._update_selected_id_list(supervoxel_id)
        
    def motion_image(self, event):
        """ Select multiple supervoxels and color it in blue. 
        Called when clicked and motioned on an image. """
        
        supervoxel_id = self._get_supervoxel_id(event.x, event.y)
        self._update_selected_id_list(supervoxel_id, unselect=False)
        
    def select_connected(self, event):
        
        supervoxel_id = self._get_supervoxel_id(event.x, event.y)
        label = self.segm[self.supervoxel_id == supervoxel_id][0]
        
        im = sitk.GetImageFromArray((self.segm==label).astype(np.int))
        connected = sitk.GetArrayFromImage(sitk.ConnectedComponent(im))
        clabel = connected[self.supervoxel_id == supervoxel_id][0]
        supervoxel_ids = list(np.unique(self.supervoxel_id[connected==clabel]))
        self._update_selected_id_list(supervoxel_ids)
        
#     def all_image(self, *args):
#         """ Select multiple supervoxels and color it in blue. 
#         Called when clicked and motioned on an image. """
#         
#         supervoxel_ids = list(np.unique(self.supervoxel_id_slice))
#         supervoxel_ids.remove(0)
#         self._update_selected_id_list(supervoxel_ids)
        
    def _get_supervoxel_id(self, eventx, eventy):
        """ Get the supervoxel id of the given mouse position. """
        
        #the size of the image:
        #0 element of image corresponds to 1 element
        #of supervoxel_id_slice and vice versa

        #converting the coordinates on the clicked image into the 
        #coordinates of the voxel
        #Since the displayed pixels range from 1 to lenght+1,
        #need to subtract 1 from the coordinates
#         print self.supervoxel_id_slice.shape
        x_coordinate_supervoxel = (eventx - 1) *\
                                  len(self.supervoxel_id_slice[0]) /\
                                  self.image_size[0]

        y_coordinate_supervoxel = (eventy - 1) *\
                                  len(self.supervoxel_id_slice) /\
                                  self.image_size[1]

        z_coordinate_supervoxel = int(self._slice_scroll.val)

        coordinates = [x_coordinate_supervoxel,
                       y_coordinate_supervoxel,
                       z_coordinate_supervoxel]
        
        selected_id = self.supervoxel_id_slice[coordinates[1], coordinates[0]]
        return selected_id
        
    def _update_selected_id_list(self, selected_id, add_to_undo=True, unselect=True):
        """ Depending whether this supervoxel is already selected, mark
        or unmark the supervoxel. """
        
        if isinstance(selected_id, list):
            if unselect:
                if all([sid in self.selected_id_list for sid in selected_id]):
                    map(self.selected_id_list.remove, selected_id)
                else:
                    self.selected_id_list.extend(selected_id)
            else:
                if not all([sid in self.selected_id_list for sid in selected_id]):
                    self.selected_id_list.extend(selected_id)
                else:
                    return #nothing changed                    
        else:
            if unselect:
                if selected_id in self.selected_id_list:
                    self.selected_id_list.remove(selected_id)
                else:
                    self.selected_id_list.append(selected_id)
            else:
                if selected_id not in self.selected_id_list:
                    self.selected_id_list.append(selected_id)
                else:
                    return #nothing changed
        print 'Selected supervoxels: %s' % str(self.selected_id_list)
            
        if add_to_undo:
            action = selected_id, None, None
            self.undo_stack.append(action)
            
        self.update_segm_display()
        
    def update_segm_display(self):
        """ Color all supervoxels with ids in self.selected_id_list blue
        in self.segm_disp. """
        
        #Selection is updated for visualisation
        self.segm_disp = self.segm.copy()
        if len(self.selected_id_list) == 1:
            mask = self.supervoxel_id == self.selected_id_list[0]            
        elif len(self.selected_id_list) > 1:
            ind1d = np.in1d(self.supervoxel_id.flatten(), self.selected_id_list)
            mask = np.reshape(ind1d, self.supervoxel_id.shape)
        else:
            mask = np.zeros_like(self.supervoxel_id)
        
        selected_idx = np.where(mask)
        self.segm_disp[selected_idx[0], selected_idx[1], selected_idx[2]] = 4
            
        self.disp_im()
        
    def label_change(self, event):
        """When clicking right on a supervoxel, give a drop-down list
        with labels to change to."""

        # Adding the selection menu with radio  buttons.
        self.menu = Menu(self, tearoff=0)
        self.menu\
            .add_radiobutton(label="Background",
                             value=0,
                             command=lambda\
                             arg0=0,
                             arg1=self.selected_id_list: self.change_label_onclick(arg0, arg1))

        self.menu\
            .add_radiobutton(label=labels[0],
                             value=3,
                             command=lambda\
                             arg0=3,
                             arg1=self.selected_id_list: self.change_label_onclick(arg0, arg1))

        self.menu\
            .add_radiobutton(label=labels[1],
                             value=2,
                             command=lambda\
                             arg0=2,
                             arg1=self.selected_id_list: self.change_label_onclick(arg0, arg1))
        self.menu\
            .add_radiobutton(label=labels[2],
                             value=1,
                             command=lambda\
                             arg0=1,
                             arg1=self.selected_id_list: self.change_label_onclick(arg0, arg1))
        self.menu.tk_popup(event.x_root, event.y_root)

    def change_label_onclick(self, new_label, selected_id_list):
        """Changing the label of the supervoxel

        cooordinates is a list of the ids of the selected voxel.
        #coordinates[0] - x coordinate,
        #coordinate[1] - y coordinate,
        #coordinate[2] - z coordinate

        new label is the type of pixel 0 - background,
        #3 - edema, 2 - Non-active tumor and 1 - Active tumor

        self.segms is the array with segmentations
        self.supervoxel_ids is the the array with the supervoxels

        """

        #Empty the redo_stack whenever segmentation is changed by user
        self.redo_stack = []

        for selected_id in (self.selected_id_list):
            #Segmentation is updated with new labels
            #Old label is saved for undo and redo actions
            selected_idx = np.where(self.supervoxel_id == selected_id)
            old_label = self.segm[selected_idx[0], selected_idx[1], selected_idx[2]]
            old_label = old_label[0]
            self.segm[selected_idx[0], selected_idx[1], selected_idx[2]] = new_label
    
            # if the checkboxes are unselected but changed, they are automatically checked.
            if new_label == 3:
                self.cb1_var.set(1)
                self.cb5_var.set(0)
            if new_label == 2:
                self.cb2_var.set(1)
                self.cb5_var.set(0)
            if new_label == 1:
                self.cb3_var.set(1)
                self.cb5_var.set(0)
    
            #Actions as coordinates, old_label and new_label to go switch between segmentation states
            action = selected_idx, old_label, new_label
            self.undo_stack.append(action)
            
        self.selected_id_list = []
        self.disp_im()

    def change_intensity(self, event):
        """ Change the intensity of the images based on the hist slider."""
        slider = event.widget
        i = self.histogram_sliders.index(slider)

        # find the image index based on the slider
        image_i = 3
        if i == 0 or i == 1:
            image_i = 0
        elif i == 2 or i == 3:
            image_i = 1
        elif i == 4 or i == 5:
            image_i = 2

        original_image = self.images_original[image_i]
        image = self.images[image_i]

        if (i + 1) % 2 == 0:
            slider_upper = slider
            slider_lower = self.histogram_sliders[i - 1]
        else:
            slider_lower = slider
            slider_upper = self.histogram_sliders[i + 1]

        lower = slider_lower.get()
        upper = slider_upper.get()
        lower = np.float(lower)
        upper = np.float(upper)
        np.clip(original_image, lower, upper, image)

        np.subtract(image, lower, out=image, casting='unsafe')
        self.disp_im()

    def change_segm(self, button_ind):
        """ Show or hide the segmentation from the images."""

        if button_ind <= 2:
            if self.cb1_var.get() + self.cb2_var.get() + self.cb3_var.get() < 3:
                self.cb4_var.set(0)
            else:
                self.cb4_var.set(1)
            if self.cb1_var.get() + self.cb2_var.get() + self.cb3_var.get() > 0:
                self.cb5_var.set(0)
            else:
                self.cb5_var.set(1)

        if button_ind == 3:
            self.cb1_var.set(1)
            self.cb2_var.set(1)
            self.cb3_var.set(1)
            self.cb4_var.set(1)
            self.cb5_var.set(0)
        if button_ind == 4:
            self.cb1_var.set(0)
            self.cb2_var.set(0)
            self.cb3_var.set(0)
            self.cb4_var.set(0)
            self.cb5_var.set(1)
        self.disp_im()

    def change_supervoxels(self):
        """ Toggle between showing supervoxels or not."""
        self.show_supervoxels = not self.show_supervoxels
        self.disp_im()

    def set_alpha(self, *args):
        """ Change the opacity level."""
        self.alpha = self.alpha_scale.get()
        self.disp_im()

    def undo_action(self, *args):
        """ Execute undo action on CTRL-Z."""

        #If respective stack is not empty
        #Go to the last state of segmentation
        #and update the redo_stack
        print 'undo!'
        if len(self.undo_stack) > 0:
            action = self.undo_stack.pop()
            self.redo_stack.append(action)
            selected_id, old_label, _ = action
            if old_label is not None:
                self._change_label_supervoxel(old_label, selected_id)
            else:
                self._update_selected_id_list(selected_id, add_to_undo=False)
            self.disp_im()

    def redo_action(self, *args):
        """Execute redo action on CTRL-Y"""

        #If respective stack is not empty
        #Go to the last state of segmentation
        #and update the undo_stack
        print 'redo!'
        if len(self.redo_stack) > 0:
            action = self.redo_stack.pop()
            self.undo_stack.append(action)
            selected_id, _, new_label = action
            if new_label is not None:
                self._change_label_supervoxel(new_label, selected_id)
            else:
                self._update_selected_id_list(selected_id, add_to_undo=False)
            self.disp_im()    
            
    def _change_label_supervoxel(self, new_label, selected_idx):
        """ Change the label of the supervoxel

        cooordinates is a list of the ids of the selected voxel.
        coordinates[0] - x coordinate, coordinate[1] - y coordinate, coordinate[2] - z coordinate
        new label is the type of pixel 0 - background,
        3 - edema, 2 - Non-active tumor and 1 - Active tumor
        self.segms is the array with segmentations
        self.supervoxel_ids is the the array with the supervoxels"""
        #Segmentation is updated with new labels
        self.segm[selected_idx[0], selected_idx[1], selected_idx[2]] = new_label
        self.disp_im()   
        
    #################### Save or load a segmentation ###################        

    def save_segm(self):
        """ Save the current custom segmentation into a file."""
        kwargs = {}
        if self.segm_path is not None:
            dirname, basename = os.path.split(self.segm_path)
            if not basename.startswith('corrected_'):
                basename = 'corrected_'+basename
            kwargs['initialfile'] = basename
            kwargs['initialdir'] = dirname
        path = asksaveasfilename(title="Please select a path to save your segmentation",
                                 filetypes=[('Image files',
                                             ('.nii',
                                              '.mha',
                                              '.nii.gz'))],
                                 **kwargs)

        #TODO: change here self.segm_path
        if self.segm_path is not None:
            old_segm = oitk.get_itk_image(self.segm_path)
        image = oitk.make_itk_image(self.segm, old_segm)
        oitk.write_itk_image(image, path)

    def open_segm(self):
        """ Open a new custom segmentation from a file."""
        kwargs = {}
        kwargs['initialdir'] = os.environ.get('HOME')
        if self.segm_path is not None:
            dirname, basename = os.path.split(self.segm_path)
            if not basename.startswith('corrected_'):
                basename = 'corrected_'+basename
            kwargs['initialfile'] = basename
            kwargs['initialdir'] = dirname
        msg = 'Please select a segmentation'
        segm_path = askopenfilename(title=msg,
                                    filetypes=[('Image files',
                                                ('.nii',
                                                 '.mha',
                                                 '.nii.gz'))],
                                     **kwargs)
        if os.path.exists(segm_path):
            self.segm_path = segm_path
            self.segm = oitk.get_itk_array(self.segm_path)
            self.disp_im()

    ################# EVENTS - END #####################################

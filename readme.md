# Code

- main = ./main_correct_segmentations.py
   This module allows you to run the gui
- matrix_slicing.py
   Allows to manipulate numpy arrays for visualisation purposes (i.e. select slices at certain indices)
- LinkedScrollBar.py
    Substructure for the gui that allows to scroll through image slices
- my_frame.py
    Contains the parent class of the gui
- own_itk.py
    Allows to load and read medical images into numpy arrays for example.

# Run

To run, execute main_correct_segmentations.py:

python main_correct_segmentations.py

In this setting, the gui will ask you to supply image paths. Press cancel if you are done selecting image paths (you can choose as many as you want). Then, the gui will ask you to supply segmentation paths for the image paths you have supplied. You are obliged to either supply no segmentation paths, or to supply the same number of segmentation paths as image paths.

# Code

- main = ./visualise_volumes.py
   This module allows you to run the gui
- matrix_slicing.py
   Allows to manipulate numpy arrays for visualisation purposes (i.e. select slices at certain indices)
- LinkedScrollBar.py
    Substructure for the gui that allows to scroll through image slices
- my_frame.py
    Contains the parent class of the gui
- own_itk.py
    Allows to load and read medical images into numpy arrays for example.
- utils.py
    Contains a few usefull functions that might help you.
- assemble_data_supervoxel_gui.py
    Ignore this, I left it there so that I know which data I gave you for the project.

# Run

To run, execute visualise_volumes.py:

python visualise_volumes.py

In this setting, the gui will ask you to supply image paths. Press cancel if you are done selecting image paths (you can choose as many as you want). Then, the gui will ask you to supply segmentation paths for the image paths you have supplied. You are obliged to either supply no segmentation paths, or to supply the same number of segmentation paths as image paths.

# Todos:

- Allow to show multiple segmentations at once, instead of only accepting binary segmentations.
- There is a button 'Change axis'. I suggest to make a button 'Revert axis horizontal' and 'Revert axis vertical' as well, this basically allows the user to revert the image from right-to-left and from bottom-to-top.
- When the gui is launched an obsolete window is opened, entitled 'tk'. It remains there and doesnt show anything. See if you can find out why it is there and whether it can be removed...

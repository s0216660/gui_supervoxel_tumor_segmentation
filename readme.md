# Code

- main = ./main_correct_segmentations.py
    
    This module allows you to run the gui
   
- visualize_volumes.py

    This module allows to visualize multiple modalities. It also loads a segmentation and supervoxel map, and allows you to change the segmentation by changing the labels of supervoxels.
   
Helpers:

- matrix_slicing.py

    Allows to manipulate numpy arrays for visualisation purposes (i.e. select slices at certain indices)
    
- LinkedScrollBar.py

     Substructure for the gui that allows to scroll through image slices
     
- my_frame.py

     Contains the parent class of the gui
     
- own_itk.py

     Allows to load and read medical images into numpy arrays for example.

# Run

Before running, you have to set a few filename indicators in main_correct_segmentations.py:

- SEGM_PREFIX: the basename (without extension) of the segmentation files within the patient folders.
- SUPERVOXEL_PREFIX: the basename (without extension) of the supervoxel files within the patient folders.
- MODALITY_PREFIXES: the basenames (without extension) of the modality files within the patient folders.
    
These are defined in main_correct_segmentations.py:
    
~~~~
# Define basenames (without extension) that allow to find the correct paths
SEGM_PREFIX = 'gt' # for the segmentation path
SUPERVOXEL_PREFIX = 'supervoxels' # for the supervoxel path
MODALITY_PREFIXES = ['t1','t1c','t2','fla'] # for the modality paths
~~~~

Make sure your image exstensions are in ['.nii', '.nii.gz', '.mha']

Once the filenames are set, execute main_correct_segmentations.py to run the gui:

~~~~
python main_correct_segmentations.py
~~~~

The GUI will then,
1. ask to give the path to the folder containing all your patients, 
2. load those patients and present them to you in a drop-down list,
3. Once you click on a patient, it will allow you to press the visualize button to visualize the modality images and the segmentation found in that patient folder.
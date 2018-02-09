from tkFileDialog import askdirectory

import os
import shutil

from Tkinter import Scrollbar
from Tkinter import RIGHT
from Tkinter import Y
from Tkinter import LEFT
from ttk import Frame
from ttk import Button
from ttk import Label
from ttk import Entry
from Tkinter import Text
from Tkinter import Listbox
from Tkinter import Tk
from Tkinter import FLAT
from Tkinter import END

from ttk import Style

from my_frame import MyFrame

import visualise_volumes as vv
import help_window

#########################################################################

# Define initial path to load data from
DATA_PATH = '/home/alberts/Documents/Data/BRATS/2016_/separated_for_gui'
if not os.path.exists(DATA_PATH):
    DATA_PATH = os.environ.get('HOME')

# Define basenames (without extension) that allow to find the correct paths
SEGM_PREFIX = 'gt' # for the segmentation path
SUPERVOXEL_PREFIX = 'supervoxels' # for the supervoxel path
MODALITY_PREFIXES = ['t1','t1c','t2','fla'] # for the modality paths

#########################################################################

class SelectPaths(MyFrame):

    def __init__(self, topframe=None):

        MyFrame.__init__(self,
                         topframe=topframe)

        style = Style()
        style.theme_use('clam')

        self.patient_foler_path = ""
        self.patients = []
        self.set_title('Brain segmentation GUI')
        self.add_ui_components()

    def add_ui_components(self):

        # Creating the frames.
        self.sub_frame1 = Frame(self)
        self.sub_frame1.grid(column=0, row=0)

        sub_frame2 = Frame(self)
        sub_frame2.grid(column=0, row=1)

        sub_frame3 = Frame(self)
        sub_frame3.grid(column=0, row=2)

        sub_frame21 = Frame(sub_frame2)
        sub_frame21.grid(column=0, row=0)

        sub_frame22 = Frame(sub_frame2)
        sub_frame22.grid(padx=20, column=1, row=0)
        
        sub_frame221 = Frame(sub_frame22)
        sub_frame221.grid(row=1, column=0)


        # Creating the top-menu buttons.
        self.visualise_button = Button(self.sub_frame1,
                                       text="Visualise",
                                       command=self.start_visualisation)
        self.visualise_button.grid(row=0, column=1)

        self.help_button = Button(self.sub_frame1,
                                  text="Help",
                                  command=self.open_help)
        self.help_button.grid(row=0, column=2)

        # Creating the select modality path.
        self.modality_label = Label(sub_frame21,
                                    text="Path to patient folders",
                                    relief=FLAT)
        self.modality_label.grid(row=1, column=1)
        self.modality_path_entry = Entry(sub_frame21)
        self.modality_path_entry.grid(row=2, column=1)
        #self.modality_path_entry.set(self.patient_folder_path)

        self.modality_path_button = Button(sub_frame21,
                                           text="Choose",
                                           command=self.choose_directory_and_import)
        self.modality_path_button.grid(row=2, column=2)

        # Creating the patients listbox.
        self.label_patients = Label(sub_frame22, text="Patients")
        self.label_patients.grid(row=0, column=0)

        self.listbox_patients = Listbox(sub_frame221,
                                        selectmode='multiple',
                                        width=50,
                                        height=10)

        self.listbox_patients.pack(side=LEFT, fill=Y)
        #self.listbox_patients.grid(row=1, column=0)
        self.listbox_patients.bind("<Button-1>", self.listbox_changed)

        self.scrollbar = Scrollbar(sub_frame221)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        
        # attach listbox to scrollbar
        self.listbox_patients.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox_patients.yview)
        # Creating the status console.
        self.status_text = Text(sub_frame3, height=5)
        self.status_text.grid(column=0, row=0)
        self.status_text.tag_configure('title', justify='center', font="Arial 10 bold")
        self.status_text.tag_configure('entry', justify='left', font="Arial 9")
        self.status_text.insert(END, 'Status Console', 'title')
        self.status_text_entry_number = 1
        self.status_text.configure(state='disabled')


# ***** EVENTS - START********************************

    def start_visualisation(self):
        """ Launch visualisation module. 
        Linked to self.visualise_button (Button). """

        patient_path = os.path.join(self.patient_folder_path,
                                    'processed_'+self.patients[0])
    
        segmentation_path = os.path.join(patient_path,
                                         SEGM_PREFIX+'_'+self.patients[0]+'.nii.gz')
            
        supervoxel_path = os.path.join(patient_path,
                                       SUPERVOXEL_PREFIX+'_'+self.patients[0]+'.nii.gz')
    
        # check if the supervoxels and the segmentation exist
        if not os.path.exists(supervoxel_path):
            supervoxel_path = None
        if not os.path.exists(segmentation_path):
            segmentation_path = None
        
        mod_paths = []
        for mod in MODALITY_PREFIXES:
            mod_paths.append(\
                    os.path.join(patient_path, 
                                 mod+'_'+self.patients[0]+'.nii.gz'))

        vis = vv.VisualVolumes(image_paths=mod_paths,
                               segm_path=segmentation_path,
                               supervoxel_id_path=supervoxel_path,
                               topframe=self.master)
        vis.tkraise()

    def listbox_changed(self, event):
        """ Add a patient upon selection in the listbox. 
        Linked to self.listbox_patients (Listbox). """

        indices = list(self.listbox_patients.curselection())
        selected_idx = self.listbox_patients.nearest(event.y)

        if selected_idx == -1:
            return

        # remove or add a patient index
        if selected_idx not in indices:
            indices.append(selected_idx)
        else:
            indices.remove(selected_idx)

        # set self.patients based on the new patient indices and enable visualisation if only one is selected.
        self.patients = []
        for idx in indices:
            self.patients.append(self.listbox_patients.get(idx).split(' ')[0])
        if len(self.patients) == 1:
            self.visualise_button['state'] = 'enabled'
        else:
            self.visualise_button['state'] = 'disabled'

    def choose_directory_and_import(self):
        """ Allow the user to select an import path. 
	    Linked to self.modality_path_button (Button), 
	    and sets self.modality_path_entry (Entry). """

        initialdir = DATA_PATH
        msg = 'Select directory containing patients'
        path = askdirectory(title=msg,
                            initialdir=initialdir)
        # update the text box.
        self.modality_path_entry.delete(0, END)
        self.modality_path_entry.insert(0, str(path))

        # Adding the modality paths after the folder is selected.
        self.patient_folder_path = self.modality_path_entry.get()
        if os.path.exists(self.patient_folder_path):
       
            patients_validation = os.listdir(self.patient_folder_path)           

            # Checking if the patient has the right modalities and importing the patient.
            for i, patient in enumerate(patients_validation):

                # Checking if the patient was already processed.
                if patient.startswith('processed_') or os.path.exists(os.path.join(self.patient_folder_path, 'processed_'+patient)):
                    print("The files of the patient "+patient+" are already copied")
                    continue

                # If everything is fine, then it continues to makign folders and copying files
                # Copying the files into the new folder.
                valid = self._convert_and_copy_files(patient)
                if not valid:
                    patients_validation[i] = None

            # We make a list of patients with only ids for the listbox.
            valid_patients = [p for p in patients_validation if p is not None]
            self.list_existing_patients(valid_patients)

    def _convert_and_copy_files(self, patient):
        """ Check if all valid files exist for this patient and return
        True if so. """

        # Getting the list of modalities for every patient.
        patient_path = os.path.join(self.patient_folder_path, patient)
        modalities = os.listdir(patient_path)

        # Look for paths
        valid_paths = {}
        prefices = [SEGM_PREFIX, SUPERVOXEL_PREFIX] + MODALITY_PREFIXES
        for prefix in prefices:
            candidates = [modality \
                          for modality in modalities \
                          if modality.startswith(prefix+'.')]
            if len(candidates) != 1:
                err = '%s file not identified. Look for ambiguities in %s.' \
                        % (prefix, patient_path)
                print (err)
                return False
            modality = candidates[0]
            
            if not any([modality.endswith(ext) 
                        for ext in ['.mha', '.nii', '.nii.gz']]):
                err = "Image format not recognized: %s. In %s" \
                            % (modality, patient_path)
                print (err)
                return False
            
            valid_paths[prefix] = modality
            
        # Creating a processed patient folder.
        os.mkdir(os.path.join(self.patient_folder_path, 'processed_'+patient))
        for prefix, basename in valid_paths.iteritems(): 
            shutil.copyfile(os.path.join(self.patient_folder_path,
                                         patient,
                                         basename),
                            os.path.join(self.patient_folder_path,
                                         'processed_'+patient,
                                         prefix+'_'+patient+'.nii.gz'))
        return True
            
    def open_help(self):
        
        self.help_window = help_window.HelpWindow()
        self.help_window.tkraise()
            
# ***** EVENTS - END***************************

    def list_existing_patients(self, patients=None):
        print("Importing existing patients")
        # We make a list of patients with only ids for the listbox.
        
        if patients is None:
            patients = os.listdir(self.patient_folder_path)      
        self.patients = []
        for patient in patients:       
            if not patient.startswith('processed_'):
                self.patients.append(patient)
        self.patients.sort()
        self.populate_patient_listbox(self.patients)

        if self.listbox_patients.size() > 0:
            self.listbox_patients.selection_set(0)
            
        self.status_text.configure(state='normal')
        self.status_text.insert(END, '\n'+str(self.status_text_entry_number)+'- Patients are imported.', 'entry')
        self.status_text_entry_number += 1
        self.status_text.insert(END, '\n'+str(self.status_text_entry_number)+'- Please select a patient to proceed', 'entry')
        self.status_text_entry_number += 1
        self.status_text.configure(state='disabled')            

    def populate_patient_listbox(self, patients):

        self.listbox_patients.delete(0, END)
        for patient in patients:
            patient_path = os.path.join(self.patient_folder_path,
                                             'processed_'+patient)

            #check if a given patient has a label
            if os.path.exists(os.path.join(patient_path,
                                           'corrected_'+SEGM_PREFIX+'_'+patient+'.nii.gz')):
                patient = patient + ' - segmentation corrected'
            if os.path.exists(os.path.join(patient_path,
                                           patient+'_mask.nii.gz')):
                patient = patient + ' - preprocessed'
            if os.path.exists(os.path.join(patient_path,
                                           'post_results')):
                patient = patient + ', segmented'
            self.listbox_patients.insert(END, patient)

if __name__ == "__main__":

    tk_window = Tk()
    select_paths = SelectPaths(topframe=tk_window)
    select_paths.start()
    tk_window.withdraw()

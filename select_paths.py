from tkFileDialog import askopenfilename
from tkFileDialog import askdirectory

import os
import threading
import shutil

from ttk import Frame
from ttk import Button
from ttk import Label
from ttk import Entry
from Tkinter import Text
from Tkinter import Listbox
from Tkinter import Tk
from Tkinter import DISABLED
from Tkinter import FLAT
from Tkinter import HORIZONTAL
from Tkinter import END

from ttk import Style
from ttk import Progressbar

from my_frame import MyFrame

from skull_stripping import skull

#Three cascade steps in the tumor segmentation method.
from segmentation import supervoxel_initializer
from segmentation import em_segmenter
from segmentation import supervoxel_postprocessor

import visualise_volumes
import help_window

from segmentation.utilities import own_itk as oitk

class SelectPaths(MyFrame):

    def __init__(self, topframe=None):

        MyFrame.__init__(self,
                         topframe=topframe)

        style = Style()
        style.theme_use('clam')

        self.patient_foler_path = ""
        self.mod_paths = []
        self.patients = []
        self.set_title('Brain segmentation GUI')
        self.add_ui_components()
        #self.import_existing_patients()

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


	# Creating the top-menu buttons.
        self.preprocess_button = Button(self.sub_frame1, text="Preprocess", command=self.preprocess)
        self.preprocess_button.grid(row=0, column=1)

        self.segment_button = Button(self.sub_frame1,
                                     text="Segment",
                                     state=DISABLED,
                                     command=self.segment)

        self.segment_button.grid(row=0, column=2)

        self.visualise_button = Button(self.sub_frame1,
                                       text="Visualise",
                                       command=self.start_visualisation)
        self.visualise_button.grid(row=0, column=3)

        self.help_button = Button(self.sub_frame1,
                                  text="Help",
                                  command=self.open_help)

        self.help_button.grid(row=0, column=4)

        if len(self.mod_paths) == 0:
            self.preprocess_button['state'] = 'disabled'
            self.visualise_button['state'] = 'disabled'


	# Creating the select modality path.
        self.modality_label = Label(sub_frame21,
                                    text="Modality Paths",
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

        self.listbox_patients = Listbox(sub_frame22,
                                        selectmode='multiple',
                                        width=35,
                                        height=10)

        self.listbox_patients.grid(row=1, column=0)
        self.listbox_patients.bind("<Button-1>", self.listbox_changed)


        # Creating the status console.
        self.status_text = Text(sub_frame3, height=5)
        self.status_text.grid(column=0, row=0)
        self.status_text.tag_configure('title', justify='center', font="Arial 10 bold")
        self.status_text.tag_configure('entry', justify='left', font="Arial 9")
        self.status_text.insert(END, 'Status Console', 'title')
        self.status_text_entry_number = 1
        self.status_text.configure(state='disabled')


# ***** EVENTS - START********************************

    def preprocess(self):

        self.progress_label = Label(self.sub_frame1,
                                    text="Skull stripping: ",
                                    relief=FLAT)

        self.progress_label.grid(column=5, row=0)

        self.progress = Progressbar(self.sub_frame1,
                                        orient=HORIZONTAL,
                                        length=100,
                                        mode='determinate')

        self.progress.grid(column=6, row=0, sticky=['w', 'e'])
        self.parallel_thread_skull_strip()

    def segment(self):
        self.progress_label = Label(self.sub_frame1,
                                    text = "Segmenting: ",
                                    relief=FLAT)

        self.progress_label.grid(column=5, row=0)

        self.progress = Progressbar(self.sub_frame1,
                                        orient=HORIZONTAL,
                                        length=100,
                                        mode='determinate')

        self.progress.grid(column=6, row=0, sticky=['w', 'e'])
        self.parallel_thread_segment()

    def start_visualisation(self):

        #get the patient
        preprocessed_path = os.path.join(os.getcwd(),
                                         'temp',
                                         'processed',
                                         self.patients[0],
                                         'preprocessed')

        segmentation_path = os.path.join(preprocessed_path,
                                         'post_results',
                                         'hard_map.nii')

        supervoxel_path = os.path.join(preprocessed_path,
                                       'init_supervoxels.nii.gz')

        # check if the supervoxels and the segmentation exist
        if not os.path.exists(supervoxel_path):
            supervoxel_path = None
        if not os.path.exists(segmentation_path):
            segmentation_path = None


        if os.path.exists(os.path.join(preprocessed_path,
                                       self.patients[0]+'_FLAIR_stripped_reg.nii')):
            self.mod_paths = []
            self.mod_paths.append(os.path.join(preprocessed_path,
                                               self.patients[0]+'_FLAIR_stripped_reg.nii'))

            self.mod_paths.append(os.path.join(preprocessed_path,
                                               self.patients[0]+'_T1_stripped_reg.nii'))
            self.mod_paths.append(os.path.join(preprocessed_path,
                                               self.patients[0]+'_T1c_stripped_reg.nii'))
            self.mod_paths.append(os.path.join(preprocessed_path,
                                               self.patients[0]+'_T2_stripped_reg.nii'))


        vis = visualise_volumes.VisualVolumes(image_paths=self.mod_paths,
                                              segm_path=segmentation_path,
                                              supervoxel_id_path=supervoxel_path,
                                              topframe=self.master)
        vis.tkraise()

    def listbox_changed(self, event):

        indices = list(self.listbox_patients.curselection())
        selected_idx = self.listbox_patients.nearest(event.y)

        if selected_idx == -1:
            return

        if selected_idx not in indices:
            indices.append(selected_idx)
        else:
            indices.remove(selected_idx)
        self.patients = []

        for idx in indices:
            self.patients.append(self.listbox_patients.get(idx).split(' ')[0])
        if len(self.patients) == 1:
            self.visualise_button['state'] = 'enabled'
            list_modalities = os.listdir(os.path.join(self.patient_folder_path,
                                                      'processed_'+self.patients[0]))
            self.mod_paths = []
            for modality in list_modalities:
                self.mod_paths.append(os.path.join(self.patient_folder_path,
                                                   'processed_'+self.patients[0],
                                                   modality))
        else:
            self.visualise_button['state'] = 'disabled'

        flag_preprocess = False
        flag_segment = False
        if len(self.patients) > 0:

            for idx in indices:
                patient_label = self.listbox_patients.get(idx)
                if 'preprocessed' not in patient_label and 'segmented' not in patient_label:
                    flag_preprocess = True
                if 'preprocessed' in patient_label and 'segmented' not in patient_label:
                    flag_segment = True

        if flag_preprocess:
            self.preprocess_button['state'] = 'enabled'
        else:
            self.preprocess_button['state'] = 'disabled'
        if flag_segment:
            self.segment_button['state'] = 'enabled'
        else:
            self.segment_button['state'] = 'disabled'

    def open_help(self):
        self.help_window = help_window.HelpWindow()
        self.help_window.tkraise()

    def choose_directory_and_import(self):
        initialdir = os.environ.get('HOME')
        msg = 'Select directory containing patients'
        path = askdirectory(title=msg,
                            initialdir=initialdir)
        # update the text box.
        self.modality_path_entry.delete(0, END)
        self.modality_path_entry.insert(0, str(path))

        # Adding the modality paths after the folder is selected.
        self.patient_folder_path = self.modality_path_entry.get()

        self.mod_paths = []
        if os.path.exists(self.patient_folder_path):
       
            patients_validation = os.listdir(self.patient_folder_path)           

            # Checking if the patient has the right modalities and importing the patient.
            for patient in patients_validation:

                # Checking if the patient was already processed.
                if patient.startswith('processed_') or os.path.exists(os.path.join(self.patient_folder_path, 'processed_'+patient)):
                    print("The files of the patient "+patient+" are already copied")
                    continue

                modalities = os.listdir(os.path.join(self.patient_folder_path, patient))

                # Checking if the patient has the right modalities.
                if not ('T1c' in modalities and 'T1' in modalities and 'T2' in modalities and 'FLAIR' in modalities):                    
                    print("Wrong modalities for patient "+patient)
                    continue

                # If everything is fine, then it continues to makign folders and copying files
                self.mod_paths.append(os.path.join(self.patient_folder_path, patient))
                
                
                # Creating a processed patient folder.
            	os.mkdir(os.path.join(self.patient_folder_path, 'processed_'+patient))

                # Copying the files into the new folder.
                self.convert_and_copy_files(patient)


            # We make a list of patients with only ids for the listbox.
            self.patients = []
            for patient in patients_validation:       
                if not patient.startswith('processed_'):
                    self.patients.append(patient)
            self.populate_patient_listbox(self.patients)


            self.status_text.configure(state='normal')
            self.status_text.insert(END, '\n'+str(self.status_text_entry_number)+'- Patients are imported.', 'entry')
            self.status_text_entry_number += 1
            self.status_text.insert(END, '\n'+str(self.status_text_entry_number)+'- Please select a patient to proceed', 'entry')
            self.status_text_entry_number += 1
            self.status_text.configure(state='disabled')


# ***** EVENTS - END***************************


# ***** PARALLEL THREADS _ START ********************************
    def parallel_thread_skull_strip(self):
        def parallel_thread_skull_strip_func():
            patients = list(self.patients)
            self.progress.start()
            for patient in patients:
                patient_path = os.path.join(self.patient_folder_path,
                                            'processed_'+patient)
                modalities = os.listdir(patient_path)

                skull_stripper = skull.SkullStripper(output_folder=patient_path,
                                                     id_folder=patient)
                self.mod_paths = []
                
                for modality in modalities:
                    self.mod_paths.append(os.path.join(patient_path,
                                                       modality))

                skull_stripper.strip_skull(self.mod_paths, 0)

            self.progress.stop()
            self.progress.grid_forget()
            self.progress_label.grid_forget()
            self.status_text.configure(state='normal')
            self.status_text.insert(END,
                                    '\n'+str(self.status_text_entry_number)+'- Preprocessing is finished.',
                                    'entry')
            self.status_text_entry_number += 1
            self.status_text.configure(state='disabled')

            self.import_existing_patients()
            #tkMessageBox.showinfo("Status", "Skull stripping finished.")
        threading.Thread(target=parallel_thread_skull_strip_func).start()

    def parallel_thread_segment(self):
        def parallel_thread_segment_func():
            patients = list(self.patients)
            self.progress.start()
            for patient in patients:
                patient_path = os.path.join(self.patient_folder_path,
                                            'processed_'+patient)

                if os.path.exists(os.path.join(patient_path,
                                               'post_results')):
                    continue
                modalities = os.listdir(patient_path)

                #Step 1: segmentation preprocessing - supervoxel initializer
                print("Step 1 started")

                mod_maps = {'t1':os.path.join(patient_path,
                                              'stripped_T1_'+patient+'.nii.gz'),
                            't1c':os.path.join(patient_path,
                                               'stripped_T1c_'+patient+'.nii.gz'),
                            't2':os.path.join(patient_path,
                                              'stripped_T2_'+patient+'.nii.gz'),
                            'flair':os.path.join(patient_path,
                                                 'stripped_FLAIR_'+patient+'.nii.gz')}

                mask = os.path.join(patient_path,
                                    patient+'_mask.nii.gz')

                # load supervoxels if they exist, and segment
                supervoxel_path = os.path.join(patient_path,
                                               patient+'_init_supervoxels.nii.gz')
                loaded_supervoxels = None
                if os.path.exists(supervoxel_path):
                    loaded_supervoxels = oitk.get_itk_array(supervoxel_path)

                # make the mask binary
                mask = oitk.get_itk_array(mask) > 0
                mask = mask.astype(int)

                soft_maps, supervoxels = supervoxel_initializer.get_segmentation(mod_maps, mask, loaded_supervoxels)
                proto = oitk.get_itk_image(mod_maps['t1'])
                if loaded_supervoxels is None:
                    image = oitk.make_itk_image(supervoxels,
                                             proto,
                                             verbose=False)
                    oitk.write_itk_image(image, supervoxel_path)
                for label, prob_map in soft_maps.iteritems():
                    dirname = os.path.join(patient_path,
                                           'init_results')
                    if not os.path.exists(dirname):
                        os.mkdir(dirname)
                    path = os.path.join(dirname, label+'.nii.gz')
                    image = oitk.make_itk_image(soft_maps[label], proto, verbose=False)
                    oitk.write_itk_image(image, path)

                #Step 2: segmentation
                print("Step 2 started")
                # assemble the paths for your patient
                this_dir = os.path.dirname(os.path.realpath(__file__))

                tissue_maps = {'gm':os.path.join(patient_path, patient+'_gm.nii.gz'),
                               'wm':os.path.join(patient_path, patient+'_wm.nii.gz'),
                               'csf':os.path.join(patient_path, patient+'_csf.nii.gz')}
                init_maps = {}

                tumors = ['enhanced', 'nonactive', 'necrotic', 'edema']
                tissues = ['gm', 'wm', 'csf']
                em_labels = tissues + tumors
                for label in em_labels:
                    init_maps[label] = os.path.join(patient_path, 'init_results', label+'.nii.gz')

                save_dir = os.path.join(patient_path, 'em_results')
                em_segmenter.get_segmentation(mod_maps, tissue_maps, init_maps, mask, save_dir=save_dir)
                #Step 3: segmentation postprocesing - supervoxel
                print("Step 3 started")

                em_maps = {}
                em_path = os.path.join(patient_path, 'em_results', 'to_replace.nii.gz')
                for label in em_labels:
                    em_maps[label] = oitk.get_itk_array(em_path.replace('to_replace', label))
                em_maps_list = []
                em_maps_list.append(em_maps['gm']+em_maps['wm']+em_maps['csf'])
                em_maps_list.append(em_maps['enhanced'])
                em_maps_list.append(em_maps['nonactive'] + em_maps['necrotic'])
                em_maps_list.append(em_maps['edema'])
                soft_maps, hard_map, supervoxels = supervoxel_postprocessor.get_segmentation(mod_maps,
                                          em_maps_list,
                                          mask,
                                          loaded_supervoxels)
                proto = oitk.get_itk_image(mod_maps['t1'])
                if loaded_supervoxels is None:
                    image = oitk.make_itk_image(supervoxels, proto, verbose=False)
                    oitk.write_itk_image(image, supervoxel_path)
                dirname = os.path.join(preprocessed_path, 'post_results')
                if not os.path.exists(dirname):
                    os.mkdir(dirname)
                for label, prob_map in soft_maps.iteritems():
                    path = os.path.join(dirname, label+'.nii.gz')
                    image = oitk.make_itk_image(soft_maps[label], proto, verbose=False)
                    oitk.write_itk_image(image, path)
                path = os.path.join(dirname, 'hard_map.nii.gz')
                image = oitk.make_itk_image(hard_map, proto, verbose=False)
                oitk.write_itk_image(image, path)
                print("Segmentation finished")


            self.progress.stop()
            self.progress.grid_forget()
            self.progress_label.grid_forget()
            self.status_text.configure(state='normal')
            self.status_text.insert(END, '\n'+str(self.status_text_entry_number)+'- Segmentation is finished.', 'entry')
            self.status_text_entry_number += 1
            self.import_existing_patients()
            #tkMessageBox.showinfo("Status", "Segmentation finished.")
        threading.Thread(target=parallel_thread_segment_func).start()   

# PARALLEL THREADS - END ******************************


    def import_existing_patients(self):
        print("Importing existing patients")
        self.populate_patient_listbox(self.patients)
        if self.listbox_patients.size() > 0:
            self.listbox_patients.selection_set(0)

    def convert_and_copy_files(self, patient):

        # Getting the list of modalities for every patient.
        modalities = os.listdir(os.path.join(self.patient_folder_path,
                                             patient))

        # Checks if the patient is full of nifti files
        if modalities[0].endswith(('.nii', '.nii.gz')):

            # Copy every modality in original format.
            for modality in modalities:
                # To remove the extension.
                name_modality = modality.split('.')[0]
                shutil.copyfile(os.path.join(self.patient_folder_path,
                                             patient,
                                             modality),
                                os.path.join(self.patient_folder_path,
                                             'processed_'+patient,
                                             name_modality+'_'+patient+'.nii.gz'))

        # Checks if the patient is full of DICOM files.
        elif '.' not in modalities:
            # Going through every modality folder with the DICOM files.
            for modality in modalities:
     
                # Converting the dicom image into a ITK one.
                itk_image = oitk.read_dicom(os.path.join(self.patient_folder_path, patient, modality), verbose=False)
                # Saving the ITK image as nifti into temp.
                oitk.write_itk_image(itk_image,os.path.join(self.patient_folder_path,
                                                            'processed_'+patient,
                                                            modality+'_'+patient+'.nii.gz'))
        else:
            print("Wrong format.")
        

    def populate_patient_listbox(self, patients):

        self.listbox_patients.delete(0, END)
        for patient in patients:
            preprocessed_path = os.path.join(self.patient_folder_path,
                                             'processed_'+patient,
                                             patient+'_mask.nii.gz')

            #check if a given patient has a label
            if os.path.exists(preprocessed_path):
                patient = patient + ' - preprocessed'
            #if os.path.exists(os.path.join(preprocessed_path,
            #                               'post_results')):
            #    patient = patient + ', segmented'
            self.listbox_patients.insert(END, patient)

if __name__ == "__main__":
    tk_window = Tk()
    select_paths = SelectPaths(topframe=tk_window)
    select_paths.start()
    tk_window.withdraw()

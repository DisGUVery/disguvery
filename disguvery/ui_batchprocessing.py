###############################################################################
#   DisGUVery: detect and analyse Giant Unilamellar Vesicles in microscopy images
#
#       Copyright (C) 2022, the DisGUVery developers
#
# This file is part of DisGUVery.
# 
# DisGUVery is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# DisGUVery is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with 
# this program. If not, see <https://www.gnu.org/licenses/>.
###############################################################################

from tkinter import ttk
import tkinter.filedialog

import os

from data_processing import ProfileIntegration

# Import custom widgets
import ui_custom_widgets as ctk
from file_handling import FileExport, FileImage
from data_processing import GeoMat
from image_processing import ImageCorrection, ImageFilters, ImageCheck
from ui_encapefficiency import EncapEfficiency
from vesicle_detection import VesicleDetection
from ui_basicmembrane import BMAsegmentation
from ui_vessizedist import VesSizePanel

class BatchPanel():

    def __init__(self, controller = None):

        # We keep track of the controller to trigger acgtions easily
        self.controller = controller
        settings_var = controller.appdata_settingsbatch

        # Initialise batch processing window
        bpanel = ctk.ControlPanel(title = 'Batch Processing')

        # Configure window layout
        bpanel.configure_layout(cols = [0,1,2], rows= [1,2,3])
        
        # Create options for preprocessing
        preLabelFrame = ttk.LabelFrame(bpanel, text = 'Pre-processing')
        filterCheckbox = ttk.Checkbutton(preLabelFrame, text = 'Filter', variable = settings_var['preprocess'][0])
        enhanceCheckbox = ttk.Checkbutton(preLabelFrame, text = 'Membrane Enhancement', variable = settings_var['preprocess'][1])

        for n, w in enumerate([filterCheckbox, enhanceCheckbox]):
            w.grid(row = n, column = 0, sticky = 'nsew', padx = 7, pady = 3)

        # Create vesicle detection options
        vesLabelFrame = ttk.LabelFrame(bpanel, text = 'Vesicle Detection')
        metLabel = ttk.Label(vesLabelFrame, text = 'Method')
        metCombobox = ttk.Combobox(vesLabelFrame, textvariable = settings_var['vesdet_method'][0], 
                                    values = settings_var['vesdet_method'][1])
        metCombobox.current(0)
        for n, w in enumerate([metLabel, metCombobox]):
            w.grid(row = 0, column = n, sticky = 'nsew', padx = 5, pady = 5)
        chFrame = ttk.Frame(vesLabelFrame)
        chFrame.grid(row = 1, column = 0, sticky = 'nsew', padx = 5, pady = 5, columnspan = 2)
        chLabel = ttk.Label(chFrame, text = 'Channel')
        chLabel.grid(row = 0, column = 0, sticky = 'nsew', padx = 5, pady = 5)
        for i in range(1,5):
            rbutton = ttk.Radiobutton(chFrame, text = i, value = i, variable=settings_var['vesdet'][0])
            rbutton.grid(row = 0, column = i, sticky = 'nsew', padx = 2, pady = 5)
        vesexportCheckbox = ttk.Checkbutton(vesLabelFrame, text = 'Export', variable=settings_var['vesdet'][1])
        vesexportCheckbox.grid(row = 2, column = 0, sticky = 'nsw', padx = 5, pady = 5)

        # Create Membrane Segmentation options
        memLabelFrame = ttk.LabelFrame(bpanel, text = 'Membrane Segmentation')
        memCheckbox = ttk.Checkbutton(memLabelFrame, text = 'Enable', variable = settings_var['membrane'][0])
        memCheckbox.grid(row = 0, column = 0, sticky = 'nsew', padx = 10, pady = 10)
        
        # Create Intensity Profiles options
        intLabelFrame = ttk.LabelFrame(bpanel, text = 'Intensity Profiles')
        ianFrame = ttk.LabelFrame(intLabelFrame, text = 'Angular')
        iradFrame = ttk.LabelFrame(intLabelFrame, text = 'Radial')
        for n, iframe in enumerate([ianFrame, iradFrame]):
            iframe.grid(row = n, column = 0, sticky = 'nsew', padx = 5, pady = 5)
        for i in range(1, 4):
            cbox = ttk.Checkbutton(ianFrame, text = f'Ch {i}', variable = settings_var['intprofiles_an'][i-1])
            cbox.grid(row = 1, column = i -1, sticky = 'nsew', padx = 2, pady = 2)
            cbox = ttk.Checkbutton(iradFrame, text = f'Ch {i}', variable = settings_var['intprofiles_rad'][i-1])
            cbox.grid(row = 1, column = i - 1, sticky = 'nsew', padx = 2, pady = 2)

        # Create metrics options
        metLabelFrame = ttk.LabelFrame(bpanel, text = 'Metrics')
        metvsizeCheckbox = ttk.Checkbutton(metLabelFrame, text = 'Vesicle Size Distribution', variable = settings_var['metrics_size'])
        metencapCheckbox = ttk.Checkbutton(metLabelFrame, text = 'Encapsulation Efficiency', variable = settings_var['metrics_encap'][0])
        for n, w in enumerate([metvsizeCheckbox, metencapCheckbox]):
            w.grid(row = n , column = 0, sticky = 'nsew', padx = 5, pady = 5, columnspan = 4)
        for n, s in enumerate(['Detection Mask', 'Refined Mask']):      
            rbutton = ttk.Radiobutton(metLabelFrame, text = s, variable = settings_var['metrics_encap'][1], value = n)
            rbutton.grid(row = n+2, column = 0, sticky = 'nswe', padx = 15, pady = 5, columnspan = 3)
        for i in range(1, 4):
            cbox = ttk.Checkbutton(metLabelFrame, text = f'Ch {i}', variable = settings_var['metrics_encap'][2][i-1])
            cbox.grid(row = n+4, column = i -1, sticky = 'nsew', padx = 2, pady = 2)
        
        # Create batch processing options
        optLabelFrame = ttk.LabelFrame(bpanel, text = 'Results Saved in ')
        folderLabel = ttk.Label(optLabelFrame, textvariable = settings_var['savedir'])
        folderButton = ttk.Button(optLabelFrame, text = 'Choose Folder', command = self.folder_save) 
        
        folderButton.grid(row = 0, column = 0, sticky = 'nsw', padx = 5, pady = 7)
        folderLabel.grid(row = 0, column = 1, sticky = 'nsew', padx = 10, pady = 7)
        
        # Buttons to test and run
        testcurrentButton = ttk.Button(bpanel, text = 'Test on Current Image', command = self.test_current)
        runButton = ttk.Button(bpanel, text = 'Run', command = self.run_all_images)
        testcurrentButton.grid(row = 0, column = 1, sticky = 'nse', padx = 10, pady = 5)
        runButton.grid(row = 0, column = 0, sticky = 'nsw', padx = 10, pady = 5)

        # Place close button
        bpanel.closeButton.grid(row = 0, column = 2, sticky = 'nse', padx = 10, pady = 5)

        # Place frames
        preLabelFrame.grid(row = 1, column = 0, sticky = 'nsew', padx = 3, pady = 2)
        optLabelFrame.grid(row = 4, column = 0, sticky = 'nsew', padx = 3, pady = 2, columnspan = 3)
        vesLabelFrame.grid(row = 1, column = 1, sticky = 'nsew', padx = 3, pady = 2, rowspan = 2)
        intLabelFrame.grid(row = 2, column = 0, sticky = 'nsew', padx = 3, pady = 2, rowspan = 2)
        memLabelFrame.grid(row = 3, column = 1, sticky = 'nsew', padx = 3, pady = 2)
        metLabelFrame.grid(row = 1, column = 2, sticky = 'nsew', padx = 3, pady = 2, rowspan = 3)
    
        # Keep track of window
        self.window = bpanel

    def folder_save(self):

        # Define default folder for saving
        curr_image = self.controller.appdata_imagesource['name']
        curr_dir = self.controller.appdata_imageinfo[curr_image]['directory']

        dir_save = tkinter.filedialog.askdirectory(initialdir = curr_dir)
        if dir_save:
            self.controller.appdata_settingsbatch['savedir'].set(dir_save)

    def run_all_images(self):

        controller = self.controller

        # Get the image name for the dictionary of imageinfo
        for img_name in controller.appdata_imageinfo.keys():
            img_dir = controller.appdata_imageinfo[img_name]['directory']
            img_ext = controller.appdata_imageinfo[img_name]['extension']
            filename = os.path.join(os.path.normpath(img_dir), f'{img_name}.{img_ext}')
            print(f'Working with image {filename} ------------')
            
            # Read the image
            img_info, img_n, source_image = FileImage.open(filename, verbose = False)

            # Settings batch processing
            settings_batch = controller.appdata_settingsbatch
            det_results, bma_results, profiles_results, encap_results = BatchRun.run(controller, source_image, settings_batch,
                                                                    display_results = False)

            # Export the desired results
            if settings_batch['vesdet'][1].get() == 1 and det_results is not None:
                # Export vesicle detection results
                filename = os.path.join(settings_batch['savedir'].get(), f'{img_name}_detected_vesicles.csv')
                FileExport.vesicle_detection(filename, det_results)
            if profiles_results is not None:
                # Export intensity profiles
                filename = os.path.join(settings_batch['savedir'].get(), f'{img_name}_results.csv')
                FileExport.intensity_profiles(filename, profiles_results)
            if encap_results is not None:
                for k, v in encap_results.items():
                    filename = os.path.join(settings_batch['savedir'].get(), f'{img_name}_encapresults_{k}')
                    FileExport.encapsulation_results(filename, v[0], v[1])
            # Assign the detection results to the current image
            controller.appdata_resultsvesdet[img_name] = det_results

        # Run vesicle size distribution if required
        if settings_batch['metrics_size'].get() == 1:
            # Set the method for calculation for all the images
            controller.appdata_settingsvessizedist['input_data'].set(1)
            # Open the window 
            controller.gw_vessizedist = VesSizePanel(controller)
            controller.gw_vessizedist.compute_histogram(overwrite_minmax = True)

    def test_current(self):

        controller = self.controller

        # Image to work on is the curret image
        mat_image = controller.appdata_imagecurrent
        img_name = controller.appdata_imagesource['name']
        current_channel = controller.appdata_channels['current'].get()
        # Settings batch processing
        settings_batch = controller.appdata_settingsbatch

        det_results, bma_results, profiles_results, encap_results = BatchRun.run(controller, mat_image, settings_batch)

        # Export the desired results
        if settings_batch['vesdet'][1].get() == 1 and det_results is not None:
            # Export vesicle detection results
            filename = os.path.join(settings_batch['savedir'].get(), f'{img_name}_detected_vesicles.csv')
            FileExport.vesicle_detection(filename, det_results)
        if profiles_results is not None:
            # Export intensity profiles
            filename = os.path.join(settings_batch['savedir'].get(), f'{img_name}_results.csv')
            FileExport.intensity_profiles(filename, profiles_results)
        if encap_results is not None:
            for k, v in encap_results.items():
                filename = os.path.join(settings_batch['savedir'].get(), f'{img_name}_encapresults_{k}')
                FileExport.encapsulation_results(filename, v[0], v[1])
        # Assign the detection results to the current image
        controller.appdata_resultsvesdet[img_name] = det_results


        # Run vesicle size distribution if required
        if settings_batch['metrics_size'].get() == 1:
            # Set the method for calculation as a single image
            controller.appdata_settingsvessizedist['input_data'].set(0)
            # Open the window 
            controller.gw_vessizedist = VesSizePanel(controller)
            controller.gw_vessizedist.compute_histogram(overwrite_minmax = True)


class BatchRun(): 
                  
    def run(controller, mat_image, settings_batch, display_results = True): 

        # Get vesicle detection method
        det_method = settings_batch['vesdet_method'][0].get().lower()

        # Preprocessing (enhancement)
        enhance_type = [False, False]
        if settings_batch['preprocess'][0].get() == 1: enhance_type[0] = True
        if settings_batch['preprocess'][1].get() == 1: enhance_type[1] = True

        if True in enhance_type:
            print('Image pre-processing...')
            enhanced_image = BatchRun.enhancement(mat_image, controller.appdata_settingsenhance, 
                                            enhance_type, det_method)
        else:
            enhanced_image = mat_image.copy()

        if display_results is True:
            controller.gw_maindisplay.clear_showimage(enhanced_image)

        # Vesicle detection. This step is mandatory
        # Set the current channel according to chosen option
        vesdet_channel = int(settings_batch['vesdet'][0].get())
        controller.appdata_channels['current'].set(vesdet_channel)
        ch_image = ImageCheck.single_channel(enhanced_image, vesdet_channel)
        
        # If the method is template, retrieve the template image
        if 'template' in det_method:
            template_image = controller.appdata_templateimage
        else: 
            template_image = None
        # Run the vesicle detection
        print('Detecting vesicles...')
        det_results = BatchRun.vesicledet(ch_image, det_method, controller.appdata_settingsvesdet, template_image)
        if det_results is not None:
            results_forint = det_results
            # Show the detection results
            if 'hough' in det_method: det_object = 'circle'
            else: det_object = 'box'
            if display_results is True:
                controller.gw_maindisplay.clear_showobject([det_object, det_results['rois']], label_old = 'all')
            # Set current channel as the membrane channel
            if 'membrane' not in controller.appdata_channels.values():
                controller.appdata_channels[vesdet_channel].set('membrane')
        # Run the membrane segmentation
        if settings_batch['membrane'][0].get() == 1:
            settings_bma = controller.appdata_settingsbma
            if 'hough' in det_method:
                offset_box = 0
            else:
                offset_box = int(settings_bma['offset'][1].get())
            rois_in, rois_out = BMAsegmentation.run(det_results, controller.appdata_settingsbma, offset_box)
            results_forint = bma_results =  BMAsegmentation.combine_rois(rois_in, rois_out)
            # Show the results
            if display_results is True:
                controller.gw_maindisplay.clear_showobject(['circle',  rois_in], 
                                                        label_old = 'bma', label = 'bma',
                                                        edgecolor = 'skyblue',
                                                        textcolor = 'none')
                controller.gw_maindisplay.clear_showobject(['circle', rois_out], 
                                                        label_old = '', label = 'bma',
                                                        edgecolor = 'steelblue',
                                                        textcolor = 'none')
        else: bma_results = None

        # Run the intensity profile computation. Input image is the raw image
        intan_set = controller.appdata_settingsbatch['intprofiles_an']
        intrad_set = controller.appdata_settingsbatch['intprofiles_rad']
        intan_channels = [i+1 for i,x in enumerate(intan_set) if x.get() == 1]
        intrad_channels = [i+1 for i,x in enumerate(intrad_set) if x.get() == 1]
        
        # Settings variable
        settings_int = controller.appdata_settingsiprofile
        
        # Check which profile computation to run. Initialise variables
        angular_profiles_all, radial_profiles_all = None, None
        if intan_channels:
            # Run angular integration
            print('Computing angular intensity profiles...')
            angular_profiles_all = BatchRun.anprofiles(mat_image, len(det_results['rois']), results_forint, 
                                                    intan_channels, settings_int,
                                                    controller.appdata_channels)
        if intrad_channels:
            # Run radial integration
            print('Computing radial intensity profiles...')
            radial_profiles_all = BatchRun.radprofiles(mat_image, len(det_results['rois']), results_forint, 
                                                    intrad_channels, settings_int)
        if None not in [angular_profiles_all, radial_profiles_all]:
            profiles_results = {}
            try: 
                keys_ves = angular_profiles_all.keys()
            except AttributeError:
                keys_ves = radial_profiles_all.keys()
            for ikey in keys_ves:
                profiles_results[ikey] = {'angular': angular_profiles_all.get(ikey, None),
                                        'radial': radial_profiles_all.get(ikey, None)}
        else: profiles_results = None

        # Run the encapsulation efficiency analysis
        if settings_batch['metrics_encap'][0].get() == 1:
            print('Computing Encapsulation Efficiency')
            if settings_batch['metrics_encap'][1].get() == 0:
                mask_source = 'detection'
            else:
                mask_source = 'refined'
            # Get the settings for encapsulation refined mask
            encap_settings = controller.appdata_settingsencap
            # Get the membrane channel
            ch_membrane = [ich for ich in [1,2,3,4] if 'membrane' in controller.appdata_channels[ich].get()][0]
            # get the  channels to run encapsulation at
            ch_encap = [ich+1 for ich, ch in enumerate(settings_batch['metrics_encap'][2]) if ch.get() == 1]
            # Get background correction
            bg_corr = encap_settings['bg_correction'].get()
            # Get the labels mask. The detection is to be done on the enhanced image
            m_image = ImageCheck.single_channel(enhanced_image, ch_membrane)
            mask_labels = BatchRun.encapsulation_mask(m_image, mask_source, det_results, encap_settings)
            encap_results = BatchRun.encapsulation(mat_image, mask_labels, ch_encap, bg_corr)
            # Visualize mask used
            if display_results is True:
                controller.gw_maindisplay.overlay_mask(mask_labels, alpha = 0.3, remove_old = True)
        else: encap_results = None

        # Return the detection results
        return det_results, bma_results, profiles_results, encap_results

    def enhancement(input_image, settings_enhance, enhance_type, det_method = None):

        # For smoothing and enhancement, we take the full image
        # enhance_type = [smooth, enhance], Boolean

        # Update enhancement settings based on detection method
        if len(settings_enhance['current'][1].get()) < 1:
            method_key = [x for x in settings_enhance.keys() if x in det_method]
            settings_enhance['current'][0].set(method_key[0])
            settings_enhance['current'][1].set(str(settings_enhance[method_key[0]][0]))
            settings_enhance['current'][2].set(str(settings_enhance[method_key[0]][1]))

        if enhance_type[0] is True:
            # Get the filter size for smoothing
            filter_size = int(settings_enhance['current'][1].get())
            # Check that filter size is odd, and force it if it's not
            filter_size = ImageFilters.check_filtersize(filter_size)

            # Smooth image
            smoothed_image = ImageFilters.smooth(input_image, filter_size)
        else:
            smoothed_image = input_image.copy()

        if enhance_type[1] is True:
            # Get the filter size for enhancing
            filter_size = int(settings_enhance['current'][2].get())
            # Check that filter size is off, and force it if it's not
            filter_size = ImageFilters.check_filtersize(filter_size)

            # Enhance image
            enhanced_image = ImageFilters.enhance(smoothed_image, filter_size)
        else:
            enhanced_image = smoothed_image

        # Return the output image
        return enhanced_image

    def vesicledet(input_image, det_method, settings_det, template_image = None):

        # Initialise mask_regions variable, used only in floodfill
        mask_regions = None
        if 'hough' in det_method:
            # Run hough detection
            det_vesicles = VesicleDetection.hough(input_image, settings_det)
        elif 'template' in det_method:
            # Run Template Matching. There needs to be a template image!
            if template_image is None:
                print('ERROR: no template image found, set or load a template first!')
                det_vesicles = None
            else:
                det_vesicles = VesicleDetection.template(input_image, template_image, settings_det)
        else:
            # Run Floodfill detection
            det_vesicles, mask_regions = VesicleDetection.floodfill(input_image, settings_det)        

        if det_vesicles is not None:
            # Format results accordingly
            det_results = VesicleDetection.save_results(det_vesicles, det_method.split()[0], mask_regions)
        else:
            print('No vesicles were detected with current method and settings')
            det_results = None

        return det_results
   
    def anprofiles(input_image, nvesicles, det_results, ch_toint, settings_int, appdata_channels):

        # Get normalisation option. Only intensity normalisation is valid here
        norm_int = bool(settings_int['int_norm'].get())
        #  Get angular interval
        dtheta = int(settings_int['angular_profile'][1].get())

        # Run the computation for all the vesicles.
        # Initialise variable to store the results
        all_profiles = {}
        # Compute for each desired channel
        for ic in ch_toint:
            # Get the type of structure labeled with the channel. If membrane, apply rlim
            if 'membrane' in appdata_channels[ic].get(): 
                rlim_channel = True
            else:
                rlim_channel = None
            # Get the image from the corresponding channel
            mat_image = ImageCheck.single_channel(input_image, ic)
            # Correct the background intensity for the whole image, if required
            bg_corr = settings_int['bg_corr'][ic-1].get()
            if 'Image' in bg_corr: 
                mat_image = ImageCorrection.substract_background(mat_image.astype('float16'), corr_type = bg_corr)

            for ivesicle in range(nvesicles):
                # Get bounding box
                image_bbox, bbox_center, rlim_results = BatchRun.bbox_profiles(mat_image, det_results, int(ivesicle))
                # Set limits to compute segmented membrane radius
                if rlim_channel is True:
                    rlim_channel = rlim_results
               
                # Correct background intensity for the ROI, if required
                if 'ROI' in bg_corr:
                    image_bbox = ImageCorrection.substract_background(image_bbox.astype('float16'), corr_type = bg_corr)
                # Compute angular profiles
                angular_profiles, mean_radius, _ = ProfileIntegration.angular(image_bbox, bbox_center[0:2], dtheta,
                                                                            rlim = rlim_channel, 
                                                                            norm = norm_int)
                s_vesicle = f'ves {ivesicle + 1}'
                if s_vesicle not in all_profiles.keys():
                    all_profiles[s_vesicle] = {'mean radius': mean_radius}
                all_profiles[f'ves {ivesicle + 1}'][f'ch {ic}'] =  angular_profiles
                
        return all_profiles

    def radprofiles(input_image, nvesicles, det_results, ch_toint, settings_int):

        # Get normalisation options. Both intensity and radial normalisation are valid
        norm_int = bool(settings_int['int_norm'].get())
        norm_rad = bool(settings_int['rad_norm'].get())
        # Get radial interval
        dr = int(settings_int['radial_profile'][1].get()) 

        # Run the computation for all the vesicles. 
        # Initialise variable to store the results
        all_profiles = {}

        # Compute for each desired channel
        for ic in ch_toint:
            # Get the image from the corresponding channel
            mat_image = ImageCheck.single_channel(input_image, ic)
            # Correct the background intensity for the whole image, if required
            bg_corr = settings_int['bg_corr'][ic-1].get()
            if 'Image' in bg_corr: 
                mat_image = ImageCorrection.substract_background(mat_image.astype('float16'), corr_type = bg_corr)
            for ivesicle in range(nvesicles):
                # Get bounding box
                image_bbox, bbox_center, rlim_results = BatchRun.bbox_profiles(mat_image, det_results, int(ivesicle))
                
                # Correct background intensity for the ROI, if required
                if 'ROI' in bg_corr:
                    image_bbox = ImageCorrection.substract_background(image_bbox.astype('float16'), corr_type = bg_corr)
                # Compute the radial profiles
                radial_profiles, found_error = ProfileIntegration.radial(image_bbox, bbox_center[0:2], dr, 
                                                                    norm = norm_int)
                # If required, normalise the radius
                if norm_rad is True:
                    radial_profiles[:,0] /= bbox_center[-1]
                
                s_vesicle = f'ves {ivesicle + 1}'
                if s_vesicle not in all_profiles.keys():
                    all_profiles[s_vesicle] = { }
                all_profiles[f'ves {ivesicle + 1}'][f'ch {ic}'] =  radial_profiles

        return all_profiles

    def bbox_profiles(mat_image, det_results, ivesicle):

        # Get the bounding box for the vesicles in the intensity profiles computation

        # The detection results will be a dictionary for the output of vesicle detection
        if isinstance(det_results, dict):
            [xc, yc, r] = det_results['rois'][ivesicle][:3]
            if 'hough' not in det_results['method']:
                r /= 2
            rlim_results = None
        else:
            [xc, yc] = det_results[ivesicle,[0,1]]
            r = det_results[ivesicle, 3]
            rlim_results = [det_results[ivesicle, 2], r]

        # Set bounding box coordinates and center
        x1, x2 = int(xc - r - 5), int(xc + r + 5)
        y1, y2 = int(yc - r - 5), int(yc + r + 5)
        bbox_center = [int(xc-x1), int(yc-y1), r]

        # Get the image only to the bounding box of the detected vesicle
        image_bbox = mat_image[y1:y2, x1:x2]

        return image_bbox, bbox_center, rlim_results
    
    def encapsulation_mask(input_image, mask_source, det_results, det_settings):

        if mask_source == 'detection':
            if det_results['method'] == 'hough': half_r = False
            else: half_r = True
            try: 
                mask_all = det_results['mask_rois']
            except KeyError:
                mask_all = GeoMat.mask_contours(det_results['rois'], input_image.shape[0:2], half_r)
        else:
            # Get the image from the membrane channel
            mask_all = EncapEfficiency.mask_refined(input_image, det_results['rois'], 
                                        float(det_settings['flood_th'].get()),
                                        det_settings['flood_minarea'])

        mask_labels = mask_all.astype(int)

        return mask_labels
    
    def encapsulation(input_image, mask_labels, channels, bg_corr):
        
        # Compute the encapsulation efficiency for each selected channel
        # Initialise variable to store results
        encap_results = {}
        for ich in channels:
            mat_image = ImageCheck.single_channel(input_image, ich)
            encap_results_ch, _ = EncapEfficiency.run(mat_image, mask_labels, bg_corr)
            masked_image = mat_image*(mask_labels >0).astype(int)
            encap_results[f'ch {ich}'] = [encap_results_ch, masked_image]

        return encap_results
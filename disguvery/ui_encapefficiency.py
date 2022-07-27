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

import numpy as np
from data_processing import GeoMat

# import custom widgets
import ui_custom_widgets as ctk 
from image_processing import ImageCheck, ImageCorrection, ImageMask
from file_handling import FileExport

class EncapPanel():

    def __init__(self, controller = None):
        # Keep track of the controller to trigger actions easily
        self.controller = controller

        # Settings variable
        settings_var = controller.appdata_settingsencap

        # Initialise the encapsulation efficiency window
        encappanel = ctk.ControlPanel(title = 'Encapsulation Efficiency')

        # Create frame to put the options in
        f_options= ttk.Frame(encappanel)
        f_options.grid(row = 0, column = 0, columnspan = 3, sticky = ' nsew', padx = 5, pady = 5)

        # Create Label Frames for widgets
        f_mask = ttk.LabelFrame(f_options, text = 'Mask content')
        f_back = ttk.LabelFrame(f_options, text = 'Background correction')

        
        # Place frames in window
        f_mask.grid(row = 0, column = 0, sticky = 'nsew', padx = 5, pady = 5)
        f_back.grid(row = 0, column = 1, columnspan = 2, sticky = 'nsew', padx = 5, pady = 5)
        
        # Create mask content widgets and place them
        sourceButton = ttk.Button(f_mask, text = 'Show Detection Mask', command = self.show_detmask)
        refinedButton = ttk.Button(f_mask, text = 'Refine Vesicle Mask', command = self.refine_detmask)
        refinedthLabel = ttk.Label(f_mask, text = 'Vesicle mask threshold: ')
        refinedthEntry = ttk.Entry(f_mask, width = 4, textvariable = settings_var['flood_th'])
        
        for n, w in enumerate([sourceButton, refinedButton]):
            w.grid(row = n, column = 0, sticky = 'nsew', padx = 5, pady = 5, columnspan = 2)
        for n, w in enumerate([refinedthLabel, refinedthEntry]):
            w.grid(row = 2, column = n, sticky = 'nsew', padx = 5, pady = 5)

        # Create background correction radiobuttons and place them
        labels_rbutton = [' None' , 'Image Mean', 'B.Box Corner']        
        for n, s in enumerate(labels_rbutton):
            rb = ttk.Radiobutton(f_back, text = s, value = n, variable = settings_var['bg_correction'])
            rb.grid(row = n, column = 0, sticky = ' nsw', padx = 5, pady = 5)
        
        # Create button widgets and place them
        runButton = ttk.Button(encappanel, text = 'Run', command = self.run)
        exportButton = ttk.Button(encappanel, text = 'Export results and mask', command = self.export)

        for n, b in enumerate([runButton, exportButton]):
            b.grid(row = 1, column = n, sticky = 'nsew', padx = 5, pady = 5)
        
        # Close button
        encappanel.closeButton.grid(row = 1, column = 2, sticky = 'nse', padx = 5, pady = 5)
        # bind event to close button, to clear the display. Need to get the actual button from the frame
        close_button = encappanel.closeButton.children['!button']
        close_button.bind('<Button>', lambda event: self.close_panel(), add = '+')

        # Keep track of window
        self.window = encappanel

    def close_panel(self):

        # In addition to closing the panel, the display needs to be cleared and temporal results erased

        # Delete all objects drawn on the display
        self.controller.gw_maindisplay.clear_showobject(drawn_object = None, label_old = 'all')
        # Remove mask if added
        try:
            self.controller.gw_maindisplay.s_mask.remove()
        except (AttributeError, ValueError):
            pass
        else:
            self.controller.gw_maindisplay.canvas.draw()

        # Delete temporal results
        try:
            del self.temp_results_mask
        except AttributeError:
            pass
    
        try:
            del self.temp_results_rois
        except AttributeError:
            pass
        else:
            del self.temp_results_imgmask

    def show_detmask(self):

        # Remove any current mask from the display
        try:
            self.controller.gw_maindisplay.s_mask.remove()
        except (AttributeError, ValueError):
            pass
        else:
            # Remove also other objects drawn
            self.controller.gw_maindisplay.clear_showobject(drawn_object = None, label_old = 'all')

        # Clear the temporal results for the mask
        try: 
            del self.temp_results_mask 
        except AttributeError:
            pass
    
        # get the results from the current image
        img_name = self.controller.appdata_imagesource['name']
        det_results = self.controller.appdata_resultsvesdet[img_name]

        # Show the current mask
        # If the results are from floodfill, take directly the mask
        mask_results = det_results.get('mask_rois', None)

        if mask_results is None:
            if det_results['method'] == 'hough': det_object = 'circle'
            else: det_object = 'box'
            self.controller.gw_maindisplay.clear_showobject([det_object, det_results['rois']],
                                                            edgecolor = 'none', facecolor = 'yellow', alpha = 0.3)
        else:
            self.controller.gw_maindisplay.overlay_mask(mask_results, alpha = 0.3)
            # Assign mask to temporal results mask
            self.temp_results_mask = mask_results

    def refine_detmask(self):

        # Clear detection mask if added
        self.controller.gw_maindisplay.clear_showobject(drawn_object = None, label_old = 'all')

        # get the detection settings to run a second floodfill detection per bounding box
        det_settings = self.controller.appdata_settingsencap

        # get the results from the current image
        img_name = self.controller.appdata_imagesource['name']
        det_results = self.controller.appdata_resultsvesdet[img_name]
        
        # Get current image, checking that is the right dimension
        current_channel = self.controller.appdata_channels['current'].get()
        mat_image = ImageCheck.single_channel(self.controller.appdata_imagecurrent, current_channel)

        mask_all = EncapEfficiency.mask_refined(mat_image, det_results['rois'],
                                float(det_settings['flood_th'].get()),
                                det_settings['flood_minarea'])
            
        # Show the output of the refined mask
        self.controller.gw_maindisplay.overlay_mask(mask_all, alpha = 0.3, remove_old = True)

        # Assign refined mask to temporal results variable
        self.temp_results_mask = mask_all.astype(int)

    def run(self):

        # Get the current image
        current_image = self.controller.appdata_imagecurrent

        # Get the mask with the labels for the vesicle interior
        try: 
            mask_labels = self.temp_results_mask
        except AttributeError:
            # get the results from the current image
            img_name = self.controller.appdata_imagesource['name']
            det_results = self.controller.appdata_resultsvesdet[img_name]
            
            if 'mask_rois' in det_results.keys():
                mask_labels = det_results['mask_rois']
            else:
                if det_results['method'] == 'hough': 
                    half_r = False
                else:
                    half_r = True
                mask_labels = GeoMat.mask_contours(det_results['rois'], current_image.shape[0:2], half_r)
        
        
        # Get the current image with the right channel. 
        # Check first if there is any channel defined as the content and select as current
        # Otherwise, check if image is single channel and force it
        content_ch = [ich for ich in [1,2,3,4] if 'content' in self.controller.appdata_channels[ich].get()]        
        if len(content_ch) >= 1:
            self.controller.appdata_channels['current'].set(content_ch[0])
            print(f'Found channel {content_ch[0]} defined as content. Used for encapsulation analysis.')
        mat_image = ImageCheck.single_channel(current_image, self.controller.appdata_channels['current'].get())
        # Get background correction
        bg_corr = self.controller.appdata_settingsencap['bg_correction'].get()

        # Save results in temporal variable
        self.temp_results_rois, results_display = EncapEfficiency.run(mat_image, mask_labels, bg_corr, return_fordisplay=True)
        self.temp_results_imgmask = mat_image*(mask_labels>0).astype(int)

        # Compile results to show them on main display
        
        self.controller.gw_maindisplay.clear_showobject(drawn_object = None, label_old = 'all')
        self.controller.gw_maindisplay.overlay_mask(mask_labels, alpha = 0.3, remove_old = True)
        self.controller.gw_maindisplay.clear_showobject(['text_info', results_display])
        
    def export(self):

        # Define default filename for saving
        img_name = self.controller.appdata_imagesource['name']
        initial_file = '{}_encapsulation_results'.format(img_name)

        # Note that the results are the ones stored 
        if hasattr(self, 'temp_results_rois'):
            # Get path + filename
            filename = tkinter.filedialog.asksaveasfilename(initialfile = initial_file)
            # Export and save encapsulation results as .csv file and the mask as tiff
            if len(filename) > 1:
                FileExport.encapsulation_results(filename, self.temp_results_rois, self.temp_results_imgmask)
        else:
            print('There are no encapsulation results to be saved')

class EncapEfficiency():

    def mask_refined(input_image, rois, flood_th, flood_minarea):

        # Build mask of refined floodfill results
        mask_all = 0*input_image

        for i, vesicle in enumerate(rois):
            [xc, yc, r] = vesicle[:3]
            x1, x2 = int(xc - r), int(xc + r)
            y1, y2 = int(yc - r), int(yc + r)

            # Correct the limits of the bounding box if necessary
            if x1 < 0: x1 = 0
            if y1 < 0: y1 = 0
            if x2 > input_image.shape[1]: x2 = input_image.shape[1]
            if y2 > input_image.shape[0]: y2 = input_image.shape[0]

            image_th = ImageMask.threshold(input_image[y1:y2, x1:x2], flood_th)
            min_area = 0.01*flood_minarea*(image_th.shape[0])
            mask_flood = ImageMask.floodfill(image_th, min_area, method = 'inside')
            mask_all[y1:y2, x1:x2]= (mask_flood != 0).astype(int)*(i+1)
          

        return mask_all

    def run(mat_image, mask_labels, bg_corr, return_fordisplay = False):

        roi_labels = np.unique(mask_labels)
        results_encap = np.zeros_like(roi_labels)
        roi_area = np.zeros_like(roi_labels)

        # Correct background if required
        
        if  bg_corr == 1:
            bg_corr_type = 'mean'
            bg_int = ImageCorrection.substract_background(mat_image.astype('float16'), bg_corr_type, inplace = False)
        elif bg_corr == 2:
            bg_corr_type = 'ROI corner'
        else:
            bg_corr_type = None
            bg_int = 0

        xall = np.zeros(len(results_encap))
        yall = np.zeros(len(results_encap))

        for id_roi in roi_labels:
            mask_roi = 0*mask_labels
            mask_roi[mask_labels == id_roi] = 1
            roi_int = mat_image*mask_roi
            mean_roi_int = np.mean(roi_int[roi_int>0].flatten())

            # If required, correct the ROI corner background
            if bg_corr_type == 'ROI corner':
                xmin, ymin = np.min(np.where(mask_roi)[1]), np.min(np.where(mask_roi)[0])
                xmax, ymax = np.max(np.where(mask_roi)[1]), np.max(np.where(mask_roi)[0])
                roi_img = mat_image[ymin:ymax, xmin:xmax]
                bg_int = ImageCorrection.substract_background(roi_img.astype('float16'), bg_corr_type, inplace = False)

            try:
                xall[id_roi] =  np.mean(np.where(mask_roi)[1])
            except IndexError:
                pass
            else:
                yall[id_roi] = np.mean(np.where(mask_roi)[0])

                results_encap[id_roi] = mean_roi_int - bg_int
                roi_area[id_roi] = np.sum(mask_roi)

        results_encap_all = np.stack((roi_labels, xall,yall, results_encap , roi_area), axis = 1)
    
        if return_fordisplay is True:
            results_display = np.stack((xall[1:], yall[1:], results_encap[1:]), axis = 1)
        else:
            results_display = None

        return results_encap_all, results_display
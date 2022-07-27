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
import numpy as np

# Import custom widgets
import ui_custom_widgets as ctk
from skimage.filters import apply_hysteresis_threshold
# Import image processing functions
from image_processing import ImageFilters, ImageMask

class RmdPanel():

    def __init__(self, controller = None):

        # We keep track of the controller to trigger actions easily
        self.controller = controller

        # Settings variable
        settings_var = controller.appdata_settingsrmd

        # Initialise the refined membrane detection window
        detpanel = ctk.ControlPanel(title = 'Refined Membrane Detection')

        # Configure window layout
        detpanel.configure_layout(cols = [0,1], rows = [0,1,2,3])

        # Create frame containers for widgets and place them
        f_mask = ttk.LabelFrame(detpanel, text = 'Image Edge Mask')
        f_det = ttk.LabelFrame(detpanel, text = 'Membrane Detection')
        for n, iframe in enumerate([f_mask, f_det]):
            iframe.grid(row = n, column = 0, columnspan = 3, sticky = 'nsew', padx = 5, pady = 5)
        
        # configure layout of frame
        f_det.rowconfigure([0,1], weight = 1)
        f_det.columnconfigure([0,1,2,3], weight = 1)

        # Create and place widgets for image edge mask
        tvar = [settings_var['img_filter'], settings_var['img_th'][1]]
        for n, s in enumerate(['Filter: ', 'Threshold: ']):
            ttk.Label(f_mask, text = s).grid(row = 0, column = 2*n, sticky = 'nsew', padx = 5, pady = 5)
            ttk.Entry(f_mask, width = 5, textvariable = tvar[n]).grid(row = 0, column = 2*n + 1, sticky = 'nsew', padx = 5, pady = 5)
        
        # Add button to create mask
        maskButton = ttk.Button(f_mask, text = 'Mask', command = self.mask)
        maskButton.grid(row = 0, column = 4, sticky = 'nsew', padx = 5, pady = 5)

        # Create and place widgets for membrane detection options
        tvar = [settings_var['bbox_margin'], settings_var['vesicle_th']]
        for n, s in enumerate(['Bbox margin: ', 'Threshold: ']):
            ttk.Label(f_det, text = s).grid(row = 0, column = 2*n, sticky = 'nsew', padx = 5, pady = 5)
            ttk.Entry(f_det, width = 5, textvariable = tvar[n]).grid(row = 0, column = 2*n + 1, sticky = 'nsew', padx = 5, pady = 5)
        tvar = [settings_var['search_l'], settings_var['search_w']]
        for n, s in enumerate(['Search Size: ', 'Search Width']):
            ttk.Label(f_det, text = s).grid(row = 1, column = 2*n, sticky = 'nsew', padx = 5, pady = 5)
            ttk.Entry(f_det, width = 5, textvariable = tvar[n]).grid(row = 1, column = 2*n + 1, sticky = 'nsew', padx = 5, pady = 5)
        
        # Create and place buttons to run detection, possible to do it by vesicle or per image
        vesButton = ttk.Button(f_det, text = 'Select and Detect', command = self.select)
        imgButton = ttk.Button(f_det, text = 'Run on Image', command = lambda: self.detect_vesicle('all'))
        for n, b in enumerate([vesButton, imgButton]): 
            b.grid(row = 2, column = 2*n, columnspan = 2, sticky = 'nsew', padx = 5, pady = 5)

        # Create and place save and close buttons
        saveButton = ttk.Button(detpanel, text = 'Save', command = self.save)
        saveButton.grid(row = 2, column = 1, sticky = 'nse', padx = 5, pady = 5)
        detpanel.closeButton.grid(row = 2, column = 2, sticky = 'nse', padx = 5 , pady = 5)

        # Bind event to close button to clear the display
        close_button = detpanel.closeButton.children['!button']
        close_button.bind('<Button>', lambda event: self.clear_display(), add = '+')
       
        # Keep track of window and select button
        self.window = detpanel
        self.selectButton = vesButton

    def mask(self):

        # Settings variable
        settings_var = self.controller.appdata_settingsrmd

        # Get current image, checking that is the right dimension
        input_image = self.check_image()

        # Get scale of the filter used for detecting the edge
        a_scale = float(settings_var['img_filter'].get())
        # Threshold used to discard edges, based on normalised WT modulus
        img_th_low = settings_var['img_th'][0]
        img_th_high = float(settings_var['img_th'][1].get())
       
        # Compute the 2D Wavelet using the first derivative
        WT_mod, WT_arg = ImageFilters.wavelet2d_firstdet(input_image, a_scale)
        # Get the thinned edges using a modified canny detector
        mask_edge = ImageMask.wt_edges(WT_mod, WT_arg)
        # Normalise the modulus
        WT_norm = WT_mod / np.max(WT_mod.flatten())
    
        # Clear the borders
        mask_edge[:int(a_scale/2), :] = 0
        mask_edge[-int(a_scale/2):, :] = 0
        mask_edge[:, -int(a_scale/2):] = 0
        mask_edge[:, :int(a_scale/2)] = 0
        
        # Apply hysteresis threshold
        WT_norm_edge = mask_edge*WT_norm
        mask_edgehigh = (WT_norm_edge > img_th_high).astype(int)
        mask_edge = mask_edgehigh + apply_hysteresis_threshold(WT_norm_edge, img_th_low, img_th_high).astype(int)

        # Save results in a temporable variable
        self.temp_results_mask = [WT_mod, WT_arg, mask_edge]

        # Update display
        self.controller.gw_maindisplay.show_scattermask(mask_edge)

    def check_image(self): 

        ## TO DO: Add check for membrane channel

        # Check the current channel selected, if it´s multiple, force it to be the first channel
        current_channel = self.controller.appdata_channels['current'].get()
        if current_channel == 0: 
            mat_image = 1*self.controller.appdata_imagecurrent[:,:,0]
            print('A single channel needs to be selected. Setting channel 1 as working channel.')
        else:
            try: 
                mat_image = 1*self.controller.appdata_imagecurrent[:,:, current_channel - 1]
            except IndexError:
                mat_image = 1*self.controller.appdata_imagecurrent
                
        return mat_image
    
    def select(self):

        # Bind on-pick event with the selection object function of the main display
        state_mpl = self.controller.gw_maindisplay.bind_onpick(off_color = 'white', delete_on_disconnect = False)
        
        # Change appearance of button based on state mpl
        if state_mpl == 'connected':
            self.selectButton.state(['pressed'])
        elif state_mpl == 'disconnected':
            self.selectButton.state(['!pressed'])
            # Run detection function if there has been any objects detected
            try: 
                selected_ves = self.controller.gw_maindisplay.object_selected
            except AttributeError:
                pass
            else:
                self.detect_vesicle(selected_ves)
                del self.controller.gw_maindisplay.object_selected
    
    def detect_vesicle(self, selected_vesicle):

        # Get the current vesicle detection results
        img_name = self.controller.appdata_imagesource['name']
        det_results = self.controller.appdata_resultsvesdet[img_name]
        all_rois = det_results['rois']
        det_method = det_results['method']

        # Get type of vesicle selection. If 'run on image',  selected_vesicle = 'all'
        if selected_vesicle == 'all':
            selected_vesicle = range(len(all_rois))

        # Settings variable
        settings_var = self.controller.appdata_settingsrmd

        # Get values from widgets
        margin_bbox = int(settings_var['bbox_margin'].get())
        search_length = int(settings_var['search_l'].get())
        search_width = float(settings_var['search_w'].get())
        ves_th = float(settings_var['vesicle_th'].get())

        # Check if there are mask results saved already in the app
        try: 
            self.temp_results_mask     
        except AttributeError:
            self.mask()
        finally: 
            WT_mod, WT_arg, mask_edge = self.temp_results_mask

        # Attempt to get the temporal results
        try:
            all_contours, centers = self.temp_results
        except AttributeError:
            all_contours = np.zeros(WT_mod.shape, dtype = int)
            # Results of detection are the same size as all rois
            centers = np.zeros((len(all_rois),2))

        # Make the WT argument only positive
        WT_arg_pos = WT_arg.copy()
        WT_arg_pos[WT_arg_pos < 0] = WT_arg_pos[WT_arg_pos < 0] + 180

        # Iterate over the vesicles
        for ves in selected_vesicle:
            roi = all_rois[ves]
            x_center, y_center = roi[0], roi[1]
            if det_method == 'hough':
                bbox = 2*roi[2] + 2*margin_bbox
            else:
                bbox =  roi[2] + 2*margin_bbox

            # Define coordinates of the bounding box
            y1 = int(y_center - bbox/2); y2 = int(y_center + bbox/2)
            x1 = int(x_center - bbox/2); x2 = int(x_center + bbox/2)

            # Check coordinates of bounding box are contained in the image
            if y1 < 0: y1 = 0
            if x1 < 0: x1 = 0
            if y2 > mask_edge.shape[1]: y2 = mask_edge.shape[1]
            if x2 > mask_edge.shape[0]: x2 = mask_edge.shape[0]

            # Show the bounding box
            self.controller.gw_maindisplay.clear_showobject(['box', [[x_center, y_center, bbox]]], 
                                                            label_old = 'selected_ves', 
                                                            label = 'selected_ves',
                                                            edgecolor = 'mediumvioletred',
                                                            draw_text = False)

            # Retrieve the WT and the edge mask for only the ROI
            WT_ves = np.zeros((int(y2-y1), int(x2-x1)))
            try:
                WT_ves[:,:] = WT_mod[y1:y2, x1:x2]
            except ValueError:
                WT_ves = WT_mod[y1:y2, x1:x2]
            finally:
                edge_ves = np.zeros(WT_ves.shape, dtype = int)
                edge_ves[:,:] = mask_edge[y1:y2, x1:x2]

            # normalize the WT modulus within the ROI and eliminate noise in edge mask
            WT_norm = WT_ves / np.max(WT_ves[WT_ves!=0].flatten())
            edge_ves[WT_norm <= ves_th] = 0

            # Construct mask for the positive arguement on the edges
            mask_WTarg = WT_arg_pos[y1:y2, x1:x2]*edge_ves
            # Show the mask of the bounding box, with the right offset
            self.controller.gw_maindisplay.show_scattermask(edge_ves, color = 'red', offset = [x1,y1],
                                                            label = 'rmd_base')
            
            # Run directional search to chain edges
            ri, ro = ImageMask.chain_search(mask_WTarg, [search_length, search_width])

            # Add offset to the ri/ro coordinates
            ri[:,0] += x1
            ri[:,1] += y1
            ro[:,0] += x1
            ro[:,1] += y1

            # Calculate center for the contours
            xc1, yc1 = np.mean(ri[:,0]), np.mean(ri[:, 1])
            xc2, yc2 = np.mean(ro[:,0]), np.mean(ro[:, 1])
            centers[ves][0] = np.mean([xc1, xc2])
            centers[ves][1] = np.mean([yc1, yc2])

            # Add results to the contours matrix
            all_contours[(ri[:,1], ri[:,0])] = -ves
            all_contours[(ro[:,1], ro[:,0])] = ves

            # Update display
            self.controller.gw_maindisplay.clear_showscatter([ri[:,0], ri[:,1]], color = 'cyan', 
                                                            label = 'rmd_contour')
            self.controller.gw_maindisplay.clear_showscatter([ro[:,0], ro[:,1]], color = 'blue',
                                                            label = 'rmd_contour')

        # Update temporal results
        self.temp_results = all_contours, centers               

    def clear_display(self):

        # Remove the vesicle detection results
        self.controller.gw_maindisplay.clear_showobject(drawn_object = None, label_old = 'vesicle')
        # Remove selected vesicle box
        self.controller.gw_maindisplay.clear_showobject(drawn_object = None, label_old = 'selected_ves')
        # Remove refined membrane detection results
        self.controller.gw_maindisplay.clear_showscatter(None, remove_old = True, label_old = 'rmd')
        # Remove mask
        self.controller.gw_maindisplay.clear_showscatter(None, remove_old = True, label_old = 'scatter')
        
        # Delete temporal results mask
        try: 
            del self.temp_results_mask
        except AttributeError:
            pass

        # Delete temporal results contours
        try:
            del self.temp_results
        except AttributeError:
            pass

    def save(self):

        # Retrieve temporal results for contours only!
        try:
            # Get the temporal results
            all_contours, centers = self.temp_results
        except AttributeError:
            print('There are no RMD results available.')
        else:        
            # Get the current image name
            img_name = self.controller.appdata_imagesource['name']
            # Assign the results to the current image
            self.controller.appdata_resultsmembrane[img_name] = {'method': 'rmd', 
                                                                'contours': all_contours,
                                                                'center': centers}
            # Print successful save
            print('The displayed membrane detection has been saved.')

        # Assign used channel to the membrane signal, IF it hasn't been assigned yet
        channel_used = self.controller.appdata_channels['current'].get()
        struct_channel = self.controller.appdata_channels[channel_used].get()
        if len(struct_channel) < 1:
            self.controller.appdata_channels[channel_used].set('membrane')
            print(f'Channel {channel_used} has been assigned to the membrane signal.')

                                

        


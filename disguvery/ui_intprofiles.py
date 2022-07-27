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

# Imporr the filedialog option from tkinter
import tkinter.filedialog

import numpy as np
from data_processing import ProfileIntegration
from image_processing import ImageCheck, ImageCorrection
from ui_canvas import CanvasEmbeddedPlot

# Import custom widgets
import ui_custom_widgets as ctk
from file_handling import FileExport


class IprofilePanel():

    def __init__(self, controller = None):

        # We keep track of the controller to trigger actions easily
        self.controller = controller

        # Variable settings
        settings_var = self.controller.appdata_settingsiprofile

        # Initialise the intensity profile panel window
        ipanel = ctk.ControlPanel(title = 'Intensity Profiles')

        # Configure window layout
        ipanel.configure_layout(cols = [0,1,2,3,4], rows = [2,3,4], weight = 2)

        # Create frame containers for widgets and pkace them
        f_adisplay = ttk.Frame(ipanel, height = 200)
        f_adisplay.grid_propagate(False)
        f_rdisplay = ttk.Frame(ipanel, height = 200)
        f_rdisplay.grid_propagate(False)
        f_profiles = ttk.Frame(ipanel)
        f_options = ttk.Frame(ipanel)
        for n, iframe in enumerate([f_adisplay, f_rdisplay, f_profiles, f_options]):
            iframe.grid(row = n, column = 0, sticky = 'nsew', padx = 5, pady = 5, columnspan = 4)
            iframe.columnconfigure([0,1], weight =1)
        
        # Create and place canvas for angular plot
        aplot_display = CanvasEmbeddedPlot(f_adisplay, small_font = True)
        # Create and place canvas for radial plot
        rplot_display = CanvasEmbeddedPlot(f_rdisplay, small_font = True)

        # Create angular and radial profiles options
        f_angular = ttk.LabelFrame(f_profiles, text = 'Angular Profiles')
        f_radial = ttk.LabelFrame(f_profiles, text = 'Radial Profiles')
        # Place frames
        for n, iframe in enumerate([f_angular, f_radial]):
            iframe.grid(row = 0, column = n, sticky = 'nsew', padx = 5, pady = 5)

        # Enable checkbox
        angularCheckbox = ttk.Checkbutton(f_angular, text = 'Enable', variable=settings_var['angular_profile'][0])
        radialCheckbox = ttk.Checkbutton(f_radial, text = 'Enable', variable = settings_var['radial_profile'][0])
        # dtheta, dr entries
        dthetaLabel = ttk.Label(f_angular, text = 'd' + u'\u03b8' + ' (deg): ')
        drLabel = ttk.Label(f_radial, text = 'dr (pix): ')
        dthetaEntry = ttk.Entry(f_angular, width = 5, textvariable=settings_var['angular_profile'][1])
        drEntry = ttk.Entry(f_radial, width = 5, textvariable=settings_var['radial_profile'][1])
        # Place widgets in corresponding frame
        w_angular = [angularCheckbox, dthetaLabel, dthetaEntry]
        w_radial = [radialCheckbox, drLabel, drEntry]
        for list_widgets in [w_angular, w_radial]:
            for n in range(3):
                list_widgets[n].grid(row = 0, column = n, sticky = 'nsew', padx = 5, pady = 5)

        # Create frames for channel checkboxes in each profile frame
        f_achannel = ttk.Frame(f_angular)
        f_rchannel = ttk.Frame(f_radial)
        w_variables = [settings_var['angular_channels'], settings_var['radial_channels']]
        for nf, iframe in enumerate([f_achannel, f_rchannel]):
            iframe.grid(row = 1, column = 0, columnspan = 4, sticky = 'nsew', padx = 5, pady = 5)
            # Create and add channel checkboxes
            for i in range(3):
                b = ttk.Checkbutton(iframe, text = f'Ch {i+1}', variable = w_variables[nf][i])
                b.grid(row = 0, column = i, sticky = 'nsew', padx = 5, pady = 5)
        
        # Create and place background correction options
        f_back = ttk.LabelFrame(f_options, text = 'Background Correction')
        f_back.grid(row = 0, column = 0, sticky = 'nsew', padx = 5, pady = 5)
        for i in range(3):
            l = ttk.Label(f_back, text = f'Ch {i+1}')
            cbox = ttk.Combobox(f_back, values = settings_var['bg_corr_options'], textvariable = settings_var['bg_corr'][i],
                                state="readonly")
            l.grid(row = i, column = 0, sticky = 'nsw', padx = 5, pady = 5)
            cbox.grid(row = i, column = 1, sticky = 'nsew', padx = 5, pady = 5)

        # Create and place normalisation options
        f_norm = ttk.LabelFrame(f_options, text = 'Normalisation Options')
        f_norm.grid(row = 0, column = 1, sticky = 'nsew', padx = 5, pady = 5)
        w_var = [settings_var['int_norm'], settings_var['rad_norm']]
        for n, s in enumerate(['Intensity', 'Radius']):
            nlabel = ttk.Label(f_norm, text = s)
            vesrb = ttk.Radiobutton(f_norm, text = 'Per Vesicle', variable = w_var[n], value = 1)
            nonerb = ttk.Radiobutton(f_norm, text = 'None', variable = w_var[n], value = 0)
            nlabel.grid(row = 2*n, column = 0, sticky = 'nsew', padx = 5, pady = 5)
            nonerb.grid(row = 2*n + 1, column = 0, sticky = 'nsew', padx = 10, pady = 2)
            vesrb.grid(row = 2*n + 1, column = 1, sticky = 'nsew', padx = 10, pady = 2)
        
        # Create and place buttons
        inspectButton = ttk.Button(ipanel, text = 'Inspect Vesicle', command = self.inspect)
        runButton = ttk.Button(ipanel, text = 'Run on Image', command = self.run_onimage)
        exportButton = ttk.Button(ipanel, text = 'Export Data', command = self.export)

        ipanel.closeButton.rowconfigure(0, weight = 1)
        ipanel.closeButton.columnconfigure(0, weight = 1)

        for n, ibutton in enumerate([inspectButton, runButton, exportButton, ipanel.closeButton]):
            ibutton.grid(row = 4, column = n, sticky = 'nsew', padx = 5, pady = 10)

        # bind event to close button, to clear the display. Need to get the actual button from the frame
        close_button = ipanel.closeButton.children['!button']
        close_button.bind('<Button>', lambda event: self.close_panel(), add = '+')

        # Keep track of window and canvas elements
        self.window = ipanel
        self.adisplay = aplot_display
        self.rdisplay = rplot_display
        # Keep track of all the widgets relevant to channels
        self.achframe = f_achannel
        self.rchframe = f_rchannel
        self.bgframe = f_back
        # Keep track of inspect button
        self.inspectButton = inspectButton

    	# Set state of the widgets according to image info
        self.update_widgets()

    def update_widgets(self):

        # Get the number of channels for the image and update available options accordingly
        image_name = self.controller.appdata_imagesource['name']
        nchannels = self.controller.appdata_imageinfo[image_name]['channels']

        if nchannels == 1: enabled_channels = [1]
        else: enabled_channels = [x + 1 for x in range(nchannels)]

        # Update checkboxes in angular and radial frame
        achildren = self.achframe.winfo_children()
        rchildren = self.rchframe.winfo_children()
        for w in range(len(achildren)):
            achildren[w].state(['disabled'])
            rchildren[w].state(['disabled'])
            for nch in enabled_channels:
                if str(nch) in achildren[w].cget('text'): 
                    achildren[w].state(['!disabled'])
                    rchildren[w].state(['!disabled'])
                
                    
        # Update combobox background correction
        bgchildren = [x for x in self.bgframe.winfo_children() if type(x) ==  ttk.Combobox]
        for w in bgchildren:
            w.state(['disabled'])
        for nch in enabled_channels:
            bgchildren[nch-1].state(['!disabled'])
        
    def get_detresults(self):

        # Get the current image name
        img_name = self.controller.appdata_imagesource['name']

        # Try to retrieve the results from membrane segmentation
        try:
            det_results = self.controller.appdata_resultsmembrane[img_name]
        except (AttributeError, KeyError):
            det_results = self.controller.appdata_resultsvesdet.get(img_name, None)
            type_det = 'vesdet'
        else:
            type_det = det_results['method']
        
        return det_results, type_det
        
    def show_detresults(self, print_source = True):

        # Retrieve detection results
        det_results, type_det = self.get_detresults()

        # If results have been found, display according to type of detection
        if det_results is not None:
            # For vesicle detection, display as usual
            if type_det == 'vesdet':
                # Print a message of results used, if wanted
                if print_source == True:
                    print('No membrane segmentation results found. Using vesicle detection results')
                if det_results['method'] == 'hough': det_method = 'circle'
                else: det_method = 'box'
                self.controller.gw_maindisplay.clear_showobject([det_method, det_results['rois']],
                                                        edgecolor = 'gray',
                                                        textcolor = 'white')
            # For bma, display the inner and outer rois based on the radius
            elif type_det == 'bma':
                # Display inner and outer rois
                self.controller.gw_maindisplay.clear_showobject(['circle', det_results['rois'][:,[0,1,2]]],
                                                                label = 'contour', 
                                                                edgecolor = 'skyblue',
                                                                textcolor = 'white') 
                self.controller.gw_maindisplay.clear_showobject(['circle', det_results['rois'][:,[0,1,3]]],
                                                                label = 'contour',
                                                                edgecolor = 'steelblue', 
                                                                draw_text = False)
            elif type_det == 'rmd':
                self.controller.gw_maindisplay.clear_showobject(['center', det_results['center']],
                                                                ignore_zeros = True,
                                                                label = 'contour',
                                                                text_color = 'white')
                self.controller.gw_maindisplay.show_scattermask(det_results['contours'],
                                                                point_color = 'steelblue')
        else:
            print('No detection results found. Please detect vesicles first!')

    def inspect(self):

        # Bind on-pick event with the selection object function of the main display
        state_mpl = self.controller.gw_maindisplay.bind_onpick(off_color = 'white', delete_on_disconnect = False,
                                                                custom_callback = True)
        # Bind right-click event 
        self.controller.gw_maindisplay.bind_right(None, custom_callback = True)

        # Change appearance of button based on state mpl
        if state_mpl == 'connected':
            self.inspectButton.state(['pressed'])
            # connect the right callback
            self.controller.gw_maindisplay.cid_pick = self.controller.gw_maindisplay.canvas.mpl_connect('pick_event', 
                                                                            lambda event: self.selected_vesicle(event))
            self.controller.gw_maindisplay.cid_right = self.controller.gw_maindisplay.canvas.mpl_connect('button_press_event',
                                                                            lambda event: self.clear_selection(event))
            # Initialise temporal results if they don't exist yet
            if not hasattr(self, 'temp_results'):
                self.temp_results = {}

        elif state_mpl == 'disconnected':
            # Clear the bounding boxes
            self.controller.gw_maindisplay.clear_showobject(drawn_object = None, 
                                                            label_old = 'selected_bbox')
            self.inspectButton.state(['!pressed'])

    def clear_selection(self, event):  
        # Only proceed if the event was triggered with the right click
        try: 
            check_button = event.button
        except AttributeError:
            if event == 'manual':
                check_button = 3

        if check_button == 3:
            # set the color of all the text labels back to the original 'on' color
            for s in self.controller.gw_maindisplay.axis_img.texts:
                s.set(color = 'skyblue')
            # Clear the bounding boxes
            self.controller.gw_maindisplay.clear_showobject(drawn_object = None, 
                                                            label_old = 'selected_bbox')
            
            # Clear the radial and angular plots
            self.rdisplay.axis_plot.clear()
            self.adisplay.axis_plot.clear()
            try: 
                self.adisplay.axis_ploty2.clear()
            except AttributeError: 
                pass
            # Update canvas
            self.rdisplay.canvas.draw()
            self.adisplay.canvas.draw()

            # Delete temporal results
            self.temp_results = {}
            
    def selected_vesicle(self, event):

        # Only proceed if the event was triggered with the left click
        if event.mouseevent.button == 1:
            # Get the artist that was selected and highlight it
            selected_object = event.artist
            selected_object.set(color = 'deeppink')
            # Ge the text, it should be equal to the vesicle id
            selected_id = int(selected_object.get_text()) - 1
            # Update canvas
            self.controller.gw_maindisplay.canvas.draw()

            # Retrieve detection results
            det_results, type_det = self.get_detresults()

            # Run the computation on the selected vesicle
            radial_profiles, angular_profiles = self.run_on_vesicle(selected_id, [det_results, type_det])
            # Assign results to vesicle
            self.temp_results[f'ves {selected_id + 1}'] = {'radial': radial_profiles, 'angular': angular_profiles}
            
    def run_on_vesicle(self, selected_vesicle, input_results):

        # Get variable settings
        settings_var = self.controller.appdata_settingsiprofile
         
        # Retrieve detection results
        det_results, type_det = input_results

        # Get normalisation options.
        norm_rad, norm_int = False, False
        int_label = '<I> (a.u.)'
        if settings_var['rad_norm'].get() == 1:
            norm_rad = True
        if settings_var['int_norm'].get() == 1:
            norm_int = True
            int_label = ' <I> / I_o'

        # depending on the type of results, get bounding box
        if type_det == 'bma':
            [xc,yc] = det_results['rois'][selected_vesicle, [0,1]]
            r = det_results['rois'][selected_vesicle, 3]
            rlim_results = [det_results['rois'][selected_vesicle, 2], r]
        elif type_det == 'vesdet':
            [xc, yc, r] = det_results['rois'][selected_vesicle][:3]
            if det_results['method'] != 'hough':
                r /= 2    
            rlim_results = None
        elif type_det == 'rmd':
            # We set the bounding box to the max distance between dx,dy in ro
            # Only for the selected vesicle    
            yo, xo = np.where(det_results['contours'] == selected_vesicle)
            xc, yc = det_results['center'][selected_vesicle]
            r = np.max([np.abs(xo - xc), np.abs(yo - yc)])
            
        # Set bounding box coordinates
        x1, x2 = int(xc - r - 5), int(xc + r + 5)
        y1, y2 = int(yc - r - 5), int(yc + r + 5)

        # If the detection is made with rmd, get the mask for the contours only on the bounding box
        try: 
            rlim_results = det_results['contours'][y1:y2, x1:x2]
            rlim_results = rlim_results/selected_vesicle
        except KeyError:
            pass

        # set bounding box center
        bbox_center = [int(xc-x1), int(yc-y1)]

        # Update display with the bounding box
        self.controller.gw_maindisplay.clear_showobject(['box', [[xc, yc, (x2 - x1)]]],
                                                                label = 'selected_bbox',
                                                                edgecolor = 'magenta', 
                                                                draw_text = False, 
                                                                label_old = 'nothing')
        
        # get current channel to get back to once computation is done
        initial_channel = self.controller.appdata_channels['current'].get()
        # Set colors for line plots
        colors_channels = ['k', 'firebrick', 'steelblue']

        # Perform radial integration, if desired
        if settings_var['radial_profile'][0].get() == 1:
            # Get radial interval
            dr = int(settings_var['radial_profile'][1].get())

            # compute for each desired channel
            ch_toint = [i+1 for i,x in enumerate(settings_var['radial_channels']) if x.get()]

            # Initialise radial profile list
            radial_profiles_all = {}
            for ic in ch_toint:
                # Set the working channel to the channel selected
                self.controller.appdata_channels['current'].set(ic)
                
                # Check if the image is the right dimension
                current_channel = self.controller.appdata_channels['current'].get()
                mat_image = ImageCheck.single_channel(self.controller.appdata_imagecurrent, current_channel)

                # correct background intensity for the whole image, if required
                bg_corr = settings_var['bg_corr'][ic - 1].get()
                if  'Image' in bg_corr:
                    mat_image = ImageCorrection.substract_background(mat_image.astype('float16'), corr_type = bg_corr)
                
                # Get the image only to the bounding box of the detected vesicle
                image_bbox = mat_image[y1:y2, x1:x2]

                # Compute background intensity for the ROI, if required
                if 'ROI' in bg_corr:
                    image_bbox = ImageCorrection.substract_background(image_bbox.astype('float16'), corr_type = bg_corr)


                radial_profiles, found_error = ProfileIntegration.radial(image_bbox, bbox_center, dr, 
                                                                        norm = norm_int)

                # If required, normalise the radius
                if norm_rad is True:
                    radial_profiles[:,0] /= r
                    rlabel = 'r / r_d'
                else:
                    rlabel = 'r (pix)'

                # Update plot for radial profile
                if len(ch_toint) > 1:
                    textlabel = f'v{selected_vesicle + 1}c{ic}'
                else:
                    textlabel = f'v{selected_vesicle + 1}'
                self.rdisplay.plot_line(radial_profiles[:,0], radial_profiles[:,1], 
                                    xlabel = rlabel, ylabel = int_label, 
                                    textlabel = textlabel, alpha = 0.8,
                                    color = colors_channels[ic-1])
                radial_profiles_all[f'ch {ic}'] = radial_profiles
        else:
            radial_profiles_all = None
        
        # Perform angular integration if desired
        if settings_var['angular_profile'][0].get() == 1:
            # Get angular interval
            dtheta = int(settings_var['angular_profile'][1].get())

            # Compute for each desired channel
            ch_toint = [i+1 for i,x in enumerate(settings_var['angular_channels']) if x.get()]
            compute_rad = True

            # Initialise angular profiles and mean radius lists
            angular_profiles_all = {}
            for ic in ch_toint:
                # Set the working channel to the channel selected
                self.controller.appdata_channels['current'].set(ic)
                # Get the type of structure labeled with the corresponding channel
                struct_channel = self.controller.appdata_channels[ic].get()
                # If the structure is related to the membrane, the rlim applied
                if 'membrane' in struct_channel: rlim_channel = rlim_results
                else: rlim_channel = None
                
                # Check if the image is the right dimension
                current_channel = self.controller.appdata_channels['current'].get()
                mat_image = ImageCheck.single_channel(self.controller.appdata_imagecurrent, current_channel)

                # correct background intensity for the whole image, if required
                bg_corr = settings_var['bg_corr'][ic - 1].get()
                if  'Image' in bg_corr:
                    mat_image = ImageCorrection.substract_background(mat_image.astype('float16'), corr_type = bg_corr)
                
                # Get the image only to the bounding box of the detected vesicle
                image_bbox = mat_image[y1:y2, x1:x2]

                # Compute background intensity for the ROI, if required
                if 'ROI' in bg_corr:
                    image_bbox = ImageCorrection.substract_background(image_bbox.astype('float16'), corr_type = bg_corr)

                # Compute angular profiles
                angular_profiles, mean_radius, _ = ProfileIntegration.angular(image_bbox, bbox_center, dtheta, 
                                                                                rlim = rlim_channel,
                                                                                norm = norm_int)

                # Update plot for angular profile
                if len(ch_toint) > 1:
                    textlabel = f'v{selected_vesicle + 1}c{ic}'
                else:
                    textlabel = f'v{selected_vesicle + 1}'
                
                self.adisplay.plot_line(angular_profiles[:,0], angular_profiles[:,1], 
                                    xlabel = "\u03b8" + "(deg)", ylabel = int_label, 
                                    textlabel = textlabel, alpha = 0.8,
                                    color = colors_channels[ic-1])
                # If the mean radius is variable, also plot the profile
                if mean_radius is not None and compute_rad is True:
                    self.adisplay.plot_secline(angular_profiles[:,0], mean_radius[:,0],
                                    xlabel = "\u03b8" + "(deg)", ylabel = 'r (pix)', alpha = 0.8,
                                    textlabel = textlabel) 
                compute_rad = False
                angular_profiles_all[f'ch {ic}'] = angular_profiles
                angular_profiles_all[f'mean radius']  = mean_radius
        else:
            angular_profiles_all = None
            
        # Set channel back to initial one
        self.controller.appdata_channels['current'].set(initial_channel)

        # return results of radial and angular profiles, as well as the mean radius
        return radial_profiles_all, angular_profiles_all

    def run_onimage(self):

        # Start by clearing the display
        self.clear_selection(event = 'manual')

        # Get detection results
        det_results, type_det = self.get_detresults()

        # Initialise temporal results if they don't exist yet
        if not hasattr(self, 'temp_results'):
            self.temp_results = {}

        # Get the rois depending on the method used for detection/segmentation
        try: 
            all_vesicles = range(det_results['rois'].shape[0])
        except KeyError:
            # RMD stores results in the 'contours' key
            all_vesicles = [x for x in np.unique(det_results['contours']) if x > 0]

        for ivesicle in all_vesicles:
            radial_profiles, angular_profiles = self.run_on_vesicle(ivesicle, [det_results, type_det])
            # Assign results to vesicle
            self.temp_results[f'ves {ivesicle + 1}'] = {'radial': radial_profiles, 'angular': angular_profiles}

    def close_panel(self):

        # In addition to closing the panel, the display needs to be cleared and results erased
        
        # Disconnect the canvas, and rset the button status if necessary
        if 'pressed' in self.inspectButton.state():
            self.inspect()
        
        # Delete all objects drawn on the display
        self.controller.gw_maindisplay.clear_showobject(drawn_object = None, 
                                                            label_old = 'all')
        # Remove scatter points - from RMD - if they have been drawn
        self.controller.gw_maindisplay.clear_showscatter(scatter_points = None, remove_old = True)
                                
        # clear the intensity profile canvas
        self.clear_selection(event = 'manual')

        # Delete temporal results
        try: 
            del self.temp_results
        except AttributeError:
            pass
        
    def export(self):

        # Define default filename for saving
        img_name = self.controller.appdata_imagesource['name']
        initial_file = '{}_results'.format(img_name)

        # Note that the results are the ones stored in the temporal variable
        if hasattr(self, 'temp_results'):
            # Get path + filename
            filename = tkinter.filedialog.asksaveasfilename(initialfile = initial_file, 
                                                            defaultextension = '.csv')
            # Export and save file as .csv, skip error upon pressing cancel
            if len(filename) > 4:
                FileExport.intensity_profiles(filename, self.temp_results)
        else:
            print('There are not intensity profiles found')
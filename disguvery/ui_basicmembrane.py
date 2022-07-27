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

# import tkinter
from tkinter import ttk

# import custom widgets
import ui_custom_widgets as ctk

class BmaPanel():

    def __init__(self, controller = None):

        # We keep track of the controller to trigger actions easily
        self.controller = controller

        # Settings variable
        settings_var = self.controller.appdata_settingsbma

        # Initialise the basic membrane analysis window
        detpanel = ctk.ControlPanel(title = 'Basic Membrane Analysis')

        # Configure window layout
        detpanel.configure_layout(cols = [0,1,2], rows = [0,1,2])

        # Create frame containers for widgets
        [f_width, f_offset] = detpanel.create_frames(2)
        # Create label frame
        f_contour = ttk.LabelFrame(detpanel, text = 'Contour position')

        # Place frames in window
        for n, iframe in enumerate([f_width, f_contour, f_offset]):
            iframe.grid(row = n, column = 0, columnspan = 3, sticky = 'nsew', padx = 5, pady = 2)
            iframe.rowconfigure(0, weight = 1)
            iframe.columnconfigure([0,1,2], weight = 1)

        # Create widgets for membrane width
        w_label = ttk.Label(f_width, text = 'Membrane width (pixels): ')
        w_entry = ttk.Entry(f_width, width = 4, textvariable = settings_var['width'])
        for n, w in enumerate([w_label, w_entry]):
            w.grid(row = 0, column = n, sticky = 'nsew', padx = 5, pady = 5)

        # Create radiobuttons for contour position options
        for n, s in enumerate(['Inside', 'Middle', 'Outside']):
            w = ttk.Radiobutton(f_contour, text = s, value = n, variable = settings_var['contour_position'])
            w.grid(row = 0, column = n, sticky = 'nsew', padx = 5, pady = 5)

        # Create widgets for offset
        offCheckbutton = ttk.Checkbutton(f_offset, text = 'Offset bounding box: ', variable = settings_var['offset'][0])
        offEntry = ttk.Entry(f_offset, width = 4, textvariable = settings_var['offset'][1])

        for n, w in enumerate([offCheckbutton, offEntry]):
            w.grid(row = 0, column = n, sticky = 'nsew', padx = 5, pady = 5)

        # Create and place buttons in window
        runButton = ttk.Button(detpanel, text = 'Run', command = self.run)
        saveButton = ttk.Button(detpanel, text = 'Save', command = self.save)

        for n, ibutton in enumerate([runButton, saveButton]):
            ibutton.grid(row = 3, column = n, sticky = 'nse', padx = 10, pady = 10)
        
        detpanel.closeButton.grid(row = 3, column = 2, sticky = 'nse', padx = 10, pady = 10)

        # bind event to close button, to clear the display. Need to get the actual button from the frame
        close_button = detpanel.closeButton.children['!button']
        close_button.bind('<Button>', lambda event: self.clear_display(), add = '+')

        # Keep track of window, and the offset widgets
        self.window = detpanel
        self.offCheckbutton = offCheckbutton
        self.offEntry = offEntry

    def update_offset(self, det_method):

        # If the detection method is 'circle', no need for the offset of bounding box
        if det_method == 'circle':
            self.offCheckbutton.config(state='disabled')
            self.offEntry.config(state= 'disabled')
        else:
            self.offCheckbutton.config(state='normal')
            self.offEntry.config(state='normal')
    
    def clear_display(self):

        # Remove the vesicle detection results
        self.controller.gw_maindisplay.clear_showobject(drawn_object = None, 
                                                        label_old = 'vesicle')
        # Remove bma rois
        self.controller.gw_maindisplay.clear_showobject(drawn_object = None, 
                                                        label_old = 'bma')

        # Delete temporal results
        del self.temp_results

    def run(self):

        # Settings variable
        settings_var = self.controller.appdata_settingsbma

        # Get the current vesicle detection results
        img_name = self.controller.appdata_imagesource['name']
        det_results = self.controller.appdata_resultsvesdet[img_name]
        
        # For the if statement to work, we need to get the state of the checkbutton before
        state_offset = str(self.offCheckbutton.cget('state'))

        # If valid, get the offset from the bounding box
        if settings_var['offset'][0].get() == 0:
            offset_box = 0
        elif (det_results['method'] != 'hough') and (state_offset == 'normal'):
            offset_box = int(settings_var['offset'][1].get())
        else:
            offset_box = 0

        # Run the basic membrane segmentation
        rois_in, rois_out = BMAsegmentation.run(det_results, settings_var, offset_box)
       
        # Save results in a temporal variable
        self.temp_results = [rois_in, rois_out]

        # Display the results in the main window, first clearing the canvas from the old results
        self.controller.gw_maindisplay.clear_showobject(['circle',  rois_in], 
                                                        label_old = 'bma', label = 'bma',
                                                        edgecolor = 'skyblue',
                                                        textcolor = 'none')
        self.controller.gw_maindisplay.clear_showobject(['circle', rois_out], 
                                                        label_old = '', label = 'bma',
                                                        edgecolor = 'steelblue',
                                                        textcolor = 'none')

    def save(self):

        # Retrieve temporal results
        try: 
            # Get the temporal results
            rois_in, rois_out = self.temp_results
        except AttributeError:
            print('There are no BMA results available.')
        else:
            rois_combined = BMAsegmentation.combine_rois(rois_in, rois_out)
            
            # Get the current image name
            img_name = self.controller.appdata_imagesource['name']
            # Assign the results to the current image
            self.controller.appdata_resultsmembrane[img_name] = {'method': 'bma',
                                                                'rois': rois_combined}
            # Print successful save
            print('The displayed membrane segmentation has been saved.')

            # Assign used channel to the membrane signal, IF it hasn't been assigned yet
            channel_used = self.controller.appdata_channels['current'].get()
            struct_channel = self.controller.appdata_channels[channel_used].get()
            if len(struct_channel) < 1:
                self.controller.appdata_channels[channel_used].set('membrane')
                print(f'Channel {channel_used} has been assigned to the membrane signal.')
        

class BMAsegmentation():

    def run(det_results, settings_var, offset_box):

        # Get the rois from the detection results
        rois = det_results['rois']

        # Options for the inside offset, and outside offset
        pix_width = int(settings_var['width'].get())
        offset_in_opt = [0, int(pix_width/2), pix_width]
        offset_out_opt = [pix_width, int(pix_width/2), 0]
        
        # Determine offset to make the inner and outer membrane boundary
        contour_pos = settings_var['contour_position'].get()
        offset_in = offset_in_opt[contour_pos]
        offset_out = offset_out_opt[contour_pos]

        # Build list with rois equivalent to the inner and outer contour
        rois_in = rois[:,:3].copy()
        rois_out = rois[:,:3].copy()

        if det_results['method'] == 'hough':
            for ic, roi in enumerate(rois):
                rois_in[ic][2] = roi[2] - offset_in 
                rois_out[ic][2] = roi[2] + offset_out 
        else:
            for ic, roi in enumerate(rois):
                rois_in[ic][2] = roi[2]/2 - offset_in - offset_box
                rois_out[ic][2] = roi[2]/2 + offset_out - offset_box
        
        return rois_in, rois_out         

    def combine_rois(rois_in, rois_out):

        # Create a new array like rois_in
        rois_combined = rois_in.copy()
        # Resize to allow for buffer
        rois_combined.resize(rois_out.shape[0], 6)
        # Assign values from rois in and out
        rois_combined[:,:3] = rois_in
        rois_combined[:,3:] = rois_out
        # Reduce the array to only have [x,y,rin,rout]
        rois_combined = rois_combined[:,[0,1,2,5]]
        
        return rois_combined

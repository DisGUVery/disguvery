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

# Import the functions to smooth/enhance the image
from image_processing import ImageFilters

class EnhancePanel():

    def __init__(self, controller = None):
        # As the panel for membrane enhancement is a toplevel window it doesn't need a master widget
        # We do need the controller to trigger actions easily
        self.controller = controller

        # Initialise the membrane enhancement window
        enhancepanel = ctk.ControlPanel(title = 'Enhance Membrane')

        # Configure layout of the window
        enhancepanel.configure_layout(cols = [0], rows = [0,1])

        # Create frame containers for widgets
        [f_settings, f_main]  = enhancepanel.create_frames(2)

        # Place frames in window and configure their layout
        for n, iframe in enumerate([f_settings, f_main]):
            iframe.grid(row = n, column = 0, sticky = 'nsew', padx = 5, pady = 5)
            iframe.columnconfigure([1,2], weight = 1)
            iframe.rowconfigure(0, weight = 1)

        # Get the values for the widgets
        appdata_settings = controller.appdata_settingsenhance
        method_opt = appdata_settings['method']
        current_method = appdata_settings['current'][0]
        method_index = [x for x in range(len(method_opt)) if current_method in method_opt[x].lower()]
        smooth_value = str(appdata_settings[current_method][0])
        enhance_value = str(appdata_settings[current_method][1])
        controller.appdata_settingsenhance['current'][1].set(smooth_value)
        controller.appdata_settingsenhance['current'][2].set(enhance_value)

        # Create settings widgets and place them
        s_label = ttk.Label(f_settings, text = 'Settings: ')
        s_combobox = ttk.Combobox(f_settings, values = method_opt)
        s_saveButton = ttk.Button(f_settings, text = 'Save', command = self.save_settings)

        for n, s_widget in enumerate([s_label, s_combobox, s_saveButton]):
            s_widget.grid(row = 0, column = n, sticky = 'nsew', padx = 5, pady = 2)

        # configure combobox and bind selection event to update the entry settings
        s_combobox.current(method_index)
        s_combobox.bind('<<ComboboxSelected>>', lambda event: self.update_settings(event, controller.appdata_settingsenhance))
        
        # Create widgets for smooth filter and place them
        f_label = ttk.Label(f_main, text = 'Smooth Filter Size: ')
        f_entry = ttk.Entry(f_main, width = 5, textvariable = controller.appdata_settingsenhance['current'][1])
        f_button = ttk.Button(f_main, text = 'Smooth Image', command = self.smooth)

        for n, f_widget in enumerate([f_label, f_entry, f_button]):
            f_widget.grid(row = 0, column = n, sticky = 'nsew', padx = 5, pady = 2)
        
        # Create widgets for enhance filter and place them
        e_label = ttk.Label(f_main, text = 'Enhance Filter Size: ')
        e_entry = ttk.Entry(f_main, width = 5, textvariable = controller.appdata_settingsenhance['current'][2])
        e_button = ttk.Button(f_main, text = 'Enhance Signal', command = self.enhance)

        for n, e_widget in enumerate([e_label, e_entry, e_button]):
            e_widget.grid(row = 1, column = n, sticky = 'nsew', padx = 5, pady = 5)

        # Place 'Close' Button
        enhancepanel.closeButton.grid(row = 2, column = 0, sticky = 'nse', padx = 2, pady = 2)

        # Keep track of the window
        self.window = enhancepanel

    def update_settings(self, event, settings_var = None):

        # Get current method from combobox selection
        current_method = event.widget.get()

        # Set current value of combobox to the right variable and entry widgets
        method_key = [x for x in settings_var.keys() if x in current_method.lower()]
        smooth_value = str(settings_var[method_key[0]][0])
        enhance_value = str(settings_var[method_key[0]][1])

        settings_var['current'][0] = method_key[0]
        settings_var['current'][1].set(smooth_value)
        settings_var['current'][2].set(enhance_value)

    def save_settings(self):

        # Variable settings
        settings_var = self.controller.appdata_settingsenhance

        # Get current method
        current_method = settings_var['current'][0]

        # Set values in respective dictionary
        settings_var[current_method][0] = int(settings_var['current'][1].get())
        settings_var[current_method][1] = int(settings_var['current'][2].get())

        # Print message in the terminal to notify the user about the updated settings
        print(f'The membrane enhancement settings for {current_method} detection have been saved.')

    def smooth(self):
        # Image to work on is the current image
        mat_image = self.controller.appdata_imagecurrent
        # Get the current cannel
        current_channel = self.controller.appdata_channels['current'].get()
        # Get the image only from the current channel
        if (mat_image.ndim > 2) and (current_channel != 0):
            update_single_channel = True
            mat_image = mat_image[:,:,current_channel - 1]
        else:
            update_single_channel = False
            
        # Get the filter size
        filter_size = int(self.controller.appdata_settingsenhance['current'][1].get())
        # Check that filter size is odd, and force it if it's not
        filter_size = ImageFilters.check_filtersize(filter_size)
        # Update settings values
        self.update_filtersize(filter_size, 'smooth')

        # Smooth image
        smooth_image = ImageFilters.smooth(mat_image, filter_size)
        # Update current image with the smoothed image in the right channel
        if update_single_channel is True:
            self.controller.appdata_imagecurrent[:,:,current_channel - 1] = 1*smooth_image
        else:
            self.controller.appdata_imagecurrent = 1*smooth_image

        # Add the current value to the variable that tracks smoothing
        self.update_enhancesettings('smooth', current_channel)

        # Show the smoothed image and assign as current image
        self.controller.gw_maindisplay.clear_showimage(smooth_image)
      
    def update_filtersize(self, filter_size, filter_type): 

        # Variable settins
        settings_var = self.controller.appdata_settingsenhance

        # Get current method
        current_method = settings_var['current'][0]

        if filter_type == 'smooth': filter_option = 1
        elif filter_type == 'enhance': filter_option = 2
        
        # Set variable of the current method with the new value
        settings_var['current'][filter_option].set(str(filter_size))

        # Set values in respective dictionary
        settings_var[current_method][filter_option - 1] = filter_size
        
    def enhance(self):

        # Image to work on is the current image
        mat_image = self.controller.appdata_imagecurrent
        # Get the current cannel
        current_channel = self.controller.appdata_channels['current'].get()
        # Get the image only from the current channel
        if (mat_image.ndim > 2) and (current_channel != 0):
            update_single_channel = True
            mat_image = mat_image[:,:,current_channel - 1]
        else:
            update_single_channel = False

        # Get the filter size 
        filter_size = int(self.controller.appdata_settingsenhance['current'][2].get())
        # Check that filter size is odd, and force it if it's not
        filter_size = ImageFilters.check_filtersize(filter_size)
        # Update settings values
        self.update_filtersize(filter_size, 'enhance')

        # Enhance image
        enhanced_image = ImageFilters.enhance(mat_image, filter_size)
        # Update current image with the smoothed image in the right channel
        if update_single_channel is True:
            self.controller.appdata_imagecurrent[:,:,current_channel - 1] = 1*enhanced_image
        else:
            self.controller.appdata_imagecurrent = 1*enhanced_image

        # Add the current channel to the variable that tracks enhancement
        self.update_enhancesettings('enhance', current_channel)
        # Show the enhanced image and assign as current image
        self.controller.gw_maindisplay.clear_showimage(enhanced_image)
          
    def update_enhancesettings(self, track_event, current_channel):

        if track_event == 'smooth':
            track_channels = self.controller.appdata_settingsenhance['ch_status'][0]
        elif track_event == 'enhance':
            track_channels = self.controller.appdata_settingsenhance['ch_status'][1]

        if current_channel == 0:
            track_channels = [x for x in range(4)]
        elif current_channel not in track_channels:
            track_channels.append(current_channel)

        # Check if the tracked channels are all of the channels in the image, and add the 
        # option for the 'all channels' selection
        try:
            nchannels = self.controller.appdata_imagecurrent.shape[2]
        except IndexError:
            pass
        else:
            if len(track_channels) >= nchannels:
                track_channels.append(0)

        if track_event == 'smooth':
            self.controller.appdata_settingsenhance['ch_status'][0] = track_channels
        elif track_event == 'enhance':
            self.controller.appdata_settingsenhance['ch_status'][1] = track_channels

      
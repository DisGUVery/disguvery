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

import tkinter as tk

# Imporr the filedialog option from tkinter
import tkinter.filedialog
# Import the os package to access directories and files
import os

# Import hte file handling functions
from file_handling import FileImage, FileExport
# Import the control panels
from ui_filemanager import FileManager
from ui_channelmanager import ChannelManager
from ui_enhancement import EnhancePanel
from ui_intprofiles import IprofilePanel
from ui_refinedmembrane import RmdPanel
from ui_vesdetection import VesdetPanel
from ui_vessizedist import VesSizePanel
from ui_encapefficiency import EncapPanel
from ui_basicmembrane import BmaPanel
from ui_batchprocessing import BatchPanel

class MenuMain(tk.Menu):
    
    def __init__(self, parent = None, controller = None):

        # Initialise the General Menu
        tk.Menu.__init__(self, parent)

        # Create the subemnus
        menu_file = MenuFile(self, parent)
        menu_image = MenuImage(self, parent)
        menu_detection = MenuDetection(self, parent)
        menu_membrane = MenuMembrane(self, parent)
        menu_analysis = MenuAnalysis(self, parent)
        menu_batch = MenuBatch(self, parent)
        

        # Set the initial state of the elements in submenus to disabled
        for imenu in [menu_image, menu_detection, menu_membrane, menu_analysis]:
            self.setstate_all(imenu, 'disabled')
        
        # dictionary with the label of the submenus and corresponding menu
        submenu_labels = {0: ['File', menu_file],
                          1: ['Image Options', menu_image],
                          2: ['Vesicle Detection', menu_detection],
                          3: ['Membrane Segmentation', menu_membrane],
                          4: ['Analysis', menu_analysis],
                          5: ['Batch Processing', menu_batch]}

        # Add the submenus to the menubar in the order stated by the key
        for menu_order in sorted(submenu_labels.keys()):
            label_submenu, submenu = submenu_labels[menu_order]
            self.add_cascade(label = label_submenu, menu = submenu)

    def setstate_all(self, submenu, set_state = 'disabled'):
        
        # Set the state of all the elements in submenu
        for index in range(submenu.index('end')+1): 
            try:
                submenu.entryconfigure(index, state = set_state)
            except tk.TclError:
                pass

class MenuFile(tk.Menu):

    def __init__(self, parent = None, controller = None):
        self.controller = controller

        # Initialise the menu
        tk.Menu.__init__(self, parent)

        # Add the menu elements
        self.add_command(label = 'Open Image', command = lambda: self.open('single'))
        self.add_command(label = 'Load Multiple Images', command = lambda: self.open('multiple'))
        self.add_command(label = 'Load Folder', command = lambda: self.open('folder'))
        self.add_command(label = 'Show File Manager', command = self.show_manager)
        self.add_separator()
        self.add_command(label = 'Quit', command = controller.quit, accelerator = '<Ctrl + q>')

    def open(self, input_file):

        # Define options for loading the image
        options = {}
        options['defaultextension'] = '.tif'
        options['filetypes'] = [('TIFF Files', ('.tif', '.tiff')),
                                ('PNG Files', '.png')]
        
        # Open dialog where user can select the file ot be opened
        # Dialog depends on whether a single image or multiple images are opened
        if input_file == 'single':
            options['title'] = 'Open Image'
            file_list = [tkinter.filedialog.askopenfilename(**options)]
        elif input_file == 'multiple':
            options['title'] = 'Load Multiple Images'
            file_list = list(tkinter.filedialog.askopenfilenames(**options))
        elif input_file == 'folder':
            # For the folder loading, we need to processs further the input
            # best to do it in a separate function
            file_list = self.load_folder()

        # Check if there was a file selected or not
        try: file_list[0][1]
        except IndexError: pass
        else:
            # Set default number of channels
            nchannels = 1
            # :oadd all images, from the last to the first, sroting the file information
            for ifile in file_list[::-1]:
                # Attempt to load the image file
                print(f'\n Loading file: {ifile}')
                image_info, image_name, source_image = FileImage.open(ifile)

                # If supported, store the file information and update the source image
                if source_image is not None:
                    self.controller.appdata_imagesource['image'] = source_image
                    self.controller.appdata_imagesource['name'] = image_name
                    nchannels = image_info['channels']
                    self.controller.appdata_imageinfo[image_name] = image_info
           
            # Update the channel information
            if nchannels == 1: self.controller.appdata_channels['current'].set(1)
            else: self.controller.appdata_channels['current'].set(0)
            # Show the last loaded image in display - clearing the axis first
            # and update the current image
            image_toshow = self.controller.appdata_imagesource['image']
            self.controller.appdata_imagecurrent = image_toshow
            # Update the display and set the current image
            self.controller.gw_maindisplay.clear_showimage(image_toshow , update_current = True) 
      
            # Enable the options within the image menu and the vesicle detection menu
            for submenu_name, submenu in self.master.children.items():
                if submenu_name in ['!menuimage', '!menudetection']:
                    self.master.setstate_all(submenu, set_state = 'normal')

            # Update channel submenu state
            menu_image = self.master.children['!menuimage']
            menu_image.setstate_channels(nchannels)
            # Update directory for batch processing
            if len(self.controller.appdata_settingsbatch['savedir'].get()) <=1:
                self.controller.appdata_settingsbatch['savedir'].set(image_info['directory'])

            # Update enhancement status of pre-processing options to None
            self.controller.appdata_settingsenhance['ch_status'] = [[],[]]

    def load_folder(self):

        # Open dialog where user can select the directory to be opened
        file_dir = tkinter.filedialog.askdirectory(title = 'Select Folder')
        # Supported image files. It only accepts TIFF and PNG format at the moment
        supported_files = ['png', 'tif', 'tiff']

        # Get the names of all the files within the directory
        # and add them only if htey are one of the supported files
        try:
            file_list = os.listdir(file_dir)
        except FileNotFoundError:
            pass
        else:
            image_list = [x for x in file_list if x.split('.')[-1] in supported_files]

        # Join the file directory and the image name for full path
        try: 
            file_list = ['/'.join([file_dir, x]) for x in image_list]        
        except UnboundLocalError:
            file_list = []

        return file_list

    def show_manager(self):

        # Check if window exists and raise on top of the other windows
        try:
            self.controller.gw_filemanager.window.lift()
        except (AttributeError, tkinter.TclError):
            # If it doesn't exist create it
            self.controller.gw_filemanager = FileManager(self.controller)
        finally:
            # Assign the info to be used in the lists
            image_info = self.controller.appdata_imageinfo
            img_name = self.controller.appdata_imagesource['name']   

        # Get the current directory if exists
        try:
            current_dir = image_info[img_name]['directory']
        except KeyError:
            current_dir = None
        
        # Fill in the directory list and highlight current directory
        self.controller.gw_filemanager.add_directories(image_info)
        self.controller.gw_filemanager.show_ascurrent('directory', current_dir)
        # FIll in the image list and highlight current image
        self.controller.gw_filemanager.add_images(image_info, current_dir)
        self.controller.gw_filemanager.show_ascurrent('image', img_name)     

class MenuImage(tk.Menu):

    def __init__(self, parent = None, controller = None):

        self.controller = controller
        # Initialise the menu
        tk.Menu.__init__(self, parent)

        # Add menu for managing the image channels
        self.add_channelmenu(self, controller.appdata_channels['current'])
        # Add channel manager
        self.add_command(label = 'Channel Manager', command = self.show_manager)
        # Add option to reset the image
        self.add_command(label = 'Reset Image', accelerator = '<Ctrl + r>', command = self.image_reset)

        # Bind the key to reset image
        self.controller.bind_all('<Control-r>', lambda event:self.image_reset())

    def add_channelmenu(self, parent = None, channel_var = None):

        # Initialise menu
        menu_channels = tk.Menu(parent, name = '!menuchannels')
        # Add elements
        menu_channels.add_radiobutton(label = 'All Channels', variable = channel_var,
                                    value = 0, command = self.set_channel)
        menu_channels.add_separator()
        for ch in range(1,5):
            menu_channels.add_radiobutton(label = f'Channel {ch}',
                                    variable = channel_var,
                                    value = ch, command = self.set_channel)

        # Add the cascade to the image menu
        self.add_cascade(label = 'Channels', menu = menu_channels)

    def set_channel(self):

        # Read the current working image
        current_image = self.controller.appdata_imagecurrent
        # Update the display and set the current image
        self.controller.gw_maindisplay.clear_showimage(current_image, update_current = True) 
        # Update the enhancement status of the pre-processing options
        MenuShared.check_enhancement(self.controller)

    def setstate_channels(self, number_channels):

        # Get the channels submenu
        menu_channels = self.children['!menuchannels']
        
        if number_channels == 1: enabled_channels = ['Channel 1']
        else:
            enabled_channels = [f'Channel {x+1}' for x in range(number_channels)]
            enabled_channels.insert(0, 'All Channels')
        # Disable all the options that are not relevant
        for index in range(menu_channels.index('end')):
            set_state = 'disabled' 
            try:
                 item_label = menu_channels.entrycget(index, 'label')
            except tk.TclError: 
                item_label = 'none'            
            if item_label in enabled_channels: 
                set_state = 'normal'
            try: 
                menu_channels.entryconfigure(index, state = set_state)
            except tk.TclError:
                pass
    
    def show_manager(self):

        # Check if window exists and raise on top of the other windows
        try:
            self.controller.gw_channelmanager.window.lift()
        except (AttributeError, tk.TclError):
            # If it doesn't exist create it
            self.controller.gw_channelmanager = ChannelManager(self.controller)

    def image_reset(self):

        # Show the source image, clearing the axis first
        reset_image = self.controller.appdata_imagesource['image']
        # Display the updated (reset) image
        self.controller.gw_maindisplay.clear_showimage(reset_image, update_current = True)

        # Reset enhancement status
        MenuShared.reset_enhancement(self.controller)
        MenuShared.check_enhancement(self.controller)
    
class MenuDetection(tk.Menu):

    def __init__(self, parent = None, controller = None):

        self.controller = controller
        # Initialise menu
        tk.Menu.__init__(self, parent)        

        # Add menu elements
        self.add_command(label = 'Detect Vesicles', command = self.vesdetection)
        self.add_separator()
        self.add_command(label = 'Membrane Enhancement', command = self.enhancement)
        self.add_command(label = 'Display Options')
        # Add submenu for exporting
        self.add_exportmenu(self)
        # Add option to select and delete vesicles
        self.add_separator()
        self.add_command(label = 'Select and Delete', accelerator = '<Ctrl-d>', command = self.select_delete)
       
        # Bind select and delete to key-event
        self.controller.bind_all('<Control-d>', lambda event: self.select_delete())

    def add_exportmenu(self, parent = None):

        # Initialise menu
        menu_export = tk.Menu(parent)
        # Add elements
        menu_export.add_command(label = 'Current', command = self.export_current)
        menu_export.add_command(label = 'All', command = self.export_all)
        
        # Add the cascade to the image menu
        self.add_cascade(label = 'Export as .csv', menu = menu_export)

    def enhancement(self):

        # Check if window exists and raise on top of the other windows
        try:
            self.controller.gw_enhancement.window.lift()
        except (AttributeError, tkinter.TclError):
            # If it doesn't exist, create it
            self.controller.gw_enhancement = EnhancePanel(self.controller)

    def vesdetection(self):

        # Update value of the pre-processing options based on enhancement status fo the channel
        MenuShared.check_enhancement(self.controller)
        # Check if window exists and raise on top of the other windows
        try:
            self.controller.gw_vesdetection.window.lift()
        except (AttributeError, tkinter.TclError):
            # If it doesn't exist, create it
            self.controller.gw_vesdetection = VesdetPanel(self.controller) 
        
        # Check if enhancement panel has been initialised, otherwise, create and destroy it
        # Finally, bind the checkbox for processing with the command that updates the enhancement
        try: 
           self.controller.gw_enhancement
        except AttributeError:
            self.enhancement()
            self.controller.gw_enhancement.window.destroy()
        finally:
            self.controller.gw_vesdetection.smooth_check.config(command = self.update_enhancement)
            self.controller.gw_vesdetection.enhance_check.config(command= self.update_enhancement)

    def update_enhancement(self):

        # Check value of smooth and enhance variable
        smooth_state = self.controller.appdata_settingsvesdet['enhancement'][0].get()
        enhance_state = self.controller.appdata_settingsvesdet['enhancement'][1].get()

        # Always start from the raw image
        current_image = self.controller.appdata_imagesource['image']
        self.controller.gw_maindisplay.clear_showimage(current_image, update_current = True)

        # If either of the values if False, update the enhacement status and text
        if False in [smooth_state, enhance_state]:
            # Clear the enhancement status of the current channel
            MenuShared.reset_enhancement(self.controller)
            # Update text in show image button in vesicle detection
            self.controller.gw_vesdetection.showimgButton.config(text = 'Show Current Image')

        # If smooth is True, smooth the image
        if smooth_state == True:
            self.controller.gw_enhancement.smooth()
            self.controller.gw_vesdetection.showimgButton.config(text = 'Show Original Image')
        if enhance_state == True:
            self.controller.gw_enhancement.enhance()
            self.controller.gw_vesdetection.showimgButton.config(text = 'Show Original Image')

    def export_current(self):

        # Define default filename for saving 
        img_name = self.controller.appdata_imagesource['name']
        initial_file = '{}_detected_vesicles'.format(img_name)

        # Get the detected vesicles for this image, if any. Otherwise, flag with a message
        try: 
            det_results = self.controller.appdata_resultsvesdet[img_name]
        except KeyError:
            print('There are no vesicles detected for this image.')
        else:
            # Get path + filename
            filename = tkinter.filedialog.asksaveasfilename(initialfile = initial_file, 
                                                        defaultextension = '.csv')

            # Export and save file as .csv, skip error upon pressing cancel
            if len(filename) > 4:
                FileExport.vesicle_detection(filename, det_results)
                print(f'Detected vesicles successfully saved in {filename}')

    def export_all(self):

        # Check if there are any results saved
        if self.controller.appdata_resultsvesdet:
            # Get the filename for saving the vesicles
            filedir = tkinter.filedialog.askdirectory()
            if len(filedir) > 1:
                # Get all the results saved, this can include other images. Loop over all the results
                for current_image, det_results in self.controller.appdata_resultsvesdet.items():
                    filename = f'{current_image}_detected_vesicles.csv'
                    # Join the directory and filename
                    full_filename = os.path.join(filedir, filename)
                    FileExport.vesicle_detection(full_filename, det_results)
                print(f'Detected vesicles successfully saved in {filedir}')
        else:
            print('There are no saved results of vesicle detection.')

    def select_delete(self):

        # Function to select and delete the vesicles

        # The variable to use for handling selected object is the vesicle detection results
        # Note: it works with the TEMPORAL results data, so it can only be triggered 
        # from within the vesicle detection panel

        try: 
            det_vesicles = self.controller.appdata_detresultstemp
        except AttributeError:
            pass
        else:
            # Attempt to get the mask of detected results, if it exists
            if hasattr(self.controller, 'appdata_maskdettemp'):
                det_mask = self.controller.appdata_maskdettemp
            else:
                det_mask = None
            # Bind on-pick event with the selection object function of the main display
            state_mpl = self.controller.gw_maindisplay.bind_onpick()
            # Bind right-click event with a delete object function of the main display
            self.controller.gw_maindisplay.bind_right(input_data = det_vesicles, input_mask = det_mask)

class MenuMembrane(tk.Menu):

    def __init__(self, parent = None, controller = None):

        self.controller = controller
        # Initialise menu
        tk.Menu.__init__(self, parent)

        # Add menu elements
        self.add_command(label = 'Basic Segmentation', command = self.basic)
        self.add_command(label = 'Refined Detection', command = self.refined)

    def basic(self):

        # Check if window exists and raise on top of the other windows
        try:
            self.controller.gw_bma.window.lift()
        except (AttributeError, tkinter.TclError):
            self.controller.gw_bma = BmaPanel(self.controller)

        # Show vesicle detection results
        self.show_vesdetresults(trigger_mode = 'bma')

    def show_vesdetresults(self, trigger_mode):

        # Get the detected results and show accordingly
        # Current image
        img_name = self.controller.appdata_imagesource['name']
        # Check if there are any results saved already
        vesdet_results = self.controller.appdata_resultsvesdet.get(img_name, None)
        
        # Show the detected vesicles results accordingly
        if vesdet_results is not None:
            # Get detection method
            det_method = vesdet_results['method']
            # Get the method of detection, to know how to display the results
            if vesdet_results['method'] == 'hough': det_method = 'circle'
            else: det_method = 'box'
            # Update the widget state of the offset accordingly
            if trigger_mode == 'bma':
                self.controller.gw_bma.update_offset(det_method)
                tcolor = 'none'
            elif trigger_mode == 'rmd':
                tcolor = 'white'
            # Show the results
            self.controller.gw_maindisplay.clear_showobject([det_method, vesdet_results['rois']],
                                                        edgecolor = 'gray',
                                                        textcolor = tcolor)
        else:
            print('There are no detected vesicles.')
        
    def refined(self):

        # Check if window exists and raise on top of the other windows
        try:
            self.controller.gw_rmd.window.lift()
        except (AttributeError, tkinter.TclError):
            self.controller.gw_rmd = RmdPanel(self.controller)
        
         # Show vesicle detection results
        self.show_vesdetresults(trigger_mode = 'rmd')

class MenuAnalysis(tk.Menu):

    def __init__(self, parent = None, controller = None):

        self.controller = controller
        # Initialise menu
        tk.Menu.__init__(self, parent)

        # Add menu elements
        self.add_command(label = 'Vesicle Size Distribution', command = self.sizedistribution)
        self.add_command(label = 'Encapsulation Efficiency', command = self.encapefficiency)
        self.add_command(label = 'Intensity Profiles', command = self.intprofiles)

    def sizedistribution(self):

        # Check if window exists and raise on top of the other windows
        try:
            self.controller.gw_vessizedist.window.lift()
        except (AttributeError, tkinter.TclError):
            # If it doesn't exist create it
            self.controller.gw_vessizedist = VesSizePanel(self.controller)
        finally:
            # Compute histogram
            self.controller.gw_vessizedist.compute_histogram(overwrite_minmax=True)

    def encapefficiency(self):

        # Check if window exists and raise on top of the other windows
        try:
            self.controller.gw_encapeff.window.lift()
        except (AttributeError, tkinter.TclError):
            # If it doesn't exist create it
            self.controller.gw_encapeff = EncapPanel(self.controller)

    def intprofiles(self):

        # Check if window exists and raise on top of the other windows
        try:
            self.controller.gw_iprofiles.window.lift()
        except (AttributeError, tkinter.TclError):
            # If it doesn't exist create it
            self.controller.gw_iprofiles = IprofilePanel(self.controller)
            # Update display with the detection results
            self.controller.gw_iprofiles.show_detresults()
        
class MenuBatch(tk.Menu):

    def __init__(self, parent = None, controller = None):

        self.controller = controller
        # Initialise menu
        tk.Menu.__init__(self, parent)

        # Add menu elements
        self.add_command(label = 'Multi-image Processing', command = self.batchprocessing)

    def batchprocessing(self):

        # Check if window exists  and raise on top of the other windows
        try:
            self.controller.gw_batch.window.lift()
        except (AttributeError, tkinter.TclError):
            # If it doesn't exist create it
            self.controller.gw_batch = BatchPanel(self.controller)
            
class MenuShared():

    def check_enhancement(controller = None):

        # Get the current channel settings and the smoothing and enhancement status
        current_channel = controller.appdata_channels['current'].get()
        smooth_channel = controller.appdata_settingsenhance['ch_status'][0]
        enhance_channel = controller.appdata_settingsenhance['ch_status'][1]

        # Update the value of the smoothing status for vesicle detection
        if current_channel in smooth_channel:
            controller.appdata_settingsvesdet['enhancement'][0].set(True)
        else:
            controller.appdata_settingsvesdet['enhancement'][0].set(False)
        # Update the value of the enhancement status for vesicle detection
        if current_channel in enhance_channel:
            controller.appdata_settingsvesdet['enhancement'][1].set(True)
        else:
            controller.appdata_settingsvesdet['enhancement'][1].set(False)

    def reset_enhancement(controller = None):
        
        # Get current channel
        current_channel = controller.appdata_channels['current'].get()
        # Get current tracking channels
        smooth_channels, enhance_channels = controller.appdata_settingsenhance['ch_status']
        
        # Remove all channels if the current_channel = 0
        if current_channel == 0:
            smooth_channels = []
            enhance_channels = []
        else:
            # Remove selected channel
            try: smooth_channels.remove(current_channel)
            except ValueError: pass
            try: enhance_channels.remove(current_channel)
            except ValueError: pass
           
            # remove the 'all channels' option, channel = 0
            try: smooth_channels.remove(0)
            except ValueError: pass
            try: enhance_channels.remove(0)
            except ValueError: pass

        # Set the new channels in teh settings
        controller.appdata_settingsenhance['ch_status'][0] = smooth_channels
        controller.appdata_settingsenhance['ch_status'][1] = enhance_channels
        
    
        
        






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
# Import the filedialog option from tkinter
import tkinter.filedialog

# import custom widgets
import ui_custom_widgets as ctk

# Import functions for vesicle detection
from vesicle_detection import VesicleDetection

# Import function to handle template files
from file_handling import FileTemplate
# Import function to threshold the image
from image_processing import ImageMask

class VesdetPanel():

    def __init__(self, controller = None):
        # As the panel for vesicle detection is a toplevel window it doesn't need
        # a master widget
        # we do need the controller to trigger actions easily
        self.controller = controller

        # Initialise the vesicle detection window
        detpanel = ctk.ControlPanel(title = 'Vesicle Detection')

        # Configure window layout
        detpanel.configure_layout(cols = [0], rows = [0,1,2])

        # Create frame containers for widgets
        f_pre = ttk.LabelFrame(detpanel, text = 'Image pre-processing')
        f_main = ttk.Frame(detpanel)
        f_vis = ttk.LabelFrame(detpanel, text = 'Visualization')

        # Place frames in window
        for n, iframe in enumerate([f_pre, f_main, f_vis]):
            iframe.grid(row = n, column = 0, columnspan = 2, sticky = 'nsew', padx = 5, pady = 5)
            iframe.columnconfigure([0,1], weight = 1)
            iframe.rowconfigure(0, weight = 1)

        # create notebook with detection options
        detNotebook = ttk.Notebook(f_main)
        detNotebook.add(self.create_houghpanel(detNotebook, controller), text = 'Hough Detection')
        detNotebook.add(self.create_templatepanel(detNotebook, controller), text = 'Template Matching')
        detNotebook.add(self.create_floodpanel(detNotebook, controller), text = 'Floodfill')

        # Bind event for keeping track of the method (notebook tab) being used
        detNotebook.bind('<<NotebookTabChanged>>', lambda event: self.update_method(detNotebook))
        
        # Place the notebook
        detNotebook.grid(row = 0, column = 0, sticky = 'nsew', padx = 2, pady = 2)

        # Create pre-processing options and place them
        smooth_cbox = ttk.Checkbutton(f_pre, text = 'Smoothing', 
                            variable = controller.appdata_settingsvesdet['enhancement'][0])
        enhance_cbox = ttk.Checkbutton(f_pre, text = 'Enhancement',
                            variable = controller.appdata_settingsvesdet['enhancement'][1])
        for n, cbox in enumerate([smooth_cbox, enhance_cbox]):
            cbox.grid(row = 0, column = n, sticky = 'nsew', padx = 5, pady = 2)

        # create visualization options and place them
        showdet_button = ttk.Button(f_vis, text = 'Show Detection', command = lambda: self.update_display(update_source = 'results'))
        showimg_button = ttk.Button(f_vis, text = 'Show Original Image', command = lambda: self.update_display(update_source = 'image'))
        for n,b in enumerate([showdet_button, showimg_button]):
            b.grid(row = 0, column = n, sticky = 'nsew', padx = 5, pady = 5)

        # save button
        save_button = ttk.Button(detpanel, text = 'Save', command = self.save)
        save_button.grid(row = 3, column = 0, sticky = 'nse', padx = 5, pady = 5)

        # close button (note this is only the frame where the button is placed!)
        detpanel.closeButton.grid(row = 3, column = 1, sticky = 'nsew', padx = 5, pady = 5)

        # Bind event to close button, to delete the temporal results stored
        # We first need to get the actual button from the closeButton frame
        close_button = detpanel.closeButton.children['!button']
        close_button.bind("<Button>", lambda event: self.delete_tempresults(), add="+")
        
        # Keep track of window, checkbuttons, and visualisation buttons
        self.window = detpanel
        self.smooth_check = smooth_cbox
        self.enhance_check = enhance_cbox
        self.showdetButton = showdet_button
        self.showimgButton = showimg_button

        # Initialise temporal results with last saved results
        self.init_tempresults()
    
    def create_houghpanel(self, parent = None, controller = None):
        # Frame with detection options for hough method
        houghframe = ttk.Frame(parent)

        # configure layout of frame
        houghframe.columnconfigure([0,1,2,3], weight = 1)
        houghframe.rowconfigure([0,1,2], weight = 1)

        # Create Labels
        labels_opt = ['Edge threshold: ', 'Hough threshold: ', 'Min. distance: ', 
                    'Min. radius: ', 'Max. radius: ']
        labels_widgets = []
        for ilabel in labels_opt:
            labels_widgets.append(ttk.Label(houghframe, text = ilabel))
    
        # Create entries
        settings_hough = controller.appdata_settingsvesdet
        entry_var = [settings_hough[x] for x in settings_hough.keys() if 'hough' in x]
        entry_widgets = []
        for ientry in range(len(labels_opt)):
            entry_widgets.append(ttk.Entry(houghframe, width = 5, textvariable=entry_var[ientry]))

        # Place widgets
        for n, w in enumerate(labels_widgets[0:3]):
            w.grid(row = n, column = 0, sticky = 'ew', padx = 5, pady = 10)
        for n, w in enumerate(entry_widgets[0:3]):
            w.grid(row = n, column = 1, sticky = 'ew', padx = 5, pady = 10)
        for n, w in enumerate(labels_widgets[3:]):
            w.grid(row = n, column = 2, sticky = 'ew', padx = 5, pady = 10)
        for n, w in enumerate(entry_widgets[3:]):
            w.grid(row = n, column = 3, sticky = 'ew', padx = 5, pady = 10)

        # Create run button and place it
        run_button = ttk.Button(houghframe, text = 'Run', command = self.run)
        run_button.grid(row = 2, column = 2, columnspan = 2, sticky = 'ew', padx = 5, pady = 10)

        return houghframe

    def create_templatepanel(self, parent = None, controller = None):
        # Frame with detection options for template maching
        templateframe = ttk.Frame(parent)

        # configure layout of the frame
        templateframe.columnconfigure(0, weight = 1)
        templateframe.rowconfigure(0, weight = 1)

        # create and place label frames that contain all of the options
        templateopt = ttk.LabelFrame(templateframe, text = 'Template Options')
        matchingopt = ttk.Frame(templateframe)

        for n, opt_frame in enumerate([templateopt, matchingopt]):
            opt_frame.grid(row = n, column = 0, sticky = 'nsew', padx = 2, pady = 5)
        
        # configure layout of frames
        templateopt.rowconfigure(0, weight  = 1)
        templateopt.columnconfigure([0,1,2,3], weight = 1)
        matchingopt.rowconfigure([0,1,2], weight = 1)
        matchingopt.columnconfigure([0,1,3,4,5], weight = 1)

        # create buttons for template options
        load_button = ttk.Button(templateopt, text = 'Load', width = 5, command = self.load_template)
        set_button = ttk.Button(templateopt, text = 'Set', width = 5, command = self.set_template)
        show_button = ttk.Button(templateopt, text = 'Show', width = 5, command = self.show_template)
        save_button = ttk.Button(templateopt, text = 'Save', width = 5, command = self.save_template)

        for n, b in enumerate([set_button, load_button, show_button, save_button]):
            b.grid(row = 0, column = n, sticky = 'nsew', padx = 2, pady = 5)
        
        # Create labels for matching options
        labels_opt = ['Resize range:', 'Number of scales:', 'Threshold match:' ]
        labels_widgets = []
        for ilabel in labels_opt:
            labels_widgets.append(ttk.Label(matchingopt, text = ilabel))
        
        # Create entry widgets for matching options
        settings_det = controller.appdata_settingsvesdet
        entry_var = [settings_det[x] for x in settings_det.keys() if 'template' in x]
        entry_widgets = []
        for ientry in range(len(labels_opt)+1):
            entry_widgets.append(ttk.Entry(matchingopt, width = 4, textvariable = entry_var[ientry]))
        
        # Place matching options labels
        rows_labels = [0,1,0]
        columns_labels = [0,0,4]
        columnspan_labels = [1,2,1]
        for n, w in enumerate(labels_widgets):
            w.grid(row = rows_labels[n], column = columns_labels[n], columnspan = columnspan_labels[n],
                    sticky = 'nsew', padx = 2, pady = 2)
        # Place matching options entries
        rows_entries = [0,0,1,0]
        columns_entries = [1,3,2,5]
        columnspan_entries = [1,1,2,1]
        for n, w in enumerate(entry_widgets):
            w.grid(row = rows_entries[n], column = columns_entries[n], 
                    columnspan = columnspan_entries[n], sticky = 'nsew', padx = 3, pady = 2)

        # Add a dash label to separate resize range
        d_label = ttk.Label(matchingopt, text = '-')
        d_label.grid(row = 0, column = 2, sticky = 'ew')

        # Create buttons to rn detection and place them
        rundet_button = ttk.Button(matchingopt, text = 'Run Detection', command = self.run)
        rundet_button.grid(row = 1, column = 4, columnspan = 2, sticky = 'nsew', padx = 5, pady = 2)
        
        return templateframe

    def create_floodpanel(self, parent = None, controller = None):
        # Frame with detection options for floodfill
        floodframe = ttk.Frame(parent)

        # Configure layout of the frame
        floodframe.columnconfigure(0, weight = 1)
        floodframe.rowconfigure(0, weight = 1)

        # Create label frames, for better visualisation
        maskoptFrame = ttk.LabelFrame(floodframe, text = 'Image thresholding')
        detFrame = ttk.LabelFrame(floodframe, text = 'Flooding options')

        maskoptFrame.grid(row = 0, column = 0, sticky = 'ew', padx = 5, pady = 5)
        detFrame.grid(row = 1, column = 0, sticky = 'ew', padx = 5, pady = 5)

        # Configure label frame layout
        for iframe in [maskoptFrame, detFrame]:
            iframe.rowconfigure(0, weight = 1)
            iframe.columnconfigure([0,2], weight = 1)

        # Create and place binarisation options
        thLabel = ttk.Label(maskoptFrame, text = 'Threshold: ')
        thEntry = ttk.Entry(maskoptFrame, width = 5, 
                            textvariable = controller.appdata_settingsvesdet['flood_th'])
        thButton = ttk.Button(maskoptFrame, text = 'Show threshold', command = self.show_threshold)

        for n,w in enumerate([thLabel, thEntry, thButton]):
            w.grid(row = 0, column = n, sticky = 'nsew', padx = 5, pady = 5)
        
        
        # Create and place flooding widgets
        minaLabel = ttk.Label(detFrame, text = 'Minimal area: ')
        minaEntry = ttk.Entry(detFrame, width = 5, 
                            textvariable = controller.appdata_settingsvesdet['flood_minarea'])
        runButton = ttk.Button(detFrame, text = 'Run Detection', command = self.run)
        
        for n, w in enumerate([minaLabel, minaEntry, runButton]):
            w.grid(row = 0, column = n, sticky = 'nsew', padx = 5, pady = 5)
        
        
        return floodframe

    def update_method(self, notebook):
        # Update the vesicle detection method based on the selected tab

        # Get current tab selected
        current_tab = notebook.index('current')

        # Update the method based on the tab
        det_methods = ['hough', 'template', 'floodfill']
        current_method = det_methods[current_tab]

        # Update value in the settings
        self.controller.appdata_settingsvesdet['method'] = current_method

    def run(self):

        # Get settings for the vesicle detection
        det_settings = self.controller.appdata_settingsvesdet
        # Check if the image is the right dimension
        mat_image = self.check_image(self.controller)

        # Get the current detection method to run
        current_method = det_settings['method']
        # configure the text of the show results button
        self.showdetButton.config(text = 'Show Detection')

        # Initialise detection results as a None variable
        det_results = None

        # Run detection based on method selected
        if current_method == 'hough':
            # Run hough detection
            hough_circles = VesicleDetection.hough(mat_image, det_settings)
            # If the results are not None, format accordingly
            if hough_circles is not None:
                det_results = ['circle', hough_circles]
        elif current_method == 'template':
            # Get the template image, if no template is set, flag it with a message
            template_image = self.controller.appdata_templateimage
            if template_image is not None:
                # Run the detection based on template matching
                matched_templates = VesicleDetection.template(mat_image, template_image, det_settings)
                # If the results are not None, format accordingly
                if matched_templates is not None:
                    det_results = ['box', matched_templates]
            else:
                print('No template image found.')
        elif current_method == 'floodfill':
            # Run Floodfill detection
            filled_regions, mask_filled = VesicleDetection.floodfill(mat_image, det_settings)
            # If the results are not None, format accordingly
            if filled_regions is not None:
                det_results = ['center', filled_regions]

        # Update temporal results variable
        self.controller.appdata_detresultstemp = det_results

        # Show results if any
        if det_results is None:
            print('No vesicles were detected with the current settings')
        try: 
            self.controller.appdata_maskdettemp = mask_filled
        except NameError:
            self.update_display(det_results)
        else:
            self.update_display(det_results, mask = mask_filled, update_source = 'image-results')
    
    def check_image(self, controller = None):

        # Check the current channel selected, if it´s multiple, force it to be the first channel
        current_channel = controller.appdata_channels['current'].get()
        if current_channel == 0: 
            mat_image = 1*controller.appdata_imagecurrent[:,:,0]
            print('A single channel needs to be selected. Setting channel 1 as working channel.')
        else:
            try: 
                mat_image = 1*controller.appdata_imagecurrent[:,:, current_channel - 1]
            except IndexError:
                mat_image = 1*controller.appdata_imagecurrent
                
        return mat_image

    def load_template(self):

        # Define options or loading the template image
        options = {}
        options['defaultextension'] = '.tif'
        # At the moment it should accept only TIFF and PNG format
        options['filetypes'] = [('TIFF Files', ('.tif', '.tiff')),
                                ('PNG Files', '.png')]
        options['title'] = 'Load Template' 
            
        # Open dialog where user can select the file to be opened
        filename = tkinter.filedialog.askopenfilename(**options)
        try:
            template_image = FileTemplate.read(filename)
            # Update image in appdata
            self.controller.appdata_templateimage = template_image
        except AttributeError:
            template_image = None
        
        # If the template is loaded, check if the window to display it is opened
        if template_image is not None:
            try: 
                self.controller.gw_template.windisplay.clear_showimage(template_image, cmap = 'gray', channel = 1)
            except AttributeError:
                pass
     
    def show_template(self):

        # Check if window exists and raise on top of the other windows
        try:
            self.controller.gw_template.lift()
        except (AttributeError, tkinter.TclError):
            # If it doesn't exist, create it
            self.controller.gw_template = ctk.WindowFullCanvas(title = 'Template Image')

        # Check if there's a template image, and show it
        if self.controller.appdata_templateimage is not None:
            self.controller.gw_template.windisplay.clear_showimage(self.controller.appdata_templateimage, 
                                                cmap = 'gray', channel = 1)

    def set_template(self):

        # Get the current working image, checking if it's single channel or not
        mat_image = self.check_image(self.controller)
      
        # Get the limits of the image shown in display - should be zoomed in for template
        # the Ylim needs to be reversed due to imshow orientation
        x1, x2 = self.controller.gw_maindisplay.axis_img.get_xlim()
        y2, y1 = self.controller.gw_maindisplay.axis_img.get_ylim()

        # Make sure the limits are within the image size
        if int(x1) < 0: x1 = 0
        if int(y1) < 0: y1 = 0
        if int(x2) > mat_image.shape[1]: x2 = mat_image.shape[1]
        if int(y2) > mat_image.shape[0]: y2 = mat_image.shape[0]

        # Assign shown (zoomed) image as template
        template_image = mat_image[int(y1):int(y2), int(x1):int(x2)]
        self.controller.appdata_templateimage = template_image

        # If show template window exists update
        try:
            self.controller.gw_template.state()
        except (AttributeError, tkinter.TclError):
            pass
        else:
            self.controller.gw_template.windisplay.clear_showimage(template_image, cmap = 'gray', channel = 1)
    
        # Reset main display with current working image
        try: 
            self.controller.gw_maindisplay.clear_showimage(mat_image)
        except IndexError:
            self.controller.gw_maindisplay.clear_showimage(self.controller.appdata_imagecurrent)

    def save_template(self):

        # Get the current template image
        template_image = self.controller.appdata_templateimage
        
        if template_image is not None:
            # Define default filename for saving
            img_name = self.controller.appdata_imagesource['name']
            initialfile = f'{img_name}_template.tiff'

            # Open dialog where user can select the file to saved in
            save_options = {}
            save_options['title'] = 'Save Template As'
            save_options['initialfile'] = initialfile
            filename = tkinter.filedialog.asksaveasfilename(**save_options)

            try: 
                filename[1]
            except IndexError:
                pass
            else:
                FileTemplate.save(filename, template_image)
        else:
            print('There is no template image currently set.')

    def show_threshold(self):

        # Check if image is the right dimension
        mat_image = self.check_image(self.controller)
        # Get the threshold from settings
        threshold = self.controller.appdata_settingsvesdet['flood_th'].get()
        # Get the binary image with the desired threshold
        img_threshold = ImageMask.threshold(mat_image, threshold)

        # Display the binary image
        self.controller.gw_maindisplay.clear_showimage(img_threshold, cmap = 'gray', channel = 1)
        
    def update_display(self, det_results = None, **kwargs):

        # Update display according to visualization options

        # Get the controller and the buttons
        controller = self.controller
        image_button = self.showimgButton
        results_button = self.showdetButton

        # Get detection method used
        det_method = controller.appdata_settingsvesdet['method']
        # Get the source of display update, if both desired, then 'image-results' should be specified
        update_source = kwargs.get('update_source', 'results')
        # Get the mask for floodfill
        mask = kwargs.get('mask', None)

        # If the method is floodfill, attempt to get the mask
        if det_method == 'floodfill' and mask is None:
            try: 
                mask = controller.appdata_maskdettemp
            except AttributeError:
                pass
        
        # First check if the image is to be updated
        if 'image' in update_source:
            # Check status of image button to know which image to show
            if 'Current' in image_button.cget('text'):
                display_img = controller.appdata_imagecurrent
                # Text to configure the button with
                text_button = image_button.cget('text').replace('Current', 'Original')
            else:
                display_img = controller.appdata_imagesource['image']
                # Text to configure the button with
                text_button = image_button.cget('text').replace('Original', 'Current')
            # Configure text of the button
            image_button.config(text = text_button)
            # Show image in current channel
            controller.gw_maindisplay.clear_showimage(display_img)
            # Configure state of the results button to also show the detection if needed
            if 'Hide' in results_button.cget('text'):
                update_source = 'results'
                results_button.config(text = 'Show Detection')

        # Get last accessible detection results if they're not speficied
        if det_results is None and 'results' in update_source:
            try: 
                det_results = controller.appdata_detresultstemp
            except AttributeError:
                print('There are no results for vesicle detection available.')
                update_source = 'None'
        
        # Now check if the results are to be updated
        if 'results' in update_source:
            # attempt to remove any mask that has been overlaid
            try:
                controller.gw_maindisplay.s_mask.remove()
            except (AttributeError, ValueError) as e:
                pass
            # Check status of results button to know if to show/hide the results
            if 'Show' in results_button.cget('text'):
                # Check if floodfill has been used, then overlay the mask
                if det_method == 'floodfill':
                    controller.gw_maindisplay.overlay_mask(mask, alpha = 0.3)
                # Show results
                controller.gw_maindisplay.clear_showobject(det_results)
                # Text to configure the button with
                text_button = results_button.cget('text').replace('Show', 'Hide')
            else:
                # Clear the results
                controller.gw_maindisplay.clear_showobject(drawn_object = None)
                # text to configure the button with
                text_button = results_button.cget('text').replace('Hide', 'Show')
            # Configure the text in the button
            results_button.config(text = text_button)

    def save(self):

        # Type of results
        type_results = self.controller.appdata_detresultstemp[0]
        # Get the results
        detected_vesicles = self.controller.appdata_detresultstemp[1]
        # Attempt to get the mask from floodfill
        try:
            mask_floodfill = self.controller.appdata_maskdettemp
        except AttributeError:
            mask_floodfill = None

        # Get the method used to detect the vesicles
        if type_results == 'circle': det_method = 'hough'
        elif type_results == 'box': det_method = 'template'
        else: det_method = 'floodfill'

        # Format the results as a dictionary with the correct input
        det_results = VesicleDetection.save_results(detected_vesicles, det_method, mask_floodfill)

        # Get current image name to use as a key in the dictionary
        img_name = self.controller.appdata_imagesource['name']            
        # Save detected vesicles for further analysis
        self.controller.appdata_resultsvesdet[img_name] = det_results

        # Print message confirming the assignment
        print(f'Objects detected using {det_method} detection have been assigned as detected vesicles.')

        # Enable analysis menu
        submenu = self.controller.children['!menumain'].children['!menuanalysis']
        self.controller.children['!menumain'].setstate_all(submenu, set_state = 'normal')

        # Enable membrane segmentation menu
        submenu = self.controller.children['!menumain'].children['!menumembrane']
        self.controller.children['!menumain'].setstate_all(submenu, set_state = 'normal')

    def init_tempresults(self):

        # Check if any results have been saved, and retrieve them as temporal results
        # for the purpose of displaying them

        # Current image
        img_name = self.controller.appdata_imagesource['name']
        # Check if there are any results saved already
        saved_results = self.controller.appdata_resultsvesdet.get(img_name, None)

        if saved_results is not None:
            # Print a message to let the user know that there are already results found
            print('Results have been found for detected vesicles in this image.')
            if saved_results['method'] == 'hough': det_method = 'circle'
            elif saved_results['method'] == 'template': det_method = 'box' 
            else: det_method = 'center'

            self.controller.appdata_detresultstemp = [det_method, 
                                                    saved_results['rois']]
            try:
                self.controller.appdata_maskdettemp = saved_results['mask_rois']
            except KeyError:
                pass

            # Update display with the found results
            self.update_display(update_source = 'results')
            
    def delete_tempresults(self):

        # Disconnect canvas if it was connected to pick event
        try:
            self.controller.gw_maindisplay.canvas.mpl_disconnect(self.controller.gw_maindisplay.cid_pick)
        except AttributeError:
            pass
        else:
            self.controller.gw_maindisplay.canvas.mpl_disconnect(self.controller.gw_maindisplay.cid_right)
            del self.controller.gw_maindisplay.cid_pick, self.controller.gw_maindisplay.cid_right

        # Erase the results that were stored in the temporal variable
        try: 
            del self.controller.appdata_detresultstemp
        except AttributeError:
            pass
        
        # Delete the floodfill temp results, if any
        try:
            del self.controller.appdata_maskdettemp
        except AttributeError:
            pass

        # Try to remove the masks from floodfill
        try:
            self.controller.gw_maindisplay.s_mask.remove()
        except (AttributeError, ValueError) as e:
            pass
        # Try to remove the previous results
        self.controller.gw_maindisplay.clear_showobject(drawn_object = None)

        



        
        

        


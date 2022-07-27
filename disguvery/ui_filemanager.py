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
import os
# Import custom widgets
import ui_custom_widgets as ctk
from file_handling import FileImage

class FileManager():

    def __init__(self, controller = None):
        # As the file manager is a toplevel window it doesn't have a master widget
        # We do need the controller to be able to manage the listbox easily
        self.controller = controller

        # Initialise the file manager window and keep track of it
        filemanager = ctk.ControlPanel(title = 'File Manager', resizable = (1,1))
        self.window = filemanager

        # configure Layout of the window
        filemanager.configure_layout(cols = [0,1], rows = [0])

        # Create frame containers for widgets
        [fdir, fimg, fbuttons] = filemanager.create_frames(3)

        # Configure layout of frames where lists are
        for iframe in [fdir, fimg]:
            iframe.columnconfigure(0, weight = 1)
            iframe.rowconfigure(0, weight = 1)
        
        # Place frames in window
        for n, iframe in enumerate([fdir, fimg, fbuttons]):
            iframe.grid(row = 0, column = n, sticky = 'nsew', padx = 2, pady = 2)
        # Place close button
        filemanager.closeButton.grid(row = 1, column = 0, columnspan = 3, sticky = 'nsew')
        # bind event to close button, to clear the display. Need to get the actual button from the frame
        close_button = filemanager.closeButton.children['!button']
        close_button.bind('<Button>', lambda event: self.close_panel(), add = '+')


        # create the labeled lists in each frame and place them
        dirList = ctk.FramedList(fdir, text = 'Available Directories')
        imgList = ctk.FramedList(fimg, text = 'Available Images')
        dirList.grid(row = 0, column = 0, sticky = 'nsew')
        imgList.grid(row = 0, column = 0, sticky = 'nsew')

        # Keep track of the framed lists objects 
        self.dirList = dirList.framed_list
        self.imgList = imgList.framed_list

        # create buttons in each frame
        previewButton = ttk.Button(fbuttons, text = 'Preview', command = self.preview)
        removeimgButton = ttk.Button(fbuttons, text = 'Remove Image', command = self.remove_image)
        setcurrentButton = ttk.Button(fbuttons, text = 'Set as Current', command = self.set_current)

        # Place buttons
        buttons_to_place = [previewButton, removeimgButton, setcurrentButton]
        for n, ibutton in enumerate(buttons_to_place):
            ibutton.grid(row = n, column = 0, sticky = 'nsew', padx = 5, pady = 5)

    def add_directories(self, image_info):

        # Get all of the available directories
        try:
            dir_list = set([image_info[x]['directory'] for x in image_info.keys()])
        except KeyError:
            dir_list = []

        # Add directories to the listbox
        self.clear_additems(self.dirList, dir_list)

    def add_images(self, image_info, current_dir):

        # Get all the images from the current directory
        try:
            img_list = [x for x in image_info.keys() if image_info[x]['directory'] == current_dir]
        except KeyError:
            img_list = []

        # Add images to the listbox
        self.clear_additems(self.imgList, img_list)

    def clear_additems(self, listbox, items_toadd):

        # Clear all the items in the listbox
        listbox.delete(0, 'end')
        # Add all the items to the listbox
        for i in items_toadd:
            listbox.insert('end', i)

    def show_ascurrent(self, source_list, string_to_match):
        
        if source_list == 'directory': listbox = self.dirList
        elif source_list == 'image': listbox = self.imgList

        for ic, item in enumerate(listbox.get(0, 'end')):
            if item == string_to_match: fg_color = 'green'
            else: fg_color = 'black'
            listbox.itemconfig(ic, foreground = fg_color)

    def remove_image(self):

        # Get selected image
        item_selected = self.imgList.curselection()
        image_name = self.imgList.get(item_selected)
        # Remove item from dictionary of image info
        info_removed = self.controller.appdata_imageinfo.pop(image_name)
        # Remove from vesicle detection results
        vesdet_results = self.controller.appdata_resultsvesdet.pop(image_name, None)
        # Remove from membrane segmentation results
        memseg_results = self.controller.appdata_resultsmembrane.pop(image_name, None)

        # Remove the item from the list
        self.imgList.delete(item_selected)

        # Check if image was the current one and change to last image if necessary
        if image_name == self.controller.appdata_imagesource['name']:
            self.imgList.selection_set('end')
            self.set_current()

        # Get the results associated to the image, to raise the outcome in the printed message
        del_results = '' 
        if vesdet_results is not None: del_results += 'vesicle detection, '
        if memseg_results is not None: del_results += 'membrane segmentation'
        if '' == del_results: del_results += 'No'

        

        # Print a message to say which image was removed
        print(f'Image {image_name} has been removed from the image data. {del_results} results have been removed.')

    def set_current(self):

        # Get selected image
        new_current_item = self.imgList.curselection()
        new_current_img = self.imgList.get(new_current_item)

        # Show the item as current in the list
        self.show_ascurrent('image', new_current_img)

        # Read the information from the current image
        source_image = self.read_selected(new_current_img)

        # Update imagesource dictionary and current image variable
        self.controller.appdata_imagesource = {'image': source_image, 
                                                'name': new_current_img}
        # Update the display and set the current image
        self.controller.gw_maindisplay.clear_showimage(source_image, update_current = True)

    def preview(self):

        # Get selected image
        selected_item = self.imgList.curselection()
        selected_img = self.imgList.get(selected_item)

        # Read the information from the current image
        source_image = self.read_selected(selected_img)

        # Update the display without updating the current image
        self.controller.gw_maindisplay.clear_showimage(source_image, update_current = False)

    def read_selected(self, selected_img):

        # Read the information from the selected image
        img_dir = self.controller.appdata_imageinfo[selected_img]['directory']
        img_ext = self.controller.appdata_imageinfo[selected_img]['extension']
        filename = os.path.join(os.path.normpath(img_dir), f'{selected_img}.{img_ext}')

        # Read the image
        img_info, img_n, source_image = FileImage.open(filename, verbose = False)

        return source_image

    def close_panel(self):

        # When closing the panel, we want to return to the current image visualization
        current_image = self.controller.appdata_imagecurrent
        self.controller.gw_maindisplay.clear_showimage(current_image)


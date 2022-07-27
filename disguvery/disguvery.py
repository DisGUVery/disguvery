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

# Import tkinter
import tkinter as tk
from tkinter import ttk

# Try to import ttkthemes to be able to use their styles
try: from ttkthemes import ThemedStyle
except ModuleNotFoundError: print('ttkthemes not found: using standard OS interface')

# Import the MenuMain class, responsible of adding the elements in the Menu bar
from ui_menu import MenuMain
# Import the CanvasFullImage class responsible of creating main display canvas
from ui_canvas import CanvasFullImage


# Initialise the application
class disGUVery(tk.Frame):
    def __init__(self, master = None):

        # We inherit the tk.Frame class
        tk.Frame.__init__(self, master)

        # Use grid spatial arrangement
        self.grid(sticky = 'nsew')
        # Configure GUI and window layout. 
        # Set "apply_theme" to False if ttkthemes is not wanted
        self.configure_gui(apply_theme = True)
        self.configure_layout()

        # Initialise variables
        self.init_appdata()

        # Add the Menu to the main Window
        self.add_menu()
        # Add the main display to the main Window -> keep track of canvas
        self.gw_maindisplay = self.add_display()

        # Bind key shortcuts
        self.bind_shortcuts()

    def configure_gui(self, apply_theme):
        # Configure display of the main GUI 

        # Apply ttk Themed Style if it's installed (and wanted)
        if apply_theme == True:
            try: self.ttkStyle = ThemedStyle(self)
            except NameError: print('Using standard OS graphical interface')
            else: 
                print('The GUI runs with a ttk.Themed Style. This can affect performance on large data volumes.')
                self.ttkStyle.set_theme('arc')
        
        # Configure initial size of the main window
        self.master.geometry('800x600+50+50')
        # Configure the title of the window
        self.master.title('DisGUVery v1.0')
        # Configure tearoff of menus
        self.master.option_add('*tearOff', False)

    def configure_layout(self):

        # Configure layout of the top window
        # Set weight of the different columns/rows for placing widgets
        top = self.winfo_toplevel()
        top.columnconfigure(0, weight = 1)
        top.rowconfigure(0, weight = 1)

    def init_appdata(self):

        # Image information, for all images opened
        self.appdata_imageinfo = {}
        # Information of the current source image
        self.appdata_imagesource = {'image': None,
                                    'name': ''}
        
        # working image
        self.appdata_imagecurrent = None
        # Information about the image channels
        self.appdata_channels = {'current': tk.IntVar(),
                                1: tk.StringVar(),
                                2: tk.StringVar(),
                                3: tk.StringVar(),
                                4: tk.StringVar()}

        # Information about the colormap
        self.appdata_colormap = {'channels': [None, 'gray', 'hot', 'cividis'], 
                                'current': tk.StringVar()}

        # Information about the membrane enhancement settings
        self.appdata_settingsenhance = {'method': ['Hough Detection',
                                                    'Template Matching',
                                                    'Floodfill'],
                                        'hough': [15, 45], 
                                        'template': [15,45],
                                        'flood': [5, 105],
                                        'current': ['hough', tk.StringVar(value = '15'), tk.StringVar(value = '45')],
                                        'ch_status': [[], []]
                                        }
        
        # Information about the vesicle detection settings
        self.appdata_settingsvesdet = {'enhancement': [tk.BooleanVar(value = False), tk.BooleanVar(value = False)],
                                        'method': 'hough',
                                        'hough_eth': tk.StringVar(value = '60'),
                                        'hough_hth': tk.StringVar(value = '50'),
                                        'hough_mindist': tk.StringVar(value = '200'),
                                        'hough_minrad': tk.StringVar(value = '10'),
                                        'hough_maxrad': tk.StringVar(value = '400'),
                                        'template_minre': tk.StringVar(value = '0.8'),
                                        'template_maxre': tk.StringVar(value = '1.2'),
                                        'template_nscales': tk.StringVar(value = '10'),
                                        'template_thmatch': tk.StringVar(value = '0.5'),
                                        'flood_th': tk.StringVar(value = '10'),
                                        'flood_minarea': tk.StringVar(value = '100')
                                        }
        # Array containing the template image
        self.appdata_templateimage = None

        # Results of the vesicle detection
        self.appdata_resultsvesdet = {}

        # Settings for basic membrane detection
        self.appdata_settingsbma = {'width': tk.StringVar(value = '15'),
                            'contour_position': tk.IntVar(value = 2),
                            'offset': [tk.IntVar(value = 0), tk.StringVar(value = '10')]}
        # Settings for refined membrane detection
        self.appdata_settingsrmd = {'img_filter': tk.StringVar(value = '6'), 
                                    'img_th': [0.05, tk.StringVar(value = '0.1')], 
                                    'vesicle_th': tk.StringVar(value = '0.15'), 
                                    'search_l': tk.StringVar(value = '11'), 
                                    'search_w': tk.StringVar(value = '4'), 
                                    'bbox_margin': tk.StringVar(value = '20')}

        # Results for membrane detection
        self.appdata_resultsmembrane = {}

        # Settings for the vesicle size distribution computation
        self.appdata_settingsvessizedist = {'nbins': tk.StringVar(value = '10'), 
                                            'min' : tk.StringVar(),
                                            'max': tk.StringVar(),
                                            'input_data': tk.IntVar(value = 0)}

        # Settings for the encapsulation efficiency computation
        self.appdata_settingsencap = {'flood_th': tk.StringVar(value = '1.5'),
                                    'flood_minarea': 25, 
                                    'bg_correction': tk.IntVar(value = 0)}      

        # Settings for intensity profile computation
        self.appdata_settingsiprofile = {'angular_profile': [tk.IntVar(value = 1), tk.StringVar(value = '2')],
                                        'angular_channels': [tk.IntVar(value = 1), tk.IntVar(value = 0), tk.IntVar(value = 0)],
                                        'radial_profile': [tk.IntVar(value = 1), tk.StringVar(value = '2')],
                                        'radial_channels': [tk.IntVar(value = 1), tk.IntVar(value = 0), tk.IntVar(value = 0)],
                                        'bg_corr_options': ['None', 'Image mean', 'ROI mean', 'ROI corner', 'ROI center'],
                                        'bg_corr': [tk.StringVar(value = 'None'), tk.StringVar(value = 'None'), tk.StringVar(value = 'None')],
                                        'int_norm': tk.IntVar(value = 0),
                                        'rad_norm': tk.IntVar(value = 0)}   

        # Settings for batch processing
        self.appdata_settingsbatch = {'preprocess': [tk.IntVar(value = 1), tk.IntVar(value = 1)],
                                    'vesdet_method': [tk.StringVar(value = 'Hough Detection'), ['Hough Detection', 'Template Matching', 'Floodfill']],
                                    'vesdet': [tk.IntVar(value = 1), tk.IntVar(value = 1)],
                                    'membrane': [tk.IntVar(value = 1), tk.IntVar(value = 0)],
                                    'intprofiles_an': [tk.IntVar(value = 1), tk.IntVar(value = 0), tk.IntVar(value = 0)],
                                    'intprofiles_rad': [tk.IntVar(value = 1), tk.IntVar(value = 0), tk.IntVar(value = 0)],
                                    'metrics_size':  tk.IntVar(value = 1),
                                    'metrics_encap': [tk.IntVar(value = 1), tk.IntVar(value =  0), 
                                                    [tk.IntVar(value = 1), tk.IntVar(value = 0), tk.IntVar(value = 0)]],
                                    'savedir': tk.StringVar()}

    def add_menu(self):

        # Initialise the main menu
        menubar = MenuMain(self)
        # Add main menu, including the submenus
        self.master.config(menu = menubar)

    def add_display(self):

        # Initialise the main display
        top = self.winfo_toplevel()
        frameDisplay = ttk.Frame(top)
        frameDisplay.grid(row = 0, column = 0, sticky = 'nsew', padx = 2, pady = 10)

        # Initialise canvas
        displaymain = CanvasFullImage(frameDisplay, self)

        return displaymain

    def bind_shortcuts(self):

        # Quit the application
        self.bind_all('<Control-q>', lambda event: self.quit())


# Run the application. Start main loop
if __name__ == '__main__':
    root = tk.Tk()
    # Get the logo and apply it
    root.iconbitmap(False, 'logo/logo-disguvery.ico')
    app = disGUVery(root)
    root.mainloop()




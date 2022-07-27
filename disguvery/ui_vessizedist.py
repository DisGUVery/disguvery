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
# Imporr the filedialog option from tkinter
import tkinter.filedialog

# import numpy
import numpy as np

# import custom widgets
import ui_custom_widgets as ctk
# import custom canvas
from ui_canvas import CanvasEmbeddedPlot

from data_processing import FitData


class VesSizePanel():

    def __init__(self, controller = None):
        # As the panel for vesicle detection is a toplevel window it doesn't need a master widget
        # We do need the controller to trigger actions easily
        self.controller = controller

        # Settings variable
        settings_var = controller.appdata_settingsvessizedist

        # Initialise the vesicle size distribution panel
        sizepanel = ctk.ControlPanel(title = 'Vesicle Size Distribution')

        # Configure layout of the panel
        sizepanel.configure_layout(rows = [1,2,3], cols = [0,1])
        
        # Create frame containers for widgets
        all_frames = [f_data, f_display, f_settings] = sizepanel.create_frames(3)
        col_span = [1,2,2]
        # Place frames in window
        for n, iframe in enumerate(all_frames):
            iframe.grid(row = n, column = 0, sticky = 'nsew', padx = 5, pady = 5, columnspan = col_span[n])
    
        # Configure layout of settings frame
        f_settings.columnconfigure([1,3,5,6,7,8], weight = 1)

        # Create and place elements of data frame
        data_label = ttk.Label(f_data, text = 'Input data: ')
        data_ccheck = ttk.Radiobutton(f_data, text = 'Current', variable = settings_var['input_data'], value = 0)
        data_acheck = ttk.Radiobutton(f_data, text = 'All Images', variable = settings_var['input_data'], value = 1)

        for n,w in enumerate([data_label, data_ccheck, data_acheck]):
            w.grid(row = 0, column = n, sticky = 'nsw', padx = 5, pady = 5)

        # Create and place canvas for plot
        plot_display = CanvasEmbeddedPlot(f_display)

        # Create and place settings widgets
        text_settings = ['N bins: ', 'Min: ', 'Max: ']
        entry_var = [settings_var['nbins'], settings_var['min'], settings_var['max']]
        entry_settings = []
        for n, s in enumerate(text_settings):
            l = ttk.Label(f_settings, text = s)
            l.grid(row = 0, column = 2*n, sticky = 'nsw', padx = 5, pady = 10)
            entry_settings.append(ttk.Entry(f_settings, width = 5, textvariable = entry_var[n]))
            entry_settings[-1].grid(row = 0, column = 2*n + 1, sticky = 'nsew', padx = 5, pady = 10)

        # Create and place buttons
        update_button = ttk.Button(f_settings, text = 'Update', command = self.compute_histogram)
        fit_button = ttk.Button(f_settings, text = 'Fit Data', command = self.fit_data)
        export_button = ttk.Button(f_settings, text = 'Export as .csv', command = self.export)
        
        for n, ibutton in enumerate([update_button, fit_button, export_button]):
            ibutton.grid(row = 0, column = n+6, sticky = 'nsew', padx = 5, pady = 10)
        
        # Place close button
        sizepanel.closeButton.grid(row = 0, column = 1, sticky = 'nse', padx = 5, pady = 5)
        # Bind event to close button to delete the temporal results stored
        close_button = sizepanel.closeButton.children['!button']
        close_button.bind('<Button>', lambda event: self.delete_tempresults(), add = '+')

        # Keep track of window and canvas elements
        self.window = sizepanel
        self.display = plot_display
        
    def compute_histogram(self, overwrite_minmax = False):

        # Erase fit data
        try:
            del self.controller.appdata_vessizefittemp
        except AttributeError:
            pass

        # Settings variable
        settings_var = self.controller.appdata_settingsvessizedist

        # Get the input data depending on the user choice
        if settings_var['input_data'].get() == 0:
            img_name = self.controller.appdata_imagesource['name']
            input_data = self.controller.appdata_resultsvesdet[img_name]
            method_det = input_data['method']
            size_data = input_data['rois'][:,2]
        elif settings_var['input_data'].get() == 1:
            # If all images are required, the results are compiled 
            size_data = []
            method_old = ''
            for results in self.controller.appdata_resultsvesdet.values():
                method_new = results['method']
                if method_old not in method_new:
                    print('Different methods have been used for vesicle detection. Size distribution cannot be computed')
                    size_data = None
                    break
                else:
                    method_old = method_new
                    size_data.extend(results['rois'][:,2])
            if size_data is not None:
                size_data = np.array(size_data)
                method_det = method_new    
        
        # Set the x label depending on the  method of detection
        if method_det == 'hough': xdata_label = 'r (pix)'
        elif method_det == 'template': xdata_label = 's (pix)'
        elif method_det == 'floodfill': xdata_label = 'major axis length (pix)'

        # Get the parameters to compute the histogram
        n_bins = int(settings_var['nbins'].get())

        try: 
            xmin = float(settings_var['min'].get())
        except ValueError:
            xmin = np.min(size_data)
            settings_var['min'].set(xmin)
        try:
            xmax = float(settings_var['max'].get())
        except ValueError:
            xmax = np.max(size_data)
            settings_var['max'].set(xmax)

        # If overwrite min/max values is True (e.g, when creating panel again)
        if overwrite_minmax is True:
            xmin = np.min(size_data)
            settings_var['min'].set(xmin)
            xmax = np.max(size_data)
            settings_var['max'].set(xmax)
        # Compute histogram with the desired bin array
        try:
            histo, bins = np.histogram(size_data, bins = n_bins, range = (xmin, xmax))
        except ValueError:
            print('Min. value needs to be smaller than Max. value, and n bins larger than 0')
        else:
            # Get center of beans
            bins_center = np.mean([bins[1:], bins[:-1]], axis = 0)
            # Plot histogram
            self.display.plot_histogram(bins_center, histo, x_label = xdata_label)

            # Save the histogram and the bins data temporally
            self.controller.appdata_vessizedisttemp = [[bins_center, histo], len(size_data)]

    def fit_data(self):

        # Get data to fit from temporal variable
        x, y = self.controller.appdata_vessizedisttemp[0]
        n = self.controller.appdata_vessizedisttemp[1]

        # Fit the data
        fit_param, fit_histo = FitData.histo_gauss(x, y)

        # Store the fit results in a temporal variable
        self.controller.appdata_vessizefittemp = fit_histo[0]

        # Format the dictionary with the fit parameters
        fit_param_dict = {'Mean (pix)': [fit_param[0][1], np.sqrt(fit_param[1][1,1])], 
                          'Stdev (pix)': [fit_param[0][2], np.sqrt(fit_param[1][2,2])],
                          'n': n}

        # Plot the fit with 10x more points than x
        x_new = np.linspace(x[0], x[-1], 10*len(x))
        self.display.plot_fit(x_new, fit_histo[1], fit_param_dict)

    def delete_tempresults(self):

        # Erase the results that were stored on the temporal variable
        try:
            del self.controller.appdata_vessizedisttemp
        except AttributeError: 
            pass
        
        # Delete the fit data that was stored on the temporal variable
        try:
            del self.controller.appdata_vessizefittemp
        except AttributeError:
            pass

    def export(self):

        # Define default filename for saving
        if self.controller.appdata_settingsvessizedist['input_data'].get() == 0:
            img_name = self.controller.appdata_imagesource['name']
            initial_file = '{}_size_distribution'.format(img_name)
        else:
            initial_file = 'Results_size_distribution'

        # Get the fitted data
        try: 
            fit_dist = self.controller.appdata_vessizefittemp
        except AttributeError:
            fit_dist = None

        # Get the results for vesicle size distribution. These are only stored temporally while the panel is opened
        try:
            size_dist = self.controller.appdata_vessizedisttemp[0]
        except AttributeError:
            print('No results available for export.')
        else:
            # Get path + filename
            filename = tkinter.filedialog.asksaveasfilename(initialfile = initial_file, defaultextension = '.csv')

            # Export and save file as .csv, skip error upon pressing cancel
            if len (filename) > 4:
                if fit_dist is None:
                    string_header = 'Size (pix), Counts'
                    size_dist = np.stack((size_dist[0], size_dist[1]), axis = 1)
                else:
                    string_header = 'Size (pix), Counts, Fitted Data'
                    size_dist = np.stack((size_dist[0], size_dist[1], fit_dist), axis = 1)
                # Save results 
                np.savetxt(filename, size_dist, header = string_header, fmt = '%i', delimiter = ',')
                print(f'Size distribution saved in {filename}')
                




        

        


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

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import numpy as np

from display import ImageDisplay, ObjectDisplay

class CanvasFullImage():

    def __init__(self, frame_container, controller = None):
        self.controller = controller

        # Configure layout of frame
        frame_container.columnconfigure(0, weight = 1)
        frame_container.rowconfigure(1, weight = 1)

        # Initialize figure and adjust subplot area to maximize display
        fig = Figure(facecolor = [0.15, 0.15, 0.16])
        fig.subplots_adjust(left = 0.0, bottom = 0.0, 
                            right = 1.0, top = 1.0, 
                            wspace = 0, hspace = 0)

        # Initialize subplot area, without axis
        axis_img = fig.add_subplot(111)
        axis_img.axis('off')

        # Add canvas to the figure within the frame of the window
        canvas = FigureCanvasTkAgg(fig, master = frame_container)
        frame_canvas = canvas.get_tk_widget()
        frame_canvas.grid(row = 1, column = 0, sticky = 'nsew')

        # Add matplotlib toolbar to the figure within the frame of the window
        frame_itoolbar = ttk.Frame(frame_container)
        frame_itoolbar.grid(row = 0, column = 0, sticky = 'nsew')
        t_img = NavigationToolbar2Tk(canvas, frame_itoolbar)

        # Store canvas and axis image in object
        self.canvas = canvas
        self.axis_img = axis_img

    def clear_axis(self):

        # clear axis
        self.axis_img.clear()        
        # Take off axis
        self.axis_img.axis('off')

    def clear_showimage(self, img, **kwargs):

        # Get image axis, colormap and channels for display
        img_axis = kwargs.get('axis_img', self.axis_img)

        # Get the display settings from the app. This only works for the main display
        # If the dislay is from a different window, there are no settings, and they need to be specified
        display_settings = ['cmap', 'channel']
        try:
            display_settings[0] = self.controller.appdata_colormap['channels']
        except AttributeError as e:
            display_settings = [None, None]
        else:
            display_settings[1] = self.controller.appdata_channels['current'].get()

        # Get colormap options
        cmap_options = kwargs.get('cmap', display_settings[0])
        # Get current channel
        current_channel = kwargs.get('channel', display_settings[1])

        # Set the image to the current channel and correct the colormap if necessary
        if current_channel != 0:
            try:
                img = img[:,:,current_channel - 1]
            except IndexError as e:
                if type(cmap_options) == str:
                    cmap_options = [None, cmap_options]

        # Clear the previous shown image and show new image, keep displayed image object
        try:
            self.s_img.remove()
        except (AttributeError, ValueError):
            pass
        
        self.s_img = ImageDisplay.show_image(img, img_axis, cmap_options, current_channel)
        self.canvas.draw()

        # If required, update the current working image
        update_current = kwargs.get('update_current', False)
        if update_current == True:
            self.shown_ascurrent(img, current_channel)

    def clear_showobject(self, drawn_object, **kwargs):

        # Get image axis where to display
        img_axis = kwargs.get('axis_img', self.axis_img)
        # Get label of old artist objects
        label_old = kwargs.get('label_old', 'vesicle')
       
        # Clear old patch objects
        if label_old == 'all':
            old_objects = [x for x in img_axis.patches]
            old_text = [x for x in img_axis.texts]
        else:
            old_objects = [x for x in img_axis.patches if label_old == x.get_label()]
            old_text = [x for x in img_axis.texts if label_old in x.get_label()]

        for patch in old_objects:
            img_axis.patches.remove(patch)
        for s in old_text:
            img_axis.texts.remove(s)

        # If the drawn_object is not none, it adds the artists
        if drawn_object is not None: 
            # Draw text with information or the new artist objects
            if drawn_object[0] == 'text_info':
                ObjectDisplay.text_info(drawn_object[1], img_axis, **kwargs)
            else:
                ObjectDisplay.show_object(drawn_object, img_axis, **kwargs)
        
        # Draw canvas
        self.canvas.draw()
        
    def overlay_mask(self, mask, **kwargs):
        
        # Get colormap and alpha options
        colormap = kwargs.get('colormap', 'inferno')
        c_alpha = kwargs.get('alpha', 0.5)

        # Get option to remove old mask
        remove_old = kwargs.get('remove_old', False)
        if remove_old is True:
            try:
                self.s_mask.remove()
            except (AttributeError, ValueError) as e:
                pass

        # Show mask on axis without clearing it
        self.s_mask = self.axis_img.imshow(mask, alpha = c_alpha, cmap = colormap, zorder = 10)

        # Draw canvas
        self.canvas.draw()

    def clear_showscatter(self, scatter_points, **kwargs):

        # Get image axis where to display
        img_axis = kwargs.get('axis_img', self.axis_img)

        # Get label of old artist objects
        label_old = kwargs.get('label_old', 'scatter')
        # Get label of new artist objects
        label_new = kwargs.get('label', 'scatter')

        # Get option to remove old objects
        remove_old = kwargs.get('remove_old', False)

        # Get color for the scatter points
        scolor = kwargs.get('color', 'blue')

        # clear old objects if required
        if remove_old is True:
            old_scatter = [x for x in img_axis.collections if label_old in x.get_label()]
            for s in old_scatter:
                img_axis.collections.remove(s)
        
        # If the scatter points is not none, add the collection with the desired label
        if scatter_points is not None:
            img_axis.scatter(scatter_points[0], scatter_points[1], s = 1, marker = '.',
                            c = scolor, label = label_new)

        # Draw canvas
        self.canvas.draw()
  
    def show_scattermask(self, mask, **kwargs):

        # Get the coordinates of the mask
        ye, xe = np.where(mask)

        # If there is an offset, add it to the coordinates
        offset_points = kwargs.get('offset', [0,0])
        xe = xe + offset_points[0]
        ye = ye + offset_points[1]

        # Get the color for hte points drawn
        point_color = kwargs.get('color', 'orange')
        # By default remove the previous scatter plot
        remove_old = kwargs.get('remove_old', True)
        # Get label to add
        label_scatter =kwargs.get('label', 'scatter')

        # Remove old scatter plot if desired
        if remove_old is True:
            try:
                self.s_smask.remove()
            except (AttributeError, ValueError):
                pass

        # Show the points overlayed
        self.s_smask = self.axis_img.scatter(xe, ye, s = 1, marker = '.', c = point_color, label = label_scatter)

        # Draw canvas
        self.canvas.draw()

    def shown_ascurrent(self, img, channel):

        if (channel == 0) or (self.controller.appdata_imagecurrent.ndim == 2):
            self.controller.appdata_imagecurrent = 1*img
        else:
            self.controller.appdata_imagecurrent[:,:,channel - 1] = 1*img

    def bind_onpick(self, **kwargs):

        # Get additional arguments
        delete_on_disconnect = kwargs.get('delete_on_disconnect', True)
        off_color = kwargs.get('off_color', 'yellow')
        on_color = kwargs.get('on_color', 'skyblue')
        custom_callback = kwargs.get('custom_callback', False)

        # Check if the canvas has been connected to the pick_event
        try:
            self.canvas.mpl_disconnect(self.cid_pick)
        except AttributeError:
            if custom_callback == False:
                # Connect the mpl with the pick event#
                # If the callback is custom, the mpl is connected outside of this function
                self.cid_pick = self.canvas.mpl_connect('pick_event', lambda event: self.select_object(event))
            # Initialise selected objects variable
            self.object_selected = []
            # Configure all the text objects in the canvas to be pickable
            for s in self.axis_img.texts:
                s.set(picker = 20, color = on_color)
            state_mpl = 'connected'
        else:
            del self.cid_pick
            if delete_on_disconnect == True: 
                del self.object_selected
            for s in self.axis_img.texts:
                s.set(picker = False, color = off_color)
            state_mpl = 'disconnected'

        self.canvas.draw()

        return state_mpl

    def bind_right(self, input_data, **kwargs):
        
        # Get the option to add a custom callback
        custom_callback = kwargs.get('custom_callback', False)

        # Check if the canvas has been connected to the right-click event and disconnect
        try:
            self.canvas.mpl_disconnect(self.cid_right)
        except AttributeError:
            if custom_callback == False:
                # If no custom callback is needed, connect the mpl with the right click event 
                self.cid_right = self.canvas.mpl_connect('button_press_event', lambda event: self.delete_selected(event, input_data, **kwargs))
        else:
            del self.cid_right

    def select_object(self, event,**kwargs):

        # Only proceed if the event was triggered with the left click
        if event.mouseevent.button == 1:
            # Get the artist that was selected and highlight it
            selected_object = event.artist
            selected_object.set(color = 'deeppink')
            # Ge the text, it should be equal to the vesicle id
            selected_id = int(selected_object.get_text()) - 1
            # Add selected id to the variable of selected objects
            self.object_selected.append(selected_id)
            
            # Update canvas
            self.canvas.draw()

    def delete_selected(self, event, input_data, **kwargs):

        if event.button == 3:
            # Keep only the unique elements of the object selection and clear original variable
            selected_ids  = list(set(self.object_selected))
            self.object_selected = []

            # Delete the selected objects from input data (input data is numpy array)
            clean_data = np.delete(input_data[1], selected_ids, axis = 0)
            input_data[1] = clean_data

            # Delete the selected objects from the mask data
            mask_data = kwargs.get('input_mask', None)
            if mask_data is not None:
                for s_ind in selected_ids:
                    mask_data[mask_data == (s_ind+1)] = 0
                for ic, ilabel in enumerate(np.unique(mask_data.flatten())[1:]):
                    mask_data[mask_data == ilabel] = ic+1
                self.s_mask.remove()
                self.overlay_mask(mask_data, alpha = 0.3)
            # Update canvas with the clean results
            self.clear_showobject(input_data, textcolor = 'skyblue', pick = 20)

class CanvasEmbeddedPlot():

    def __init__(self, frame_container, controller = None, **kwargs):
        self.controller = controller 

        # Configure layout of frame
        frame_container.columnconfigure(0, weight = 1)
        frame_container.rowconfigure(1, weight = 1)

        # Initialize figure and subplot area
        fig = Figure()
        axis_plot = fig.add_subplot(111)
        fig.set_tight_layout(True)
        # Set fontsize as 'small' if required
        small_font = kwargs.get('small_font', False)
        if small_font is True:
            for item in ([axis_plot.xaxis.label, axis_plot.yaxis.label] + 
                        axis_plot.get_xticklabels() + axis_plot.get_yticklabels()):
                item.set_fontsize(8)


        # Add canvas to the figure wihtin the frame
        canvas = FigureCanvasTkAgg(fig, master = frame_container)
        frame_canvas = canvas.get_tk_widget()
        frame_canvas.grid(row = 1, column = 0, sticky = 'nsew')

        # Add matplotlib toolbar to the figure within the frame
        frame_itoolbar = ttk.Frame(frame_container)
        frame_itoolbar.grid(row = 0, column = 0, sticky = 'nse')
        t_plot = NavigationToolbar2Tk(canvas, frame_itoolbar)

        # Store canvas and axis plot in object
        self.canvas = canvas
        self.axis_plot = axis_plot

    def plot_histogram(self, bin_data, counts, **kwargs):

        # Get data label
        data_label = kwargs.get('data_label', 'Data')

        # Calculate the appropriate bar width
        bar_width = 0.9*(bin_data[1]-bin_data[0])

        # Clear axis first
        self.axis_plot.cla()

        # Plot the histogram with the barplot
        self.axis_plot.bar(bin_data, counts, 
                            edgecolor = 'slategray', facecolor = 'lightsteelblue', linewidth = 1,
                            label = data_label, width = bar_width)

        # Add the axis labels
        x_label = kwargs.get('x_label', 'x')
        y_label = kwargs.get('y_label', 'counts')
        self.axis_plot.set_xlabel(x_label)
        self.axis_plot.set_ylabel(y_label)

        # Set the axis limits
        self.axis_plot.set_xlim([0, bin_data[-1]+ 2*bar_width])

        # Add the legend
        self.axis_plot.legend()
        
        # Draw canvas
        self.canvas.draw()

    def plot_fit(self, x, y_fit, fit_param_dict):

        # Plot the fitted data as a curve
        self.axis_plot.plot(x, y_fit, c = 'mediumvioletred', lw = 2, label = 'Fit')
        # Redraw legend
        self.axis_plot.legend()

        # Add text with parameters of the fit
        text_string = ''
        for key, value in fit_param_dict.items():
            try:
                text_string = f'{text_string}\n{key}: {value[0]:.1f} +/- {value[1]:.2f}'
            except TypeError:
                text_string = f'{text_string}\n{key}: {value:.1f}'
        
        self.axis_plot.text(0.02, 0.95, text_string, c = 'mediumvioletred', size = 9,
                            ha = 'left', va = 'center', transform = self.axis_plot.transAxes)

        # Configure y_axis to cover slightly more than the maximum and the legend can fit nicely
        self.axis_plot.set_ylim([0, 1.3*np.max(y_fit)])

        # Draw canvas
        self.canvas.draw()

    def plot_line(self, x, y, **kwargs):

        # get label to be able to remove objects
        label = kwargs.get('label', 'line')
        # Get option to dim the old profiles
        dim_old = kwargs.get('dim_old', True)

        # Get x and y labels
        xlabel = kwargs.get('xlabel', 'x')
        ylabel = kwargs.get('ylabel', 'y')

        # Get color of the line and alpha value
        cline = kwargs.get('color', 'steelblue')
        alpha_line = kwargs.get('alpha', 1)

        # Get text to label the curves if required
        textlabel = kwargs.get('textlabel', None)
        
        # Set a higher transparency for older lines
        if dim_old is True:
            for line in self.axis_plot.lines:
                line.set(alpha = 0.2)
            for s in self.axis_plot.texts:
                s.set(alpha = 0.3)
            
        # Plot the data as a 2D curve
        self.axis_plot.plot(x, y, c = cline, lw = 1, label = label, marker = '.', ms = 1, alpha = alpha_line)
        # Add a text label to the curve, if required
        if textlabel is not None:
            self.axis_plot.text(x[-1], y[-1], s = textlabel, size = 6, color = cline)
        # Set the x and y axis labels
        self.axis_plot.set_xlabel(xlabel)
        self.axis_plot.set_ylabel(ylabel)
        
        # Draw canas
        self.canvas.draw()
           
    def plot_secline(self, x, y, **kwargs):

        if not hasattr(self, 'axis_ploty2'):
            # Add the secondary axis, if needed
            self.axis_ploty2 = self.axis_plot.twinx()
        
        # get label to be able to remove objects
        label = kwargs.get('label', 'secline')
        # Get option to dim old results
        dim_old = kwargs.get('dim_old', True)

        # Get y labels
        ylabel = kwargs.get('ylabel', 'y')
        # Get color of the line
        cline = kwargs.get('color', 'slategray')

        # Get text to label the curves if required
        textlabel = kwargs.get('textlabel', None)

        # Set a higher transparency for older lines
        if dim_old is True:
            for line in self.axis_ploty2.lines:
                line.set(alpha = 0.2)
            for s in self.axis_ploty2.texts:
                s.set(alpha = 0.3)
            
        # Plot the data as a 2D curve in the secondary y-axis
        self.axis_ploty2.plot(x, y, c = cline, lw = 1, label = label, alpha = 0.5)
        # Add a text label to the curve, if required
        if textlabel is not None:
            self.axis_ploty2.text(x[0], y[0], s = textlabel, size = 6, color = cline)
        # Set the x and y axis labels
        self.axis_ploty2.set_ylabel(ylabel)
        
        # Draw canas
        self.canvas.draw()

        


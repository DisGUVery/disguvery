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

# Import custom widgets
import ui_custom_widgets as ctk

class ChannelManager():

    def __init__(self, controller = None):
        # As the channel manager is a toplevbel window it doesn't need a master widget
        # we do need the controller to be able to manage the radiobuttons easily
        self.controller = controller

        # Initialise the channel manager window
        chmanager = ctk.ControlPanel(title = 'Channel Manager')
        # Configure layout of the window
        chmanager.configure_layout(cols = [0,1], rows = [0,1])

        # Create the labels for the structure options and the channels
        frame_options = ttk.Frame(chmanager)
        frame_options.grid(row = 0, column = 0, columnspan = 2, sticky = 'nsew', padx = 5, pady = 5)
        structures_ch = ['Membrane signal', 'Membrane-bound', 'Encapsulated content',
                        'Bright Field', 'Other']
        channels = [f'Ch {n}' for n in range(1,5)]

        labels_structures = []
        labels_channels = []
        for s in structures_ch:
            labels_structures.append(ttk.Label(frame_options, text = s))
        for s in channels:
            labels_channels.append(ttk.Label(frame_options, text = s))
        
        # Place labels in window
        for n, s in enumerate(labels_structures):
            s.grid(row = n + 1, column = 0, sticky = 'nsw', padx = 10, pady = 5)
        for n, s in enumerate(labels_channels):
            s.grid(row = 0, column = n + 1, sticky = 'nsew', padx = 10, pady = 2)

        structure_options = ['membrane', 'bound', 'content', 'bf', 'other']   

        # Add radiobuttons
        for n_op in range(len(labels_structures)):
            structure_op = structure_options[n_op]
            for n_ch in range(1, len(labels_channels) + 1):
                ch_var = controller.appdata_channels[n_ch]
                rbutton = ttk.Radiobutton(frame_options, 
                                        variable = ch_var, value = structure_op)
                rbutton.grid(row = n_op + 1, column = n_ch, sticky = 'nsew', padx = 10)
        
        # Button to close
        chmanager.closeButton.grid(row = 1, column = 1, sticky = 'nse', padx = 5, pady = 10)
            
        # keep track of the window
        self.window = chmanager
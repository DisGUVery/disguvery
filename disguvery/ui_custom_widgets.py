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
from tkinter import ttk

from ui_canvas import CanvasFullImage

class ControlPanel(tk.Toplevel):

    def __init__(self, **kwargs):
        # Initialize the toplevel window for the control panel
        # as is a toplevel window, we don't need a master widget
        tk.Toplevel.__init__(self)

        # configure title
        title_window = kwargs.get('title', 'Control Panel')
        self.title(title_window)

        # Set resizable property
        resizable = kwargs.get('resizable', False)
        if resizable == False: self.resizable(0,0)
        # Set window as topmost if desired
        topmost = kwargs.get('topmost', False)
        if topmost == True: self.attributes('-topmost', 'true')

        # Add a close button
        self.closeButton = ttk.Frame(self)
        self.closeButton.columnconfigure(0, weight = 1)
        self.closeButton.rowconfigure(0, weight = 1)
        close_button = ttk.Button(self.closeButton, text = 'Close',
                                    command = self.destroy)
        close_button.grid(row = 0, column = 0, sticky =  'nse')

    def configure_layout(self, cols = None, rows = None, **kwargs):
        # Configure the layout of the window by weighting
        # the columns and the rows 

        # Check if there was a weight specified
        set_weight = kwargs.get('weight', 1)

        # Check if rows and/or columns are set
        if cols:
            self.columnconfigure(cols, weight= set_weight)
        if rows:
            self.rowconfigure(rows, weight = set_weight)

    def create_frames(self, number_frames):

        # Create the number of frames specified and return the objects

        all_frames = []
        for nframe in range(number_frames):
            all_frames.append(ttk.Frame(self))

        return all_frames

class FramedList(ttk.Frame):

    def __init__(self, parent, text = None, width = 20, **kwargs):

        ttk.Frame.__init__(self, parent)
        
        # Define Label Frame and place it
        label_frame = ttk.LabelFrame(self, text = text)
        label_frame.grid(row = 0, column = 0, sticky = 'nsew', padx = 2, pady = 2)
        # Define List and place it
        self.framed_list = tk.Listbox(label_frame, exportselection = 0)
        self.framed_list.grid(row = 0, column = 0, sticky = 'nsew', padx = 10, pady = 5)

        # configure layout of frame
        label_frame.rowconfigure(0, weight = 1)
        label_frame.columnconfigure(0, weight = 1)

        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

class WindowFullCanvas(tk.Toplevel):

    def __init__(self, **kwargs):
        # Initialise the toplevel window for the new canvas to be in
        # as is a toplevel window, we don't need a master widget
        tk.Toplevel.__init__(self)

        # configure title
        title_window = kwargs.get('title', 'Image')
        self.title(title_window)
        self.geometry('400x400+250+250')

        # Set resizable property
        resizable = kwargs.get('resizable', True)
        if resizable == False: self.resizable(0,0)

        # configure top level window
        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

        # Add a frame for the canvas to be placed in
        frame_canvas = ttk.Frame(self)
        frame_canvas.grid(row = 0, column = 0, sticky = 'nsew')

        # Initialise canvas
        self.windisplay = CanvasFullImage(frame_canvas, self)
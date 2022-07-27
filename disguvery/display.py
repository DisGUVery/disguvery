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

from matplotlib import cm
from matplotlib.colors import ListedColormap
from matplotlib.patches import Circle, Rectangle

import numpy as np

class ImageDisplay():

    def show_image(img, img_axis, cmap_options, channel):

        # colormap to show the image, for each channel we have one colormap
        # get the colormap from the corresponding channel        
        if channel != 0: colormap = cmap_options[channel]
        else: colormaps = [x for x in cmap_options[1:]]
        
        if channel > 0:
            img_object = img_axis.imshow(img, cmap = colormap, zorder = 0)
        else:
            for ic in range(img.shape[2]):
                img_channel = img[:,:,ic]
                my_cmap = cm.get_cmap(colormaps[ic])
                my_cmap_new = my_cmap(np.arange(my_cmap.N))
                if ic > 0:
                    my_cmap_new[:, -1] = np.linspace(0, 1, my_cmap.N)
                    my_cmap = ListedColormap(my_cmap_new)
                img_object = img_axis.imshow(img_channel, cmap = my_cmap, alpha = 0.95, zorder = 0)

        return img_object

class ObjectDisplay():

    def text_info(drawn_text, img_axis, **kwargs):

        # Set color of the text drawn
        textcolor = kwargs.get('textcolor', 'mediumvioletred')
        
        # Draw the text strings on their coordinates
        for ic in range(len(drawn_text)):
            x, y = drawn_text[ic][0], drawn_text[ic][1]
            s_value = str(drawn_text[ic][2])
            img_axis.text(x, y, s_value, 
                            ha = 'center', family = 'sans-serif',
                            size = 12, color = textcolor)
    
    def show_object(drawn_object, img_axis, **kwargs):
        """
        Function to draw the required objects into the target container

        INPUT
            drawn_object :      list, [object_type, object_param]
                object_type:    string, name of the object type. It can be
                                'circle', 'box', 'center'
                object_param:   list, [x, y, s], where x,y are the coordinates
                                of the center of the object, and s is the object size.
            target_container :  list, [image_axis, target_canvas]
        """

        # Define objects
        object_type = drawn_object[0]
        object_par = drawn_object[1]

        # Set color of the lines for objects drawn and for text
        edgecolor = kwargs.get('edgecolor','yellow')
        textcolor = kwargs.get('textcolor', 'yellow')
        # Set color for the face fill of the objects
        facecolor = kwargs.get('facecolor', 'none')
        alphacolor = kwargs.get('alpha', 1)
        # Get vesicle ids
        v_ids = np.arange(1, len(object_par)+1)
        vesicle_ids = kwargs.get('ids', v_ids)
        # Get item label
        item_label = kwargs.get('label', 'vesicle')
        text_label = f'{item_label}_text'
        # Get pick option
        pick = kwargs.get('pick', False)
        # Get option to draw text
        draw_text = kwargs.get('draw_text', True)
        # Get option to ignore zeros in center coordinates
        ignore_zeros = kwargs.get('ignore_zeros', True)

        for ic in np.arange(len(object_par)):
            try: 
                x,y,s = object_par[ic][0:3]
            except ValueError:
                x,y = object_par[ic][0:2]
            if (ignore_zeros is False) or ((x != 0) and (y != 0)):
                id_ves = vesicle_ids[ic]
                # Define object to draw depending on type
                if object_type == 'circle':
                    citem = Circle((x,y), s,
                                fc = facecolor,
                                ec = edgecolor,
                                alpha = alphacolor, 
                                label = item_label)
                elif object_type == 'box':
                    citem = Rectangle((x - s/2, y - s/2), s, s,
                                    fc = facecolor,
                                    ec = edgecolor,
                                    alpha = alphacolor, 
                                    label = item_label)
                elif object_type == 'center':
                    citem = Circle((x,y), 1,
                                fc = 'none',
                                ec = edgecolor,
                                label = item_label)
                # Add artist to the image axis
                img_axis.add_patch(citem)
                # Add text with object label
                if draw_text == True:
                    img_axis.text(x, y, id_ves, picker = pick,
                            ha = 'center', family = 'sans-serif',
                            size = 14, color = textcolor, label = text_label)        
        

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

import numpy as np
import cv2
from skimage import measure, morphology

from image_processing import ImageMask

class VesicleDetection():

    def hough(mat_image, det_settings):

        # Convert image to uint8 -> NECESSARY for Hough Circle to work!
        mat_image = VesicleDetection.image_uint8(mat_image)

        # Get parameters
        p1 = int(det_settings['hough_eth'].get())
        p2 = int(det_settings['hough_hth'].get())
        mindist = int(det_settings['hough_mindist'].get())
        rmin = int(det_settings['hough_minrad'].get())
        rmax = int(det_settings['hough_maxrad'].get())

        # Detect circles in image
        circles = cv2.HoughCircles(mat_image, cv2.HOUGH_GRADIENT, 1, 
                                mindist, param1 = p1, param2 = p2, 
                                minRadius = rmin, maxRadius = rmax)

        try:
            det_circles = circles[0,:]
        except TypeError:
            det_circles = None

        # Return detected circles in the right format
        return det_circles
    
    def template(mat_image, template_image, det_settings):

        # convert image and template to uint8 -> NECESSARY for Template Matching to work!
        # (it also works for float32, but we force it here to uint8 for simplicity)
        mat_image = VesicleDetection.image_uint8(mat_image)
        template_image = VesicleDetection.image_uint8(template_image)

        # Get parameters
        min_resize = float(det_settings['template_minre'].get())
        max_resize = float(det_settings['template_maxre'].get())
        number_scales = int(det_settings['template_nscales'].get())
        threshold = float(det_settings['template_thmatch'].get())

        # Define array of scales for multiscale detection
        a_scale = np.linspace(min_resize, max_resize, number_scales)
        a_scale = [round(x,2) for x in a_scale]
        # Initialize variables
        cx = [] # Center in x
        cy = [] # Center in y
        ca = [] # Scale
        match = []  # Match

        # Loop for multiscale detection
        for a in a_scale:
            # Resize template according to scale
            template = cv2.resize(template_image, None, fx = a, fy = a)
            w, h = template.shape[::-1]
            # If template is bigget ahn the image, break the loop
            if (w >= mat_image.shape[0]) or (h >= mat_image.shape[1]):
                break

            # Apply template matching
            match_output = cv2.matchTemplate(mat_image, template, cv2.TM_CCOEFF_NORMED)

            # Only select the locations that are above the threshold
            match_select = np.where(match_output >= threshold)

            # Add the results at the current scale
            cx.extend(match_select[1] + w/2) 
            cy.extend(match_select[0] + h/2) 
            ca.extend(w + 0*match_select[1])
            match.extend(match_output[match_select[0], match_select[1]])

        # Transform lists into numpy arrays
        cx = np.array(cx)
        cy = np.array(cy)
        ca = np.array(ca)
        match = np.array(match)

        # Filter the results by discarding overlaping bounding boxes

        # Create mask matrix for the bounding boxes
        mask_newbox = np.zeros(mat_image.shape, dtype = float)
        # Order results by matching value
        ind_sort = np.argsort(match)
        sort_match = match[ind_sort[::-1]]
        fx = [int(x) for x in cx[ind_sort[::-1]]]
        fy = [int(x) for x in cy[ind_sort[::-1]]]
        bbox = [int(x) for x in ca[ind_sort[::-1]]]

        # Loop over all the bounding boxes detected to discard the overlaping ones
        new_xc = []
        new_yc = []
        new_bbox = []
        new_match = []

        for x,y,s,m in zip(fx, fy, bbox, sort_match):
            # Check if the point has not been matched before
            # # and if it doesn't fall within another larger bounding box
            if mask_newbox[y, x] == 0:
                y1 = int(y - s/2)
                y2 = int(y + s/2)
                x1 = int(x - s/2)
                x2 = int(x + s/2)

                if y1 < 0: y1 = 0
                if x1 < 0: x1 = 0
                if y2 > mask_newbox.shape[0]: y2 = mask_newbox.shape[0]
                if x2 > mask_newbox.shape[1]: x2 = mask_newbox.shape[1] 

                mask_newbox[y1:y2, x1:x2] = m
                new_xc.append(x)
                new_yc.append(y)
                new_bbox.append(s)
                new_match.append(m)

        # Filtered values of center in x,y and bounding box size
        if len(new_xc) < 1:
            match_results = None
        else: 
            match_results = np.stack((np.array(new_xc), np.array(new_yc),
                                    np.array(new_bbox), np.array(new_match)), axis = 1)
       
        # Return bounding boxes for the detected objects and the bounding box matching score
        return match_results
        
    def floodfill(mat_image, det_settings):

        # Get parameters
        threshold = float(det_settings['flood_th'].get())
        min_area = float(det_settings['flood_minarea'].get())
        min_area = min_area**2

        # Threshold the image
        image_th = ImageMask.threshold(mat_image, threshold)

        # Get seedpoint for floodfilling. The seed should be localted in outer aqueous phase, and not 
        # within vesicle. Take 10 seedpoints along the x-direction to find which one gives the most flooded pixels
        h, w = image_th.shape[:2]
        seed_xs = np.linspace(2, w, 10).astype(int)

        # Initialise iteration
        pixels_flooded_current = 0
        seed_point_current = (0,0)

        # For each seed point, track number of pixels that is flooded
        for seed_x in seed_xs:
            seed_point = (seed_x-1,0)
            # Flood the image with the current seedpoint
            flooded_img = VesicleDetection.flood(image_th, seed_point)      
            # Count number of flooded pixels
            pixels_flooded_next = np.sum((flooded_img>0).astype(int))

            # If number of flooded pixels has increased, keep the seedpoint
            if pixels_flooded_next > pixels_flooded_current:
                seed_point_current = seed_point
                pixels_flooded_current = pixels_flooded_next

        # First floodfilling to find the vesicle contour
        flooded_outer = VesicleDetection.flood(image_th, seed_point_current)
        # Interior: 0, membranes: 1, exterior: 255
        # Only keep the ineer area: remove membrane and exterior
        inner_holes = (flooded_outer == 0).astype(int)
        # Second floodfilling to fill the holes
        flooded_outer_rep = inner_holes.copy().astype('uint8')
        flooded_outer_rep = VesicleDetection.flood(flooded_outer_rep, seed_point_current)
        # Non-flooded pixels are vesicle lumen
        inner = (flooded_outer_rep < 255).astype(int)
        inner = inner.astype('uint8')

        # Connect points and label them
        img_label = measure.label(inner, background = 0)
        img_label = morphology.remove_small_objects(img_label, min_size = min_area, connectivity = 1)

        # Relabel the vesicles
        mask_labels = 0*img_label
        new_id = 0
        # Relabel the vesicles
        for ves_label in np.unique(img_label.flatten())[1:]:
            new_id += 1
            mask_labels[img_label == ves_label] = new_id
        
        # Get the centroids for each vesicle
        props = measure.regionprops(mask_labels)
        x_all = []; y_all = []; amajor = []
        for region in sorted(props, key = lambda r: r.label):
            y, x = region.centroid
            amajor.append(region.major_axis_length)
            x_all.append(x)
            y_all.append(y)
        # Transform lists to numpy arrays
        amajor = np.array(amajor)
        x_all = np.array(x_all)
        y_all = np.array(y_all)

        if len(amajor) >= 1:
            floodfill_results = np.stack((x_all, y_all, amajor), axis = 1)
        else:
            floodfill_results = None

        return floodfill_results, mask_labels

    def flood(image_th, seed_point):

        # Copy the image to prevent cv2 of destroying it
        image_fill = image_th.copy()
        # Get shape of image
        h, w = image_fill.shape

        # Create empty mask that is one pixel wider on each side
        mask = np.zeros((h+2, w+2), np.uint8)

        # Create flooded image
        _, flooded_img, _, _ = cv2.floodFill(image_fill, mask, seed_point, 255)

        return flooded_img

    def image_uint8(mat_image):

        # Convert image to uint8 -> NECESSARY for detection methods to work
        # Sometimes it can also work with float32, but we force it to uint8 for simplicity
        ratio = np.amax(mat_image) / 256
        mat_image = (mat_image / ratio).astype('uint8')

        return mat_image

    def save_results(detected_vesicles, detection_method, mask_floodfill = None):

        # Assign id for the vesicles based on number of vesicles
        id_vesicles = np.arange(1, len(detected_vesicles)+1)

        # Initialise dictionary where to store the results
        det_results = {}
        det_results['method'] = detection_method
        det_results['id_vesicle'] = id_vesicles

        # Save results depending on the method used
        if detection_method == 'floodfill':
            det_results['mask_rois'] = mask_floodfill
        
        det_results['rois'] = detected_vesicles
        
        return det_results



   
        

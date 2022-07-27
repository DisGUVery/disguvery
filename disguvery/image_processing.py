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

from matplotlib.patches import Rectangle

class ImageFilters():

    def smooth(mat_image, filter_size):

        # Get image type and check is an accepted type by the gaussian blur function
        img_type = mat_image.dtype
        types_allowed = ['int8', 'int16', 'float32']

        if img_type not in types_allowed:
            if img_type in ['int8', 'int16']: 
                mat_image = np.int16(mat_image)
            # Force 32bit and 64 bit types to be float 32
            else:
                mat_image = np.float32(mat_image)

        # Check if current image has all channels, and smooth all of them
        if mat_image.ndim > 2: n_cycles = mat_image.shape[2]
        else: n_cycles = 1

        # Initialise img_blur with the same shape as mat_image
        img_blur = np.zeros(mat_image.shape)

        # Loop over all the image channels
        for i_channel in range(n_cycles):
            try: 
                ch_image = mat_image[:,:,i_channel]
                # Use sigma blurring to smooth the image
                img_blur[:,:,i_channel] = cv2.GaussianBlur(ch_image, (filter_size, filter_size), 0)
            except IndexError:
                img_blur = cv2.GaussianBlur(mat_image, (filter_size, filter_size), 0)

        return img_blur

    def enhance(mat_image, filter_size):

        # Use large sigma blurring to smooth the image to substract
        img_substract = ImageFilters.smooth(mat_image, filter_size)

        # Create denoised image by substraction
        img_enhanced = mat_image - img_substract
        # Set negative values to zero
        img_enhanced[img_enhanced < 0 ] = 0

        return img_enhanced
        
    def check_filtersize(filter_size):

        # If filter size is not odd, update to first higher odd number
        if (filter_size % 2 == 0) & (filter_size != 0):
            filter_size +=1
            print('Filter size has to be an odd number. Filter size has been changed to next odd number.')

        return filter_size

    def wavelet2d_firstdet(mat_image, a_scale):

        """
        Funtion to compute the 2D Wavelet Transform using the first derivative
        of a gaussian as a mother wavelet

        INPUT:
            a_scale: float, scale or dilation for the gaussian envelop,
                        it works better when it's a multiple of 2
            mat_image: numpy array, image to be transformed
        OUTPUT:
            WT_mod: numpy array, modulus of the WT, same size as the input image
            WT_arg: numpy array, argument of the WT in degrees

        """
        # Construct x and y vectors, with zero at the middle
        x = np.arange(-mat_image.shape[1]/2, mat_image.shape[1]/2)
        y = np.arange(-mat_image.shape[0]/2, mat_image.shape[0]/2)
        # Construct the matrix as a stack of vectors
        xg = np.tile(x, (len(y), 1))
        yg = np.tile(y, (len(x), 1)).transpose()

        # Compute the 2D FFT of the image, shifted
        fft_img = np.fft.fftshift(np.fft.fft2(mat_image))

        # Define the gaussian function in real space. 
        # Note that x*x is better than x**2
        phi = np.exp(-((xg/a_scale)*(xg/a_scale)+(yg/a_scale)*(yg/a_scale))/2)
        # Define the first derivative in x and in y
        phi_x = -(xg/a_scale)*phi
        phi_y = -(yg/a_scale)*phi
        # Normalise according to the scale
        phi_xg = 1/(a_scale**2)*phi_x
        phi_yg = 1/(a_scale**2)*phi_y
        # Compute the 2D FFT, shifted
        fft_phi_x = np.fft.fftshift(np.fft.fft2(phi_xg))
        fft_phi_y = np.fft.fftshift(np.fft.fft2(phi_yg))
        # Compute the gradient in x and in y, and inverse the FFT
        WT_x = np.fft.ifftshift(np.fft.ifft2(fft_phi_x*fft_img))
        WT_y = np.fft.ifftshift(np.fft.ifft2(fft_phi_y*fft_img))
        # Compute the modulus (not normalised) and the argument in degrees
        WT_mod = np.sqrt(np.abs(WT_x)**2 + np.abs(WT_y)**2)
        WT_arg = np.angle(WT_x + 1j*WT_y, deg = True)

        return WT_mod, WT_arg      

class ImageMask():

    def threshold(mat_image, threshold):

        # Take the median of all pixels higher than zero
        median_positive = np.median(mat_image[mat_image>0].flatten())

        # Calculate threshold intensity.
        # threshold is based on the median of all positive pixel values
        intensity_th = np.float(threshold)*median_positive

        # Threshold the image as uint8
        img_th = (mat_image > intensity_th).astype('uint8')

        return img_th

    def floodfill(image_th, min_size, method = 'outside'):

        # Minimum area to discard objects, input is size
        min_area = min_size**2

        # Get seedpoint for floodfilling. The seed should be localted in outer aqueous phase, and not 
        # within vesicle. Take 10 seedpoints along the x-direction to find which one gives the most flooded pixels
        h, w = image_th.shape[:2]

        if method == 'outside':
            seed_xs = np.linspace(2, w, 10).astype(int)
            seed_y = 0
            value_infill = 0
        else:
            seed_xs = np.linspace(h/2-5, h/2 + 5, 10).astype(int)
            seed_y = int(w/2)
            value_infill = 255

        # Initialise iteration
        pixels_flooded_current = 0
        seed_point_current = (0,0)

        # For each seed point, track number of pixels that is flooded
        for seed_x in seed_xs:
            seed_point = (seed_x-1,seed_y)
            # Flood the image with the current seedpoint
            flooded_img = ImageMask.flood(image_th, seed_point)      
            # Count number of flooded pixels
            pixels_flooded_next = np.sum((flooded_img>0).astype(int))

            # If number of flooded pixels has increased, keep the seedpoint
            if pixels_flooded_next > pixels_flooded_current:
                seed_point_current = seed_point
                pixels_flooded_current = pixels_flooded_next
    
        # First floodfilling to find the vesicle contour
        flooded_outer = ImageMask.flood(image_th, seed_point_current)
        # For flooding the exerior: Interior: 0, membranes: 1, exterior: 255
        # For flooding the interior: Interior: 255, membranes: 1, exterior: 0
        # Only keep the inner area: remove membrane and exterior
        inner_holes = (flooded_outer == value_infill).astype(int)
        # Second floodfilling to fill the holes
        flooded_outer_rep = inner_holes.copy().astype('uint8')
        flooded_outer_rep = ImageMask.flood(flooded_outer_rep, seed_point_current)
        # Non-flooded pixels are vesicle lumen
        if method == 'outside':
            inner = (flooded_outer_rep < 255).astype(int)
        else:
            inner = (flooded_outer_rep == 255).astype(int)
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

        return mask_labels
        
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

    def wt_edges(WT_mod, WT_arg):

        """
        Function to implement the edge detection based on a modified
        canny detector with the WT
        Note that no threshold is used with this version
        INPUT:
            WT_mod: numpy array, WT modulus, same size as image
            WT_arg: numpy array, WT argument in degrees
        OUTPUT
            mask_edge: numpy array, binary mask with the detected edged
                        same size as image
        """

        # Discretise the argument to follow the directions
        # where we can look for the gradient
        rWT_arg = 45.*np.round(WT_arg/45.)
        # Define matrices with each direction to look for the 
        # maxima with matrix operations instead of loops
        dir_sa=[0.,45.,90.,135.,-180.,-135.,-90.,-45.]
        # Initialise direction matrix
        WT_mod_0=np.zeros(WT_mod.shape)
        WT_mod_45=np.zeros(WT_mod.shape)
        WT_mod_90=np.zeros(WT_mod.shape)
        WT_mod_135=np.zeros(WT_mod.shape)
        WT_mod_m180=np.zeros(WT_mod.shape)
        WT_mod_m135=np.zeros(WT_mod.shape)
        WT_mod_m90=np.zeros(WT_mod.shape)
        WT_mod_m45=np.zeros(WT_mod.shape)
        # Get the values from the WT modulus
        WT_mod_0[:,:-1]=WT_mod[:,1:]
        WT_mod_m180[:,1:]=WT_mod[:,: -1]
        WT_mod_90[:-1,:]=WT_mod[1:,:]
        WT_mod_m90[1:,:]=WT_mod[:-1,:]
        WT_mod_45[:-1,:-1]=WT_mod[1:,1:]
        WT_mod_m135[1:,1:]=WT_mod[:-1,:-1]
        WT_mod_135[:-1,1:]=WT_mod[1:,:-1]
        WT_mod_m45[1:,:-1]=WT_mod[:-1,1:]
 
        # Construct the matrices to compare with the pixel i+1
        # and with the pixel i-1
        WT_mod_ap=[WT_mod_0,WT_mod_45,
                    WT_mod_90,WT_mod_135,
                    WT_mod_m180,WT_mod_m135,
                    WT_mod_m90,WT_mod_m45]
        WT_mod_am=[WT_mod_m180,WT_mod_m135,
                    WT_mod_m90,WT_mod_m45,
                    WT_mod_0,WT_mod_45,
                    WT_mod_90,WT_mod_135]
 
        # Initialize matrix for the edge mask
        mask_edge=np.zeros(WT_mod.shape)
        # Loop through each direction and compare the corresponding matrices
        # keeping the maxima
        for idir in range(len(dir_sa)):
            mask_angle=rWT_arg==dir_sa[idir]
            mask_edge[mask_angle*np.greater(WT_mod,WT_mod_ap[idir])*np.greater(WT_mod,WT_mod_am[idir])]=1
        
        
        return mask_edge

    def chain_search(mask_WTarg, search_mat):

        # Get search parameters
        search_length, search_width = search_mat

        # Get the points where the mask is not zero
        ye, xe = np.where(mask_WTarg)

        # Create a new matrix to store the labeled points
        mask_label = np.zeros_like(mask_WTarg)

        # Get the search limits
        search_limit = int(np.floor(search_length/2))
        xmax = mask_WTarg.shape[0] - search_limit
        ymax = mask_WTarg.shape[1] - search_limit

        # Create array of points that fall within the search limits
        pointsp = [[x,y] for x,y in zip(xe, ye) if (x > search_limit) and (y > search_limit)]
        pointsp = [[x,y] for x,y in pointsp if (x < xmax) and (y < ymax)]
        # Assign label to points in matrix
        for idc, point in enumerate(pointsp, start = 1):
            mask_label[point[1], point[0]] = idc
        
        # Search algorithm, it runs only two times
        for _ in range(2):
            for point in pointsp:
                xc, yc = point[0], point[1]
                if mask_WTarg[yc, xc] <= 90:
                    search_angle = mask_WTarg[yc, xc] + 90
                else:
                    search_angle = mask_WTarg[yc, xc] - 90

                r1 = Rectangle((xc, yc), search_limit, search_width, angle=search_angle)
                r2 = Rectangle((xc, yc), search_limit, -search_width, angle=search_angle)
                r3 = Rectangle((xc, yc), -search_limit, search_width, angle=search_angle)
                r4 = Rectangle((xc, yc), -search_limit, -search_width, angle=search_angle)
                
                xs1 = xc - search_limit
                xs2 = xc + search_limit
                ys1 = yc - search_limit
                ys2 = yc + search_limit

                pointsp_search = [[x,y] for x,y in pointsp if (xs1 <= x <= xs2) and (ys1 <= y <= ys2)]

                # Check if points are contained within the rectangle
                found_pix = []
                for rect in [r1,r2,r3,r4]:
                    match_points = rect.contains_points(pointsp_search)
                    found_pix.extend(np.array(pointsp_search)[match_points])
                    
                xp = [x for x,y in found_pix]
                yp = [y for x,y in found_pix]
            
                try:
                    id_1 = np.min(mask_label[yp, xp].flatten())
                except ValueError:
                    pass
                else:
                    mask_label[yp, xp] = id_1
               
        for idc, id_label in enumerate(np.unique(mask_label.flatten())):
            mask_label[mask_label == id_label] = idc

        length_chain = []
        id_chain_all = np.unique(mask_label.flatten())
        id_chain_all = id_chain_all[id_chain_all != 0]
        for id_chain in id_chain_all:
            length_chain.append(len(np.where(mask_label==id_chain)[0]))

        ind_sort = np.argsort(length_chain)
        try: yo, xo = np.where(mask_label == id_chain_all[ind_sort][-1])
        except IndexError: yo = [0]; xo = [0]
        try: yi, xi = np.where(mask_label == id_chain_all[ind_sort][-2])
        except IndexError: xi = [0]; yi = [0]

        ri = np.stack((xi, yi), axis = 1)
        ro = np.stack((xo, yo), axis = 1)

        return ri, ro

class ImageCorrection():

    def substract_background(input_image, corr_type, inplace = True):

        # Correct input image according to the method in 'corr_type'
        if 'mean' in corr_type:
            bg_int = np.mean(input_image)
        elif corr_type == 'ROI corner':
            bg_ul = np.mean(input_image[:3,:3])
            bg_ur = np.mean(input_image[:3, -3:])
            bg_ll = np.mean(input_image[-3:, :3])
            bg_lr = np.mean(input_image[-3:, -3:])
            bg_int = np.mean([bg_ul, bg_ur, bg_ll, bg_lr])
        elif corr_type == 'ROI center':
            sy = input_image.shape[0]
            sx = input_image.shape[1]
            bg_int = np.mean(input_image[int(sy/2) - 1: int(sy/2) + 2, int(sx/2) - 1: int(sx/2) + 2])

        if inplace is True:
            input_image -= bg_int.astype(input_image.dtype)
            return input_image
        elif inplace is False:
            return bg_int


class ImageCheck():

    def single_channel(current_image, current_channel):

        # Check the current channel selected, if it's multiple, force it to be the first channel
        if current_channel == 0:
            mat_image = 1*current_image[:,:,0]
            print('A single channel needs to be selected. Setting channel 1 as working channel')
        else:
            try:
                mat_image = 1*current_image[:,:,current_channel - 1]
            except IndexError:
                mat_image = 1*current_image

        return mat_image


        


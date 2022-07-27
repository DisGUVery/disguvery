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
from scipy.optimize import curve_fit

class FitData():

    def histo_gauss(x,y, **kwargs):

        # Get initial parameters
        max_data = np.max(y)
        mean_data = kwargs.get('mean_data', x[np.argmax(y)])
        std_data = kwargs.get('std_data', 0.2*mean_data)
        p0 = [max_data, mean_data, std_data]

        # Find parameters fit
        popt, pcov = curve_fit(FitFunctions.gauss_1d, x, y, p0)
        # Reconstruct fit with parameters
        f = FitFunctions.gauss_1d(x, popt[0], popt[1], popt[2])
        # Reconstruct curve with 10x more points
        x10 = np.linspace(x[0], x[-1], 10*len(x))
        f10 = FitFunctions.gauss_1d(x10, popt[0], popt[1], popt[2])

        return [popt, pcov], [f, f10]

class FitFunctions():

    def gauss_1d(x, a, x0, sigma):

        return a*np.exp(-(x - x0)**2/(2*sigma**2))

class GeoMat():

    def coordinates(x_size, y_size):

        X, Y = np.ogrid[:x_size, :y_size]
        coord_matrix = [X, Y]


        return coord_matrix

    def theta_degrees(coord_matrix, center):

        # Shift coordinates to take into account the right center
        coord_matrix[0] -= int(center[0])
        coord_matrix[1] -= int(center[1])
        # Calculate theta
        theta = np.arctan2(coord_matrix[0], coord_matrix[-1])
        # Make only positive
        theta += np.pi
        # Convert to degrees
        theta = theta / (np.pi) * 180

        return theta
    
    def dist_radial(coord_matrix, center):

        X = coord_matrix[0]
        Y = coord_matrix[1]
        xc = center[0]
        yc = center[1]

        dist_matrix = np.sqrt((X - xc)**2 + (Y - yc)**2)
       
        return dist_matrix

    def mask_contours(roi_coords, mat_shape, half_r = False):

        # Build coordinate matrix
        coord_matrix = GeoMat.coordinates(mat_shape[1], mat_shape[0])
        
        mask_labels = np.zeros((mat_shape[1], mat_shape[0]), dtype = int)
        # For each roi, mask the contour as a circle
        for i, roi in enumerate(roi_coords):
            rad_mat = GeoMat.dist_radial(coord_matrix, [roi[0], roi[1]])
            if half_r is True:
                r = roi[2] / 2
            else:
                r = roi[2]
            mask_labels[rad_mat <= r] = i+1

        return mask_labels.transpose()

class ProfileIntegration():

    def radial(signal_matrix, center, dr = 1, norm = False):

        coord_matrix = GeoMat.coordinates(signal_matrix.shape[0], signal_matrix.shape[1])
        rad_mat = GeoMat.dist_radial(coord_matrix, center)

        # Define radial vector for integration
        max_radius = np.max([signal_matrix.shape[0]/2, signal_matrix.shape[1]/2])
        d_radius = np.arange(0, max_radius, dr)
        mean_radius = np.mean([d_radius[1:], d_radius[:-1]], 0)

        # Initialize metric array: [mean_radius, mean_signal, min_signal, max_signal, sum_signal]
        all_signals = np.zeros((len(mean_radius), 5))
        all_signals[:,0] = mean_radius
        
        # Keep track of errors in integration
        found_error = False

        # Loop over the radius and integrate the signal
        for i_radius in range(1, len(d_radius)):
            slice_radius = 0*signal_matrix
            slice_radius[(rad_mat >= d_radius[i_radius -1]) & (rad_mat < d_radius[i_radius])] = 1
            # Get signal over slice
            signal_slice = signal_matrix * slice_radius
            roi_slice = signal_slice[signal_slice > 0]

            try:
                roi_slice[0]
            except IndexError:
                found_error = True
                roi_slice = np.zeros(2)
            finally:
                all_signals[i_radius - 1, 1] = np.mean(roi_slice)
                all_signals[i_radius - 1, 2] = np.min(roi_slice)
                all_signals[i_radius - 1, 3] = np.max(roi_slice)
                all_signals[i_radius - 1, 4] = np.sum(roi_slice)

        # Normalise the mean intensity if required
        if norm is True:
            all_signals[:, 1] = all_signals[:,1]/np.mean(all_signals[:,1])
        
        return all_signals, found_error

    def angular(signal_matrix, center, dt = 1, rlim = None, norm = None):

        # Build angular matrix
        coord_matrix = GeoMat.coordinates(signal_matrix.shape[0], signal_matrix.shape[1])
        theta_mat = GeoMat.theta_degrees(coord_matrix, center)
        # compute the radial matrix for the selected vesicle
        rad_mat = GeoMat.dist_radial(coord_matrix, [0,0])
        mask_radius = 0*rad_mat

        # Define theta vector for integration
        d_theta = np.arange(0, 360 + dt, dt)
        mean_theta = np.mean([d_theta[1:], d_theta[:-1]], 0)
        # Initialize metrics array: [mean_theta, mean_signal, min_signal, max_signal, sum_signal]
        all_signals = np.zeros((len(mean_theta), 5))
        all_signals[:,0] = mean_theta

        var_rlim = False
        mean_radius = None
        # Set the type of integration with respect to the radius
        if rlim is None:
            # No limits in the radius -> integration should be limited to bounding box size w,h not diagonal size
            max_radius = np.max([signal_matrix.shape[0]/2, signal_matrix.shape[1]/2])
            mask_radius[rad_mat <= max_radius] = 1
        else:
            # If BMA was used for detection, the radius is constant, and we need to slice only once
            if len(rlim) == 2:
                mask_radius[rad_mat >= rlim[0]] = 1
                mask_radius[rad_mat >= rlim[1]] = 0
            else:
                var_rlim = True
                mean_radius = np.zeros((len(mean_theta), 2))
        
        # Keep track of errors in integration
        found_error = False
        # Iterate over theta and integrate the signal
        for i_theta in range(1, len(d_theta)):
            slice_theta = 0*signal_matrix
            roi_slice = []
            try:
                slice_theta[(theta_mat >= d_theta[i_theta - 1]) & (theta_mat < d_theta[i_theta])] = 1
            except ValueError:
                found_error = True
            else:
                # If RMD was used, we also need to set the mask radius
                # Mask with the radial slice
                if var_rlim is True:
                    slice_theta_rlim = slice_theta*rad_mat*rlim
                    try: mean_radius[i_theta-1, 0] = np.mean(np.abs(slice_theta_rlim[slice_theta_rlim < 0]))
                    except ValueError: pass
                    try: mean_radius[i_theta -1, 1] = np.mean(slice_theta_rlim[slice_theta_rlim > 0])
                    except ValueError: pass
                    mask_radius[rad_mat < mean_radius[i_theta-1][1]] = 1
                    mask_radius[rad_mat < mean_radius[i_theta-1][0]] = 0
                signal_slice = signal_matrix * mask_radius * slice_theta
                roi_slice = signal_slice[signal_slice > 0]
            
            try:
                roi_slice[0]
            except IndexError:
                found_error = True
                roi_slice = np.zeros(2)
            finally:
                all_signals[i_theta - 1, 1] = np.mean(roi_slice)
                all_signals[i_theta - 1, 2] = np.min(roi_slice)
                all_signals[i_theta - 1, 3] = np.max(roi_slice)
                all_signals[i_theta - 1, 4] = np.sum(roi_slice)
        # Normalise the mean intensity if required
        if norm is True:
            all_signals[:, 1] = all_signals[:,1]/np.mean(all_signals[:,1])
        
        return all_signals, mean_radius, found_error




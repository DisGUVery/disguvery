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

from PIL import Image, ImageSequence
import numpy as np

class FileImage():

    def open(filename, verbose = True):

        # We don't care if the image has already been opened or not
        # We read the image and overwrite the info associated to it

        # check if the image is supported and read it
        source_image = FileImage.read_supported(filename)
        image_info = None
        image_name = None

        if source_image is not None:
            if verbose is True:
                # Print a message for successfull loading
                print(f'Image sucessfully loaded as {source_image.dtype.name}')

            # get image and file information
            image_info, image_name= FileImage.get_info(filename, source_image, verbose)

        return image_info, image_name, source_image

    def read_supported(filename):

        # Supported image formats
        supported_format = ['L', 'P', 'RGB', 'I', 'F', 'I;16B', 'I;16L', 'I;16N', 'I;16']
        source_image = None
        # Read the image object
        try:
            img = Image.open(filename)
        except:
            print('Image type cannot be identified. Please choose another type.')
        else:
            # Get the image type and if nor supported, raise an error message.
            if img.mode not in supported_format:
                print(f'ERROR: Image type {img.mode} not supported.')
            else:
                # Load all the frames in an image
                # ATTENTION: for now this is handled only as multiple channels
                # THIS NEEDS TO BE CHANGED WHEN DEALING WHEN SEQUENCES

                # Frames will be loaded into an empty list first
                all_frames = []
                # Load all frames in the image
                ic = 0
                for frame in ImageSequence.Iterator(img):
                    ic += 1
                    all_frames.append(np.array(frame))
                # Close the image file
                img.close()
                # Convert list to numpy array
                all_frames = np.array(all_frames)

                # Assign value as source_image, if image has been loaded
                # with the multiple frames of the iterator, transpose.
                if ic == 1:
                    source_image = np.array(all_frames)[0]
                else:
                    # Get axis from frame, and build tuple for transpose
                    axis_frame = [x for x in range(1, len(all_frames.shape))]
                    axis_frame.insert(2,0)
                    source_image = 1*np.transpose(all_frames, tuple(axis_frame))
                
                    # If image is [NxMxCxS], take only [NxMxC]
                    source_image = source_image[:,:,:]

        return source_image

    def get_info(filename, source_image, verbose = True):

        # Initialise dictionary
        image_info = {}
        
        # Get file information from the filename
        file_only = filename.split('/')[-1]
        image_name = file_only.split('.')[0]

        image_info['directory'] = '/'.join(filename.split('/')[:-1])
        image_info['extension'] = file_only.split('.')[1]

        # get the image information
        image_info['size_x'] = source_image.shape[0]
        image_info['size y'] = source_image.shape[1]
        
        # if there's more than one channel, get the info
        try:
            nchannels = source_image.shape[2]
        except IndexError:
            nchannels = 1
        finally:
            image_info['channels'] = nchannels
            if verbose is True:
                print(f'There are {nchannels} channels identified')

        return image_info, image_name

class FileTemplate():

    def read(filename):
        
        # Supported image formats
        supported_format = ['L', 'P', 'RGB', 'I', 'F', 'I;16B','I;16L','I;16N','I;16']
        # Read the image object
        img = Image.open(filename)

        # Get the image type, and if not supported, raise an error message
        if img.mode not in supported_format:
            print(f'ERROR: Image type {img.mode} not supported')
        else:
            # Flag the single-channel read
            print('Template is loaded as a single-channel image.', end= ' ')
            try:
                template_image = np.array(img)[:,:,0]      
            except IndexError:
                template_image = np.array(img)[:,:]
            finally:
                # print a message for successfull loading
                print(f'Template successfuly loaded as {template_image.dtype.name}')

            return template_image

    def save(filename, template_image):

        # Add the extension depending on whether the filename already includes it
        if len(filename.split('.')) == 1:
            filesave = '.'.join([filename, 'tiff'])
        else:
            filesave = filename

        # Get the image from the array containing the template
        save_image = Image.fromarray(template_image)
        # Save the image as the filesave, with TIFF format
        save_image.save(filesave, format = 'TIFF')
        print(f'Template image saved in {filesave}')
        
class FileExport():

    def vesicle_detection(filename, detection_results):

        # Get detection method and detected vesicles
        det_method = detection_results['method']
        det_vesicles = detection_results['rois']
        id_vesicles = detection_results['id_vesicle']
        
        # Header for hough detection and template matching
        header_file = {'hough': 'id_vesicle, xc (pix), yc (pix), radius (pix)',
                'template': 'id_vesicle, xc (pix), yc (pix), size (pix), matching score',
                'floodfill': 'id_vesicle, xc (pix), yc (pix), axis major length (pix)'}
        # 
        if det_method in ['hough', 'floodfill'] : n_columns = 4
        elif det_method == 'template': n_columns = 5
        write_results = np.zeros((det_vesicles.shape[0], n_columns))
        write_results[:,1:] = det_vesicles

        write_results[:,0] = id_vesicles
        np.savetxt(filename, write_results, header = header_file[det_method], delimiter = ',', 
                    fmt = '%i,' + '%.1f,'*(n_columns-1))

        # For floodfill results we also need to export the individual regions
        # We export here only a mask with the labels of each region -> 0 is for background
        try: 
            mask_rois = detection_results['mask_rois'].astype('uint8')
        except KeyError:
            pass
        else:
            # Save the mask as a uint8 tiff image. This is for keeping a small size
            # this format gives a file about half the size as a txt file
            filemask = filename.replace('.csv', '_mask.tiff')
            image_tosave = Image.fromarray(mask_rois)
            image_tosave.save(filemask)
            print(f'Regions mask saved in {filemask}')

    def intensity_profiles(filename, profiles_results):

        # The results are saved differently whether they are angular or radial profiles

        # For radial profiles, per vesicle, per channel, we have a matrix: [mean r, mean int, min, max, sum]
        header_main_rad = '# Ves ID, Channel, Mean radius (pix), Mean Intensity (a.u.), Min. Intensity, Max. Intensity, Sum Intensity \n'
        # For angular profiles, per vesicle, per channel, we have two matrices. The first one is like the radial profiles
        # except for mean radius, is mean theta
        header_main_theta = header_main_rad.replace('radius (pix)', 'theta (deg)')
        header_sec_theta = 'Ves ID, Theta (deg), ri (pix), ro (pix)'

        # Write the results for the main matrix, in two different files
        filename_rad = filename.replace('.csv', '_radial_profiles.csv')
        filename_angular = filename.replace('.csv', '_angular_profiles.csv')
        filename_angularsec = filename_angular.replace('profiles', 'radius')

        # Check which vesicles have radial profiles in them, and which have angular profiles
        ves_rad = [x for x,y in profiles_results.items() if y['radial'] is not None]
        ves_angular = [x for x,y in profiles_results.items() if y['angular'] is not None]

        # Write radial profiles, if found
        if len(ves_rad) >= 1:
            # Initialise array
            array_tosave = np.zeros(7)
            for ives in ves_rad:
                nves = int(ives.split(' ')[-1])
                results_ves = profiles_results[ives]['radial']
                for ich, results_ch in results_ves.items():
                    nch = int(ich.split(' ')[-1])
                    ves_array = np.full((results_ch.shape[0],1), nves)
                    ch_array = np.full_like(ves_array, nch)
                    mid_array = np.hstack([ves_array, ch_array, results_ch])
                    array_tosave = np.vstack([array_tosave, mid_array])
        
            np.savetxt(filename_rad, array_tosave[1:], header = header_main_rad, delimiter = ',', 
                    fmt = '%i, %i, ' + '%.2f, '*5)
            print(f'Radial intensity profiles saved in {filename_rad}')
        
        # Write angular profiles, if found
        if len(ves_angular) >= 1:
            # Initialise array
            array_tosave = np.zeros(7)
            arraysec_tosave = np.zeros(4)
            for ives in ves_angular:
                nves = int(ives.split(' ')[-1])
                results_ves = profiles_results[ives]['angular']
                for ich, results_ch in results_ves.items():
                    if results_ch is not None:
                        ves_array = np.full((results_ch.shape[0],1), nves)
                        if 'ch' in ich:
                            nch = int(ich.split(' ')[-1])
                            ch_array = np.full_like(ves_array, nch)
                            theta_vec = np.zeros_like(ch_array)
                            mid_array = np.hstack([ves_array, ch_array, results_ch])
                            array_tosave = np.vstack([array_tosave, mid_array])
                            theta_vec[:,0] = results_ch[:,0]
                        else:
                            mid_array = np.hstack([ves_array, theta_vec, results_ch])
                            arraysec_tosave = np.vstack([arraysec_tosave, mid_array])
        
            np.savetxt(filename_angular, array_tosave[1:], header = header_main_theta, delimiter = ',', 
                    fmt = '%i, %i, ' + '%.2f, '*5)
            print(f'Angular intensity profiles saved in {filename_angular}')
            
            if len(arraysec_tosave) > 4: 
                np.savetxt(filename_angularsec, arraysec_tosave[1:], header = header_sec_theta, delimiter = ',',
                        fmt = '%i, ' +  '%.2f, '*3)
                print(f'Angular contours saved in {filename_angularsec}')
            
    def encapsulation_results(filename, encap_results, mask_matrix):

        # Header for the encapsulation results
        header_file = 'ROI, xc (pix), yc (pix), <I> roi (a.u.), A roi (pix^2)'
        
        np.savetxt(filename + '.csv', encap_results, header = header_file, delimiter = ',', 
                            fmt = '%i, '*3 + '%.2f, '*2)
        
        # Export also the masked image as a uint8 tiff image. This is for keeping a small size
        image_tosave = Image.fromarray(mask_matrix)
        image_tosave.save(filename + '.tiff')
        
        print(f'Encapsulation results saved in {filename}')
        


            


            





        

        



   
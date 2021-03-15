from rasterio.windows import Window
import os
import gdal
import numpy as np
import geojson as gj
import rasterio 

def generate_array(wanted_files, bands, polar_dict, pol, other_pol, polygon_file):
    xmin, xmax, ymin, ymax, mask, transform = get_window(polygon_file, wanted_files[0])
    smaller = False
    if xmin < 0: # polygon overlapping left-hand edge of area of interest
        smaller = True
        xneg = xmin
        xmin = 0
        ysize, xsize = int(ymax-ymin), int(xmax-xneg)
    else:
        ysize, xsize = int(ymax-ymin), int(xmax-xmin)
    burn_array = np.zeros((len(wanted_files), len(bands), int(ymax-ymin), int(xmax-xmin)))        
    count = 0
    for n, file in enumerate(wanted_files):
        win = Window.from_slices((ymin, ymax), (xmin, xmax))
        with rasterio.open(file) as src:
            arr = src.read(window = win)
        if arr.shape[2] == 0:
            continue
        if smaller:
            #print(burn_array.shape, arr.shape)
            burn_array[n, polar_dict[pol], :, :] = arr
        else:
            #print(burn_array.shape, arr.shape, xmin, xmax, ymin, ymax, ysize, xsize)
            burn_array[n, polar_dict[pol], :arr.shape[1], :arr.shape[2]] = arr

        matching_file = file.replace(pol, other_pol)
        if os.path.exists(matching_file):
            band = polar_dict[other_pol]
            with rasterio.open(matching_file) as src:
                arr = src.read(window = win)
            if smaller:
                burn_array[n, polar_dict[pol], :, -xneg:] = arr
            else:
                burn_array[n, polar_dict[other_pol], :arr.shape[1], :arr.shape[2]] = arr
            count += 1
        else:
            continue
            
    if count == 0:
        #print("No valid data found intersecting {}".format(os.path.splitext(os.path.basename(polygon_file))[0]))
        return None, None, None
    else:
        return burn_array, mask, transform

def generate_array_backscatter(wanted_files, bands, polygon_file):
    xmin, xmax, ymin, ymax, mask, transform = get_window(polygon_file, wanted_files[0])
    burn_array = np.zeros((len(wanted_files), bands, int(ymax-ymin), int(xmax-xmin)))
    for n, file in enumerate(wanted_files):
        win = Window.from_slices((ymin, ymax), (xmin, xmax))
        with rasterio.open(file) as src:
            arr = src.read(window = win)
        if arr.shape[2] > 0:
            burn_array[n, :, :, :] = arr
        else:
            burn_array[n, :, :, :] = 0
        
    return burn_array, mask, transform

from PIL import Image, ImageDraw
def get_window(polygon_file, example_file, just_coords= False, verbose=False):
    # Get coords for bounding box
    with open (polygon_file, 'r') as f:
        loadg = gj.loads(f.read())
    x, y = zip(*gj.utils.coords(loadg))
    min_x, max_x, min_y, max_y = min(x), max(x), min(y), max(y)
    if verbose:
        print("Input for GeoJSON ULeft {}:{} LRight {}:{} ".format(min_x, max_y, max_x, min_y))

    # Get coordinate information from GeoTIFF file
    if verbose:
        print("Loading {} into HDF file".format(ofiles[0]))
    ds = gdal.Open(example_file, gdal.GA_ReadOnly)
    bands = ds.RasterCount
    image = ds.GetRasterBand(1).ReadAsArray()
    xdim, ydim = image.shape
    del image

    global pixelWidth
    global pixelHeight
    
    # Getting georeference info
    transform = ds.GetGeoTransform()
    projection = ds.GetProjection()
    xOrigin = transform[0] # top left x 
    yOrigin = transform[3] # top left y 
    pixelWidth = transform[1] # w-e pixel resolution 
    pixelHeight = -transform[5] # n-s pixel resolution (negative value) 

    #print(xOrigin, yOrigin, pixelHeight, pixelWidth)

    # Close HDF file
    ds = None

    # Computing [top left] [lower right]
    i1 = int((min_x - xOrigin) / pixelWidth) - 100
    i2 = int((max_x - xOrigin) / pixelWidth) + 101 #we need to add 1 as int rounds down
    j1 = int((yOrigin - max_y) / pixelHeight) - 100
    j2 = int((yOrigin - min_y) / pixelHeight) + 101 # we need to add 1 as int rounds down

    if verbose:
        print("Pixel coordinates for subset ULeft {}:{} LRight {}:{}".format(i1, j1, i2, j2))
    if just_coords:
        return i1, i2, j1, j2, pixelWidth, pixelHeight
    vect = []
    # first lets get the coordinates of the shape outline
    for x1, y1 in zip(x, y):
        xpix = ((x1 - xOrigin) / pixelWidth) - i1
        ypix = ((yOrigin - y1) / pixelHeight) - j1
        #vect.append([int(ypix), int(xpix)])
        vect.append(int(xpix))
        vect.append(int(ypix))
    img = Image.new('L',  (i2-i1,j2-j1), 0)                                                                                                                                                                                                                  
    draw = ImageDraw.Draw(img)                                                                                                                                                                                                                                        
    draw.polygon(vect, fill=1)
    mask = np.array(img)
    
    # New upper-left X,Y values
    start_x = xOrigin + (i1 * pixelWidth)
    start_y = yOrigin - (j1 * pixelHeight)
    end_x = xOrigin + (i2 * pixelWidth)
    end_y = yOrigin - (j2 * pixelHeight)
    new_transform = (start_x, transform[1], transform[2], start_y, transform[4], transform[5])
    if verbose:
        print("Origin: Old-UL {:.3f} {:.3f} New-UL {:.3f} {:.3f} New-LR {:.3f} {:.3f}".
              format(xOrigin, yOrigin, start_x, start_y, end_x, end_y))
    
    return i1, i2, j1, j2, mask, new_transform

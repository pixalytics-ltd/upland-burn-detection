---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.1
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

# Combined (Backscattering and Coherence) Analysis Notebook

When initially deploying the notebook, you will be asked to choose the dataset (either Coherence or Backscatter) and then the case study area (Skye, Cairngorms or Peak District)

Once these have been chosen, the third drop down menu will automatically be populated with a list of available polygons (there may be a brief delay). These are listed by a unique reference number, followed by the date on which the burn occured. 

The last dropdown menu, is the dataset version you want to investigate.

**Note:** Upon initially processing the coherence dataset, the tiles were paired based on the slice number from Sentinel-1. However, upon analysing the results at the end of the project, it became apparent that this didn't always provide full coverage of the area due to slight staggering in the area they covered. Therefore, additional combinations would need to be processed to fill these gaps in some images / orbits. Therfore, some orbits were reprocessed for the Peak District National Park and Cairngorms but due to the way the slices lay, we already had a full dataset for the Isle of Skye so no v2 dataset was created. For Backscatter there is only a single dataset. 

**Note:** For the test dataset limited data has been provided. Skye v1 relative orbit 125, Cairngorms v2 relative orbit 30 and Peak District v2 relative orbit 154. The same orbits have been provided for the backscatter data.


```python
#Reload modules without shutting notebook
%load_ext autoreload
%autoreload 2

import os
import glob
import numpy as np
import rasterio
from rasterio.windows import Window
import datetime
import pandas as pd
import geojson as gj
import matplotlib.pyplot as plt 
from ipywidgets import Dropdown, interact, interactive, fixed, interact_manual
import ipywidgets as widgets
import yaml

# Import upburn utils
from utils.array_creation import generate_array, generate_array_backscatter, get_window
from utils.get_configuration import get_config
from utils.functions import order_files_by_date, get_data_dict, get_aoi_date_dict, get_polygon_list
from utils.load_corine import subset_corine
from utils.plot_jsons import plot_jsons
from utils.extract_s1ard import extract_s1ard
from utils.calc_era_api import calc_era_api

current_burn = None
home = os.path.expanduser("~")
utils_dir = os.path.join(os.getcwd(), "utils")
with open(os.path.join(utils_dir, "configuration.yml")) as yaml_file:
    config = yaml.safe_load(yaml_file)
    print("Loaded configuration: {:}.".format(config))
    sharedfolder = os.path.expanduser(config.get("sharedfolder"))
shared_folder = os.path.join(home, sharedfolder)
datasets = os.path.join(shared_folder, "datasets")
print("Datasets in %s"%(datasets))
```

```python
# Create a widget that allows us to choose our analysis type
workbook_widget = Dropdown(options = ["", "Coherence", "Backscatter"], description = "Dataset:", value = "")
def change_wbook(*args): 
    global workbook 
    workbook = workbook_widget.value
    if workbook == "":
        return

workbook_widget.observe(change_wbook, 'value')
print("Choose the type of data to look at")
display(workbook_widget)

# Create a widget that can be used the choose the case study area
cstudy_widget = Dropdown(options = ["", "skye", "cairngorms", "pdistrict"], description = "Case study:", value = "")
def change_cstudy(*args):
    global cstudy 
    global aoi
    global poly_list
    global poly_dict
    global polygons
    cstudy = cstudy_widget.value
    length = 3 # Number of characters in the id number
    # Set the aoi depending on the chosen cstudy
    if cstudy == "":
        poly_list = []
        return
    elif cstudy == "skye":
        aoi = os.path.join(datasets, "Skye_extent_OSGB36.geojson")
    elif cstudy == "cairngorms":
        aoi = os.path.join(datasets, "Cairngorms_extent_OSGB36-extended.geojson")    
    else:
        aoi = os.path.join(datasets, "PDistrict_extent_OSGB36.geojson")
        length = 5
    # get a list of polygons and a dictionary linking the polygons to the burn date
    poly_list = get_polygon_list(datasets, aoi)
    date_dict = get_aoi_date_dict(cstudy, shared_folder)
    
    ###  Below needs updating when we get dates for burns ###    
    fstart = os.path.basename(aoi).split("_")[0] 
    searchstr = fstart + "_burn_extent_*.geojson"
    polygons = glob.glob(os.path.join(datasets, searchstr)) # get the polygons relevant to the chosen cstudy 
    if len(polygons) == 0:
        print("No polygons exist for {}".format(searchstr))
    poly_list = []
    for poly in polygons:
        fpoly = os.path.splitext(os.path.basename(poly))[0]
        poly_list.append(fpoly.split("_")[3])

    # Convert string list to int list, sort then convert back
    poly_int = [i for i in poly_list]
    poly_int.sort()
    poly_list = [str(i).zfill(3) for i in poly_int]
    poly_list2 = [pol + " (%s)"%(date_dict[int(pol[:length])]) for pol in poly_list]

    poly_dict = {pol_string : pol for pol, pol_string in zip(poly_list, poly_list2)}
    b_widget.options = poly_dict.keys() # set the polygon widget options 
    del poly_int
    
cstudy_widget.observe(change_cstudy, 'value')
print("Choose a Case study area")
display(cstudy_widget)

poly_dict = {}

# Create a widget that can be used the choose the polygon of interest
b_widget = Dropdown(options = poly_dict.keys(), description = "Polygon:")
def change_x(*args):
    print("Set to {}".format(b_widget.value))
    
b_widget.observe(change_x, 'value')
print("Choose burn area")
display(b_widget)

# Create a widget that can be used the choose the polygon of interest
version_widget = Dropdown(options = ["v2", "v1"], description = "Version:")
def change_version(*args):
    print("Set to {}".format(version_widget.value))
    
version_widget.observe(change_version, 'value')
print("Choose dataset version")
display(version_widget)
```

## Display polygons
Once you have made the selections above, you are able to visualise the locations of each burn by generating an interactive map.

```python
# Show all the case study polygons on a map
if len(polygons) < 1:
        raise SystemExit("Could not find any polygons for {}".format(searchstr))
else:
    print("Displaying {} polygons".format(len(polygons)))

# Plot on map
wdown = widgets.Dropdown(
    options=['map', 'image'],
    value='map',
    description='Background:'
)

def display_map(background):
    m = plot_jsons(background, polygons, cstudy)
    display(m)

# display the dropdown and map
interactive_map = interactive(display_map, background=['map','image'])
output = interactive_map.children[-1]
output.layout.height = '350px'
interactive_map
```

## Pull in additional data based on the chosen polygon
The following cells set the configuration based on the selections above, and pull in data from ERA5.

```python
# Set polygon from drop-down above
endstr = ".geojson"
fstart = os.path.basename(aoi).split("_")[0]
burn = fstart + "_burn_extent_" + poly_dict[b_widget.value]
non_burn = fstart + "_baseline_extent_" + poly_dict[b_widget.value].split("-")[0]
if os.path.exists(os.path.join(datasets, burn + endstr)):
    print("Chosen polygon: {}".format(burn))
    if os.path.exists(os.path.join(datasets, non_burn + endstr)):
        print("Non-burn polygon available")
        bdata = True
    else:
        print("No non-burn data available")
        bdata = False
else:
    print("ERROR: chosen polygon {} not found".format(burn))
chosen_burn = b_widget.value
```

```python
# Load ERA5Land data
graphics = False # do not display graphs
verbose = False # do not show extra print statements
polygon = burn
%run ./Pull-ERA5.ipynb $polygon $verbose $graphics $cstudy
if bdata:  # run for non burn polygon:
    polygon = non_burn
    %run ./Pull-ERA5.ipynb $polygon $verbose $graphics $cstudy
```

```python
if version_widget.value == "v2":
    v2=True
    ofiles, outfolder, baselines = get_config(cstudy, workbook, v2=v2)
    if len(ofiles) == 0:
        print("No v2 data, switching to v1")
        v2=False
else:
    v2=False
    ofiles, outfolder, baselines = get_config(cstudy, workbook, v2=v2)
    if len(ofiles) == 0:
        print("No v1 data, switching to v2")
        v2=True
ofiles, outfolder, baselines = get_config(cstudy, workbook, v2=v2)
if len(ofiles) == 0:
     raise SystemExit("No valid data found")
else:
    print("Found %s potential files and %s baselines for %s"%(len(ofiles), len(baselines), version_widget.value))
```

## Extract the data of interest
Once the above selection has been completed, running the cell below will produce an interactive dataframe, where you can choose the files you want to investigate based on a combination of date range, orbit number and or orbit direction. 
When you are happy with your selection you can the following two cells will load the files you have chosen into a 3D array and display them. These can then be investigated visually by scrolling between them / switching between polarisation.

You should see either 2 or 4 images (depending if a non burn area was available in the close vicinity for comparison). The first 2 images will show the burn area side by side, with the right hand image showing an extended area around it and the edge of the burn area drawn in red. The left image will show just the extracted burn area, with the surrounding area "blanked out".
If a non burn area is available, the next 2 images will show the same for that area, respectively. 

The raw images / arrays (without the border drawn on or the area outside "blanked") can be output in a variety of ways. 
* "Save" will save a projected version of the image you are current viewing. 
* "Save all burn geotiffs" will save a projected version of every image chosen into a zip folder. 
* "Save burn array" will save the whole array as a python pickle object that can be loaded and analysed elsewhere

```python
# get a list of only VV files and only VH files
only_VV = [file for file in ofiles if "VV" in file]
only_VH = [file for file in ofiles if "VH" in file]
bands = set([file.strip("_%s.tif"%(cstudy))[-2:] for file in ofiles])
polar_dict = {'VV' : 0, 'VH' : 1}
pol, other_pol = "VV", "VH"
if workbook == "Coherence": # determine if we have more VV or VH as we will use this for the dataframe
    if len(only_VV) > len(only_VH):
        most_files = only_VV
    else:
        most_files = only_VH
        pol, other_pol = "VH", "VV" 
else:
    most_files = ofiles
print("Found %s input files for %s"%(len(most_files), version_widget.value))

# Setup data frame
most_files = order_files_by_date(most_files, workbook)
data_dict = get_data_dict(most_files, workbook, baselines)
pd.set_option('display.max_rows', 500)
df = pd.DataFrame.from_dict(data_dict)
wanted_files = df['filename']
unwanted_files = []
xmin, xmax, ymin, ymax, pixelWidth, pixelHeight = get_window(os.path.join(datasets, burn + ".geojson"), wanted_files[0], just_coords= True)
if xmin < 0: # polygon overlapping edge of area of interest
    xmin = 0
    print("Warning: Polygon overlaps the edge of the processed area")
else:
    print("Polygon being extracted %d %d %d %d"%(xmin, xmax, ymin, ymax))

# loop through the files and remove any that don't have data as well as loading in a matching file for the other polarisation
for n, file in enumerate(wanted_files): 
    win = Window.from_slices((ymin, ymax), (xmin, xmax))
    with rasterio.open(file) as src:
        arr = src.read(window = win)
    if workbook == "Backscatter":
        if np.mean(arr) == 0:
            unwanted_files.append(n)
            continue
    matching_file = file.replace(pol, other_pol)
    if os.path.exists(matching_file):
        with rasterio.open(matching_file) as src:
            arr2 = src.read(window = win)
    else:
        arr2 = np.zeros(arr.shape)
    both_arrays = np.concatenate([arr, arr2])
    if np.mean(both_arrays) == 0:
        unwanted_files.append(n)
        continue
        
# Drop unwanted files from the dataframe
unwanted_files = sorted(unwanted_files, reverse=True)
print("Removed %s of %s files that don't have data for this polygon"%(len(unwanted_files), len(wanted_files)))

df = df.drop(unwanted_files).reset_index(drop=True) # remove any images which have no data for either polarisation
if df.empty:
    raise SystemExit('DataFrame is empty after filtering')
```

```python
chosen_orbit = 'All'
chosen_direction = 'both'        
# create an interactive dataframe for filtering
def get_files_by_date(start_date, end_date, rel_orbit, orbit_dir):
    global chosen_orbit
    global chosen_direction
    global time_filtered_df
    # filter it by date
    time_filtered_df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
    if rel_orbit != "":
        # filter by relative orbit
        time_filtered_df = time_filtered_df[time_filtered_df["rorbit"] == rel_orbit]
        chosen_orbit = "All" 
    if orbit_dir != "":
        # filter by orbit direction
        time_filtered_df = time_filtered_df[time_filtered_df["direction"] == orbit_dir]
        chosen_direction = "Both"
    if len(set(time_filtered_df.direction.values)) == 1:
        # if we only have one orbit direction we can set this now
        orbit_dir = time_filtered_df.direction.values[0]
    time_filtered_df_vis = time_filtered_df.copy(deep=True)
    # set the chosen values
    chosen_orbit = rel_orbit
    chosen_direction = orbit_dir
    # return the filtered df without filename and polarisation for visualisation
    return time_filtered_df_vis.drop(['filename', 'polarisation'], axis = 1)

orbit_opts = list(set(df['rorbit'].values))
orbit_opts.append("")
orbit_dir_opts = list(set(df['direction'].values))
orbit_dir_opts.append("")
interact(get_files_by_date,
        start_date=widgets.DatePicker(value=pd.to_datetime(min(df['date']))),
        end_date=widgets.DatePicker(value=pd.to_datetime(max(df['date']))),
        rel_orbit=widgets.Dropdown(options=orbit_opts, value = ""),
        orbit_dir=widgets.Dropdown(options=orbit_dir_opts, value = ""))
```

```python
# Turn some of the column info into lists we can use during plotting
wanted_files = time_filtered_df.filename.to_list()
list_of_dates = time_filtered_df.date.to_list()
list_of_directions = time_filtered_df.direction.to_list()
# lets load the correct data
if workbook == "Coherence":
    list_of_baselines = time_filtered_df.perpbaseline.to_list()
    burn_subarray, burn_mask, burn_transform = generate_array(wanted_files, bands, polar_dict, pol, other_pol, os.path.join(datasets, burn + ".geojson"))
    if bdata:
        non_burn_subarray, non_burn_mask, non_burn_transform = generate_array(wanted_files, bands, polar_dict, pol, other_pol, os.path.join(datasets, polygon + ".geojson"))
elif workbook == "Backscatter":
    burn_subarray, burn_mask, burn_transform = generate_array_backscatter(wanted_files, 2, os.path.join(datasets, burn + ".geojson"))
    if bdata:
        non_burn_subarray, non_burn_mask, non_burn_transform = generate_array_backscatter(wanted_files, 2, os.path.join(datasets, polygon + ".geojson"))

if burn_subarray is None:
    raise SystemExit("No valid {} data found intersecting {}".format(workbook, os.path.splitext(os.path.basename(polygon_file))[0]))
```

```python
import matplotlib.pyplot as plt 
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
import matplotlib.ticker as ticker 

def save_image():
    # create the filename for saving
    dst_filename = os.path.join(outfolder, "%s_%s_%s_%s_%s_%s.tif"%(polygon.split("_")[0], polygon.split("_")[3], date, pol_text, direct, "burn_%s"%(workbook)))
    if not os.path.exists(outfolder):
        os.mkdir(outfolder)
    if os.path.exists(dst_filename):
        return
    driver = gdal.GetDriverByName( 'GTiff' )
    dst_ds=driver.Create(dst_filename, curr_arr.shape[1],curr_arr.shape[0], 1, gdal.GDT_Float32) # is shape the wrong way around?
    dst_ds.SetGeoTransform(burn_transform)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(27700)
    dest_wkt = srs.ExportToWkt()
    dst_ds.SetProjection (dest_wkt) # is this right?

    dst_ds.GetRasterBand(1).WriteArray( curr_arr )
    print("Saved to: {}".format(dst_filename))


@interact(img_num=(1,len(burn_subarray),1), polarisation=['VV','VH'])
def plot_polygons(polarisation='VV', img_num=0):
    # get max and min vals to normalise plots with
    max_val= np.max(burn_subarray)
    min_val = np.min(burn_subarray)
    if workbook == "Coherence":
        max_val = 1
        min_val = 0
    global date
    global pol_text
    global curr_arr
    global direct
    pol_text = polarisation
    pol = polar_dict[polarisation]
    date = list_of_dates[img_num-1]
    if workbook == "Coherence":
        baseline = list_of_baselines[img_num-1]
    if not isinstance(date, str):
        date = date.strftime("%Y%m%d")
    direct = list_of_directions[img_num-1]
    # set the current array so the user can save it if needed 
    curr_arr = np.copy(burn_subarray[(img_num-1), pol, :, :])
    curr_arr[burn_mask==0] = np.nan # set anything outside the polygon to np.nan
    fig = plt.figure(figsize=((20,10)))
    ax = fig.add_subplot(121)
    ax.imshow(curr_arr, vmax=max_val, vmin=min_val) # show the chosen array 
    if workbook == "Coherence":
        plt.title("Burn %s: %s direction %s perpbaseline %s"%(workbook, date, direct, baseline))
    else:
        plt.title("Burn %s: %s direction %s"%(workbook, date, direct))
    # Do not plot ticks
    plt.xticks([]) 
    plt.yticks([]) 
              
    curr_arr2= np.copy(burn_subarray[(img_num-1), pol, :, ])
    ax2 = fig.add_subplot(122)
    im = ax2.imshow(curr_arr2, vmax=max_val, vmin=min_val) # show the current array 
    # this time we will keep the data outside the polygon and just draw a contour around it
    ax2.contour(burn_mask > 0, levels=[2], colors=['r'])
    ax2.xaxis.set_major_locator(ticker.NullLocator())
    ax2.yaxis.set_major_locator(ticker.NullLocator())
    
    fig.subplots_adjust(right=0.85)# add space for colour bar
    cbar_ax = fig.add_axes([0.88, 0.25, 0.04, 0.5])
    fig.colorbar(im, cax=cbar_ax)
    
    plt.show()
    
savebutton = interactive(save_image, {'manual' : True, 'manual_name' : 'Save'})
display(savebutton)

def save_all_images():
    """
    Saves all the chosen images individually and zips them for downloading
    """
    fold_name = list_of_dates[0].strftime("%Y%m%d") + "_" + list_of_dates[-1].strftime("%Y%m%d") + "_" + burn +"_"+ "orb%s"%(chosen_orbit)+ "_" +"dir%s"%(chosen_direction)+ "_" + workbook
    fold_name = os.path.join(outfolder, fold_name)
    if not os.path.exists(fold_name):
        os.mkdir(fold_name)
    for n, subarr in enumerate(burn_subarray, start=0):
        # loop through and save each image to the folder
        for pol in polar_dict.keys():
            wanted_arr = subarr[polar_dict[pol], :, :]
            arrdate = list_of_dates[n]
            if not isinstance(arrdate, str):
                arrdate = arrdate.strftime("%Y%m%d")
            direct = list_of_directions[n]
            dst_filename = os.path.join(fold_name, "%s_%s_%s_%s_%s_%s.tif"%(polygon.split("_")[0], polygon.split("_")[3], arrdate, pol, list_of_directions[n], "burn_%s"%(workbook)))
            if os.path.exists(dst_filename):
                continue
            driver = gdal.GetDriverByName( 'GTiff' )
            dst_ds=driver.Create(dst_filename, wanted_arr.shape[1], wanted_arr.shape[0], 1, gdal.GDT_Float32) # is shape the wrong way around?
            dst_ds.SetGeoTransform(burn_transform)
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(27700)
            dest_wkt = srs.ExportToWkt()
            dst_ds.SetProjection (dest_wkt) # is this right?
            dst_ds.GetRasterBand(1).WriteArray( wanted_arr )
    import shutil
    shutil.make_archive(fold_name, 'zip', fold_name)
    shutil.rmtree(fold_name) # remove the non zipped folder
    
    print("Saved to: {}".format(fold_name + ".zip"))

saveallbutton = interactive(save_all_images, {'manual' : True, 'manual_name' : 'Save all burn geotiffs'})
display(saveallbutton)

def save_whole_array():
    import pickle 
    print(burn)
    if not isinstance(list_of_dates[0], str):
        start = list_of_dates[0].strftime("%Y%m%d")
        end = list_of_dates[-1].strftime("%Y%m%d")
        print(start, end)
    else: 
        start = list_of_dates[0]
        end = list_of_dates[-1]
    fname = burn +"_"+ "orb%s"%(chosen_orbit)+ "_" +"dir%s"%(chosen_direction)+ "_" + start + "_" + end +  ".p"
    pickle.dump(burn_subarray, open(os.path.join(outfolder, fname), "wb"))
    print("Saved to: {}".format(os.path.join(outfolder, fname)))
    
save_whole_burn = interactive(save_whole_array, {'manual' : True, 'manual_name' : 'Save burn array'})
display(save_whole_burn)

if bdata:
    def save_image2():
        dst_filename = os.path.join(outfolder, "%s_%s_%s_%s_%s_%s.tif"%(polygon.split("_")[0], polygon.split("_")[3], date2, pol_text2, direct, "burn_%s"%(workbook)))
        if not os.path.exists(outfolder):
            os.mkdir(outfolder)
        if os.path.exists(dst_filename):
            return
        driver = gdal.GetDriverByName( 'GTiff' )
        dst_ds=driver.Create(dst_filename, curr_arr3.shape[1],curr_arr3.shape[0], 1, gdal.GDT_Float32) # is shape the wrong way around?
        dst_ds.SetGeoTransform(non_burn_transform)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(27700)
        dest_wkt = srs.ExportToWkt()
        dst_ds.SetProjection (dest_wkt) # is this right?

        dst_ds.GetRasterBand(1).WriteArray( curr_arr3 )
        print("Saved to: {}".format(dst_filename))


    @interact(img_num_non_burn=(1,len(non_burn_subarray),1), polarisation_non_burn=['VV','VH'])
    def plot_polygons2(polarisation_non_burn='VV', img_num_non_burn=0):
        max_val= np.max(burn_subarray)
        min_val = np.min(burn_subarray)
        if workbook == "Coherence":
            max_val = 1
            min_val = 0
        global date2
        global pol_text2
        global curr_arr3
        global direct2
        pol_text2 = polarisation_non_burn
        pol = polar_dict[polarisation_non_burn]
        date2 = list_of_dates[img_num_non_burn-1]
        if workbook == "Coherence":
            baseline2 = list_of_baselines[img_num_non_burn-1]
        if not isinstance(date2, str):
            date2 = date2.strftime("%Y%m%d")
        direct2 = list_of_directions[img_num_non_burn-1]
        curr_arr3 = np.copy(non_burn_subarray[(img_num_non_burn-1), pol, :, :])
        curr_arr3[non_burn_mask==0] = np.nan # set anything outside the polygon to np.nan
        fig2 = plt.figure(figsize=((20,10)))
        ax3 = fig2.add_subplot(121)
        ax3.imshow(curr_arr3, vmax=max_val, vmin=min_val)   
        if workbook == "Coherence":
            plt.title("Non-Burn %s: %s direction %s perpbaseline %s"%(workbook, date, direct, baseline2))
        else:
            plt.title("Non-Burn %s: %s direction %s"%(workbook, date, direct))
        # Do not plot axes ticks
        plt.xticks([]) 
        plt.yticks([]) 

        curr_arr4= np.copy(non_burn_subarray[(img_num_non_burn-1), pol, :, ])
        ax4 = fig2.add_subplot(122)
        im2 =ax4.imshow(curr_arr4, vmax=max_val, vmin=min_val)
        ax4.contour(non_burn_mask > 0, levels=[2], colors=['r'])
        ax4.xaxis.set_major_locator(ticker.NullLocator())
        ax4.yaxis.set_major_locator(ticker.NullLocator())
        # add space for colour bar
        fig2.subplots_adjust(right=0.85)# add space for colour bar
        cbar_ax = fig2.add_axes([0.88, 0.25, 0.04, 0.5])
        fig2.colorbar(im2, cax=cbar_ax)
        plt.show()

    savebutton2 = interactive(save_image2, {'manual' : True, 'manual_name' : 'Save'})
    display(savebutton2)

    def save_all_images2():
        fold_name = list_of_dates[0].strftime("%Y%m%d") + "_" + list_of_dates[-1].strftime("%Y%m%d") + "_" + non_burn +"_"+ "orb%s"%(chosen_orbit)+ "_" +"dir%s"%(chosen_direction) + "_" + workbook
        fold_name = os.path.join(outfolder, fold_name)
        if not os.path.exists(fold_name):
            os.mkdir(fold_name)
        for n, subarr in enumerate(non_burn_subarray, start=0):
            for pol in polar_dict.keys():
                wanted_arr = subarr[polar_dict[pol], :, :]
                arrdate = list_of_dates[n]
                if not isinstance(arrdate, str):
                    arrdate = arrdate.strftime("%Y%m%d")
                direct = list_of_directions[n]
                dst_filename = os.path.join(fold_name, "%s_%s_%s_%s_%s_%s.tif"%(polygon.split("_")[0], polygon.split("_")[3], arrdate, pol, list_of_directions[n], "burn_%s"%(workbook)))
                if os.path.exists(dst_filename):
                    continue
                driver = gdal.GetDriverByName( 'GTiff' )
                dst_ds=driver.Create(dst_filename, wanted_arr.shape[1], wanted_arr.shape[0], 1, gdal.GDT_Float32) # is shape the wrong way around?
                dst_ds.SetGeoTransform(non_burn_transform)
                srs = osr.SpatialReference()
                srs.ImportFromEPSG(27700)
                dest_wkt = srs.ExportToWkt()
                dst_ds.SetProjection (dest_wkt) # is this right?
                dst_ds.GetRasterBand(1).WriteArray( wanted_arr )
        import shutil
        shutil.make_archive(fold_name, 'zip', fold_name)
        shutil.rmtree(fold_name)
        print("Saved to: {}".format(fold_name + ".zip"))

    saveallbutton2 = interactive(save_all_images2, {'manual' : True, 'manual_name' : 'Save all non-burn geotiffs'})
    display(saveallbutton2)

    def save_whole_array2():
        import pickle 
        if not isinstance(list_of_dates[0], str):
            start = list_of_dates[0].strftime("%Y%m%d")
            end = list_of_dates[-1].strftime("%Y%m%d")
            print(start, end)
        else: 
            start = list_of_dates[0]
            end = list_of_dates[-1]
        fname = non_burn+"_"+ "orb%s"%(chosen_orbit)+ "_" +"dir%s"%(chosen_direction)+ "_" + start + "_" + end +  ".p"
        pickle.dump(non_burn_subarray, open(os.path.join(outfolder, fname), "wb"))
        print("Saved to: {}".format(os.path.join(outfolder, fname)))

    save_whole_burn2 = interactive(save_whole_array2, {'manual' : True, 'manual_name' : 'Save non burn array'})
    display(save_whole_burn2)
```

## Import CORINE land cover
Running the next cell will allow you to chose a specific land cover classification you wish to further analyse. 

```python
current_burn = chosen_burn 
burn_df = time_filtered_df
string_dates = [pd.to_datetime(d).strftime("%Y%m%d") for d in list_of_dates]
burn_df['date'] = string_dates

# Filter the S1ARD data
filtered_burndf, filtered_burnarray, filtered_dates_burn = time_filtered_df, burn_subarray, time_filtered_df.date.to_list()
if bdata:
    filtered_basedf, filtered_basearray, filtered_dates_base = time_filtered_df, non_burn_subarray, time_filtered_df.date.to_list()
#print(filtered_burndf, filtered_burnarray.shape, filtered_dates_burn)

# Load CORINE land cover for polygon burn area subset
feature_list = ['All']
cpolygons, legend_df = subset_corine(xymin[0], xymin[1], xymax[0], xymax[1], pixelWidth, pixelHeight, datasets, verb = verbose)
if cpolygons == None:
    print("CORINE data is not available, see utils/load_corine for details of what is expected")
    feature_list = ['Whole-Polygon']
    # Extract burn area using original polygon
    mean_s1burn, std_s1burn, pnames, features = extract_s1ard(cpolygons, filtered_burnarray, verb = verbose)
    if bdata:
        mean_s1base, std_s1base, pnames, features = extract_s1ard(cpolygons, filtered_basearray, verb = verbose)
else:
    # Extract subsets of burn area using CORINE polygons
    mean_s1burn, std_s1burn, pnames, features = extract_s1ard(cpolygons, filtered_burnarray, verb = verbose)
    if bdata:
        mean_s1base, std_s1base, pnames, features = extract_s1ard(cpolygons, filtered_basearray, verb = verbose)

    for feature in features:
        feature_list.append(feature)

c_widget = Dropdown(options = feature_list, description = "Landcover types:", value = feature_list[0])
def change_x(*args):
    print("Set to {}".format(c_widget.value))

c_widget.observe(change_x, 'value')
print("Choose {} land cover type: ".format(cstudy))
display(c_widget)
```

## Calculate precipitation index and generate plots

Finally, the last 3 cells will determine precipitation, create plots and then finallyt display plots that can be analysed. 

```python
subpolygons = {}
if c_widget.value == "Whole-Polygon":
    print("Using the whole polygon as CORINE data not available")
elif c_widget.value != "All":
    for feat, p in cpolygons.items():
        if feat == c_widget.value:  # Matching names
            subpolygons[feat] = p
                    
    # Run subset again for just the chosen feature
    mean_s1burn, std_s1burn, pnames, features = extract_s1ard(subpolygons, filtered_burnarray, verb = verbose)
    if bdata:
        mean_s1base, std_s1base, pnames, features = extract_s1ard(subpolygons, filtered_basearray, verb = verbose)

# Extract ERA5 data for matching dates and calculate Antecedent Precipitation Index
filtered_dates = burn_df['date'].values
mean_edata, std_edata = calc_era_api(dt_num, mean_parameters, filtered_burnarray, filtered_dates, verb = True)
filtered_edata = filtered_dates
eraname = 'Antecedent Precipitation Index'

# Print initial arrays
print("{} S1 dates: {} ...".format(len(list_of_dates),list_of_dates[0:5]))
print("S1 {} array {}".format(workbook, mean_s1burn.shape))
for fnum in range(len(features)):
    print("   Burn {} max VV {:.3f} max VH {:.3f} VHrVV {:.3f} RFDI {:.3f} NVHI {:.3f} NVVI {:.3f}"
        .format(features[fnum],np.nanmax(mean_s1burn[fnum,0,:]),np.nanmax(mean_s1burn[fnum,1,:]),np.nanmax(mean_s1burn[fnum,2,:]),
        np.nanmax(mean_s1burn[fnum,3,:]),np.nanmax(mean_s1burn[fnum,4,:]),np.nanmax(mean_s1burn[fnum,5,:])))
    if bdata:
        print("  Non-burn {} max VV {:.3f} max VH {:.3f} VHrVV {:.3f} RFDI {:.3f} NVHI {:.3f} NVVI {:.3f}"
            .format(features[fnum],np.nanmax(mean_s1base[fnum,0,:]),np.nanmax(mean_s1base[fnum,1,:]),np.nanmax(mean_s1base[fnum,2,:]),
            np.nanmax(mean_s1base[fnum,3,:]),np.nanmax(mean_s1base[fnum,4,:]),np.nanmax(mean_s1base[fnum,5,:])))
print("ERA5 Precip: {} values from {} to {} max {:.3f}".format(len(mean_edata), filtered_edata[0], filtered_edata[-1], np.nanmax(mean_edata)))

```

```python
burn_start = current_burn.split(" (")[1][:-1]
burn_start = datetime.datetime.strptime(burn_start, '%d/%m/%Y')
# Create plots for ERA5 data in comparison to Sentinel-1 ARD dates for each CORINE polygon
import utils.plot_data as plotd
plt.set_loglevel("critical")

if not os.path.exists(outfolder):
    os.mkdir(outfolder)

print("Filtering: between {} and {} for rorbit {} and direction {}".format(filtered_dates[0], filtered_dates[-1], chosen_orbit, chosen_direction)) 
if bdata:
    outbase = os.path.join(outfolder,"plot-" + workbook + "-era-non-burn.png")
    plotd.plot_lines(filtered_dates, mean_s1base, std_s1base, filtered_edata, mean_edata, std_edata, features, pnames, eraname, outbase, burn_start, graphics = False)
    print("Generated: {}".format(outbase))

outburn = os.path.join(outfolder,"plot-" + workbook + "-era-burn.png")
plotd.plot_lines(filtered_dates, mean_s1burn, std_s1burn, filtered_edata, mean_edata, std_edata, features, pnames, eraname, outburn, burn_start, graphics = False)
print("Generated: {}".format(outburn))

```

```python
# Display plots side by side if have both non-burn and burn data extracted

# read plot images
if bdata:
    img1 = open(outbase, 'rb').read()
    img2 = open(outburn, 'rb').read()

    # Text widgets
    t1 = widgets.Text(value='Non-burn %s polygon'%(workbook))
    t2 = widgets.Text(value='Plotting for rorbit {} and direction {}'.format(chosen_orbit, chosen_direction))
    t3 = widgets.Text(value='Burn %s polygon'%(workbook))
    ## Create image widgets.
    i1 = widgets.Image(value=img1, width='50%')
    i2 = widgets.Image(value=img2, width='50%')
    ## Side by side thanks to HBox widget
    titles = widgets.HBox([t1, t2, t3], width='100%')
    plots = widgets.HBox([i1, i2], width='100%')

else:
    img1 = open(outburn, 'rb').read()
    
    # Text widgets
    t1 = widgets.Text(value='Burn %s polygon'%(workbook), width='20%')
    t2 = widgets.Text(value='Plotting for rorbit {} and direction {}'.format(chosen_orbit, chosen_direction), width='80%')
    ## Create image widgets.
    i1 = widgets.Image(value=img1, width='100%')
    ## Side by side thanks to HBox widget
    titles = widgets.HBox([t1, t2], width='100%')
    plots = widgets.HBox([i1], width='100%')

# User interface
ui = widgets.VBox([titles,plots])
## Finally, show.
display(ui)



```

```python

```

```python

```

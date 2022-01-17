# Upland Burn Project Jupyter Notebooks

[![DOI](https://zenodo.org/badge/331396785.svg)](https://zenodo.org/badge/latestdoi/331396785)

This repository is part of the final set of deliverables produced by Pixalytics and EnviroSAR under their contract in response to the Department for Environment & Rural Affairs (DEFRA) Invitation To Tender (ITT) 76044 “Upland Burn Detection with Radar”. 

For this project, three case study areas were of interest: Isle of Skye, Cairngorms and the Peak District National Park. From the following DropBox link, a subset of the data generated can be downloaded for testing the Jupyter Notebooks: https://www.dropbox.com/s/phje3itiat6yt33/my_shared_data_folder.tar.gz?dl=0 

The folder structure that was setup in the original Jupyter Lab was:
* notebooks (contents of the GitHub respository)
* my_shared_data_folder (datasets on a mounted drive, with the location defined in the yml file in the utils folder)
    + datasets (small files that included the CORINE land cover data and GeoJSONs)
        - baselines (calculated coherence baselines)
        - era-downloaded (downloaded and stored ERA5 data, files generated each time the Combined_UBurn_WorkBook Jupyter notebook is run)
        - shape_files (shapefiles corresponding to the GeoJSONs in the main datasets folder)
    + cairngorms
        - backscatter_tiffs
        - coherence_tiffs
        - coherence_tiffs2
    + pdistrict
        - backscatter_tiffs
        - coherence_tiffs
        - coherence_tiffs2
    + skye
        - backscatter_tiffs
        - coherence_tiffs (no data as same as v2)
        - coherence_tiffs2

<bold>Note:</bold> The coherence processing required several iterations to generate the best dataset for automated extraction. In comparison to version 1 that produced coherence based on matching slice numbers, version 2 ensures the area of interest is fully covered when moving from north to south (or vice versa) by analysing multiple combinations that account for any shift in slice position between consecutive orbits. However, a small limitation remains because Sentinel-1 files will only cover part of the area of interest in the east / west direction as the 
orbit path itself may "clip" the area of interest. Therefore a future step may be to combine multiple orbits, or filter these orbits out entirely. Currently, the latter can be achieved during the Jupyter Notebook analysis, or initial processing when the user can select the relative orbit to process.

## Downloading Backscattering Datasets

In the pre-process folder there is a notebook (Download-Sentine1ARD-JNCC) to download Sentinel-1 backscattering data for an area / timeframe you wish. The data is downloaded from the JNCC ARD archived held on CEDA, and then subsetted and merged for the area of interest.

## Processing Coherence Datasets

In the pre-process folder there is a notebook (Generate-Sentine1SLC) to process Sentinel-1 coherence data for an area / timeframe you wish.

<bold>Note:</bold> Once you have your final images, it is worth cleaning up the initial download folder and intermediate folder as the memory usage quickly adds up!

## Running the Analysis of the Backscattering and Coherence Data

Coherence or Backscatter datasets can be investigated using the Combined_UBurn_WorkBook Jupyter notebook. 
* When initially deploying the notebook, you will be asked to choose the dataset (either Coherence or Backscatter) and then the case study areas 
* Once these have been chosen, the third drop down menu will automatically be populated with a list of available polygons. These are listed by a unique reference number, followed by the date on which the burn occured. 
* The last dropdown menu, is the dataset version you want to investigate. 
* Once you have made the selections above, you are able to visualise the locations of each burn by generating an interactive map of all burns.
* Then you can read in the ERA5 and CORINE data and visualise the Sentinel-1 data through time-series plots, plus you have the options of downloading the data as GeoTIFFs for use in a GIS package

## Running the Initial Automated Detection

<bold>Note:</bold> For running analysis - due to the large size of the area, running the analysis on too many files at once can cause the notebook to crash. Therefore, the number of files has been restricted to 20 but what your system can handle depends on the memory available. 

* Similarly to the main notebook, the first couple of cells in the Initial_Automated_Detection notebook will set the initial configuration and allow you to choose the case study / dataset of interest. After these have been selected, the following cells will load and show an interactive dataframe which, again, allows you to filter out the data you want to investigate. 

* After this, the images are loaded into an array and the analysis run (notebook currently setup to preform denormalisation followed by a gaussian filter with a sigma of 5). The analysis steps can be adjusted and or different steps can be added at a different point. More information on how to do this is given in the notebook. 

* The resulting image is thresholded to provide us with a potential prediction, and this is compared to known burn areas with an accuracy and precision score calculated. 

* The prediction, ground truth array and / or the pre thresholded total change can be saved either as a simple png, or projected to the correct coordinate system (OSGB36) and saved as a GeoTIFF.




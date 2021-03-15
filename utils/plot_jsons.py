import subprocess
import glob
import os
home = os.path.expanduser("~")
import shutil
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from IPython.display import display, Image
from ipyleaflet import basemaps, GeoJSON, ImageOverlay, Map, Marker, Polygon, Popup 
from ipywidgets import FloatProgress, HTML
from shapely.wkt import loads as load_wkt
import pandas as pd
import geopandas as gpd
import json
import random
from osgeo import ogr
import numpy as np

# Define paths to exe files
gdalbin = "/usr/anaconda3/envs/rsgidlib_dev/bin/"

# Import python utilities
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import gdal

def plot_jsons(background, jfiles, cstudy):
    
    ## setup temp folder
    tmpfolder = os.path.join(home, "temp")
    if not os.path.exists(tmpfolder):
        os.mkdir(tmpfolder)

    # Setup progress bar
    f = FloatProgress(min=0, max=100, description='Running:')
    display(f)
        
    # Setup map display
    zoomin = 9
    if cstudy == "skye":
        lat, lon = 57.3, -6.3
    elif cstudy == "cairngorms":
        lat, lon = 57.5, -3.5 
    else: # Peak district
        lat, lon = 53.14, -2.06
        
    if background == 'map':
        m = Map(center=(lat,lon), zoom=zoomin, basemap=basemaps.OpenStreetMap.BlackAndWhite)
    else:
        m = Map(center=(lat,lon), zoom=zoomin, basemap=basemaps.Esri.WorldImagery)
    m.layout.height="550px"
    f.value += 5

    percent = 95.0/len(jfiles)
    if percent < 1.0:
        percent = 1
    else:
        percent = np.ceil(percent)

    # Load json files
    def json_color(feature):
        return {
            'color': 'black',
            'fillColor': random.choice(['red', 'yellow', 'green', 'orange']),
        }

    outjson = os.path.join(tmpfolder,"temp.json")
    if os.path.exists(outjson):
        os.remove(outjson)
    for jsonfile in jfiles:
        
        # Extract polygon number
        basestem = os.path.splitext(os.path.basename(jsonfile))[0]
        polyname = basestem.split("_")[3]
        
        # Reproject to WGS84
        cmd = 'ogr2ogr -s_srs EPSG:27700 -f "GeoJSON" {} {} -t_srs EPSG:4326'.format(outjson,jsonfile)
        os.system(cmd)
        
        # Load current vector layer - chosen in cell above
        with open(outjson, 'r') as file:
            data = json.load(file)
            geo_json = GeoJSON(data=data,
                style={'opacity': 1, 'dashArray': '9', 'fillOpacity': 0.1, 'weight': 1},
                hover_style={'color': 'white', 'dashArray': '0', 'fillOpacity': 0.5},
                style_callback=json_color)
        #print("Displaying: {}".format(jsonfile))
        m.add_layer(geo_json)
        
        # Popup with a polygon cetroid on the map:
        df = gpd.read_file(outjson)
        # Find the center point
        df['Center_point'] = df['geometry'].centroid
        # Extract centerpoint
        df["long"] = df.Center_point.map(lambda p: p.x)
        df["lat"] = df.Center_point.map(lambda p: p.y)
        latv = df["lat"].values[0]
        lonv = df["long"].values[0]
        label = "Burn polygon: {} {:.3f} {:.3f} ".format(polyname,latv,lonv)
        #print(label)
        message = HTML(value=label)
        marker = Marker(location=(latv, lonv))
        marker.popup = message
        m.add_layer(marker)
        
        f.value += percent
        if os.path.exists(outjson):
            os.remove(outjson)


    # save to html
    # m.save(os.path.join(tmpfolder, "map.html"))

    return m


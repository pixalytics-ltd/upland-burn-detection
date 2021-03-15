# Load CORINE data
import os
import csv
import fiona
from shapely.geometry import MultiPolygon,Polygon, shape
from osgeo import osr
from pandas import DataFrame
import numpy as np

def subset_corine(xmin, ymin, xmax, ymax, pixelWidth, pixelHeight, datasets, verb = False):
    # Datasets
    corine = os.path.join(datasets,"u2018_clc2018_v2020_20u1_geoPackage/DATA/U2018_CLC2018_V2020_20u1.gpkg")
    legend = os.path.join(datasets,"u2018_clc2018_v2020_20u1_geoPackage/Legend/CLC_legend.csv")
    if not os.path.exists(corine) or not os.path.exists(legend):
        return None, None

    # Transform ERA5 bounding box to ETRS-LAEA map projection
    if verb:
        print("Bounding box: {:.3f} {:.3f} {:.3f} {:.3f}".format(xmin, ymin, xmax, ymax))
    OSR_WGS84 = osr.SpatialReference()
    OSR_WGS84.ImportFromEPSG(4326)
    OSR_LAEA = osr.SpatialReference()
    OSR_LAEA.ImportFromEPSG(3035)
    to_laea = osr.CoordinateTransformation(OSR_WGS84, OSR_LAEA)
    xymin = to_laea.TransformPoint(xmin, ymin)
    xymax = to_laea.TransformPoint(xmax, ymax)
    if verb:
        print("Bounding box: {:.3f} {:.3f} {:.3f} {:.3f}".format(xymin[0], xymin[1], xymax[0], xymax[1]))

    # Load Legend
    legend_dict = []
    with open(legend) as csvDataFile:
        csvReader = csv.reader(csvDataFile)
        for row in csvReader:
            splits = row[0].split(";")
            if len(splits) == 4:
                if splits[0] == 'GRID_CODE':
                    if verb:
                        print("Reading header: ",splits)
                else:
                    legend_dict.append({'GRID_CODE': splits[0], 'CLC_CODE': splits[1], 'LABEL3': splits[2], 'RGB': splits[3]})

    # Convert to dataframe
    legend_df = DataFrame(legend_dict, columns=['GRID_CODE', 'CLC_CODE', 'LABEL3', 'RGB'])

    if verb:
        print("Read {} LCC codes...".format(len(legend_df)))
        print(legend_df.loc[0])
    legend_df.set_index('CLC_CODE', inplace=True)

    
    # Extract Corine subset based on bounding box
    polygons = {}
    with fiona.open(corine) as src:
        print(src)
        count = 0
        for feature in src.filter(bbox=(xymin[0], xymin[1], xymax[0], xymax[1])): # minx, miny, maxx, maxy
            vect = []
            all_coords = feature['geometry']['coordinates'][0][0]
            for coords in all_coords:
                xcoo = coords[0]
                ycoo = coords[1]
                xpix = (xcoo - xymin[0]) / pixelWidth
                ypix = (ycoo - xymin[1]) / pixelHeight
                vect.append(int(xpix))
                vect.append(int(ypix))
            #this_shape = MultiPolygon(shape(vect))
            #this_id = feature['properties']['ID']
            #polygons[this_id] = this_shape
            lc_type = feature['properties']['Code_18']
            lvalue = legend_df.loc[lc_type]
            count += 1
            #polygons[lvalue['LABEL3']] = Polygon(vect) # create polygon
            polygons[lvalue['LABEL3']] = vect # create polygon
            #if verb:
            #    print("{} is {}: {} ".format(feature['properties']['ID'], lc_type, lvalue['LABEL3']))

    print("Extracted {} polygons".format(len(polygons)))
    return polygons, legend_df
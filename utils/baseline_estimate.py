import datetime 
import requests
from datetime import date
import sys
import os
import requests
import pandas as pd
import xml.etree.ElementTree as et
import datetime
import math
import pickle
import numpy as np
from shapely import wkt

def find_potential_orbit_files(url):
    """
    Takes a url and sends a request returning a json object
    """
    response = requests.get(url)
    data = response.json()
    return data

def create_url_string(filename):
    """
    creates the correct url from the filename of interest
    """
    start = filename.split("_")[-5]
    stop = filename.split("_")[-4]
    mission = filename.split("_")[0]
    base_url= "https://qc.sentinel1.eo.esa.int/api/v1/?product_type=AUX_POEORB&validity_stop__gt=%s&validity_start__lt=%s&sentinel1__mission=%s&page_size=1"%(stop, start, mission)
    return base_url

def convert_utc_column_to_timestamp(data):
    col_list = data["UTC"].to_list()
    converted_list = []
    for val in col_list:
        val = val.strip("UTC=")
        val = val.split("T")
        val = " ".join(val)
        converted_list.append(datetime.datetime.strptime(val, '%Y-%m-%d %H:%M:%S.%f'))
    data["UTC"] = converted_list
    return data

def convert_xml_to_df(file):
    # Parse the file and get the root
    xtree = et.parse(file)
    xroot = xtree.getroot()
    # extract the osv elements we are interested in
    rows = xroot.findall('.//OSV')
    all_osv_data = {}
    for r in rows:
        # create a dictionary with the tag the key and text the value
        osv_data = {child.tag : child.text for child in list(r)}
        osv_data.pop("TAI") # remove the different time zones we dont need
        osv_data.pop("UT1")
        # loop through them and create one bit dictionary that can be converted to a dataframe
        for tag, data in osv_data.items():
            if not tag in all_osv_data.keys():
                all_osv_data[tag] = [data]
                continue
            all_osv_data[tag].append(data)
    all_osv_data = pd.DataFrame.from_dict(all_osv_data)
    all_osv_data = convert_utc_column_to_timestamp(all_osv_data)
    return all_osv_data


### Not used ###
def determine_rel_location(file1, file2, products):
    filt_products = products.loc[products['title'].isin([file1, file2])] # get the files we want 
    # get the overlap areas to determine the relative change 
    g1 = wkt.loads(filt_products.iloc[0]['footprint'])
    g2 = wkt.loads(filt_products.iloc[1]['footprint'])
    mean_match = (((g1.intersection(g2).area/g1.area)*100) +((g2.intersection(g1).area/g2.area)*100)) / 2
    for id1, p in products.iterrows():
        if p['title'] != file2:
            continue
        diff = (p['endposition'] - p['beginposition']).total_seconds() 
        diff = diff * ((100 - mean_match) / 100)
        start = p['beginposition'] + datetime.timedelta(seconds=diff)
        new_x, new_y = estimate_location(p, start)
        return [new_x, new_y]


def get_vector_data(products, vector_data=None):
    if vector_data is None:
        vector_data = {}
    for n, p in products.iterrows():
        xmlfile = "orbitfile.xml"
        if p['title'] in vector_data.keys():
            print("%s has previously been determined"%(p['title']))
            continue
        print("Querying for %s"%(p['title']))
        queryurl = create_url_string(p['title'])
        query_results = find_potential_orbit_files(queryurl)
        filelink = query_results['results'][0]['remote_url']
        if os.path.exists(xmlfile):
            os.remove(xmlfile)
        print("Getting the orbit file from %s"%(filelink))
        r = requests.get(filelink, allow_redirects=True)
        open(xmlfile, 'wb').write(r.content)
        print("Extracting information from xml file")
        start = p['beginposition'] - datetime.timedelta(seconds=30)
        end = p['endposition'] + datetime.timedelta(seconds=30)
        all_osv_data = convert_xml_to_df(xmlfile)
        filtered_data = all_osv_data[(end > all_osv_data["UTC"]) & (start < all_osv_data["UTC"])]
        xy = []
        for id1, p2 in filtered_data.iterrows():
            xy.append(([float(p2["X"]), float(p2["Y"]), float(p2["Z"])]))
        vector_data[p['title']] = xy
    return vector_data


def closestDistanceBetweenLines(a0,a1,b0,b1,clampAll=False,clampA0=False,clampA1=False,clampB0=False,clampB1=False):

    ''' Given two lines defined by numpy.array pairs (a0,a1,b0,b1)
        Return the closest points on each segment and their distance
    '''

    # If clampAll=True, set all clamps to True
    if clampAll:
        clampA0=True
        clampA1=True
        clampB0=True
        clampB1=True


    # Calculate denomitator
    A = a1 - a0
    B = b1 - b0
    magA = np.linalg.norm(A)
    magB = np.linalg.norm(B)
    
    _A = A / magA
    _B = B / magB
    
    cross = np.cross(_A, _B);
    denom = np.linalg.norm(cross)**2
    
    # If lines are parallel (denom=0) test if lines overlap.
    # If they don't overlap then there is a closest point solution.
    # If they do overlap, there are infinite closest positions, but there is a closest distance
    if not denom:
        d0 = np.dot(_A,(b0-a0))
        
        # Overlap only possible with clamping
        if clampA0 or clampA1 or clampB0 or clampB1:
            d1 = np.dot(_A,(b1-a0))
            
            # Is segment B before A?
            if d0 <= 0 >= d1:
                if clampA0 and clampB1:
                    if np.absolute(d0) < np.absolute(d1):
                        return a0,b0,np.linalg.norm(a0-b0)
                    return a0,b1,np.linalg.norm(a0-b1)
                
                
            # Is segment B after A?
            elif d0 >= magA <= d1:
                if clampA1 and clampB0:
                    if np.absolute(d0) < np.absolute(d1):
                        return a1,b0,np.linalg.norm(a1-b0)
                    return a1,b1,np.linalg.norm(a1-b1)
                
                
        # Segments overlap, return distance between parallel segments
        return None,None,np.linalg.norm(((d0*_A)+a0)-b0)

    
    
    # Lines criss-cross: Calculate the projected closest points
    t = (b0 - a0);
    detA = np.linalg.det([t, _B, cross])
    detB = np.linalg.det([t, _A, cross])

    t0 = detA/denom;
    t1 = detB/denom;

    pA = a0 + (_A * t0) # Projected closest point on segment A
    pB = b0 + (_B * t1) # Projected closest point on segment B


    # Clamp projections
    if clampA0 or clampA1 or clampB0 or clampB1:
        if clampA0 and t0 < 0:
            pA = a0
        elif clampA1 and t0 > magA:
            pA = a1
        
        if clampB0 and t1 < 0:
            pB = b0
        elif clampB1 and t1 > magB:
            pB = b1
            
        # Clamp projection A
        if (clampA0 and t0 < 0) or (clampA1 and t0 > magA):
            dot = np.dot(_B,(pA-b0))
            if clampB0 and dot < 0:
                dot = 0
            elif clampB1 and dot > magB:
                dot = magB
            pB = b0 + (_B * dot)
    
        # Clamp projection B
        if (clampB0 and t1 < 0) or (clampB1 and t1 > magB):
            dot = np.dot(_A,(pB-a0))
            if clampA0 and dot < 0:
                dot = 0
            elif clampA1 and dot > magA:
                dot = magA
            pA = a0 + (_A * dot)

    return np.linalg.norm(pA-pB)
    #return pA,pB,np.linalg.norm(pA-pB)
import os 
import glob
import datetime 
import geopandas
import datetime
from shapely import wkt as wkt2

def filter_dataframe_by_overlap(products, file_id, min_overlap=60):
    """
    Takes a dataframe and a specific file and determines the overlap between it and 
    every other file, returning a dataframe of products that match the minimum overlap
    
    Parameters
    ------
    products : dataframe 
        A dataframe containing information on the available products
    file_id : str
        The file id of the file we want to compare (needs to be in the dataframe as well)
    min_overlap : float, opt 
        The minimum percentage overlap between the images (default : 60)
        
    Returns
    ------
    filtered_data : dataframe
        The filtered dataframe containing any products which match the criteria
    """
    # get the footprint for the file of interest
    g1 = wkt2.loads(products.loc[file_id]['footprint'])
    wanted_indices = []
    for id1, p in products.iterrows(): # loop through the products
        if file_id == id1: # if its the same one skip it!
            continue
        # get the product footprint
        g2 = wkt2.loads(products.loc[id1]['footprint'])
        # calculate the match 
        mean_match = (((g1.intersection(g2).area/g1.area)*100) +((g2.intersection(g1).area/g2.area)*100)) / 2
        if mean_match < min_overlap:
            continue
        wanted_indices.append(id1)
    filtered_data = products.loc[wanted_indices]
    return filtered_data

def filter_dataframe_by_time(products, p, max_time=8):
    """
    Takes a dataframe and a specific product and returns only other products within a given time frame
    
    Parameters
    ------
    products : dataframe 
        A dataframe containing information on the available products
    p : series
        Pandas series for the product of interest
    max_time : int, opt 
        The maximum time difference between the images (default : 8)
        
    Returns
    ------
    filtered_data : dataframe
        The filtered dataframe containing any products which match the criteria
    """
    start = p['beginposition'] - datetime.timedelta(days=max_time)
    end = p['beginposition'] + datetime.timedelta(days=max_time)
    filtered_data = products[(end >= products["beginposition"]) & (products["beginposition"] >= start)]
    return filtered_data

def filter_dataframe_by_file_list(products, not_needed):
    potential_downloads = products["title"].to_list()
    titles_to_keep = []
    for potential in potential_downloads:
        # check for any match in existing downloads
        matching = any(potential in title for title in not_needed)
        if not matching:
            titles_to_keep.append(potential)
    # only keep the dataframe rows we want
    filtered_products = products[products['title'].isin(titles_to_keep)].sort_values(['ingestiondate'], ascending=True)
    return filtered_products

# Number of days in month
def numberOfDays(y, m):
  leap = 0
  if y% 400 == 0:
     leap = 1
  elif y % 100 == 0:
     leap = 0
  elif y% 4 == 0:
     leap = 1
  if m==2:
     return 28 + leap
  list = [1,3,5,7,8,10,12]
  if m in list:
     return 31
  return 30

def get_aoi_date_dict(aoi, shared_folder, getpoly = False):
    shape_files_folder = os.path.join(shared_folder, os.path.join("datasets", "shape_files"))
    cstudy_folder = os.path.join(shape_files_folder, "%s_burns"%(aoi))
    if not os.path.exists(cstudy_folder):
        print("%s does not exist"%(cstudy_folder))
    shp_files = [os.path.join(cstudy_folder, f) for f in os.listdir(cstudy_folder) if f.endswith(".shp")]
        
    # check for id - where ID or id 
    fid = "id"
    fdate = "date"
    if "kye" in aoi: 
        fid = "ID"
    elif "istrict" in aoi: 
        fdate = "FIREDATE"

    count = 0 
    for shp_file in shp_files:
        burns_dates = geopandas.read_file(shp_file)

        # Load dates
        date_dict = {int(d[fid]) : d[fdate] for n, d in burns_dates.iterrows()}
        for n, d in date_dict.items():
            new_d = "%s/%s/%s"%(d.split("-")[2], d.split("-")[1], d.split("-")[0])
            date_dict[n] = new_d
    
        if getpoly:
            polygon = None
            for index, row in burns_dates.iterrows():
                if int(index) == int(getpoly.split(" ")[0]):
                    polygon = row['geometry']
                    return polygon
        
        if count == 0:
            merge_dict = date_dict.copy()
        else:
            for index, row in date_dict.items():
                merge_dict[index] = row
                
    return merge_dict

def get_polygon_list(datasets, aoi):
    global polygons
    fstart = os.path.basename(aoi).split("_")[0]
    searchstr = fstart + "_burn_extent_*.geojson"
    polygons = glob.glob(os.path.join(datasets, searchstr))
    if len(polygons) == 0:
        return []
    poly_list = []
    for poly in polygons:
        fpoly = os.path.splitext(os.path.basename(poly))[0]
        poly_list.append(fpoly.split("_")[3])
    return poly_list

def get_data_dict(most_files, workbook, baselines):
    if workbook == "Coherence":
        data_dict = {"filename" : [], "date" : [], 'sensor' : [], 'seconddate': [], 'polarisation': [], 'rorbit': [], 'direction': [], 'perpbaseline' : []}
        for file in most_files:
            splits = os.path.basename(file).split("_")
            data_dict["filename"].append(file)
            date1 = datetime.datetime.strptime(splits[2], '%Y%m%d')
            data_dict["date"].append(date1)
            date2 = datetime.datetime.strptime(splits[3], '%Y%m%d')
            data_dict["seconddate"].append(date2)
            data_dict["sensor"].append(splits[1])
            data_dict["polarisation"].append(splits[5])
            data_dict['rorbit'].append(splits[0])
            data_dict['direction'].append(splits[4])
            if file in baselines.keys():
                data_dict['perpbaseline'].append(baselines[file])
            else:
                data_dict['perpbaseline'].append(0)
            
    elif workbook == "Backscatter":
        data_dict = {"filename" : [], "date" : [], 'sensor' : [], 'stime': [], 'etime': [], 'polarisation': [], 'rorbit': [], 'direction': []}

        for file in most_files:
            splits = os.path.basename(file).split("_")
            data_dict["filename"].append(file)
            date1 = datetime.datetime.strptime(splits[1], '%Y%m%d')
            data_dict["date"].append(date1)
            data_dict["sensor"].append(splits[0])
            data_dict["polarisation"].append(splits[6])
            data_dict['rorbit'].append(splits[2])
            data_dict['direction'].append(splits[3])
            data_dict['etime'].append(splits[5])
            data_dict['stime'].append(splits[4])
            
    return data_dict

def order_files_by_date(files, workbook):
    sorted_files = []
    date_to_name = {}
    for file in files:
        if workbook == "Coherence":
            t1 = os.path.basename(file).split("_")[2]
            t2 = os.path.basename(file).split("_")[3]
            t3 = os.path.basename(file).split("_")[4]
            t = t1 + "_" + t2 + "_" + t3
        elif workbook == "Backscatter":
            t1 = os.path.basename(file).split("_")[1]
            t2 = os.path.basename(file).split("_")[2]
            t = t1 + "_" + t2
        date_to_name[t] = file
    ordered_dates = sorted(list(date_to_name.keys()))
    sorted_files = [date_to_name[date] for date in ordered_dates]
    
    return sorted_files

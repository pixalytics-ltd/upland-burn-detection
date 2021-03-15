import os
import sys
import numpy as np
import json
import geojson as gj
from osgeo import ogr, osr, gdal
from pyproj import Proj, transform

# Enable GDAL/OGR exceptions
gdal.UseExceptions()

# GDAL & OGR memory drivers
GDAL_MEMORY_DRIVER = gdal.GetDriverByName('MEM')
OGR_MEMORY_DRIVER = ogr.GetDriverByName('Memory')

# Much simpler version than version below that does not work correctly
def cut_by_geojson(input_file, output_file, shape_geojson, verb = False, slc=False):

    # Get coords for bounding box
    with open (shape_geojson, 'r') as f:
        loadg = gj.loads(f.read())
    x, y = zip(*gj.utils.coords(loadg))
    
    del loadg
    xmin, xmax, ymin, ymax = min(x), max(x), min(y), max(y)
    if slc:
        xmin, ymin = convert_cs(xmin, ymin)
        xmax, ymax = convert_cs(xmax, ymax)
    #return
    # Use gdal translate
    ds = gdal.Open(input_file)
    # projWin = <ulx> <uly> <lrx> <lry>
    try:
        ds = gdal.Translate(output_file, ds, projWin = [xmin, ymax, xmax, ymin])
        ds = None
    except:
        print("Failed to extract from {}, skipping".format(input_file))
        if os.path.exists(output_file):
            os.remove(output_file)
        return
    
    # Load data and check has valid values
    dataset = gdal.Open(output_file, gdal.GA_ReadOnly)
    data = dataset.GetRasterBand(1).ReadAsArray()
    if np.nanmax(data) == 0:        
        print("No valid data in extracted subset, deleting subset file")
        os.remove(output_file)
    else:
        print("Band VV min {:.3f} max {:.3f}".format(np.nanmin(data),np.nanmax(data)))
    dataset = None
    del data
    
def convert_cs(x, y):
    
    #print(loadg.crs)
    inproj = Proj(init='epsg:27700')#loadg.crs)
    outproj = Proj(init='epsg:4326')
    
    lon, lat = transform(inproj, outproj, x, y)
    return lon, lat

def create_polygon(coords):
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for coord in coords:
        ring.AddPoint(float(coord[0]), float(coord[1]))
 
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return poly.ExportToWkt()
                      
def cut_by_geojson_old(input_file, output_file, shape_geojson, verb = False):

    # Get coords for bounding box
    with open (shape_geojson, 'r') as f:
        loadg = gj.loads(f.read())
    x, y = zip(*gj.utils.coords(loadg))
    min_x, max_x, min_y, max_y = min(x), max(x), min(y), max(y)

    # Open original data as read only
    dataset = gdal.Open(input_file, gdal.GA_ReadOnly)

    bands = dataset.RasterCount
    
    # Getting georeference info
    transform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()
    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = -transform[5]

    # Getting spatial reference of input raster
    srs = osr.SpatialReference()
    srs.ImportFromWkt(projection)
    if verb:
        band = dataset.GetRasterBand(1).ReadAsArray()
        cols, rows = band.shape
        band = None
        print("Input GeoTIFF coordinates: Upper Left {:.3f} {:.3f} Lower Right {:.3f} {:.3f} ".
              format(xOrigin, yOrigin, xOrigin+(pixelWidth*cols), yOrigin-(pixelHeight*rows)))

    # WGS84 projection reference
    OSR_WGS84_REF = osr.SpatialReference()
    OSR_WGS84_REF.ImportFromEPSG(4326)

    osgb = True  # Currently hard-coded
    if not osgb:
        if verb:
            print("Input for GeoJSON: ", min_x, max_x, min_y, max_y)

        # OSR transformation
        wgs84_to_image_trasformation = osr.CoordinateTransformation(OSR_WGS84_REF, srs)
        XYmin = wgs84_to_image_trasformation.TransformPoint(min_x, max_y)
        XYmax = wgs84_to_image_trasformation.TransformPoint(max_x, min_y)
    else:
        XYmin = [0,0]
        XYmax = [0,0]        
        XYmin[:] = min_x, max_y # Used max_y at top left corner
        XYmax[:] = max_x, min_y
    if verb:
        print("Input coordinates for GeoJSON: Upper Left {:.3f} {:.3f} Lower Right {:.3f} {:.3f} ".
              format(XYmin[0], XYmin[1], XYmax[0], XYmax[1]))

    # Computing Point1(i1,j1) [upper left], Point2(i2,j2) [lower right]
    i1 = int((XYmin[0] - xOrigin) / pixelWidth)
    if i1 < 0:
        print("i1 < 0, changed to 0")
        i1 = 0
        
    j1 = int((yOrigin - XYmin[1]) / pixelHeight)
    if j1 < 0:
        print("j1 < 0, changed to 0")
        j1 = 0
        
    i2 = int((XYmax[0] - xOrigin) / pixelWidth)
    if i2 < 0:
        print("i1 < 0, changed to {}".format(cols-1))
        i2 = cols - 1
        
    j2 = int((yOrigin - XYmax[1]) / pixelHeight)
    if j2 < 0:
        print("i1 < 0, changed to {}".format(rows-1))
        j2 = rows - 1
        
    new_cols = i2 - i1 + 1
    new_rows = j2 - j1 + 1
    if verb:
        print("Pixel coordinates for subset: Upper Left {} {} Lower Right {} {}".format( i1, j1, i2, j2))
        print("Size: Old {} {} New {} {} ".format(cols, rows, new_cols, new_rows))
    
    # New upper-left X,Y values
    new_x = xOrigin + (i1 * pixelWidth)
    new_y = yOrigin - (j1 * pixelHeight)
    if verb:
        print("Origin: Old {:.3f} {:.3f} New {:.3f} {:.3f} ".format(xOrigin, yOrigin, new_x, new_y))

    for i in loadg['features']:
        geo = i.get('geometry')
        geo_type = geo.get('type')
        if geo_type == 'Polygon':  # If it's a polygon, do this
            polycoords = geo.get('coordinates')
            wkt = create_polygon(polycoords[0])
            wkt_geom = ogr.CreateGeometryFromWkt(wkt)
        
    new_transform = (new_x, transform[1], transform[2], new_y, transform[4],
                     transform[5])
    if not osgb:
        wkt_geom.Transform(wgs84_to_image_trasformation)
        
    target_ds = GDAL_MEMORY_DRIVER.Create('', new_cols, new_rows, 1,
                                          gdal.GDT_Byte)
    target_ds.SetGeoTransform(new_transform)
    target_ds.SetProjection(projection)

    # Create a memory layer to rasterize from.
    ogr_dataset = OGR_MEMORY_DRIVER.CreateDataSource('shapemask')
    ogr_layer = ogr_dataset.CreateLayer('shapemask', srs=srs)
    ogr_feature = ogr.Feature(ogr_layer.GetLayerDefn())
    ogr_feature.SetGeometryDirectly(ogr.Geometry(wkt=wkt_geom.ExportToWkt()))
    ogr_layer.CreateFeature(ogr_feature)

    gdal.RasterizeLayer(target_ds, [1], ogr_layer, burn_values=[1],
                        options=["ALL_TOUCHED=TRUE"])

    # Create output file
    driver = gdal.GetDriverByName('GTiff')
    outds = driver.Create(output_file, new_cols, new_rows, bands,
                          gdal.GDT_Float32)

    # Read in bands and store all the data in bandList
    mask_array = target_ds.GetRasterBand(1).ReadAsArray()
    band_list = []

    for i in range(bands):
        band_list.append(dataset.GetRasterBand(i + 1).ReadAsArray(i1, j1,
                         new_cols, new_rows))

    nodata = 0
    for j in range(bands):
        data = np.where(mask_array == 1, band_list[j], mask_array)
            
        # Check there is valid data
        if data is None or np.nanmax(band_list[j]) is None:
            nodata += 1
        else:
            if np.nanmax(data) == 0:
                nodata += 1
            else:
                print("Band {} min {:.3f} max {:.3f}".format(j,np.nanmin(data),np.nanmax(data)))

        # Write output data
        outds.GetRasterBand(j + 1).SetNoDataValue(0)
        outds.GetRasterBand(j + 1).WriteArray(data)
        
    outds.SetProjection(projection)
    outds.SetGeoTransform(new_transform)

    target_ds = None
    dataset = None
    outds = None
    ogr_dataset = None
    
    if nodata == bands:
        print("No valid data in extracted subset, deleting")
        os.remove(output_file)

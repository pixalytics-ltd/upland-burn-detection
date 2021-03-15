import subprocess
from sentinelsat import SentinelAPI, geojson_to_wkt
from osgeo import ogr, osr
import geojson as gj
from IPython.display import clear_output

def find_new_data(
        api,
        start_date,
        end_date,
        search_area,
        product = "GRD",
        ):
    """
    Takes search criteria and runs a query on the sen5p data

    Parameters
    ------
    api : api
        api that can be used to query and download data
    start_date : datetime.date
        The start date for the search
    end_date : datetime.date
        The end date for the search
    search_area : wkt
        The search area in wkt format
    which_sat : str, opt
        Determines if we want to search for Sen1 or Sen2 data (default : 'sen2')

    Returns
    ------
    products : list?        ## TODO:  check this
        List of product IDs that match the search criteria
    """

    products = api.query(search_area,
                    date = (start_date, end_date),
                    platformname = 'Sentinel-1',
                    producttype = product
                    #raw = which_data,
                    )
    products = api.to_dataframe(products)
    return products

def check_for_existing_downloads(products, folder):
    """
    This checks the products returned from the query to see if they have already
    been downloaded in the folder # TODO: this will likely be checking a log file long term as the raw data will be deleted once analysed

    Parameters
    ------
    products : dataframe
        A dataframe containing the potential tiles to download
    folder : str
        The folder to check for existing tiles

    Returns
    ------
    filtered_products : dataframe
        A dataframe where any tiles that had already been downloaded have now been removed
    """
    # get list of existing downloads and potential downloads
    existing_downloads = [file for file in os.listdir(folder)]
    potential_downloads = products["title"].to_list()
    titles_to_keep = []
    for potential in potential_downloads:
        # check for any match in existing downloads
        matching = any(potential in title for title in existing_downloads)
        if not matching:
            titles_to_keep.append(potential)
    # only keep the dataframe rows we want
    filtered_products = products[products['title'].isin(titles_to_keep)].sort_values(['ingestiondate'], ascending=True)

    return filtered_products


def download_file(credentials, download_url, outfile):
    args = [
            "wget",
            '%s'%(download_url),
            "--user",
            credentials[0],
            "--password",
            credentials[1],
            "-O",
            outfile,
            ]

    # create the subprocess
    p = subprocess.Popen(args,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         bufsize=1,
                         universal_newlines=True)

    # forward messages from stdout and stderr onto the console
    with p.stdout as stdout:
        for line in iter(stdout.readline, b""):
            if line == "":
                break
            clear_output(wait=True)
            print("Downloading %s"%(outfile), line.rstrip())

    # wait to exit and retreieve the exit code
    exit_code = p.wait()

    # raise an exception if 'gpt' return an unexpected exit code
    if exit_code != 0:
        raise RuntimeError("Non-zero return code from download.")


def call_cophub(credentials, start_date, end_date, polygon_file, SLC = False):

    # WGS84 projection reference
    OSR_WGS84 = osr.SpatialReference()
    OSR_WGS84.ImportFromEPSG(4326)
    OSR_OSGB36 = osr.SpatialReference()
    OSR_OSGB36.ImportFromEPSG(27700)
    to_wgs84 = osr.CoordinateTransformation(OSR_OSGB36, OSR_WGS84)

    # Get coords for bounding box
    with open (polygon_file, 'r') as f:
        loadg = gj.loads(f.read())
    xvals, yvals = zip(*gj.utils.coords(loadg))
    coords = []
    for x, y in zip(xvals, yvals):
        # Transform to WGS84
        xy = to_wgs84.TransformPoint(x, y)
        coords.append((xy[0], xy[1]))
    del loadg
    print(coords)
    polygon = gj.Polygon([coords])
    wkt = geojson_to_wkt(polygon)

    api = SentinelAPI(credentials[0], credentials[1], 'https://scihub.copernicus.eu/dhus')
    if SLC:
        products = find_new_data(api, start_date, end_date, wkt, product="SLC")
    else:
        products = find_new_data(api, start_date, end_date, wkt)
    
    return products, wkt
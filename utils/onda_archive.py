import os
import requests
import time
import call_cophub as callc
from IPython.display import clear_output
from sentinelsat import SentinelAPI

import portal_credentials as portalc

def batch_download_from_archive(cop_credentials, ids, downloadfolder):
    download_num = 0
    currently_requested = None
    for id1, data in ids.iterrows():
        session = requests.Session()
        session.auth = (cop_credentials[0], cop_credentials[1])
        waiting_for = 0
        queryurl = """https://scihub.copernicus.eu/dhus/odata/v1/Products('%s')"""%(id1)
        online = session.get(queryurl)
        if "401" in online.text:
            print("Copernicus 401 message skipping {} download".format(id1))
            continue
        online = online.text.split("<d:Online>")[1][:5]
        print(online)
        if online == "false": # offline
            if download_num == 0:
                # Load ONDA credentials
                pfile = "onda.txt"
                home = os.path.expanduser("~")
                if not os.path.exists(os.path.join(home, pfile)):
                    portalc.save_credentials(pfile)
                onda_credentials = portalc.read_credentials(pfile)

            while True:
                session = requests.Session()
                session.auth = (onda_credentials[0], onda_credentials[1])
                queryurl = """https://catalogue.onda-dias.eu/dias-catalogue/Products(%s)"""%(id1)
                offline = session.get(queryurl)
                offline = offline.text.split("offline")[1][2:6]
                if offline == "true":
                    offline = True 
                elif offline == "fals":
                    offline = False
                if offline:
                    clear_output(wait=True)
                    print("Downloaded %s of %s files"%(download_num, len(ids)))
                    print("Requested %s, id = %s"%(data['title'], id1))
                    print("Waiting for %s minutes"%(waiting_for))
                    if id1 == currently_requested:
                        time.sleep(300)
                        waiting_for += 5
                    else:
                        requested = session.post("https://catalogue.onda-dias.eu/dias-catalogue/Products(%s)/Ens.Order"%(id1))
                        currently_requested = id1
                else:
                    download_url = """https://catalogue.onda-dias.eu/dias-catalogue/Products(%s)/$value"""%(id1)
                    callc.download_file(onda_credentials, download_url, os.path.join(downloadfolder, data['title'] + '.zip'))
                    clear_output(wait=True)
                    print("Downloaded %s of %s files"%(download_num, len(ids)))
                    print("Requested %s, id = %s"%(data['title'], id1))
                    break

        else: # Try from Copernicus hub
            api = SentinelAPI(cop_credentials[0], cop_credentials[1], 'https://scihub.copernicus.eu/dhus')
            print("Downloading from Copernicus Hub")
            api.download(id1, directory_path=downloadfolder)


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
            
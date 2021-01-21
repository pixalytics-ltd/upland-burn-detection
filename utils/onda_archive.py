import os
import requests
import time
import call_cophub as callc
from IPython.display import clear_output

def batch_download_from_archive(credentials, products, downloadfolder):
    currently_requested = None
    for download_num, (id1, data) in enumerate(products.iterrows()):
        session = requests.Session()
        session.auth = (credentials[0], credentials[1])
        waiting_for = 0
        while True:
            queryurl = """https://catalogue.onda-dias.eu/dias-catalogue/Products(%s)"""%(id1)
            offline = session.get(queryurl)
            offline = offline.text.split("offline")[1][2:6]
            if offline == "true":
                offline = True 
            elif offline == "fals":
                offline = False
            if offline:
                clear_output(wait=True)
                print("Downloaded %s of %s files"%(download_num, len(products)))
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
                callc.download_file(credentials, download_url, os.path.join(downloadfolder, data['title'] + '.zip'))
                clear_output(wait=True)
                print("Downloaded %s of %s files"%(download_num, len(products)))
                print("Requested %s, id = %s"%(data['title'], id1))
                break
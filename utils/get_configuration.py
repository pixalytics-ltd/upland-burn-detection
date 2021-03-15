import os
import numpy as np
import yaml
import pickle

def get_config(cstudy, workbook, v2=False):
    ofiles = []
    folder = os.getcwd()
    if "pre-process" in folder:
        folder = os.path.dirname(folder)
    utils_dir = os.path.join(folder,"utils")
    with open(os.path.join(utils_dir, "configuration.yml")) as yaml_file:
        config = yaml.safe_load(yaml_file)
        print("Loaded configuration: {:}.".format(config))
        sharedfolder = os.path.expanduser(config.get("sharedfolder"))

    # Global variables and setup
    home = os.path.expanduser("~")
    basefolder = os.path.join(home, sharedfolder)
    cstudyfolder = os.path.join(basefolder, cstudy)
    if workbook == "Backscatter":
        datafolder = os.path.join(cstudyfolder, "backscatter_tiffs")
    elif workbook == "Coherence":
        if v2:
            datafolder = os.path.join(cstudyfolder, "coherence_tiffs2")
        else:
            datafolder = os.path.join(cstudyfolder, "coherence_tiffs1")
    if not os.path.exists(datafolder):
        os.mkdir(datafolder)
    ofiles = [os.path.join(datafolder, file) for file in os.listdir(datafolder)]
    if len(ofiles) == 0:
        print("Could not find any files in %s"%(datafolder))
        return {}, {}, {}
    notebook_folder = os.path.join(home, "notebooks")

    ## setup output folder
    outfolder = os.path.join(notebook_folder, "output_folder")
    if not os.path.exists(outfolder) and not os.path.islink(outfolder):
        os.mkdir(outfolder)
       
    if workbook == "Backscatter":
        return ofiles, outfolder, {}
    
    ## Get baseline dictionary 
    datasets = os.path.join(basefolder, "datasets")
    baseline_file = os.path.join(datasets, os.path.join("baselines", "baselines_%s.p"%(cstudy)))
    if os.path.exists(baseline_file):
        print("Loading baselines from {}".format(baseline_file))
        baselines = pickle.load(open(baseline_file, "rb"))
    else:
        baselines = {}
    
    return ofiles, outfolder, baselines

# Used in first set of workbooks and ERA5Land
def get_configuration(cstudy, workbook="s1ard"):
    cfolder = os.getcwd()    
    folder = os.path.join(os.path.dirname(cfolder.split("notebooks")[0]),"notebooks")
    utils_dir = os.path.join(folder,"utils")
    with open(os.path.join(utils_dir, "configuration.yml")) as yaml_file:
        config = yaml.safe_load(yaml_file)
        print("Loaded configuration: {:}.".format(config))
        sharedfolder = os.path.expanduser(config.get("sharedfolder"))

    # Global variables and setup
    home = os.path.expanduser("~")
    basefolder = os.path.join(home, sharedfolder)
    s1ardfolder = os.path.join(basefolder, workbook)
    datasets = os.path.join(basefolder, "datasets")
    notebook_folder = os.path.join(home, "notebooks")

    ## setup output folder
    outfolder = os.path.join(notebook_folder, "output_folder")
    if not os.path.exists(outfolder) and not os.path.islink(outfolder):
        os.mkdir(outfolder)

    ## setup temp folder
    tmpfolder = os.path.join(home, "temp")
    if not os.path.exists(tmpfolder):
        os.mkdir(tmpfolder)

    # Subsets
    casefolder = os.path.join(basefolder, cstudy)
    if os.path.exists(os.path.join(casefolder, cstudy + '_%s.npy'%(workbook))):
        tfiles = np.load(os.path.join(casefolder, cstudy + '_%s.npy'%(workbook)))
    else:
        tfiles = []
    ofiles = []
    for file in tfiles:
        if workbook=="s1slc":
            cfolder = os.path.join(basefolder, "s1slc/final_merged_images")
        else:
            cfolder = casefolder
        ofiles.append(os.path.join(cfolder,os.path.basename(file)))
    del tfiles
    hdfile = os.path.join(casefolder, cstudy + '_%s.h5'%(workbook))
    pfile = os.path.join(casefolder, cstudy + '_%s.txt'%(workbook))

    # Verbose output mode
    verbose = False
    
    # Display graphs
    graphics = True
    
    return basefolder, s1ardfolder, datasets, outfolder, tmpfolder, ofiles, hdfile, pfile, verbose, graphics


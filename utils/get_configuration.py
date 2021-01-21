import os
import numpy as np
import yaml

def get_configuration(cstudy):
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
    s1ardfolder = os.path.join(basefolder, "s1ard")
    datasets = os.path.join(basefolder, "datasets")

    ## setup output folder
    outfolder = os.path.join(home, "output_folder")
    if not os.path.exists(outfolder):
        os.mkdir(outfolder)

    ## setup temp folder
    tmpfolder = os.path.join(home, "temp")
    if not os.path.exists(tmpfolder):
        os.mkdir(tmpfolder)

    # Subsets
    casefolder = os.path.join(basefolder, cstudy)
    if os.path.exists(os.path.join(casefolder, cstudy + '_s1ard.npy')):
        tfiles = np.load(os.path.join(casefolder, cstudy + '_s1ard.npy'))
    else:
        tfiles = []
    ofiles = []
    for file in tfiles:
        ofiles.append(os.path.join(casefolder,os.path.basename(file)))
    del tfiles
    hdfile = os.path.join(casefolder, cstudy + '_s1ard.h5')
    pfile = os.path.join(casefolder, cstudy + '_s1ard.txt')

    # Verbose output mode
    verbose = False
    
    # Display graphs
    graphics = True
    
    return basefolder, s1ardfolder, datasets, outfolder, tmpfolder, ofiles, hdfile, pfile, verbose, graphics
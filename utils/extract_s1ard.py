import numpy as np
from PIL import Image, ImageDraw

def extract_s1ard(cpolygons, subarray, verb = False):

    products = 6  # VV, VH, VHrVV, RFDI, NVHI, NVVI
    pnames = []
    tlength = subarray.shape[0]
    mask_dict = {}
    features = []

    if cpolygons is None: # No CORINE data
        features = 1
        mean_s1data = np.zeros((features,products,tlength), dtype=np.float)
        std_s1data = np.zeros((features,products,tlength), dtype=np.float)         
        features = ['Whole-Polygon']
        
        fnum = 0
        # Polarised backscatter data extraction
        for lay_num, lay in enumerate(subarray):
            for pol_num, pol_img in enumerate(lay):
                if pol_num == 0:
                    vv = pol_img
                else:
                    vh = pol_img

            # Stack layers into s1data mean and standard deviation output arrays
            for pnum in range(products):
                if pnum == 0:
                    #print(mean_s1data.shape,fnum,pnum,lay_num,np.nanmean(vv))
                    mean_s1data[fnum,pnum,lay_num] = np.nanmean(vv)
                    std_s1data[fnum,pnum,lay_num] = np.nanstd(vv)
                    if fnum == 0 and lay_num == 0:
                        pnames.append('VV')
                elif pnum == 1:
                    mean_s1data[fnum,pnum,lay_num] = np.nanmean(vh)
                    std_s1data[fnum,pnum,lay_num] = np.nanstd(vh)
                    if fnum == 0 and lay_num == 0:
                        pnames.append('VH')
                elif pnum == 2:
                    mean_s1data[fnum,pnum,lay_num] = np.nanmean(vh/vv)
                    std_s1data[fnum,pnum,lay_num] = np.nanstd(vh/vv)
                    if fnum == 0 and lay_num == 0:
                        pnames.append('VHrVV')
                elif pnum == 3:
                    mean_s1data[fnum,pnum,lay_num] = np.nanmean((vv - vh)/(vv + vh))
                    std_s1data[fnum,pnum,lay_num] = np.nanstd((vv - vh)/(vv + vh))
                    if fnum == 0 and lay_num == 0:
                        pnames.append('RFDI')
                elif pnum == 4:
                    mean_s1data[fnum,pnum,lay_num] = np.nanmean(vh/(vv + vh))
                    std_s1data[fnum,pnum,lay_num] = np.nanstd(vh/(vv + vh))
                    if fnum == 0 and lay_num == 0:
                        pnames.append('NVHI')
                elif pnum == 5:
                    mean_s1data[fnum,pnum,lay_num] = np.nanmean(vv/(vv + vh))
                    std_s1data[fnum,pnum,lay_num] = np.nanstd(vv/(vv + vh))
                    if fnum == 0 and lay_num == 0:
                        pnames.append('NVVI')

        # Clear arrays
        del vv, vh

        
    else:
        # Loop through each land cover class
        for feat, p in cpolygons.items():
            if feat == 'Sea and ocean':  # Skip as not needed
                continue
            else:
                img = Image.new('L', (subarray[0,0,:,:].shape[1], subarray[0,0,:,:].shape[0]), 0)                                             
                draw = ImageDraw.Draw(img)                                                                                                     
                draw.polygon(p, fill=1)
                img = np.array(img)
                mask_dict[feat] = img
                features.append(feat)

        # Results
        if verb:
            print("Features for burnt area: {}".format(features))    

        # Extract S1ARD data into arrays
        mean_s1data = np.zeros((len(features),products,tlength), dtype=np.float)
        std_s1data = np.zeros((len(features),products,tlength), dtype=np.float)

    fnum = 0
    for feat, current_mask in mask_dict.items():
        # Polarised backscatter data extraction
        for lay_num, lay in enumerate(subarray):
            for pol_num, pol_img in enumerate(lay):
                if pol_num == 0:
                    vv = pol_img[current_mask==1]
                else:
                    vh = pol_img[current_mask==1]

            # Stack layers into s1data mean and standard deviation output arrays
            for pnum in range(products):
                if pnum == 0:
                    #print(mean_s1data.shape,fnum,pnum,lay_num,np.nanmean(vv))
                    mean_s1data[fnum,pnum,lay_num] = np.nanmean(vv)
                    std_s1data[fnum,pnum,lay_num] = np.nanstd(vv)
                    if fnum == 0 and lay_num == 0:
                        pnames.append('VV')
                elif pnum == 1:
                    mean_s1data[fnum,pnum,lay_num] = np.nanmean(vh)
                    std_s1data[fnum,pnum,lay_num] = np.nanstd(vh)
                    if fnum == 0 and lay_num == 0:
                        pnames.append('VH')
                elif pnum == 2:
                    mean_s1data[fnum,pnum,lay_num] = np.nanmean(vh/vv)
                    std_s1data[fnum,pnum,lay_num] = np.nanstd(vh/vv)
                    if fnum == 0 and lay_num == 0:
                        pnames.append('VHrVV')
                elif pnum == 3:
                    mean_s1data[fnum,pnum,lay_num] = np.nanmean((vv - vh)/(vv + vh))
                    std_s1data[fnum,pnum,lay_num] = np.nanstd((vv - vh)/(vv + vh))
                    if fnum == 0 and lay_num == 0:
                        pnames.append('RFDI')
                elif pnum == 4:
                    mean_s1data[fnum,pnum,lay_num] = np.nanmean(vh/(vv + vh))
                    std_s1data[fnum,pnum,lay_num] = np.nanstd(vh/(vv + vh))
                    if fnum == 0 and lay_num == 0:
                        pnames.append('NVHI')
                elif pnum == 5:
                    mean_s1data[fnum,pnum,lay_num] = np.nanmean(vv/(vv + vh))
                    std_s1data[fnum,pnum,lay_num] = np.nanstd(vv/(vv + vh))
                    if fnum == 0 and lay_num == 0:
                        pnames.append('NVVI')

        # Increment for features
        fnum +=1 

        # Clear arrays
        del vv, vh

    # Set missing values to NAN    
    mean_s1data[mean_s1data == 0] = np.nan
    std_s1data[std_s1data == 0] = np.nan

    return mean_s1data, std_s1data, pnames, features
import os
import numpy as np
import matplotlib.pyplot as plt
plt.set_loglevel("critical")
import matplotlib.image as mpimg
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
import datetime
from pathlib import Path

import warnings
warnings.filterwarnings('ignore')

def plot_line(xdata, ydata, stdata, product, outfile):
    fig, ax1 = plt.subplots(figsize = (10,6))
    plt.xticks(rotation=45)
    plt.ylabel(product, fontsize=12)
    ax1.xaxis.set_major_locator(ticker.MultipleLocator(15)) # Space out labels - every 15th

    plt.errorbar(x=xdata, y=ydata, yerr=stdata, linestyle='-', marker='None', color='black', label=product)
    plt.tight_layout()

    # Save Graph
    fig.savefig(outfile, dpi=300)
    
def get_burn_dates(xdata, burn_start, burn_end):
    xdata = sorted([datetime.datetime.strptime(d, "%Y%m%d") for d in xdata])
    if burn_start < xdata[0]:
        burn_start_points = [-0.5, -0.5]
    else:
        for n, d in enumerate(xdata):
            if burn_start == d:
                burn_start_points = [n, n]       
                break
            elif burn_start < d:
                burn_start_points = [n-1, n]
                break
            burn_start_points = [n+1, n+1]
    for n, d in enumerate(xdata):
        if burn_end == d:
            burn_end_points = [n, n]      
            break
        elif burn_end < d:
            burn_end_points = [n-1, n]
            break
        burn_end_points = [n+1, n+1]
    
    return np.mean(burn_start_points), np.mean(burn_end_points)

def plot_lines(xdata, ydata, stdata, xdata2, ydata2, stdata2, fnames, pnames, product2, outfile, burn_start, graphics = True):

    # Setup variables
    prows = len(pnames)
    frows = len(fnames)
    if prows == 0 or frows == 0:
        return
    print("Running for {} features with {} products".format(frows, prows))
    
    # Setup plot
    fig, ax = plt.subplots(nrows = prows, ncols = 1, figsize = (10,6*prows))
        
    # Spacing of ticks on x-axis
    if len(xdata) < 12:
        spacing = len(xdata)
    else:
        spacing = 12
    #print("Xaxis spacing {}".format(spacing))
    
    # Setup showing burn date range
    burn_start, burn_end = get_burn_dates(xdata, burn_start, burn_start)
            
    # Setup colour palette
    cpal=['olive','green','orange','purple','red','blue', 'yellow']

    for pnum in range(prows):  # Each layer has its own plot

        # Setup legend
        patches = []
        
        # Plot primary data - product for each frame
        for fnum in range(frows):
            pname = fnames[fnum]
            ax[pnum].errorbar(x=xdata, y=ydata[fnum,pnum,:], yerr=stdata[fnum,pnum,:], linestyle='-', marker='None', color=cpal[fnum], label=pname, ecolor='gainsboro', elinewidth= 10)
            patches.append(mpatches.Patch(color=cpal[fnum], label=pname))
            
            # Set y-range
            ptile = np.percentile(stdata[fnum,pnum,:], 50)
            minv = np.nanmin(ydata[fnum,pnum,:]) - ptile
            maxv = np.nanmax(ydata[fnum,pnum,:]) + ptile
            #print("{} {} yrange min {:.3f} max {:.3f} std ptile {:.3f}".format(pnum, pname, minv, maxv, ptile))
            if np.isnan(minv) or np.isnan(maxv):
                continue
            else:
                ax[pnum].set_ylim([minv, maxv])

        # Setup axes formatting
        ax[pnum].axvline(burn_start, linewidth = 5, alpha=0.2, color='red')
        ax[pnum].get_xaxis().set_major_formatter(ticker.StrMethodFormatter('{x:.0f}'))
        ax[pnum].set_ylabel(pnames[pnum], fontsize=12)

        # Plot on second y-axis
        ax2 = ax[pnum].twinx()
        ax2.errorbar(x=xdata2, y=ydata2, yerr=stdata2, linestyle='-', marker='None', color='black', label=product2)
        ax2.set_ylabel(product2)

        # Finalise legend
        patches.append(mpatches.Patch(color='black', label=product2))
        plt.legend(handles=patches, loc='upper left', fontsize=12)

    # Rotate x-axis labelling for every plot
    for ax in fig.axes:
        ax.tick_params(axis='x', labelrotation=45)
        ax.xaxis.set_major_locator(ticker.LinearLocator(numticks=spacing)) # Space out labels, set number
            
    # Tight layout
    plt.tight_layout()

    # Save Graph
    fig.savefig(outfile, dpi=300)
    
    # Do not display
    if not graphics:
        plt.close()  # prevents figure from being displayed when code cell is executed

def plot_images(darray, ofiles, verb = False, hdf = False):

    # Number of columns
    numcols = 4

    if hdf:
        layers = len(ofiles)
        if hdf == 'VV':
            band = 0
        else:
            band = 1
    else:
        layers = darray.shape[0]
    prows = int(layers/numcols)
    if (prows - (layers > 2.0)) < 0.0:
        prows += 1

    # Setup plot
    fig, ax1 = plt.subplots(nrows = prows , ncols = numcols, figsize = (10,8))

    xdim, ydim = 0, 0
    for dlayer in range(layers):
        if verb:
            print("Loading layer {}".format(dlayer))
        if hdf:
            temp=np.copy(darray[dlayer,band,:,:])
            rescaled = display_layer(ofiles, temp, dlayer, verb = verb, hdf = True)
        else:
            rescaled = display_layer(ofiles[dlayer], darray, dlayer, verb = verb)

        # Display images
        ax1[xdim,ydim].imshow(rescaled, interpolation='nearest', vmin=0, cmap=plt.cm.gray_r)
        dir, fname = os.path.split(ofiles[dlayer])
        ax1[xdim,ydim].title.set_text(fname[4:12])

        ydim += 1
        if ydim == numcols:
            xdim += 1
            ydim = 0

    for ax in fig.axes:
        ax.tick_params(labelrotation=45)        
        
def display_layer(ofile, dtarray, layer, verb = False, hdf = False):
    
    if hdf:
        darray = dtarray
    else:
        darray = dtarray[layer,:,:]
        
    minv = np.nanmin(darray)
    maxv = np.nanmax(darray)
    if verb:
        print("Original min {:.3f} max {:.3f}".format(minv,maxv))
    rescaled = np.zeros((darray.shape[0],darray.shape[1]), dtype=np.byte)
    
    # Slope
    maxval = 40
    minval = -85
    slope = 255/(maxval - minval)
    # Apply conversion
    rescaled[:,:] = (darray - minv) * slope
    minv = np.nanmin(rescaled)
    maxv = np.nanmax(rescaled)
    if verb:
        print("Rescaled min {} max {} using slope {:.3f} minv {:.3f}".format(minv, maxv, slope, minval))
    return rescaled

def display_geotiff(filename):
    import matplotlib.pyplot as plt
    import gdal
    
    ds = gdal.Open(str(Path(filename).with_suffix(".tif")))
    
    classes_band = ds.GetRasterBand(1).ReadAsArray()
    cols, rows = classes_band.shape
    
    plt.figure(figsize = (10,10))
    plt.imshow(classes_band)
    plt.title("Classes")
    plt.show()
    
    confidence_band = ds.GetRasterBand(2).ReadAsArray()
    plt.figure(figsize = (10,10))
    plt.imshow(confidence_band, cmap="RdYlGn")
    plt.title("Confidence")
    plt.show()
    


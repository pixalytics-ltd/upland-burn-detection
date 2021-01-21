import numpy as np

# https://tonyladson.wordpress.com/tag/antecedent-precipitation-index/
def calc_era_api(dt_num, mean_parameters, subarray, list_of_dates, verb = False):
    prodnum = 8 # Precipitation
    elength = len(dt_num) # Input ERA dates
    tlength = subarray.shape[0] # Input S1 dates
    hlength = 5 # length of historical dates to calculate API for
    
    # Define output arrays
    mean_edata = np.zeros(tlength, dtype=np.float)
    std_edata = np.zeros(tlength, dtype=np.float)
    
    for enum in range(elength):  # Loop for ERA dates
        for snum in range(tlength):  # Loop for S1ARD dates
            if list_of_dates[snum] == dt_num[enum]:
                for hnum in range(hlength):
                    if enum-hnum > 0:
                        if hnum == 0:
                            k = 1.0
                        else:
                            k = np.power(0.95,hnum)
                        mean_edata[snum] += mean_parameters[enum-hnum,prodnum] * k
                        #print("mean_edate[{}] = {} loop {} using {}".format(snum,mean_edata[snum],hnum,k))

    return mean_edata, std_edata

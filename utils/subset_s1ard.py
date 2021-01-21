import numpy as np

def subset_s1ard(df, subarray, d_widget, sub_widget, verb = False):
    
    if d_widget == 'All':
        dates_with_data = []
        num = 0
        for i, row in df.iterrows():
            num += 1
            dates_with_data.append(num)

        return df, subarray, dates_with_data
    else:
        
        full_df = df.copy()
        if d_widget == 'date' or d_widget == 'stime':
            subset_df = full_df[full_df[d_widget] >= sub_widget]
            print("Subsetting to {} >= {}".format(d_widget, sub_widget))
        else:
            subset_df = full_df.set_index(d_widget).loc[sub_widget]
            print("Subsetting to {} = {}".format(d_widget, sub_widget))

        layers = len(subset_df)
        print("Original {} subsetted to {} layers".format(subarray.shape,layers))
        #print(subset_df)
        new_subarray = np.zeros((layers,subarray.shape[1],subarray.shape[2],subarray.shape[3]), dtype=float)

        # Create subset array of layers
        num = 0
        snum = 0
        dates_with_data = []
        for i, row in full_df.iterrows():
            if d_widget == 'date' or d_widget == 'stime':
                if row[d_widget] < sub_widget:
                    num += 1
                    continue                
            elif row[d_widget] != sub_widget:
                    num += 1
                    continue
            new_subarray[snum,:,:,:] = subarray[num,:,:,:]
            #print(i,num,row[d_widget],sub_widget)
            snum += 1
            dates_with_data.append(num)
            num += 1
        #print(dates_with_data)
        
        return subset_df, new_subarray, dates_with_data
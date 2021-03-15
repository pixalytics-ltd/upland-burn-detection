import os

def generate_polylist(polygons):
    
    if len(polygons) == 0:
        print("No polygons exist for {}".format(searchstr))
    poly_list = []
    poly_sublist = []
    for poly in polygons:
        fpoly = os.path.splitext(os.path.basename(poly))[0]
        numstr = fpoly.split("_")[3]
        if not "-" in numstr:
            poly_list.append(numstr)
        else:
            poly_sublist.append(numstr.replace("-","."))

    # Convert string list to int list, sort then convert back
    poly_int = [int(i) for i in poly_list]
    poly_int.sort()
    poly_list = [str(i).zfill(3) for i in poly_int]
    del poly_int 
    # Convert and sort sub-polygons
    poly_subflt = [float(i) for i in poly_sublist]
    poly_subflt.sort()
    for subpoly in poly_subflt:
        substr = str(subpoly).split(".")[1]
        polystr = str(int(subpoly)).zfill(3) + '-' + substr
        poly_list.append(polystr)
    
    return poly_list
import os
import subprocess
from enum import Enum, auto, unique

## SNAP GPT
gpt = '/opt/snap/bin/gpt'
pconcvert = '/opt/snap/bin/pconvert'

@unique
class OutputFormat(Enum):
    DIMAP = auto()
    GEOTIFF = auto()

_output_format_lookup = {
    OutputFormat.DIMAP: ("BEAM-DIMAP", ".dim"),
    #OutputFormat.GEOTIFF: ("GeoTIFF-BigTIFF", ".tif"),
    OutputFormat.GEOTIFF: ("GeoTIFF+XML", ".tif"),
}

def save_file(filename, text):
    with open(filename, "w") as text_file:
         text_file.write(text)
            
def get_shape_file_paths(shape_file_dir: str) -> [str]:
    return [os.path.join(shape_file_dir, file) for file in os.listdir(shape_file_dir) if file[-4:] == ".shp"]

def convert_tiff(infile,outfolder):
    # Running SNAP DIMAP to GeoTIFF converstion
    assert os.path.exists(pconcvert), "Unable to find 'pconvert' executable."
    cmd = "{} -f tifp -o {} {} ".format(pconvert,ofolder,infile)
    

def run_gpt(infile,outfile,xml_file,properties_file, subset = False, multiple = False, layer = False):
    assert os.path.exists(gpt), "Unable to find 'gpt' executable."
    assert os.path.isfile(xml_file), "Unable to locate '{}'.".format(xml_file)
    assert os.path.isfile(properties_file), "Unable to locate '{}'.".format(properties_file)
    
    # create the subprocess
    args = [
            gpt,
            "-e",
            xml_file,
            "-p",
            properties_file,
            "-t",
            outfile,
            "-Pfile={}".format(infile)
        ]
    if subset:
        args.append("-PgeoRegion={}".format(subset))
    if multiple:
        if len(multiple) == 1:
            args.append("-Pfile2={}".format(multiple))
        else:
            count = 2
            for file in multiple:
                args.append("-Pfile"+str(count)+"={}".format(file))
                count += 1
    if layer:
        args.append("-PsourceBands={}".format(layer))
        
    print("Running: ",args)

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
            print(line.rstrip())

    # wait to exit and retreieve the exit code
    exit_code = p.wait()

    # raise an exception if 'gpt' return an unexpected exit code
    if exit_code != 0:
        raise RuntimeError("Non-zero return code from GPT.")
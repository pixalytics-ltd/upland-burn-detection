import os
import subprocess
## SNAP GPT
gpt = '/opt/snap/bin/gpt'
pconcvert = '/opt/snap/bin/pconvert'

def convert_tiff(infile,outfolder):
    # Running SNAP DIMAP to GeoTIFF converstion
    assert os.path.exists(pconcvert), "Unable to find 'pconvert' executable."
    cmd = "{} -f tifp -o {} {} ".format(pconvert,ofolder,infile)
    

def run_gpt(infile,outfile,xml_file,properties_file, subset = False, collocate = False):
    assert os.path.exists(gpt), "Unable to find 'gpt' executable."
    assert os.path.isfile(xml_file), "Unable to locate '{}'.".format(xml_file)
    assert os.path.isfile(properties_file), "Unable to locate '{}'.".format(properties_file)
    
    # create the subprocess
    if subset and not collocate:
        args = [
                gpt,
    #            "-e",
                xml_file,
                "-p",
                properties_file,
                "-t",
                outfile,
                "-Pfile={}".format(infile),
                "-PgeoRegion={}".format(subset)
            ]
    elif collocate:
        args = [
                gpt,
                "-e",
                xml_file,
                "-p",
                properties_file,
                "-t",
                outfile,
                "-Pfile={}".format(infile),
                "-Pfile2={}".format(collocate),
                "-PgeoRegion={}".format(subset)
            ]
    else:
        args = [
                gpt,
    #            "-e",
                xml_file,
                "-p",
                properties_file,
                "-t",
                outfile,
                "-Pfile={}".format(infile)
            ]
    
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
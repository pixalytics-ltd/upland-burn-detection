import os
import subprocess

def syscmd(cmd, verb = False):
    """
    Enables commands to be run from inside the python code with appropriate outputs and error returns when necessary
    
    :param cmd: command to be run
    :type cmd: str
    :param verb: enable more verbose outputs
    :type verb: bool
    """
    logger = setup_logging(args)
    if verb:
        cmd = cmd.split()
        proc = subprocess.Popen(cmd)  # ,stdout=subprocess.PIPE, stderr=subprocess.PIPE,universal_newlines=True)
    else:
        cmd = cmd.split()
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    out, errors = proc.communicate()
    if out != "" and out is not None:
        print("Cmd Output: {}".format(out))

    if proc.returncode != 0:
        print("Crash encountered when running {}".format(cmd))
        print("Cmd Output: {}".format(out))
        print("Cmd Errors: {}".format(errors))
        sys.exit()


def execmd(cmd, verb = False):
    """
    Enables commands to be run from inside the python code with the output returned

    :param cmd: command to be run
    :type cmd: str
    :param verb: enable more verbose outputs
    :type verb: bool
    """

    # Replaced due to shell=True being a security hazard
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         close_fds=True)
    output = p.stdout.read()
    p.stdin.close()
    p.stdout.close()
    # p.communicate()
    if output:
        return output
    else:
        print("No output returned")
        return None

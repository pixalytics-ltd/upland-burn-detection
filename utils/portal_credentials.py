import os
import getpass
home = os.path.expanduser("~")

def read_credentials(file):
    # Login details are parsed    
    with open(os.path.join(home, file), 'r') as f1:
        first_line = f1.readline().rstrip("\n")
    credentials = first_line.split(",")
    print("Login details retrieved")
    return credentials

def save_credentials(file):
    # Login details are saved
    uname = getpass.getpass('Username:') 
    pswd = getpass.getpass('Password:')
    
    output_file = open(os.path.join(home, file),'w')
    output_file.write(uname+","+pswd)
    output_file.close()
    
    return
    
#! python3

import os
import json
from sys import argv
import zipfile
import time
import sys

BACKUP_PATH = "backup"
CFG_PATH = "cfg.json"
MAX_STORED_BACKUPS = 10
FOLDER_LIST = []
FILE_LIST = []
FORCE_BACKUP = False

ERROR_CONFIG = 1
ERROR_ARGUMENTS = 2
ERROR_PATH = 3
ERROR_ACCESS = 4

def generate_name()->str:
    if FORCE_BACKUP:
        sToday = time.strftime("%y-%m-%dT%H_%M_%S", time.localtime())
    else:
        sToday = time.strftime("%y-%m-%d", time.localtime())
    return sToday

def bckup_file(path: str, zip: zipfile.ZipFile):
    full_path = os.path.realpath(path) #realpath to something, not link
    zip.write(full_path, full_path.replace(':', ''))

def bckup_folder(path: str, zip: zipfile.ZipFile):
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            full_path = os.path.realpath(full_path)
            try:
                zip.write(full_path, full_path.replace(':', ''))
            except PermissionError as err:
                sys.stderr.write(str(err) + "\n")

def write_cfg():
    global FILE_LIST, FOLDER_LIST, MAX_STORED_BACKUPS
    data = {
        "files": FILE_LIST,
        "folders": FOLDER_LIST,
        "max_stored_backups" : MAX_STORED_BACKUPS
    }
    file = open(CFG_PATH, "w")
    json.dump(data, file)
    file.close()

def load_cfg():
    global FILE_LIST, FOLDER_LIST, MAX_STORED_BACKUPS
    file = open(CFG_PATH, "r")
    data = json.load(file)
    file.close()
    FILE_LIST = data['files']
    FOLDER_LIST = data['folders']
    MAX_STORED_BACKUPS = data['max_stored_backups']

def create_zip(name: str) -> zipfile.ZipFile:
    zfile = zipfile.ZipFile(os.path.join(BACKUP_PATH, name), 'w', zipfile.ZIP_LZMA)
    return zfile

def close_zip(zip: zipfile.ZipFile):
    zip.close()

def get_backups():
    files = []
    for _, _, filenames in os.walk(BACKUP_PATH):
        files += [f for f in filenames if f.endswith(".zip")]
        break
    # Get only those that fit the format YY-MM-DD
    backups = []
    for f in files:
        tokens = f.split(".")[0].split("-")
        if len(tokens) != 3:
            continue
        try:
            int(tokens[0])
            int(tokens[1])
            int(tokens[2])
        except ValueError:
            #print(f + " is not a backup zipfile.")
            continue
        backups.append(f)
    return backups

def delete_old_backups(filenames):
    if len(filenames) <= MAX_STORED_BACKUPS:
        return
    #Make sure the list is sorted
    filenames = sorted(filenames)
    files_to_del = filenames[:len(filenames) - MAX_STORED_BACKUPS]
    for fname in files_to_del:
        full_path = os.path.abspath(os.path.join(BACKUP_PATH, fname))
        os.remove(full_path)
        #print("Deleted old backup: " + fname)

def restore(zippath):
    if not os.path.exists(zippath):
        return ERROR_PATH
    zip = zipfile.ZipFile(zippath, 'r')
    #Check access 
    realpaths = []
    for path in zip.namelist():
        disk , rest = path.split('/', 1)
        disk += ":/"
        realpaths.append((path, os.path.join(disk,rest)))
    
    errors = 0
    for _ , path in realpaths:
        if os.path.exists(path) and not os.access(path, os.W_OK):
            errors += 1
            sys.stderr.write("Cannot access " + path)
    
    if errors > 0:
        return ERROR_ACCESS

    for zippath, realpath in realpaths:
        data = zip.read(zippath)
        try:
            os.makedirs(os.path.split(realpath)[0], exist_ok=True)
            f = open(realpath, "wb")
            f.write(data)
            f.close()
        except FileNotFoundError as err:
            sys.stderr.write(f"Cannot unpack {zippath} to {realpath}. ", err)
            return ERROR_ACCESS

def run():
    global FILE_LIST, FOLDER_LIST, MAX_STORED_BACKUPS, FORCE_BACKUP
    #Create stuff
    if not os.path.exists(BACKUP_PATH):
        os.mkdir(BACKUP_PATH)
    if not os.path.exists(CFG_PATH):
        write_cfg()

    #Load config file
    load_cfg()
    
    zipfilename = generate_name() + ".zip"
    if not FORCE_BACKUP:
        #Check 2: Check if there is a zip file with today's date
        if os.path.exists(os.path.join(BACKUP_PATH,zipfilename)):
            print(f"ZIP file for today already exists ({zipfilename})! Backup not required.")
            write_cfg()
            exit(0)

    zip = create_zip(zipfilename)

    for filename in FILE_LIST:
        bckup_file(filename, zip)
    for folder in FOLDER_LIST:
        bckup_folder(folder, zip)
    close_zip(zip)

    if FORCE_BACKUP:
        sys.stdout.write("Created backup in " + zipfilename)

    #Check if we need to delete old files
    backups = sorted(get_backups())
    delete_old_backups(backups)
    #Update config
    LAST_BACKUP = int(time.time())
    write_cfg()

if __name__ == "__main__":
    print(argv)
    if len(argv) > 1 and argv[1] in ['-r', '--restore']:
        if len(argv) > 2:
            exit(restore(argv[2]))
        else:
            exit(ERROR_ARGUMENTS)
    if len(argv) > 1 and argv[1] in ['-f', '--force']:
        FORCE_BACKUP = True
    run()
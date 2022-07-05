#! python3

import os
import json
import zipfile
import time

BACKUP_PATH = "backup"
CFG_PATH = "cfg.json"
MAX_STORED_BACKUPS = 10
LAST_BACKUP = 0
FOLDER_LIST = []
FILE_LIST = []

ERROR_CONFIG = 1

def generate_name()->str:
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
            print(full_path)
            zip.write(full_path, full_path.replace(':', ''))

def write_cfg():
    global FILE_LIST, FOLDER_LIST, MAX_STORED_BACKUPS, LAST_BACKUP
    data = {
        "files": FILE_LIST,
        "folders": FOLDER_LIST,
        "max_stored_backups" : MAX_STORED_BACKUPS,
        "last_backup" : LAST_BACKUP
    }
    file = open(CFG_PATH, "w")
    json.dump(data, file)
    file.close()

def load_cfg():
    global FILE_LIST, FOLDER_LIST, MAX_STORED_BACKUPS, LAST_BACKUP
    file = open(CFG_PATH, "r")
    data = json.load(file)
    file.close()
    FILE_LIST = data['files']
    FOLDER_LIST = data['folders']
    MAX_STORED_BACKUPS = data['max_stored_backups']
    LAST_BACKUP = data['last_backup']

def create_zip(name: str) -> zipfile.ZipFile:
    zfile = zipfile.ZipFile(os.path.join(BACKUP_PATH, name + ".zip"), 'w', zipfile.ZIP_STORED)
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
            print(f + " is not a backup zipfile.")
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
        print("Deleted old backup: " + fname)

def run():
    global FILE_LIST, FOLDER_LIST, MAX_STORED_BACKUPS, LAST_BACKUP
    #Create stuff
    if not os.path.exists(BACKUP_PATH):
        os.mkdir(BACKUP_PATH)
    if not os.path.exists(CFG_PATH):
        write_cfg()

    #Load config file
    load_cfg()

    #Check 1: Check last update date in cfg
    now_time = time.localtime()
    last_time = time.localtime(LAST_BACKUP)
    if now_time.tm_year == last_time.tm_year and now_time.tm_yday == last_time.tm_yday:
        print("Backup not required.")
        exit(0)
    #Check 2: Check if there is a zip file with today's date
    zipfilename = generate_name()
    if os.path.exists(os.path.join(BACKUP_PATH,zipfilename)):
        print("ZIP file for today already exists! Backup not required.")
        LAST_BACKUP = int(time.time()) #make sure the update date is correct
        write_cfg()
        exit(0)

    zip = create_zip(zipfilename)

    for filename in FILE_LIST:
        bckup_file(filename, zip)
    for folder in FOLDER_LIST:
        bckup_folder(folder, zip)
    close_zip(zip)

    #Check if we need to delete old files
    backups = sorted(get_backups())
    delete_old_backups(backups)
    #Update config
    LAST_BACKUP = int(time.time())
    write_cfg()

if __name__ == "__main__":
    run()
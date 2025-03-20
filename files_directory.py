import os
import datetime
from pathlib import Path



files = {}
dir_path = None


def getLastModifiedDate(file_path):
    modified_time = os.path.getmtime(file_path)
    return modified_time


def setFileNames(directory):
    global files
    global dir_path 
    if dir_path:
        files = {f.name: getLastModifiedDate(f) for f in Path(directory).iterdir() if f.is_file()}
        return files

def getFileNames():
    global files
    return files


def getFilePath(file_name):
    global dir_path
    file_path = f"{dir_path}/{file_name}"
    return file_path
    

def setDirPath(new_path):
    global dir_path
    string_path = new_path[1:-1]
    if os.path.exists(new_path) and os.path.isdir(new_path):
        dir_path = new_path
        print(f"Added {new_path} to shared directories.")
        setFileNames(dir_path)
    elif os.path.exists(string_path) and os.path.isdir(string_path):
        dir_path = string_path
        print(f"Added {new_path} to shared directories.")
        setFileNames(string_path)
    else:
        print("Invalid directory path")


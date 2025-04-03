import os
import datetime
from pathlib import Path



files = {}
private_files = {}
dir_path = None
private_dir_path = None


def getLastModifiedDate(file_path):
    modified_time = os.path.getmtime(file_path)
    return modified_time


def setFileNames(directory):
    global files
    global dir_path 
    if dir_path:
        files = {f.name: getLastModifiedDate(f) for f in Path(directory).iterdir() if f.is_file()}
        return files

def setPrivateFileNames(directory):
    global private_files
    global private_dir_path 
    if private_dir_path:
        files = {f.name: getLastModifiedDate(f) for f in Path(directory).iterdir() if f.is_file()}
        return files

def getFileNames():
    global files
    return files

def getPrivateFileNames():
    global private_files
    return private_files

def getFilePath(file_name):
    global dir_path
    file_path = f"{dir_path}/{file_name}"
    return file_path

def getPrivateFilePath(file_name):
    global private_dir_path
    file_path = f"{private_dir_path}/{file_name}"
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

def setPrivateDirPath(new_path):
    global private_dir_path
    string_path = new_path[1:-1]
    if os.path.exists(new_path) and os.path.isdir(new_path):
        private_dir_path = new_path
        print(f"Added {new_path} to shared directories.")
        setPrivateFileNames(private_dir_path)
    elif os.path.exists(string_path) and os.path.isdir(string_path):
        private_dir_path = string_path
        print(f"Added {new_path} to shared directories.")
        setPrivateFileNames(private_dir_path)
    else:
        print("Invalid directory path")

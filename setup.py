from distutils.core import setup
import py2exe

#TODO Find a way to change BACKUPER_CMD and BACKUPERW_CMD in settings_editor to .exe when deploying

includes = ["sys", "time", "zipfile", "json", "os", "re", "subprocess", "tkinter",
    "datetime", "shutil"]
excludes = ["asyncio", "hashlib", "elementtree", "multiprocession", "overlapped",
    "socket", "ssl", "testcapi", "testinternalcapi", "queue", "select", "unicodedata",
    "multiprocessing", "decimal", "bz2"]
packages = []
dll_excludes = []
setup(windows=[
    {'script': "backuper.py", "dest_base": "backuper"}, 
    {'script': "settings_editor.pyw"}],
    options={
        "py2exe":{
            "compressed": 2,
            "optimize": 2,
            "includes": includes,
            "excludes": excludes,
            "packages": packages,
            "dll_excludes": dll_excludes,
        }
    })
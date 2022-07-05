#! python3

from tkinter import *
from tkinter import ttk
import json
from tkinter import filedialog
import datetime
import os
import subprocess
from tkinter import dialog
from tkinter import messagebox
import locale

CFG_PATH = "cfg.json"
TASK_NAME = "RunBackuper"
XML_TASK_FORMAT = """<?xml version="1.0" ?>
<!--
This sample schedules a task to start on a daily basis.
-->
<Task xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
    <RegistrationInfo>
        <Author>rand</Author>
        <Version>0.1.0</Version>
        <Description>Backuper task.</Description>
    </RegistrationInfo>
    <Triggers>
        <CalendarTrigger>
            <StartBoundary>{}</StartBoundary>
            <ScheduleByDay>
                <DaysInterval>1</DaysInterval>
            </ScheduleByDay>
        </CalendarTrigger>
    </Triggers>
    <Settings>
        <Enabled>true</Enabled>
		<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
        <AllowStartOnDemand>true</AllowStartOnDemand>
        <AllowHardTerminate>true</AllowHardTerminate>
    </Settings>
    <Actions>
        <Exec>
            <Command>{}</Command>
			<WorkingDirectory>{}</WorkingDirectory>
        </Exec>
    </Actions>
</Task>"""

CREATE_TASK_COMMAND = 'schtasks /create /xml task.xml /tn \{}'.format(TASK_NAME)
DELETE_TASK_COMMAND = 'schtasks /delete /tn \{} /f'.format(TASK_NAME)
QUERY_TASK_COMMAND = 'schtasks /query /tn \{}'.format(TASK_NAME)

def load_cfg():
    file = open(CFG_PATH, "r")
    data = json.load(file)
    file.close()
    return data

def write_cfg(data):
    file = open(CFG_PATH, "w")
    json.dump(data, file)
    file.close()

class App(Frame):
    def __init__(self, master, cfg):
        self.master = master
        self.cfg = cfg
        Frame.__init__(self, master)
        self.pack(fill='both', expand=True)

        self.create_widgets()

    def create_widgets(self):
        buttonsFrame = Frame(self)
        buttonsFrame.grid(column=0, row=0, sticky="EW")

        folderButtons = Frame(self)
        folderButtons.grid(column=1, row=2, sticky="N")
        self.bAddFolder = ttk.Button(folderButtons, text="+", width=4)
        self.bAddFolder.pack(side=TOP)
        self.bRemoveFolder = ttk.Button(folderButtons, text="-", width=4)
        self.bRemoveFolder.pack(side=TOP)

        fileButtons = Frame(self)
        fileButtons.grid(column=1, row=1, sticky="N")
        self.bAddFile = ttk.Button(fileButtons, text="+", width=4)
        self.bAddFile.pack(side=TOP)
        self.bRemoveFile = ttk.Button(fileButtons, text="-", width=4)
        self.bRemoveFile.pack(side=TOP)

        self.bCreateTask = ttk.Button(buttonsFrame, text="Create Task")
        self.bCreateTask.pack(side=LEFT)

        self.bRemoveTask = ttk.Button(buttonsFrame, text="Remove Task")
        self.bRemoveTask.pack(side=LEFT)

        self.bSaveConfig = ttk.Button(buttonsFrame, text="Save Config")
        self.bSaveConfig.pack(side=LEFT)
        
        self.treeFile = ttk.Treeview(self, show='tree')
        self.treeFolder = ttk.Treeview(self, show='tree')
        self.treeFile.column("#0", width= 500)
        self.treeFolder.column("#0", width= 500)
        self.load_filelist()
        self.load_folderlist()

        vscrlbarFile = ttk.Scrollbar(self, orient='vertical', command=self.treeFile.yview)
        vscrlbarFolder = ttk.Scrollbar(self, orient='vertical', command=self.treeFolder.yview)

        self.treeFile.configure(yscrollcommand=vscrlbarFile.set)
        self.treeFolder.configure(yscrollcommand=vscrlbarFolder.set)

        # XXX They are overlapping
        self.treeFile.grid(column=0, row=1, sticky="news")
        vscrlbarFile.grid(column=0,row=1, sticky="nse")
        self.treeFolder.grid(column=0, row=2, sticky="news")
        vscrlbarFolder.grid(column=0,row=2, sticky="nse")

        # Create the application variable.
        self.vMaxBackups = IntVar()
        # Set it to some value.
        self.vMaxBackups.set(self.cfg["max_stored_backups"])
        # Tell the entry widget to watch this variable.
        Label(buttonsFrame, text="Max Stored Backups:").pack(side=LEFT)
        self.sbMaxBackups = Spinbox(buttonsFrame, from_=1, to=100, textvariable=self.vMaxBackups)
        self.sbMaxBackups.pack(side=LEFT, fill=BOTH, expand=True)

        self.bAddFile.bind("<Button>", self.add_file)
        self.bAddFolder.bind("<Button>", self.add_folder)
        self.bCreateTask.bind("<Button>", self.create_windows_task)
        self.bRemoveFile.bind("<Button>", self.remove_file)
        self.bRemoveFolder.bind("<Button>", self.remove_folder)
        self.bRemoveTask.bind("<Button>", self.delete_windows_task)
        self.bSaveConfig.bind("<Button>", self.save_config)

        self.columnconfigure(0, weight=1) # column with treeview
        self.rowconfigure(1, weight=1) # row with treeview      
        self.rowconfigure(2, weight=1) # row with treeview      

    def print_contents(self, event):
        print("Hi. The current entry content is:",
              self.contents.get())

    def load_filelist(self):
        for path in self.cfg['files']:
            self.treeFile.insert('', 'end', path, text=path)


    def load_folderlist(self):
        for path in self.cfg['folders']:
            self.treeFolder.insert('', 'end', path, text=path)

    def create_windows_task(self, event):
        #NOTE Need to do xml file because there you can't set working directory when creating using command line 
        xml_file = open("task.xml", 'w')
        start_time = datetime.datetime.now()
        start_time = start_time.replace(hour=18, minute=0, second=0, microsecond=0)
        xml_file.write(XML_TASK_FORMAT.format(datetime.datetime.isoformat(start_time), "backuper.pyw", os.path.abspath(".")))
        xml_file.close()
        result = subprocess.run(CREATE_TASK_COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            messagebox.showinfo("Create Task", "Task Created:\n" + result.stdout.decode("CP852"))
        else:
            #FIXME Fix the decoding here
            messagebox.showerror("Create Task", "Cannot Create Task:\n" + result.stderr.decode("CP852"))
        os.remove("task.xml")


    def delete_windows_task(self, event):
        result = subprocess.run(DELETE_TASK_COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            messagebox.showinfo("Remove Task", "Task Removed:\n" + result.stdout.decode("CP852"))
        else:
            #FIXME Fix the decoding here
            messagebox.showerror("Remove Task", "Cannot Remove Task:\n" + str(result.stderr.decode('CP852')))

    def add_file(self, event):
        filenames = filedialog.askopenfilenames()
        if filenames == "":
            return
        for filename in filenames:
            self.treeFile.insert('', 'end', filename, text=filename)

    def add_folder(self, event):
        foldername = filedialog.askdirectory()
        if foldername == "":
            return
        self.treeFolder.insert('', 'end', foldername, text=foldername)

    def remove_file(self, event):
        selected = self.treeFile.selection()
        self.treeFile.delete(*selected)

    def remove_folder(self, event):
        selected = self.treeFolder.selection()
        self.treeFolder.delete(*selected)

    def save_config(self, event):
        files = []
        for path in self.treeFile.get_children(''):
            files.append(path)
        folders = []
        for path in self.treeFolder.get_children(''):
            folders.append(path)
        self.cfg['files'] = files
        self.cfg['folders'] = folders
        self.cfg['max_stored_backups'] = self.vMaxBackups.get()
        write_cfg(self.cfg)

if __name__ == "__main__":
    root = Tk()
    cfg = load_cfg()
    myapp = App(root, cfg)
    myapp.mainloop()
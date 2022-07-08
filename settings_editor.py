#! python3

import datetime
import json
import os
import re
import subprocess
from tkinter import *
from tkinter import filedialog, messagebox, ttk

from backupper import BACKUP_PATH

CFG_PATH = "cfg.json"
TASK_NAME = "RunBackupper"
XML_TASK_FORMAT = """<?xml version="1.0" ?>
<!--
This sample schedules a task to start on a daily basis.
-->
<Task xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
    <RegistrationInfo>
        <Author>rand</Author>
        <Version>0.1.0</Version>
        <Description>Backupper task.</Description>
    </RegistrationInfo>
    <Triggers>
        <CalendarTrigger>
            <StartBoundary>{}</StartBoundary>
            <ScheduleByDay>
                <DaysInterval>{}</DaysInterval>
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

BACKUPPER_CMD = "backupper.py"
BACKUPPERW_CMD = "backupper.pyw"

def load_cfg():
    file = open(CFG_PATH, "r")
    data = json.load(file)
    file.close()
    return data

def write_cfg(data):
    file = open(CFG_PATH, "w")
    json.dump(data, file)
    file.close()

class RestoreDialog:
    def __init__(self, master) -> None:
        self.master = master
        self.selected = ""
        self.dlg = Toplevel(self.master)
        self.dlg.title("Restore Files")
        #self.dlg.geometry("300x200+0+0")
        self.dlg.resizable(FALSE, FALSE)
        frame = Frame(self.dlg)
        frame.pack(fill=BOTH, expand=TRUE)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="WARNING!\nRestoring will remove the currently stored files!\n\nSelect backup:").grid(column=0, row=0, columnspan=2, sticky="NEWS")
        
        backups = []
        for _,_, filenames in os.walk(BACKUP_PATH):
            backups = [filename for filename in filenames if filename.endswith(".zip")]
            break
        self.listbox = Listbox(frame, listvariable=StringVar(value=backups))
        self.listbox.grid(column=0,row=1, columnspan=2, sticky="NEWS")

        vscrlbar = ttk.Scrollbar(frame, orient='vertical', command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=vscrlbar.set)
        vscrlbar.grid(column=0, row=1, columnspan=2, sticky="ENS")
        
        ttk.Button(frame, text="Restore", command=self.select).grid(column=0,row=2, sticky="NEWS")
        ttk.Button(frame, text="Cancel", command=self.dismiss).grid(column=1,row=2, sticky="NEWS")

        self.dlg.protocol("WM_DELETE_WINDOW", self.dismiss) # intercept close button
        self.dlg.transient(self.master)   # dialog window is related to main
    
    def show(self):
        self.dlg.wait_visibility() # can't grab until window appears, so we wait

        master_width, master_height, x, y = re.split('x|\+|-',self.dlg.master.geometry())
        width, height, _, _ = re.split('x|\+|-',self.dlg.geometry())
        self.dlg.geometry("{}x{}{:+}{:+}".format(width, height, int(int(x) + int(master_width)/2 - int(width)/2), int(int(y) + int(master_height)/2 - int(height)/2)))

        self.dlg.grab_set()        # ensure all input goes to our window
        self.dlg.wait_window()     # block until window is destroyed
        return self.selected

    def dismiss (self):
        self.dlg.grab_release()
        self.dlg.destroy()

    def select(self):
        try:
            self.selected = self.listbox.selection_get()
            self.dismiss()
        except TclError as err:
            messagebox.showinfo("Restore Backup", "Select what backup to restore.")

class CreateTaskDialog:
    def __init__(self, master) -> None:
        self.master = master
        self.data = None
        self.dlg = Toplevel(self.master)
        self.dlg.title("Create Task")
        self.dlg.resizable(FALSE, FALSE)
        frame = Frame(self.dlg)
        frame.pack(fill=BOTH, expand=TRUE)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Time:").grid(column=0, row=0, sticky="NEWS")
        ttk.Label(frame, text="Interval (days):").grid(column=0, row=1, sticky="NEWS")

        self.daysvar = IntVar(self.dlg, 1)
        self.hourvar = IntVar(self.dlg, 18)
        self.minutevar = IntVar(self.dlg, 00)

        timeFrame = Frame(frame)
        timeFrame.grid(column=1,row=0, sticky="NEWS")
        ttk.Spinbox(timeFrame, from_ = 0, to=23, wrap=True,  textvariable=self.hourvar, state='readonly').pack(side=LEFT)
        ttk.Label(timeFrame, text=":").pack(side=LEFT)
        ttk.Spinbox(timeFrame, from_ = 0, to=59, wrap=True, textvariable=self.minutevar, state='readonly').pack(side=LEFT)

        ttk.Spinbox(frame, from_=1, to=30, wrap=True, textvariable=self.daysvar, state='readonly').grid(column=1,row=1, sticky="NEWS")

        buttonFrame = Frame(frame)
        buttonFrame.grid(column=0,row=2, columnspan=2)
        ttk.Button(buttonFrame, text="Create", command=self.create).grid(column=0, row=0)
        ttk.Button(buttonFrame, text="Cancel", command=self.dismiss).grid(column=1, row=0)

        self.dlg.protocol("WM_DELETE_WINDOW", self.dismiss) # intercept close button
        self.dlg.transient(self.master)   # dialog window is related to main
    
    def show(self):
        self.dlg.wait_visibility() # can't grab until window appears, so we wait

        master_width, master_height, x, y = re.split('x|\+|-',self.dlg.master.geometry())
        width, height, _, _ = re.split('x|\+|-',self.dlg.geometry())
        self.dlg.geometry("{}x{}{:+}{:+}".format(width, height, int(int(x) + int(master_width)/2 - int(width)/2), int(int(y) + int(master_height)/2 - int(height)/2)))

        self.dlg.grab_set()        # ensure all input goes to our window
        self.dlg.wait_window()     # block until window is destroyed
        return self.data

    def dismiss (self):
        self.dlg.grab_release()
        self.dlg.destroy()

    def create(self):
        try:
            self.data = {
                "hour": self.hourvar.get(),
                "minute": self.minutevar.get(),
                "days_interval" : self.daysvar.get()
            }
            self.dismiss()
        except TclError as err:
            messagebox.showinfo("Create Task Error", str(err))

class App(Frame):
    def __init__(self, master, cfg):
        self.master = master
        self.cfg = cfg
        Frame.__init__(self, master)
        self.master.title("Backupper Config Editor")
        self.pack(fill='both', expand=True)
        self.create_widgets()

    def create_widgets(self):
        folderButtons = Frame(self)
        folderButtons.grid(column=1, row=4, sticky="N")
        self.bAddFolder = ttk.Button(folderButtons, text="+", width=4)
        self.bAddFolder.pack(side=TOP)
        self.bRemoveFolder = ttk.Button(folderButtons, text="-", width=4)
        self.bRemoveFolder.pack(side=TOP)

        fileButtons = Frame(self)
        fileButtons.grid(column=1, row=2, sticky="N")
        self.bAddFile = ttk.Button(fileButtons, text="+", width=4)
        self.bAddFile.pack(side=TOP)
        self.bRemoveFile = ttk.Button(fileButtons, text="-", width=4)
        self.bRemoveFile.pack(side=TOP)
        
        buttonsFrame = Frame(self)
        buttonsFrame.grid(column=0, row=0, sticky="EW")
        self.bCreateTask = ttk.Button(buttonsFrame, text="Create Task")
        self.bCreateTask.pack(side=LEFT)
        self.bRemoveTask = ttk.Button(buttonsFrame, text="Remove Task")
        self.bRemoveTask.pack(side=LEFT)
        self.bSaveConfig = ttk.Button(buttonsFrame, text="Save Config")
        self.bSaveConfig.pack(side=LEFT)
        self.bCreateBackup = ttk.Button(buttonsFrame, text="Create Backup")
        self.bCreateBackup.pack(side=LEFT)
        self.bRestoreBackup = ttk.Button(buttonsFrame, text="Restore")
        self.bRestoreBackup.pack(side=LEFT)
        
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

        ttk.Label(self, text="Files:").grid(column=0, row=1, sticky="news")
        ttk.Label(self, text="Folders:").grid(column=0, row=3, sticky="news")
        # XXX They are overlapping
        self.treeFile.grid(column=0, row=2, sticky="news")
        vscrlbarFile.grid(column=0,row=2, sticky="nse")
        self.treeFolder.grid(column=0, row=4, sticky="news")
        vscrlbarFolder.grid(column=0,row=4, sticky="nse")

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
        self.bCreateBackup.bind("<Button>", self.create_backup)
        self.bRestoreBackup.bind("<Button>", self.restore_backup)

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
        result = CreateTaskDialog(self.master).show()
        if result is None:
            return
        #NOTE Need to do xml file because there you can't set working directory when creating using command line 
        xml_file = open("task.xml", 'w')
        start_time = datetime.datetime.now()
        start_time = start_time.replace(hour=result['hour'], minute=result['minute'], second=0, microsecond=0)
        xml_file.write(XML_TASK_FORMAT.format(datetime.datetime.isoformat(start_time), result['days_interval'], BACKUPPERW_CMD, os.path.abspath(".")))
        xml_file.close()
        result = subprocess.run(CREATE_TASK_COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.remove("task.xml")
        if result.returncode == 0:
            messagebox.showinfo("Create Task", "Task Created:\n" + result.stdout.decode("CP852"))
        else:
            #FIXME Fix the decoding here
            messagebox.showerror("Create Task", "Cannot Create Task:\n" + result.stderr.decode("CP852"))


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

    def create_backup(self,event):
        result = subprocess.run(f'{BACKUPPER_CMD} -f', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            messagebox.showinfo("Create Backup", "Success:\n" + result.stdout.decode("CP852"))
        else:
            #FIXME Fix the decoding here
            messagebox.showerror("Create Backup", "ERROR:\n" + result.stderr.decode("CP852"))

    def restore_backup(self,event):
        selected = RestoreDialog(self.master).show()
        if selected != "":
            result = subprocess.run(f'{BACKUPPER_CMD} -r {os.path.join(BACKUP_PATH, selected)}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                messagebox.showinfo("Restore Successful", "Success:\nRestored backup from " + selected)
            else:
                #FIXME Fix the decoding here
                messagebox.showerror("Restore Failed", f"ERROR {result.returncode}\n" + result.stderr.decode("CP852"))


def run():
    if os.path.exists(CFG_PATH):
        cfg = load_cfg()
    else:
        cfg = {"files" : [], "folders": [], "max_stored_backups": 10}
    root = Tk()
    myapp = App(root, cfg)
    myapp.mainloop()

if __name__ == "__main__":
    run()

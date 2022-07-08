#Backupper
Backupper is a simple application that allows you to backup and restore files and folders.
Create scheduled task to repeat the operation periodically.

##Usage
1. Run settings_editor.pyw (or settings_editor.exe).
2. Add files and folders you want to backup using + buttons next to their respective lists.
3. Set maximum amount of backups you want stored.
4. Save config.
5. Use **Create Task** button to create Windows' scheduled task. You can remove the task using **Remove Task** button. (Created task is named "RunBackupper", if you want to further customize the task beyond time and days interval open Task Scheduler - press **Ctrl+R** and run __taskschd.msc__)

You can also create backup manually by pressing **Create Backup**.
To restore saved backup press **Restore** and select zipfile with the date you want to use.
All backups are stored in _backups_ folder. 

###Warning
There may be bugs. Use at your own risk.
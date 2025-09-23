import os
import winshell
from win32com.client import Dispatch

def create_silent_desktop_shortcut():
    """Create a desktop shortcut for the silent Expense Tracker"""
    desktop = winshell.desktop()
    path = os.path.join(desktop, "Expense Tracker (Silent).lnk")
    target = os.path.join(os.getcwd(), "ExpenseTracker.vbs")
    wDir = os.getcwd()
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = wDir
    shortcut.Description = "Personal Expense & Income Tracker (Silent Mode)"
    shortcut.save()
    
    print(f"Silent desktop shortcut created: {path}")

if __name__ == '__main__':
    try:
        create_silent_desktop_shortcut()
        print("✅ Silent desktop shortcut created successfully!")
        print("You can now double-click 'Expense Tracker (Silent)' on your desktop.")
        print("The app will launch directly without showing any terminal windows!")
    except Exception as e:
        print(f"❌ Error creating shortcut: {e}")
        print("You can manually run the app using 'ExpenseTracker.vbs'")

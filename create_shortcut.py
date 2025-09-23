import os
import winshell
from win32com.client import Dispatch

def create_desktop_shortcut():
    """Create a desktop shortcut for the Expense Tracker"""
    desktop = winshell.desktop()
    path = os.path.join(desktop, "Personal Expense Tracker.lnk")
    target = os.path.join(os.getcwd(), "Expense_Tracker.bat")
    wDir = os.getcwd()
    icon = target
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = wDir
    shortcut.IconLocation = icon
    shortcut.Description = "Personal Expense & Income Tracker"
    shortcut.save()
    
    print(f"Desktop shortcut created: {path}")

if __name__ == '__main__':
    try:
        create_desktop_shortcut()
        print("✅ Desktop shortcut created successfully!")
        print("You can now double-click 'Personal Expense Tracker' on your desktop to launch the app.")
    except Exception as e:
        print(f"❌ Error creating shortcut: {e}")
        print("You can manually run the app using 'Expense_Tracker.bat'")

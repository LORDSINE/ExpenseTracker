Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\nitro\Desktop\web"
WshShell.Run """C:\Users\nitro\Desktop\web\.venv\Scripts\pythonw.exe"" desktop_app.py", 0, False

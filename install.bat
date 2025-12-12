@echo off
echo Installing Windows C Drive Cleaner...

REM Create installation directory
if not exist "%ProgramFiles%\Windows C Drive Cleaner" mkdir "%ProgramFiles%\Windows C Drive Cleaner"

REM Copy files
xcopy /Y /E "dist\Windows_C_Drive_Cleaner" "%ProgramFiles%\Windows C Drive Cleaner\"

REM Create desktop shortcut (optional)
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\Windows C Drive Cleaner.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%ProgramFiles%\Windows C Drive Cleaner\Windows_C_Drive_Cleaner.exe" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%ProgramFiles%\Windows C Drive Cleaner" >> CreateShortcut.vbs
echo oLink.Description = "Windows C Drive Cleaner" >> CreateShortcut.vbs
echo oLink.IconLocation = "%ProgramFiles%\Windows C Drive Cleaner\Windows_C_Drive_Cleaner.exe" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs
del CreateShortcut.vbs

echo Installation completed!
pause

@echo off
rem Open an activated Windows PowerShell session; arguments are PowerShell parameters.
powershell.exe -NoLogo -NoProfile -NoExit -File "%~dp0start-esp-idf.ps1" %*

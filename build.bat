@echo off
echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building VirtualCam.exe...
pyinstaller --onefile --windowed --name VirtualCam app.py

echo.
echo Done! Find VirtualCam.exe in the dist\ folder.
pause

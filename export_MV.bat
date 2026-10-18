@echo off
cd /d "%~dp0"
title GhostChain MV - Export MP4
echo Exporting 1080p60 MP4. Keep this window open until it finishes.
echo Output: output\CHAINEDGHOST_1080p60.mp4
where python >nul 2>nul
if errorlevel 1 goto trypy
python tools\export_mp4.py %*
goto end
:trypy
py tools\export_mp4.py %*
:end
echo.
echo Export finished or stopped. Press any key to close.
pause >nul

@echo off
cd /d "%~dp0"
title GhostChain MV
echo Starting GhostChain MV server... keep this window open while watching.
where python >nul 2>nul
if errorlevel 1 goto trypy
python tools\serve.py
goto end
:trypy
py tools\serve.py
:end
echo.
echo Server stopped or failed to start. Press any key to close.
pause >nul

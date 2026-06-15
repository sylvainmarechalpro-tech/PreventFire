@echo off
title PreventFire Pro
cd /d "%~dp0app"

:: Essayer python directement (fonctionne si Python est dans le PATH)
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo  Demarrage sur http://localhost:5174
    echo  Fermez cette fenetre pour arreter.
    echo.
    python server.py
    pause
    exit /b 0
)

:: Essayer les chemins Python connus
set PYEXE=
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set PYEXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
if exist "C:\Python312\python.exe" set PYEXE=C:\Python312\python.exe
if exist "C:\Python311\python.exe" set PYEXE=C:\Python311\python.exe

if "%PYEXE%"=="" (
    echo.
    echo  Python introuvable. Lancez install.bat
    echo.
    pause
    exit /b 1
)

echo  Python: %PYEXE%
echo  Demarrage sur http://localhost:5174
echo.
"%PYEXE%" server.py
pause

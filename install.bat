@echo off
title PreventFire Pro - Installation
echo.
echo  PreventFire Pro - Installation
echo  ================================
echo.

:: Trouver Python
set PYEXE=
python --version >nul 2>&1
if %errorlevel% == 0 set PYEXE=python

if "%PYEXE%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if "%PYEXE%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
if "%PYEXE%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set PYEXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe

if "%PYEXE%"=="" (
    echo  Python non trouve.
    echo  Installez Python depuis https://www.python.org/downloads/
    echo  COCHEZ "Add Python to PATH" pendant l'installation !
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

echo  Python trouve : %PYEXE%
echo.
echo  Installation de flask, anthropic, defusedxml, lxml...

"%PYEXE%" -m pip install flask anthropic defusedxml lxml pymupdf -q --no-warn-script-location

if %errorlevel% neq 0 (
    echo.
    echo  [ERREUR] Installation echouee.
    pause
    exit /b 1
)

echo.
echo  [OK] Installation terminee !
echo.

:: Creer dossier projets
if not exist "%~dp0projets" mkdir "%~dp0projets"

:: Ouvrir config.json
findstr "VOTRE_CLE" "%~dp0config.json" >nul 2>&1
if %errorlevel% == 0 (
    echo  Ajoutez votre cle API dans config.json
    echo  Obtenez-la sur https://console.anthropic.com
    echo.
    notepad "%~dp0config.json"
)

echo  Lancez maintenant preventfire.bat
echo.
pause

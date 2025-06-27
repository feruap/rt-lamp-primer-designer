
@echo off
echo RT-LAMP Primer Designer - Windows Build Script
echo =============================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/windows/
    pause
    exit /b 1
)

REM Create and activate virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM Build executable
echo Building executable...
pyinstaller RT_LAMP_Designer.spec

REM Check if build was successful
if exist "dist\RT_LAMP_Designer_Folder\RT_LAMP_Designer.exe" (
    echo.
    echo =============================================
    echo BUILD SUCCESSFUL!
    echo Executable location: dist\RT_LAMP_Designer_Folder\RT_LAMP_Designer.exe
    echo =============================================
    echo.
) else (
    echo.
    echo =============================================
    echo BUILD FAILED!
    echo Please check the error messages above.
    echo =============================================
    echo.
)

pause

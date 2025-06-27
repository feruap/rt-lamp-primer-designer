
# Windows Build Instructions for RT-LAMP Primer Designer

This document provides comprehensive instructions for building the RT-LAMP Primer Designer application on Windows systems.

## Prerequisites

### System Requirements
- Windows 10 or Windows 11 (64-bit)
- At least 4GB RAM
- 2GB free disk space
- Internet connection for downloading dependencies

### Required Software
1. **Python 3.8 or higher** (recommended: Python 3.9-3.11)
   - Download from: https://www.python.org/downloads/windows/
   - **IMPORTANT**: Check "Add Python to PATH" during installation

2. **Git for Windows**
   - Download from: https://git-scm.com/download/win
   - Use default installation options

3. **Microsoft Visual C++ Redistributable**
   - Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - Required for some Python packages

## Option 1: Build from GitHub Repository (Recommended)

### Step 1: Clone the Repository
```cmd
git clone https://github.com/YOUR_USERNAME/rt-lamp-primer-designer.git
cd rt-lamp-primer-designer
```

### Step 2: Set Up Python Environment
```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 3: Install Dependencies
```cmd
# Install required packages
pip install -r requirements.txt

# Install PyInstaller for building executable
pip install pyinstaller
```

### Step 4: Build the Executable
```cmd
# Build using the provided spec file
pyinstaller RT_LAMP_Designer.spec

# Alternative: Build with command line options
pyinstaller --onefile --windowed --name "RT-LAMP Designer" --icon=src/gui/icon.ico main_launcher.py
```

### Step 5: Locate the Executable
The built executable will be located in:
```
dist\RT-LAMP Designer.exe
```

## Option 2: Build from Release Package

### Step 1: Download Release Package
1. Download `RT_LAMP_Release_v1.0.0.tar.gz` from the GitHub releases
2. Extract to a folder (e.g., `C:\RT-LAMP-Designer`)

### Step 2: Set Up Environment
```cmd
cd C:\RT-LAMP-Designer
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
```

### Step 3: Install and Build
```cmd
pip install -r requirements.txt
pip install pyinstaller
pyinstaller RT_LAMP_Designer.spec
```

## Automated Build Script

Create a batch file `build_windows.bat` with the following content:

```batch
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
if exist "dist\RT-LAMP Designer.exe" (
    echo.
    echo =============================================
    echo BUILD SUCCESSFUL!
    echo Executable location: dist\RT-LAMP Designer.exe
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
```

## Troubleshooting

### Common Issues and Solutions

1. **"Python is not recognized as an internal or external command"**
   - Solution: Reinstall Python and ensure "Add Python to PATH" is checked
   - Alternative: Add Python manually to system PATH

2. **"Microsoft Visual C++ 14.0 is required"**
   - Solution: Install Microsoft Visual C++ Redistributable
   - Download: https://aka.ms/vs/17/release/vc_redist.x64.exe

3. **PyInstaller fails with import errors**
   - Solution: Install missing packages individually
   ```cmd
   pip install tkinter
   pip install pillow
   pip install biopython
   ```

4. **Executable crashes on startup**
   - Solution: Run from command line to see error messages
   ```cmd
   cd dist
   "RT-LAMP Designer.exe"
   ```

5. **Antivirus software blocks the executable**
   - Solution: Add exception for the dist folder in your antivirus software
   - This is common with PyInstaller-built executables

### Performance Optimization

For faster builds and smaller executables:

```cmd
# Use UPX compression (optional)
pip install upx-ucl
pyinstaller --upx-dir=upx RT_LAMP_Designer.spec

# Exclude unnecessary modules
pyinstaller --exclude-module matplotlib --exclude-module scipy RT_LAMP_Designer.spec
```

## Testing the Build

After building, test the executable:

1. Navigate to the `dist` folder
2. Double-click `RT-LAMP Designer.exe`
3. Verify the GUI opens correctly
4. Test basic functionality:
   - Load a sample sequence
   - Run primer design
   - Export results

## Distribution

To distribute the application:

1. Copy the entire `dist` folder contents
2. Include any required data files
3. Provide this build documentation
4. Consider creating an installer using tools like:
   - Inno Setup: https://jrsoftware.org/isinfo.php
   - NSIS: https://nsis.sourceforge.io/

## Support

For build issues:
1. Check the GitHub Issues page
2. Ensure all prerequisites are installed
3. Try building in a clean virtual environment
4. Check Windows Event Viewer for detailed error messages

## Version Information

- Application Version: 1.0.0
- Python Version: 3.8+
- PyInstaller Version: 5.0+
- Last Updated: June 2025

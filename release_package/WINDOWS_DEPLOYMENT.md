# Windows Deployment Guide for RT-LAMP Application

## Cross-Platform Deployment Notes

The executables in this package were built on Linux and are primarily intended for Linux systems. For Windows deployment, you have several options:

## Option 1: Rebuild on Windows (Recommended)

### Prerequisites
1. **Windows 10/11** (64-bit)
2. **Python 3.11+** installed from python.org
3. **Git** (optional, for source code management)

### Steps
1. **Install Python Dependencies**:
   ```cmd
   pip install PySide6 numpy pandas biopython openpyxl pyinstaller
   ```

2. **Copy Source Code**:
   - Copy the entire `src/` directory to your Windows machine
   - Copy `main_launcher.py` and `RT_LAMP_Designer.spec`

3. **Modify Spec File for Windows**:
   Edit `RT_LAMP_Designer.spec` and add Windows-specific options:
   ```python
   # Add to the EXE section:
   icon='app_icon.ico',  # if you have an icon file
   ```

4. **Build Windows Executable**:
   ```cmd
   pyinstaller RT_LAMP_Designer.spec
   ```

5. **Test the Executable**:
   ```cmd
   dist\RT_LAMP_Designer_Folder\RT_LAMP_Designer.exe
   ```

## Option 2: Using Wine (Linux Executable on Windows)

### Prerequisites
1. **Wine** installed on Windows (via WSL or native Wine builds)
2. **Xvfb** for headless operation

### Steps
1. Install Wine and configure it
2. Install Python and dependencies in Wine environment
3. Run the Linux executable through Wine:
   ```bash
   wine ./RT_LAMP_Designer
   ```

**Note**: This method may have compatibility issues and is not recommended for production use.

## Option 3: Windows Subsystem for Linux (WSL)

### Prerequisites
1. **WSL2** installed on Windows
2. **Ubuntu** or similar Linux distribution in WSL

### Steps
1. Copy the Linux executable to your WSL environment
2. Install required libraries in WSL:
   ```bash
   sudo apt-get update
   sudo apt-get install libxcb-cursor0 python3-tk
   ```
3. Run with X11 forwarding:
   ```bash
   export DISPLAY=:0
   ./RT_LAMP_Designer
   ```

## Recommended Windows Build Script

Create a `build_windows.bat` file:

```batch
@echo off
echo Building RT-LAMP Application for Windows...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install PySide6 numpy pandas biopython openpyxl pyinstaller

REM Build the application
echo Building executable...
pyinstaller RT_LAMP_Designer.spec

REM Check if build was successful
if exist "dist\RT_LAMP_Designer_Folder\RT_LAMP_Designer.exe" (
    echo Build successful! Executable created at: dist\RT_LAMP_Designer_Folder\RT_LAMP_Designer.exe
) else (
    echo Build failed!
    exit /b 1
)

pause
```

## Windows-Specific Considerations

### System Requirements
- **Windows 10/11** (64-bit recommended)
- **4GB RAM** minimum, 8GB recommended
- **500MB** free disk space for installation
- **Visual C++ Redistributable** (usually included with Windows)

### Antivirus Software
Some antivirus software may flag PyInstaller executables as suspicious. To resolve:
1. Add the executable to your antivirus whitelist
2. Scan the executable with multiple antivirus engines
3. Consider code signing for distribution

### File Associations
To associate `.fasta` files with the RT-LAMP application:
1. Right-click on a `.fasta` file
2. Select "Open with" → "Choose another app"
3. Browse to the RT-LAMP executable
4. Check "Always use this app"

## Distribution Package for Windows

When distributing to Windows users, include:

```
RT_LAMP_Windows_Package/
├── RT_LAMP_Designer.exe          # Main executable
├── _internal/                    # Dependencies folder
├── test_data/                    # Sample data
│   └── sars2_n.fasta
├── README_WINDOWS.txt            # Windows-specific instructions
├── INSTALL.bat                   # Installation script
└── UNINSTALL.bat                # Uninstallation script
```

### Sample INSTALL.bat
```batch
@echo off
echo Installing RT-LAMP Primer Designer...

REM Create desktop shortcut
set "desktop=%USERPROFILE%\Desktop"
set "target=%~dp0RT_LAMP_Designer.exe"
set "shortcut=%desktop%\RT-LAMP Primer Designer.lnk"

powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%shortcut%'); $Shortcut.TargetPath = '%target%'; $Shortcut.Save()"

echo Installation complete!
echo Desktop shortcut created: RT-LAMP Primer Designer
pause
```

## Troubleshooting Windows Issues

### Common Problems

1. **Missing DLL errors**:
   - Install Visual C++ Redistributable
   - Use the folder version instead of single-file

2. **Slow startup**:
   - Add executable to antivirus exclusions
   - Run from SSD instead of HDD

3. **GUI scaling issues**:
   - Right-click executable → Properties → Compatibility
   - Check "Override high DPI scaling behavior"

4. **File permission errors**:
   - Run as administrator
   - Check Windows Defender settings

## Performance Optimization

For better Windows performance:
1. **Use folder version** instead of single-file executable
2. **Add to antivirus exclusions** to prevent scanning delays
3. **Run from local drive** rather than network drives
4. **Close unnecessary applications** to free up memory

---

**Note**: For the most reliable Windows experience, rebuilding the application on a Windows system using the provided source code is strongly recommended.

# RT-LAMP Primer Design Application - Installation Guide

## Package Overview

This release package contains the complete RT-LAMP Primer Design Application compiled as standalone executables for easy deployment and distribution.

## Package Structure

```
RT_LAMP_Release_Package/
├── RT_LAMP_Designer                    # Single-file executable (Linux)
├── RT_LAMP_Designer_Folder/            # Directory-based executable
│   ├── RT_LAMP_Designer                # Main executable
│   ├── _internal/                      # Dependencies and libraries
│   ├── data/                          # Application data
│   └── logs/                          # Log files
├── src/                               # Source code (for rebuilding)
├── test_data/                         # Sample FASTA files
├── README.md                          # Main documentation
├── README_DEPLOYMENT.md               # Deployment instructions
├── WINDOWS_DEPLOYMENT.md              # Windows-specific guide
├── USAGE_EXAMPLES.md                  # Usage examples and tutorials
├── LICENSE                            # License information
├── requirements.txt                   # Python dependencies
└── pyproject.toml                     # Project configuration
```

## Quick Installation

### Linux Systems (Recommended)

#### Option 1: Single-File Executable
```bash
# 1. Extract the package
tar -xzf rt_lamp_release.tar.gz  # or unzip rt_lamp_release.zip
cd RT_LAMP_Release_Package

# 2. Make executable
chmod +x RT_LAMP_Designer

# 3. Run the application
./RT_LAMP_Designer
```

#### Option 2: Folder-Based Executable
```bash
# 1. Navigate to folder version
cd RT_LAMP_Designer_Folder

# 2. Make executable
chmod +x RT_LAMP_Designer

# 3. Run the application
./RT_LAMP_Designer
```

### Windows Systems

For Windows deployment, see `WINDOWS_DEPLOYMENT.md` for detailed instructions including:
- Rebuilding on Windows (recommended)
- Using Wine compatibility layer
- WSL deployment options

## System Requirements

### Minimum Requirements
- **OS**: Linux 64-bit (Ubuntu 18.04+, CentOS 7+, or equivalent)
- **RAM**: 4 GB
- **Storage**: 500 MB free space
- **Display**: 1024x768 resolution

### Recommended Requirements
- **OS**: Linux 64-bit (Ubuntu 20.04+)
- **RAM**: 8 GB or more
- **Storage**: 1 GB free space
- **Display**: 1920x1080 resolution
- **CPU**: Multi-core processor for better performance

### Dependencies
The executables are self-contained and include all necessary dependencies. However, for GUI functionality, you may need:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install libxcb-cursor0 libgl1-mesa-glx

# CentOS/RHEL/Fedora
sudo yum install libxcb-cursor
# or
sudo dnf install libxcb-cursor
```

## Installation Methods

### Method 1: Direct Execution (No Installation)
The application can be run directly without installation:

```bash
# Download and extract
wget [download_url] -O rt_lamp_release.tar.gz
tar -xzf rt_lamp_release.tar.gz
cd RT_LAMP_Release_Package

# Run immediately
chmod +x RT_LAMP_Designer
./RT_LAMP_Designer
```

### Method 2: System Installation
For system-wide installation:

```bash
# 1. Create application directory
sudo mkdir -p /opt/rt-lamp

# 2. Copy files
sudo cp -r RT_LAMP_Designer_Folder/* /opt/rt-lamp/

# 3. Create system link
sudo ln -s /opt/rt-lamp/RT_LAMP_Designer /usr/local/bin/rt-lamp-designer

# 4. Create desktop entry (optional)
cat > ~/.local/share/applications/rt-lamp-designer.desktop << EOF
[Desktop Entry]
Name=RT-LAMP Primer Designer
Comment=Design RT-LAMP primers for molecular diagnostics
Exec=/opt/rt-lamp/RT_LAMP_Designer
Icon=/opt/rt-lamp/icon.png
Terminal=false
Type=Application
Categories=Science;Biology;
EOF
```

### Method 3: User Installation
For single-user installation:

```bash
# 1. Create user application directory
mkdir -p ~/.local/bin/rt-lamp

# 2. Copy files
cp -r RT_LAMP_Designer_Folder/* ~/.local/bin/rt-lamp/

# 3. Add to PATH (add to ~/.bashrc)
echo 'export PATH="$HOME/.local/bin/rt-lamp:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 4. Run from anywhere
RT_LAMP_Designer
```

## Verification

### Test Installation
```bash
# Test basic functionality
./RT_LAMP_Designer --version  # if version flag is supported

# Test with sample data
./RT_LAMP_Designer test_data/sars2_n.fasta  # if CLI mode is supported

# Test GUI (will open application window)
./RT_LAMP_Designer
```

### Verify Dependencies
```bash
# Check executable type
file RT_LAMP_Designer

# Check dependencies (for folder version)
ldd RT_LAMP_Designer_Folder/RT_LAMP_Designer

# Test headless mode
QT_QPA_PLATFORM=offscreen ./RT_LAMP_Designer
```

## Troubleshooting Installation

### Common Issues

#### 1. Permission Denied
```bash
# Problem: Cannot execute file
# Solution: Make file executable
chmod +x RT_LAMP_Designer
```

#### 2. Library Not Found
```bash
# Problem: Missing system libraries
# Solution: Install required packages
sudo apt-get install libxcb-cursor0 libgl1-mesa-glx
```

#### 3. Display Issues
```bash
# Problem: Cannot connect to display
# Solution: Use offscreen mode or check X11 forwarding
export QT_QPA_PLATFORM=offscreen
./RT_LAMP_Designer
```

#### 4. Slow Startup
```bash
# Problem: Application takes long to start
# Possible causes: Antivirus scanning, slow storage
# Solutions:
# - Add to antivirus exclusions
# - Run from SSD instead of network drive
# - Use folder version instead of single-file
```

### Advanced Troubleshooting

#### Debug Mode
```bash
# Run with debug output
QT_LOGGING_RULES="*=true" ./RT_LAMP_Designer

# Check application logs
tail -f RT_LAMP_Designer_Folder/logs/application.log
```

#### Environment Variables
```bash
# Set Qt platform explicitly
export QT_QPA_PLATFORM=xcb  # for X11
export QT_QPA_PLATFORM=wayland  # for Wayland
export QT_QPA_PLATFORM=offscreen  # for headless

# Set Qt scaling
export QT_SCALE_FACTOR=1.0
export QT_AUTO_SCREEN_SCALE_FACTOR=1
```

## Uninstallation

### Remove User Installation
```bash
# Remove application files
rm -rf ~/.local/bin/rt-lamp

# Remove from PATH (edit ~/.bashrc)
# Remove the line: export PATH="$HOME/.local/bin/rt-lamp:$PATH"

# Remove desktop entry
rm ~/.local/share/applications/rt-lamp-designer.desktop
```

### Remove System Installation
```bash
# Remove application files
sudo rm -rf /opt/rt-lamp

# Remove system link
sudo rm /usr/local/bin/rt-lamp-designer

# Remove desktop entry
sudo rm /usr/share/applications/rt-lamp-designer.desktop
```

## Building from Source

If you need to rebuild the application or modify it:

### Prerequisites
```bash
# Install Python and dependencies
sudo apt-get install python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv rt_lamp_env
source rt_lamp_env/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller
```

### Build Process
```bash
# Navigate to source directory
cd src/

# Build executable
pyinstaller ../RT_LAMP_Designer.spec

# Test build
./dist/RT_LAMP_Designer_Folder/RT_LAMP_Designer
```

## Support and Documentation

- **Main Documentation**: `README.md`
- **Usage Examples**: `USAGE_EXAMPLES.md`
- **Windows Deployment**: `WINDOWS_DEPLOYMENT.md`
- **Source Code**: Available in `src/` directory
- **Sample Data**: Available in `test_data/` directory

## Version Information

- **Application Version**: 1.0.0
- **Build Date**: June 27, 2025
- **Python Version**: 3.11.6
- **PyInstaller Version**: 6.14.1
- **Platform**: Linux x86_64

---

For additional support or custom builds, refer to the source code documentation or contact the development team.

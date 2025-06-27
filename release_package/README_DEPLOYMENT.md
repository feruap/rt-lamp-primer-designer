# RT-LAMP Primer Design Application - Deployment Guide

## Overview
This package contains the RT-LAMP Primer Design Application compiled as standalone executables for easy deployment and distribution.

## Package Contents

### Executables
- **RT_LAMP_Designer** - Single-file executable (~113 MB)
- **RT_LAMP_Designer_Folder/** - Directory-based executable with dependencies

### Data Files
- **test_data/** - Sample SARS-CoV-2 sequence files for testing
- **src/** - Application source code (included for reference)

## System Requirements

### Linux Systems
- **Operating System**: Linux (64-bit)
- **Architecture**: x86_64
- **Dependencies**: 
  - Qt6 platform libraries (for GUI)
  - X11 or Wayland display server
  - libxcb-cursor0 (recommended for full GUI support)

### Windows Systems
- **Note**: This build was created on Linux. For Windows deployment:
  - Use Wine compatibility layer, or
  - Rebuild on Windows system using the included source code

## Installation & Usage

### Quick Start (Linux)
1. Extract the package to your desired location
2. Make the executable file executable:
   ```bash
   chmod +x RT_LAMP_Designer
   ```
3. Run the application:
   ```bash
   ./RT_LAMP_Designer
   ```

### Alternative: Folder Version
If the single-file version has issues, use the folder version:
```bash
cd RT_LAMP_Designer_Folder
./RT_LAMP_Designer
```

### Headless/Server Environment
For systems without GUI support, run with offscreen platform:
```bash
QT_QPA_PLATFORM=offscreen ./RT_LAMP_Designer
```

## Troubleshooting

### Common Issues

#### 1. Qt Platform Plugin Error
**Error**: "Could not load the Qt platform plugin 'xcb'"
**Solution**: 
- Install libxcb-cursor0: `sudo apt-get install libxcb-cursor0`
- Or use offscreen mode: `QT_QPA_PLATFORM=offscreen ./RT_LAMP_Designer`

#### 2. Permission Denied
**Error**: "Permission denied"
**Solution**: Make executable: `chmod +x RT_LAMP_Designer`

#### 3. Missing Libraries
**Error**: Various library not found errors
**Solution**: Use the folder version which includes all dependencies

### GUI Issues
The application includes a comprehensive GUI for primer design. If you encounter GUI-related errors:
1. Try the folder version instead of single-file
2. Use offscreen platform for headless environments
3. Ensure X11 forwarding is enabled for remote connections

## Application Features

### Core Functionality
- **Sequence Processing**: Load and analyze target sequences
- **Primer Design**: Design LAMP primers with thermodynamic validation
- **Specificity Checking**: Validate primer specificity
- **Results Export**: Export results in multiple formats

### Advanced Features
- **Multiple Sequence Alignment**: Consensus sequence analysis
- **Batch Processing**: Process multiple sequences
- **Visualization**: Graphical results display

## Sample Data
The package includes sample SARS-CoV-2 sequence data in the `test_data/` directory:
- `sars2_n.fasta` - SARS-CoV-2 nucleocapsid gene sequence

## Technical Details

### Build Information
- **PyInstaller Version**: 6.14.1
- **Python Version**: 3.11.6
- **PySide6 Version**: 6.9.1
- **Platform**: Linux x86_64
- **Build Date**: June 27, 2025

### Dependencies Included
- PySide6 (Qt6 Python bindings)
- NumPy (numerical computing)
- Pandas (data analysis)
- Biopython (bioinformatics tools)
- OpenPyXL (Excel file support)

## Support & Development

### Source Code
The complete source code is included in the `src/` directory and can be used to:
- Rebuild the application for other platforms
- Modify functionality
- Debug issues

### Building from Source
To rebuild the application:
1. Install Python 3.11+ and required dependencies
2. Navigate to the source directory
3. Install dependencies: `pip install -r requirements.txt`
4. Run PyInstaller: `pyinstaller RT_LAMP_Designer.spec`

### Known Limitations
- Built on Linux for Linux systems
- Windows compatibility requires Wine or native rebuild
- Some GUI features may not work in headless environments
- Large file size due to included Qt libraries

## License
This application is distributed under the terms specified in the LICENSE file.

## Version Information
- **Application Version**: 1.0.0
- **Build Version**: 2025.06.27
- **Executable Type**: PyInstaller standalone

---

For technical support or questions, refer to the source code documentation or rebuild from the included source files.

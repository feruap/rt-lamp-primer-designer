#!/usr/bin/env python3
"""
RT-LAMP Primer Design Application Launcher
Main entry point for the executable version.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))

def main():
    """Main launcher function."""
    try:
        # Import and run the GUI application
        from rt_lamp_app.gui.app import main as gui_main
        return gui_main()
    except ImportError as e:
        print(f"Error importing RT-LAMP application: {e}")
        print("Please ensure all dependencies are installed.")
        return 1
    except Exception as e:
        print(f"Error starting RT-LAMP application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

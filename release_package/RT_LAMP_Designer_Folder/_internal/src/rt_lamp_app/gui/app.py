
"""
RT-LAMP GUI Application Entry Point

Main application class that initializes and runs the GUI.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QIcon

from rt_lamp_app.config import setup_logging
from rt_lamp_app.logger import get_logger
from .main_window import MainWindow


class RTLampApp(QApplication):
    """Main RT-LAMP GUI Application class."""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # Setup logging
        setup_logging()
        self.logger = get_logger(__name__)
        
        # Application properties
        self.setApplicationName("RT-LAMP Primer Designer")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("RT-LAMP Team")
        self.setOrganizationDomain("rtlamp.dev")
        
        # Set application icon if available
        icon_path = Path(__file__).parent / "resources" / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Enable high DPI scaling
        self.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        self.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Create main window
        self.main_window = MainWindow()
        
        self.logger.info("RT-LAMP GUI Application initialized")
    
    def run(self):
        """Run the application."""
        self.main_window.show()
        self.logger.info("RT-LAMP GUI Application started")
        return self.exec()


def main():
    """Entry point for the GUI application."""
    app = RTLampApp(sys.argv)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())

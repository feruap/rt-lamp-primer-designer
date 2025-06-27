#!/usr/bin/env python3
"""
Test script for RT-LAMP GUI application.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_gui_imports():
    """Test that all GUI components can be imported."""
    print("Testing GUI imports...")
    
    try:
        from rt_lamp_app.gui.app import RTLampApp, main
        print("✓ Main app imports successful")
        
        from rt_lamp_app.gui.main_window import MainWindow
        print("✓ Main window imports successful")
        
        from rt_lamp_app.gui.sequence_input import SequenceInputWidget
        print("✓ Sequence input widget imports successful")
        
        from rt_lamp_app.gui.parameter_panel import ParameterPanel
        print("✓ Parameter panel imports successful")
        
        from rt_lamp_app.gui.results_display import ResultsDisplay
        print("✓ Results display imports successful")
        
        from rt_lamp_app.gui.dialogs import AboutDialog, SettingsDialog, ExportDialog
        print("✓ Dialog imports successful")
        
        from rt_lamp_app.gui.widgets import StatusWidget, ProgressWidget
        print("✓ Custom widgets imports successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_creation():
    """Test that GUI components can be created."""
    print("\nTesting GUI component creation...")
    
    try:
        # Test without actually showing the GUI
        from PySide6.QtWidgets import QApplication
        from rt_lamp_app.gui.main_window import MainWindow
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create main window
        window = MainWindow()
        print("✓ Main window created successfully")
        
        # Test basic functionality
        print(f"✓ Window title: {window.windowTitle()}")
        print(f"✓ Window size: {window.size().width()}x{window.size().height()}")
        
        # Clean up
        window.close()
        
        return True
        
    except Exception as e:
        print(f"✗ GUI creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backend_integration():
    """Test that GUI can integrate with backend modules."""
    print("\nTesting backend integration...")
    
    try:
        from rt_lamp_app.core.sequence_processing import Sequence
        from rt_lamp_app.design.primer_design import PrimerDesigner
        
        # Create test sequence
        test_sequence = Sequence("Test", "ATCGATCGATCG" * 20)
        print(f"✓ Test sequence created: {len(test_sequence.sequence)} bp")
        
        # Create designer
        designer = PrimerDesigner()
        print("✓ Primer designer created")
        
        # Test parameter extraction (simulate GUI parameter panel)
        test_params = {
            'max_sets': 3,
            'include_loop_primers': True,
            'check_specificity': False,  # Disable for quick test
            'tm_min': 58.0,
            'tm_max': 65.0,
        }
        print("✓ Test parameters created")
        
        return True
        
    except Exception as e:
        print(f"✗ Backend integration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all GUI tests."""
    print("RT-LAMP GUI Test Suite")
    print("=" * 50)
    
    success = True
    
    # Test imports
    if not test_gui_imports():
        success = False
    
    # Test GUI creation
    if not test_gui_creation():
        success = False
    
    # Test backend integration
    if not test_backend_integration():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All GUI tests passed!")
        print("✓ GUI is ready for use")
        print("\nTo launch the GUI application:")
        print("  python -m rt_lamp_app.gui.app")
        print("  or")
        print("  rt-lamp-gui  (after installation)")
    else:
        print("✗ Some tests failed")
        print("✗ GUI may not work correctly")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

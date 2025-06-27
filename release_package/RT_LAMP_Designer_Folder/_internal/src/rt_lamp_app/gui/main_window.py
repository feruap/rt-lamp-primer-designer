
"""
RT-LAMP Main Window

Main application window containing all GUI components and coordinating
the primer design workflow.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QStatusBar, QProgressBar, QLabel, QMessageBox,
    QFileDialog, QTabWidget, QTextEdit, QApplication
)
from PySide6.QtCore import Qt, QThread, QTimer, Signal, QSettings
from PySide6.QtGui import QAction, QKeySequence, QFont

from rt_lamp_app.core.sequence_processing import Sequence
from rt_lamp_app.design.primer_design import PrimerDesigner
from rt_lamp_app.design.specificity_checker import SpecificityChecker
from rt_lamp_app.logger import get_logger

from .sequence_input import SequenceInputWidget
from .parameter_panel import ParameterPanel
from .results_display import ResultsDisplay
from .dialogs import AboutDialog, SettingsDialog, ExportDialog
from .widgets import StatusWidget


class PrimerDesignWorker(QThread):
    """Worker thread for primer design to avoid blocking the GUI."""
    
    progress_updated = Signal(int, str)  # progress percentage, status message
    design_completed = Signal(object)    # primer sets result
    design_failed = Signal(str)          # error message
    
    def __init__(self, target_sequence, parameters):
        super().__init__()
        self.target_sequence = target_sequence
        self.parameters = parameters
        self.logger = get_logger(__name__)
    
    def run(self):
        """Run primer design in background thread."""
        try:
            self.progress_updated.emit(10, "Initializing primer designer...")
            designer = PrimerDesigner()
            
            self.progress_updated.emit(30, "Analyzing target sequence...")
            # Validate sequence
            if len(self.target_sequence.sequence) < 200:
                raise ValueError("Target sequence too short for RT-LAMP design (minimum 200 bp)")
            
            self.progress_updated.emit(50, "Designing primer sets...")
            # Design primers with parameters
            primer_sets = designer.design_primer_set(
                self.target_sequence,
                max_sets=self.parameters.get('max_sets', 5),
                include_loop_primers=self.parameters.get('include_loop_primers', True)
            )
            
            self.progress_updated.emit(80, "Checking specificity...")
            # Check specificity if enabled
            if self.parameters.get('check_specificity', True):
                checker = SpecificityChecker()
                for primer_set in primer_sets:
                    specificity_result = checker.check_primer_set_specificity(primer_set)
                    primer_set.specificity_score = specificity_result.overall_score
            
            self.progress_updated.emit(100, "Design completed successfully!")
            self.design_completed.emit(primer_sets)
            
        except Exception as e:
            self.logger.error(f"Primer design failed: {e}")
            self.design_failed.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window for RT-LAMP primer design."""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        
        # Application state
        self.current_sequence: Optional[Sequence] = None
        self.current_results: Optional[List] = None
        self.design_worker: Optional[PrimerDesignWorker] = None
        
        # Settings
        self.settings = QSettings()
        
        self.setup_ui()
        self.setup_menus()
        self.setup_status_bar()
        self.connect_signals()
        self.restore_settings()
        
        self.logger.info("Main window initialized")
    
    def setup_ui(self):
        """Setup the main user interface."""
        self.setWindowTitle("RT-LAMP Primer Designer")
        self.setMinimumSize(1200, 800)
        
        # Central widget with splitter layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left panel for input and parameters
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Sequence input widget
        self.sequence_input = SequenceInputWidget()
        left_layout.addWidget(self.sequence_input)
        
        # Parameter panel
        self.parameter_panel = ParameterPanel()
        left_layout.addWidget(self.parameter_panel)
        
        # Design button and controls
        self.setup_design_controls(left_layout)
        
        # Right panel for results
        self.results_display = ResultsDisplay()
        
        # Add panels to splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(self.results_display)
        main_splitter.setSizes([400, 800])  # Give more space to results
    
    def setup_design_controls(self, layout):
        """Setup primer design control buttons."""
        from PySide6.QtWidgets import QPushButton, QHBoxLayout
        
        controls_layout = QHBoxLayout()
        
        self.design_button = QPushButton("Design Primers")
        self.design_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.design_button.clicked.connect(self.start_primer_design)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_primer_design)
        
        controls_layout.addWidget(self.design_button)
        controls_layout.addWidget(self.cancel_button)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
    
    def setup_menus(self):
        """Setup application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Open sequence file
        open_action = QAction("&Open Sequence...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_sequence_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Export results
        export_action = QAction("&Export Results...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_results)
        export_action.setEnabled(False)
        self.export_action = export_action
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Settings
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut(QKeySequence.Preferences)
        settings_action.triggered.connect(self.show_settings)
        edit_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Setup status bar with progress indicator."""
        self.status_bar = self.statusBar()
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Status widget for additional info
        self.status_widget = StatusWidget()
        self.status_bar.addPermanentWidget(self.status_widget)
    
    def connect_signals(self):
        """Connect widget signals to handlers."""
        # Sequence input signals
        self.sequence_input.sequence_changed.connect(self.on_sequence_changed)
        self.sequence_input.sequence_loaded.connect(self.on_sequence_loaded)
        
        # Parameter panel signals
        self.parameter_panel.parameters_changed.connect(self.on_parameters_changed)
        
        # Results display signals
        self.results_display.export_requested.connect(self.export_results)
    
    def restore_settings(self):
        """Restore application settings."""
        # Window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Window state
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
        
        # Parameter settings
        self.parameter_panel.restore_settings(self.settings)
    
    def save_settings(self):
        """Save application settings."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.parameter_panel.save_settings(self.settings)
    
    def on_sequence_changed(self, sequence_text):
        """Handle sequence text changes."""
        try:
            if sequence_text.strip():
                # Create sequence object
                self.current_sequence = Sequence("User Input", sequence_text.strip())
                self.status_label.setText(f"Sequence loaded: {len(self.current_sequence.sequence)} bp")
                self.design_button.setEnabled(True)
            else:
                self.current_sequence = None
                self.status_label.setText("Ready")
                self.design_button.setEnabled(False)
        except Exception as e:
            self.status_label.setText(f"Invalid sequence: {str(e)}")
            self.design_button.setEnabled(False)
    
    def on_sequence_loaded(self, sequence):
        """Handle sequence loaded from file."""
        self.current_sequence = sequence
        self.status_label.setText(f"Sequence loaded: {len(sequence.sequence)} bp")
        self.design_button.setEnabled(True)
    
    def on_parameters_changed(self):
        """Handle parameter changes."""
        # Could trigger re-validation or preview updates
        pass
    
    def open_sequence_file(self):
        """Open sequence file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Sequence File",
            "",
            "FASTA files (*.fasta *.fa *.fas);;Text files (*.txt);;All files (*.*)"
        )
        
        if file_path:
            self.sequence_input.load_file(file_path)
    
    def start_primer_design(self):
        """Start primer design process."""
        if not self.current_sequence:
            QMessageBox.warning(self, "Warning", "Please load a target sequence first.")
            return
        
        # Get parameters
        parameters = self.parameter_panel.get_parameters()
        
        # Setup UI for design process
        self.design_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Clear previous results
        self.results_display.clear_results()
        
        # Start worker thread
        self.design_worker = PrimerDesignWorker(self.current_sequence, parameters)
        self.design_worker.progress_updated.connect(self.on_design_progress)
        self.design_worker.design_completed.connect(self.on_design_completed)
        self.design_worker.design_failed.connect(self.on_design_failed)
        self.design_worker.start()
        
        self.logger.info("Started primer design process")
    
    def cancel_primer_design(self):
        """Cancel ongoing primer design."""
        if self.design_worker and self.design_worker.isRunning():
            self.design_worker.terminate()
            self.design_worker.wait()
        
        self.reset_design_ui()
        self.status_label.setText("Design cancelled")
        self.logger.info("Primer design cancelled")
    
    def on_design_progress(self, percentage, message):
        """Handle design progress updates."""
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)
    
    def on_design_completed(self, primer_sets):
        """Handle successful primer design completion."""
        self.current_results = primer_sets
        self.results_display.display_results(primer_sets)
        
        self.reset_design_ui()
        self.export_action.setEnabled(True)
        
        self.status_label.setText(f"Design completed: {len(primer_sets)} primer sets found")
        self.logger.info(f"Primer design completed successfully: {len(primer_sets)} sets")
        
        # Show success message
        QMessageBox.information(
            self,
            "Success",
            f"Primer design completed successfully!\n\n"
            f"Found {len(primer_sets)} primer sets.\n"
            f"Results are displayed in the Results panel."
        )
    
    def on_design_failed(self, error_message):
        """Handle primer design failure."""
        self.reset_design_ui()
        self.status_label.setText("Design failed")
        
        QMessageBox.critical(
            self,
            "Design Failed",
            f"Primer design failed:\n\n{error_message}"
        )
        
        self.logger.error(f"Primer design failed: {error_message}")
    
    def reset_design_ui(self):
        """Reset UI after design completion or cancellation."""
        self.design_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.design_worker = None
    
    def export_results(self):
        """Export primer design results."""
        if not self.current_results:
            QMessageBox.warning(self, "Warning", "No results to export.")
            return
        
        dialog = ExportDialog(self.current_results, self)
        dialog.exec()
    
    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Apply settings changes
            self.parameter_panel.apply_settings(dialog.get_settings())
    
    def show_about(self):
        """Show about dialog."""
        dialog = AboutDialog(self)
        dialog.exec()
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Cancel any running design
        if self.design_worker and self.design_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Primer design is in progress. Do you want to cancel and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.design_worker.terminate()
                self.design_worker.wait()
            else:
                event.ignore()
                return
        
        # Save settings
        self.save_settings()
        
        self.logger.info("Application closing")
        event.accept()

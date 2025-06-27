
"""
Sequence Input Widget

Widget for entering and loading target sequences for primer design.
"""

import os
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QFileDialog, QMessageBox, QGroupBox, QLineEdit, QCheckBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent

from rt_lamp_app.core.sequence_processing import Sequence, validate_sequence_quality
from rt_lamp_app.logger import get_logger


class SequenceInputWidget(QWidget):
    """Widget for sequence input and file loading."""
    
    sequence_changed = Signal(str)  # Emitted when sequence text changes
    sequence_loaded = Signal(object)  # Emitted when sequence is loaded from file
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.current_sequence: Optional[Sequence] = None
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Sequence input group
        input_group = QGroupBox("Target Sequence")
        input_layout = QVBoxLayout(input_group)
        
        # Sequence name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Sequence Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter sequence name (optional)")
        name_layout.addWidget(self.name_input)
        input_layout.addLayout(name_layout)
        
        # File loading controls
        file_layout = QHBoxLayout()
        self.load_button = QPushButton("Load from File...")
        self.load_button.clicked.connect(self.load_file_dialog)
        file_layout.addWidget(self.load_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_sequence)
        file_layout.addWidget(self.clear_button)
        
        file_layout.addStretch()
        input_layout.addLayout(file_layout)
        
        # Sequence text area
        self.sequence_text = QTextEdit()
        self.sequence_text.setPlaceholderText(
            "Enter target sequence here (FASTA format or plain sequence)...\n\n"
            "You can also drag and drop a FASTA file here."
        )
        self.sequence_text.setMinimumHeight(200)
        self.sequence_text.setFont(QFont("Courier", 10))
        self.sequence_text.setAcceptDrops(True)
        input_layout.addWidget(self.sequence_text)
        
        # Sequence info
        self.info_label = QLabel("No sequence loaded")
        self.info_label.setStyleSheet("color: #666; font-style: italic;")
        input_layout.addWidget(self.info_label)
        
        # Validation options
        validation_layout = QHBoxLayout()
        self.auto_validate = QCheckBox("Auto-validate sequence")
        self.auto_validate.setChecked(True)
        validation_layout.addWidget(self.auto_validate)
        validation_layout.addStretch()
        input_layout.addLayout(validation_layout)
        
        layout.addWidget(input_group)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
    
    def connect_signals(self):
        """Connect widget signals."""
        self.sequence_text.textChanged.connect(self.on_text_changed)
        self.name_input.textChanged.connect(self.on_name_changed)
    
    def on_text_changed(self):
        """Handle sequence text changes."""
        text = self.sequence_text.toPlainText().strip()
        
        if text:
            try:
                # Parse sequence (handle FASTA format)
                sequence_data = self.parse_sequence_input(text)
                
                if sequence_data:
                    name, sequence = sequence_data
                    
                    # Update name field if it was parsed from FASTA
                    if name and not self.name_input.text():
                        self.name_input.setText(name)
                    
                    # Validate if enabled
                    if self.auto_validate.isChecked():
                        self.validate_sequence(sequence)
                    
                    # Update info
                    self.update_sequence_info(sequence)
                    
                    # Emit signal
                    self.sequence_changed.emit(sequence)
                else:
                    self.info_label.setText("Invalid sequence format")
            except Exception as e:
                self.info_label.setText(f"Error: {str(e)}")
        else:
            self.info_label.setText("No sequence loaded")
            self.sequence_changed.emit("")
    
    def on_name_changed(self):
        """Handle sequence name changes."""
        # Update current sequence name if we have one
        if self.current_sequence:
            self.current_sequence.name = self.name_input.text() or "User Input"
    
    def parse_sequence_input(self, text):
        """Parse sequence input (FASTA or plain text)."""
        lines = text.strip().split('\n')
        
        if lines[0].startswith('>'):
            # FASTA format
            name = lines[0][1:].strip()
            sequence = ''.join(line.strip() for line in lines[1:] if not line.startswith('>'))
            return name, sequence
        else:
            # Plain sequence
            sequence = ''.join(line.strip() for line in lines)
            return None, sequence
    
    def validate_sequence(self, sequence):
        """Validate sequence quality."""
        try:
            # Create temporary sequence object for validation
            temp_seq = Sequence("temp", sequence)
            quality_issues = validate_sequence_quality(temp_seq)
            
            if quality_issues:
                self.info_label.setText(f"Validation warnings: {', '.join(quality_issues)}")
                self.info_label.setStyleSheet("color: #ff6600; font-style: italic;")
            else:
                self.info_label.setStyleSheet("color: #666; font-style: italic;")
        except Exception as e:
            self.info_label.setText(f"Validation error: {str(e)}")
            self.info_label.setStyleSheet("color: #cc0000; font-style: italic;")
    
    def update_sequence_info(self, sequence):
        """Update sequence information display."""
        if sequence:
            length = len(sequence)
            gc_content = sequence.count('G') + sequence.count('C')
            gc_percent = (gc_content / length * 100) if length > 0 else 0
            
            info_text = f"Length: {length} bp, GC: {gc_percent:.1f}%"
            
            if length < 200:
                info_text += " (Warning: Too short for RT-LAMP)"
                self.info_label.setStyleSheet("color: #cc0000; font-style: italic;")
            elif length > 5000:
                info_text += " (Warning: Very long sequence)"
                self.info_label.setStyleSheet("color: #ff6600; font-style: italic;")
            else:
                self.info_label.setStyleSheet("color: #666; font-style: italic;")
            
            self.info_label.setText(info_text)
    
    def load_file_dialog(self):
        """Open file dialog to load sequence."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Sequence File",
            "",
            "FASTA files (*.fasta *.fa *.fas);;Text files (*.txt);;All files (*.*)"
        )
        
        if file_path:
            self.load_file(file_path)
    
    def load_file(self, file_path):
        """Load sequence from file."""
        try:
            file_path = Path(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the file content
            sequence_data = self.parse_sequence_input(content)
            
            if sequence_data:
                name, sequence = sequence_data
                
                # Use filename as name if not provided in FASTA
                if not name:
                    name = file_path.stem
                
                # Create sequence object
                self.current_sequence = Sequence(name, sequence)
                
                # Update UI
                self.name_input.setText(name)
                self.sequence_text.setPlainText(content)
                
                # Emit signal
                self.sequence_loaded.emit(self.current_sequence)
                
                self.logger.info(f"Loaded sequence from {file_path}: {len(sequence)} bp")
            else:
                raise ValueError("Could not parse sequence from file")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "File Load Error",
                f"Failed to load sequence from file:\n\n{str(e)}"
            )
            self.logger.error(f"Failed to load sequence from {file_path}: {e}")
    
    def clear_sequence(self):
        """Clear the sequence input."""
        self.sequence_text.clear()
        self.name_input.clear()
        self.current_sequence = None
        self.info_label.setText("No sequence loaded")
        self.info_label.setStyleSheet("color: #666; font-style: italic;")
    
    def get_sequence(self) -> Optional[Sequence]:
        """Get the current sequence object."""
        return self.current_sequence
    
    def set_sequence(self, sequence: Sequence):
        """Set the sequence programmatically."""
        self.current_sequence = sequence
        self.name_input.setText(sequence.name)
        self.sequence_text.setPlainText(sequence.sequence)
    
    # Drag and drop support
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path:
                self.load_file(file_path)

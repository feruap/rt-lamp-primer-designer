
"""
Custom Widgets

Custom widget components for the RT-LAMP GUI application.
"""

from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QFrame, QTextEdit, QScrollArea, QGroupBox, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPalette, QPainter, QLinearGradient

from rt_lamp_app.logger import get_logger


class StatusWidget(QWidget):
    """Status widget for displaying application status information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        
        self.setup_ui()
        self.update_status()
    
    def setup_ui(self):
        """Setup the status widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: green; font-size: 12px;")
        layout.addWidget(self.status_indicator)
        
        # Status text
        self.status_text = QLabel("Ready")
        self.status_text.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(self.status_text)
        
        # Memory usage (optional)
        self.memory_label = QLabel("")
        self.memory_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(self.memory_label)
        
        # Timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def update_status(self):
        """Update status information."""
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            self.memory_label.setText(f"Memory: {memory_percent:.1f}%")
            
            if memory_percent > 80:
                self.memory_label.setStyleSheet("font-size: 10px; color: red;")
            elif memory_percent > 60:
                self.memory_label.setStyleSheet("font-size: 10px; color: orange;")
            else:
                self.memory_label.setStyleSheet("font-size: 10px; color: #666;")
        except ImportError:
            # psutil not available
            self.memory_label.setText("")
    
    def set_status(self, status: str, color: str = "green"):
        """Set status text and indicator color."""
        self.status_text.setText(status)
        self.status_indicator.setStyleSheet(f"color: {color}; font-size: 12px;")


class ProgressWidget(QWidget):
    """Enhanced progress widget with status and cancellation."""
    
    cancelled = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the progress widget UI."""
        layout = QVBoxLayout(self)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # Status and cancel layout
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 11px; color: #666;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMaximumWidth(80)
        self.cancel_button.clicked.connect(self.cancelled.emit)
        self.cancel_button.setVisible(False)
        status_layout.addWidget(self.cancel_button)
        
        layout.addLayout(status_layout)
    
    def start_progress(self, message: str = "Processing..."):
        """Start progress indication."""
        self.progress_bar.setValue(0)
        self.status_label.setText(message)
        self.cancel_button.setVisible(True)
        self.setVisible(True)
    
    def update_progress(self, percentage: int, message: str = ""):
        """Update progress."""
        self.progress_bar.setValue(percentage)
        if message:
            self.status_label.setText(message)
    
    def finish_progress(self, message: str = "Completed"):
        """Finish progress indication."""
        self.progress_bar.setValue(100)
        self.status_label.setText(message)
        self.cancel_button.setVisible(False)
        
        # Hide after a short delay
        QTimer.singleShot(2000, lambda: self.setVisible(False))


class CollapsibleGroupBox(QGroupBox):
    """Collapsible group box widget."""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(True)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.content_widget)
        
        self.toggled.connect(self.on_toggled)
    
    def on_toggled(self, checked: bool):
        """Handle toggle state changes."""
        self.content_widget.setVisible(checked)
    
    def add_widget(self, widget: QWidget):
        """Add widget to the collapsible content."""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add layout to the collapsible content."""
        self.content_layout.addLayout(layout)


class InfoPanel(QFrame):
    """Information panel widget for displaying tips and help."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.set_default_content()
    
    def setup_ui(self):
        """Setup the info panel UI."""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f8ff;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Title
        self.title_label = QLabel("Information")
        self.title_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.title_label.setStyleSheet("color: #333; margin-bottom: 5px;")
        layout.addWidget(self.title_label)
        
        # Content
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setMaximumHeight(150)
        self.content_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                font-size: 10px;
                color: #555;
            }
        """)
        layout.addWidget(self.content_text)
    
    def set_default_content(self):
        """Set default information content."""
        self.set_content(
            "Quick Start",
            """
1. Load your target sequence using the 'Load from File' button or paste it directly
2. Adjust primer design parameters if needed
3. Click 'Design Primers' to start the analysis
4. Review results in the Results panel
5. Export your primer sets for laboratory use

Tips:
• Sequences should be at least 200 bp for RT-LAMP design
• Check the warnings for potential issues
• Higher scores indicate better primer sets
            """
        )
    
    def set_content(self, title: str, content: str):
        """Set panel content."""
        self.title_label.setText(title)
        self.content_text.setPlainText(content.strip())


class ParameterHelpWidget(QWidget):
    """Widget for displaying parameter help and tooltips."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.help_data = self.load_help_data()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the help widget UI."""
        layout = QVBoxLayout(self)
        
        # Search/filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search parameters...")
        self.search_input.textChanged.connect(self.filter_help)
        layout.addWidget(self.search_input)
        
        # Help content
        self.help_text = QTextEdit()
        self.help_text.setReadOnly(True)
        layout.addWidget(self.help_text)
        
        self.update_help_display()
    
    def load_help_data(self) -> Dict[str, str]:
        """Load parameter help data."""
        return {
            "F3/B3 Length": "Length constraints for outer primers. Typical range: 18-22 bp",
            "FIP/BIP Length": "Length constraints for inner primers. Typical range: 40-60 bp",
            "GC Content": "Percentage of G and C nucleotides. Optimal range: 40-65%",
            "Melting Temperature": "Temperature at which primer dissociates. Target: 58-65°C",
            "Tm Uniformity": "Difference between primer Tm values. Keep below 5°C",
            "Geometric Constraints": "Spacing requirements between primer binding sites",
            "Specificity Checking": "Verify primers don't bind to unintended targets",
            "Loop Primers": "Optional primers to accelerate amplification",
            "Salt Concentration": "Affects Tm calculations. Standard: 50mM Na+, 8mM Mg2+",
            "Secondary Structure": "Check for hairpins and primer dimers",
        }
    
    def filter_help(self, search_text: str):
        """Filter help content based on search text."""
        self.update_help_display(search_text.lower())
    
    def update_help_display(self, filter_text: str = ""):
        """Update help display with optional filtering."""
        content = "Parameter Help\n" + "=" * 50 + "\n\n"
        
        for param, description in self.help_data.items():
            if not filter_text or filter_text in param.lower() or filter_text in description.lower():
                content += f"{param}:\n{description}\n\n"
        
        self.help_text.setPlainText(content)


class AnimatedButton(QPushButton):
    """Button with hover animations."""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setup_animation()
    
    def setup_animation(self):
        """Setup button animations."""
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)


class LoadingSpinner(QWidget):
    """Simple loading spinner widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        
        self.setFixedSize(32, 32)
    
    def start(self):
        """Start the spinner animation."""
        self.timer.start(50)  # 20 FPS
        self.show()
    
    def stop(self):
        """Stop the spinner animation."""
        self.timer.stop()
        self.hide()
    
    def rotate(self):
        """Rotate the spinner."""
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """Paint the spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(100, 150, 255, 255))
        gradient.setColorAt(1, QColor(100, 150, 255, 50))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        
        # Draw spinning arc
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        
        for i in range(8):
            painter.drawEllipse(-2, -10, 4, 8)
            painter.rotate(45)

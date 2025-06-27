
"""
Parameter Panel Widget

Widget for configuring RT-LAMP primer design parameters.
"""

from typing import Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QGroupBox, QSlider, QLineEdit, QPushButton,
    QTabWidget, QFormLayout, QScrollArea
)
from PySide6.QtCore import Signal, Qt, QSettings
from PySide6.QtGui import QFont

from rt_lamp_app.logger import get_logger


class ParameterPanel(QWidget):
    """Widget for RT-LAMP primer design parameters."""
    
    parameters_changed = Signal()  # Emitted when parameters change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        
        self.setup_ui()
        self.connect_signals()
        self.set_default_values()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Create scrollable area for parameters
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Parameter tabs
        self.tab_widget = QTabWidget()
        
        # Basic parameters tab
        self.setup_basic_tab()
        
        # Advanced parameters tab
        self.setup_advanced_tab()
        
        # Thermodynamic parameters tab
        self.setup_thermodynamic_tab()
        
        # Specificity parameters tab
        self.setup_specificity_tab()
        
        scroll_layout.addWidget(self.tab_widget)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Reset and preset buttons
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Default", "High Sensitivity", "High Specificity", 
            "Fast Design", "Comprehensive"
        ])
        self.preset_combo.currentTextChanged.connect(self.apply_preset)
        button_layout.addWidget(QLabel("Preset:"))
        button_layout.addWidget(self.preset_combo)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def setup_basic_tab(self):
        """Setup basic parameters tab."""
        basic_tab = QWidget()
        layout = QVBoxLayout(basic_tab)
        
        # Primer length constraints
        length_group = QGroupBox("Primer Length Constraints")
        length_layout = QFormLayout(length_group)
        
        self.f3_b3_min_length = QSpinBox()
        self.f3_b3_min_length.setRange(15, 30)
        self.f3_b3_min_length.setSuffix(" bp")
        length_layout.addRow("F3/B3 Min Length:", self.f3_b3_min_length)
        
        self.f3_b3_max_length = QSpinBox()
        self.f3_b3_max_length.setRange(18, 35)
        self.f3_b3_max_length.setSuffix(" bp")
        length_layout.addRow("F3/B3 Max Length:", self.f3_b3_max_length)
        
        self.fip_bip_min_length = QSpinBox()
        self.fip_bip_min_length.setRange(35, 50)
        self.fip_bip_min_length.setSuffix(" bp")
        length_layout.addRow("FIP/BIP Min Length:", self.fip_bip_min_length)
        
        self.fip_bip_max_length = QSpinBox()
        self.fip_bip_max_length.setRange(40, 65)
        self.fip_bip_max_length.setSuffix(" bp")
        length_layout.addRow("FIP/BIP Max Length:", self.fip_bip_max_length)
        
        layout.addWidget(length_group)
        
        # GC content constraints
        gc_group = QGroupBox("GC Content Constraints")
        gc_layout = QFormLayout(gc_group)
        
        self.gc_min = QDoubleSpinBox()
        self.gc_min.setRange(20.0, 80.0)
        self.gc_min.setSuffix("%")
        self.gc_min.setDecimals(1)
        gc_layout.addRow("Minimum GC:", self.gc_min)
        
        self.gc_max = QDoubleSpinBox()
        self.gc_max.setRange(20.0, 80.0)
        self.gc_max.setSuffix("%")
        self.gc_max.setDecimals(1)
        gc_layout.addRow("Maximum GC:", self.gc_max)
        
        layout.addWidget(gc_group)
        
        # Design options
        options_group = QGroupBox("Design Options")
        options_layout = QVBoxLayout(options_group)
        
        self.include_loop_primers = QCheckBox("Include Loop Primers (LF/LB)")
        options_layout.addWidget(self.include_loop_primers)
        
        self.check_specificity = QCheckBox("Check Primer Specificity")
        options_layout.addWidget(self.check_specificity)
        
        self.optimize_tm_uniformity = QCheckBox("Optimize Tm Uniformity")
        options_layout.addWidget(self.optimize_tm_uniformity)
        
        layout.addWidget(options_group)
        
        # Number of results
        results_group = QGroupBox("Results")
        results_layout = QFormLayout(results_group)
        
        self.max_primer_sets = QSpinBox()
        self.max_primer_sets.setRange(1, 20)
        results_layout.addRow("Max Primer Sets:", self.max_primer_sets)
        
        layout.addWidget(results_group)
        
        layout.addStretch()
        self.tab_widget.addTab(basic_tab, "Basic")
    
    def setup_advanced_tab(self):
        """Setup advanced parameters tab."""
        advanced_tab = QWidget()
        layout = QVBoxLayout(advanced_tab)
        
        # Geometric constraints
        geometry_group = QGroupBox("Geometric Constraints")
        geometry_layout = QFormLayout(geometry_group)
        
        self.f3_f2_distance_min = QSpinBox()
        self.f3_f2_distance_min.setRange(0, 100)
        self.f3_f2_distance_min.setSuffix(" bp")
        geometry_layout.addRow("F3-F2 Min Distance:", self.f3_f2_distance_min)
        
        self.f3_f2_distance_max = QSpinBox()
        self.f3_f2_distance_max.setRange(20, 200)
        self.f3_f2_distance_max.setSuffix(" bp")
        geometry_layout.addRow("F3-F2 Max Distance:", self.f3_f2_distance_max)
        
        self.b3_b2_distance_min = QSpinBox()
        self.b3_b2_distance_min.setRange(0, 100)
        self.b3_b2_distance_min.setSuffix(" bp")
        geometry_layout.addRow("B3-B2 Min Distance:", self.b3_b2_distance_min)
        
        self.b3_b2_distance_max = QSpinBox()
        self.b3_b2_distance_max.setRange(20, 200)
        self.b3_b2_distance_max.setSuffix(" bp")
        geometry_layout.addRow("B3-B2 Max Distance:", self.b3_b2_distance_max)
        
        self.amplicon_size_min = QSpinBox()
        self.amplicon_size_min.setRange(100, 300)
        self.amplicon_size_min.setSuffix(" bp")
        geometry_layout.addRow("Min Amplicon Size:", self.amplicon_size_min)
        
        self.amplicon_size_max = QSpinBox()
        self.amplicon_size_max.setRange(150, 500)
        self.amplicon_size_max.setSuffix(" bp")
        geometry_layout.addRow("Max Amplicon Size:", self.amplicon_size_max)
        
        layout.addWidget(geometry_group)
        
        # Primer composition
        composition_group = QGroupBox("Primer Composition")
        composition_layout = QVBoxLayout(composition_group)
        
        self.avoid_runs = QCheckBox("Avoid Homopolymer Runs")
        composition_layout.addWidget(self.avoid_runs)
        
        run_layout = QHBoxLayout()
        run_layout.addWidget(QLabel("Max Run Length:"))
        self.max_run_length = QSpinBox()
        self.max_run_length.setRange(3, 8)
        run_layout.addWidget(self.max_run_length)
        run_layout.addStretch()
        composition_layout.addLayout(run_layout)
        
        self.avoid_3prime_gc = QCheckBox("Avoid 3' GC Clamp")
        composition_layout.addWidget(self.avoid_3prime_gc)
        
        layout.addWidget(composition_group)
        
        layout.addStretch()
        self.tab_widget.addTab(advanced_tab, "Advanced")
    
    def setup_thermodynamic_tab(self):
        """Setup thermodynamic parameters tab."""
        thermo_tab = QWidget()
        layout = QVBoxLayout(thermo_tab)
        
        # Melting temperature
        tm_group = QGroupBox("Melting Temperature")
        tm_layout = QFormLayout(tm_group)
        
        self.tm_min = QDoubleSpinBox()
        self.tm_min.setRange(50.0, 80.0)
        self.tm_min.setSuffix("°C")
        self.tm_min.setDecimals(1)
        tm_layout.addRow("Minimum Tm:", self.tm_min)
        
        self.tm_max = QDoubleSpinBox()
        self.tm_max.setRange(60.0, 90.0)
        self.tm_max.setSuffix("°C")
        self.tm_max.setDecimals(1)
        tm_layout.addRow("Maximum Tm:", self.tm_max)
        
        self.tm_difference_max = QDoubleSpinBox()
        self.tm_difference_max.setRange(1.0, 10.0)
        self.tm_difference_max.setSuffix("°C")
        self.tm_difference_max.setDecimals(1)
        tm_layout.addRow("Max Tm Difference:", self.tm_difference_max)
        
        layout.addWidget(tm_group)
        
        # Salt conditions
        salt_group = QGroupBox("Salt Conditions")
        salt_layout = QFormLayout(salt_group)
        
        self.na_concentration = QDoubleSpinBox()
        self.na_concentration.setRange(0.01, 1.0)
        self.na_concentration.setSuffix(" M")
        self.na_concentration.setDecimals(3)
        salt_layout.addRow("Na+ Concentration:", self.na_concentration)
        
        self.mg_concentration = QDoubleSpinBox()
        self.mg_concentration.setRange(0.001, 0.1)
        self.mg_concentration.setSuffix(" M")
        self.mg_concentration.setDecimals(4)
        salt_layout.addRow("Mg2+ Concentration:", self.mg_concentration)
        
        layout.addWidget(salt_group)
        
        # Secondary structure
        structure_group = QGroupBox("Secondary Structure")
        structure_layout = QVBoxLayout(structure_group)
        
        self.check_hairpins = QCheckBox("Check for Hairpins")
        structure_layout.addWidget(self.check_hairpins)
        
        hairpin_layout = QHBoxLayout()
        hairpin_layout.addWidget(QLabel("Max Hairpin ΔG:"))
        self.max_hairpin_dg = QDoubleSpinBox()
        self.max_hairpin_dg.setRange(-20.0, 0.0)
        self.max_hairpin_dg.setSuffix(" kcal/mol")
        self.max_hairpin_dg.setDecimals(1)
        hairpin_layout.addWidget(self.max_hairpin_dg)
        hairpin_layout.addStretch()
        structure_layout.addLayout(hairpin_layout)
        
        self.check_dimers = QCheckBox("Check for Primer Dimers")
        structure_layout.addWidget(self.check_dimers)
        
        layout.addWidget(structure_group)
        
        layout.addStretch()
        self.tab_widget.addTab(thermo_tab, "Thermodynamic")
    
    def setup_specificity_tab(self):
        """Setup specificity parameters tab."""
        specificity_tab = QWidget()
        layout = QVBoxLayout(specificity_tab)
        
        # BLAST parameters
        blast_group = QGroupBox("BLAST Parameters")
        blast_layout = QFormLayout(blast_group)
        
        self.blast_database = QLineEdit()
        self.blast_database.setPlaceholderText("Path to BLAST database")
        blast_layout.addRow("BLAST Database:", self.blast_database)
        
        self.blast_evalue = QDoubleSpinBox()
        self.blast_evalue.setRange(1e-10, 1.0)
        self.blast_evalue.setDecimals(2)
        self.blast_evalue.setValue(0.01)
        blast_layout.addRow("E-value Threshold:", self.blast_evalue)
        
        self.min_identity = QDoubleSpinBox()
        self.min_identity.setRange(70.0, 100.0)
        self.min_identity.setSuffix("%")
        self.min_identity.setDecimals(1)
        blast_layout.addRow("Min Identity:", self.min_identity)
        
        layout.addWidget(blast_group)
        
        # Cross-reactivity
        cross_group = QGroupBox("Cross-reactivity")
        cross_layout = QVBoxLayout(cross_group)
        
        self.check_cross_reactivity = QCheckBox("Check Cross-reactivity")
        cross_layout.addWidget(self.check_cross_reactivity)
        
        self.exclude_target = QCheckBox("Exclude Target Organism")
        cross_layout.addWidget(self.exclude_target)
        
        layout.addWidget(cross_group)
        
        layout.addStretch()
        self.tab_widget.addTab(specificity_tab, "Specificity")
    
    def connect_signals(self):
        """Connect parameter change signals."""
        # Connect all parameter widgets to the change signal
        for widget in self.findChildren((QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox)):
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.valueChanged.connect(self.parameters_changed.emit)
            elif isinstance(widget, QCheckBox):
                widget.toggled.connect(self.parameters_changed.emit)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(self.parameters_changed.emit)
    
    def set_default_values(self):
        """Set default parameter values."""
        # Basic parameters
        self.f3_b3_min_length.setValue(18)
        self.f3_b3_max_length.setValue(22)
        self.fip_bip_min_length.setValue(40)
        self.fip_bip_max_length.setValue(60)
        
        self.gc_min.setValue(40.0)
        self.gc_max.setValue(65.0)
        
        self.include_loop_primers.setChecked(True)
        self.check_specificity.setChecked(True)
        self.optimize_tm_uniformity.setChecked(True)
        
        self.max_primer_sets.setValue(5)
        
        # Advanced parameters
        self.f3_f2_distance_min.setValue(0)
        self.f3_f2_distance_max.setValue(60)
        self.b3_b2_distance_min.setValue(0)
        self.b3_b2_distance_max.setValue(60)
        self.amplicon_size_min.setValue(120)
        self.amplicon_size_max.setValue(300)
        
        self.avoid_runs.setChecked(True)
        self.max_run_length.setValue(4)
        self.avoid_3prime_gc.setChecked(False)
        
        # Thermodynamic parameters
        self.tm_min.setValue(58.0)
        self.tm_max.setValue(65.0)
        self.tm_difference_max.setValue(5.0)
        
        self.na_concentration.setValue(0.05)
        self.mg_concentration.setValue(0.008)
        
        self.check_hairpins.setChecked(True)
        self.max_hairpin_dg.setValue(-3.0)
        self.check_dimers.setChecked(True)
        
        # Specificity parameters
        self.min_identity.setValue(85.0)
        self.check_cross_reactivity.setChecked(True)
        self.exclude_target.setChecked(True)
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values as dictionary."""
        return {
            # Basic parameters
            'f3_b3_min_length': self.f3_b3_min_length.value(),
            'f3_b3_max_length': self.f3_b3_max_length.value(),
            'fip_bip_min_length': self.fip_bip_min_length.value(),
            'fip_bip_max_length': self.fip_bip_max_length.value(),
            'gc_min': self.gc_min.value(),
            'gc_max': self.gc_max.value(),
            'include_loop_primers': self.include_loop_primers.isChecked(),
            'check_specificity': self.check_specificity.isChecked(),
            'optimize_tm_uniformity': self.optimize_tm_uniformity.isChecked(),
            'max_sets': self.max_primer_sets.value(),
            
            # Advanced parameters
            'f3_f2_distance_min': self.f3_f2_distance_min.value(),
            'f3_f2_distance_max': self.f3_f2_distance_max.value(),
            'b3_b2_distance_min': self.b3_b2_distance_min.value(),
            'b3_b2_distance_max': self.b3_b2_distance_max.value(),
            'amplicon_size_min': self.amplicon_size_min.value(),
            'amplicon_size_max': self.amplicon_size_max.value(),
            'avoid_runs': self.avoid_runs.isChecked(),
            'max_run_length': self.max_run_length.value(),
            'avoid_3prime_gc': self.avoid_3prime_gc.isChecked(),
            
            # Thermodynamic parameters
            'tm_min': self.tm_min.value(),
            'tm_max': self.tm_max.value(),
            'tm_difference_max': self.tm_difference_max.value(),
            'na_concentration': self.na_concentration.value(),
            'mg_concentration': self.mg_concentration.value(),
            'check_hairpins': self.check_hairpins.isChecked(),
            'max_hairpin_dg': self.max_hairpin_dg.value(),
            'check_dimers': self.check_dimers.isChecked(),
            
            # Specificity parameters
            'blast_database': self.blast_database.text(),
            'blast_evalue': self.blast_evalue.value(),
            'min_identity': self.min_identity.value(),
            'check_cross_reactivity': self.check_cross_reactivity.isChecked(),
            'exclude_target': self.exclude_target.isChecked(),
        }
    
    def reset_to_defaults(self):
        """Reset all parameters to default values."""
        self.set_default_values()
        self.parameters_changed.emit()
    
    def apply_preset(self, preset_name):
        """Apply parameter preset."""
        if preset_name == "High Sensitivity":
            self.tm_min.setValue(55.0)
            self.tm_max.setValue(70.0)
            self.gc_min.setValue(35.0)
            self.gc_max.setValue(70.0)
            self.max_primer_sets.setValue(10)
        elif preset_name == "High Specificity":
            self.tm_min.setValue(60.0)
            self.tm_max.setValue(65.0)
            self.gc_min.setValue(45.0)
            self.gc_max.setValue(60.0)
            self.check_specificity.setChecked(True)
            self.check_cross_reactivity.setChecked(True)
        elif preset_name == "Fast Design":
            self.max_primer_sets.setValue(3)
            self.check_specificity.setChecked(False)
            self.include_loop_primers.setChecked(False)
        elif preset_name == "Comprehensive":
            self.max_primer_sets.setValue(15)
            self.include_loop_primers.setChecked(True)
            self.check_specificity.setChecked(True)
            self.optimize_tm_uniformity.setChecked(True)
        else:  # Default
            self.set_default_values()
        
        self.parameters_changed.emit()
    
    def save_settings(self, settings: QSettings):
        """Save parameters to settings."""
        parameters = self.get_parameters()
        for key, value in parameters.items():
            settings.setValue(f"parameters/{key}", value)
    
    def restore_settings(self, settings: QSettings):
        """Restore parameters from settings."""
        # This would restore saved parameter values
        # Implementation depends on specific requirements
        pass
    
    def apply_settings(self, settings_dict):
        """Apply settings from settings dialog."""
        # This would apply settings from the settings dialog
        # Implementation depends on specific requirements
        pass

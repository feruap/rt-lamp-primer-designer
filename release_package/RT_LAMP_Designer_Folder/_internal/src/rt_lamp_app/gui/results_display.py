
"""
Results Display Widget

Widget for displaying primer design results with tables, charts, and export options.
"""

import csv
from pathlib import Path
from typing import List, Optional, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QTextEdit, QLabel, QPushButton, QGroupBox, QHeaderView, QAbstractItemView,
    QSplitter, QTreeWidget, QTreeWidgetItem, QProgressBar, QComboBox,
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel, QAbstractTableModel
from PySide6.QtGui import QFont, QColor, QPalette

from rt_lamp_app.design.primer_design import LampPrimerSet, Primer, PrimerType
from rt_lamp_app.logger import get_logger


class PrimerSetTableModel(QAbstractTableModel):
    """Table model for primer sets."""
    
    def __init__(self, primer_sets: List[LampPrimerSet]):
        super().__init__()
        self.primer_sets = primer_sets
        self.headers = [
            "Set #", "Overall Score", "Tm Uniformity", "Specificity", 
            "F3 Tm", "B3 Tm", "FIP Tm", "BIP Tm", "Amplicon Size", "Warnings"
        ]
    
    def rowCount(self, parent=None):
        return len(self.primer_sets)
    
    def columnCount(self, parent=None):
        return len(self.headers)
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        primer_set = self.primer_sets[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0:  # Set #
                return index.row() + 1
            elif col == 1:  # Overall Score
                return f"{primer_set.overall_score:.2f}"
            elif col == 2:  # Tm Uniformity
                return f"{primer_set.tm_uniformity:.1f}°C"
            elif col == 3:  # Specificity
                return f"{primer_set.specificity_score:.2f}"
            elif col == 4:  # F3 Tm
                return f"{primer_set.f3.tm:.1f}°C"
            elif col == 5:  # B3 Tm
                return f"{primer_set.b3.tm:.1f}°C"
            elif col == 6:  # FIP Tm
                return f"{primer_set.fip.tm:.1f}°C"
            elif col == 7:  # BIP Tm
                return f"{primer_set.bip.tm:.1f}°C"
            elif col == 8:  # Amplicon Size
                return f"{primer_set.f2_b2_amplicon_size} bp"
            elif col == 9:  # Warnings
                return len(primer_set.warnings)
        
        elif role == Qt.BackgroundRole:
            # Color coding based on quality
            if col == 1:  # Overall Score
                score = primer_set.overall_score
                if score >= 0.8:
                    return QColor(200, 255, 200)  # Light green
                elif score >= 0.6:
                    return QColor(255, 255, 200)  # Light yellow
                else:
                    return QColor(255, 200, 200)  # Light red
        
        return None


class ResultsDisplay(QWidget):
    """Widget for displaying primer design results."""
    
    export_requested = Signal()  # Emitted when export is requested
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.current_results: Optional[List[LampPrimerSet]] = None
        self.selected_set: Optional[LampPrimerSet] = None
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Results header
        header_layout = QHBoxLayout()
        
        self.results_label = QLabel("No results to display")
        self.results_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(self.results_label)
        
        header_layout.addStretch()
        
        # Export button
        self.export_button = QPushButton("Export Results")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_requested.emit)
        header_layout.addWidget(self.export_button)
        
        layout.addLayout(header_layout)
        
        # Main results area with tabs
        self.tab_widget = QTabWidget()
        
        # Overview tab
        self.setup_overview_tab()
        
        # Detailed view tab
        self.setup_detailed_tab()
        
        # Analysis tab
        self.setup_analysis_tab()
        
        layout.addWidget(self.tab_widget)
    
    def setup_overview_tab(self):
        """Setup overview tab with primer sets table."""
        overview_tab = QWidget()
        layout = QVBoxLayout(overview_tab)
        
        # Primer sets table
        self.primer_sets_table = QTableWidget()
        self.primer_sets_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.primer_sets_table.setAlternatingRowColors(True)
        self.primer_sets_table.setSortingEnabled(True)
        layout.addWidget(self.primer_sets_table)
        
        # Selected set summary
        summary_group = QGroupBox("Selected Primer Set Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(150)
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        layout.addWidget(summary_group)
        
        self.tab_widget.addTab(overview_tab, "Overview")
    
    def setup_detailed_tab(self):
        """Setup detailed view tab."""
        detailed_tab = QWidget()
        layout = QVBoxLayout(detailed_tab)
        
        # Set selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Primer Set:"))
        
        self.set_selector = QComboBox()
        self.set_selector.currentIndexChanged.connect(self.on_set_selected)
        selector_layout.addWidget(self.set_selector)
        
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Splitter for primer details
        splitter = QSplitter(Qt.Vertical)
        
        # Individual primers table
        self.primers_table = QTableWidget()
        self.primers_table.setAlternatingRowColors(True)
        splitter.addWidget(self.primers_table)
        
        # Primer sequence details
        details_group = QGroupBox("Primer Details")
        details_layout = QVBoxLayout(details_group)
        
        self.primer_details = QTextEdit()
        self.primer_details.setReadOnly(True)
        self.primer_details.setFont(QFont("Courier", 10))
        details_layout.addWidget(self.primer_details)
        
        splitter.addWidget(details_group)
        
        layout.addWidget(splitter)
        
        self.tab_widget.addTab(detailed_tab, "Detailed View")
    
    def setup_analysis_tab(self):
        """Setup analysis tab with charts and statistics."""
        analysis_tab = QWidget()
        layout = QVBoxLayout(analysis_tab)
        
        # Statistics summary
        stats_group = QGroupBox("Design Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        stats_layout.addWidget(self.stats_text)
        
        layout.addWidget(stats_group)
        
        # Quality metrics
        quality_group = QGroupBox("Quality Metrics")
        quality_layout = QVBoxLayout(quality_group)
        
        self.quality_text = QTextEdit()
        self.quality_text.setReadOnly(True)
        quality_layout.addWidget(self.quality_text)
        
        layout.addWidget(quality_group)
        
        self.tab_widget.addTab(analysis_tab, "Analysis")
    
    def connect_signals(self):
        """Connect widget signals."""
        self.primer_sets_table.itemSelectionChanged.connect(self.on_table_selection_changed)
        self.primers_table.itemSelectionChanged.connect(self.on_primer_selection_changed)
    
    def display_results(self, primer_sets: List[LampPrimerSet]):
        """Display primer design results."""
        self.current_results = primer_sets
        self.logger.info(f"Displaying {len(primer_sets)} primer sets")
        
        # Update header
        self.results_label.setText(f"Primer Design Results ({len(primer_sets)} sets found)")
        self.export_button.setEnabled(True)
        
        # Update overview table
        self.update_overview_table()
        
        # Update set selector
        self.update_set_selector()
        
        # Update analysis
        self.update_analysis()
        
        # Select first set by default
        if primer_sets:
            self.primer_sets_table.selectRow(0)
            self.set_selector.setCurrentIndex(0)
    
    def update_overview_table(self):
        """Update the primer sets overview table."""
        if not self.current_results:
            return
        
        table = self.primer_sets_table
        table.setRowCount(len(self.current_results))
        table.setColumnCount(10)
        
        headers = [
            "Set #", "Overall Score", "Tm Uniformity", "Specificity", 
            "F3 Tm", "B3 Tm", "FIP Tm", "BIP Tm", "Amplicon Size", "Warnings"
        ]
        table.setHorizontalHeaderLabels(headers)
        
        for row, primer_set in enumerate(self.current_results):
            # Set #
            table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            
            # Overall Score
            score_item = QTableWidgetItem(f"{primer_set.overall_score:.3f}")
            if primer_set.overall_score >= 0.8:
                score_item.setBackground(QColor(200, 255, 200))
            elif primer_set.overall_score >= 0.6:
                score_item.setBackground(QColor(255, 255, 200))
            else:
                score_item.setBackground(QColor(255, 200, 200))
            table.setItem(row, 1, score_item)
            
            # Tm Uniformity
            table.setItem(row, 2, QTableWidgetItem(f"{primer_set.tm_uniformity:.1f}°C"))
            
            # Specificity
            table.setItem(row, 3, QTableWidgetItem(f"{primer_set.specificity_score:.3f}"))
            
            # Individual Tm values
            table.setItem(row, 4, QTableWidgetItem(f"{primer_set.f3.tm:.1f}°C"))
            table.setItem(row, 5, QTableWidgetItem(f"{primer_set.b3.tm:.1f}°C"))
            table.setItem(row, 6, QTableWidgetItem(f"{primer_set.fip.tm:.1f}°C"))
            table.setItem(row, 7, QTableWidgetItem(f"{primer_set.bip.tm:.1f}°C"))
            
            # Amplicon size
            table.setItem(row, 8, QTableWidgetItem(f"{primer_set.f2_b2_amplicon_size} bp"))
            
            # Warnings
            warnings_item = QTableWidgetItem(str(len(primer_set.warnings)))
            if len(primer_set.warnings) > 0:
                warnings_item.setBackground(QColor(255, 200, 200))
            table.setItem(row, 9, warnings_item)
        
        # Resize columns to content
        table.resizeColumnsToContents()
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
    
    def update_set_selector(self):
        """Update the set selector combo box."""
        self.set_selector.clear()
        if self.current_results:
            for i, primer_set in enumerate(self.current_results):
                self.set_selector.addItem(f"Set {i+1} (Score: {primer_set.overall_score:.3f})")
    
    def update_analysis(self):
        """Update analysis tab with statistics."""
        if not self.current_results:
            return
        
        # Calculate statistics
        scores = [ps.overall_score for ps in self.current_results]
        tm_uniformities = [ps.tm_uniformity for ps in self.current_results]
        amplicon_sizes = [ps.f2_b2_amplicon_size for ps in self.current_results]
        
        stats_text = f"""
Design Statistics:
==================

Total Primer Sets: {len(self.current_results)}

Overall Scores:
- Best: {max(scores):.3f}
- Average: {sum(scores)/len(scores):.3f}
- Worst: {min(scores):.3f}

Tm Uniformity:
- Best: {min(tm_uniformities):.1f}°C
- Average: {sum(tm_uniformities)/len(tm_uniformities):.1f}°C
- Worst: {max(tm_uniformities):.1f}°C

Amplicon Sizes:
- Smallest: {min(amplicon_sizes)} bp
- Average: {sum(amplicon_sizes)//len(amplicon_sizes)} bp
- Largest: {max(amplicon_sizes)} bp

Quality Distribution:
- Excellent (≥0.8): {sum(1 for s in scores if s >= 0.8)} sets
- Good (≥0.6): {sum(1 for s in scores if 0.6 <= s < 0.8)} sets
- Fair (<0.6): {sum(1 for s in scores if s < 0.6)} sets
"""
        
        self.stats_text.setPlainText(stats_text)
        
        # Quality metrics
        quality_text = f"""
Quality Assessment:
==================

The primer design analysis found {len(self.current_results)} viable primer sets.

Recommendations:
- Use primer sets with scores ≥ 0.8 for best performance
- Consider Tm uniformity for consistent amplification
- Verify specificity results before experimental use
- Check warnings for potential issues

Best Primer Set: Set {scores.index(max(scores)) + 1}
- Score: {max(scores):.3f}
- Tm Uniformity: {self.current_results[scores.index(max(scores))].tm_uniformity:.1f}°C
- Amplicon Size: {self.current_results[scores.index(max(scores))].f2_b2_amplicon_size} bp
"""
        
        self.quality_text.setPlainText(quality_text)
    
    def on_table_selection_changed(self):
        """Handle primer sets table selection changes."""
        current_row = self.primer_sets_table.currentRow()
        if current_row >= 0 and self.current_results:
            self.selected_set = self.current_results[current_row]
            self.update_summary()
            self.set_selector.setCurrentIndex(current_row)
    
    def on_set_selected(self, index):
        """Handle set selector changes."""
        if index >= 0 and self.current_results:
            self.selected_set = self.current_results[index]
            self.update_detailed_view()
            self.primer_sets_table.selectRow(index)
    
    def on_primer_selection_changed(self):
        """Handle individual primer selection changes."""
        current_row = self.primers_table.currentRow()
        if current_row >= 0 and self.selected_set:
            primers = self.selected_set.get_all_primers()
            if current_row < len(primers):
                primer = primers[current_row]
                self.update_primer_details(primer)
    
    def update_summary(self):
        """Update the selected primer set summary."""
        if not self.selected_set:
            self.summary_text.clear()
            return
        
        summary = f"""
Selected Primer Set Summary:
============================

Overall Score: {self.selected_set.overall_score:.3f}
Tm Uniformity: {self.selected_set.tm_uniformity:.1f}°C
Specificity Score: {self.selected_set.specificity_score:.3f}
Amplicon Size: {self.selected_set.f2_b2_amplicon_size} bp

Primer Details:
- F3: {self.selected_set.f3.sequence} (Tm: {self.selected_set.f3.tm:.1f}°C)
- B3: {self.selected_set.b3.sequence} (Tm: {self.selected_set.b3.tm:.1f}°C)
- FIP: {self.selected_set.fip.sequence[:30]}... (Tm: {self.selected_set.fip.tm:.1f}°C)
- BIP: {self.selected_set.bip.sequence[:30]}... (Tm: {self.selected_set.bip.tm:.1f}°C)

Warnings: {len(self.selected_set.warnings)}
"""
        
        if self.selected_set.warnings:
            summary += "\nWarnings:\n"
            for warning in self.selected_set.warnings:
                summary += f"- {warning}\n"
        
        self.summary_text.setPlainText(summary)
    
    def update_detailed_view(self):
        """Update the detailed view tab."""
        if not self.selected_set:
            return
        
        primers = self.selected_set.get_all_primers()
        
        # Update primers table
        table = self.primers_table
        table.setRowCount(len(primers))
        table.setColumnCount(8)
        
        headers = ["Type", "Sequence", "Length", "Tm (°C)", "GC (%)", "ΔG", "Position", "Strand"]
        table.setHorizontalHeaderLabels(headers)
        
        for row, primer in enumerate(primers):
            table.setItem(row, 0, QTableWidgetItem(primer.type.value))
            table.setItem(row, 1, QTableWidgetItem(primer.sequence))
            table.setItem(row, 2, QTableWidgetItem(str(len(primer.sequence))))
            table.setItem(row, 3, QTableWidgetItem(f"{primer.tm:.1f}"))
            table.setItem(row, 4, QTableWidgetItem(f"{primer.gc_content:.1f}"))
            table.setItem(row, 5, QTableWidgetItem(f"{primer.delta_g:.1f}"))
            table.setItem(row, 6, QTableWidgetItem(f"{primer.start_pos}-{primer.end_pos}"))
            table.setItem(row, 7, QTableWidgetItem(primer.strand))
        
        table.resizeColumnsToContents()
        
        # Select first primer
        if primers:
            table.selectRow(0)
    
    def update_primer_details(self, primer: Primer):
        """Update primer details display."""
        details = f"""
Primer Details: {primer.type.value}
===============================

Sequence: {primer.sequence}
Length: {len(primer.sequence)} bp
Position: {primer.start_pos}-{primer.end_pos} ({primer.strand} strand)

Thermodynamic Properties:
- Melting Temperature: {primer.tm:.1f}°C
- GC Content: {primer.gc_content:.1f}%
- Free Energy: {primer.delta_g:.1f} kcal/mol
- End Stability: {primer.end_stability:.1f} kcal/mol

Quality Metrics:
- Score: {primer.score:.3f}
- Hairpin ΔG: {primer.hairpin_dg:.1f} kcal/mol
- Dimer ΔG: {primer.dimer_dg:.1f} kcal/mol

"""
        
        if primer.type in [PrimerType.FIP, PrimerType.BIP]:
            details += f"""
Composite Primer Components:
"""
            if primer.f1c_sequence:
                details += f"- F1c: {primer.f1c_sequence}\n"
            if primer.f2_sequence:
                details += f"- F2: {primer.f2_sequence}\n"
            if primer.b1c_sequence:
                details += f"- B1c: {primer.b1c_sequence}\n"
            if primer.b2_sequence:
                details += f"- B2: {primer.b2_sequence}\n"
        
        if primer.warnings:
            details += f"\nWarnings:\n"
            for warning in primer.warnings:
                details += f"- {warning}\n"
        
        self.primer_details.setPlainText(details)
    
    def clear_results(self):
        """Clear all results displays."""
        self.current_results = None
        self.selected_set = None
        
        self.results_label.setText("No results to display")
        self.export_button.setEnabled(False)
        
        self.primer_sets_table.setRowCount(0)
        self.primers_table.setRowCount(0)
        self.set_selector.clear()
        
        self.summary_text.clear()
        self.primer_details.clear()
        self.stats_text.clear()
        self.quality_text.clear()
    
    def export_to_csv(self, file_path: str):
        """Export results to CSV file."""
        if not self.current_results:
            return
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                "Set", "Overall_Score", "Tm_Uniformity", "Specificity_Score",
                "F3_Sequence", "F3_Tm", "F3_GC", "F3_Position",
                "B3_Sequence", "B3_Tm", "B3_GC", "B3_Position",
                "FIP_Sequence", "FIP_Tm", "FIP_GC", "FIP_Position",
                "BIP_Sequence", "BIP_Tm", "BIP_GC", "BIP_Position",
                "Amplicon_Size", "Warnings"
            ])
            
            # Write data
            for i, primer_set in enumerate(self.current_results):
                writer.writerow([
                    i + 1,
                    f"{primer_set.overall_score:.3f}",
                    f"{primer_set.tm_uniformity:.1f}",
                    f"{primer_set.specificity_score:.3f}",
                    primer_set.f3.sequence,
                    f"{primer_set.f3.tm:.1f}",
                    f"{primer_set.f3.gc_content:.1f}",
                    f"{primer_set.f3.start_pos}-{primer_set.f3.end_pos}",
                    primer_set.b3.sequence,
                    f"{primer_set.b3.tm:.1f}",
                    f"{primer_set.b3.gc_content:.1f}",
                    f"{primer_set.b3.start_pos}-{primer_set.b3.end_pos}",
                    primer_set.fip.sequence,
                    f"{primer_set.fip.tm:.1f}",
                    f"{primer_set.fip.gc_content:.1f}",
                    f"{primer_set.fip.start_pos}-{primer_set.fip.end_pos}",
                    primer_set.bip.sequence,
                    f"{primer_set.bip.tm:.1f}",
                    f"{primer_set.bip.gc_content:.1f}",
                    f"{primer_set.bip.start_pos}-{primer_set.bip.end_pos}",
                    primer_set.f2_b2_amplicon_size,
                    "; ".join(primer_set.warnings)
                ])
        
        self.logger.info(f"Results exported to {file_path}")

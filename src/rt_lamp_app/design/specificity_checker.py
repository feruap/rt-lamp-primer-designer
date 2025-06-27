"""
Specificity Checker Module for RT-LAMP Primer Design

This module implements specificity checking including local sequence alignment,
off-target binding prediction, and primer specificity scoring. Supports both
basic specificity checking (Phase 1) and full BLAST-based analysis (Phase 1.5+).
"""

import re
import subprocess
import tempfile
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from rt_lamp_app.core.sequence_processing import Sequence
from rt_lamp_app.core.thermodynamics import ThermoCalculator
from rt_lamp_app.design.exceptions import SpecificityError
from rt_lamp_app.design.utils import reverse_complement
from rt_lamp_app.design.primer_design import Primer, LampPrimerSet
from rt_lamp_app.logger import LoggerMixin


class RiskLevel(Enum):
    """Risk levels for specificity hits."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class SpecificityHit:
    """Represents a specificity hit from alignment."""
    query_primer: str
    target_sequence: str
    target_id: str
    alignment_length: int
    identity_percent: float
    query_start: int
    query_end: int
    target_start: int
    target_end: int
    e_value: float = 1.0
    bit_score: float = 0.0
    predicted_tm: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    is_human_genome: bool = False
    three_prime_match: int = 0  # Number of matching bases at 3' end


@dataclass
class SpecificityResult:
    """Complete specificity analysis result."""
    primer_sequence: str
    primer_type: str
    total_hits: int
    high_risk_hits: int
    medium_risk_hits: int
    low_risk_hits: int
    hits: List[SpecificityHit] = field(default_factory=list)
    overall_risk: RiskLevel = RiskLevel.LOW
    specificity_score: float = 100.0  # 0-100, higher is better
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class PrimerSetSpecificityResult:
    """Specificity analysis for complete primer set."""
    primer_results: Dict[str, SpecificityResult] = field(default_factory=dict)
    overall_specificity_score: float = 100.0
    cross_reactivity_detected: bool = False
    high_risk_primers: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class SpecificityChecker(LoggerMixin):
    """
    Specificity checker for RT-LAMP primers with multiple analysis methods.
    """
    
    def __init__(self, 
                 blast_db_path: Optional[str] = None,
                 assay_temperature: float = 65.0):
        """
        Initialize specificity checker.
        
        Args:
            blast_db_path: Path to BLAST database (for Phase 1.5+)
            assay_temperature: RT-LAMP assay temperature in Celsius
        """
        self.blast_db_path = blast_db_path
        self.assay_temperature = assay_temperature
        self.thermo_calc = ThermoCalculator()
        
        # Default exclusion list for basic specificity (Phase 1)
        self.exclusion_sequences = [
            # Common human sequences that could cause issues
            "GGGGGGGGGGGGGGGG",  # Poly-G
            "AAAAAAAAAAAAAAAA",  # Poly-A
            "TTTTTTTTTTTTTTTT",  # Poly-T
            "CCCCCCCCCCCCCCCC",  # Poly-C
            # Add more problematic sequences as needed
        ]
        
        self.logger.info(f"Initialized SpecificityChecker (assay temp: {assay_temperature}°C)")
    
    def check_primer_specificity(self, 
                                primer: Primer,
                                method: str = "basic") -> SpecificityResult:
        """
        Check specificity of a single primer.
        
        Args:
            primer: Primer to check
            method: "basic" for Phase 1, "blast" for Phase 1.5+
            
        Returns:
            SpecificityResult object
        """
        self.logger.debug(f"Checking specificity for {primer.type.value} primer")
        
        if method == "basic":
            return self._check_basic_specificity(primer)
        elif method == "blast":
            return self._check_blast_specificity(primer)
        else:
            raise SpecificityError(f"Unknown specificity method: {method}")
    
    def check_primer_set_specificity(self, 
                                   primer_set: LampPrimerSet,
                                   method: str = "basic") -> PrimerSetSpecificityResult:
        """
        Check specificity of complete primer set.
        
        Args:
            primer_set: Complete primer set
            method: Specificity checking method
            
        Returns:
            PrimerSetSpecificityResult object
        """
        self.logger.info("Checking primer set specificity")
        
        result = PrimerSetSpecificityResult()
        
        # Check each primer individually
        for primer in primer_set.get_all_primers():
            primer_result = self.check_primer_specificity(primer, method)
            result.primer_results[primer.type.value] = primer_result
            
            # Track high-risk primers
            if primer_result.overall_risk == RiskLevel.HIGH:
                result.high_risk_primers.append(primer.type.value)
        
        # Check for cross-reactivity between primers
        result.cross_reactivity_detected = self._check_cross_reactivity(primer_set)
        
        # Calculate overall specificity score
        result.overall_specificity_score = self._calculate_set_specificity_score(result)
        
        # Generate recommendations
        result.recommendations = self._generate_specificity_recommendations(result)
        
        return result
    
    def _check_basic_specificity(self, primer: Primer) -> SpecificityResult:
        """
        Basic specificity check using exclusion list (Phase 1).
        
        Checks for exact full-length substring matches against exclusion sequences
        and their reverse complements.
        """
        result = SpecificityResult(
            primer_sequence=primer.sequence,
            primer_type=primer.type.value,
            total_hits=0,
            high_risk_hits=0,
            medium_risk_hits=0,
            low_risk_hits=0
        )
        
        primer_seq = primer.sequence.upper()
        primer_rc = reverse_complement(primer_seq)
        
        # Check against exclusion list
        for exclusion_seq in self.exclusion_sequences:
            exclusion_rc = reverse_complement(exclusion_seq)
            
            # Check for exact matches
            if exclusion_seq in primer_seq or exclusion_rc in primer_seq:
                hit = SpecificityHit(
                    query_primer=primer_seq,
                    target_sequence=exclusion_seq,
                    target_id="exclusion_list",
                    alignment_length=len(exclusion_seq),
                    identity_percent=100.0,
                    query_start=0,
                    query_end=len(primer_seq) - 1,
                    target_start=0,
                    target_end=len(exclusion_seq) - 1,
                    risk_level=RiskLevel.HIGH
                )
                
                result.hits.append(hit)
                result.high_risk_hits += 1
                result.total_hits += 1
        
        # Check for excessive repeats (potential non-specific binding)
        repeat_patterns = ['AAAA', 'TTTT', 'GGGG', 'CCCC', 'ATAT', 'GCGC']
        for pattern in repeat_patterns:
            if pattern in primer_seq:
                result.warnings.append(f"Repeat pattern detected: {pattern}")
                result.specificity_score -= 10
        
        # Check for low complexity regions
        if self._has_low_complexity(primer_seq):
            result.warnings.append("Low complexity sequence detected")
            result.specificity_score -= 15
        
        # Determine overall risk
        if result.high_risk_hits > 0:
            result.overall_risk = RiskLevel.HIGH
            result.specificity_score = max(0, result.specificity_score - 50)
        elif result.medium_risk_hits > 0:
            result.overall_risk = RiskLevel.MEDIUM
            result.specificity_score = max(0, result.specificity_score - 25)
        else:
            result.overall_risk = RiskLevel.LOW
        
        return result
    
    def _check_blast_specificity(self, primer: Primer) -> SpecificityResult:
        """
        BLAST-based specificity check (Phase 1.5+).
        
        This is a placeholder implementation for Phase 1.5+.
        """
        self.logger.info("BLAST specificity checking (Phase 1.5+ feature)")
        
        # For Phase 1, return basic specificity result
        return self._check_basic_specificity(primer)
    
    def _run_blast_search(self, primer_sequence: str) -> List[SpecificityHit]:
        """
        Run BLAST search against database (Phase 1.5+).
        
        This is a placeholder for the full BLAST implementation.
        """
        # Placeholder implementation
        hits = []
        
        if not self.blast_db_path or not Path(self.blast_db_path).exists():
            self.logger.warning("BLAST database not available")
            return hits
        
        try:
            # Create temporary query file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
                f.write(f">query\n{primer_sequence}\n")
                query_file = f.name
            
            # Run BLAST (simplified command)
            blast_cmd = [
                'blastn',
                '-query', query_file,
                '-db', self.blast_db_path,
                '-outfmt', '6',  # Tabular format
                '-word_size', '7',
                '-evalue', '1000',
                '-max_target_seqs', '100'
            ]
            
            result = subprocess.run(blast_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                hits = self._parse_blast_output(result.stdout, primer_sequence)
            else:
                self.logger.error(f"BLAST failed: {result.stderr}")
            
            # Clean up
            Path(query_file).unlink()
            
        except subprocess.TimeoutExpired:
            self.logger.error("BLAST search timed out")
        except Exception as e:
            self.logger.error(f"BLAST search failed: {e}")
        
        return hits
    
    def _parse_blast_output(self, blast_output: str, query_sequence: str) -> List[SpecificityHit]:
        """Parse BLAST tabular output into SpecificityHit objects."""
        hits = []
        
        for line in blast_output.strip().split('\n'):
            if not line:
                continue
            
            fields = line.split('\t')
            if len(fields) < 12:
                continue
            
            try:
                hit = SpecificityHit(
                    query_primer=query_sequence,
                    target_sequence=fields[1],  # Subject ID
                    target_id=fields[1],
                    alignment_length=int(fields[3]),
                    identity_percent=float(fields[2]),
                    query_start=int(fields[6]) - 1,  # Convert to 0-based
                    query_end=int(fields[7]) - 1,
                    target_start=int(fields[8]) - 1,
                    target_end=int(fields[9]) - 1,
                    e_value=float(fields[10]),
                    bit_score=float(fields[11])
                )
                
                # Classify risk level
                hit.risk_level = self._classify_hit_risk(hit)
                
                # Check if human genome hit
                hit.is_human_genome = 'human' in hit.target_id.lower() or 'homo_sapiens' in hit.target_id.lower()
                
                # Calculate 3' end match
                hit.three_prime_match = self._calculate_three_prime_match(hit, query_sequence)
                
                # Predict melting temperature for the hit
                if hit.alignment_length >= 10:
                    aligned_seq = query_sequence[hit.query_start:hit.query_end + 1]
                    hit.predicted_tm = self.thermo_calc.calculate_tm(aligned_seq)
                
                hits.append(hit)
                
            except (ValueError, IndexError) as e:
                self.logger.warning(f"Error parsing BLAST line: {e}")
                continue
        
        return hits
    
    def _classify_hit_risk(self, hit: SpecificityHit) -> RiskLevel:
        """
        Classify specificity hit risk level based on SPEC criteria.
        
        High Risk: (Alignment length ≥18bp AND match to human genome) OR 
                  (Perfect 3'-end match of 5+ bases AND predicted off-target Tm > (AssayTemp - 7°C))
        
        Medium Risk: (Alignment length ≥15bp AND identity ≥85%) AND 
                    predicted off-target Tm > (AssayTemp - 12°C)
        """
        
        # High risk conditions
        if (hit.alignment_length >= 18 and hit.is_human_genome):
            return RiskLevel.HIGH
        
        if (hit.three_prime_match >= 5 and 
            hit.predicted_tm > (self.assay_temperature - 7)):
            return RiskLevel.HIGH
        
        # Medium risk conditions
        if (hit.alignment_length >= 15 and 
            hit.identity_percent >= 85 and
            hit.predicted_tm > (self.assay_temperature - 12)):
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def _calculate_three_prime_match(self, hit: SpecificityHit, query_sequence: str) -> int:
        """Calculate number of matching bases at 3' end."""
        # This is a simplified calculation
        # In full implementation, would need actual alignment details
        if hit.query_end == len(query_sequence) - 1:  # Hit extends to 3' end
            return min(5, hit.alignment_length)  # Assume up to 5 bases match
        return 0
    
    def _check_cross_reactivity(self, primer_set: LampPrimerSet) -> bool:
        """
        Check for cross-reactivity between primers in the set.
        
        Args:
            primer_set: Complete primer set
            
        Returns:
            True if cross-reactivity detected
        """
        primers = primer_set.get_all_primers()
        
        for i, primer1 in enumerate(primers):
            for primer2 in primers[i + 1:]:
                # Check for primer-dimer formation
                dimers = self.thermo_calc.predict_dimer(primer1.sequence, primer2.sequence)
                
                for dimer in dimers:
                    if dimer.delta_g < -5.0:  # Strong dimer formation
                        self.logger.warning(f"Strong dimer predicted between {primer1.type.value} and {primer2.type.value}")
                        return True
        
        return False
    
    def _calculate_set_specificity_score(self, result: PrimerSetSpecificityResult) -> float:
        """Calculate overall specificity score for primer set."""
        
        if not result.primer_results:
            return 0.0
        
        # Average individual primer scores
        individual_scores = [r.specificity_score for r in result.primer_results.values()]
        avg_score = sum(individual_scores) / len(individual_scores)
        
        # Penalty for high-risk primers
        high_risk_penalty = len(result.high_risk_primers) * 20
        
        # Penalty for cross-reactivity
        cross_reactivity_penalty = 15 if result.cross_reactivity_detected else 0
        
        final_score = max(0, avg_score - high_risk_penalty - cross_reactivity_penalty)
        
        return final_score
    
    def _generate_specificity_recommendations(self, result: PrimerSetSpecificityResult) -> List[str]:
        """Generate recommendations based on specificity analysis."""
        recommendations = []
        
        if result.high_risk_primers:
            recommendations.append(f"High-risk primers detected: {', '.join(result.high_risk_primers)}. Consider redesigning these primers.")
        
        if result.cross_reactivity_detected:
            recommendations.append("Cross-reactivity detected between primers. Consider adjusting primer sequences.")
        
        if result.overall_specificity_score < 70:
            recommendations.append("Low overall specificity score. Consider alternative primer combinations.")
        
        # Check individual primer issues
        for primer_type, primer_result in result.primer_results.items():
            if primer_result.overall_risk == RiskLevel.HIGH:
                recommendations.append(f"{primer_type} primer has high specificity risk. Consider redesigning.")
            
            if primer_result.warnings:
                recommendations.append(f"{primer_type} primer warnings: {'; '.join(primer_result.warnings)}")
        
        return recommendations
    
    def _has_low_complexity(self, sequence: str) -> bool:
        """
        Check for low complexity sequences.
        
        Args:
            sequence: DNA sequence
            
        Returns:
            True if low complexity detected
        """
        # Simple low complexity check - high frequency of single nucleotide
        for base in 'ATGC':
            if sequence.count(base) / len(sequence) > 0.6:  # >60% single base
                return True
        
        # Check for simple repeats
        for i in range(2, 5):  # Check 2-4 base repeats
            for j in range(len(sequence) - i * 3):
                motif = sequence[j:j + i]
                if sequence[j:j + i * 3] == motif * 3:  # 3x repeat
                    return True
        
        return False
    
    def generate_specificity_report(self, result: PrimerSetSpecificityResult) -> Dict[str, Any]:
        """
        Generate comprehensive specificity report.
        
        Args:
            result: Primer set specificity result
            
        Returns:
            Dictionary containing specificity report
        """
        report = {
            'overall_specificity_score': result.overall_specificity_score,
            'cross_reactivity_detected': result.cross_reactivity_detected,
            'high_risk_primers': result.high_risk_primers.copy(),
            'primer_details': {},
            'summary': {
                'total_primers_analyzed': len(result.primer_results),
                'high_risk_count': len(result.high_risk_primers),
                'medium_risk_count': 0,
                'low_risk_count': 0
            },
            'recommendations': result.recommendations.copy()
        }
        
        # Individual primer details
        for primer_type, primer_result in result.primer_results.items():
            report['primer_details'][primer_type] = {
                'sequence': primer_result.primer_sequence,
                'specificity_score': primer_result.specificity_score,
                'risk_level': primer_result.overall_risk.value,
                'total_hits': primer_result.total_hits,
                'high_risk_hits': primer_result.high_risk_hits,
                'medium_risk_hits': primer_result.medium_risk_hits,
                'low_risk_hits': primer_result.low_risk_hits,
                'warnings': primer_result.warnings.copy(),
                'top_hits': []
            }
            
            # Add top hits (up to 5)
            for hit in primer_result.hits[:5]:
                hit_info = {
                    'target_id': hit.target_id,
                    'alignment_length': hit.alignment_length,
                    'identity_percent': hit.identity_percent,
                    'risk_level': hit.risk_level.value,
                    'predicted_tm': hit.predicted_tm,
                    'is_human_genome': hit.is_human_genome
                }
                report['primer_details'][primer_type]['top_hits'].append(hit_info)
            
            # Update summary counts
            if primer_result.overall_risk == RiskLevel.MEDIUM:
                report['summary']['medium_risk_count'] += 1
            elif primer_result.overall_risk == RiskLevel.LOW:
                report['summary']['low_risk_count'] += 1
        
        return report
    
    def add_exclusion_sequence(self, sequence: str) -> None:
        """
        Add sequence to exclusion list for basic specificity checking.
        
        Args:
            sequence: DNA sequence to exclude
        """
        if sequence not in self.exclusion_sequences:
            self.exclusion_sequences.append(sequence.upper())
            self.logger.info(f"Added exclusion sequence: {sequence}")
    
    def remove_exclusion_sequence(self, sequence: str) -> None:
        """
        Remove sequence from exclusion list.
        
        Args:
            sequence: DNA sequence to remove
        """
        if sequence.upper() in self.exclusion_sequences:
            self.exclusion_sequences.remove(sequence.upper())
            self.logger.info(f"Removed exclusion sequence: {sequence}")
    
    def set_blast_database(self, db_path: str) -> None:
        """
        Set BLAST database path for specificity checking.
        
        Args:
            db_path: Path to BLAST database
        """
        if Path(db_path).exists():
            self.blast_db_path = db_path
            self.logger.info(f"Set BLAST database: {db_path}")
        else:
            raise SpecificityError(f"BLAST database not found: {db_path}")

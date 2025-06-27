"""
RT-LAMP Primer Design Module

This module implements RT-LAMP specific primer design algorithms including
primer candidate generation, optimization, validation, and scoring functions.
Supports F3, B3, FIP, BIP primers and optional loop primers (LF/LB).
"""

import math
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from rt_lamp_app.core.sequence_processing import Sequence
from rt_lamp_app.core.thermodynamics import ThermoCalculator
from rt_lamp_app.design.exceptions import (
    GeometricConstraintError, PrimerOptimizationError, 
    InsufficientCandidatesError
)
from rt_lamp_app.design.utils import (
    reverse_complement, calculate_gc_content, validate_primer_geometry,
    validate_sequence_composition
)
from rt_lamp_app.logger import LoggerMixin


class PrimerType(Enum):
    """Enumeration of RT-LAMP primer types."""
    F3 = "F3"
    B3 = "B3" 
    FIP = "FIP"
    BIP = "BIP"
    LF = "LF"  # Loop Forward
    LB = "LB"  # Loop Backward


@dataclass
class Primer:
    """
    Represents a single RT-LAMP primer with all properties.
    """
    type: PrimerType
    sequence: str
    start_pos: int
    end_pos: int
    strand: str  # "+" or "-"
    tm: float
    gc_content: float
    delta_g: float
    score: float = 0.0
    
    # Sub-sequences for composite primers (FIP/BIP)
    f1c_sequence: Optional[str] = None
    f2_sequence: Optional[str] = None
    b1c_sequence: Optional[str] = None
    b2_sequence: Optional[str] = None
    
    # Thermodynamic properties
    end_stability: float = 0.0
    hairpin_dg: float = 0.0
    dimer_dg: float = 0.0
    
    # Quality metrics
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate derived properties after initialization."""
        if not self.gc_content:
            self.gc_content = calculate_gc_content(self.sequence)


@dataclass 
class LampPrimerSet:
    """
    Complete set of RT-LAMP primers with validation and scoring.
    """
    f3: Primer
    b3: Primer
    fip: Primer
    bip: Primer
    lf: Optional[Primer] = None
    lb: Optional[Primer] = None
    
    # Set-level properties
    overall_score: float = 0.0
    tm_uniformity: float = 0.0
    specificity_score: float = 0.0
    geometric_validity: bool = True
    
    # Distances and spacing
    f3_f2_distance: int = 0
    b3_b2_distance: int = 0
    f2_b2_amplicon_size: int = 0
    
    # Reports and analysis
    design_report: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    def get_all_primers(self) -> List[Primer]:
        """Get all primers in the set."""
        primers = [self.f3, self.b3, self.fip, self.bip]
        if self.lf:
            primers.append(self.lf)
        if self.lb:
            primers.append(self.lb)
        return primers
    
    def get_tm_range(self) -> Tuple[float, float]:
        """Get melting temperature range of all primers."""
        tms = [p.tm for p in self.get_all_primers()]
        return min(tms), max(tms)


class PrimerDesigner(LoggerMixin):
    """
    RT-LAMP primer designer implementing geometric constraints and optimization.
    """
    
    # Default geometric constraints for RT-LAMP
    DEFAULT_CONSTRAINTS = {
        'F3_length_min': 15, 'F3_length_max': 25,
        'B3_length_min': 15, 'B3_length_max': 25,
        'FIP_length_min': 35, 'FIP_length_max': 50,
        'BIP_length_min': 35, 'BIP_length_max': 50,
        'F1c_length_min': 15, 'F1c_length_max': 25,
        'B1c_length_min': 15, 'B1c_length_max': 25,
        'F2_length_min': 18, 'F2_length_max': 25,
        'B2_length_min': 18, 'B2_length_max': 25,
        'F2_B2_amplicon_min': 120, 'F2_B2_amplicon_max': 200,
        'F3_F2_spacing_min': 0, 'F3_F2_spacing_max': 20,
        'B3_B2_spacing_min': 0, 'B3_B2_spacing_max': 20,
        'LF_length_min': 15, 'LF_length_max': 25,
        'LB_length_min': 15, 'LB_length_max': 25
    }
    
    # Optimal ranges for primer properties
    OPTIMAL_RANGES = {
        'tm_min': 58.0, 'tm_max': 65.0, 'tm_optimal': 61.5,
        'gc_min': 40.0, 'gc_max': 60.0, 'gc_optimal': 50.0,
        'end_stability_max': -2.0,  # kcal/mol
        'hairpin_dg_max': -3.0,     # kcal/mol
        'dimer_dg_max': -5.0        # kcal/mol
    }
    
    def __init__(self, constraints: Optional[Dict] = None):
        """
        Initialize primer designer.
        
        Args:
            constraints: Custom geometric constraints (optional)
        """
        self.constraints = {**self.DEFAULT_CONSTRAINTS}
        if constraints:
            self.constraints.update(constraints)
        
        self.thermo_calc = ThermoCalculator()
        self.logger.info("Initialized PrimerDesigner with RT-LAMP constraints")
    
    def design_primer_set(self, 
                         target_sequence: Sequence,
                         include_loop_primers: bool = False,
                         max_candidates: int = 100) -> List[LampPrimerSet]:
        """
        Design complete RT-LAMP primer sets for target sequence.
        
        Args:
            target_sequence: Target sequence for primer design
            include_loop_primers: Whether to include LF/LB primers
            max_candidates: Maximum number of candidate sets to generate
            
        Returns:
            List of LampPrimerSet objects ranked by score
            
        Raises:
            InsufficientCandidatesError: If insufficient candidates found
        """
        self.logger.info(f"Designing RT-LAMP primers for {target_sequence.header}")
        
        # Generate primer candidates for each type
        f3_candidates = self._generate_f3_candidates(target_sequence)
        b3_candidates = self._generate_b3_candidates(target_sequence)
        fip_candidates = self._generate_fip_candidates(target_sequence)
        bip_candidates = self._generate_bip_candidates(target_sequence)
        
        self.logger.info(f"Generated candidates: F3={len(f3_candidates)}, B3={len(b3_candidates)}, "
                        f"FIP={len(fip_candidates)}, BIP={len(bip_candidates)}")
        
        # Check minimum candidates
        min_candidates = 5
        for primer_type, candidates in [("F3", f3_candidates), ("B3", b3_candidates), 
                                       ("FIP", fip_candidates), ("BIP", bip_candidates)]:
            if len(candidates) < min_candidates:
                raise InsufficientCandidatesError(primer_type, len(candidates), min_candidates)
        
        # Generate loop primer candidates if requested
        lf_candidates = []
        lb_candidates = []
        if include_loop_primers:
            lf_candidates = self._generate_loop_candidates(target_sequence, PrimerType.LF)
            lb_candidates = self._generate_loop_candidates(target_sequence, PrimerType.LB)
        
        # Combine primers into sets and validate geometry
        primer_sets = []
        combinations_tested = 0
        
        for f3 in f3_candidates[:20]:  # Limit combinations for performance
            for b3 in b3_candidates[:20]:
                for fip in fip_candidates[:20]:
                    for bip in bip_candidates[:20]:
                        combinations_tested += 1
                        
                        try:
                            # Create base primer set
                            primer_set = LampPrimerSet(f3=f3, b3=b3, fip=fip, bip=bip)
                            
                            # Validate geometry
                            self._validate_primer_set_geometry(primer_set, target_sequence)
                            
                            # Add loop primers if available
                            if include_loop_primers and lf_candidates:
                                primer_set.lf = lf_candidates[0]  # Use best LF candidate
                            if include_loop_primers and lb_candidates:
                                primer_set.lb = lb_candidates[0]  # Use best LB candidate
                            
                            # Score the primer set
                            self._score_primer_set(primer_set)
                            
                            primer_sets.append(primer_set)
                            
                            if len(primer_sets) >= max_candidates:
                                break
                                
                        except GeometricConstraintError as e:
                            self.logger.debug(f"Geometric constraint violation: {e}")
                            continue
                        except Exception as e:
                            self.logger.warning(f"Error creating primer set: {e}")
                            continue
                    
                    if len(primer_sets) >= max_candidates:
                        break
                if len(primer_sets) >= max_candidates:
                    break
            if len(primer_sets) >= max_candidates:
                break
        
        self.logger.info(f"Tested {combinations_tested} combinations, found {len(primer_sets)} valid sets")
        
        if not primer_sets:
            raise InsufficientCandidatesError("primer_sets", 0, 1)
        
        # Sort by overall score (higher is better)
        primer_sets.sort(key=lambda x: x.overall_score, reverse=True)
        
        return primer_sets
    
    def _generate_f3_candidates(self, target_sequence: Sequence) -> List[Primer]:
        """Generate F3 primer candidates."""
        candidates = []
        sequence = target_sequence.sequence
        
        min_len = self.constraints['F3_length_min']
        max_len = self.constraints['F3_length_max']
        
        # F3 is at the 5' end of the target region
        for length in range(min_len, max_len + 1):
            for start in range(0, min(50, len(sequence) - length + 1)):  # Search first 50bp
                end = start + length - 1
                primer_seq = sequence[start:end + 1]
                
                try:
                    primer = self._create_primer(
                        PrimerType.F3, primer_seq, start, end, "+", target_sequence
                    )
                    
                    if self._is_valid_primer(primer):
                        candidates.append(primer)
                        
                except Exception as e:
                    self.logger.debug(f"Error creating F3 primer: {e}")
                    continue
        
        # Score and sort candidates
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:50]  # Return top 50
    
    def _generate_b3_candidates(self, target_sequence: Sequence) -> List[Primer]:
        """Generate B3 primer candidates."""
        candidates = []
        sequence = target_sequence.sequence
        seq_len = len(sequence)
        
        min_len = self.constraints['B3_length_min']
        max_len = self.constraints['B3_length_max']
        
        # B3 is at the 3' end of the target region (reverse complement)
        for length in range(min_len, max_len + 1):
            for start in range(max(0, seq_len - 50), seq_len - length + 1):  # Search last 50bp
                end = start + length - 1
                target_region = sequence[start:end + 1]
                primer_seq = reverse_complement(target_region)  # B3 is reverse complement
                
                try:
                    primer = self._create_primer(
                        PrimerType.B3, primer_seq, start, end, "-", target_sequence
                    )
                    
                    if self._is_valid_primer(primer):
                        candidates.append(primer)
                        
                except Exception as e:
                    self.logger.debug(f"Error creating B3 primer: {e}")
                    continue
        
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:50]
    
    def _generate_fip_candidates(self, target_sequence: Sequence) -> List[Primer]:
        """Generate FIP primer candidates using definitive LAMP construction logic."""
        candidates = []
        sequence = target_sequence.sequence
        seq_len = len(sequence)
        
        f1c_min = self.constraints['F1c_length_min']
        f1c_max = self.constraints['F1c_length_max']
        f2_min = self.constraints['F2_length_min']
        f2_max = self.constraints['F2_length_max']
        
        # Search for F1c and F2 regions
        for f1c_len in range(f1c_min, f1c_max + 1):
            for f2_len in range(f2_min, f2_max + 1):
                # F1c region (middle-right of sequence)
                for f1c_start in range(seq_len // 3, seq_len - f1c_len - 50):
                    f1c_end = f1c_start + f1c_len - 1
                    f1c_region = (f1c_start, f1c_end)
                    
                    # F2 region (left of F1c, with spacing)
                    for f2_start in range(50, f1c_start - 20):  # Ensure spacing
                        f2_end = f2_start + f2_len - 1
                        f2_region = (f2_start, f2_end)
                        
                        try:
                            # Construct FIP using definitive logic
                            fip_seq = self._construct_fip_primer(sequence, f1c_region, f2_region)
                            
                            primer = self._create_primer(
                                PrimerType.FIP, fip_seq, f2_start, f1c_end, "+", target_sequence
                            )
                            
                            # Store sub-sequences
                            primer.f1c_sequence = sequence[f1c_start:f1c_end + 1]
                            primer.f2_sequence = sequence[f2_start:f2_end + 1]
                            
                            if self._is_valid_primer(primer):
                                candidates.append(primer)
                                
                        except Exception as e:
                            self.logger.debug(f"Error creating FIP primer: {e}")
                            continue
        
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:50]
    
    def _generate_bip_candidates(self, target_sequence: Sequence) -> List[Primer]:
        """Generate BIP primer candidates using definitive LAMP construction logic."""
        candidates = []
        sequence = target_sequence.sequence
        seq_len = len(sequence)
        
        b1c_min = self.constraints['B1c_length_min']
        b1c_max = self.constraints['B1c_length_max']
        b2_min = self.constraints['B2_length_min']
        b2_max = self.constraints['B2_length_max']
        
        # Search for B1c and B2 regions
        for b1c_len in range(b1c_min, b1c_max + 1):
            for b2_len in range(b2_min, b2_max + 1):
                # B1c region (middle-left of sequence)
                for b1c_start in range(50, seq_len // 2):
                    b1c_end = b1c_start + b1c_len - 1
                    b1c_region = (b1c_start, b1c_end)
                    
                    # B2 region (right of B1c, with spacing)
                    for b2_start in range(b1c_end + 20, seq_len - b2_len - 50):
                        b2_end = b2_start + b2_len - 1
                        b2_region = (b2_start, b2_end)
                        
                        try:
                            # Construct BIP using definitive logic
                            bip_seq = self._construct_bip_primer(sequence, b1c_region, b2_region)
                            
                            primer = self._create_primer(
                                PrimerType.BIP, bip_seq, b1c_start, b2_end, "-", target_sequence
                            )
                            
                            # Store sub-sequences
                            primer.b1c_sequence = sequence[b1c_start:b1c_end + 1]
                            primer.b2_sequence = sequence[b2_start:b2_end + 1]
                            
                            if self._is_valid_primer(primer):
                                candidates.append(primer)
                                
                        except Exception as e:
                            self.logger.debug(f"Error creating BIP primer: {e}")
                            continue
        
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:50]
    
    def _generate_loop_candidates(self, target_sequence: Sequence, 
                                 primer_type: PrimerType) -> List[Primer]:
        """Generate loop primer candidates (LF/LB)."""
        candidates = []
        sequence = target_sequence.sequence
        seq_len = len(sequence)
        
        min_len = self.constraints[f'{primer_type.value}_length_min']
        max_len = self.constraints[f'{primer_type.value}_length_max']
        
        # Loop primers are in the middle regions
        if primer_type == PrimerType.LF:
            # LF is in the F1-F2 loop region
            search_start = seq_len // 4
            search_end = seq_len // 2
            strand = "+"
        else:  # LB
            # LB is in the B1-B2 loop region  
            search_start = seq_len // 2
            search_end = 3 * seq_len // 4
            strand = "-"
        
        for length in range(min_len, max_len + 1):
            for start in range(search_start, min(search_end, seq_len - length + 1)):
                end = start + length - 1
                
                if strand == "+":
                    primer_seq = sequence[start:end + 1]
                else:
                    primer_seq = reverse_complement(sequence[start:end + 1])
                
                try:
                    primer = self._create_primer(
                        primer_type, primer_seq, start, end, strand, target_sequence
                    )
                    
                    if self._is_valid_primer(primer):
                        candidates.append(primer)
                        
                except Exception as e:
                    self.logger.debug(f"Error creating {primer_type.value} primer: {e}")
                    continue
        
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:20]
    
    def _construct_fip_primer(self, target_sequence: str, 
                             f1c_region: Tuple[int, int], 
                             f2_region: Tuple[int, int]) -> str:
        """
        Construct FIP primer using definitive LAMP logic.
        
        FIP = F1c_reverse_complement + F2_sense
        """
        f1c_part = target_sequence[f1c_region[0]:f1c_region[1] + 1]
        f2_part = target_sequence[f2_region[0]:f2_region[1] + 1]
        
        return reverse_complement(f1c_part) + f2_part
    
    def _construct_bip_primer(self, target_sequence: str,
                             b1c_region: Tuple[int, int],
                             b2_region: Tuple[int, int]) -> str:
        """
        Construct BIP primer using definitive LAMP logic.
        
        BIP = B1c_reverse_complement + B2_sense
        """
        b1c_part = target_sequence[b1c_region[0]:b1c_region[1] + 1]
        b2_part = target_sequence[b2_region[0]:b2_region[1] + 1]
        
        return reverse_complement(b1c_part) + b2_part
    
    def _create_primer(self, primer_type: PrimerType, sequence: str,
                      start_pos: int, end_pos: int, strand: str,
                      target_sequence: Sequence) -> Primer:
        """Create primer object with thermodynamic properties."""
        
        # Calculate thermodynamic properties
        tm = self.thermo_calc.calculate_tm(sequence)
        gc_content = calculate_gc_content(sequence)
        delta_g = self.thermo_calc.calculate_free_energy_37c(sequence)
        end_stability = self.thermo_calc.calculate_end_stability(sequence)
        
        # Predict secondary structures
        hairpins = self.thermo_calc.predict_hairpin(sequence)
        hairpin_dg = hairpins[0].delta_g if hairpins else 0.0
        
        # Create primer
        primer = Primer(
            type=primer_type,
            sequence=sequence,
            start_pos=start_pos,
            end_pos=end_pos,
            strand=strand,
            tm=tm,
            gc_content=gc_content,
            delta_g=delta_g,
            end_stability=end_stability,
            hairpin_dg=hairpin_dg
        )
        
        # Score the primer
        primer.score = self._score_primer(primer)
        
        return primer
    
    def _is_valid_primer(self, primer: Primer) -> bool:
        """Check if primer meets basic validity criteria."""
        
        # Check sequence composition
        is_valid, issues = validate_sequence_composition(primer.sequence)
        if not is_valid:
            primer.warnings.extend(issues)
            return False
        
        # Check thermodynamic properties
        if not (self.OPTIMAL_RANGES['tm_min'] <= primer.tm <= self.OPTIMAL_RANGES['tm_max']):
            return False
        
        if not (self.OPTIMAL_RANGES['gc_min'] <= primer.gc_content <= self.OPTIMAL_RANGES['gc_max']):
            return False
        
        if primer.hairpin_dg < self.OPTIMAL_RANGES['hairpin_dg_max']:
            return False
        
        return True
    
    def _score_primer(self, primer: Primer) -> float:
        """
        Score individual primer using simplified scoring for Phase 1.
        
        Score = penalty_tm + penalty_gc + penalty_hairpin + penalty_end_stability
        Higher score is better (penalties are negative).
        """
        score = 0.0
        
        # Tm penalty (squared deviation from optimal)
        tm_optimal = self.OPTIMAL_RANGES['tm_optimal']
        tm_penalty = -((primer.tm - tm_optimal) ** 2) / 10.0
        score += tm_penalty
        
        # GC content penalty
        gc_optimal = self.OPTIMAL_RANGES['gc_optimal']
        gc_penalty = -((primer.gc_content - gc_optimal) ** 2) / 100.0
        score += gc_penalty
        
        # Hairpin penalty
        if primer.hairpin_dg < self.OPTIMAL_RANGES['hairpin_dg_max']:
            hairpin_penalty = primer.hairpin_dg  # More negative = worse
            score += hairpin_penalty
        
        # End stability penalty
        if primer.end_stability > self.OPTIMAL_RANGES['end_stability_max']:
            end_penalty = -abs(primer.end_stability - self.OPTIMAL_RANGES['end_stability_max'])
            score += end_penalty
        
        return score
    
    def _validate_primer_set_geometry(self, primer_set: LampPrimerSet, 
                                     target_sequence: Sequence) -> None:
        """Validate geometric constraints for primer set."""
        
        # Extract regions for validation
        regions = {
            'F3': (primer_set.f3.start_pos, primer_set.f3.end_pos),
            'B3': (primer_set.b3.start_pos, primer_set.b3.end_pos)
        }
        
        # Add FIP/BIP sub-regions if available
        if primer_set.fip.f2_sequence and primer_set.fip.f1c_sequence:
            f2_len = len(primer_set.fip.f2_sequence)
            f1c_len = len(primer_set.fip.f1c_sequence)
            regions['F2'] = (primer_set.fip.start_pos, primer_set.fip.start_pos + f2_len - 1)
            regions['F1c'] = (primer_set.fip.end_pos - f1c_len + 1, primer_set.fip.end_pos)
        
        if primer_set.bip.b1c_sequence and primer_set.bip.b2_sequence:
            b1c_len = len(primer_set.bip.b1c_sequence)
            b2_len = len(primer_set.bip.b2_sequence)
            regions['B1c'] = (primer_set.bip.start_pos, primer_set.bip.start_pos + b1c_len - 1)
            regions['B2'] = (primer_set.bip.end_pos - b2_len + 1, primer_set.bip.end_pos)
        
        # Validate using utility function
        validate_primer_geometry(regions, self.constraints)
        
        # Calculate distances
        if 'F2' in regions and 'B2' in regions:
            primer_set.f2_b2_amplicon_size = regions['B2'][0] - regions['F2'][1] - 1
        
        primer_set.geometric_validity = True
    
    def _score_primer_set(self, primer_set: LampPrimerSet) -> None:
        """Score complete primer set."""
        
        # Individual primer scores
        individual_scores = [p.score for p in primer_set.get_all_primers()]
        avg_individual_score = sum(individual_scores) / len(individual_scores)
        
        # Tm uniformity (lower range is better)
        tm_min, tm_max = primer_set.get_tm_range()
        tm_uniformity = tm_max - tm_min
        primer_set.tm_uniformity = tm_uniformity
        tm_uniformity_penalty = -tm_uniformity  # Penalty for large range
        
        # Amplicon size penalty
        amplicon_penalty = 0.0
        if primer_set.f2_b2_amplicon_size > 0:
            optimal_amplicon = 160  # Middle of 120-200 range
            amplicon_deviation = abs(primer_set.f2_b2_amplicon_size - optimal_amplicon)
            amplicon_penalty = -amplicon_deviation / 10.0
        
        # Overall score
        primer_set.overall_score = (
            avg_individual_score + 
            tm_uniformity_penalty + 
            amplicon_penalty
        )
        
        # Add warnings
        if tm_uniformity > 5.0:
            primer_set.warnings.append(f"Large Tm range: {tm_uniformity:.1f}°C")
        
        if primer_set.f2_b2_amplicon_size > 200:
            primer_set.warnings.append(f"Large amplicon: {primer_set.f2_b2_amplicon_size}bp")
    
    def optimize_primer_set(self, primer_set: LampPrimerSet) -> LampPrimerSet:
        """
        Optimize primer set by fine-tuning individual primers.
        
        Args:
            primer_set: Initial primer set
            
        Returns:
            Optimized primer set
        """
        # For Phase 1, return the input set (optimization in Phase 1.5+)
        self.logger.info("Primer set optimization (Phase 1.5+ feature)")
        return primer_set
    
    def generate_design_report(self, primer_set: LampPrimerSet) -> Dict[str, Any]:
        """
        Generate comprehensive design report for primer set.
        
        Args:
            primer_set: Primer set to analyze
            
        Returns:
            Dictionary containing design report
        """
        report = {
            'primer_set_id': id(primer_set),
            'overall_score': primer_set.overall_score,
            'tm_uniformity': primer_set.tm_uniformity,
            'geometric_validity': primer_set.geometric_validity,
            'amplicon_size': primer_set.f2_b2_amplicon_size,
            'primers': {},
            'warnings': primer_set.warnings.copy(),
            'recommendations': []
        }
        
        # Individual primer details
        for primer in primer_set.get_all_primers():
            report['primers'][primer.type.value] = {
                'sequence': primer.sequence,
                'length': len(primer.sequence),
                'tm': primer.tm,
                'gc_content': primer.gc_content,
                'delta_g': primer.delta_g,
                'score': primer.score,
                'warnings': primer.warnings.copy()
            }
        
        # Add recommendations
        if primer_set.tm_uniformity > 3.0:
            report['recommendations'].append("Consider adjusting primer lengths to improve Tm uniformity")
        
        if primer_set.overall_score < -10:
            report['recommendations'].append("Low overall score - consider alternative primer combinations")
        
        primer_set.design_report = report
        return report

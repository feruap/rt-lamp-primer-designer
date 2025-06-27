
"""
Consensus orchestrator module for RT-LAMP primer design.

Orchestrates the entire consensus-based primer design workflow, integrating
MSA, consensus analysis, and variant-aware primer optimization.
"""

from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

from .msa import MultipleSequenceAlignment, AlignmentResult
from .consensus_analysis import ConsensusAnalyzer, ConsensusResult
from ..design.primer_design import PrimerDesigner
from ..core.sequence_processing import SequenceProcessor

logger = logging.getLogger(__name__)


@dataclass
class ConsensusDesignParameters:
    """Parameters for consensus-based primer design."""
    min_conservation_threshold: float = 0.8
    max_variants_per_position: int = 3
    primer_length_range: Tuple[int, int] = (18, 25)
    tm_range: Tuple[float, float] = (58.0, 65.0)
    gc_content_range: Tuple[float, float] = (40.0, 60.0)
    gap_penalty: float = -2.0
    match_score: float = 2.0
    mismatch_penalty: float = -1.0


@dataclass
class ConsensusPrimerSet:
    """Result of consensus primer design."""
    consensus_sequence: str
    primer_sets: List[Dict]
    conservation_analysis: ConsensusResult
    alignment_result: AlignmentResult
    robustness_scores: Dict[str, float]
    cross_variant_validation: Dict[str, Dict]


class ConsensusOrchestrator:
    """
    Orchestrates consensus-based RT-LAMP primer design workflow.
    
    Integrates multiple sequence alignment, consensus analysis, and
    variant-aware primer optimization for robust primer design.
    """
    
    def __init__(self, parameters: Optional[ConsensusDesignParameters] = None):
        """
        Initialize consensus orchestrator.
        
        Args:
            parameters: Design parameters for consensus workflow
        """
        self.parameters = parameters or ConsensusDesignParameters()
        self.msa = MultipleSequenceAlignment(
            gap_penalty=self.parameters.gap_penalty,
            match_score=self.parameters.match_score,
            mismatch_penalty=self.parameters.mismatch_penalty
        )
        self.consensus_analyzer = ConsensusAnalyzer(
            min_conservation_threshold=self.parameters.min_conservation_threshold
        )
        self.primer_designer = PrimerDesigner()
        self.sequence_processor = SequenceProcessor()
        
    def generate_consensus_primers(self, sequences: List[str], 
                                 target_region: Optional[Tuple[int, int]] = None) -> ConsensusPrimerSet:
        """
        Generate consensus-based RT-LAMP primer sets from multiple sequences.
        
        Args:
            sequences: List of nucleotide sequences (variants)
            target_region: Optional target region (start, end) for primer design
            
        Returns:
            ConsensusPrimerSet with optimized primers and analysis
        """
        logger.info(f"Starting consensus primer design for {len(sequences)} sequences")
        
        # Step 1: Validate and preprocess sequences
        validated_sequences = self._validate_input_sequences(sequences)
        
        # Step 2: Perform multiple sequence alignment
        logger.info("Performing multiple sequence alignment...")
        alignment_result = self.msa.align(validated_sequences)
        
        # Step 3: Generate consensus analysis
        logger.info("Generating consensus analysis...")
        consensus_result = self.consensus_analyzer.generate_consensus(alignment_result.aligned_sequences)
        
        # Step 4: Apply target region if specified
        if target_region:
            start, end = target_region
            # Extract target region from aligned sequences
            target_aligned_sequences = [seq[start:end] for seq in alignment_result.aligned_sequences]
            target_consensus_result = self.consensus_analyzer.generate_consensus(target_aligned_sequences)
        else:
            target_consensus_result = consensus_result
            target_aligned_sequences = alignment_result.aligned_sequences
        
        # Step 5: Design variant-aware primers
        logger.info("Designing variant-aware primers...")
        primer_sets = self._design_variant_aware_primers(target_consensus_result, alignment_result)
        
        # Step 6: Calculate robustness scores
        logger.info("Calculating robustness scores...")
        robustness_scores = self._calculate_robustness_scores(primer_sets, target_aligned_sequences)
        
        # Step 7: Cross-validate primers
        logger.info("Cross-validating primers...")
        cross_validation = self._cross_validate_primers(primer_sets, validated_sequences)
        
        logger.info("Consensus primer design completed")
        
        return ConsensusPrimerSet(
            consensus_sequence=consensus_result.consensus_sequence,
            primer_sets=primer_sets,
            conservation_analysis=consensus_result,
            alignment_result=alignment_result,
            robustness_scores=robustness_scores,
            cross_variant_validation=cross_validation
        )
        
    def _validate_input_sequences(self, sequences: List[str]) -> List[str]:
        """
        Validate and preprocess input sequences.
        
        Args:
            sequences: Raw input sequences
            
        Returns:
            Validated and cleaned sequences
        """
        if not sequences:
            raise ValueError("No sequences provided")
        
        if len(sequences) < 2:
            raise ValueError("At least 2 sequences required for consensus analysis")
        
        validated_sequences = []
        
        for i, seq in enumerate(sequences):
            # Clean sequence (remove whitespace, convert to uppercase)
            cleaned_seq = ''.join(seq.split()).upper()
            
            # Validate nucleotide content
            valid_nucleotides = set('ATCGN-')
            if not all(c in valid_nucleotides for c in cleaned_seq):
                logger.warning(f"Sequence {i} contains invalid nucleotides, filtering...")
                cleaned_seq = ''.join(c for c in cleaned_seq if c in valid_nucleotides)
            
            # Check minimum length
            if len(cleaned_seq) < 50:
                logger.warning(f"Sequence {i} is very short ({len(cleaned_seq)} bp)")
            
            validated_sequences.append(cleaned_seq)
        
        # Check for reasonable sequence length variation
        lengths = [len(seq) for seq in validated_sequences]
        max_length = max(lengths)
        min_length = min(lengths)
        
        if max_length / min_length > 2.0:
            logger.warning("Large variation in sequence lengths detected")
        
        return validated_sequences
        
    def _design_variant_aware_primers(self, consensus_result: ConsensusResult,
                                    alignment_result: AlignmentResult) -> List[Dict]:
        """
        Design primers that are robust across sequence variants.
        
        Args:
            consensus_result: Consensus analysis results
            alignment_result: MSA results
            
        Returns:
            List of primer sets with variant robustness scores
        """
        # Identify conserved regions suitable for primer design
        conserved_regions = self.consensus_analyzer.identify_conserved_regions(
            consensus_result.conservation_scores,
            min_length=self.parameters.primer_length_range[0]
        )
        
        if not conserved_regions:
            logger.warning("No conserved regions found for primer design")
            return []
        
        primer_sets = []
        
        # Design primers for each conserved region
        for region_start, region_end in conserved_regions:
            try:
                # Extract consensus sequence for this region
                region_consensus = consensus_result.consensus_sequence[region_start:region_end]
                
                # Design RT-LAMP primers using existing primer designer
                # Note: This is a simplified approach - in practice, we'd need to integrate
                # more sophisticated RT-LAMP specific design logic
                primer_candidates = self._generate_primer_candidates(
                    region_consensus, region_start, region_end, consensus_result
                )
                
                if primer_candidates:
                    primer_sets.extend(primer_candidates)
                    
            except Exception as e:
                logger.error(f"Error designing primers for region {region_start}-{region_end}: {e}")
                continue
        
        # Sort primer sets by conservation score
        primer_sets.sort(key=lambda x: x.get('conservation_score', 0), reverse=True)
        
        # Return top candidates
        return primer_sets[:10]  # Limit to top 10 primer sets
        
    def _generate_primer_candidates(self, consensus_seq: str, start: int, end: int,
                                  consensus_result: ConsensusResult) -> List[Dict]:
        """
        Generate primer candidates for a conserved region.
        
        Args:
            consensus_seq: Consensus sequence for the region
            start: Start position in alignment
            end: End position in alignment
            consensus_result: Full consensus analysis
            
        Returns:
            List of primer candidate dictionaries
        """
        candidates = []
        
        # Generate primers of different lengths within the specified range
        min_len, max_len = self.parameters.primer_length_range
        
        for primer_len in range(min_len, min(max_len + 1, len(consensus_seq) + 1)):
            for i in range(len(consensus_seq) - primer_len + 1):
                primer_seq = consensus_seq[i:i + primer_len]
                primer_start = start + i
                primer_end = start + i + primer_len
                
                # Calculate conservation score for this primer
                primer_conservation_scores = consensus_result.conservation_scores[primer_start:primer_end]
                avg_conservation = sum(cs.score for cs in primer_conservation_scores) / len(primer_conservation_scores)
                min_conservation = min(cs.score for cs in primer_conservation_scores)
                
                # Basic primer quality checks
                gc_content = (primer_seq.count('G') + primer_seq.count('C')) / len(primer_seq) * 100
                
                # Skip primers that don't meet basic criteria
                if not (self.parameters.gc_content_range[0] <= gc_content <= self.parameters.gc_content_range[1]):
                    continue
                
                if avg_conservation < self.parameters.min_conservation_threshold:
                    continue
                
                # Calculate melting temperature (simplified)
                tm = self._calculate_tm(primer_seq)
                
                if not (self.parameters.tm_range[0] <= tm <= self.parameters.tm_range[1]):
                    continue
                
                candidate = {
                    'sequence': primer_seq,
                    'start': primer_start,
                    'end': primer_end,
                    'length': primer_len,
                    'gc_content': gc_content,
                    'tm': tm,
                    'conservation_score': avg_conservation,
                    'min_conservation': min_conservation,
                    'type': 'consensus_primer'
                }
                
                candidates.append(candidate)
        
        return candidates
    
    def _calculate_tm(self, sequence: str) -> float:
        """
        Calculate melting temperature using simplified formula.
        
        Args:
            sequence: Primer sequence
            
        Returns:
            Estimated melting temperature in Celsius
        """
        # Simplified Tm calculation (Wallace rule for short sequences)
        if len(sequence) < 14:
            tm = (sequence.count('A') + sequence.count('T')) * 2 + (sequence.count('G') + sequence.count('C')) * 4
        else:
            # More accurate formula for longer sequences
            gc_count = sequence.count('G') + sequence.count('C')
            tm = 64.9 + 41 * (gc_count - 16.4) / len(sequence)
        
        return float(tm)
        
    def _calculate_robustness_scores(self, primer_sets: List[Dict],
                                   aligned_sequences: List[str]) -> Dict[str, float]:
        """
        Calculate robustness scores for primer sets across variants.
        
        Args:
            primer_sets: List of primer sets
            aligned_sequences: Aligned variant sequences
            
        Returns:
            Dictionary of robustness metrics
        """
        if not primer_sets:
            return {}
        
        robustness_metrics = {}
        
        # Calculate overall robustness across all primer sets
        total_conservation = sum(ps.get('conservation_score', 0) for ps in primer_sets)
        avg_conservation = total_conservation / len(primer_sets) if primer_sets else 0
        
        # Calculate primer length distribution
        lengths = [ps.get('length', 0) for ps in primer_sets]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        
        # Calculate GC content distribution
        gc_contents = [ps.get('gc_content', 0) for ps in primer_sets]
        avg_gc_content = sum(gc_contents) / len(gc_contents) if gc_contents else 0
        
        # Calculate Tm distribution
        tms = [ps.get('tm', 0) for ps in primer_sets]
        avg_tm = sum(tms) / len(tms) if tms else 0
        
        # Count primers meeting high conservation threshold
        high_conservation_count = sum(1 for ps in primer_sets if ps.get('conservation_score', 0) >= 0.9)
        high_conservation_percentage = (high_conservation_count / len(primer_sets) * 100) if primer_sets else 0
        
        robustness_metrics = {
            'average_conservation': avg_conservation,
            'average_length': avg_length,
            'average_gc_content': avg_gc_content,
            'average_tm': avg_tm,
            'high_conservation_percentage': high_conservation_percentage,
            'total_primer_candidates': len(primer_sets),
            'num_variants_analyzed': len(aligned_sequences)
        }
        
        return robustness_metrics
        
    def _cross_validate_primers(self, primer_sets: List[Dict],
                              sequences: List[str]) -> Dict[str, Dict]:
        """
        Cross-validate primer performance across all input variants.
        
        Args:
            primer_sets: List of primer sets
            sequences: Original variant sequences
            
        Returns:
            Cross-validation results for each primer set
        """
        if not primer_sets or not sequences:
            return {}
        
        cross_validation_results = {}
        
        for i, primer_set in enumerate(primer_sets):
            primer_seq = primer_set.get('sequence', '')
            if not primer_seq:
                continue
            
            validation_results = {
                'primer_sequence': primer_seq,
                'matches_per_variant': [],
                'binding_efficiency': 0.0,
                'cross_reactivity': 0.0,
                'variant_coverage': 0.0
            }
            
            successful_bindings = 0
            
            # Test primer against each variant
            for seq in sequences:
                # Simple exact match search (in practice, would use more sophisticated alignment)
                matches = seq.upper().count(primer_seq)
                validation_results['matches_per_variant'].append(matches)
                
                if matches > 0:
                    successful_bindings += 1
            
            # Calculate metrics
            total_matches = sum(validation_results['matches_per_variant'])
            validation_results['binding_efficiency'] = total_matches / len(sequences) if sequences else 0
            validation_results['variant_coverage'] = (successful_bindings / len(sequences) * 100) if sequences else 0
            
            # Calculate cross-reactivity (simplified)
            validation_results['cross_reactivity'] = min(100.0, total_matches / len(sequences) * 10)
            
            cross_validation_results[f'primer_set_{i}'] = validation_results
        
        return cross_validation_results

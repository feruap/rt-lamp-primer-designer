
"""
Consensus analysis module for RT-LAMP primer design.

Provides functionality for analyzing sequence conservation, variant frequencies,
and primer region stability across multiple sequences.
"""

from typing import List, Dict, Tuple, Optional
import logging
import math
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class ConservationScore:
    """Conservation score for a sequence position."""
    position: int
    score: float
    dominant_nucleotide: str
    frequency: float
    variants: Dict[str, int]


@dataclass
class ConsensusResult:
    """Result of consensus sequence analysis."""
    consensus_sequence: str
    conservation_scores: List[ConservationScore]
    variant_frequencies: Dict[int, Dict[str, float]]
    stability_metrics: Dict[str, float]


class ConsensusAnalyzer:
    """
    Consensus sequence analysis for variant-aware primer design.
    
    Analyzes conservation patterns, variant frequencies, and stability
    metrics across multiple aligned sequences.
    """
    
    def __init__(self, min_conservation_threshold: float = 0.8):
        """
        Initialize consensus analyzer.
        
        Args:
            min_conservation_threshold: Minimum conservation score for stable regions
        """
        self.min_conservation_threshold = min_conservation_threshold
        
    def generate_consensus(self, aligned_sequences: List[str]) -> ConsensusResult:
        """
        Generate consensus sequence and analysis from aligned sequences.
        
        Args:
            aligned_sequences: List of aligned nucleotide sequences
            
        Returns:
            ConsensusResult with consensus sequence and analysis
        """
        if not aligned_sequences:
            raise ValueError("No sequences provided for consensus generation")
        
        # Calculate conservation scores
        conservation_scores = self.calculate_conservation_scores(aligned_sequences)
        
        # Generate consensus sequence
        consensus_sequence = self._build_consensus_sequence(aligned_sequences, conservation_scores)
        
        # Analyze variant frequencies
        variant_frequencies = self.analyze_variant_frequencies(aligned_sequences)
        
        # Calculate stability metrics
        stability_metrics = self._calculate_stability_metrics(aligned_sequences, conservation_scores)
        
        return ConsensusResult(
            consensus_sequence=consensus_sequence,
            conservation_scores=conservation_scores,
            variant_frequencies=variant_frequencies,
            stability_metrics=stability_metrics
        )
        
    def calculate_conservation_scores(self, aligned_sequences: List[str]) -> List[ConservationScore]:
        """
        Calculate conservation scores for each position in the alignment.
        
        Args:
            aligned_sequences: List of aligned sequences
            
        Returns:
            List of conservation scores for each position
        """
        if not aligned_sequences:
            return []
        
        length = len(aligned_sequences[0])
        conservation_scores = []
        
        for pos in range(length):
            column = [seq[pos] for seq in aligned_sequences if pos < len(seq)]
            non_gap_column = [c for c in column if c != '-']
            
            if not non_gap_column:
                # All gaps at this position
                conservation_scores.append(ConservationScore(
                    position=pos,
                    score=0.0,
                    dominant_nucleotide='-',
                    frequency=1.0,
                    variants={'-': len(column)}
                ))
                continue
            
            # Count nucleotide frequencies
            nucleotide_counts = Counter(non_gap_column)
            total_non_gaps = len(non_gap_column)
            
            # Find dominant nucleotide
            dominant_nucleotide = nucleotide_counts.most_common(1)[0][0]
            dominant_frequency = nucleotide_counts[dominant_nucleotide] / total_non_gaps
            
            # Calculate Shannon entropy for conservation score
            entropy = 0.0
            for count in nucleotide_counts.values():
                if count > 0:
                    p = count / total_non_gaps
                    entropy -= p * math.log2(p)
            
            # Convert entropy to conservation score (0-1 scale, higher = more conserved)
            max_entropy = math.log2(min(4, len(nucleotide_counts)))  # Max possible entropy
            conservation_score = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 1.0
            
            # Include gap information in variants
            all_variants = dict(nucleotide_counts)
            gap_count = len(column) - total_non_gaps
            if gap_count > 0:
                all_variants['-'] = gap_count
            
            conservation_scores.append(ConservationScore(
                position=pos,
                score=conservation_score,
                dominant_nucleotide=dominant_nucleotide,
                frequency=dominant_frequency,
                variants=all_variants
            ))
        
        return conservation_scores
        
    def analyze_variant_frequencies(self, aligned_sequences: List[str]) -> Dict[int, Dict[str, float]]:
        """
        Analyze variant frequencies at each position.
        
        Args:
            aligned_sequences: List of aligned sequences
            
        Returns:
            Dictionary mapping positions to variant frequencies
        """
        if not aligned_sequences:
            return {}
        
        length = len(aligned_sequences[0])
        variant_frequencies = {}
        
        for pos in range(length):
            column = [seq[pos] for seq in aligned_sequences if pos < len(seq)]
            nucleotide_counts = Counter(column)
            total = len(column)
            
            # Calculate frequencies
            frequencies = {nucleotide: count / total for nucleotide, count in nucleotide_counts.items()}
            variant_frequencies[pos] = frequencies
        
        return variant_frequencies
        
    def assess_primer_region_stability(self, aligned_sequences: List[str], 
                                     start: int, end: int) -> Dict[str, float]:
        """
        Assess stability of a primer region across variants.
        
        Args:
            aligned_sequences: List of aligned sequences
            start: Start position of primer region
            end: End position of primer region
            
        Returns:
            Dictionary of stability metrics
        """
        if not aligned_sequences or start >= end:
            return {}
        
        # Extract primer region from all sequences
        primer_regions = []
        for seq in aligned_sequences:
            if end <= len(seq):
                primer_regions.append(seq[start:end])
        
        if not primer_regions:
            return {}
        
        # Calculate conservation scores for the region
        region_conservation = self.calculate_conservation_scores(primer_regions)
        
        # Calculate stability metrics
        avg_conservation = sum(cs.score for cs in region_conservation) / len(region_conservation)
        min_conservation = min(cs.score for cs in region_conservation)
        
        # Calculate sequence identity within region
        identical_sequences = 0
        reference_seq = primer_regions[0]
        for seq in primer_regions:
            if seq == reference_seq:
                identical_sequences += 1
        
        identity_percentage = (identical_sequences / len(primer_regions)) * 100
        
        # Calculate gap percentage in region
        total_chars = sum(len(seq) for seq in primer_regions)
        total_gaps = sum(seq.count('-') for seq in primer_regions)
        gap_percentage = (total_gaps / total_chars * 100) if total_chars > 0 else 0
        
        # Calculate variant diversity (number of unique sequences)
        unique_sequences = len(set(primer_regions))
        diversity_index = unique_sequences / len(primer_regions)
        
        return {
            'average_conservation': avg_conservation,
            'minimum_conservation': min_conservation,
            'identity_percentage': identity_percentage,
            'gap_percentage': gap_percentage,
            'diversity_index': diversity_index,
            'region_length': end - start,
            'num_variants': len(primer_regions)
        }
        
    def identify_conserved_regions(self, conservation_scores: List[ConservationScore],
                                 min_length: int = 20) -> List[Tuple[int, int]]:
        """
        Identify conserved regions suitable for primer design.
        
        Args:
            conservation_scores: List of conservation scores
            min_length: Minimum length for conserved regions
            
        Returns:
            List of (start, end) tuples for conserved regions
        """
        if not conservation_scores:
            return []
        
        conserved_regions = []
        current_start = None
        
        for i, cs in enumerate(conservation_scores):
            if cs.score >= self.min_conservation_threshold:
                if current_start is None:
                    current_start = i
            else:
                if current_start is not None:
                    # End of conserved region
                    region_length = i - current_start
                    if region_length >= min_length:
                        conserved_regions.append((current_start, i))
                    current_start = None
        
        # Check if we ended in a conserved region
        if current_start is not None:
            region_length = len(conservation_scores) - current_start
            if region_length >= min_length:
                conserved_regions.append((current_start, len(conservation_scores)))
        
        return conserved_regions
    
    def _build_consensus_sequence(self, aligned_sequences: List[str], 
                                conservation_scores: List[ConservationScore]) -> str:
        """
        Build consensus sequence from aligned sequences and conservation scores.
        
        Args:
            aligned_sequences: List of aligned sequences
            conservation_scores: Conservation scores for each position
            
        Returns:
            Consensus sequence string
        """
        consensus = []
        
        for cs in conservation_scores:
            if cs.dominant_nucleotide == '-':
                # Skip gap-only positions in consensus
                continue
            elif cs.frequency >= 0.5:  # Majority rule
                consensus.append(cs.dominant_nucleotide)
            else:
                # Use IUPAC ambiguity codes for mixed positions
                non_gap_variants = {nuc: count for nuc, count in cs.variants.items() if nuc != '-'}
                if len(non_gap_variants) <= 1:
                    consensus.append(cs.dominant_nucleotide)
                else:
                    # Use most common nucleotide for simplicity
                    consensus.append(cs.dominant_nucleotide)
        
        return ''.join(consensus)
    
    def _calculate_stability_metrics(self, aligned_sequences: List[str], 
                                   conservation_scores: List[ConservationScore]) -> Dict[str, float]:
        """
        Calculate overall stability metrics for the alignment.
        
        Args:
            aligned_sequences: List of aligned sequences
            conservation_scores: Conservation scores for each position
            
        Returns:
            Dictionary of stability metrics
        """
        if not conservation_scores:
            return {}
        
        # Overall conservation statistics
        avg_conservation = sum(cs.score for cs in conservation_scores) / len(conservation_scores)
        min_conservation = min(cs.score for cs in conservation_scores)
        max_conservation = max(cs.score for cs in conservation_scores)
        
        # Count highly conserved positions
        highly_conserved = sum(1 for cs in conservation_scores if cs.score >= 0.9)
        moderately_conserved = sum(1 for cs in conservation_scores if 0.7 <= cs.score < 0.9)
        poorly_conserved = sum(1 for cs in conservation_scores if cs.score < 0.7)
        
        # Calculate conservation distribution
        total_positions = len(conservation_scores)
        
        return {
            'average_conservation': avg_conservation,
            'minimum_conservation': min_conservation,
            'maximum_conservation': max_conservation,
            'highly_conserved_percentage': (highly_conserved / total_positions * 100),
            'moderately_conserved_percentage': (moderately_conserved / total_positions * 100),
            'poorly_conserved_percentage': (poorly_conserved / total_positions * 100),
            'total_positions': total_positions,
            'num_sequences': len(aligned_sequences)
        }

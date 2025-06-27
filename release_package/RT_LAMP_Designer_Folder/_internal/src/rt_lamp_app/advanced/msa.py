
"""
Multiple Sequence Alignment (MSA) module for RT-LAMP primer design.

Provides functionality for aligning multiple sequences and assessing alignment quality.
"""

from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AlignmentResult:
    """Result of multiple sequence alignment."""
    aligned_sequences: List[str]
    alignment_score: float
    gap_percentage: float
    conservation_scores: List[float]
    quality_metrics: Dict[str, float]


class MultipleSequenceAlignment:
    """
    Multiple sequence alignment implementation for consensus primer design.
    
    Implements progressive alignment algorithm with gap penalties and
    similarity scoring for nucleotide sequences.
    """
    
    def __init__(self, gap_penalty: float = -2.0, match_score: float = 2.0, 
                 mismatch_penalty: float = -1.0):
        """
        Initialize MSA with scoring parameters.
        
        Args:
            gap_penalty: Penalty for introducing gaps
            match_score: Score for matching nucleotides
            mismatch_penalty: Penalty for mismatched nucleotides
        """
        self.gap_penalty = gap_penalty
        self.match_score = match_score
        self.mismatch_penalty = mismatch_penalty
        
    def align(self, sequences: List[str]) -> AlignmentResult:
        """
        Perform multiple sequence alignment on input sequences.
        
        Args:
            sequences: List of nucleotide sequences to align
            
        Returns:
            AlignmentResult containing aligned sequences and metrics
        """
        if len(sequences) < 2:
            raise ValueError("At least 2 sequences required for alignment")
        
        if len(sequences) == 2:
            # Simple pairwise alignment
            aligned_seq1, aligned_seq2, score = self._pairwise_align(sequences[0], sequences[1])
            aligned_sequences = [aligned_seq1, aligned_seq2]
        else:
            # Progressive alignment for multiple sequences
            aligned_sequences = self._progressive_align(sequences)
        
        # Calculate metrics
        alignment_score = self._calculate_overall_score(aligned_sequences)
        gap_percentage = self._calculate_gap_percentage(aligned_sequences)
        conservation_scores = self._calculate_conservation_scores(aligned_sequences)
        quality_metrics = self._assess_alignment_quality(aligned_sequences)
        
        return AlignmentResult(
            aligned_sequences=aligned_sequences,
            alignment_score=alignment_score,
            gap_percentage=gap_percentage,
            conservation_scores=conservation_scores,
            quality_metrics=quality_metrics
        )
        
    def _pairwise_align(self, seq1: str, seq2: str) -> Tuple[str, str, float]:
        """
        Perform pairwise alignment using dynamic programming (Needleman-Wunsch).
        
        Args:
            seq1: First sequence
            seq2: Second sequence
            
        Returns:
            Tuple of (aligned_seq1, aligned_seq2, alignment_score)
        """
        m, n = len(seq1), len(seq2)
        
        # Initialize scoring matrix
        dp = [[0.0 for _ in range(n + 1)] for _ in range(m + 1)]
        
        # Initialize first row and column
        for i in range(1, m + 1):
            dp[i][0] = i * self.gap_penalty
        for j in range(1, n + 1):
            dp[0][j] = j * self.gap_penalty
        
        # Fill the scoring matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                match_score = self.match_score if seq1[i-1] == seq2[j-1] else self.mismatch_penalty
                dp[i][j] = max(
                    dp[i-1][j-1] + match_score,  # Match/mismatch
                    dp[i-1][j] + self.gap_penalty,  # Gap in seq2
                    dp[i][j-1] + self.gap_penalty   # Gap in seq1
                )
        
        # Traceback to get alignment
        aligned_seq1, aligned_seq2 = self._traceback(seq1, seq2, dp)
        
        return aligned_seq1, aligned_seq2, dp[m][n]
    
    def _traceback(self, seq1: str, seq2: str, dp: List[List[float]]) -> Tuple[str, str]:
        """Traceback to reconstruct alignment from scoring matrix."""
        aligned_seq1, aligned_seq2 = "", ""
        i, j = len(seq1), len(seq2)
        
        while i > 0 or j > 0:
            if i > 0 and j > 0:
                match_score = self.match_score if seq1[i-1] == seq2[j-1] else self.mismatch_penalty
                if dp[i][j] == dp[i-1][j-1] + match_score:
                    aligned_seq1 = seq1[i-1] + aligned_seq1
                    aligned_seq2 = seq2[j-1] + aligned_seq2
                    i -= 1
                    j -= 1
                elif dp[i][j] == dp[i-1][j] + self.gap_penalty:
                    aligned_seq1 = seq1[i-1] + aligned_seq1
                    aligned_seq2 = "-" + aligned_seq2
                    i -= 1
                else:
                    aligned_seq1 = "-" + aligned_seq1
                    aligned_seq2 = seq2[j-1] + aligned_seq2
                    j -= 1
            elif i > 0:
                aligned_seq1 = seq1[i-1] + aligned_seq1
                aligned_seq2 = "-" + aligned_seq2
                i -= 1
            else:
                aligned_seq1 = "-" + aligned_seq1
                aligned_seq2 = seq2[j-1] + aligned_seq2
                j -= 1
        
        return aligned_seq1, aligned_seq2
    
    def _progressive_align(self, sequences: List[str]) -> List[str]:
        """
        Perform progressive alignment using guide tree approach.
        
        Args:
            sequences: List of sequences to align
            
        Returns:
            List of aligned sequences
        """
        # Calculate similarity matrix
        similarity_matrix = self._calculate_similarity_matrix(sequences)
        
        # Build guide tree using simple clustering
        clusters = [[i] for i in range(len(sequences))]
        aligned_groups = {i: [sequences[i]] for i in range(len(sequences))}
        
        while len(clusters) > 1:
            # Find most similar pair
            best_score = float('-inf')
            best_pair = (0, 1)
            
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    # Calculate average similarity between clusters
                    total_score = 0
                    count = 0
                    for seq_i in clusters[i]:
                        for seq_j in clusters[j]:
                            total_score += similarity_matrix[seq_i][seq_j]
                            count += 1
                    avg_score = total_score / count if count > 0 else 0
                    
                    if avg_score > best_score:
                        best_score = avg_score
                        best_pair = (i, j)
            
            # Merge best pair
            i, j = best_pair
            if i > j:
                i, j = j, i  # Ensure i < j
            
            # Align the two groups
            group1 = aligned_groups[clusters[i][0]]
            group2 = aligned_groups[clusters[j][0]]
            merged_group = self._align_groups(group1, group2)
            
            # Update data structures
            new_cluster = clusters[i] + clusters[j]
            aligned_groups[new_cluster[0]] = merged_group
            
            # Remove old clusters (remove j first since j > i)
            del clusters[j]
            del clusters[i]
            clusters.append(new_cluster)
        
        return aligned_groups[clusters[0][0]]
    
    def _align_groups(self, group1: List[str], group2: List[str]) -> List[str]:
        """Align two groups of already aligned sequences."""
        if len(group1) == 1 and len(group2) == 1:
            aligned_seq1, aligned_seq2, _ = self._pairwise_align(group1[0], group2[0])
            return [aligned_seq1, aligned_seq2]
        
        # For simplicity, align first sequence of each group and apply gaps to others
        seq1 = group1[0]
        seq2 = group2[0]
        aligned_seq1, aligned_seq2, _ = self._pairwise_align(seq1, seq2)
        
        # Apply same gap pattern to other sequences in groups
        result = []
        
        # Process group1
        gap_pattern1 = self._extract_gap_pattern(seq1, aligned_seq1)
        for seq in group1:
            result.append(self._apply_gap_pattern(seq, gap_pattern1))
        
        # Process group2
        gap_pattern2 = self._extract_gap_pattern(seq2, aligned_seq2)
        for seq in group2:
            result.append(self._apply_gap_pattern(seq, gap_pattern2))
        
        return result
    
    def _extract_gap_pattern(self, original: str, aligned: str) -> List[int]:
        """Extract gap positions from alignment."""
        gaps = []
        orig_pos = 0
        for i, char in enumerate(aligned):
            if char == '-':
                gaps.append(i)
            else:
                orig_pos += 1
        return gaps
    
    def _apply_gap_pattern(self, sequence: str, gap_pattern: List[int]) -> str:
        """Apply gap pattern to a sequence."""
        result = list(sequence)
        for gap_pos in sorted(gap_pattern, reverse=True):
            if gap_pos <= len(result):
                result.insert(gap_pos, '-')
        return ''.join(result)
        
    def _calculate_similarity_matrix(self, sequences: List[str]) -> List[List[float]]:
        """
        Calculate pairwise similarity matrix for sequences.
        
        Args:
            sequences: List of sequences
            
        Returns:
            2D matrix of pairwise similarity scores
        """
        n = len(sequences)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(i, n):
                if i == j:
                    matrix[i][j] = float('inf')  # Self-similarity
                else:
                    _, _, score = self._pairwise_align(sequences[i], sequences[j])
                    matrix[i][j] = matrix[j][i] = score
        
        return matrix
    
    def _calculate_overall_score(self, aligned_sequences: List[str]) -> float:
        """Calculate overall alignment score."""
        if not aligned_sequences:
            return 0.0
        
        total_score = 0.0
        length = len(aligned_sequences[0])
        
        for pos in range(length):
            column = [seq[pos] for seq in aligned_sequences if pos < len(seq)]
            # Score based on conservation at this position
            if len(set(column)) == 1 and column[0] != '-':
                total_score += self.match_score
            else:
                total_score += self.mismatch_penalty
        
        return total_score / length if length > 0 else 0.0
    
    def _calculate_gap_percentage(self, aligned_sequences: List[str]) -> float:
        """Calculate percentage of gaps in alignment."""
        if not aligned_sequences:
            return 0.0
        
        total_chars = sum(len(seq) for seq in aligned_sequences)
        total_gaps = sum(seq.count('-') for seq in aligned_sequences)
        
        return (total_gaps / total_chars * 100) if total_chars > 0 else 0.0
    
    def _calculate_conservation_scores(self, aligned_sequences: List[str]) -> List[float]:
        """Calculate conservation score for each position using Shannon entropy."""
        if not aligned_sequences:
            return []
        
        length = len(aligned_sequences[0])
        conservation_scores = []
        
        for pos in range(length):
            column = [seq[pos] for seq in aligned_sequences if pos < len(seq)]
            # Calculate Shannon entropy
            from collections import Counter
            counts = Counter(column)
            total = len(column)
            
            entropy = 0.0
            for count in counts.values():
                if count > 0:
                    p = count / total
                    entropy -= p * (p.bit_length() - 1) if p > 0 else 0
            
            # Convert entropy to conservation score (lower entropy = higher conservation)
            conservation_scores.append(2.0 - entropy)  # Max entropy for 4 nucleotides is 2
        
        return conservation_scores
        
    def _assess_alignment_quality(self, aligned_sequences: List[str]) -> Dict[str, float]:
        """
        Assess the quality of the alignment.
        
        Args:
            aligned_sequences: List of aligned sequences
            
        Returns:
            Dictionary of quality metrics
        """
        if not aligned_sequences:
            return {}
        
        length = len(aligned_sequences[0])
        num_sequences = len(aligned_sequences)
        
        # Calculate various quality metrics
        total_matches = 0
        total_positions = 0
        conserved_positions = 0
        
        for pos in range(length):
            column = [seq[pos] for seq in aligned_sequences if pos < len(seq)]
            non_gap_column = [c for c in column if c != '-']
            
            if len(non_gap_column) > 1:
                total_positions += 1
                if len(set(non_gap_column)) == 1:
                    total_matches += 1
                    conserved_positions += 1
        
        identity = (total_matches / total_positions * 100) if total_positions > 0 else 0
        conservation = (conserved_positions / length * 100) if length > 0 else 0
        
        return {
            'identity_percentage': identity,
            'conservation_percentage': conservation,
            'alignment_length': length,
            'num_sequences': num_sequences,
            'gap_percentage': self._calculate_gap_percentage(aligned_sequences)
        }

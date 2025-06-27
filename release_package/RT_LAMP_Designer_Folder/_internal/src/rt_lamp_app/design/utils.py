
"""
Utility functions for RT-LAMP primer design.
"""

from typing import Tuple, Dict, Any
import re

from rt_lamp_app.design.exceptions import GeometricConstraintError


def reverse_complement(sequence: str) -> str:
    """
    Calculate reverse complement of DNA sequence.
    
    Args:
        sequence: DNA sequence string
        
    Returns:
        Reverse complement sequence
    """
    complement_map = {
        'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C',
        'R': 'Y', 'Y': 'R', 'K': 'M', 'M': 'K', 
        'S': 'S', 'W': 'W', 'B': 'V', 'D': 'H', 
        'H': 'D', 'V': 'B', 'N': 'N'
    }
    
    try:
        complement = ''.join(complement_map[base.upper()] for base in sequence)
        return complement[::-1]
    except KeyError as e:
        raise ValueError(f"Invalid nucleotide in sequence: {e}")


def calculate_distance(pos1: int, pos2: int) -> int:
    """
    Calculate distance between two positions.
    
    Args:
        pos1: First position
        pos2: Second position
        
    Returns:
        Absolute distance between positions
    """
    return abs(pos2 - pos1)


def validate_primer_geometry(f3_start: int, f3_end: int, b3_start: int, b3_end: int,
                           fip_start: int, fip_end: int, bip_start: int, bip_end: int) -> None:
    """
    Validate RT-LAMP primer geometric constraints (simplified version for tests).
    
    Args:
        f3_start, f3_end: F3 primer positions
        b3_start, b3_end: B3 primer positions  
        fip_start, fip_end: FIP primer positions
        bip_start, bip_end: BIP primer positions
        
    Raises:
        GeometricConstraintError: If constraints are violated
    """
    # Check for overlaps
    if f3_end >= fip_start:
        raise GeometricConstraintError("F3_FIP_overlap", "no overlap", f"F3 ends at {f3_end}, FIP starts at {fip_start}")
    
    if fip_end >= bip_start:
        raise GeometricConstraintError("FIP_BIP_overlap", "no overlap", f"FIP ends at {fip_end}, BIP starts at {bip_start}")
    
    if bip_end >= b3_start:
        raise GeometricConstraintError("BIP_B3_overlap", "no overlap", f"BIP ends at {bip_end}, B3 starts at {b3_start}")
    
    # Check amplicon size (simplified)
    amplicon_size = b3_start - f3_end
    if amplicon_size < 120:
        raise GeometricConstraintError("amplicon_size", ">=120", str(amplicon_size))


def validate_primer_geometry_full(regions: Dict[str, Tuple[int, int]], 
                           constraints: Dict[str, Any]) -> None:
    """
    Validate RT-LAMP primer geometric constraints.
    
    Args:
        regions: Dictionary of primer regions with (start, end) positions
        constraints: Dictionary of geometric constraints
        
    Raises:
        GeometricConstraintError: If constraints are violated
    """
    # Extract regions
    f3_region = regions.get('F3')
    b3_region = regions.get('B3') 
    f2_region = regions.get('F2')
    b2_region = regions.get('B2')
    f1c_region = regions.get('F1c')
    b1c_region = regions.get('B1c')
    
    # Validate F3 length
    if f3_region:
        f3_length = f3_region[1] - f3_region[0] + 1
        min_f3 = constraints.get('F3_length_min', 15)
        max_f3 = constraints.get('F3_length_max', 25)
        if not (min_f3 <= f3_length <= max_f3):
            raise GeometricConstraintError(
                "F3_length", f"{min_f3}-{max_f3}", str(f3_length)
            )
    
    # Validate B3 length
    if b3_region:
        b3_length = b3_region[1] - b3_region[0] + 1
        min_b3 = constraints.get('B3_length_min', 15)
        max_b3 = constraints.get('B3_length_max', 25)
        if not (min_b3 <= b3_length <= max_b3):
            raise GeometricConstraintError(
                "B3_length", f"{min_b3}-{max_b3}", str(b3_length)
            )
    
    # Validate FIP length (F1c + F2)
    if f1c_region and f2_region:
        fip_length = (f1c_region[1] - f1c_region[0] + 1) + (f2_region[1] - f2_region[0] + 1)
        min_fip = constraints.get('FIP_length_min', 35)
        max_fip = constraints.get('FIP_length_max', 50)
        if not (min_fip <= fip_length <= max_fip):
            raise GeometricConstraintError(
                "FIP_length", f"{min_fip}-{max_fip}", str(fip_length)
            )
    
    # Validate BIP length (B1c + B2)
    if b1c_region and b2_region:
        bip_length = (b1c_region[1] - b1c_region[0] + 1) + (b2_region[1] - b2_region[0] + 1)
        min_bip = constraints.get('BIP_length_min', 35)
        max_bip = constraints.get('BIP_length_max', 50)
        if not (min_bip <= bip_length <= max_bip):
            raise GeometricConstraintError(
                "BIP_length", f"{min_bip}-{max_bip}", str(bip_length)
            )
    
    # Validate F2-B2 amplicon size
    if f2_region and b2_region:
        amplicon_size = b2_region[0] - f2_region[1] - 1
        min_amplicon = constraints.get('F2_B2_amplicon_min', 120)
        max_amplicon = constraints.get('F2_B2_amplicon_max', 200)
        if not (min_amplicon <= amplicon_size <= max_amplicon):
            raise GeometricConstraintError(
                "F2_B2_amplicon", f"{min_amplicon}-{max_amplicon}", str(amplicon_size)
            )


def calculate_gc_content(sequence: str) -> float:
    """
    Calculate GC content percentage.
    
    Args:
        sequence: DNA sequence
        
    Returns:
        GC content as percentage (0-100)
    """
    if not sequence:
        return 0.0
    
    gc_count = sequence.upper().count('G') + sequence.upper().count('C')
    return (gc_count / len(sequence)) * 100


def has_excessive_repeats(sequence: str, max_repeat: int = 4) -> bool:
    """
    Check for excessive nucleotide repeats.
    
    Args:
        sequence: DNA sequence
        max_repeat: Maximum allowed consecutive repeats
        
    Returns:
        True if excessive repeats found
    """
    for base in 'ATGC':
        if base * (max_repeat + 1) in sequence.upper():
            return True
    return False


def has_strong_secondary_structure(sequence: str, max_hairpin_dg: float = -3.0) -> bool:
    """
    Simple check for strong secondary structures.
    
    Args:
        sequence: DNA sequence
        max_hairpin_dg: Maximum allowed hairpin ΔG (kcal/mol)
        
    Returns:
        True if strong secondary structure predicted
    """
    # Simple palindrome detection for hairpins
    seq_len = len(sequence)
    
    for i in range(seq_len - 6):  # Minimum hairpin size
        for j in range(i + 4, min(i + 15, seq_len)):  # Check up to 15bp stems
            stem_len = min(4, (seq_len - j), i + 1)
            if stem_len < 3:
                continue
                
            left = sequence[i-stem_len+1:i+1]
            right = sequence[j:j+stem_len]
            
            # Check complementarity
            if left == reverse_complement(right):
                # Rough ΔG estimate: -1.5 kcal/mol per bp + loop penalty
                estimated_dg = -1.5 * stem_len + 4.0  # Rough loop penalty
                if estimated_dg < max_hairpin_dg:
                    return True
    
    return False


def validate_sequence_composition(sequence: str, 
                                min_gc: float = 30.0, 
                                max_gc: float = 70.0,
                                max_homopolymer: int = 4,
                                check_repeats: bool = False,
                                check_dinuc_repeats: bool = False) -> Tuple[bool, list]:
    """
    Validate sequence composition for primer design.
    
    Args:
        sequence: DNA sequence
        min_gc: Minimum GC content percentage
        max_gc: Maximum GC content percentage
        max_homopolymer: Maximum homopolymer length
        check_repeats: Whether to check for repetitive sequences
        check_dinuc_repeats: Whether to check for dinucleotide repeats
        
    Returns:
        Tuple of (is_valid, list_of_issues)
        
    Raises:
        ValueError: If parameters are invalid or sequence has issues
    """
    # Validate parameters
    if min_gc < 0 or max_gc > 100 or min_gc > max_gc:
        raise ValueError("Invalid GC content parameters")
    
    if max_homopolymer <= 0:
        raise ValueError("Invalid homopolymer length")
    
    issues = []
    
    # Check GC content
    gc_content = calculate_gc_content(sequence)
    if gc_content < min_gc or gc_content > max_gc:
        if min_gc > gc_content:
            raise ValueError(f"GC content too low: {gc_content:.1f}% (minimum: {min_gc}%)")
        else:
            raise ValueError(f"GC content too high: {gc_content:.1f}% (maximum: {max_gc}%)")
    
    # Check for excessive repeats
    if check_repeats and has_excessive_repeats(sequence, max_homopolymer):
        raise ValueError("Excessive nucleotide repeats detected")
    
    # Check for dinucleotide repeats
    if check_dinuc_repeats:
        for dinuc in ['AT', 'TA', 'GC', 'CG']:
            if (dinuc * 4) in sequence.upper():  # 8+ consecutive dinucleotide repeats
                raise ValueError(f"Excessive {dinuc} dinucleotide repeats detected")
    
    # Check homopolymer runs
    for base in 'ATGC':
        if (base * (max_homopolymer + 1)) in sequence.upper():
            raise ValueError(f"Homopolymer run too long: {base} repeated {max_homopolymer + 1}+ times")
    
    # Check for strong secondary structures
    if has_strong_secondary_structure(sequence):
        issues.append("Strong secondary structure predicted")
    
    # Check 3'-end stability (avoid G/C at 3'-end for some applications)
    if len(sequence) > 0 and sequence[-1] in 'GC':
        issues.append("Strong 3'-end (G/C) may cause non-specific priming")
    
    return len(issues) == 0, issues

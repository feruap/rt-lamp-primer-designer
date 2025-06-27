"""
Tests for design utilities module.
"""

import pytest

from rt_lamp_app.design.utils import (
    reverse_complement, calculate_distance, validate_primer_geometry,
    calculate_gc_content, validate_sequence_composition
)
from rt_lamp_app.design.exceptions import GeometricConstraintError


class TestReverseComplement:
    """Test reverse complement function."""
    
    def test_simple_sequence(self):
        """Test reverse complement of simple sequence."""
        sequence = "ATCG"
        expected = "CGAT"
        result = reverse_complement(sequence)
        assert result == expected
    
    def test_longer_sequence(self):
        """Test reverse complement of longer sequence."""
        sequence = "ATCGATCGATCGATCG"
        expected = "CGATCGATCGATCGAT"
        result = reverse_complement(sequence)
        assert result == expected
    
    def test_ambiguous_bases(self):
        """Test reverse complement with ambiguous bases."""
        sequence = "ATCGNRYKMSWBDHV"
        expected = "BDHVWSKMRYNCGAT"  # Fixed: S complements to S, W to W
        result = reverse_complement(sequence)
        assert result == expected
    
    def test_lowercase_sequence(self):
        """Test reverse complement with lowercase sequence."""
        sequence = "atcg"
        expected = "CGAT"
        result = reverse_complement(sequence)
        assert result == expected
    
    def test_mixed_case_sequence(self):
        """Test reverse complement with mixed case sequence."""
        sequence = "AtCg"
        expected = "CGAT"
        result = reverse_complement(sequence)
        assert result == expected
    
    def test_empty_sequence(self):
        """Test reverse complement of empty sequence."""
        sequence = ""
        expected = ""
        result = reverse_complement(sequence)
        assert result == expected
    
    def test_invalid_nucleotide(self):
        """Test reverse complement with invalid nucleotide."""
        sequence = "ATCGX"  # X is not a valid nucleotide
        
        with pytest.raises(ValueError, match="Invalid nucleotide"):
            reverse_complement(sequence)
    
    def test_palindromic_sequence(self):
        """Test reverse complement of palindromic sequence."""
        sequence = "GAATTC"  # EcoRI site
        expected = "GAATTC"  # Should be the same
        result = reverse_complement(sequence)
        assert result == expected


class TestCalculateDistance:
    """Test distance calculation function."""
    
    def test_positive_distance(self):
        """Test distance calculation with positive difference."""
        pos1 = 10
        pos2 = 20
        expected = 10
        result = calculate_distance(pos1, pos2)
        assert result == expected
    
    def test_negative_distance(self):
        """Test distance calculation with negative difference."""
        pos1 = 20
        pos2 = 10
        expected = 10
        result = calculate_distance(pos1, pos2)
        assert result == expected
    
    def test_zero_distance(self):
        """Test distance calculation with same positions."""
        pos1 = 15
        pos2 = 15
        expected = 0
        result = calculate_distance(pos1, pos2)
        assert result == expected
    
    def test_large_distance(self):
        """Test distance calculation with large numbers."""
        pos1 = 1000
        pos2 = 5000
        expected = 4000
        result = calculate_distance(pos1, pos2)
        assert result == expected


class TestValidatePrimerGeometry:
    """Test primer geometry validation function."""
    
    def test_valid_geometry(self):
        """Test validation of valid primer geometry."""
        # Mock primer positions that should be valid
        f3_start, f3_end = 0, 20
        b3_start, b3_end = 180, 200
        fip_start, fip_end = 25, 60
        bip_start, bip_end = 120, 155
        
        # Should not raise an exception for valid geometry
        try:
            validate_primer_geometry(
                f3_start, f3_end, b3_start, b3_end,
                fip_start, fip_end, bip_start, bip_end
            )
        except GeometricConstraintError:
            pytest.fail("Valid geometry should not raise GeometricConstraintError")
    
    def test_overlapping_primers(self):
        """Test validation with overlapping primers."""
        # F3 and FIP overlap
        f3_start, f3_end = 0, 30
        b3_start, b3_end = 180, 200
        fip_start, fip_end = 25, 60  # Overlaps with F3
        bip_start, bip_end = 120, 155
        
        with pytest.raises(GeometricConstraintError):
            validate_primer_geometry(
                f3_start, f3_end, b3_start, b3_end,
                fip_start, fip_end, bip_start, bip_end
            )
    
    def test_insufficient_amplicon_size(self):
        """Test validation with insufficient amplicon size."""
        # Primers too close together
        f3_start, f3_end = 0, 20
        b3_start, b3_end = 80, 100  # Too close to F3
        fip_start, fip_end = 25, 60
        bip_start, bip_end = 65, 75
        
        with pytest.raises(GeometricConstraintError):
            validate_primer_geometry(
                f3_start, f3_end, b3_start, b3_end,
                fip_start, fip_end, bip_start, bip_end
            )


class TestCalculateGcContent:
    """Test GC content calculation function."""
    
    def test_all_gc(self):
        """Test GC content calculation for all GC sequence."""
        sequence = "GCGCGCGC"
        expected = 100.0
        result = calculate_gc_content(sequence)
        assert result == expected
    
    def test_all_at(self):
        """Test GC content calculation for all AT sequence."""
        sequence = "ATATATAT"  # Fixed: removed Cyrillic character
        expected = 0.0
        result = calculate_gc_content(sequence)
        assert result == expected
    
    def test_mixed_sequence(self):
        """Test GC content calculation for mixed sequence."""
        sequence = "ATCGATCG"  # 4 GC out of 8 = 50%
        expected = 50.0
        result = calculate_gc_content(sequence)
        assert result == expected
    
    def test_lowercase_sequence(self):
        """Test GC content calculation with lowercase."""
        sequence = "atcgatcg"
        expected = 50.0
        result = calculate_gc_content(sequence)
        assert result == expected
    
    def test_ambiguous_bases(self):
        """Test GC content calculation with ambiguous bases."""
        sequence = "ATCGN"  # N should be ignored
        expected = 40.0  # 2 GC out of 5 total bases (including N)
        result = calculate_gc_content(sequence)
        assert result == expected
    
    def test_empty_sequence(self):
        """Test GC content calculation for empty sequence."""
        sequence = ""
        expected = 0.0
        result = calculate_gc_content(sequence)
        assert result == expected
    
    def test_only_ambiguous_bases(self):
        """Test GC content calculation with only ambiguous bases."""
        sequence = "NNNN"
        expected = 0.0  # No definite bases
        result = calculate_gc_content(sequence)
        assert result == expected


class TestValidateSequenceComposition:
    """Test sequence composition validation function."""
    
    def test_valid_composition(self):
        """Test validation of sequence with valid composition."""
        sequence = "ATCGATCGATCGATCG"  # Balanced composition
        
        # Should not raise an exception
        try:
            validate_sequence_composition(sequence)
        except Exception:
            pytest.fail("Valid composition should not raise exception")
    
    def test_high_gc_content(self):
        """Test validation of sequence with high GC content."""
        sequence = "GCGCGCGCGCGCGCGC"  # 100% GC
        
        # Should raise an exception or return warning
        with pytest.raises(ValueError):
            validate_sequence_composition(sequence, max_gc=80.0)
    
    def test_low_gc_content(self):
        """Test validation of sequence with low GC content."""
        sequence = "ATATATATATATATAT"  # 0% GC
        
        # Should raise an exception or return warning
        with pytest.raises(ValueError):
            validate_sequence_composition(sequence, min_gc=20.0)
    
    def test_repetitive_sequence(self):
        """Test validation of repetitive sequence."""
        sequence = "AAAAAAAAAAAAAAAA"  # All A's
        
        # Should detect repetitive pattern
        with pytest.raises(ValueError):
            validate_sequence_composition(sequence, check_repeats=True)
    
    def test_dinucleotide_repeats(self):
        """Test validation of dinucleotide repeats."""
        sequence = "ATATATATATATATAT"  # AT repeats
        
        # Should detect dinucleotide repeats
        with pytest.raises(ValueError):
            validate_sequence_composition(sequence, check_dinuc_repeats=True)
    
    def test_homopolymer_runs(self):
        """Test validation of homopolymer runs."""
        sequence = "ATCGAAAAAAAATCG"  # Long A run
        
        # Should detect homopolymer run
        with pytest.raises(ValueError):
            validate_sequence_composition(sequence, max_homopolymer=5)
    
    def test_valid_sequence_with_parameters(self):
        """Test validation with custom parameters."""
        sequence = "ATCGATCGATCGATCG"
        
        # Should pass with reasonable parameters
        try:
            validate_sequence_composition(
                sequence,
                min_gc=40.0,
                max_gc=60.0,
                max_homopolymer=3,
                check_repeats=True,
                check_dinuc_repeats=True
            )
        except Exception:
            pytest.fail("Valid sequence should pass validation")


class TestUtilityIntegration:
    """Test integration between utility functions."""
    
    def test_reverse_complement_gc_content(self):
        """Test that reverse complement preserves GC content."""
        sequence = "ATCGATCGATCGATCG"
        rc_sequence = reverse_complement(sequence)
        
        gc_original = calculate_gc_content(sequence)
        gc_reverse = calculate_gc_content(rc_sequence)
        
        assert gc_original == gc_reverse
    
    def test_distance_calculation_consistency(self):
        """Test distance calculation consistency."""
        pos1, pos2 = 10, 50
        
        # Distance should be symmetric
        dist1 = calculate_distance(pos1, pos2)
        dist2 = calculate_distance(pos2, pos1)
        
        assert dist1 == dist2
    
    def test_sequence_validation_with_reverse_complement(self):
        """Test sequence validation with reverse complement."""
        sequence = "ATCGATCGATCGATCG"
        rc_sequence = reverse_complement(sequence)
        
        # Both should pass the same validation
        try:
            validate_sequence_composition(sequence)
            validate_sequence_composition(rc_sequence)
        except Exception:
            pytest.fail("Both sequence and reverse complement should be valid")


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_very_long_sequence(self):
        """Test functions with very long sequences."""
        sequence = "ATCG" * 1000  # 4000 bp sequence
        
        # Should handle long sequences
        rc = reverse_complement(sequence)
        gc = calculate_gc_content(sequence)
        
        assert len(rc) == len(sequence)
        assert 0 <= gc <= 100
    
    def test_single_nucleotide(self):
        """Test functions with single nucleotide."""
        sequence = "A"
        
        rc = reverse_complement(sequence)
        gc = calculate_gc_content(sequence)
        
        assert rc == "T"
        assert gc == 0.0
    
    def test_special_characters(self):
        """Test handling of special characters."""
        sequence = "ATCG-ATCG"  # Contains dash
        
        # Should handle or reject special characters appropriately
        with pytest.raises(ValueError):
            reverse_complement(sequence)
    
    def test_numeric_positions(self):
        """Test distance calculation with edge numeric values."""
        # Test with zero
        assert calculate_distance(0, 0) == 0
        
        # Test with negative numbers (if allowed)
        assert calculate_distance(-10, 10) == 20
        
        # Test with very large numbers
        assert calculate_distance(1000000, 2000000) == 1000000


class TestParameterValidation:
    """Test parameter validation in utility functions."""
    
    def test_invalid_gc_parameters(self):
        """Test GC content validation with invalid parameters."""
        sequence = "ATCGATCG"
        
        # Invalid min/max GC values
        with pytest.raises(ValueError):
            validate_sequence_composition(sequence, min_gc=-10)  # Negative
        
        with pytest.raises(ValueError):
            validate_sequence_composition(sequence, max_gc=110)  # > 100
        
        with pytest.raises(ValueError):
            validate_sequence_composition(sequence, min_gc=60, max_gc=40)  # min > max
    
    def test_invalid_homopolymer_length(self):
        """Test homopolymer validation with invalid length."""
        sequence = "ATCGATCG"
        
        with pytest.raises(ValueError):
            validate_sequence_composition(sequence, max_homopolymer=0)  # Zero length
        
        with pytest.raises(ValueError):
            validate_sequence_composition(sequence, max_homopolymer=-1)  # Negative

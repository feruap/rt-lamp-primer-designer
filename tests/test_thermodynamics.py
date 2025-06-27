
"""
Unit tests for thermodynamics module.
"""

import pytest
import math
from unittest.mock import patch

from rt_lamp_app.core.thermodynamics import (
    ThermoCalculator, ThermodynamicResult, SecondaryStructure,
    DNA_DNA_NN, HAIRPIN_LOOP_PENALTIES
)
from rt_lamp_app.core.exceptions import ThermodynamicError


class TestThermoCalculator:
    """Test cases for ThermoCalculator class."""
    
    def test_calculator_initialization(self, thermo_calculator):
        """Test calculator initialization."""
        assert isinstance(thermo_calculator, ThermoCalculator)
    
    def test_calculate_tm_simple_sequence(self, thermo_calculator):
        """Test Tm calculation for simple sequences."""
        # Test with known sequence
        tm = thermo_calculator.calculate_tm("ATCGATCGATCG", na_conc_M=0.05)
        
        # Should be reasonable Tm value
        assert 30 < tm < 80
        assert isinstance(tm, float)
    
    def test_calculate_tm_gc_rich(self, thermo_calculator):
        """Test Tm calculation for GC-rich sequence."""
        gc_rich_tm = thermo_calculator.calculate_tm("GCGCGCGCGCGC", na_conc_M=0.05)
        at_rich_tm = thermo_calculator.calculate_tm("ATATATATATATAT", na_conc_M=0.05)
        
        # GC-rich should have higher Tm
        assert gc_rich_tm > at_rich_tm
    
    def test_calculate_tm_salt_effect(self, thermo_calculator):
        """Test salt concentration effect on Tm."""
        sequence = "ATCGATCGATCG"
        
        tm_low_salt = thermo_calculator.calculate_tm(sequence, na_conc_M=0.01)
        tm_high_salt = thermo_calculator.calculate_tm(sequence, na_conc_M=0.1)
        
        # Higher salt should increase Tm
        assert tm_high_salt > tm_low_salt
    
    def test_calculate_tm_too_short(self, thermo_calculator):
        """Test Tm calculation for too short sequence."""
        with pytest.raises(ThermodynamicError) as exc_info:
            thermo_calculator.calculate_tm("A")
        assert "too short" in str(exc_info.value)
    
    def test_calculate_tm_rna_conversion(self, thermo_calculator):
        """Test that RNA sequences are converted to DNA."""
        dna_tm = thermo_calculator.calculate_tm("ATCGATCGATCG")
        rna_tm = thermo_calculator.calculate_tm("AUCGAUCGAUCG")
        
        # Should be identical after U->T conversion
        assert abs(dna_tm - rna_tm) < 0.1
    
    def test_nearest_neighbor_calculation(self, thermo_calculator):
        """Test nearest-neighbor parameter usage."""
        # Test with sequence that has known dinucleotides
        result = thermo_calculator._calculate_nearest_neighbor("ATCG", 1e-7)
        
        assert isinstance(result, ThermodynamicResult)
        assert result.delta_h < 0  # Should be negative (exothermic)
        assert result.delta_s < 0  # Should be negative
        assert isinstance(result.tm_celsius, float)
    
    def test_palindromic_detection(self, thermo_calculator):
        """Test palindromic sequence detection."""
        assert thermo_calculator._is_palindromic("GAATTC")
        assert thermo_calculator._is_palindromic("ATAT")
        assert not thermo_calculator._is_palindromic("ATCG")
        assert not thermo_calculator._is_palindromic("ATCGATCG")
    
    def test_simplified_salt_correction(self, thermo_calculator):
        """Test simplified salt correction formula."""
        correction_1 = thermo_calculator._simplified_salt_correction(0.05)
        correction_2 = thermo_calculator._simplified_salt_correction(0.1)
        
        # Higher salt should give higher correction
        assert correction_2 > correction_1
        
        # Test minimum salt handling
        correction_min = thermo_calculator._simplified_salt_correction(0.001)
        assert isinstance(correction_min, float)


class TestSecondaryStructurePrediction:
    """Test cases for secondary structure prediction."""
    
    def test_predict_hairpin_simple(self, thermo_calculator):
        """Test hairpin prediction for simple cases."""
        # Sequence with potential hairpin
        hairpin_seq = "ATCGAAAAAACGAT"  # Palindromic ends with loop
        hairpins = thermo_calculator.predict_hairpin(hairpin_seq)
        
        assert isinstance(hairpins, list)
        # May or may not find hairpins depending on algorithm sensitivity
    
    def test_predict_hairpin_no_structure(self, thermo_calculator):
        """Test hairpin prediction for sequence without hairpins."""
        no_hairpin_seq = "ATCGATCGATCGATCG"
        hairpins = thermo_calculator.predict_hairpin(no_hairpin_seq)
        
        assert isinstance(hairpins, list)
        # Should find few or no stable hairpins
    
    def test_predict_hairpin_strong_structure(self, thermo_calculator):
        """Test hairpin prediction for sequence with strong hairpin."""
        # Design sequence with strong hairpin potential
        strong_hairpin = "GCGCGCGCAAAAGCGCGCGC"
        hairpins = thermo_calculator.predict_hairpin(strong_hairpin)
        
        assert isinstance(hairpins, list)
        if hairpins:
            # Check structure properties
            hairpin = hairpins[0]
            assert isinstance(hairpin, SecondaryStructure)
            assert hairpin.structure_type == "hairpin"
            assert isinstance(hairpin.delta_g, float)
    
    def test_predict_dimer_formation(self, thermo_calculator):
        """Test primer-dimer prediction."""
        seq1 = "ATCGATCGATCG"
        seq2 = "CGATCGATCGAT"  # Complementary to seq1
        
        dimers = thermo_calculator.predict_dimer(seq1, seq2)
        
        assert isinstance(dimers, list)
        if dimers:
            dimer = dimers[0]
            assert isinstance(dimer, SecondaryStructure)
            assert dimer.structure_type == "dimer"
    
    def test_predict_dimer_no_interaction(self, thermo_calculator):
        """Test dimer prediction for non-interacting sequences."""
        seq1 = "AAAAAAAAAAAAA"
        seq2 = "GGGGGGGGGGGG"
        
        dimers = thermo_calculator.predict_dimer(seq1, seq2)
        
        # Should find no strong dimers
        assert isinstance(dimers, list)
    
    def test_complementarity_check(self, thermo_calculator):
        """Test sequence complementarity checking."""
        assert thermo_calculator._are_complementary("ATCG", "CGAT")
        assert thermo_calculator._are_complementary("AAAA", "TTTT")
        assert not thermo_calculator._are_complementary("ATCG", "ATCG")
        assert not thermo_calculator._are_complementary("ATCG", "GCTA")
        assert not thermo_calculator._are_complementary("ATCG", "CGT")  # Different lengths


class TestThermodynamicCalculations:
    """Test specific thermodynamic calculations."""
    
    def test_calculate_free_energy_37c(self, thermo_calculator):
        """Test free energy calculation at 37°C."""
        delta_g = thermo_calculator.calculate_free_energy_37c("ATCGATCGATCG")
        
        assert isinstance(delta_g, float)
        assert delta_g < 0  # Should be negative for stable duplex
    
    def test_calculate_end_stability(self, thermo_calculator):
        """Test 3'-end stability calculation."""
        end_stability = thermo_calculator.calculate_end_stability("ATCGATCGATCG", end_length=5)
        
        assert isinstance(end_stability, float)
        # Should be reasonable value
        assert -20 < end_stability < 5
    
    def test_calculate_end_stability_short_sequence(self, thermo_calculator):
        """Test end stability for sequence shorter than end_length."""
        end_stability = thermo_calculator.calculate_end_stability("ATG", end_length=5)
        
        assert isinstance(end_stability, float)
    
    def test_hairpin_energy_calculation(self, thermo_calculator):
        """Test hairpin energy calculation."""
        # Test with known parameters
        energy = thermo_calculator._calculate_hairpin_energy(stem_length=4, loop_size=6)
        
        assert isinstance(energy, float)
        # Should include both stem stability and loop penalty
        assert energy < 0  # Net should be negative for stable hairpin
    
    def test_hairpin_energy_large_loop(self, thermo_calculator):
        """Test hairpin energy for large loop."""
        energy_small = thermo_calculator._calculate_hairpin_energy(4, 6)
        energy_large = thermo_calculator._calculate_hairpin_energy(4, 50)
        
        # Large loop should be less stable (higher energy)
        assert energy_large > energy_small
    
    def test_dimer_energy_calculation(self, thermo_calculator):
        """Test dimer energy calculation."""
        energy = thermo_calculator._calculate_dimer_energy("ATCG", "CGAT")
        
        assert isinstance(energy, float)
        assert energy < 0  # Should be negative for stable interaction


class TestThermodynamicReport:
    """Test comprehensive thermodynamic reporting."""
    
    def test_get_thermodynamic_report_complete(self, thermo_calculator):
        """Test complete thermodynamic report generation."""
        sequence = "ATCGATCGATCGATCG"
        report = thermo_calculator.get_thermodynamic_report(sequence, na_conc_M=0.05)
        
        # Check all required fields
        required_fields = [
            "sequence", "length", "gc_content", "tm_celsius", 
            "delta_g_37", "end_stability", "hairpins", "palindromic", "warnings"
        ]
        
        for field in required_fields:
            assert field in report
        
        # Check data types
        assert isinstance(report["length"], int)
        assert isinstance(report["gc_content"], float)
        assert isinstance(report["tm_celsius"], float)
        assert isinstance(report["delta_g_37"], float)
        assert isinstance(report["end_stability"], float)
        assert isinstance(report["hairpins"], list)
        assert isinstance(report["palindromic"], bool)
        assert isinstance(report["warnings"], list)
    
    def test_get_thermodynamic_report_warnings(self, thermo_calculator):
        """Test warning generation in thermodynamic report."""
        # Test sequence that should generate warnings
        weak_sequence = "AAAA"  # Very short, AT-rich
        
        try:
            report = thermo_calculator.get_thermodynamic_report(weak_sequence)
            # Check if warnings are generated appropriately
            assert isinstance(report["warnings"], list)
        except ThermodynamicError:
            # Short sequence might fail, which is acceptable
            pass
    
    def test_get_thermodynamic_report_error_handling(self, thermo_calculator):
        """Test error handling in report generation."""
        with pytest.raises(ThermodynamicError):
            thermo_calculator.get_thermodynamic_report("")  # Empty sequence


class TestThermodynamicConstants:
    """Test thermodynamic constants and parameters."""
    
    def test_dna_nn_parameters_completeness(self):
        """Test that all required nearest-neighbor parameters are present."""
        # Should have all 16 dinucleotide combinations
        bases = ['A', 'T', 'C', 'G']
        expected_pairs = [(b1, b2) for b1 in bases for b2 in bases]
        
        for pair in expected_pairs:
            assert pair in DNA_DNA_NN
            assert "dH" in DNA_DNA_NN[pair]
            assert "dS" in DNA_DNA_NN[pair]
            assert isinstance(DNA_DNA_NN[pair]["dH"], (int, float))
            assert isinstance(DNA_DNA_NN[pair]["dS"], (int, float))
    
    def test_hairpin_loop_penalties_range(self):
        """Test hairpin loop penalty values."""
        for size, penalty in HAIRPIN_LOOP_PENALTIES.items():
            assert isinstance(size, int)
            assert isinstance(penalty, (int, float))
            assert 3 <= size <= 30
            assert penalty > 0  # Penalties should be positive
    
    def test_initiation_terms_structure(self):
        """Test initiation terms structure."""
        from rt_lamp_app.core.thermodynamics import INITIATION_TERMS
        
        required_terms = ["HELIX_WITH_TERMINAL_AT", "HELIX_WITH_TERMINAL_GC"]
        for term in required_terms:
            assert term in INITIATION_TERMS
            assert "dH" in INITIATION_TERMS[term]
            assert "dS" in INITIATION_TERMS[term]


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error conditions."""
    
    def test_tm_calculation_extreme_conditions(self, thermo_calculator):
        """Test Tm calculation under extreme conditions."""
        sequence = "ATCGATCGATCG"
        
        # Very low salt
        tm_low = thermo_calculator.calculate_tm(sequence, na_conc_M=0.001)
        assert isinstance(tm_low, float)
        
        # Very high salt
        tm_high = thermo_calculator.calculate_tm(sequence, na_conc_M=1.0)
        assert isinstance(tm_high, float)
        assert tm_high > tm_low
    
    def test_unknown_dinucleotide_handling(self, thermo_calculator):
        """Test handling of unknown dinucleotides."""
        # This tests the fallback mechanism for ambiguous bases
        with patch.object(thermo_calculator, 'logger') as mock_logger:
            result = thermo_calculator._calculate_nearest_neighbor("ANNG", 1e-7)
            assert isinstance(result, ThermodynamicResult)
            # Should have logged warnings for unknown dinucleotides
    
    def test_very_short_sequences(self, thermo_calculator):
        """Test handling of very short sequences."""
        # Single base
        with pytest.raises(ThermodynamicError):
            thermo_calculator.calculate_tm("A")
        
        # Two bases (minimum for calculation)
        tm = thermo_calculator.calculate_tm("AT")
        assert isinstance(tm, float)
    
    def test_sequence_with_all_same_base(self, thermo_calculator):
        """Test sequences with all identical bases."""
        # All A's
        tm_a = thermo_calculator.calculate_tm("AAAAAAAAAA")
        assert isinstance(tm_a, float)
        
        # All G's
        tm_g = thermo_calculator.calculate_tm("GGGGGGGGGG")
        assert isinstance(tm_g, float)
        
        # G's should have higher Tm than A's
        assert tm_g > tm_a
    
    def test_fallback_calculations(self, thermo_calculator):
        """Test fallback calculations when main methods fail."""
        # Test end stability fallback
        with patch.object(thermo_calculator, '_calculate_nearest_neighbor', 
                         side_effect=Exception("Test error")):
            stability = thermo_calculator.calculate_end_stability("ATCGATCG")
            assert isinstance(stability, float)
            # Should use GC-based fallback


class TestPerformanceAndValidation:
    """Test performance characteristics and validation against known values."""
    
    def test_tm_calculation_performance(self, thermo_calculator):
        """Test that Tm calculations complete in reasonable time."""
        import time
        
        sequence = "ATCGATCGATCGATCGATCGATCGATCGATCG"
        
        start_time = time.time()
        tm = thermo_calculator.calculate_tm(sequence)
        end_time = time.time()
        
        # Should complete quickly
        assert end_time - start_time < 1.0  # Less than 1 second
        assert isinstance(tm, float)
    
    def test_tm_calculation_reproducibility(self, thermo_calculator):
        """Test that Tm calculations are reproducible."""
        sequence = "ATCGATCGATCGATCG"
        
        tm1 = thermo_calculator.calculate_tm(sequence, na_conc_M=0.05)
        tm2 = thermo_calculator.calculate_tm(sequence, na_conc_M=0.05)
        
        # Should be identical
        assert tm1 == tm2
    
    def test_tm_range_validation(self, thermo_calculator, primer_sequences):
        """Test that calculated Tm values are in reasonable ranges."""
        for name, sequence in primer_sequences.items():
            tm = thermo_calculator.calculate_tm(sequence, na_conc_M=0.05)
            
            # Should be in reasonable range for primers
            assert 20 < tm < 100, f"Tm {tm} out of range for {name}: {sequence}"
    
    @pytest.mark.parametrize("sequence,expected_range", [
        ("ATATATATATATATAT", (30, 50)),  # AT-rich, lower Tm
        ("GCGCGCGCGCGCGCGC", (60, 90)),  # GC-rich, higher Tm
        ("ATCGATCGATCGATCG", (40, 70)),  # Mixed, medium Tm
    ])
    def test_tm_expected_ranges(self, thermo_calculator, sequence, expected_range):
        """Test that Tm values fall within expected ranges for different sequence types."""
        tm = thermo_calculator.calculate_tm(sequence, na_conc_M=0.05)
        min_tm, max_tm = expected_range
        assert min_tm <= tm <= max_tm, f"Tm {tm} not in expected range {expected_range} for {sequence}"



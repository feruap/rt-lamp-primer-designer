
"""
Integration tests for RT-LAMP core modules.
"""

import pytest
from pathlib import Path

from rt_lamp_app.core.sequence_processing import (
    Sequence, parse_fasta_string, validate_sequence_quality
)
from rt_lamp_app.core.thermodynamics import ThermoCalculator
from rt_lamp_app.core.exceptions import InvalidInputError, ThermodynamicError


class TestSequenceProcessingThermodynamicsIntegration:
    """Test integration between sequence processing and thermodynamics modules."""
    
    def test_sequence_to_thermodynamics_pipeline(self, sample_sequences, thermo_calculator):
        """Test complete pipeline from sequence processing to thermodynamics."""
        # Get a sample sequence
        seq = sample_sequences["sars_cov2_fragment"]
        
        # Validate sequence quality
        is_valid, issues = validate_sequence_quality(seq)
        assert is_valid, f"Sample sequence should be valid: {issues}"
        
        # Calculate thermodynamics
        tm = thermo_calculator.calculate_tm(seq.sequence, na_conc_M=0.05)
        assert isinstance(tm, float)
        assert 30 < tm < 100  # Reasonable Tm range
        
        # Get comprehensive report
        report = thermo_calculator.get_thermodynamic_report(seq.sequence)
        assert report["sequence"] == seq.sequence
        assert report["length"] == seq.get_length()
        assert abs(report["gc_content"] - seq.get_gc_content()) < 0.1
    
    def test_fasta_parsing_to_thermodynamics(self, thermo_calculator):
        """Test pipeline from FASTA parsing to thermodynamic analysis."""
        fasta_content = """
>Test_Primer_F3
ATCGATCGATCGATCG
>Test_Primer_B3  
GCGCGCGCGCGCGCGC
        """.strip()
        
        # Parse FASTA
        sequences = parse_fasta_string(fasta_content)
        assert len(sequences) == 1  # Phase 0 processes only first sequence
        
        seq = sequences[0]
        
        # Analyze thermodynamics
        report = thermo_calculator.get_thermodynamic_report(seq.sequence)
        
        # Verify integration
        assert report["sequence"] == seq.sequence
        assert report["length"] == len(seq.sequence)
        assert isinstance(report["tm_celsius"], float)
    
    def test_reverse_complement_thermodynamics(self, sample_sequences, thermo_calculator):
        """Test thermodynamic analysis of reverse complement sequences."""
        seq = sample_sequences["simple_dna"]
        rc_sequence = seq.get_reverse_complement()
        
        # Calculate Tm for both
        tm_original = thermo_calculator.calculate_tm(seq.sequence)
        tm_rc = thermo_calculator.calculate_tm(rc_sequence)
        
        # Should be similar (not necessarily identical due to asymmetric parameters)
        assert abs(tm_original - tm_rc) < 10  # Within 10°C
    
    def test_sequence_quality_affects_thermodynamics(self, thermo_calculator):
        """Test that sequence quality issues affect thermodynamic calculations."""
        # Good quality sequence
        good_seq = Sequence("Good", "ATCGATCGATCGATCGATCGATCG")
        is_valid, _ = validate_sequence_quality(good_seq)
        assert is_valid
        
        tm_good = thermo_calculator.calculate_tm(good_seq.sequence)
        
        # Poor quality sequence (too short for normal use)
        poor_seq = Sequence("Poor", "ATCG")
        is_valid, issues = validate_sequence_quality(poor_seq, min_length=10)
        assert not is_valid
        
        # Should still calculate but might be unreliable
        with pytest.raises(ThermodynamicError):
            thermo_calculator.calculate_tm(poor_seq.sequence)


class TestRealWorldSequenceAnalysis:
    """Test analysis of real-world sequences."""
    
    def test_sars_cov2_sequence_analysis(self, sample_sequences, thermo_calculator):
        """Test analysis of SARS-CoV-2 sequence fragment."""
        seq = sample_sequences["sars_cov2_fragment"]
        
        # Quality validation
        is_valid, issues = validate_sequence_quality(seq)
        assert is_valid, f"SARS-CoV-2 sequence should pass quality checks: {issues}"
        
        # Thermodynamic analysis
        report = thermo_calculator.get_thermodynamic_report(seq.sequence)
        
        # Verify reasonable values for viral sequence
        assert 40 < report["gc_content"] < 60  # Typical viral GC content
        assert 70 < report["tm_celsius"] < 90  # High Tm for long sequence
        assert report["delta_g_37"] < -50  # Very stable for long sequence
        
        # Should not have excessive warnings for good sequence
        assert len(report["warnings"]) <= 1
    
    def test_primer_like_sequences(self, primer_sequences, thermo_calculator):
        """Test analysis of primer-like sequences."""
        for name, sequence in primer_sequences.items():
            # Create sequence object
            seq = Sequence(name, sequence)
            
            # Quality check
            is_valid, issues = validate_sequence_quality(
                seq, 
                min_length=15 if "loop" in name else 18,
                max_length=60
            )
            
            if not is_valid:
                print(f"Quality issues for {name}: {issues}")
            
            # Thermodynamic analysis
            report = thermo_calculator.get_thermodynamic_report(sequence)
            
            # Verify primer-appropriate values
            if "f3" in name.lower() or "b3" in name.lower():
                # F3/B3 primers should have moderate Tm
                assert 45 < report["tm_celsius"] < 75
            elif "fip" in name.lower() or "bip" in name.lower():
                # FIP/BIP primers are longer, higher Tm expected
                assert 55 < report["tm_celsius"] < 85
    
    def test_gc_extreme_sequences(self, thermo_calculator):
        """Test sequences with extreme GC content."""
        # Very GC-rich sequence
        gc_rich = Sequence("GC Rich", "GCGCGCGCGCGCGCGCGCGC")
        report_gc = thermo_calculator.get_thermodynamic_report(gc_rich.sequence)
        
        # Very AT-rich sequence  
        at_rich = Sequence("AT Rich", "ATATATATATATATATATATAT")
        report_at = thermo_calculator.get_thermodynamic_report(at_rich.sequence)
        
        # GC-rich should have higher Tm and more negative ΔG
        assert report_gc["tm_celsius"] > report_at["tm_celsius"]
        assert report_gc["delta_g_37"] < report_at["delta_g_37"]
        
        # Both should generate appropriate warnings
        assert any("GC content" in warning for warning in 
                  validate_sequence_quality(gc_rich, max_gc=80)[1])
        assert any("GC content" in warning for warning in 
                  validate_sequence_quality(at_rich, min_gc=20)[1])


class TestErrorHandlingIntegration:
    """Test error handling across module boundaries."""
    
    def test_invalid_sequence_to_thermodynamics(self, thermo_calculator):
        """Test that invalid sequences are caught before thermodynamic analysis."""
        # Invalid sequence should be caught at sequence creation
        with pytest.raises(InvalidInputError):
            Sequence("Invalid", "ATCGXYZ")
        
        # If somehow an invalid sequence gets through, thermodynamics should handle it
        with pytest.raises(ThermodynamicError):
            thermo_calculator.calculate_tm("")  # Empty sequence
    
    def test_edge_case_sequences(self, thermo_calculator):
        """Test edge case sequences across both modules."""
        # Very short sequence
        short_seq = Sequence("Short", "AT")
        is_valid, issues = validate_sequence_quality(short_seq, min_length=10)
        assert not is_valid
        
        # Thermodynamics should still work for minimum length
        tm = thermo_calculator.calculate_tm(short_seq.sequence)
        assert isinstance(tm, float)
        
        # Single repeated base
        repeat_seq = Sequence("Repeat", "AAAAAAAAAAAAAAAA")
        is_valid, issues = validate_sequence_quality(repeat_seq)
        # Should flag excessive repeats
        assert any("repeat" in issue.lower() for issue in issues)
        
        # But thermodynamics should still calculate
        tm = thermo_calculator.calculate_tm(repeat_seq.sequence)
        assert isinstance(tm, float)


class TestPerformanceIntegration:
    """Test performance of integrated workflows."""
    
    def test_batch_sequence_processing(self, thermo_calculator):
        """Test processing multiple sequences efficiently."""
        import time
        
        # Create multiple test sequences
        sequences = []
        for i in range(10):
            seq = Sequence(f"Test_{i}", "ATCGATCGATCG" + "ATCG" * i)
            sequences.append(seq)
        
        start_time = time.time()
        
        # Process all sequences
        results = []
        for seq in sequences:
            # Quality check
            is_valid, issues = validate_sequence_quality(seq)
            
            # Thermodynamic analysis
            if is_valid:
                report = thermo_calculator.get_thermodynamic_report(seq.sequence)
                results.append(report)
        
        end_time = time.time()
        
        # Should complete quickly
        assert end_time - start_time < 5.0  # Less than 5 seconds for 10 sequences
        assert len(results) > 0
    
    def test_large_sequence_handling(self, thermo_calculator):
        """Test handling of large sequences."""
        # Create a large sequence (but within limits)
        large_sequence = "ATCGATCGATCG" * 100  # 1200 bp
        seq = Sequence("Large", large_sequence)
        
        # Should pass quality checks
        is_valid, issues = validate_sequence_quality(seq, max_length=5000)
        assert is_valid
        
        # Thermodynamic analysis should work but may be slower
        import time
        start_time = time.time()
        
        report = thermo_calculator.get_thermodynamic_report(seq.sequence)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 10.0  # Less than 10 seconds
        assert isinstance(report["tm_celsius"], float)


class TestDataConsistency:
    """Test data consistency across modules."""
    
    def test_sequence_length_consistency(self, sample_sequences, thermo_calculator):
        """Test that sequence lengths are consistent across modules."""
        for name, seq in sample_sequences.items():
            # Length from sequence processing
            seq_length = seq.get_length()
            
            # Length from thermodynamic report
            report = thermo_calculator.get_thermodynamic_report(seq.sequence)
            report_length = report["length"]
            
            assert seq_length == report_length
            assert seq_length == len(seq.sequence)
    
    def test_gc_content_consistency(self, sample_sequences, thermo_calculator):
        """Test that GC content calculations are consistent."""
        for name, seq in sample_sequences.items():
            # GC content from sequence processing
            seq_gc = seq.get_gc_content()
            
            # GC content from thermodynamic report
            report = thermo_calculator.get_thermodynamic_report(seq.sequence)
            report_gc = report["gc_content"]
            
            # Should be very close (allowing for floating point precision)
            assert abs(seq_gc - report_gc) < 0.01

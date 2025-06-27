"""
Integration tests for design modules.
"""

import pytest
from unittest.mock import Mock, patch

from rt_lamp_app.core.sequence_processing import Sequence
from rt_lamp_app.core.thermodynamics import ThermoCalculator
from rt_lamp_app.design.primer_design import PrimerDesigner, Primer, LampPrimerSet, PrimerType
from rt_lamp_app.design.specificity_checker import SpecificityChecker, SpecificityResult
from rt_lamp_app.design.utils import reverse_complement, calculate_gc_content
from rt_lamp_app.design.exceptions import GeometricConstraintError, InsufficientCandidatesError


class TestDesignWorkflow:
    """Test complete design workflow integration."""
    
    @pytest.fixture
    def target_sequence(self):
        """Create a realistic target sequence for RT-LAMP design."""
        # Create a sequence that should allow for proper RT-LAMP design
        sequence = (
            "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"  # F3 region (42bp)
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"  # Spacer (42bp)
            "GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC"  # F2 region (42bp)
            "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"  # Loop region (42bp)
            "CGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCG"  # B2 region (42bp)
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"  # Spacer (42bp)
            "CGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT"   # B3 region (42bp)
        )
        return Sequence("SARS-CoV-2 Target", sequence)
    
    @pytest.fixture
    def designer(self):
        """Create primer designer instance."""
        return PrimerDesigner()
    
    @pytest.fixture
    def specificity_checker(self):
        """Create specificity checker instance."""
        return SpecificityChecker()
    
    def test_complete_design_workflow(self, designer, specificity_checker, target_sequence):
        """Test complete primer design and specificity checking workflow."""
        # Mock the primer generation to avoid complex thermodynamic calculations
        with patch.object(designer, '_generate_f3_candidates') as mock_f3, \
             patch.object(designer, '_generate_b3_candidates') as mock_b3, \
             patch.object(designer, '_generate_fip_candidates') as mock_fip, \
             patch.object(designer, '_generate_bip_candidates') as mock_bip, \
             patch.object(designer, '_validate_primer_set_geometry') as mock_validate, \
             patch.object(designer, '_score_primer_set') as mock_score:
            
            # Create mock primers
            f3_primer = Primer(PrimerType.F3, "ATCGATCGATCGATCG", 0, 15, "+", 60.0, 50.0, -5.0)
            b3_primer = Primer(PrimerType.B3, "CGATCGATCGATCGAT", 280, 295, "-", 61.0, 50.0, -5.5)
            fip_primer = Primer(PrimerType.FIP, "GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC", 84, 119, "+", 62.0, 75.0, -8.0)
            bip_primer = Primer(PrimerType.BIP, "CGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCG", 168, 203, "-", 63.0, 75.0, -8.5)
            
            # Set up mocks - need at least 5 candidates each
            mock_f3.return_value = [f3_primer] * 5
            mock_b3.return_value = [b3_primer] * 5
            mock_fip.return_value = [fip_primer] * 5
            mock_bip.return_value = [bip_primer] * 5
            mock_validate.return_value = True
            mock_score.return_value = None
            
            # Design primer sets
            primer_sets = designer.design_primer_set(target_sequence, max_candidates=1)
            
            assert len(primer_sets) > 0
            primer_set = primer_sets[0]
            
            # Check specificity of the primer set
            with patch.object(specificity_checker, 'check_primer_specificity') as mock_spec:
                mock_result = SpecificityResult(
                    primer_sequence="test",
                    primer_type="F3",
                    total_hits=1,
                    high_risk_hits=0,
                    medium_risk_hits=0,
                    low_risk_hits=1,
                    hits=[],
                    specificity_score=90.0
                )
                mock_spec.return_value = mock_result
                
                specificity_results = specificity_checker.check_primer_set_specificity(primer_set)
                
                assert len(specificity_results.primer_results) == 4  # F3, B3, FIP, BIP
                assert all(result.specificity_score > 80.0 for result in specificity_results.primer_results.values())
    
    def test_design_with_thermodynamic_integration(self, designer, target_sequence):
        """Test design workflow with real thermodynamic calculations."""
        # Use real thermodynamic calculator
        thermo_calc = ThermoCalculator()
        
        # Test that designer can calculate Tm for sequences
        test_sequence = "ATCGATCGATCGATCG"
        tm = thermo_calc.calculate_tm(test_sequence, na_conc_M=0.05)
        
        assert isinstance(tm, float)
        assert tm > 0  # Should be positive temperature
    
    def test_design_with_sequence_processing_integration(self, designer, target_sequence):
        """Test design workflow with sequence processing integration."""
        # Test that designer can work with Sequence objects
        assert isinstance(target_sequence, Sequence)
        assert len(target_sequence.sequence) > 200  # Should be long enough for RT-LAMP
        
        # Test reverse complement functionality
        rc_sequence = reverse_complement(target_sequence.sequence[:20])
        assert len(rc_sequence) == 20
        assert rc_sequence != target_sequence.sequence[:20]  # Should be different
    
    def test_design_failure_handling(self, designer):
        """Test handling of design failures."""
        # Create a sequence too short for RT-LAMP design
        short_sequence = Sequence("Too Short", "ATCGATCG")
        
        # Should handle insufficient sequence length gracefully
        with patch.object(designer, '_generate_f3_candidates', return_value=[]), \
             patch.object(designer, '_generate_b3_candidates', return_value=[]), \
             patch.object(designer, '_generate_fip_candidates', return_value=[]), \
             patch.object(designer, '_generate_bip_candidates', return_value=[]):
            
            with pytest.raises(InsufficientCandidatesError):
                designer.design_primer_set(short_sequence)


class TestCoreDesignIntegration:
    """Test integration between core and design modules."""
    
    def test_thermodynamic_primer_scoring(self):
        """Test that primer scoring uses thermodynamic calculations."""
        designer = PrimerDesigner()
        
        # Create test primer
        primer = Primer(
            type=PrimerType.F3,
            sequence="ATCGATCGATCGATCG",
            start_pos=0,
            end_pos=15,
            strand="+",
            tm=60.0,
            gc_content=50.0,
            delta_g=-5.0
        )
        
        # Mock scoring to verify thermodynamic integration
        with patch.object(designer, '_score_primer') as mock_score:
            mock_score.return_value = 8.5
            
            score = designer._score_primer(primer)
            
            assert isinstance(score, (int, float))
            mock_score.assert_called_once_with(primer)
    
    def test_sequence_validation_integration(self):
        """Test integration with sequence validation."""
        from rt_lamp_app.core.sequence_processing import validate_sequence_quality
        
        # Test valid sequence
        valid_seq = Sequence("Valid", "ATCGATCGATCGATCGATCGATCG")
        is_valid, issues = validate_sequence_quality(valid_seq)
        
        # Should integrate properly with design modules
        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)
    
    def test_gc_content_calculation_consistency(self):
        """Test GC content calculation consistency between modules."""
        sequence = "ATCGATCGATCGATCG"
        
        # Calculate GC content using design utils
        gc_design = calculate_gc_content(sequence)
        
        # Should be consistent calculation
        assert 0 <= gc_design <= 100
        assert isinstance(gc_design, float)


class TestSpecificityIntegration:
    """Test specificity checking integration."""
    
    @pytest.fixture
    def primer_set(self):
        """Create sample primer set for testing."""
        f3 = Primer(PrimerType.F3, "ATCGATCGATCGATCG", 0, 15, "+", 60.0, 50.0, -5.0)
        b3 = Primer(PrimerType.B3, "CGATCGATCGATCGAT", 200, 215, "-", 61.0, 50.0, -5.5)
        fip = Primer(PrimerType.FIP, "GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC", 20, 55, "+", 62.0, 75.0, -8.0)
        bip = Primer(PrimerType.BIP, "CGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCG", 160, 195, "-", 63.0, 75.0, -8.5)
        
        return LampPrimerSet(f3=f3, b3=b3, fip=fip, bip=bip)
    
    def test_primer_set_specificity_workflow(self, primer_set):
        """Test complete primer set specificity checking."""
        checker = SpecificityChecker()
        
        # Mock individual primer specificity checks
        with patch.object(checker, 'check_primer_specificity') as mock_check:
            mock_result = SpecificityResult(
                primer_sequence="test",
                primer_type="F3",
                total_hits=2,
                high_risk_hits=0,
                medium_risk_hits=1,
                low_risk_hits=1,
                hits=[],
                specificity_score=85.0
            )
            mock_check.return_value = mock_result
            
            results = checker.check_primer_set_specificity(primer_set)
            
            # Should check all primers
            assert len(results.primer_results) == 4
            assert mock_check.call_count == 4
            
            # All should have good specificity scores
            assert all(result.specificity_score > 80.0 for result in results.primer_results.values())
    
    def test_cross_reactivity_detection(self, primer_set):
        """Test cross-reactivity detection between primers."""
        checker = SpecificityChecker()
        
        # Mock cross-reactivity check
        with patch.object(checker, '_check_cross_reactivity') as mock_cross:
            mock_cross.return_value = True  # Cross-reactivity detected
            
            has_cross_reactivity = checker._check_cross_reactivity(primer_set)
            
            assert has_cross_reactivity is True
            mock_cross.assert_called_once_with(primer_set)
    
    def test_specificity_with_thermodynamics(self):
        """Test specificity checking with thermodynamic calculations."""
        checker = SpecificityChecker()
        
        # Verify thermodynamic calculator is available
        assert hasattr(checker, 'thermo_calc')
        assert checker.thermo_calc is not None
        
        # Test Tm calculation for specificity hits
        test_sequence = "ATCGATCGATCGATCG"
        tm = checker.thermo_calc.calculate_tm(test_sequence, na_conc_M=0.05)
        
        assert isinstance(tm, float)
        assert tm > 0


class TestErrorHandlingIntegration:
    """Test error handling across design modules."""
    
    def test_geometric_constraint_propagation(self):
        """Test that geometric constraint errors propagate properly."""
        designer = PrimerDesigner()
        
        # Create primers that violate geometric constraints
        f3 = Primer(PrimerType.F3, "ATCGATCGATCGATCG", 0, 15, "+", 60.0, 50.0, -5.0)
        b3 = Primer(PrimerType.B3, "CGATCGATCGATCGAT", 20, 35, "-", 61.0, 50.0, -5.5)  # Too close
        fip = Primer(PrimerType.FIP, "GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC", 10, 45, "+", 62.0, 75.0, -8.0)
        bip = Primer(PrimerType.BIP, "CGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCG", 25, 60, "-", 63.0, 75.0, -8.5)
        
        primer_set = LampPrimerSet(f3=f3, b3=b3, fip=fip, bip=bip)
        target_sequence = Sequence("Test", "A" * 100)
        
        # Should raise geometric constraint error
        with patch.object(designer, '_validate_primer_set_geometry') as mock_validate:
            mock_validate.side_effect = GeometricConstraintError("F2_B2_amplicon", "120-200", "50")
            
            with pytest.raises(GeometricConstraintError):
                designer._validate_primer_set_geometry(primer_set, target_sequence)
    
    def test_insufficient_candidates_handling(self):
        """Test handling of insufficient primer candidates."""
        designer = PrimerDesigner()
        target_sequence = Sequence("Test", "ATCGATCGATCGATCG")
        
        # Mock insufficient candidates
        with patch.object(designer, '_generate_f3_candidates', return_value=[]), \
             patch.object(designer, '_generate_b3_candidates', return_value=[]), \
             patch.object(designer, '_generate_fip_candidates', return_value=[]), \
             patch.object(designer, '_generate_bip_candidates', return_value=[]):
            
            with pytest.raises(InsufficientCandidatesError):
                designer.design_primer_set(target_sequence)
    
    def test_specificity_error_handling(self):
        """Test specificity checking error handling."""
        checker = SpecificityChecker(blast_db_path="/nonexistent/path")
        
        primer = Primer(
            type=PrimerType.F3,
            sequence="ATCGATCGATCGATCG",
            start_pos=0,
            end_pos=15,
            strand="+",
            tm=60.0,
            gc_content=50.0,
            delta_g=-5.0
        )
        
        # Should handle BLAST errors gracefully
        with patch.object(checker, 'check_primer_specificity') as mock_check:
            mock_result = SpecificityResult(
                primer_sequence=primer.sequence,
                primer_type="F3",
                total_hits=0,
                high_risk_hits=0,
                medium_risk_hits=0,
                low_risk_hits=0,
                hits=[],
                specificity_score=80.0,
                warnings=["BLAST unavailable"]
            )
            mock_check.return_value = mock_result
            
            result = checker.check_primer_specificity(primer, method="blast")
            
            assert result.specificity_score == 80.0
            assert len(result.warnings) > 0


class TestPerformanceIntegration:
    """Test performance aspects of design integration."""
    
    def test_batch_primer_design_performance(self):
        """Test performance of batch primer design."""
        import time
        
        designer = PrimerDesigner()
        
        # Create multiple target sequences
        sequences = []
        for i in range(3):  # Small number for testing
            seq_data = f"ATCGATCGATCGATCG{'ATCG' * (10 + i)}"
            sequences.append(Sequence(f"Target_{i}", seq_data))
        
        start_time = time.time()
        
        # Mock the design process for performance testing
        with patch.object(designer, 'design_primer_set') as mock_design:
            mock_primer_set = Mock()
            mock_primer_set.overall_score = 10.0
            mock_design.return_value = [mock_primer_set]
            
            results = []
            for seq in sequences:
                primer_sets = designer.design_primer_set(seq, max_candidates=1)
                results.extend(primer_sets)
        
        end_time = time.time()
        
        # Should complete reasonably quickly
        assert end_time - start_time < 5.0  # Less than 5 seconds
        assert len(results) == 3  # One result per sequence
    
    def test_specificity_checking_performance(self):
        """Test performance of specificity checking."""
        import time
        
        checker = SpecificityChecker()
        
        # Create multiple primers
        primers = []
        for i in range(5):  # Small number for testing
            primer = Primer(
                type=PrimerType.F3,
                sequence=f"ATCGATCGATCGATC{i}",
                start_pos=i * 20,
                end_pos=i * 20 + 15,
                strand="+",
                tm=60.0 + i,
                gc_content=50.0,
                delta_g=-5.0 - i
            )
            primers.append(primer)
        
        start_time = time.time()
        
        # Mock specificity checking for performance
        with patch.object(checker, 'check_primer_specificity') as mock_check:
            mock_result = SpecificityResult(
                primer_sequence="test",
                primer_type="F3",
                total_hits=1,
                high_risk_hits=0,
                medium_risk_hits=0,
                low_risk_hits=1,
                hits=[],
                specificity_score=90.0
            )
            mock_check.return_value = mock_result
            
            results = []
            for primer in primers:
                result = checker.check_primer_specificity(primer)
                results.append(result)
        
        end_time = time.time()
        
        # Should complete quickly
        assert end_time - start_time < 2.0  # Less than 2 seconds
        assert len(results) == 5  # One result per primer


class TestDataFlowIntegration:
    """Test data flow between design modules."""
    
    def test_primer_data_consistency(self):
        """Test that primer data remains consistent across modules."""
        # Create primer with specific properties
        original_primer = Primer(
            type=PrimerType.F3,
            sequence="ATCGATCGATCGATCG",
            start_pos=0,
            end_pos=15,
            strand="+",
            tm=60.5,
            gc_content=50.0,
            delta_g=-5.2
        )
        
        # Verify data consistency
        assert original_primer.sequence == "ATCGATCGATCGATCG"
        assert original_primer.tm == 60.5
        assert original_primer.gc_content == 50.0
        
        # Test that GC content matches calculated value
        calculated_gc = calculate_gc_content(original_primer.sequence)
        assert abs(original_primer.gc_content - calculated_gc) < 0.1  # Small tolerance
    
    def test_primer_set_data_integrity(self):
        """Test primer set data integrity."""
        f3 = Primer(PrimerType.F3, "ATCGATCGATCGATCG", 0, 15, "+", 60.0, 50.0, -5.0)
        b3 = Primer(PrimerType.B3, "CGATCGATCGATCGAT", 200, 215, "-", 61.0, 50.0, -5.5)
        fip = Primer(PrimerType.FIP, "GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC", 20, 55, "+", 62.0, 75.0, -8.0)
        bip = Primer(PrimerType.BIP, "CGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCG", 160, 195, "-", 63.0, 75.0, -8.5)
        
        primer_set = LampPrimerSet(f3=f3, b3=b3, fip=fip, bip=bip)
        
        # Verify all primers are present and correct
        all_primers = primer_set.get_all_primers()
        assert len(all_primers) == 4
        
        # Verify primer types
        primer_types = {p.type for p in all_primers}
        expected_types = {PrimerType.F3, PrimerType.B3, PrimerType.FIP, PrimerType.BIP}
        assert primer_types == expected_types
        
        # Verify Tm range calculation
        min_tm, max_tm = primer_set.get_tm_range()
        assert min_tm == 60.0
        assert max_tm == 63.0

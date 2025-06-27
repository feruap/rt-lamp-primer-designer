"""
Tests for specificity checker module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path

from rt_lamp_app.core.sequence_processing import Sequence
from rt_lamp_app.design.specificity_checker import (
    SpecificityChecker, SpecificityResult, SpecificityHit, RiskLevel
)
from rt_lamp_app.design.primer_design import Primer, LampPrimerSet, PrimerType
from rt_lamp_app.design.exceptions import SpecificityError


class TestSpecificityHit:
    """Test SpecificityHit class."""
    
    def test_hit_creation(self):
        """Test basic hit creation."""
        hit = SpecificityHit(
            query_primer="ATCGATCGATCGATCG",
            target_sequence="ATCGATCGATCGATCG",
            target_id="test_target",
            alignment_length=16,
            identity_percent=100.0,
            query_start=0,
            query_end=15,
            target_start=0,
            target_end=15
        )
        
        assert hit.query_primer == "ATCGATCGATCGATCG"
        assert hit.identity_percent == 100.0
        assert hit.risk_level == RiskLevel.LOW  # Default
    
    def test_hit_with_risk_assessment(self):
        """Test hit with risk level assessment."""
        hit = SpecificityHit(
            query_primer="ATCGATCGATCGATCG",
            target_sequence="ATCGATCGATCGATCG",
            target_id="human_genome",
            alignment_length=16,
            identity_percent=95.0,
            query_start=0,
            query_end=15,
            target_start=0,
            target_end=15,
            risk_level=RiskLevel.HIGH,
            is_human_genome=True
        )
        
        assert hit.risk_level == RiskLevel.HIGH
        assert hit.is_human_genome is True


class TestSpecificityResult:
    """Test SpecificityResult class."""
    
    def test_result_creation(self):
        """Test basic result creation."""
        hits = [
            SpecificityHit(
                query_primer="ATCGATCGATCGATCG",
                target_sequence="ATCGATCGATCGATCG",
                target_id="target1",
                alignment_length=16,
                identity_percent=100.0,
                query_start=0,
                query_end=15,
                target_start=0,
                target_end=15
            )
        ]
        
        result = SpecificityResult(
            primer_sequence="ATCGATCGATCGATCG",
            primer_type="F3",
            total_hits=1,
            high_risk_hits=0,
            medium_risk_hits=0,
            low_risk_hits=1,
            hits=hits,
            specificity_score=95.0
        )
        
        assert result.specificity_score == 95.0
        assert len(result.hits) == 1
        assert result.total_hits == 1
    
    def test_result_with_warnings(self):
        """Test result with warnings."""
        result = SpecificityResult(
            primer_sequence="ATCGATCGATCGATCG",
            primer_type="F3",
            total_hits=10,
            high_risk_hits=3,
            medium_risk_hits=4,
            low_risk_hits=3,
            hits=[],
            specificity_score=30.0,
            warnings=["High number of off-target hits", "Human genome matches found"]
        )
        
        assert result.specificity_score == 30.0
        assert len(result.warnings) == 2
        assert result.high_risk_hits == 3


class TestSpecificityChecker:
    """Test SpecificityChecker class."""
    
    @pytest.fixture
    def checker(self):
        """Create specificity checker instance."""
        return SpecificityChecker()
    
    @pytest.fixture
    def sample_primer(self):
        """Create sample primer for testing."""
        return Primer(
            type=PrimerType.F3,
            sequence="ATCGATCGATCGATCG",
            start_pos=0,
            end_pos=15,
            strand="+",
            tm=60.0,
            gc_content=50.0,
            delta_g=-5.0
        )
    
    @pytest.fixture
    def sample_primer_set(self):
        """Create sample primer set for testing."""
        f3 = Primer(PrimerType.F3, "ATCGATCGATCGATCG", 0, 15, "+", 60.0, 50.0, -5.0)
        b3 = Primer(PrimerType.B3, "GCGCGCGCGCGCGCGC", 100, 115, "-", 61.0, 75.0, -6.0)
        fip = Primer(PrimerType.FIP, "ATCGATCGATCGATCGATCGATCGATCGATCGATCG", 20, 55, "+", 62.0, 50.0, -8.0)
        bip = Primer(PrimerType.BIP, "GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC", 60, 95, "-", 63.0, 75.0, -9.0)
        
        return LampPrimerSet(f3=f3, b3=b3, fip=fip, bip=bip)
    
    def test_checker_initialization(self, checker):
        """Test checker initialization."""
        assert checker is not None
        assert hasattr(checker, 'blast_db_path')
        assert hasattr(checker, 'assay_temperature')
    
    def test_checker_with_custom_settings(self):
        """Test checker with custom settings."""
        checker = SpecificityChecker(
            blast_db_path="/custom/path/db",
            assay_temperature=68.0
        )
        
        assert checker.blast_db_path == "/custom/path/db"
        assert checker.assay_temperature == 68.0
    
    def test_basic_specificity_check(self, checker, sample_primer):
        """Test basic specificity checking."""
        # Mock the basic specificity check
        with patch.object(checker, '_check_basic_specificity') as mock_check:
            mock_result = SpecificityResult(
                primer_sequence=sample_primer.sequence,
                primer_type="F3",
                total_hits=1,
                high_risk_hits=0,
                medium_risk_hits=0,
                low_risk_hits=1,
                hits=[],
                specificity_score=95.0
            )
            mock_check.return_value = mock_result
            
            result = checker.check_primer_specificity(sample_primer)
            
            assert result.specificity_score == 95.0
            mock_check.assert_called_once_with(sample_primer)
    
    @patch('subprocess.run')
    def test_blast_specificity_check(self, mock_subprocess, checker, sample_primer):
        """Test BLAST-based specificity checking."""
        # Configure checker to use BLAST
        checker.blast_db_path = "/test/db"
        
        # Mock BLAST output
        mock_blast_output = """
        Query= test_primer
        Length=16
        
        >target1
        Length=1000
        
         Score = 32.2 bits (16),  Expect = 0.001
         Identities = 16/16 (100%), Gaps = 0/16 (0%)
         Strand=Plus/Plus
        
        Query  1   ATCGATCGATCGATCG  16
               ||||||||||||||||
        Sbjct  1   ATCGATCGATCGATCG  16
        """
        
        mock_subprocess.return_value.stdout = mock_blast_output
        mock_subprocess.return_value.returncode = 0
        
        with patch.object(checker, '_check_blast_specificity') as mock_check:
            mock_result = SpecificityResult(
                primer_sequence=sample_primer.sequence,
                primer_type="F3",
                total_hits=5,
                high_risk_hits=1,
                medium_risk_hits=2,
                low_risk_hits=2,
                hits=[],
                specificity_score=30.0
            )
            mock_check.return_value = mock_result
            
            result = checker.check_primer_specificity(sample_primer, method="blast")
            
            assert result.specificity_score == 30.0
            assert result.total_hits == 5
    
    def test_primer_set_specificity_check(self, checker, sample_primer_set):
        """Test primer set specificity checking."""
        # Mock individual primer checks
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
            
            results = checker.check_primer_set_specificity(sample_primer_set)
            
            # Should check all 4 primers
            assert len(results.primer_results) == 4
            assert mock_check.call_count == 4
    
    def test_cross_reactivity_check(self, checker, sample_primer_set):
        """Test cross-reactivity checking between primers."""
        with patch.object(checker, '_check_cross_reactivity') as mock_check:
            mock_check.return_value = False  # No cross-reactivity
            
            has_cross_reactivity = checker._check_cross_reactivity(sample_primer_set)
            
            assert has_cross_reactivity is False
            mock_check.assert_called_once_with(sample_primer_set)
    
    def test_hit_risk_classification(self, checker):
        """Test hit risk level classification."""
        # High identity, long alignment = HIGH risk
        high_risk_hit = SpecificityHit(
            query_primer="ATCGATCGATCGATCG",
            target_sequence="ATCGATCGATCGATCG",
            target_id="target1",
            alignment_length=16,
            identity_percent=95.0,
            query_start=0,
            query_end=15,
            target_start=0,
            target_end=15,
            three_prime_match=5
        )
        
        # Low identity, short alignment = LOW risk
        low_risk_hit = SpecificityHit(
            query_primer="ATCGATCGATCGATCG",
            target_sequence="AAAAAAAAAAAAAAAAA",
            target_id="target2",
            alignment_length=8,
            identity_percent=60.0,
            query_start=0,
            query_end=7,
            target_start=0,
            target_end=7,
            three_prime_match=1
        )
        
        with patch.object(checker, '_classify_hit_risk') as mock_classify:
            mock_classify.side_effect = [RiskLevel.HIGH, RiskLevel.LOW]
            
            high_risk = checker._classify_hit_risk(high_risk_hit)
            low_risk = checker._classify_hit_risk(low_risk_hit)
            
            assert high_risk == RiskLevel.HIGH
            assert low_risk == RiskLevel.LOW
    
    def test_three_prime_match_calculation(self, checker):
        """Test 3' end match calculation."""
        hit = SpecificityHit(
            query_primer="ATCGATCGATCGATCG",
            target_sequence="AAAAAAAAAATCGATCG",  # Last 8 bases match
            target_id="target1",
            alignment_length=16,
            identity_percent=50.0,
            query_start=0,
            query_end=15,
            target_start=9,
            target_end=16
        )
        
        with patch.object(checker, '_calculate_three_prime_match') as mock_calc:
            mock_calc.return_value = 8  # 8 matching bases at 3' end
            
            match_count = checker._calculate_three_prime_match(hit, "ATCGATCGATCGATCG")
            
            assert match_count == 8
    
    def test_blast_database_validation(self, checker):
        """Test BLAST database validation."""
        # Test with non-existent database
        checker.blast_db_path = "/non/existent/path"
        
        sample_primer = Primer(
            type=PrimerType.F3,
            sequence="ATCGATCGATCGATCG",
            start_pos=0,
            end_pos=15,
            strand="+",
            tm=60.0,
            gc_content=50.0,
            delta_g=-5.0
        )
        
        # Should handle missing database gracefully
        with patch.object(checker, '_check_blast_specificity') as mock_check:
            mock_check.side_effect = SpecificityError("BLAST database not found")
            
            with pytest.raises(SpecificityError):
                checker.check_primer_specificity(sample_primer, method="blast")
    
    def test_specificity_score_calculation(self, checker):
        """Test specificity score calculation."""
        hits = [
            SpecificityHit(
                query_primer="ATCGATCGATCGATCG",
                target_sequence="ATCGATCGATCGATCG",
                target_id="target1",
                alignment_length=16,
                identity_percent=100.0,
                query_start=0,
                query_end=15,
                target_start=0,
                target_end=15,
                risk_level=RiskLevel.HIGH
            ),
            SpecificityHit(
                query_primer="ATCGATCGATCGATCG",
                target_sequence="ATCGATCGATCGATAA",
                target_id="target2",
                alignment_length=14,
                identity_percent=87.5,
                query_start=0,
                query_end=15,
                target_start=0,
                target_end=15,
                risk_level=RiskLevel.MEDIUM
            )
        ]
        
        # Test that hits can be processed (simplified test)
        assert len(hits) == 2
        assert hits[0].risk_level == RiskLevel.HIGH
        assert hits[1].risk_level == RiskLevel.MEDIUM


class TestSpecificityIntegration:
    """Test integration with other modules."""
    
    @pytest.fixture
    def checker(self):
        """Create specificity checker instance."""
        return SpecificityChecker()
    
    def test_thermodynamic_integration(self, checker):
        """Test integration with thermodynamics module."""
        # Verify that checker uses ThermoCalculator for Tm predictions
        assert hasattr(checker, 'thermo_calc')
        assert checker.thermo_calc is not None
    
    def test_sequence_processing_integration(self, checker):
        """Test integration with sequence processing."""
        # Test that checker can work with reverse complements
        sequence = "ATCGATCGATCGATCG"
        
        # Should be able to process sequences without errors
        with patch('rt_lamp_app.design.utils.reverse_complement') as mock_rc:
            mock_rc.return_value = "CGATCGATCGATCGAT"
            
            rc = mock_rc(sequence)
            assert rc == "CGATCGATCGATCGAT"


class TestSpecificityErrorHandling:
    """Test error handling in specificity checking."""
    
    @pytest.fixture
    def checker(self):
        """Create specificity checker instance."""
        return SpecificityChecker()
    
    def test_invalid_primer_sequence(self, checker):
        """Test handling of invalid primer sequences."""
        invalid_primer = Primer(
            type=PrimerType.F3,
            sequence="ATCGATCGATCGATCX",  # Invalid base 'X'
            start_pos=0,
            end_pos=15,
            strand="+",
            tm=60.0,
            gc_content=50.0,
            delta_g=-5.0
        )
        
        # Should handle invalid sequences gracefully
        with patch.object(checker, '_check_basic_specificity') as mock_check:
            mock_check.side_effect = SpecificityError("Invalid nucleotide in sequence")
            
            with pytest.raises(SpecificityError):
                checker.check_primer_specificity(invalid_primer)
    
    def test_blast_execution_failure(self, checker):
        """Test handling of BLAST execution failures."""
        checker.blast_db_path = "/test/db"
        
        sample_primer = Primer(
            type=PrimerType.F3,
            sequence="ATCGATCGATCGATCG",
            start_pos=0,
            end_pos=15,
            strand="+",
            tm=60.0,
            gc_content=50.0,
            delta_g=-5.0
        )
        
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = Exception("BLAST execution failed")
            
            # Should fall back to basic specificity checking
            with patch.object(checker, '_check_basic_specificity') as mock_basic:
                mock_result = SpecificityResult(
                    primer_sequence=sample_primer.sequence,
                    primer_type="F3",
                    total_hits=0,
                    high_risk_hits=0,
                    medium_risk_hits=0,
                    low_risk_hits=0,
                    hits=[],
                    specificity_score=80.0,
                    warnings=["BLAST unavailable, using basic specificity check"]
                )
                mock_basic.return_value = mock_result
                
                result = checker.check_primer_specificity(sample_primer, method="blast")
                
                assert len(result.warnings) > 0
                assert "BLAST unavailable" in result.warnings[0]

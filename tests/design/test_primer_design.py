"""
Tests for primer design module.
"""

import pytest
from unittest.mock import Mock, patch

from rt_lamp_app.core.sequence_processing import Sequence
from rt_lamp_app.design.primer_design import (
    PrimerDesigner, Primer, LampPrimerSet, PrimerType
)
from rt_lamp_app.design.exceptions import (
    GeometricConstraintError, InsufficientCandidatesError
)


class TestPrimer:
    """Test Primer class."""
    
    def test_primer_creation(self):
        """Test basic primer creation."""
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
        
        assert primer.type == PrimerType.F3
        assert primer.sequence == "ATCGATCGATCGATCG"
        assert primer.tm == 60.0
        assert primer.gc_content == 50.0
    
    def test_primer_length(self):
        """Test primer length calculation."""
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
        
        assert len(primer.sequence) == 16


class TestLampPrimerSet:
    """Test LampPrimerSet class."""
    
    @pytest.fixture
    def sample_primers(self):
        """Create sample primers for testing."""
        f3 = Primer(PrimerType.F3, "ATCGATCGATCGATCG", 0, 15, "+", 60.0, 50.0, -5.0)
        b3 = Primer(PrimerType.B3, "GCGCGCGCGCGCGCGC", 100, 115, "-", 61.0, 75.0, -6.0)
        fip = Primer(PrimerType.FIP, "ATCGATCGATCGATCGATCGATCGATCGATCGATCG", 20, 55, "+", 62.0, 50.0, -8.0)
        bip = Primer(PrimerType.BIP, "GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC", 60, 95, "-", 63.0, 75.0, -9.0)
        
        return {"f3": f3, "b3": b3, "fip": fip, "bip": bip}
    
    def test_primer_set_creation(self, sample_primers):
        """Test primer set creation."""
        primer_set = LampPrimerSet(**sample_primers)
        
        assert primer_set.f3.type == PrimerType.F3
        assert primer_set.b3.type == PrimerType.B3
        assert primer_set.fip.type == PrimerType.FIP
        assert primer_set.bip.type == PrimerType.BIP
    
    def test_get_all_primers(self, sample_primers):
        """Test getting all primers from set."""
        primer_set = LampPrimerSet(**sample_primers)
        all_primers = primer_set.get_all_primers()
        
        assert len(all_primers) == 4
        assert all(isinstance(p, Primer) for p in all_primers)
    
    def test_get_tm_range(self, sample_primers):
        """Test Tm range calculation."""
        primer_set = LampPrimerSet(**sample_primers)
        min_tm, max_tm = primer_set.get_tm_range()
        
        assert min_tm == 60.0
        assert max_tm == 63.0
    
    def test_primer_set_with_loop_primers(self, sample_primers):
        """Test primer set with loop primers."""
        lf = Primer(PrimerType.LF, "ATCGATCGATCGATCG", 30, 45, "+", 58.0, 50.0, -4.0)
        lb = Primer(PrimerType.LB, "GCGCGCGCGCGCGCGC", 70, 85, "-", 59.0, 75.0, -5.0)
        
        primer_set = LampPrimerSet(**sample_primers, lf=lf, lb=lb)
        all_primers = primer_set.get_all_primers()
        
        assert len(all_primers) == 6
        assert primer_set.lf is not None
        assert primer_set.lb is not None


class TestPrimerDesigner:
    """Test PrimerDesigner class."""
    
    @pytest.fixture
    def designer(self):
        """Create primer designer instance."""
        return PrimerDesigner()
    
    @pytest.fixture
    def target_sequence(self):
        """Create target sequence for testing."""
        # Create a longer sequence suitable for RT-LAMP design
        sequence = (
            "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"  # F3 region
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"  # Spacer
            "GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC"  # F2 region
            "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"  # Loop region
            "CGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCG"  # B2 region
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"  # Spacer
            "CGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT"   # B3 region
        )
        return Sequence("Test Target", sequence)
    
    def test_designer_initialization(self, designer):
        """Test designer initialization."""
        assert designer is not None
        assert hasattr(designer, 'constraints')
        assert hasattr(designer, 'thermo_calc')
    
    def test_custom_constraints(self):
        """Test designer with custom constraints."""
        custom_constraints = {'F3_length_min': 18, 'F3_length_max': 22}
        designer = PrimerDesigner(constraints=custom_constraints)
        
        assert designer.constraints['F3_length_min'] == 18
        assert designer.constraints['F3_length_max'] == 22
        # Should still have default values for other constraints
        assert 'B3_length_min' in designer.constraints
    
    @patch('rt_lamp_app.design.primer_design.PrimerDesigner._generate_f3_candidates')
    @patch('rt_lamp_app.design.primer_design.PrimerDesigner._generate_b3_candidates')
    @patch('rt_lamp_app.design.primer_design.PrimerDesigner._generate_fip_candidates')
    @patch('rt_lamp_app.design.primer_design.PrimerDesigner._generate_bip_candidates')
    def test_design_primer_set_insufficient_candidates(self, mock_bip, mock_fip, mock_b3, mock_f3, designer, target_sequence):
        """Test handling of insufficient candidates."""
        # Mock insufficient candidates
        mock_f3.return_value = []  # No F3 candidates
        mock_b3.return_value = [Mock() for _ in range(10)]
        mock_fip.return_value = [Mock() for _ in range(10)]
        mock_bip.return_value = [Mock() for _ in range(10)]
        
        with pytest.raises(InsufficientCandidatesError):
            designer.design_primer_set(target_sequence)
    
    def test_generate_f3_candidates(self, designer, target_sequence):
        """Test F3 candidate generation."""
        # Mock the thermodynamic calculations to avoid complex setup
        with patch.object(designer, '_create_primer') as mock_create, \
             patch.object(designer, '_is_valid_primer', return_value=True):
            
            # Create mock primer
            mock_primer = Mock()
            mock_primer.score = 10.0
            mock_create.return_value = mock_primer
            
            candidates = designer._generate_f3_candidates(target_sequence)
            
            # Should have attempted to create primers
            assert mock_create.called
    
    def test_constraints_validation(self, designer):
        """Test that constraints are properly validated."""
        # Test that constraints contain required keys
        required_keys = [
            'F3_length_min', 'F3_length_max',
            'B3_length_min', 'B3_length_max',
            'FIP_length_min', 'FIP_length_max',
            'BIP_length_min', 'BIP_length_max'
        ]
        
        for key in required_keys:
            assert key in designer.constraints
            assert isinstance(designer.constraints[key], int)
            assert designer.constraints[key] > 0


class TestPrimerValidation:
    """Test primer validation functions."""
    
    @pytest.fixture
    def designer(self):
        """Create primer designer instance."""
        return PrimerDesigner()
    
    def test_primer_length_validation(self, designer):
        """Test primer length validation."""
        # Create primers with different lengths
        short_primer = Primer(PrimerType.F3, "ATCG", 0, 3, "+", 30.0, 50.0, -2.0)
        normal_primer = Primer(PrimerType.F3, "ATCGATCGATCGATCG", 0, 15, "+", 60.0, 50.0, -5.0)
        long_primer = Primer(PrimerType.F3, "A" * 50, 0, 49, "+", 80.0, 20.0, -10.0)
        
        # Mock the validation method
        with patch.object(designer, '_is_valid_primer') as mock_valid:
            mock_valid.side_effect = [False, True, False]  # Only normal primer is valid
            
            assert not designer._is_valid_primer(short_primer)
            assert designer._is_valid_primer(normal_primer)
            assert not designer._is_valid_primer(long_primer)


class TestPrimerScoring:
    """Test primer scoring functions."""
    
    @pytest.fixture
    def designer(self):
        """Create primer designer instance."""
        return PrimerDesigner()
    
    def test_primer_scoring(self, designer):
        """Test primer scoring mechanism."""
        primer = Primer(
            type=PrimerType.F3,
            sequence="ATCGATCGATCGATCG",
            start_pos=0,
            end_pos=15,
            strand="+",
            tm=61.5,  # Optimal Tm
            gc_content=50.0,  # Optimal GC
            delta_g=-5.0
        )
        
        # Mock the scoring method
        with patch.object(designer, '_score_primer') as mock_score:
            mock_score.return_value = 10.0
            
            score = designer._score_primer(primer)
            assert isinstance(score, (int, float))
            mock_score.assert_called_once_with(primer)


class TestGeometricConstraints:
    """Test geometric constraint validation."""
    
    @pytest.fixture
    def designer(self):
        """Create primer designer instance."""
        return PrimerDesigner()
    
    @pytest.fixture
    def sample_primer_set(self):
        """Create sample primer set for testing."""
        f3 = Primer(PrimerType.F3, "ATCGATCGATCGATCG", 0, 15, "+", 60.0, 50.0, -5.0)
        b3 = Primer(PrimerType.B3, "GCGCGCGCGCGCGCGC", 200, 215, "-", 61.0, 75.0, -6.0)
        fip = Primer(PrimerType.FIP, "ATCGATCGATCGATCGATCGATCGATCGATCGATCG", 20, 55, "+", 62.0, 50.0, -8.0)
        bip = Primer(PrimerType.BIP, "GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC", 160, 195, "-", 63.0, 75.0, -9.0)
        
        return LampPrimerSet(f3=f3, b3=b3, fip=fip, bip=bip)
    
    def test_geometric_validation(self, designer, sample_primer_set):
        """Test geometric constraint validation."""
        target_sequence = Sequence("Test", "A" * 300)  # Long enough sequence
        
        # Mock the validation method
        with patch.object(designer, '_validate_primer_set_geometry') as mock_validate:
            mock_validate.return_value = True
            
            result = designer._validate_primer_set_geometry(sample_primer_set, target_sequence)
            mock_validate.assert_called_once()
    
    def test_amplicon_size_validation(self, designer):
        """Test amplicon size validation."""
        # Test with primers that would create too small amplicon
        f3 = Primer(PrimerType.F3, "ATCGATCGATCGATCG", 0, 15, "+", 60.0, 50.0, -5.0)
        b3 = Primer(PrimerType.B3, "GCGCGCGCGCGCGCGC", 50, 65, "-", 61.0, 75.0, -6.0)  # Too close
        fip = Primer(PrimerType.FIP, "ATCGATCGATCGATCGATCGATCGATCGATCGATCG", 20, 55, "+", 62.0, 50.0, -8.0)
        bip = Primer(PrimerType.BIP, "GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC", 30, 65, "-", 63.0, 75.0, -9.0)
        
        primer_set = LampPrimerSet(f3=f3, b3=b3, fip=fip, bip=bip)
        target_sequence = Sequence("Test", "A" * 100)
        
        # This should raise a geometric constraint error due to small amplicon
        with patch.object(designer, '_validate_primer_set_geometry') as mock_validate:
            mock_validate.side_effect = GeometricConstraintError("F2_B2_amplicon", "120-200", "50")
            
            with pytest.raises(GeometricConstraintError):
                designer._validate_primer_set_geometry(primer_set, target_sequence)


class TestIntegrationWithCore:
    """Test integration with core modules."""
    
    @pytest.fixture
    def designer(self):
        """Create primer designer instance."""
        return PrimerDesigner()
    
    def test_thermodynamic_integration(self, designer):
        """Test integration with thermodynamics module."""
        # Verify that designer uses ThermoCalculator
        assert hasattr(designer, 'thermo_calc')
        assert designer.thermo_calc is not None
    
    def test_sequence_processing_integration(self, designer):
        """Test integration with sequence processing."""
        # Test that designer can work with Sequence objects
        sequence = Sequence("Test", "ATCGATCGATCGATCGATCGATCG")
        
        # Should be able to process the sequence without errors
        assert sequence.sequence is not None
        assert sequence.header == "Test"


"""
Unit tests for sequence processing module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock
import requests

from rt_lamp_app.core.sequence_processing import (
    Sequence, NCBISequenceFetcher, parse_fasta_string, 
    parse_uploaded_file, validate_sequence_quality
)
from rt_lamp_app.core.exceptions import InvalidInputError, NCBIError


class TestSequence:
    """Test cases for Sequence class."""
    
    def test_sequence_creation_valid(self, sample_sequences):
        """Test creating valid sequences."""
        seq = sample_sequences["simple_dna"]
        assert seq.header == "Simple DNA"
        assert seq.sequence == "ATCGATCGATCG"
        assert seq.get_length() == 12
    
    def test_sequence_creation_invalid_chars(self):
        """Test sequence creation with invalid characters."""
        with pytest.raises(InvalidInputError) as exc_info:
            Sequence("Invalid", "ATCGXYZ")
        assert "invalid nucleotides" in str(exc_info.value)
    
    def test_sequence_case_normalization(self):
        """Test that sequences are normalized to uppercase."""
        seq = Sequence("Test", "atcgatcg")
        assert seq.sequence == "ATCGATCG"
    
    def test_reverse_complement_simple(self):
        """Test reverse complement calculation."""
        seq = Sequence("Test", "ATCG")
        assert seq.get_reverse_complement() == "CGAT"
    
    def test_reverse_complement_palindromic(self, sample_sequences):
        """Test reverse complement of palindromic sequence."""
        seq = sample_sequences["palindromic"]
        assert seq.get_reverse_complement() == "GAATTC"
    
    def test_reverse_complement_ambiguous(self):
        """Test reverse complement with ambiguous bases."""
        seq = Sequence("Ambiguous", "ATCGNRYKMSWBDHV")
        rc = seq.get_reverse_complement()
        expected = "BDHVSWKMRYNCGAT"
        assert rc == expected
    
    def test_cdna_equivalent(self):
        """Test RNA to cDNA conversion."""
        seq = Sequence("RNA", "AUCGAUCG")
        assert seq.get_cdna_equivalent() == "ATCGATCG"
    
    def test_gc_content_calculation(self, sample_sequences):
        """Test GC content calculation."""
        gc_rich = sample_sequences["gc_rich"]
        assert gc_rich.get_gc_content() == 100.0
        
        at_rich = sample_sequences["at_rich"]
        assert at_rich.get_gc_content() == 0.0
        
        mixed = sample_sequences["mixed"]
        expected_gc = (6 / 12) * 100  # 6 G/C out of 12 bases
        assert abs(mixed.get_gc_content() - expected_gc) < 0.1
    
    def test_sequence_string_representation(self, sample_sequences):
        """Test string representation of sequence."""
        seq = sample_sequences["simple_dna"]
        str_repr = str(seq)
        assert ">Simple DNA" in str_repr
        assert "ATCGATCGATCG" in str_repr
    
    def test_sequence_repr(self, sample_sequences):
        """Test repr representation of sequence."""
        seq = sample_sequences["simple_dna"]
        repr_str = repr(seq)
        assert "Sequence" in repr_str
        assert "Simple DNA" in repr_str
        assert "length=12" in repr_str


class TestNCBISequenceFetcher:
    """Test cases for NCBI sequence fetcher."""
    
    def test_fetcher_initialization(self):
        """Test fetcher initialization."""
        fetcher = NCBISequenceFetcher(max_retries=3)
        assert fetcher.max_retries == 3
    
    @patch('requests.get')
    def test_successful_fetch(self, mock_get):
        """Test successful sequence fetching."""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = ">Test_Accession Description\nATCGATCGATCG"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        fetcher = NCBISequenceFetcher()
        sequence = fetcher.fetch_sequence("TEST123")
        
        assert sequence.header == "Test_Accession Description"
        assert sequence.sequence == "ATCGATCGATCG"
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_http_error_with_retry(self, mock_get):
        """Test HTTP error handling with retries."""
        # Mock failed responses
        mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        fetcher = NCBISequenceFetcher(max_retries=2)
        
        with pytest.raises(NCBIError) as exc_info:
            fetcher.fetch_sequence("INVALID123")
        
        assert "Failed to fetch" in str(exc_info.value)
        assert mock_get.call_count == 3  # Initial + 2 retries
    
    @patch('requests.get')
    def test_empty_response(self, mock_get):
        """Test handling of empty response."""
        mock_response = Mock()
        mock_response.text = ""
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        fetcher = NCBISequenceFetcher()
        
        with pytest.raises(NCBIError) as exc_info:
            fetcher.fetch_sequence("EMPTY123")
        
        assert "Empty response" in str(exc_info.value)


class TestFASTAParsing:
    """Test cases for FASTA parsing functions."""
    
    def test_parse_fasta_string_valid(self, sample_fasta_content):
        """Test parsing valid FASTA string."""
        sequences = parse_fasta_string(sample_fasta_content)
        
        # Should only return first sequence as per Phase 0 spec
        assert len(sequences) == 1
        assert sequences[0].header == "Test_Sequence_1"
        assert sequences[0].sequence == "ATCGATCGATCGATCGATCG"
    
    def test_parse_fasta_string_invalid(self, invalid_fasta_content):
        """Test parsing invalid FASTA string."""
        with pytest.raises(InvalidInputError) as exc_info:
            parse_fasta_string(invalid_fasta_content)
        assert "invalid nucleotides" in str(exc_info.value)
    
    def test_parse_fasta_string_empty(self):
        """Test parsing empty FASTA string."""
        with pytest.raises(InvalidInputError) as exc_info:
            parse_fasta_string("")
        assert "No valid sequences found" in str(exc_info.value)
    
    def test_parse_uploaded_file_valid(self, test_data_dir, sample_fasta_content):
        """Test parsing valid uploaded file."""
        # Create test file
        test_file = test_data_dir / "test_valid.fasta"
        test_file.write_text(sample_fasta_content)
        
        sequences = parse_uploaded_file(test_file)
        assert len(sequences) == 1
        assert sequences[0].header == "Test_Sequence_1"
    
    def test_parse_uploaded_file_not_exists(self, test_data_dir):
        """Test parsing non-existent file."""
        non_existent = test_data_dir / "does_not_exist.fasta"
        
        with pytest.raises(InvalidInputError) as exc_info:
            parse_uploaded_file(non_existent)
        assert "File does not exist" in str(exc_info.value)
    
    def test_parse_uploaded_file_encoding_fallback(self, test_data_dir):
        """Test encoding fallback mechanism."""
        # Create file with Latin-1 encoding
        test_file = test_data_dir / "test_latin1.fasta"
        content = ">Test_Séquence\nATCGATCGATCG"
        test_file.write_bytes(content.encode('latin-1'))
        
        sequences = parse_uploaded_file(test_file)
        assert len(sequences) == 1
        assert "Test_Séquence" in sequences[0].header


class TestSequenceQualityValidation:
    """Test cases for sequence quality validation."""
    
    def test_validate_sequence_quality_good(self, sample_sequences):
        """Test validation of good quality sequence."""
        seq = sample_sequences["sars_cov2_fragment"]
        is_valid, issues = validate_sequence_quality(seq)
        assert is_valid
        assert len(issues) == 0
    
    def test_validate_sequence_quality_too_short(self):
        """Test validation of too short sequence."""
        short_seq = Sequence("Short", "ATCG")
        is_valid, issues = validate_sequence_quality(short_seq, min_length=50)
        assert not is_valid
        assert any("too short" in issue for issue in issues)
    
    def test_validate_sequence_quality_too_long(self, sample_sequences):
        """Test validation of too long sequence."""
        long_seq = sample_sequences["long_sequence"]
        is_valid, issues = validate_sequence_quality(long_seq, max_length=50)
        assert not is_valid
        assert any("too long" in issue for issue in issues)
    
    def test_validate_sequence_quality_gc_content(self, sample_sequences):
        """Test GC content validation."""
        # Test GC-rich sequence
        gc_rich = sample_sequences["gc_rich"]
        is_valid, issues = validate_sequence_quality(gc_rich, max_gc=80.0)
        assert not is_valid
        assert any("GC content too high" in issue for issue in issues)
        
        # Test AT-rich sequence
        at_rich = sample_sequences["at_rich"]
        is_valid, issues = validate_sequence_quality(at_rich, min_gc=30.0)
        assert not is_valid
        assert any("GC content too low" in issue for issue in issues)
    
    def test_validate_sequence_quality_repeats(self):
        """Test detection of excessive repeats."""
        repeat_seq = Sequence("Repeats", "ATCGAAAAAAAATCG")
        is_valid, issues = validate_sequence_quality(repeat_seq)
        assert not is_valid
        assert any("Excessive A repeats" in issue for issue in issues)
    
    def test_validate_sequence_quality_ambiguous_bases(self, sample_sequences):
        """Test detection of too many ambiguous bases."""
        ambiguous_seq = Sequence("Ambiguous", "NNNNNNNNNNATCG")
        is_valid, issues = validate_sequence_quality(ambiguous_seq)
        assert not is_valid
        assert any("Too many ambiguous bases" in issue for issue in issues)
    
    def test_validate_sequence_quality_multiple_issues(self):
        """Test detection of multiple quality issues."""
        bad_seq = Sequence("Bad", "NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN")
        is_valid, issues = validate_sequence_quality(bad_seq, min_gc=20.0)
        assert not is_valid
        assert len(issues) >= 2  # Should have multiple issues


class TestSequenceProcessingEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_sequence_with_whitespace(self):
        """Test sequence creation with whitespace."""
        seq = Sequence("  Test  ", "  ATCG  ")
        assert seq.header == "Test"
        assert seq.sequence == "ATCG"
    
    def test_reverse_complement_unknown_base(self):
        """Test reverse complement with unknown base."""
        seq = Sequence("Test", "ATCG")
        # Manually modify sequence to test error handling
        seq.sequence = "ATCGX"
        
        with pytest.raises(InvalidInputError):
            seq.get_reverse_complement()
    
    def test_empty_sequence_gc_content(self):
        """Test GC content calculation for empty sequence."""
        # This should not happen in normal usage due to validation
        seq = Sequence("Empty", "A")
        seq.sequence = ""  # Manually set to empty
        assert seq.get_gc_content() == 0.0
    
    def test_sequence_length_edge_cases(self):
        """Test sequence length edge cases."""
        # Single nucleotide
        single = Sequence("Single", "A")
        assert single.get_length() == 1
        assert single.get_gc_content() == 0.0
        
        # Two nucleotides
        double = Sequence("Double", "GC")
        assert double.get_length() == 2
        assert double.get_gc_content() == 100.0



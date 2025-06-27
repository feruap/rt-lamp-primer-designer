
"""
Pytest configuration and fixtures for RT-LAMP tests.
"""

import pytest
from pathlib import Path
from rt_lamp_app.core.sequence_processing import Sequence
from rt_lamp_app.core.thermodynamics import ThermoCalculator


@pytest.fixture
def sample_sequences():
    """Provide sample sequences for testing."""
    return {
        "simple_dna": Sequence("Simple DNA", "ATCGATCGATCG"),
        "gc_rich": Sequence("GC Rich", "GCGCGCGCGCGC"),
        "at_rich": Sequence("AT Rich", "ATATATATATATAT"),
        "mixed": Sequence("Mixed", "ATCGGCTAGCTA"),
        "with_ambiguous": Sequence("Ambiguous", "ATCGNRYKMSWB"),
        "palindromic": Sequence("Palindromic", "GAATTC"),
        "long_sequence": Sequence("Long", "ATCGATCGATCG" * 10),
        "sars_cov2_fragment": Sequence(
            "SARS-CoV-2 N gene fragment",
            "GGGGAACTTCTCCTGCTAGAATGGCTGGCAATGGCGGTGATGCTGCTCTTGCTTTGCTGCTGCTTGACAGATTGAACCAGCTTGAGAGCAAAATGTCTGGTAAAGGCCAACAACAACAAGGCCAAACTGTCACTAAGAAATCTGCTGCTGAGGCTTCTAAGAAGCCTCGGCAAAAACGTACTGCCACTAAAGCATACAATGTAACACAAGCTTTCGGCAGACGTGGTCCAGAACAAACCCAAGGAAATTTTGGGGACCAGGAACTAATCAGACAAGGAACTGATTACAAACATTGGCCGCAAATTGCACAATTTGCCCCCAGCGCTTCAGCGTTCTTCGGAATGTCGCGCATTGGCATGGAAGTCACACCTTCGGGAACGTGGTTGACCTACACAGGTGCCATCAAATTGGATGACAAAGATCCAAATTTCAAAGATCAAGTCATTTTGCTGAATAAGCATATTGACGCATACAAAACATTCCCACCAACAGAGCCTAAAAAGGACAAAAAGAAGAAGGCTGATGAAACTCAAGCCTTACCGCAGAGACAGAAGAAACAGCAAACTGTGACTCTTCTTCCTGCTGCAGATTTGGATGATTTCTCCAAACAATTGCAACAATCCATGAGCAGTGCTGACTCAACTCAGGCCTAA"
        )
    }


@pytest.fixture
def thermo_calculator():
    """Provide ThermoCalculator instance."""
    return ThermoCalculator()


@pytest.fixture
def test_data_dir():
    """Provide path to test data directory."""
    test_dir = Path(__file__).parent
    data_dir = test_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture
def sample_fasta_content():
    """Provide sample FASTA content for testing."""
    return """
>Test_Sequence_1
ATCGATCGATCGATCGATCG
>Test_Sequence_2
GCGCGCGCGCGCGCGCGCGC
>Test_Sequence_3_with_description Additional info here
ATATATATATATATATATATAT
""".strip()


@pytest.fixture
def invalid_fasta_content():
    """Provide invalid FASTA content for testing."""
    return """
>Invalid_Sequence_With_Bad_Chars
ATCGXYZQWERTY
""".strip()


@pytest.fixture
def primer_sequences():
    """Provide realistic primer sequences for testing."""
    return {
        "f3_primer": "GCGCGCGCGCGCGCGCGC",
        "b3_primer": "ATATATATATATATATAT",
        "fip_primer": "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG",
        "bip_primer": "GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC",
        "loop_f": "ATCGATCGATCGATCG",
        "loop_b": "GCGCGCGCGCGCGCGC"
    }



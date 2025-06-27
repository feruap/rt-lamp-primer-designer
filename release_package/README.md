# RT-LAMP Primer Design Application

A comprehensive real-time Loop-mediated Isothermal Amplification (RT-LAMP) primer design tool with advanced consensus sequence analysis and multiplex capabilities.

## Project Structure

```
rt_lamp_app/
├── src/rt_lamp_app/
│   ├── core/                    # Core LAMP primer design functionality
│   │   ├── primer_design.py     # Main primer design logic
│   │   ├── sequence_analysis.py # Sequence analysis utilities
│   │   ├── thermodynamics.py    # Thermodynamic calculations
│   │   └── validation.py        # Primer validation
│   ├── advanced/                # Advanced features (Phase 2 & 3)
│   │   ├── msa.py              # Multiple sequence alignment
│   │   ├── consensus_analysis.py # Consensus sequence analysis
│   │   ├── consensus_orchestrator.py # Consensus-based design
│   │   └── multiplex_orchestrator.py # Multiplex primer design
│   ├── utils/                   # Utility modules
│   │   ├── file_io.py          # File input/output operations
│   │   ├── config.py           # Configuration management
│   │   └── exceptions.py       # Custom exceptions
│   └── cli/                     # Command-line interface
│       └── main.py             # CLI entry point
├── tests/                       # Test suite
│   ├── test_core/              # Core functionality tests
│   └── test_advanced/          # Advanced features tests
├── examples/                    # Example usage and data
├── docs/                       # Documentation
└── requirements.txt            # Dependencies
```

## Features

### Phase 1: Core LAMP Primer Design ✅
- **Primer Design Engine**: Complete LAMP primer set generation (F3, B3, FIP, BIP, LF, LB)
- **Thermodynamic Analysis**: Melting temperature calculations, secondary structure prediction
- **Sequence Analysis**: GC content analysis, primer specificity checks
- **Validation System**: Comprehensive primer validation with customizable parameters
- **File I/O**: Support for FASTA input and structured output formats

### Phase 2: Advanced Consensus Analysis ✅
- **Multiple Sequence Alignment**: Integration with MUSCLE for high-quality alignments
- **Consensus Generation**: Statistical consensus sequence generation with confidence scoring
- **Variability Analysis**: Identification of conserved and variable regions
- **Quality Assessment**: Alignment quality metrics and validation

### Phase 3: Multiplex Orchestrator 🚧
- **Multiplex Design**: Simultaneous primer design for multiple targets
- **Cross-reactivity Prevention**: Advanced algorithms to prevent primer interactions
- **Optimization**: Multi-objective optimization for primer set compatibility

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd rt_lamp_app

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

## Quick Start

### Basic LAMP Primer Design

```python
from rt_lamp_app.core.primer_design import LAMPPrimerDesigner
from rt_lamp_app.core.sequence_analysis import SequenceAnalyzer

# Initialize designer
designer = LAMPPrimerDesigner()

# Design primers for a target sequence
target_sequence = "ATGGAGAGCCTTGTCCCTGGTTTCAACGAGAAAACACACGTCC..."
primer_sets = designer.design_primers(target_sequence)

# Validate primers
for primer_set in primer_sets:
    validation_result = designer.validate_primer_set(primer_set)
    print(f"Primer set validation: {validation_result.is_valid}")
```

### Consensus-Based Design

```python
from rt_lamp_app.advanced.consensus_orchestrator import ConsensusOrchestrator

# Initialize orchestrator
orchestrator = ConsensusOrchestrator()

# Design primers from multiple sequences
sequences = [
    "ATGGAGAGCCTTGTCCCTGGTTTCAACGAGAAAACACACGTCC...",
    "ATGGAGAGCCTTGTCCCTGGTTTCAACGAGAAAACACACGTCC...",
    # ... more sequences
]

# Generate consensus-based primers
consensus_result = orchestrator.design_consensus_primers(
    sequences=sequences,
    target_name="SARS-CoV-2_spike"
)

print(f"Consensus primers designed: {len(consensus_result.primer_sets)}")
```

### Command Line Interface

```bash
# Basic primer design
python -m rt_lamp_app.cli.main design --input sequences.fasta --output primers.json

# Consensus-based design
python -m rt_lamp_app.cli.main consensus --input multiple_sequences.fasta --output consensus_primers.json

# Multiplex design
python -m rt_lamp_app.cli.main multiplex --input targets.fasta --output multiplex_primers.json
```

## Configuration

The application uses a flexible configuration system. Default parameters can be overridden:

```python
from rt_lamp_app.utils.config import Config

# Load custom configuration
config = Config.from_file("custom_config.yaml")

# Or modify parameters programmatically
config.primer_design.f3_length_range = (18, 25)
config.primer_design.gc_content_range = (40, 65)
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test modules
python -m pytest tests/test_core/
python -m pytest tests/test_advanced/

# Run with coverage
python -m pytest tests/ --cov=rt_lamp_app --cov-report=html
```

## Development Status

- ✅ **Phase 1 Complete**: Core LAMP primer design functionality
- ✅ **Phase 2 Complete**: Advanced consensus analysis capabilities
- 🚧 **Phase 3 In Progress**: Multiplex orchestrator implementation

## Key Classes and Methods

### Core Classes
- `LAMPPrimerDesigner`: Main primer design engine
- `SequenceAnalyzer`: Sequence analysis utilities
- `ThermodynamicsCalculator`: Thermodynamic property calculations
- `PrimerValidator`: Primer validation and quality assessment

### Advanced Classes
- `MSAProcessor`: Multiple sequence alignment processing
- `ConsensusAnalyzer`: Consensus sequence generation and analysis
- `ConsensusOrchestrator`: High-level consensus-based primer design
- `MultiplexOrchestrator`: Multiplex primer design coordination

## Dependencies

- **BioPython**: Sequence analysis and file I/O
- **NumPy**: Numerical computations
- **Pandas**: Data manipulation and analysis
- **MUSCLE**: Multiple sequence alignment (external tool)
- **Primer3**: Primer design algorithms
- **ViennaRNA**: RNA secondary structure prediction

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this software in your research, please cite:

```
RT-LAMP Primer Design Tool
[Your Institution/Organization]
[Year]
```

## Support

For questions, issues, or contributions, please:
- Open an issue on GitHub
- Contact the development team
- Check the documentation in the `docs/` directory

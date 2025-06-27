# RT-LAMP Application Usage Examples

## Quick Start Guide

### 1. Basic Primer Design

#### Command Line Usage (if applicable)
```bash
# Run the GUI application
./RT_LAMP_Designer

# For headless environments
QT_QPA_PLATFORM=offscreen ./RT_LAMP_Designer
```

#### GUI Workflow
1. **Launch Application**: Double-click `RT_LAMP_Designer` or run from terminal
2. **Load Sequence**: 
   - Click "Load Sequence" or use File → Open
   - Select a FASTA file (e.g., `test_data/sars2_n.fasta`)
3. **Configure Parameters**:
   - Set target region (start/end positions)
   - Adjust primer length constraints
   - Set thermodynamic parameters
4. **Design Primers**: Click "Design Primers"
5. **Review Results**: Examine primer sets in the results panel
6. **Export Results**: Save results as Excel, CSV, or text format

### 2. Working with Sample Data

The package includes sample SARS-CoV-2 data for testing:

```bash
# Sample file location
test_data/sars2_n.fasta
```

**Sample Sequence Information**:
- **Target**: SARS-CoV-2 Nucleocapsid (N) gene
- **Length**: ~1,260 nucleotides
- **Use Case**: Ideal for testing RT-LAMP primer design

#### Step-by-Step with Sample Data
1. Launch RT-LAMP Designer
2. Load `test_data/sars2_n.fasta`
3. Use default parameters or try these settings:
   - **Target Region**: 200-800 (nucleotides)
   - **F3/B3 Length**: 18-22 bp
   - **FIP/BIP Length**: 40-60 bp
   - **Temperature**: 60-65°C
4. Click "Design Primers"
5. Review the generated primer sets

### 3. Advanced Features

#### Multiple Sequence Alignment
1. Load multiple FASTA sequences
2. Select "Advanced" → "Multiple Sequence Alignment"
3. Generate consensus sequence
4. Design primers based on consensus

#### Specificity Checking
1. After primer design, click "Check Specificity"
2. Configure BLAST parameters
3. Review specificity results
4. Filter primers based on specificity scores

#### Batch Processing
1. Select "Batch" → "Process Multiple Files"
2. Choose input directory with FASTA files
3. Configure output directory
4. Set processing parameters
5. Start batch processing

### 4. Parameter Optimization

#### Thermodynamic Parameters
```
Recommended Settings for RT-LAMP:
- Reaction Temperature: 60-65°C
- Salt Concentration: 50 mM
- Mg²⁺ Concentration: 8 mM
- dNTP Concentration: 1.4 mM
```

#### Primer Length Constraints
```
Standard LAMP Primer Lengths:
- F3/B3: 18-22 nucleotides
- F2/B2: 18-22 nucleotides
- F1c/B1c: 18-22 nucleotides
- FIP/BIP: 40-60 nucleotides (F1c+F2 or B1c+B2)
```

#### Loop Primers (Optional)
```
Loop Primer Settings:
- LF/LB Length: 15-25 nucleotides
- Position: Between F2-F1c or B2-B1c regions
- Tm: 5-10°C lower than main primers
```

### 5. Results Interpretation

#### Primer Set Quality Indicators
- **Tm Values**: Should be within 5°C of each other
- **GC Content**: 40-60% recommended
- **Secondary Structures**: Minimal hairpins and dimers
- **Specificity Score**: >90% for target specificity

#### Output Files
- **Excel Format**: Comprehensive results with multiple sheets
- **CSV Format**: Tabular data for further analysis
- **Text Format**: Human-readable summary
- **FASTA Format**: Primer sequences for synthesis

### 6. Troubleshooting Common Issues

#### No Primers Found
**Possible Causes**:
- Target region too short
- Stringent parameters
- Poor sequence quality

**Solutions**:
- Expand target region
- Relax length constraints
- Check sequence for ambiguous bases

#### Poor Primer Quality
**Possible Causes**:
- High GC content regions
- Repetitive sequences
- Secondary structures

**Solutions**:
- Try different target regions
- Adjust thermodynamic parameters
- Use consensus sequences for variable regions

#### Slow Performance
**Possible Causes**:
- Large sequences
- Complex secondary structures
- Limited system resources

**Solutions**:
- Process smaller regions
- Use batch processing for multiple sequences
- Close other applications

### 7. Export and Synthesis

#### Primer Ordering Format
The application can export primers in synthesis-ready format:

```
Primer Name: SARS2_N_F3
Sequence: 5'-ATGCTGCAATCGTGCTACAA-3'
Length: 20 bp
Tm: 58.2°C
GC%: 45.0%

Primer Name: SARS2_N_B3
Sequence: 5'-GACTGCCGCCTCTGCTC-3'
Length: 17 bp
Tm: 59.1°C
GC%: 70.6%
```

#### Quality Control Checklist
Before ordering primers:
- [ ] Verify sequence accuracy
- [ ] Check Tm calculations
- [ ] Confirm no cross-reactivity
- [ ] Validate primer concentrations
- [ ] Review synthesis modifications (if any)

### 8. Integration with Laboratory Workflow

#### Pre-Design Phase
1. **Target Selection**: Choose conserved regions
2. **Sequence Quality**: Verify sequence accuracy
3. **Literature Review**: Check existing primer sets

#### Design Phase
1. **Parameter Setting**: Use validated parameters
2. **Multiple Designs**: Generate several primer sets
3. **Quality Assessment**: Evaluate all metrics

#### Post-Design Phase
1. **In Silico Validation**: Check against databases
2. **Primer Synthesis**: Order from reliable suppliers
3. **Laboratory Testing**: Validate experimentally

### 9. Performance Benchmarks

#### Typical Processing Times
- **Single Sequence (1-5 kb)**: 10-30 seconds
- **Multiple Sequences (5-10)**: 1-5 minutes
- **Large Genome Regions (>10 kb)**: 2-10 minutes
- **Batch Processing (10+ files)**: 5-30 minutes

#### System Requirements for Optimal Performance
- **RAM**: 8GB+ recommended
- **CPU**: Multi-core processor
- **Storage**: SSD for faster file I/O
- **Display**: 1920x1080+ for GUI

### 10. Best Practices

#### Sequence Preparation
- Use high-quality, verified sequences
- Remove vector sequences and adapters
- Check for ambiguous nucleotides
- Validate sequence orientation

#### Parameter Selection
- Start with default parameters
- Adjust based on experimental requirements
- Consider target organism characteristics
- Account for reaction conditions

#### Result Validation
- Always validate computationally designed primers
- Test multiple primer sets when possible
- Consider experimental controls
- Document parameter choices and results

---

## Support Resources

- **Documentation**: See README.md for detailed information
- **Source Code**: Available in src/ directory for customization
- **Sample Data**: Use test_data/ for learning and testing
- **Troubleshooting**: Refer to deployment guides for platform-specific issues

For additional support or questions, refer to the application documentation or rebuild from source code with modifications as needed.

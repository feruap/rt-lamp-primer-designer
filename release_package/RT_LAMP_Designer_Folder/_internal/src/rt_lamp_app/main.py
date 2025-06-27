
"""
Main entry point for the RT-LAMP Primer Design Application.
"""

import sys
import logging
from pathlib import Path

from rt_lamp_app.config import setup_logging
from rt_lamp_app.logger import get_logger


def main():
    """Main entry point for the application."""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting RT-LAMP Primer Design Application")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {Path.cwd()}")
    
    try:
        # For Phase 0, just demonstrate core modules
        from rt_lamp_app.core.sequence_processing import Sequence
        from rt_lamp_app.core.thermodynamics import ThermoCalculator
        
        # Example usage
        logger.info("Testing core modules...")
        
        # Test sequence processing
        test_seq = Sequence("Test", "ATCGATCGATCG")
        logger.info(f"Test sequence: {test_seq.sequence}")
        logger.info(f"Reverse complement: {test_seq.get_reverse_complement()}")
        
        # Test thermodynamics
        calc = ThermoCalculator()
        tm = calc.calculate_tm("ATCGATCGATCG", na_conc_M=0.05)
        logger.info(f"Calculated Tm: {tm:.2f}°C")
        
        logger.info("Core modules working correctly!")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


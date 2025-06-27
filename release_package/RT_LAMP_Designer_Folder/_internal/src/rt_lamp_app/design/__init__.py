
"""
Design modules for RT-LAMP primer design.

This package contains modules for primer design, specificity checking,
and related utilities for RT-LAMP assay development.
"""

from .primer_design import PrimerDesigner, Primer, LampPrimerSet
from .specificity_checker import SpecificityChecker, SpecificityResult
from .exceptions import DesignError, GeometricConstraintError, SpecificityError
from .utils import reverse_complement, calculate_distance, validate_primer_geometry

__all__ = [
    'PrimerDesigner',
    'Primer', 
    'LampPrimerSet',
    'SpecificityChecker',
    'SpecificityResult',
    'DesignError',
    'GeometricConstraintError', 
    'SpecificityError',
    'reverse_complement',
    'calculate_distance',
    'validate_primer_geometry'
]

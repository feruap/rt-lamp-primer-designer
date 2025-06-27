
"""
Design-specific exceptions for RT-LAMP primer design.
"""

from rt_lamp_app.core.exceptions import PrimerDesignError


class DesignError(PrimerDesignError):
    """Base exception for design module errors."""
    pass


class GeometricConstraintError(DesignError):
    """Raised when geometric constraints are violated."""
    
    def __init__(self, constraint_type: str, expected: str, actual: str):
        self.constraint_type = constraint_type
        self.expected = expected
        self.actual = actual
        super().__init__(f"Geometric constraint violation - {constraint_type}: expected {expected}, got {actual}")


class SpecificityError(DesignError):
    """Raised when specificity checking fails."""
    
    def __init__(self, message: str, risk_level: str = "unknown"):
        self.risk_level = risk_level
        super().__init__(f"Specificity error ({risk_level}): {message}")


class PrimerOptimizationError(DesignError):
    """Raised when primer optimization fails."""
    pass


class InsufficientCandidatesError(DesignError):
    """Raised when insufficient primer candidates are generated."""
    
    def __init__(self, primer_type: str, found: int, required: int):
        self.primer_type = primer_type
        self.found = found
        self.required = required
        super().__init__(f"Insufficient {primer_type} candidates: found {found}, required {required}")


"""
Configuration and parameter presets for RT-LAMP primer design.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any


# Application paths
APP_DIR = Path(__file__).parent
PROJECT_ROOT = APP_DIR.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


def setup_logging(level: str = "INFO") -> None:
    """Setup application logging configuration."""
    log_file = LOGS_DIR / "rt_lamp_app.log"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


# Default design parameters for LAMP primer design
DEFAULT_DESIGN_PARAMETERS = {
    "primer_constraints": {
        "f3_b3": {
            "length_range": (18, 22),
            "tm_range": (58, 62),
            "gc_content_range": (40, 60)
        },
        "fip_bip": {
            "length_range": (40, 60),
            "tm_range": (60, 65),
            "gc_content_range": (40, 60)
        },
        "loop_primers": {
            "length_range": (15, 25),
            "tm_range": (55, 65),
            "gc_content_range": (40, 60)
        }
    },
    "geometric_constraints": {
        "f3_f2_distance": (0, 60),
        "f2_f1c_distance": (40, 60),
        "b1c_b2_distance": (40, 60),
        "b2_b3_distance": (0, 60),
        "amplicon_size_range": (120, 300)
    },
    "thermodynamic_thresholds": {
        "hairpin_dg_threshold": -2.0,
        "dimer_dg_threshold": -5.0,
        "end_stability_dg_threshold": -4.0
    },
    "salt_conditions": {
        "na_conc_M": 0.05,
        "mg_conc_M": 0.002,
        "dntp_conc_M": 0.0008
    }
}

# Parameter presets for different applications
PARAMETER_PRESETS = {
    "Viral_Detection": {
        "description": "Optimized for viral RNA detection",
        "primer_constraints": {
            "f3_b3": {
                "length_range": (18, 20),
                "tm_range": (58, 60),
                "gc_content_range": (45, 55)
            },
            "fip_bip": {
                "length_range": (42, 50),
                "tm_range": (62, 65),
                "gc_content_range": (45, 55)
            }
        },
        "thermodynamic_thresholds": {
            "hairpin_dg_threshold": -1.5,
            "dimer_dg_threshold": -4.0,
            "end_stability_dg_threshold": -3.5
        }
    },
    "Gene_Expression": {
        "description": "Optimized for gene expression analysis",
        "primer_constraints": {
            "f3_b3": {
                "length_range": (20, 22),
                "tm_range": (60, 62),
                "gc_content_range": (40, 60)
            },
            "fip_bip": {
                "length_range": (45, 55),
                "tm_range": (63, 67),
                "gc_content_range": (40, 60)
            }
        },
        "thermodynamic_thresholds": {
            "hairpin_dg_threshold": -2.5,
            "dimer_dg_threshold": -6.0,
            "end_stability_dg_threshold": -4.5
        }
    }
}

# Performance and file limits
PERFORMANCE_CONFIG = {
    "max_sequence_length": 5000,
    "max_file_size_mb": 10,
    "max_concurrent_threads": max(1, os.cpu_count() - 1) if os.cpu_count() else 1,
    "timeout_seconds": 300
}

# External tool paths (to be configured by user)
EXTERNAL_TOOLS = {
    "blast_path": None,  # Will be auto-detected or set by user
    "mafft_path": None   # Will be auto-detected or set by user
}


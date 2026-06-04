"""Compatibility wrapper for stdlib CLI inspection helpers.

The packaged implementation lives in ``sona.stdlib_cli_commands`` so installed
wheel commands do not depend on the source-tree ``scripts/`` directory.
"""

from sona.stdlib_cli_commands import (
    stdlib_build_info,
    stdlib_doctor_check,
    stdlib_probe,
)

__all__ = [
    "stdlib_build_info",
    "stdlib_doctor_check",
    "stdlib_probe",
]

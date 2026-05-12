"""
ProblemTypes — language-agnostic input/output types for a problem.

Loaded from the `types_canonical` block in each problem JSON (populated by
scripts/migrate_problem_types.py). Consumed by core/test_codegen/ to
render per-language test runners.
"""

from dataclasses import dataclass, field
from typing import List

from bytedojo.core.models.canonical_type import CanonicalType


@dataclass
class CanonicalParameter:
    """A method parameter with its name and canonical type."""
    name: str
    type: CanonicalType

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = CanonicalType.from_string(self.type)


@dataclass
class ProblemTypes:
    """Canonical input/output types for a problem (language-agnostic)."""
    input_params: List[CanonicalParameter] = field(default_factory=list)
    output_type: CanonicalType = CanonicalType.UNKNOWN

    def __post_init__(self):
        if isinstance(self.output_type, str):
            self.output_type = CanonicalType.from_string(self.output_type)

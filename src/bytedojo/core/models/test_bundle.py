"""
TestBundle - the typed test data for a problem.

Each bundle is loaded from data/tests/{id}.json (the schema documented in
data/MIGRATION.md). Universal language runners consume this object to
dispatch the user's Solution against the bundled cases. Hand-editable;
not regenerated at test time.

The `__test__ = False` flag on each Test* class prevents pytest from
mistaking them for test fixtures during collection.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from bytedojo.core.logger import get_logger
from bytedojo.core.models.canonical_type import CanonicalType
from bytedojo.core.paths import get_test_file


class TestComparison(str, Enum):
    """How a test runner compares actual vs expected for a problem."""

    #: Element-by-element equality. The default; omitted from the JSON.
    EXACT = "exact"

    #: Sort both `actual` and `expected` recursively before comparing.
    #: Used when "return any ordering of these results" is the spec.
    UNORDERED_ALL = "unordered_all"

    #: Reserved — sort only the outer collection, leave inner as-is.
    UNORDERED_OUTER = "unordered_outer"

    @classmethod
    def _missing_(cls, value):
        """Default to EXACT for unrecognized values."""
        return cls.EXACT

    @classmethod
    def from_string(cls, value: Optional[str]) -> "TestComparison":
        """Parse a comparison mode from string; EXACT on missing/unknown."""
        if not value:
            return cls.EXACT
        return cls(value.lower())

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"TestComparison.{self.name}"


@dataclass
class TestParam:
    """A method parameter with its canonical type."""
    __test__ = False

    name: str
    type: CanonicalType

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = CanonicalType.from_string(self.type)

    def __str__(self):
        return f"{self.name}: {self.type}"

    def __repr__(self):
        return f"TestParam(name={self.name!r}, type={self.type!r})"


@dataclass
class TestSignature:
    """Method signature: ordered params and a return type."""
    __test__ = False

    params: List[TestParam] = field(default_factory=list)
    returns: CanonicalType = CanonicalType.UNKNOWN

    def __post_init__(self):
        if isinstance(self.returns, str):
            self.returns = CanonicalType.from_string(self.returns)
        # Coerce dict entries into TestParam objects
        self.params = [
            TestParam(**p) if isinstance(p, dict) else p
            for p in self.params
        ]

    def __str__(self):
        params = ", ".join(str(p) for p in self.params)
        return f"({params}) -> {self.returns}"

    def __repr__(self):
        return f"TestSignature(params={self.params!r}, returns={self.returns!r})"


@dataclass
class TestCase:
    """A single test case: structured input and expected output."""
    __test__ = False

    case_id: int
    input: Dict[str, Any]
    expected: Any

    def __str__(self):
        args = ", ".join(f"{k}={v!r}" for k, v in self.input.items())
        return f"case {self.case_id}: ({args}) -> {self.expected!r}"

    def __repr__(self):
        return (f"TestCase(case_id={self.case_id}, "
                f"input={self.input!r}, expected={self.expected!r})")


@dataclass
class TestBundle:
    """The complete typed test data for a single problem."""
    __test__ = False

    schema_version: int
    problem_id: int
    title: str
    method: str
    signature: TestSignature
    cases: List[TestCase] = field(default_factory=list)
    comparison: TestComparison = TestComparison.EXACT

    def __post_init__(self):
        if isinstance(self.signature, dict):
            self.signature = TestSignature(**self.signature)
        if isinstance(self.comparison, str):
            self.comparison = TestComparison.from_string(self.comparison)
        # Coerce dict entries into TestCase objects
        self.cases = [
            TestCase(**c) if isinstance(c, dict) else c
            for c in self.cases
        ]

    @classmethod
    def load(cls, problem_id: int) -> Optional["TestBundle"]:
        """Load a bundle from data/tests/{problem_id}.json, or None if missing."""
        logger = get_logger()
        path = get_test_file(problem_id)
        if not path.exists():
            logger.debug(f"TestBundle.load: no bundle at {path}")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"TestBundle.load: failed to parse {path}: {e}")
            return None
        return cls(**data)

    def get_param(self, name: str) -> Optional[TestParam]:
        """Look up a signature param by name."""
        for p in self.signature.params:
            if p.name == name:
                return p
        return None

    def __str__(self):
        return f"#{self.problem_id} {self.title} {self.signature}"

    def __repr__(self):
        return (f"TestBundle(problem_id={self.problem_id}, "
                f"title={self.title!r}, method={self.method!r}, "
                f"signature={self.signature!r}, "
                f"cases=<{len(self.cases)} cases>, "
                f"comparison={self.comparison!r})")

"""Tests for TestBundle and its nested types (TestComparison, TestParam,
TestSignature, TestCase)."""

import json

import pytest

from bytedojo.core.models.canonical_type import CanonicalType
from bytedojo.core.models.test_bundle import (
    TestBundle,
    TestCase,
    TestComparison,
    TestParam,
    TestSignature,
)


# --------------------------------------------------------------------------- #
# TestComparison                                                              #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, expected", [
    ("exact",           TestComparison.EXACT),
    ("EXACT",           TestComparison.EXACT),
    ("unordered_all",   TestComparison.UNORDERED_ALL),
    ("unordered_outer", TestComparison.UNORDERED_OUTER),
])
def test_comparison_from_string_known(raw, expected):
    assert TestComparison.from_string(raw) is expected


@pytest.mark.parametrize("raw", ["", None, "nonsense"])
def test_comparison_from_string_falls_back_to_exact(raw):
    """EXACT is the implicit default for missing/unknown comparison modes."""
    assert TestComparison.from_string(raw) is TestComparison.EXACT


def test_comparison_str_and_repr():
    assert str(TestComparison.UNORDERED_ALL) == "unordered_all"
    assert repr(TestComparison.EXACT) == "TestComparison.EXACT"


# --------------------------------------------------------------------------- #
# TestParam                                                                   #
# --------------------------------------------------------------------------- #

def test_param_coerces_string_type_to_enum():
    p = TestParam(name="nums", type="INT32_ARRAY")
    assert p.type is CanonicalType.INT32_ARRAY


def test_param_enum_type_passes_through():
    p = TestParam(name="grid", type=CanonicalType.CHAR_MATRIX)
    assert p.type is CanonicalType.CHAR_MATRIX


def test_param_str_format():
    p = TestParam(name="target", type=CanonicalType.INT32)
    assert str(p) == "target: INT32"


# --------------------------------------------------------------------------- #
# TestSignature                                                               #
# --------------------------------------------------------------------------- #

def test_signature_coerces_returns_string_to_enum():
    sig = TestSignature(params=[], returns="INT32")
    assert sig.returns is CanonicalType.INT32


def test_signature_coerces_dict_params_to_test_params():
    sig = TestSignature(
        params=[{"name": "nums", "type": "INT32_ARRAY"}, {"name": "target", "type": "INT32"}],
        returns="INT32_ARRAY",
    )
    assert all(isinstance(p, TestParam) for p in sig.params)
    assert sig.params[0].name == "nums"
    assert sig.params[0].type is CanonicalType.INT32_ARRAY
    assert sig.params[1].type is CanonicalType.INT32


def test_signature_str_format():
    sig = TestSignature(
        params=[TestParam(name="nums", type=CanonicalType.INT32_ARRAY)],
        returns=CanonicalType.INT32,
    )
    assert str(sig) == "(nums: INT32_ARRAY) -> INT32"


# --------------------------------------------------------------------------- #
# TestCase                                                                    #
# --------------------------------------------------------------------------- #

def test_case_construction():
    c = TestCase(case_id=1, input={"nums": [1, 2, 3]}, expected=6)
    assert c.case_id == 1
    assert c.input == {"nums": [1, 2, 3]}
    assert c.expected == 6


def test_case_str_format():
    c = TestCase(case_id=2, input={"x": 5}, expected=25)
    s = str(c)
    assert "case 2" in s
    assert "x=5" in s
    assert "25" in s


# --------------------------------------------------------------------------- #
# TestBundle: construction + coercion                                         #
# --------------------------------------------------------------------------- #

def _bundle_dict(**overrides) -> dict:
    base = {
        "schema_version": 1,
        "problem_id": 1,
        "title": "Two Sum",
        "method": "twoSum",
        "signature": {
            "params": [
                {"name": "nums", "type": "INT32_ARRAY"},
                {"name": "target", "type": "INT32"},
            ],
            "returns": "INT32_ARRAY",
        },
        "cases": [
            {"case_id": 1, "input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]},
            {"case_id": 2, "input": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2]},
        ],
    }
    base.update(overrides)
    return base


def test_bundle_construct_from_dict():
    b = TestBundle(**_bundle_dict())
    assert b.schema_version == 1
    assert b.problem_id == 1
    assert b.title == "Two Sum"
    assert b.method == "twoSum"
    assert isinstance(b.signature, TestSignature)
    assert b.signature.returns is CanonicalType.INT32_ARRAY
    assert all(isinstance(c, TestCase) for c in b.cases)
    assert b.comparison is TestComparison.EXACT     # default when omitted


def test_bundle_comparison_string_is_coerced():
    b = TestBundle(**_bundle_dict(comparison="unordered_all"))
    assert b.comparison is TestComparison.UNORDERED_ALL


def test_bundle_already_typed_signature_passes_through():
    sig = TestSignature(params=[], returns=CanonicalType.VOID)
    b = TestBundle(
        schema_version=1, problem_id=1, title="X", method="x",
        signature=sig, cases=[],
    )
    assert b.signature is sig


# --------------------------------------------------------------------------- #
# TestBundle.get_param                                                        #
# --------------------------------------------------------------------------- #

def test_get_param_returns_match_by_name():
    b = TestBundle(**_bundle_dict())
    p = b.get_param("target")
    assert p is not None
    assert p.type is CanonicalType.INT32


def test_get_param_missing_returns_none():
    b = TestBundle(**_bundle_dict())
    assert b.get_param("nonexistent") is None


# --------------------------------------------------------------------------- #
# TestBundle.load                                                             #
# --------------------------------------------------------------------------- #

def test_load_returns_none_when_file_missing(monkeypatch, tmp_path):
    """Missing bundle file -> None, not an exception."""
    monkeypatch.setattr(
        "bytedojo.core.models.test_bundle.get_test_file",
        lambda pid: tmp_path / f"{pid}.json",
    )
    assert TestBundle.load(99999) is None


def test_load_returns_none_on_malformed_json(monkeypatch, tmp_path):
    """A corrupt JSON file logs a warning and returns None instead of raising."""
    path = tmp_path / "42.json"
    path.write_text("{ not valid json", encoding="utf-8")
    monkeypatch.setattr(
        "bytedojo.core.models.test_bundle.get_test_file",
        lambda pid: path,
    )
    assert TestBundle.load(42) is None


def test_load_roundtrip_from_disk(monkeypatch, tmp_path):
    """A well-formed bundle file is loaded with all fields coerced."""
    path = tmp_path / "1.json"
    path.write_text(json.dumps(_bundle_dict()), encoding="utf-8")
    monkeypatch.setattr(
        "bytedojo.core.models.test_bundle.get_test_file",
        lambda pid: path,
    )
    b = TestBundle.load(1)
    assert b is not None
    assert b.problem_id == 1
    assert b.signature.params[0].name == "nums"
    assert len(b.cases) == 2

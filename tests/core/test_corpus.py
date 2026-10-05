"""Tests for the corpus gateway (core/corpus.py)."""

import pytest

from bytedojo.core import corpus
from bytedojo.core.errors import (
    BundleNotFoundError,
    DataError,
    UnsupportedProblemError,
)
from bytedojo.core.models.problem_difficulty import ProblemDifficulty


def _problem_payload(**overrides) -> dict:
    base = {
        "id": 1,
        "title": "Two Sum",
        "slug": "two-sum",
        "difficulty": "Easy",
        "description": "Find indices.",
        "tags": ["array"],
        "examples": [{"example_num": 1, "example_text": "x", "images": []}],
        "constraints": ["1 <= n"],
        "hints": [],
        "signature": {
            "params": [{"name": "nums", "type": {"base": "ARRAY", "element": "INT32"}}],
            "returns": {"base": "INT32"},
        },
    }
    base.update(overrides)
    return base


def _bundle_payload(**overrides) -> dict:
    base = {
        "schema_version": corpus.SCHEMA_VERSION,
        "problem_id": 1,
        "title": "Two Sum",
        "method": "twoSum",
        "signature": {
            "params": [{"name": "nums", "type": "INT32_ARRAY"}],
            "returns": "INT32_ARRAY",
        },
        "comparison": "exact",
        "cases": [{"case_id": 1, "input": {"nums": [1, 2]}, "expected": [0, 1]}],
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# index / has_problem                                                         #
# --------------------------------------------------------------------------- #


def test_index_keys_are_ints(stub_corpus):
    stub_corpus.add_entry(7, title="Seven", slug="seven", difficulty="Easy")
    catalog = corpus.index()
    assert 7 in catalog
    assert catalog[7]["title"] == "Seven"


def test_index_is_read_only(stub_corpus):
    stub_corpus.add_entry(1)
    with pytest.raises(TypeError):
        corpus.index()[2] = {}


def test_index_missing_file_raises_data_error(stub_corpus):
    (stub_corpus.root / "index.json").unlink()
    corpus._catalog.cache_clear()
    with pytest.raises(DataError, match="missing"):
        corpus.index()


def test_index_malformed_json_raises_data_error(stub_corpus):
    stub_corpus.write_raw("index.json", "{ nope")
    with pytest.raises(DataError, match="malformed"):
        corpus.index()


def test_index_wrong_shape_raises_data_error(stub_corpus):
    stub_corpus.write_raw("index.json", '["a", "list"]')
    with pytest.raises(DataError, match="invalid shape"):
        corpus.index()


def test_has_problem(stub_corpus):
    stub_corpus.add_entry(1)
    assert corpus.has_problem(1) is True
    assert corpus.has_problem(2) is False


# --------------------------------------------------------------------------- #
# problem                                                                     #
# --------------------------------------------------------------------------- #


def test_problem_parses_definition(stub_corpus):
    stub_corpus.write_problem(_problem_payload())
    p = corpus.problem(1)
    assert p.problem_detail.title == "Two Sum"
    assert p.problem_detail.difficulty is ProblemDifficulty.EASY
    assert p.signature is not None
    assert p.signature.params[0].name == "nums"


def test_problem_outside_catalog_raises_unsupported(stub_corpus):
    with pytest.raises(UnsupportedProblemError, match="dojo query"):
        corpus.problem(999)


def test_problem_in_catalog_but_file_missing_raises_data_error(stub_corpus):
    stub_corpus.add_entry(5)
    with pytest.raises(DataError, match="missing"):
        corpus.problem(5)


def test_problem_malformed_file_raises_data_error(stub_corpus):
    stub_corpus.add_entry(5)
    stub_corpus.write_raw("problems/5.json", "{ nope")
    with pytest.raises(DataError, match="malformed"):
        corpus.problem(5)


# --------------------------------------------------------------------------- #
# bundle / bundle_text                                                        #
# --------------------------------------------------------------------------- #


def test_bundle_parses_and_types(stub_corpus):
    stub_corpus.write_bundle(_bundle_payload())
    b = corpus.bundle(1)
    assert b.method == "twoSum"
    assert len(b.cases) == 1
    assert b.cases[0].expected == [0, 1]


def test_bundle_missing_raises_bundle_not_found(stub_corpus):
    with pytest.raises(BundleNotFoundError, match="#42"):
        corpus.bundle(42)


def test_bundle_malformed_raises_data_error(stub_corpus):
    stub_corpus.write_raw("tests/1.json", "{ nope")
    with pytest.raises(DataError, match="malformed"):
        corpus.bundle(1)


def test_bundle_wrong_schema_version_raises_data_error(stub_corpus):
    stub_corpus.write_bundle(_bundle_payload(schema_version=99))
    with pytest.raises(DataError, match="schema_version"):
        corpus.bundle(1)


def test_bundle_invalid_shape_raises_data_error(stub_corpus):
    stub_corpus.write_raw("tests/1.json", '{"schema_version": 1, "surprise": true}')
    with pytest.raises(DataError, match="invalid shape"):
        corpus.bundle(1)


def test_bundle_text_returns_raw_json(stub_corpus):
    stub_corpus.write_bundle(_bundle_payload())
    text = corpus.bundle_text(1)
    assert '"twoSum"' in text


def test_bundle_text_missing_raises_bundle_not_found(stub_corpus):
    with pytest.raises(BundleNotFoundError):
        corpus.bundle_text(7)


# --------------------------------------------------------------------------- #
# Real bundled corpus (no stub) — the package data is actually readable       #
# --------------------------------------------------------------------------- #


def test_real_corpus_is_wired_in():
    assert corpus.has_problem(1)
    p = corpus.problem(1)
    assert p.problem_detail.title == "Two Sum"
    b = corpus.bundle(1)
    assert b.method == "twoSum"
    assert b.cases

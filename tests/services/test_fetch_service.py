"""Tests for FetchService (corpus-restricted fetch + stub synthesis)."""

import pytest

from bytedojo.core.errors import UnsupportedProblemError
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.services.fetch_service import (
    FetchBatchResult,
    FetchResult,
    FetchService,
)

from tests.services.conftest import make_problem


def _seed_supported(
    stub_corpus,
    pid=1,
    slug="two-sum",
    title="Two Sum",
    *,
    signature=None,
    method="twoSum",
):
    """Register a fully supported problem (definition + bundle) in the stub."""
    stub_corpus.write_problem(
        {
            "id": pid,
            "title": title,
            "slug": slug,
            "difficulty": "Easy",
            "description": "Find indices.",
            "tags": ["array"],
            "examples": [{"example_num": 1, "example_text": "nums=[2,7], t=9"}],
            "constraints": ["2 <= nums.length"],
            "hints": [],
        }
    )
    stub_corpus.write_bundle(
        {
            "schema_version": 1,
            "problem_id": pid,
            "title": title,
            "method": method,
            "signature": signature
            or {
                "params": [
                    {"name": "nums", "type": {"base": "ARRAY", "element": "INT32"}},
                    {"name": "target", "type": {"base": "INT32"}},
                ],
                "returns": {"base": "ARRAY", "element": "INT32"},
            },
            "comparison": "exact",
            "cases": [
                {
                    "case_id": 1,
                    "input": {"nums": [2, 7], "target": 9},
                    "expected": [0, 1],
                }
            ],
        }
    )


# --------------------------------------------------------------------------- #
# FetchResult / FetchBatchResult                                              #
# --------------------------------------------------------------------------- #


def test_fetch_result_failed_when_neither_success_nor_skipped():
    r = FetchResult(problem_id=1, error="x")
    assert r.failed is True


def test_fetch_result_success_not_failed():
    r = FetchResult(problem_id=1, success=True)
    assert r.failed is False


def test_fetch_result_skipped_not_failed():
    r = FetchResult(problem_id=1, skipped=True)
    assert r.failed is False


def test_fetch_result_title_falls_back_to_empty_when_no_problem():
    assert FetchResult(problem_id=1).title == ""


def test_fetch_result_title_from_problem_detail():
    p = make_problem(title="Two Sum")
    assert FetchResult(problem_id=1, problem=p).title == "Two Sum"


def test_batch_result_counts():
    results = [
        FetchResult(problem_id=1, success=True),
        FetchResult(problem_id=2, skipped=True),
        FetchResult(problem_id=3, error="x"),
        FetchResult(problem_id=4, success=True),
    ]
    batch = FetchBatchResult(results=results)
    assert batch.placed_count == 2
    assert batch.skipped_count == 1
    assert batch.failed_count == 1


# --------------------------------------------------------------------------- #
# Catalog restriction                                                         #
# --------------------------------------------------------------------------- #


def test_batch_rejects_unsupported_ids_before_placing(repo, stub_corpus):
    """One unsupported id aborts the whole batch up front."""
    _seed_supported(stub_corpus, pid=1)
    with pytest.raises(UnsupportedProblemError, match="#999"):
        FetchService().fetch_and_place_batch(
            repo,
            [1, 999],
            CodeLanguage.PYTHON,
        )
    # Nothing was registered for the supported id either.
    with repo.session() as s:
        assert s.problems.get("leetcode", 1) is None


def test_batch_error_lists_every_unsupported_id(repo, stub_corpus):
    with pytest.raises(UnsupportedProblemError) as exc:
        FetchService().fetch_and_place_batch(
            repo,
            [998, 999],
            CodeLanguage.PYTHON,
        )
    assert "#998" in exc.value.message
    assert "#999" in exc.value.message
    assert "dojo query" in exc.value.message


# --------------------------------------------------------------------------- #
# fetch_and_place — default mode (register + place)                           #
# --------------------------------------------------------------------------- #


def test_default_mode_places_synthesised_stub(repo, stub_corpus):
    """The solution stub comes from the bundle signature, not any snippet."""
    _seed_supported(stub_corpus)
    result = FetchService().fetch_and_place(repo, 1, CodeLanguage.PYTHON)

    assert result.success
    assert result.version == 1
    assert result.target_path.name == "solution.py"
    assert "0001-two-sum" in str(result.target_path)

    content = result.target_path.read_text(encoding="utf-8")
    assert "class Solution:" in content
    assert "def twoSum(self, nums: List[int], target: int) -> List[int]:" in content
    assert "Find indices." in content  # prose header
    assert "Example #1" in content


def test_default_mode_refuses_already_registered(repo, stub_corpus):
    """Without --new-attempt, re-fetching a registered problem is refused."""
    _seed_supported(stub_corpus)
    svc = FetchService()
    first = svc.fetch_and_place(repo, 1, CodeLanguage.PYTHON)
    second = svc.fetch_and_place(repo, 1, CodeLanguage.PYTHON)

    assert first.success
    assert second.skipped
    assert second.skip_reason == "already registered"


def test_new_attempt_creates_next_version(repo, stub_corpus):
    _seed_supported(stub_corpus)
    svc = FetchService()
    svc.fetch_and_place(repo, 1, CodeLanguage.PYTHON)
    second = svc.fetch_and_place(repo, 1, CodeLanguage.PYTHON, new_attempt=True)

    assert second.success
    assert second.version == 2
    assert "v002" in str(second.target_path)


def test_node_signature_places_sibling_module(repo, stub_corpus):
    """A tree-typed signature places tree_node.py next to the solution."""
    _seed_supported(
        stub_corpus,
        pid=104,
        slug="maximum-depth-of-binary-tree",
        title="Maximum Depth of Binary Tree",
        method="maxDepth",
        signature={
            "params": [{"name": "root", "type": {"base": "BINARY_TREE"}}],
            "returns": {"base": "INT32"},
        },
    )
    result = FetchService().fetch_and_place(repo, 104, CodeLanguage.PYTHON)

    assert result.success
    sibling = result.target_path.parent / "tree_node.py"
    assert sibling.exists()
    assert "class TreeNode" in sibling.read_text(encoding="utf-8")

    content = result.target_path.read_text(encoding="utf-8")
    assert "from tree_node import TreeNode" in content
    assert "def maxDepth(self, root: Optional[TreeNode]) -> int:" in content


# --------------------------------------------------------------------------- #
# fetch_and_place — --version mode (rewrite existing version)                 #
# --------------------------------------------------------------------------- #


def test_version_mode_rewrites_existing(repo, stub_corpus):
    """--version N rewrites v{N} in place."""
    _seed_supported(stub_corpus)
    svc = FetchService()
    placed = svc.fetch_and_place(repo, 1, CodeLanguage.PYTHON)
    placed.target_path.write_text("ruined", encoding="utf-8")

    refetched = svc.fetch_and_place(repo, 1, CodeLanguage.PYTHON, version=1)
    assert refetched.success
    assert refetched.target_path == placed.target_path
    assert "class Solution:" in placed.target_path.read_text(encoding="utf-8")


def test_version_mode_unregistered_version_is_skipped(repo, stub_corpus):
    """--version N when attempt N doesn't exist -> skip listing available."""
    _seed_supported(stub_corpus)
    FetchService().fetch_and_place(repo, 1, CodeLanguage.PYTHON)
    result = FetchService().fetch_and_place(
        repo,
        1,
        CodeLanguage.PYTHON,
        version=99,
    )
    assert result.skipped
    assert "v99 not registered" in result.skip_reason
    assert "v1" in result.skip_reason


# --------------------------------------------------------------------------- #
# fetch_and_place — --path mode (scratch, untracked)                          #
# --------------------------------------------------------------------------- #


def test_custom_path_writes_to_scratch_dir(repo, stub_corpus, tmp_path):
    """--path writes into a custom dir, doesn't register in the DB."""
    scratch = tmp_path / "scratch"
    _seed_supported(stub_corpus)
    result = FetchService().fetch_and_place(
        repo,
        1,
        CodeLanguage.PYTHON,
        custom_path=scratch,
    )

    assert result.success
    assert scratch in result.target_path.parents
    assert result.version is None  # untracked

    # No DB row was created.
    with repo.session() as s:
        assert s.problems.get("leetcode", 1) is None


# --------------------------------------------------------------------------- #
# fetch_and_place_batch                                                       #
# --------------------------------------------------------------------------- #


def test_batch_aggregates(repo, stub_corpus):
    _seed_supported(stub_corpus, pid=1, slug="a", title="A")
    _seed_supported(stub_corpus, pid=2, slug="b", title="B")

    batch = FetchService().fetch_and_place_batch(
        repo,
        [1, 2],
        CodeLanguage.PYTHON,
    )
    assert len(batch.results) == 2
    assert batch.placed_count == 2
    assert batch.failed_count == 0


def test_batch_same_id_twice_second_is_refused(repo, stub_corpus):
    _seed_supported(stub_corpus)
    batch = FetchService().fetch_and_place_batch(
        repo,
        [1, 1],
        CodeLanguage.PYTHON,
    )
    assert batch.placed_count == 1
    assert batch.skipped_count == 1

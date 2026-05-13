"""Tests for the ProblemDetail dataclass."""

from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_tag import ProblemTag


# --------------------------------------------------------------------------- #
# __post_init__ coercion                                                      #
# --------------------------------------------------------------------------- #

def test_string_difficulty_is_coerced_to_enum():
    pd = ProblemDetail(id=1, title="Two Sum", slug="two-sum",
                       difficulty="Easy", description="")
    assert pd.difficulty is ProblemDifficulty.EASY


def test_enum_difficulty_passes_through():
    pd = ProblemDetail(id=1, title="Two Sum", slug="two-sum",
                       difficulty=ProblemDifficulty.MEDIUM, description="")
    assert pd.difficulty is ProblemDifficulty.MEDIUM


def test_string_tags_are_coerced_to_enums():
    pd = ProblemDetail(id=1, title="Two Sum", slug="two-sum",
                       difficulty=ProblemDifficulty.EASY, description="",
                       tags=["array", "hash-table"])
    assert pd.tags == [ProblemTag.ARRAY, ProblemTag.HASH_TABLE]


def test_enum_tags_pass_through():
    pd = ProblemDetail(id=1, title="Two Sum", slug="two-sum",
                       difficulty=ProblemDifficulty.EASY, description="",
                       tags=[ProblemTag.ARRAY])
    assert pd.tags == [ProblemTag.ARRAY]


def test_mixed_tags_are_normalised():
    pd = ProblemDetail(id=1, title="Two Sum", slug="two-sum",
                       difficulty=ProblemDifficulty.EASY, description="",
                       tags=["array", ProblemTag.HASH_TABLE])
    assert pd.tags == [ProblemTag.ARRAY, ProblemTag.HASH_TABLE]


def test_empty_tags_defaults_to_empty_list():
    pd = ProblemDetail(id=1, title="Two Sum", slug="two-sum",
                       difficulty=ProblemDifficulty.EASY, description="")
    assert pd.tags == []


# --------------------------------------------------------------------------- #
# __str__ / __repr__                                                          #
# --------------------------------------------------------------------------- #

def test_str_returns_title():
    pd = ProblemDetail(id=1, title="Two Sum", slug="two-sum",
                       difficulty=ProblemDifficulty.EASY, description="")
    assert str(pd) == "Two Sum"


def test_repr_includes_id_title_slug_difficulty_tags():
    pd = ProblemDetail(id=1, title="Two Sum", slug="two-sum",
                       difficulty=ProblemDifficulty.EASY, description="",
                       tags=[ProblemTag.ARRAY])
    r = repr(pd)
    assert "id=1" in r
    assert "Two Sum" in r
    assert "two-sum" in r
    assert "EASY" in r
    assert "ARRAY" in r

"""Tests for the AttemptStats dataclass."""

from bytedojo.core.models.attempt_stats import AttemptStats
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_status import ProblemStatus


def test_construct_with_all_fields():
    stats = AttemptStats(
        problem_id=1,
        language=CodeLanguage.PYTHON,
        total_attempts=3,
        latest_version=3,
        latest_status=ProblemStatus.PASSED,
        pass_count=2,
        fail_count=1,
        skip_count=0,
        total_runs=8,
    )
    assert stats.problem_id == 1
    assert stats.language is CodeLanguage.PYTHON
    assert stats.total_attempts == 3
    assert stats.latest_version == 3
    assert stats.latest_status is ProblemStatus.PASSED
    assert stats.pass_count == 2
    assert stats.fail_count == 1
    assert stats.skip_count == 0
    assert stats.total_runs == 8


def test_equality_by_fields():
    a = AttemptStats(
        problem_id=1, language=CodeLanguage.PYTHON, total_attempts=1,
        latest_version=1, latest_status=ProblemStatus.PASSED,
        pass_count=1, fail_count=0, skip_count=0, total_runs=1,
    )
    b = AttemptStats(
        problem_id=1, language=CodeLanguage.PYTHON, total_attempts=1,
        latest_version=1, latest_status=ProblemStatus.PASSED,
        pass_count=1, fail_count=0, skip_count=0, total_runs=1,
    )
    assert a == b

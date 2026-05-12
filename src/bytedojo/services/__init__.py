"""
Services - business logic orchestration layer.

Services coordinate between core modules (problem_service, repository, database)
and provide a unified API for commands (CLI) and views (TUI).
"""

from bytedojo.services.fetch_service import FetchService, FetchResult, FetchBatchResult
from bytedojo.services.pick_service import PickService, PickResult, PickScope
from bytedojo.services.problem_service import LookupResult
from bytedojo.services.test_service import (
    TestService,
    TestServiceResult,
    TestRunResult,
    TestCaseResult,
)
from bytedojo.services.run_service import RunService, RunServiceResult
from bytedojo.services.grading_service import GradingService, GradeResult
from bytedojo.services.review_service import (
    ReviewService,
    ReviewQuality,
    ReviewCompletionResult,
    ReviewActionResult,
)
from bytedojo.services.system_service import SystemService, SystemReport

__all__ = [
    "FetchService", "FetchResult", "FetchBatchResult",
    "PickService", "PickResult", "PickScope",
    "LookupResult",
    "TestService", "TestServiceResult", "TestRunResult", "TestCaseResult",
    "RunService", "RunServiceResult",
    "GradingService", "GradeResult",
    "ReviewService", "ReviewQuality", "ReviewCompletionResult", "ReviewActionResult",
    "SystemService", "SystemReport",
]

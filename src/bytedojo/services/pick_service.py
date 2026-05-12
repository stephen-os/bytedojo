"""
Pick service — selects a random problem matching filters.

Combines a local-index query with the repository's registration state
to filter by scope (unsolved / solved / all), then chooses one at random.
Returns a rich result so commands and the TUI can render their own way.
"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from bytedojo.core import problem_service
from bytedojo.core.logger import get_logger
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_tag import ProblemTag
from bytedojo.core.repository import Repository


class PickScope(str, Enum):
    """Which pool to pick from."""
    UNSOLVED = "unsolved"
    SOLVED = "solved"
    ALL = "all"

    @property
    def display_label(self) -> str:
        """Human-readable label (SOLVED renders as 'registered')."""
        return {
            PickScope.UNSOLVED: "unsolved",
            PickScope.SOLVED: "registered",
            PickScope.ALL: "all",
        }[self]


@dataclass
class PickResult:
    """Outcome of a pick operation, with pool context for display."""
    picked: Optional[ProblemDetail] = None
    candidates: List[ProblemDetail] = field(default_factory=list)
    total_count: int = 0
    registered_count: int = 0
    scope: PickScope = PickScope.UNSOLVED

    @property
    def pool_size(self) -> int:
        return len(self.candidates)

    @property
    def has_pick(self) -> bool:
        return self.picked is not None


class PickService:
    """
    Selects a random problem matching difficulty/tag filters.

    Wraps problem_service (read) and Repository (registration state).
    Inputs are assumed validated — callers should parse strings to enums
    and drop UNKNOWN tags before calling.
    """

    def __init__(self):
        self.logger = get_logger()

    def pick(
        self,
        repo: Repository,
        *,
        difficulty: ProblemDifficulty = ProblemDifficulty.NONE,
        tags: Optional[List[ProblemTag]] = None,
        scope: PickScope = PickScope.UNSOLVED,
    ) -> PickResult:
        """
        Pick a random problem matching the given filters and scope.

        Args:
            repo: Repository (used to determine which problems are registered).
            difficulty: Filter by difficulty; NONE means no filter.
            tags: Filter by tags (OR semantics). None means no filter.
            scope: Which pool to pick from (default: UNSOLVED).

        Returns:
            PickResult with the picked problem (if any) and pool context.
        """
        self.logger.debug(
            f"pick_service: difficulty={difficulty} tags={tags} scope={scope.value}"
        )

        all_problems = problem_service.query_problems(
            difficulty=difficulty,
            tags=tags,
        )
        total_count = len(all_problems)

        registered_ids = {p.problem_id for p in repo.get_registered_problems()}
        registered_count = sum(1 for p in all_problems if p.id in registered_ids)

        candidates = self._filter_by_scope(all_problems, registered_ids, scope)

        picked = random.choice(candidates) if candidates else None
        if picked is not None:
            self.logger.info(
                f"pick_service: selected #{picked.id} {picked.slug} "
                f"(scope={scope.value}, pool={len(candidates)})"
            )
        else:
            self.logger.info(
                f"pick_service: no candidates (scope={scope.value}, "
                f"total={total_count}, registered={registered_count})"
            )

        return PickResult(
            picked=picked,
            candidates=candidates,
            total_count=total_count,
            registered_count=registered_count,
            scope=scope,
        )

    @staticmethod
    def _filter_by_scope(
        problems: List[ProblemDetail],
        registered_ids: set,
        scope: PickScope,
    ) -> List[ProblemDetail]:
        if scope == PickScope.ALL:
            return problems
        if scope == PickScope.SOLVED:
            return [p for p in problems if p.id in registered_ids]
        return [p for p in problems if p.id not in registered_ids]

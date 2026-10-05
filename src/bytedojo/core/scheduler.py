"""
SM-2 spaced-repetition scheduler (§8).

Pure functions over an immutable ScheduleState — no I/O, no database.
ReviewService translates between persisted review rows and these
states; everything about *when* a problem resurfaces is decided here.

Quality values:
    FAIL (1)  a lapse — test failure/error or `grade --fail`
    HARD (2)  recalled with real difficulty (`review complete --hard`)
    GOOD (4)  standard recall; the default for a plain `test` pass
    EASY (5)  effortless recall (`review complete --easy`)

Anything below 3 is a lapse: repetitions reset and the problem comes
back ~tomorrow. The ease factor is updated on every review, lapses
included, and never drops below 1.3.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from enum import IntEnum

INITIAL_EASE = 2.5
MIN_EASE = 1.3

#: Quality threshold below which a review counts as a lapse.
_LAPSE_THRESHOLD = 3


class Quality(IntEnum):
    """SM-2 quality grades used by ByteDojo."""

    FAIL = 1
    HARD = 2
    GOOD = 4
    EASY = 5


@dataclass(frozen=True)
class ScheduleState:
    """Per-problem SM-2 state: repetitions, ease, interval and due date."""

    reps: int
    ease: float
    interval_days: int
    due: date


def review(
    state: ScheduleState,
    quality: Quality,
    base_days: int,
    today: date | None = None,
) -> ScheduleState:
    """Apply one review of `quality` to `state` and return the next state.

    `base_days` is the configured review frequency — the interval used
    for the first successful repetition.
    """
    today = today or date.today()

    # 1) Ease update (SM-2), applied on every review including lapses.
    gap = 5 - quality
    ease = state.ease + (0.1 - gap * (0.08 + gap * 0.02))
    ease = max(MIN_EASE, ease)

    # 2) Interval + repetitions.
    if quality < _LAPSE_THRESHOLD:
        reps = 0
        interval = 1
    else:
        reps = state.reps + 1
        interval = base_days if reps == 1 else round(state.interval_days * ease)

    return ScheduleState(
        reps=reps,
        ease=ease,
        interval_days=interval,
        due=today + timedelta(days=interval),
    )


def initial(base_days: int, today: date | None = None) -> ScheduleState:
    """The first graduation: a fresh problem passes and enters the track."""
    today = today or date.today()
    fresh = ScheduleState(reps=0, ease=INITIAL_EASE, interval_days=0, due=today)
    return review(fresh, Quality.GOOD, base_days, today=today)

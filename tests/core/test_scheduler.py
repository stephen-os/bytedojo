"""Tests for the pure SM-2 scheduler (core/scheduler.py, §8)."""

from datetime import date, timedelta

import pytest

from bytedojo.core.scheduler import (
    INITIAL_EASE,
    MIN_EASE,
    Quality,
    ScheduleState,
    initial,
    review,
)

TODAY = date(2026, 10, 4)


def _state(reps=1, ease=2.5, interval=7, due=TODAY) -> ScheduleState:
    return ScheduleState(reps=reps, ease=ease, interval_days=interval, due=due)


# --------------------------------------------------------------------------- #
# initial — first graduation                                                  #
# --------------------------------------------------------------------------- #


def test_initial_schedules_at_base_interval():
    state = initial(base_days=7, today=TODAY)
    assert state.reps == 1
    assert state.interval_days == 7
    assert state.due == TODAY + timedelta(days=7)


def test_initial_keeps_default_ease():
    """A GOOD review leaves ease exactly where it started (SM-2: q=4 → +0)."""
    state = initial(base_days=7, today=TODAY)
    assert state.ease == pytest.approx(INITIAL_EASE)


def test_initial_respects_custom_base():
    assert initial(base_days=3, today=TODAY).interval_days == 3


# --------------------------------------------------------------------------- #
# review — successful repetitions                                             #
# --------------------------------------------------------------------------- #


def test_good_review_multiplies_interval_by_ease():
    state = review(
        _state(reps=1, ease=2.5, interval=7), Quality.GOOD, base_days=7, today=TODAY
    )
    assert state.reps == 2
    assert state.interval_days == round(7 * 2.5)  # 18
    assert state.due == TODAY + timedelta(days=18)


def test_good_review_leaves_ease_unchanged():
    state = review(_state(ease=2.5), Quality.GOOD, base_days=7, today=TODAY)
    assert state.ease == pytest.approx(2.5)


def test_easy_review_grows_ease_and_interval():
    state = review(
        _state(reps=1, ease=2.5, interval=7), Quality.EASY, base_days=7, today=TODAY
    )
    assert state.ease == pytest.approx(2.6)
    # Interval uses the updated ease: round(7 * 2.6) = 18
    assert state.interval_days == 18


def test_first_success_uses_base_days_not_interval():
    """reps 0 -> 1 always lands on base_days regardless of stale interval."""
    state = review(_state(reps=0, interval=99), Quality.GOOD, base_days=5, today=TODAY)
    assert state.interval_days == 5


def test_interval_compounds_over_consecutive_goods():
    state = initial(base_days=7, today=TODAY)
    second = review(state, Quality.GOOD, base_days=7, today=TODAY)
    third = review(second, Quality.GOOD, base_days=7, today=TODAY)
    assert second.interval_days == 18  # 7 × 2.5
    assert third.interval_days == 45  # 18 × 2.5


# --------------------------------------------------------------------------- #
# review — lapses (quality < 3)                                               #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("quality", [Quality.FAIL, Quality.HARD])
def test_lapse_resets_reps_and_schedules_tomorrow(quality):
    state = review(_state(reps=5, interval=30), quality, base_days=7, today=TODAY)
    assert state.reps == 0
    assert state.interval_days == 1
    assert state.due == TODAY + timedelta(days=1)


def test_fail_drops_ease_harder_than_hard():
    failed = review(_state(ease=2.5), Quality.FAIL, base_days=7, today=TODAY)
    hard = review(_state(ease=2.5), Quality.HARD, base_days=7, today=TODAY)
    # q=1: 2.5 - 0.54 = 1.96;  q=2: 2.5 - 0.32 = 2.18
    assert failed.ease == pytest.approx(1.96)
    assert hard.ease == pytest.approx(2.18)
    assert failed.ease < hard.ease


def test_ease_never_drops_below_minimum():
    state = _state(ease=MIN_EASE)
    for _ in range(5):
        state = review(state, Quality.FAIL, base_days=7, today=TODAY)
    assert state.ease == pytest.approx(MIN_EASE)


def test_recovery_after_lapse_starts_at_base_days():
    """A lapse resets reps, so the next pass graduates at base again."""
    lapsed = review(_state(reps=4, interval=40), Quality.FAIL, base_days=7, today=TODAY)
    recovered = review(lapsed, Quality.GOOD, base_days=7, today=TODAY)
    assert recovered.reps == 1
    assert recovered.interval_days == 7

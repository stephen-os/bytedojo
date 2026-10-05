"""Thin renderer tests (§4.3) — formatting of the shared view fragments."""

from datetime import date

import click

from bytedojo.commands.ui.renderers import (
    render_fetch_results,
    render_schedule_effect,
)
from bytedojo.services import ScheduleEffect
from bytedojo.services.fetch_service import FetchBatchResult, FetchResult


def _out(capsys) -> str:
    return click.unstyle(capsys.readouterr().out)


def test_schedule_effect_none_prints_nothing(capsys):
    render_schedule_effect(None)
    render_schedule_effect(ScheduleEffect(action="none"))
    assert capsys.readouterr().out == ""


def test_schedule_effect_created(capsys):
    render_schedule_effect(
        ScheduleEffect(
            action="created", interval_days=7, next_review_date=date(2026, 10, 11)
        )
    )
    out = _out(capsys)
    assert "Scheduled for review in 7 days" in out
    assert "2026-10-11" in out


def test_schedule_effect_advanced(capsys):
    render_schedule_effect(
        ScheduleEffect(
            action="advanced", interval_days=18, next_review_date=date(2026, 10, 22)
        )
    )
    assert "Review advanced — next in 18 days" in _out(capsys)


def test_schedule_effect_lapsed(capsys):
    render_schedule_effect(
        ScheduleEffect(action="lapsed", next_review_date=date(2026, 10, 6))
    )
    assert "Review lapsed — due again 2026-10-06" in _out(capsys)


def test_schedule_effect_removed(capsys):
    render_schedule_effect(ScheduleEffect(action="removed"))
    assert "Removed from the review queue" in _out(capsys)


def test_fetch_results_summary_counts(capsys):
    batch = FetchBatchResult(
        results=[
            FetchResult(problem_id=1, success=True, version=1),
            FetchResult(problem_id=2, skipped=True, skip_reason="already registered"),
            FetchResult(problem_id=3, error="boom"),
        ]
    )
    render_fetch_results(batch)
    out = _out(capsys)
    assert "1 placed" in out
    assert "1 skipped" in out
    assert "1 failed" in out
    assert "--new-attempt" in out  # the already-registered hint

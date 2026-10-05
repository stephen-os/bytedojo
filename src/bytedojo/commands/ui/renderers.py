"""
Renderers — one function per CLI view (§4.3).

Each renderer takes a view-model (usually a service result struct) and
writes terminal output via click + the palette. No business logic, no
database access, no decisions beyond formatting.
"""

import click

from bytedojo.commands.ui.palette import (
    accent,
    blank,
    bold,
    difficulty_badge,
    difficulty_short,
    dim,
    error,
    header,
    hint,
    kv,
    problem_id,
    problem_line,
    status_short,
    success,
    warn,
)
from bytedojo.core.models.problem_status import ProblemStatus


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def render_schedule_effect(effect) -> None:
    """One line describing what an outcome did to the review schedule."""
    if effect is None or effect.action == "none":
        return
    if effect.action == "created":
        click.echo(
            accent(
                f"  Scheduled for review in {effect.interval_days} days"
                f" ({effect.next_review_date})"
            )
        )
    elif effect.action == "advanced":
        click.echo(
            accent(
                f"  Review advanced — next in {effect.interval_days} days"
                f" ({effect.next_review_date})"
            )
        )
    elif effect.action == "lapsed":
        click.echo(warn(f"  Review lapsed — due again {effect.next_review_date}"))
    elif effect.action == "removed":
        click.echo(dim("  Removed from the review queue"))


# --------------------------------------------------------------------------- #
# run                                                                         #
# --------------------------------------------------------------------------- #


def render_run_header(result) -> None:
    """Problem header for `dojo run` (version-aware path from the service)."""
    problem = result.problem
    file_path = str(result.file_path) if result.file_path else (problem.file_path or "")
    version_label = f"v{result.version}" if result.version is not None else "?"

    click.echo()
    click.echo(dim("  " + "─" * 60))
    line = problem_line(
        problem.problem_id,
        problem.title,
        problem.difficulty.value,
        problem.language.value,
    )
    click.echo(f"  {line}  {dim(version_label)}")
    click.echo(f"  {dim(file_path)}")
    click.echo(dim("  " + "─" * 60))
    click.echo()


def render_execution(execution) -> None:
    """stdout/stderr + final status of a `dojo run` execution."""
    if execution.compile_error:
        click.echo(error("Compilation failed:"))
        click.echo(execution.compile_error)
        return

    if execution.stdout:
        click.echo(execution.stdout, nl=False)
        if not execution.stdout.endswith("\n"):
            click.echo("")

    if execution.stderr and not execution.timed_out:
        click.echo(warn(execution.stderr), nl=False)
        if not execution.stderr.endswith("\n"):
            click.echo("")

    if execution.timed_out:
        click.echo(error(execution.stderr))

    click.echo()
    if execution.exit_code == 0:
        click.echo(f"  {success('✓ Execution completed successfully')}")
    else:
        click.echo(
            f"  {error(f'✗ Execution failed (exit code: {execution.exit_code})')}"
        )


# --------------------------------------------------------------------------- #
# test                                                                        #
# --------------------------------------------------------------------------- #


def render_test_header(result) -> None:
    """Problem header for `dojo test` (version-aware path from the service)."""
    problem = result.problem
    file_path = str(result.file_path) if result.file_path else (problem.file_path or "")
    version_label = f"v{result.version}" if result.version is not None else "?"

    click.echo()
    click.echo(dim("  " + "─" * 70))
    line = problem_line(
        problem.problem_id,
        problem.title,
        problem.difficulty.value,
        problem.language.value,
    )
    click.echo(f"  {line}  {dim(version_label)}")
    click.echo(f"  {dim(file_path)}")
    click.echo()


def render_test_results(result, verbose: bool = False) -> None:
    """Case results of a `dojo test` run (TestRunResult)."""
    click.echo(dim("  " + "─" * 70))
    click.echo(f"  {accent('Results')}")
    click.echo(dim("  " + "─" * 70))
    click.echo()

    if result.compile_error:
        click.echo(f"  {error('COMPILE ERROR')}")
        click.echo()
        click.echo(result.compile_error)
        click.echo()
        return

    if result.runtime_error and not result.case_results:
        click.echo(f"  {error('ERROR')}")
        click.echo(f"  {result.runtime_error}")
        click.echo()
        return

    if result.all_passed:
        click.echo(
            success(
                f"  ALL TESTS PASSED ({result.passed_count}/{result.runnable_count})"
            )
        )
    else:
        passed_str = success(str(result.passed_count))
        failed_str = error(str(result.failed_count))
        error_str = warn(str(result.error_count))
        skipped_part = ""
        if result.skipped_count:
            skipped_str = dim(str(result.skipped_count))
            skipped_part = f"  Skipped: {skipped_str}"
        click.echo(
            f"  Passed: {passed_str}  Failed: {failed_str}  Error: {error_str}"
            f"{skipped_part}  {dim(f'(Total: {result.total_cases})')}"
        )
    if result.skipped_count:
        click.echo(
            dim(
                f"  ({result.skipped_count} case(s) skipped — values outside int32 range)"
            )
        )

    click.echo()

    failed_cases = [c for c in result.case_results if not c.passed]

    if failed_cases:
        click.echo(f"  {error('Failed Test Cases:')}")
        click.echo(dim("  " + "─" * 70))

        display_cases = failed_cases if verbose else failed_cases[:5]

        for case in display_cases:
            click.echo()
            click.echo(f"  {accent('Case #' + str(case.case_number))}")
            click.echo(f"    {dim('Input')}     {_truncate(case.input_str, 60)}")
            click.echo(
                f"    {dim('Expected')}  {success(_truncate(case.expected, 50))}"
            )
            if case.error:
                click.echo(f"    {dim('Error')}     {warn(_truncate(case.error, 50))}")
            elif case.timed_out:
                click.echo(f"    {dim('Actual')}    {error('TIMEOUT')}")
            else:
                click.echo(
                    f"    {dim('Actual')}    {error(_truncate(case.actual, 50))}"
                )

        if len(failed_cases) > 5 and not verbose:
            click.echo()
            click.echo(f"  {dim(f'... and {len(failed_cases) - 5} more failures')}")
            click.echo(f"  {dim('Use --verbose to see all failures')}")

    click.echo()

    if verbose:
        passed_cases = [c for c in result.case_results if c.passed]
        if passed_cases:
            click.echo(f"  {success('Passed Test Cases:')}")
            click.echo(dim("  " + "─" * 70))
            for case in passed_cases:
                click.echo(
                    f"  Case #{case.case_number}: {_truncate(case.input_str, 50)}"
                )
            click.echo()


def render_test_outcome(result) -> None:
    """Recorded status + schedule effect after a `dojo test` run."""
    status = result.run_result.status
    if status == "passed":
        click.echo(success("  ✓ Solution recorded as PASSED"))
    elif status == "error":
        click.echo(warn("  ! Solution recorded as ERROR"))
    elif status == "failed":
        click.echo(error("  ✗ Solution recorded as FAILED"))
    else:  # ungraded — ran a subset, all passed, but some were skipped
        click.echo(warn("  Solution recorded as UNGRADED"))
    render_schedule_effect(result.schedule_effect)
    click.echo()


# --------------------------------------------------------------------------- #
# grade                                                                       #
# --------------------------------------------------------------------------- #


def render_problem_status(problem, show_test_hint: bool = True) -> None:
    """Status card for one registered problem (`dojo grade <id>`)."""
    click.echo()
    click.echo(dim("  " + "─" * 70))
    click.echo(f"  {accent('Problem Status')}")
    click.echo(dim("  " + "─" * 70))
    click.echo()
    click.echo(f"  {accent('#' + str(problem.problem_id))}  {bold(problem.title)}")
    click.echo(f"  {dim('Source')}      {problem.source.capitalize()}")
    click.echo(f"  {dim('Language')}    {problem.language.value.upper()}")
    click.echo(f"  {dim('Difficulty')}  {problem.difficulty.value or 'Unknown'}")

    if problem.file_path:
        click.echo(f"  {dim('File')}        {dim(problem.file_path)}")

    click.echo()
    click.echo(dim("  " + "─" * 70))
    click.echo(f"  {accent('Grade')}")
    click.echo(dim("  " + "─" * 70))
    click.echo()

    status = problem.status or ProblemStatus.UNGRADED

    if status == ProblemStatus.PASSED:
        click.echo(f"  Status: {success('PASSED')}")
    elif status == ProblemStatus.FAILED:
        click.echo(f"  Status: {error('FAILED')}")
    elif status == ProblemStatus.ERROR:
        click.echo(f"  Status: {error('ERROR')}")
    elif status == ProblemStatus.SKIPPED:
        click.echo(f"  Status: {warn('SKIPPED')}")
    elif status == ProblemStatus.UNGRADED:
        click.echo(f"  Status: {dim('UNGRADED')}")
        if show_test_hint:
            tip = accent(f"dojo test {problem.problem_id}")
            click.echo(f"  {dim('Tip:')} Run {tip} to grade it automatically")
    else:
        click.echo(f"  Status: {status.value.upper()}")

    if problem.last_graded:
        click.echo(f"  {dim('Last Graded')}  {problem.last_graded}")

    if problem.notes:
        click.echo(f"  {dim('Notes')}        {problem.notes}")

    click.echo()


def render_grade_result(result) -> None:
    """Outcome of applying a grade (GradeResult)."""
    click.echo()

    if result.status == "passed":
        click.echo(f"  {success('MARKED AS PASSED')}")
    elif result.status == "failed":
        click.echo(f"  {error('MARKED AS FAILED')}")
    elif result.status == "skipped":
        click.echo(f"  {warn('MARKED AS SKIPPED')}")

    if result.notes and result.status in ("failed", "skipped"):
        click.echo(f"  {dim('Notes')}  {result.notes}")

    render_schedule_effect(result.schedule_effect)
    click.echo()


# --------------------------------------------------------------------------- #
# fetch                                                                       #
# --------------------------------------------------------------------------- #


def render_fetch_results(batch, *, version=None, custom_path=None) -> None:
    """Per-problem lines + summary for a fetch batch."""
    click.echo()
    for result in batch.results:
        if result.success:
            if custom_path is not None:
                click.echo(
                    f"  {problem_id(result.problem_id)}  {bold(result.title)}  "
                    f"{success('✓ placed')}  {dim(str(result.target_path))}"
                )
            elif version is not None:
                click.echo(
                    f"  {problem_id(result.problem_id)}  {bold(result.title)}  "
                    f"{success('✓ refetched')}  {dim('v' + str(version))}"
                )
            else:
                click.echo(
                    f"  {problem_id(result.problem_id)}  {bold(result.title)}  "
                    f"{success('✓ placed')}  {dim('v' + str(result.version))}"
                )
        elif result.skipped:
            if result.skip_reason == "already registered":
                click.echo(
                    f"  {problem_id(result.problem_id)}  {warn('~ skipped')}  "
                    f"{dim('already registered — use --new-attempt or --version N')}"
                )
            else:
                click.echo(
                    f"  {problem_id(result.problem_id)}  {warn('~ skipped')}  "
                    f"{dim(result.skip_reason)}",
                    err=True,
                )
        elif result.failed:
            click.echo(
                f"  {problem_id(result.problem_id)}  {error('✗ failed')}  {dim(result.error)}",
                err=True,
            )

    click.echo()
    click.echo(
        f"  {success(str(batch.placed_count) + ' placed')}  "
        f"{warn(str(batch.skipped_count) + ' skipped')}  "
        f"{dim(str(batch.failed_count) + ' failed')}"
    )


# --------------------------------------------------------------------------- #
# pick                                                                        #
# --------------------------------------------------------------------------- #


def render_pick(result) -> None:
    """The picked problem + pool context (PickResult with a pick)."""
    picked = result.picked
    label = result.scope.display_label

    header("Selected")
    blank()
    click.echo(
        f"  {bold('#' + str(picked.id))}  {bold(picked.title)}  "
        f"{difficulty_badge(picked.difficulty.value)}"
    )

    if picked.tags:
        tags_display = "  ".join(dim(t.value) for t in picked.tags[:5])
        if len(picked.tags) > 5:
            tags_display += f"  {dim(f'+{len(picked.tags) - 5} more')}"
        blank()
        click.echo(f"  {dim('Tags')}   {tags_display}")

    blank()
    click.echo(
        f"  {dim('Pool')}   {bold(str(result.pool_size))} {label}  "
        f"{dim('·')}  {bold(str(result.registered_count))} registered  "
        f"{dim('·')}  {bold(str(result.total_count))} total"
    )


def render_pick_empty(result) -> None:
    """No candidates for the given filters/scope."""
    from bytedojo.services import PickScope

    if result.total_count == 0:
        click.echo(f"  {dim('No problems found matching your criteria.')}")
        return
    if result.scope == PickScope.SOLVED:
        click.echo(f"  {dim('No registered problems matching your criteria.')}")
    else:
        click.echo(f"  {dim('All matching problems already registered.')}")
        click.echo(
            f"  {dim('total:')} {bold(str(result.total_count))}  "
            f"{dim('registered:')} {bold(str(result.registered_count))}"
        )


# --------------------------------------------------------------------------- #
# review                                                                      #
# --------------------------------------------------------------------------- #


def render_review_list(
    reviews, *, show_all: bool, review_freq: int, format_due_date
) -> None:
    """The due/all review table (`dojo review [--all]`)."""
    if not reviews:
        if show_all:
            click.echo()
            click.echo(f"  {dim('No problems scheduled for review yet.')}")
            click.echo(f"  {dim('Problems are scheduled when they pass dojo test.')}")
        else:
            click.echo()
            click.echo(f"  {success('No problems due for review!')}")
            click.echo(f"  {dim('Great job staying on top of your reviews.')}")

        click.echo()
        click.echo(
            f"  {dim('Current review frequency:')} {bold(str(review_freq))} days"
        )
        click.echo(f"  {dim('Change with: dojo settings review-frequency <days>')}")
        return

    due_count = sum(1 for r in reviews if r.days_until_due <= 0)

    click.echo()
    click.echo(dim("  " + "─" * 60))
    if show_all:
        click.echo(f"  {accent('All Scheduled Reviews')}")
    else:
        click.echo(f"  {warn(f'Problems Due for Review ({due_count})')}")
    click.echo(dim("  " + "─" * 60))

    click.echo()
    click.echo(f"  {'ID':>8}  {'Source':10}  {'Due':15}  {'Reviews':>7}  Title")
    click.echo(
        f"  {dim('-' * 8)}  {dim('-' * 10)}  {dim('-' * 15)}  {dim('-' * 7)}  {dim('-' * 20)}"
    )

    for r in reviews:
        title = r.title[:30] + "..." if len(r.title) > 30 else r.title
        due_date = format_due_date(r.next_review_date)
        display_id = r.problem_num if r.problem_num else r.problem_id

        if r.is_overdue:
            due_styled = error(f"{due_date:15}")
        elif r.is_due_today:
            due_styled = warn(f"{due_date:15}")
        else:
            due_styled = success(f"{due_date:15}")

        click.echo(
            f"  {display_id:>8}  {r.source:10}  {due_styled}  {r.repetitions:>7}  {title}"
        )

    click.echo()
    click.echo(dim("  " + "─" * 60))
    click.echo(f"  {dim('Review frequency:')} {review_freq} days")
    click.echo(dim("  " + "─" * 60))
    click.echo()

    if due_count > 0:
        click.echo(f"  {dim('Start reviewing with:')}  dojo review pick")
        click.echo(
            f"  {dim('Mark complete with:')}    dojo review complete <id> --[easy|good|hard]"
        )
        click.echo()


def render_review_pick(problem, due_count: int, format_due_date) -> None:
    """One randomly picked due review (`dojo review pick`)."""
    due_date = format_due_date(problem.next_review_date)
    display_id = problem.problem_num if problem.problem_num else problem.problem_id

    click.echo()
    click.echo(dim("  " + "─" * 60))
    click.echo(f"  {warn('Review This Problem')}")
    click.echo(dim("  " + "─" * 60))
    click.echo()
    click.echo(f"  {accent('#' + str(display_id))}  {bold(problem.title)}")
    click.echo(f"  {dim('Source')}          {problem.source.capitalize()}")
    click.echo(f"  {dim('Language')}        {problem.language.upper()}")
    click.echo(f"  {dim('Difficulty')}      {problem.difficulty or 'Unknown'}")
    click.echo(f"  {dim('Times Reviewed')}  {problem.repetitions}")
    click.echo(
        f"  {dim('Interval')}        {problem.interval_days} days  "
        f"{dim(f'ease {problem.ease_factor:.2f}')}"
    )
    click.echo(f"  {dim('Due')}             {due_date}")

    if problem.file_path:
        click.echo(f"  {dim('File')}            {dim(problem.file_path)}")

    click.echo()
    click.echo(dim("  " + "─" * 60))
    click.echo(f"  {dim('Due for review:')} {bold(str(due_count))} problem(s)")
    click.echo(dim("  " + "─" * 60))
    click.echo()

    if problem.file_path:
        click.echo("  1. Open the file and solve it again")
        click.echo(f"  2. Re-test it: {accent(f'dojo test {display_id}')}")
        manual = f"(or dojo review complete {display_id} --easy/--good/--hard"
        click.echo(f"     {dim(manual + ' to grade recall manually)')}")
    click.echo()


def render_review_completion(title: str, r) -> None:
    """SM-2 before/after for `dojo review complete`."""
    click.echo()
    click.echo(dim("  " + "─" * 60))
    click.echo(f"  {success(f'Review Complete — {r.quality.value.upper()}')}")
    click.echo(dim("  " + "─" * 60))
    click.echo()
    click.echo(f"  {bold(title)}")
    click.echo()
    click.echo(
        f"  {dim('Interval')}      {r.previous_interval} days  →  "
        f"{accent(str(r.next_interval) + ' days')}"
    )
    click.echo(
        f"  {dim('Ease factor')}   {r.previous_ease:.2f}  →  "
        f"{accent(f'{r.next_ease:.2f}')}"
    )
    click.echo(
        f"  {dim('Repetitions')}   {r.previous_repetitions}  →  {r.next_repetitions}"
    )
    if r.next_review_date:
        click.echo(f"  {dim('Next review')}   {r.next_review_date}")
    click.echo()


def render_review_action(title: str, r) -> None:
    """Confirmation for review add / snooze / remove."""
    headlines = {
        "add": (success, "Added to Review Queue"),
        "snooze": (warn, "Review Snoozed"),
        "remove": (dim, "Removed from Queue"),
    }
    style_fn, headline = headlines.get(r.action, (accent, r.action.upper()))

    click.echo()
    click.echo(dim("  " + "─" * 60))
    click.echo(f"  {style_fn(headline)}")
    click.echo(dim("  " + "─" * 60))
    click.echo()
    click.echo(f"  {bold(title)}")
    click.echo()

    if r.action == "add" and r.interval_days is not None:
        click.echo(f"  {dim('Initial interval')}  {r.interval_days} days")
    if r.action == "snooze" and r.interval_days is not None:
        click.echo(f"  {dim('Snoozed by')}        {r.interval_days} days")
    if r.next_review_date is not None:
        click.echo(f"  {dim('Next review')}       {r.next_review_date}")

    click.echo()


def render_review_stats(stats, review_freq: int) -> None:
    """Counters for `dojo review stats`."""
    click.echo()
    click.echo(dim("  " + "─" * 60))
    click.echo(f"  {accent('Review Statistics')}")
    click.echo(dim("  " + "─" * 60))
    click.echo()

    click.echo(f"  {dim('Review Frequency')}  {review_freq} days")
    click.echo()
    due_styled = (
        warn(str(stats.due_today))
        if stats.due_today > 0
        else success(str(stats.due_today))
    )
    click.echo(f"  {dim('Due Today')}         {due_styled}")
    click.echo(f"  {dim('Due This Week')}      {stats.due_this_week}")
    click.echo(f"  {dim('Total in Review')}    {stats.total_in_review}")

    click.echo()
    click.echo(dim("  " + "─" * 60))
    click.echo()


# --------------------------------------------------------------------------- #
# stats                                                                       #
# --------------------------------------------------------------------------- #


def render_stats_summary(stats) -> None:
    """Registered-problem counts (`dojo stats`)."""
    header("Problems")
    blank()
    kv("Total", f"{stats.total_problems} registered")

    if stats.by_difficulty:
        blank()
        click.echo(f"  {accent('By difficulty')}")
        for diff, count in sorted(stats.by_difficulty.items()):
            click.echo(f"    {difficulty_badge(diff):<24}  {bold(str(count))}")

    if stats.by_source:
        blank()
        click.echo(f"  {accent('By source')}")
        for src, count in sorted(stats.by_source.items()):
            click.echo(f"    {dim(src):<12}  {bold(str(count))}")


def render_problem_list(problems, attempt_stats=None) -> None:
    """Per-problem cards (`dojo stats --list [-v]`).

    `attempt_stats` maps problem_id -> AttemptStats|None; None disables
    the attempts row entirely (non-verbose mode).
    """
    if not problems:
        click.echo(f"  {dim('No problems found matching criteria.')}")
        return

    click.echo(f"  Found {bold(str(len(problems)))} problem(s)")
    blank()

    for problem in problems:
        click.echo(f"  {accent('#' + str(problem.problem_id))}  {bold(problem.title)}")
        click.echo(f"    {dim('source')}      {problem.source}")
        badge = difficulty_badge(
            problem.difficulty.value if problem.difficulty else "Unknown"
        )
        click.echo(f"    {dim('difficulty')}  {badge}")
        click.echo(
            f"    {dim('language')}    {problem.language.value if problem.language else 'unknown'}"
        )
        click.echo(f"    {dim('fetched')}     {problem.fetched_at}")

        if problem.file_path:
            click.echo(f"    {dim('file')}        {dim(problem.file_path)}")

        if attempt_stats is not None:
            _render_attempt_counts(attempt_stats.get(problem.problem_id))
        blank()


def _render_attempt_counts(entry) -> None:
    if entry is None:
        click.echo(f"    {dim('attempts')}    {dim('none recorded')}")
        return
    click.echo(
        f"    {dim('attempts')}    "
        f"{bold(str(entry.total_attempts))} "
        f"{dim(f'(latest v{entry.latest_version})')}  "
        f"{dim('pass')} {entry.pass_count}  "
        f"{dim('fail')} {entry.fail_count}  "
        f"{dim('skip')} {entry.skip_count}  "
        f"{dim('runs')} {entry.total_runs}"
    )


# --------------------------------------------------------------------------- #
# query                                                                       #
# --------------------------------------------------------------------------- #


def render_query_page(problems, page: int, per_page: int, status_lookup) -> tuple:
    """One page of the catalog with status badges (`dojo query`).

    `status_lookup(problem_id)` returns the status string to badge.
    Returns (clamped_page, total_pages).
    """
    total = len(problems)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)

    click.echo(f"\n  Problems {dim(f'(page {page}/{total_pages}, {total} total)')}\n")

    for problem in problems[start_idx:end_idx]:
        status_icon = status_short(status_lookup(problem.id))
        diff_icon = difficulty_short(problem.difficulty.value)
        click.echo(f"  {problem.id:>5}  {status_icon}  {diff_icon}  {problem.title}")

    click.echo()
    hint(f"n next  p prev  q quit  ·  page {page} of {total_pages}")

    return page, total_pages


# --------------------------------------------------------------------------- #
# support                                                                     #
# --------------------------------------------------------------------------- #


def render_support(r) -> None:
    """Environment + toolchain report (`dojo support`)."""
    blank()
    click.echo(dim("  " + "─" * 70))
    click.echo(f"  {accent('ByteDojo Support')}")
    click.echo(dim("  " + "─" * 70))
    blank()

    click.echo(f"  {accent('Environment')}")
    click.echo(f"    {dim('ByteDojo')}    {r.bytedojo_version}")
    click.echo(f"    {dim('Python')}      {r.python_version}")
    if not r.python_supported:
        click.echo(
            f"                 {warn('Python 3.10+ is required — this interpreter is older.')}"
        )
    click.echo(f"                 {dim(r.python_executable)}")
    click.echo(f"    {dim('Platform')}    {r.platform_name}  {dim(r.platform_id)}")
    if r.repository_path:
        click.echo(f"    {dim('Repository')}  {r.repository_path}")
    else:
        click.echo(f"    {dim('Repository')}  {dim('not in a .dojo repository')}")

    blank()
    click.echo(f"  {accent('Toolchains')}")
    if not r.toolchains:
        click.echo(f"    {dim('(none registered)')}")
    for status in r.toolchains:
        lang = status.language.value
        if status.found:
            marker = success("[OK]") if not status.warning else warn("[WARN]")
            version = status.version or "version unknown"
            click.echo(f"    {marker}  {bold(lang):<14}  {version}")
            for binary, path in status.paths.items():
                click.echo(f"              {dim(f'{binary}: {path}')}")
            if status.warning:
                click.echo(f"              {warn(status.warning)}")
        else:
            marker = error("[NO]")
            missing = ", ".join(status.missing) or "unknown"
            click.echo(f"    {marker}  {bold(lang):<14}  {dim('Missing:')} {missing}")
            if status.install_hint:
                click.echo(f"              {warn(f'Install: {status.install_hint}')}")

    blank()
    click.echo(dim("  " + "─" * 70))
    if r.toolchains:
        if r.all_ready:
            click.echo(success(f"  All {r.total_count} toolchains ready."))
        else:
            click.echo(
                f"  {warn(str(r.ready_count))} of {r.total_count} toolchains ready."
            )
    blank()

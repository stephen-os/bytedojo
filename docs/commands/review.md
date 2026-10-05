# `dojo review`

> Spaced-repetition review system (group with subcommands).

## Synopsis

```
dojo review [--all]
dojo review pick
dojo review complete [IDENTIFIER] (--easy | --good | --hard) [selectors]
dojo review add      [IDENTIFIER] [--days N] [selectors]
dojo review snooze   [IDENTIFIER] [--days N] [selectors]
dojo review remove   [IDENTIFIER] [selectors]
dojo review stats
```

## Description

ByteDojo schedules reviews with SM-2: each problem on the track carries
a repetition count, an ease factor and an interval. A problem enters the
track the first time it passes `dojo test` (or `dojo grade --pass`).

**Testing a due problem IS completing its review** — a plain pass counts
as quality *good* and advances the interval. The `complete` subcommand
exists to signal the two other recall qualities explicitly:

- `--easy` — recalled effortlessly; ease grows, intervals stretch faster
- `--good` — the standard step (what a test pass records)
- `--hard` — a lapse: repetitions reset and the problem returns tomorrow,
  with a lowered ease

Failing a test (or `grade --fail`) also lapses a scheduled problem.
Passing a problem *before* it's due changes nothing — early practice
doesn't pull reviews forward.

### Subcommands

- *(default)* — table of reviews due today (`--all` for every schedule)
- `pick` — choose a random due review to work on
- `complete` — apply an explicit quality rating (above)
- `add` — manually queue a problem without grading it (`--days N` sets
  the initial interval; errors if it's already queued)
- `snooze` — push the due date to N days from today (default 1) without
  touching the SM-2 state
- `remove` — drop a problem from the queue entirely
- `stats` — due today / due this week / total counters

## Options

| Flag | Applies to | Description |
| --- | --- | --- |
| `--all`, `-a` | *(default view)* | Show all schedules, not just due |
| `--easy` / `--good` / `--hard` | `complete` | Recall quality (required, one of) |
| `--days N` | `add`, `snooze` | Interval / snooze length in days |
| `--name`, `--desc`, `--last`, `--python` | `complete`, `add`, `snooze`, `remove` | Standard selectors |

## Examples

```bash
dojo review                       # What's due today?
dojo review --all                 # Every scheduled review
dojo review pick                  # Give me one to do
dojo test 1                       # Solving a due problem = review done (good)
dojo review complete 1 --easy     # ...or grade recall explicitly
dojo review add 42 --days 3       # Queue manually, first review in 3 days
dojo review snooze 1 --days 2     # Not today — push it out
dojo review remove 1              # Drop from the queue
dojo review stats                 # Counters
```

## See also

- [`test`](test.md) — the primary way reviews get completed
- [`settings`](settings.md) — `review-frequency` sets the base interval

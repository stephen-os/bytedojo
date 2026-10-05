<p align="center">
  <img src="assets/banner.png" alt="ByteDojo Banner" width="100%">
</p>

<p align="center">
  <strong>A fully offline CLI for practising LeetCode problems in Python, on a spaced-repetition schedule</strong>
</p>

<p align="center">
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#the-loop">The Loop</a> •
  <a href="#commands">Commands</a> •
  <a href="docs/commands/README.md">CLI Reference</a>
</p>

---

## Features

- **Fully offline** — ~2,500 problems (statements + test cases) ship inside
  the package. No network, no account, no scraping at runtime.
- **Synthesised starter stubs** — `dojo fetch` builds a typed
  `class Solution` stub from the problem's method signature, complete with
  the prose description, examples and any `TreeNode`/`ListNode` helpers.
- **Local test runner** — `dojo test` executes your solution against the
  bundled cases and records the outcome.
- **Spaced repetition (SM-2)** — passing a test schedules the problem to
  resurface; passing it again when due advances the interval, failing
  lapses it back to tomorrow.
- **Versioned attempts** — re-attempts live side by side
  (`v001`, `v002`, ...) and each keeps its recorded outcome.
- **Smart search** — find problems by ID, name, description, difficulty
  or tag.
- **Python-only by design** — nothing *assumes* Python: formatters,
  toolchains and the runner sit behind seams so a second language is
  additive.

## Installation

### Requirements

- Python 3.10+
- pip

### Install from Source

```bash
git clone https://github.com/stephen-os/bytedojo.git
cd bytedojo
pip install .
```

### Verify Installation

```bash
dojo --version
dojo support
```

## Quick Start

```bash
# 1. Initialize a dojo repository
dojo init

# 2. Fetch a problem (or let dojo pick one: dojo pick --fetch)
dojo fetch 1

# 3. Solve it
#    problems/0001-two-sum/v001/solution.py

# 4. Run it (executes the __main__ block)
dojo run 1

# 5. Test it — a pass schedules the review automatically
dojo test 1

# 6. When reviews come due, see them and go again
dojo review
```

## The Loop

```
fetch → solve → run → test → (review comes due) → test again → ...
```

`dojo test` is the heart of the loop:

| Outcome | Problem status | Schedule effect |
| --- | --- | --- |
| Pass, not yet scheduled | `PASSED` | Review created at the base interval (default 7 days) |
| Pass, review due | `PASSED` | Review advanced (SM-2, quality *good*) |
| Pass, review not yet due | `PASSED` | No change — early practice doesn't thrash the schedule |
| Fail / error | `FAILED` / `ERROR` | Scheduled review lapses — due again tomorrow |

`dojo grade` is the manual override (`--pass/--fail/--skip`) with the same
schedule effects; `--skip` sets a problem aside and drops its review.
`dojo review complete --easy/--good/--hard` exists to grade *recall
quality* explicitly — a plain test pass on a due problem counts as *good*.

## Commands

| Command | What it does |
| --- | --- |
| `dojo init` | Create a `.dojo/` repository |
| `dojo fetch IDS` | Place bundled problems (`1`, `1,2`, `1..10`); `--new-attempt` for v2+ |
| `dojo run` | Execute a solution's `__main__` and count the run |
| `dojo test` | Run the bundled cases, record the outcome, drive the schedule |
| `dojo grade` | View status; manually pass/fail/skip |
| `dojo pick` | Random problem by difficulty/tag; `--fetch` to grab it immediately |
| `dojo query` | Browse/filter the bundled catalog |
| `dojo review` | Due reviews; `pick`, `complete`, `add`, `snooze`, `remove`, `stats` |
| `dojo stats` | Summary or per-problem attempt detail |
| `dojo settings` | View/set `default-language`, `review-frequency`, `organize-by-language` |
| `dojo support` | Environment + toolchain diagnostic (validates Python ≥ 3.10) |

Full reference with options and examples: [docs/commands](docs/commands/README.md).

## Repository Layout

```
your-practice-repo/
├── .dojo/                     # database, settings, build area
└── problems/
    └── 0001-two-sum/
        ├── v001/
        │   └── solution.py
        └── v002/              # created by `dojo fetch 1 --new-attempt`
            └── solution.py
```

Versions are flat per problem — the version number is a monotonic attempt
ordinal, and language is attempt metadata rather than a path segment. The
optional `organize-by-language` setting reintroduces a `<language>/` path
segment if you prefer it.

## Notes

- The corpus is frozen at what ships in the package; `dojo fetch` is
  deliberately restricted to it so every fetched problem is runnable,
  testable and gradable. Expanding the corpus is a planned follow-up.
- Problem content is derived from LeetCode and bundled for personal,
  non-commercial practice — see [NOTICE](NOTICE).
- Code is MIT-licensed — see [LICENSE](LICENSE).

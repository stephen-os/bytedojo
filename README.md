# ByteDojo

A CLI tool for fetching, solving, and tracking LeetCode problems. Master coding through structured practice and track your progress.

## Features

- **LeetCode Integration**: Fetch problems directly from LeetCode
- **Smart Problem Discovery**: Query and filter problems by difficulty and tags
- **Random Problem Picker**: Get random unsolved problems matching your criteria
- **Manual Grading**: Grade your solutions after verifying on LeetCode
- **Spaced Repetition**: Passed problems are scheduled for review to reinforce learning
- **Progress Tracking**: Track solved problems with pass/fail/skip status in a local database
- **Interactive Navigation**: Browse problem lists with pagination without re-fetching
- **Ready-to-Run Files**: Generated problem files include solution templates

## Installation

### Requirements

- Python 3.8 or higher
- pip

### Install from Source

```bash
# Clone the repository
git clone https://github.com/stephen-os/bytedojo.git
cd bytedojo

# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
dojo --version
dojo --help
```

## Quick Start

```bash
# 1. Initialize a new dojo repository in your project
dojo init

# 2. Fetch a LeetCode problem
dojo leetcode fetch 1

# 3. Solve the problem in the generated file
# Edit: problems/easy/0001-two-sum.py

# 4. Submit to LeetCode to verify, then grade your solution
dojo grade last --pass

# 5. Check your progress
dojo stats
```

## Commands

### Global Options

```bash
dojo --help          # Show help
dojo --version       # Show version
dojo --author        # Show author info
dojo --desc          # Show full description
dojo --debug [cmd]   # Enable debug mode
```

### Initialize Repository

```bash
dojo init            # Initialize .dojo repository in current directory
```

Creates a `.dojo` directory with a SQLite database to track your progress.

---

### LeetCode Commands

#### Fetch Problems

```bash
# Fetch by problem number
dojo leetcode fetch 1                    # Fetch "Two Sum"
dojo leetcode fetch 1 2 3                # Fetch multiple problems
dojo leetcode fetch 42 --force           # Overwrite existing problem
```

#### Query Problems

Browse and search LeetCode problems with interactive pagination.

```bash
# Browse all problems
dojo leetcode query

# Filter by difficulty
dojo leetcode query -d easy              # Easy problems only
dojo leetcode query -d medium            # Medium problems only
dojo leetcode query -d hard              # Hard problems only

# Filter by tag
dojo leetcode query -t array             # Array problems
dojo leetcode query -t "dynamic-programming"  # DP problems
dojo leetcode query -t array -t tree     # Multiple tags (OR)

# Combined filters
dojo leetcode query -d easy -t array

# List all available tags
dojo leetcode query --list-tags

# Pagination options
dojo leetcode query --page 5             # Start at page 5
dojo leetcode query --per-page 50        # 50 problems per page
```

**Interactive Navigation:**
- `n` - Next page
- `p` - Previous page
- `#` - Jump to page number
- `q` - Quit

**Status Indicators:**
- `[P]` - Passed
- `[F]` - Failed
- `[S]` - Skipped
- `[ ]` - Not graded/fetched

#### Pick Random Problem

Get a random unsolved problem matching your criteria.

```bash
# Random unsolved problem
dojo leetcode pick

# Filter by difficulty
dojo leetcode pick -d easy
dojo leetcode pick -d medium
dojo leetcode pick -d hard

# Filter by tag
dojo leetcode pick -t array
dojo leetcode pick -t tree -t graph

# Include premium problems
dojo leetcode pick --include-premium
```

---

### Grade Solutions

Mark your solutions as passed, failed, or skipped. When you grade a problem as passed, it gets scheduled for spaced repetition review.

```bash
# Interactive batch grading (shows all ungraded problems)
dojo grade

# Grade the last fetched problem
dojo grade last                          # Interactive prompt
dojo grade last --pass                   # Quick pass
dojo grade last --fail -n "TLE issue"    # Fail with notes

# Grade a specific problem
dojo grade problem 1                     # LeetCode #1 (interactive)
dojo grade problem 1 --pass              # Quick pass
dojo grade problem 1 -f -n "Need DP"     # Fail with notes
```

**Flags:**
- `--pass` / `-p` - Mark as passed (schedules review)
- `--fail` / `-f` - Mark as failed
- `--skip` / `-s` - Mark as skipped
- `--notes` / `-n` - Add notes (works with any status)

---

### Spaced Repetition Review

Problems you pass are automatically scheduled for review to reinforce learning.

```bash
# Show problems due for review
dojo review

# Show all scheduled reviews
dojo review --all

# Pick a random problem to review
dojo review pick

# View review statistics
dojo review stats
```

---

### View Statistics

```bash
dojo stats                               # View overall progress
```

---

## Problem File Example

When you fetch a LeetCode problem, ByteDojo generates a Python file like this:

```python
"""
LeetCode Problem #1: Two Sum
Difficulty: Easy
"""

# ============================================================================
# PROBLEM DESCRIPTION
# ============================================================================
# Given an array of integers nums and an integer target, return indices of
# the two numbers such that they add up to target.
#
# You may assume that each input would have exactly one solution, and you
# may not use the same element twice.
#
# Example 1:
# Input: nums = [2,7,11,15], target = 9
# Output: [0,1]
# Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].

# ============================================================================
# SOLUTION
# ============================================================================

from typing import List

class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        pass  # Your solution here
```

---

## Directory Structure

After initialization, your project will look like this:

```
your-project/
├── .dojo/
│   └── dojo.db              # SQLite database for tracking progress
├── problems/
│   ├── easy/
│   │   └── 0001-two-sum.py
│   ├── medium/
│   └── hard/
└── README.md
```

---

## LeetCode Difficulty

| Level | Description |
|-------|-------------|
| Easy | Beginner-friendly problems |
| Medium | Intermediate complexity |
| Hard | Advanced algorithmic challenges |

---

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bytedojo

# Run specific test file
pytest tests/bytedojo/core/leetcode/test_client.py
```

### Code Style

```bash
# Format code
black src/

# Lint
flake8 src/

# Type check
mypy src/
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

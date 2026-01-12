# ByteDojo

A CLI tool for fetching, solving, and tracking programming problems from LeetCode and Codeforces. Master coding through structured practice and track your progress.

## Features

- **Multi-Platform Support**: Fetch problems from LeetCode and Codeforces
- **Smart Problem Discovery**: Query and filter problems by difficulty, rating, and tags
- **Random Problem Picker**: Get random unsolved problems matching your criteria
- **Progress Tracking**: Track solved problems with pass/fail status in a local database
- **Interactive Navigation**: Browse problem lists with pagination without re-fetching
- **Ready-to-Run Files**: Generated problem files include solution templates and test cases

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
# Edit: problems/leetcode/easy/1-two-sum.py

# 4. Test your solution
dojo test problems/leetcode/easy/1-two-sum.py

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
- `[P]` - Passed (tests passing)
- `[F]` - Failed (tests failing)
- `[U]` - Untested (fetched but not tested)
- `[ ]` - Not fetched

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

### Codeforces Commands

#### Fetch Problems

```bash
# Fetch by problem ID (contestId + index)
dojo codeforces fetch 4A                 # Fetch "Watermelon"
dojo codeforces fetch 1A 4A 71A          # Fetch multiple problems
dojo codeforces fetch 1850A --force      # Overwrite existing
```

#### Query Problems

Browse Codeforces problems with rating-based filtering.

```bash
# Browse all problems
dojo codeforces query

# Filter by difficulty level
dojo codeforces query -d easy            # Rating < 1200
dojo codeforces query -d medium          # Rating 1200-1599
dojo codeforces query -d hard            # Rating 1600-2099
dojo codeforces query -d expert          # Rating 2100+

# Filter by exact rating range
dojo codeforces query -r 1200 -R 1600    # Min 1200, max 1600

# Filter by tag
dojo codeforces query -t dp              # Dynamic programming
dojo codeforces query -t graphs -t trees # Multiple tags

# List all available tags
dojo codeforces query --list-tags
```

#### Pick Random Problem

```bash
# Random unsolved problem
dojo codeforces pick

# Filter by difficulty
dojo codeforces pick -d easy
dojo codeforces pick -d hard

# Filter by rating range
dojo codeforces pick -r 1200 -R 1800

# Filter by tag
dojo codeforces pick -t dp
```

---

### Test Solutions

Run tests on your solution files.

```bash
# Test a specific file
dojo test problems/leetcode/easy/1-two-sum.py

# Test with verbose output
dojo test problems/leetcode/easy/1-two-sum.py --verbose
```

---

### View Statistics

```bash
dojo stats                               # View overall progress
```

---

## Problem File Examples

### LeetCode Problem File

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

### Codeforces Problem File

Codeforces problems use stdin/stdout and generate files like this:

```python
"""
Codeforces Problem 4A: Watermelon
Difficulty: Easy (800)
URL: https://codeforces.com/problemset/problem/4/A
Time Limit: 1 second
Memory Limit: 64 megabytes
Tags: brute force, math
"""

# ============================================================================
# PROBLEM DESCRIPTION
# ============================================================================
# One hot summer day Pete and his friend Billy decided to buy a watermelon.
# They chose the biggest one, but the seller refused to sell it to them in a
# single piece. The seller agreed to cut it into two parts. Pete and Billy
# want both parts to weigh even number of kilograms each.
#
# INPUT:
# The first line contains a single integer w (1 <= w <= 100) - the weight
# of the watermelon bought by the boys.
#
# OUTPUT:
# Print YES if the boys can divide the watermelon, NO otherwise.
#
# EXAMPLES:
#   Example 1:
#     Input:
#       8
#     Output:
#       YES

# ============================================================================
# SOLUTION
# ============================================================================

def solve():
    """
    Solve the problem.

    Read input from stdin and print output to stdout.
    """
    # Read input
    # w = int(input())

    # Your solution here
    pass


if __name__ == "__main__":
    solve()

# ============================================================================
# TESTS
# ============================================================================

import io
import sys


def run_tests():
    """Run sample test cases."""
    test_cases = [
        ("8", "YES"),
    ]

    passed = 0
    failed = 0

    for i, (test_input, expected) in enumerate(test_cases, 1):
        # Capture stdin/stdout
        old_stdin = sys.stdin
        old_stdout = sys.stdout
        sys.stdin = io.StringIO(test_input.replace("\\n", "\n"))
        sys.stdout = io.StringIO()

        try:
            solve()
            actual = sys.stdout.getvalue().strip()
            expected_clean = expected.replace("\\n", "\n").strip()

            if actual == expected_clean:
                print(f"Test {i}: PASSED", file=sys.stderr)
                passed += 1
            else:
                print(f"Test {i}: FAILED", file=sys.stderr)
                print(f"  Expected: {expected_clean!r}", file=sys.stderr)
                print(f"  Actual: {actual!r}", file=sys.stderr)
                failed += 1
        except Exception as e:
            print(f"Test {i}: ERROR - {e}", file=sys.stderr)
            failed += 1
        finally:
            sys.stdin = old_stdin
            sys.stdout = old_stdout

    print(f"\nResults: {passed} passed, {failed} failed")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_tests()
    else:
        solve()
```

Run Codeforces tests with:
```bash
python problems/codeforces/easy/4A-watermelon.py test
```

---

## Directory Structure

After initialization, your project will look like this:

```
your-project/
├── .dojo/
│   └── dojo.db              # SQLite database for tracking progress
├── problems/
│   ├── leetcode/
│   │   ├── easy/
│   │   │   └── 1-two-sum.py
│   │   ├── medium/
│   │   └── hard/
│   └── codeforces/
│       ├── easy/
│       │   └── 4A-watermelon.py
│       ├── medium/
│       ├── hard/
│       └── expert/
└── README.md
```

---

## Rating Systems

### LeetCode Difficulty
| Level | Description |
|-------|-------------|
| Easy | Beginner-friendly problems |
| Medium | Intermediate complexity |
| Hard | Advanced algorithmic challenges |

### Codeforces Rating
| Level | Rating Range | Description |
|-------|--------------|-------------|
| Easy | < 1200 | Newbie/Pupil level |
| Medium | 1200-1599 | Specialist level |
| Hard | 1600-2099 | Expert level |
| Expert | 2100+ | Master/Grandmaster level |

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

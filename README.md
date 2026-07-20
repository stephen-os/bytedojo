<p align="center">
  <img src="assets/banner.png" alt="ByteDojo Banner" width="100%">
</p>

<p align="center">
  <strong>A CLI for fetching, solving, and tracking LeetCode problems</strong>
</p>

<p align="center">
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#commands">Commands</a> •
  <a href="docs/commands/README.md">CLI Reference</a> •
  <a href="#features">Features</a>
</p>

---

## Features

- **Multi-Language Support** - Fetch and solve problems in Python, Java, or C++
- **Configurable Defaults** - Set your preferred language and settings
- **LeetCode Integration** - Fetch problems directly with solution templates
- **Smart Search** - Find problems by ID, name, or description
- **Scheduled Review** - Passed problems are scheduled for periodic review
- **Progress Tracking** - Track solved problems with pass/fail/skip status
- **Interactive Grading** - Browse and grade problems with pagination

## Installation

### Requirements

- Python 3.10+
- pip

### Install from Source

```bash
git clone https://github.com/stephen-os/bytedojo.git
cd bytedojo
pip install -e .
```

### Verify Installation

```bash
dojo --version
dojo --help
```

## Quick Start

```bash
# 1. Initialize a dojo repository
dojo init

# 2. Fetch a problem (uses your default language)
dojo fetch 1

# 3. Solve the problem in the generated file
#    problems/0001-two-sum/python3/v001/solution.py

# 4. Grade your solution (passing schedules a review)
dojo grade 1 --pass

# 5. Review problems on schedule
dojo review
```

## Commands

> Quick summary below. For every flag, every example, and the full
> behaviour of each command, see the **[CLI Reference](docs/commands/README.md)**.

### Initialize

```bash
dojo init                    # Create .dojo repository
```

### Fetch Problems

```bash
dojo fetch 1                 # Fetch problem #1 (default language)
dojo fetch 1 --python        # Fetch as Python
dojo fetch 1 --java          # Fetch as Java
dojo fetch 1 --cpp           # Fetch as C++
dojo fetch 1,2,3             # Fetch multiple
dojo fetch 1..10             # Fetch range
dojo fetch 1 --force         # Overwrite existing
```

### Grade Solutions

```bash
dojo grade                   # Interactive batch grading
dojo grade 1                 # Grade problem #1
dojo grade 1 --pass          # Quick pass
dojo grade 1 --fail          # Mark as failed
dojo grade 1 --skip          # Skip for now
dojo grade --last --pass     # Pass most recent
```

### Query & Pick Problems

```bash
dojo query                   # Browse all problems
dojo query -d easy           # Filter by difficulty
dojo query -t array          # Filter by tag
dojo query --list-tags       # Show all tags

dojo pick                    # Random unsolved problem
dojo pick -d medium          # Random medium problem
dojo pick -t tree            # Random tree problem
```

### Review System

```bash
dojo review                  # Show problems due for review
dojo review --all            # Show all scheduled reviews
dojo review pick             # Pick random due problem
dojo review stats            # Review statistics
```

### Settings

```bash
dojo settings                # View all settings
dojo settings list           # Same as above

# Change default language
dojo settings default-language python
dojo settings default-language java
dojo settings default-language cpp

# Change review frequency
dojo settings review-frequency 7     # Weekly (default)
dojo settings review-frequency 14    # Bi-weekly
```

➡ **Full per-command reference: [docs/commands/](docs/commands/README.md)**

## Directory Structure

```
your-project/
├── .dojo/
│   ├── db.sqlite            # Progress + attempts + reviews
│   ├── settings.json        # Local preferences
│   ├── .gitignore           # Excludes build artefacts
│   └── README.md            # Describes the layout
├── problems/
│   └── 0001-two-sum/
│       ├── python3/
│       │   └── v001/
│       │       ├── solution.py
│       │       └── tree_node.py   # sibling files when needed
│       ├── java/
│       │   └── v001/
│       │       ├── Solution.java
│       │       └── TreeNode.java
│       └── cpp/
│           └── v001/
│               ├── solution.cpp
│               └── tree_node.hpp
└── README.md
```

Each `dojo fetch` registers a new versioned attempt under
`problems/<id>-<slug>/<lang>/v{NNN}/`. Refetching with `--version N`
rewrites that specific version in place; refetching with `--force`
bumps to the next version so v1's recorded test outcome stays intact.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=bytedojo
```

## License

MIT License - see [LICENSE](LICENSE) for details.

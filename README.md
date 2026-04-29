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
- **Build Directory** - Compiled artifacts kept separate in `.dojo/build/`

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
#    problems/0001-two-sum/solution.py

# 4. Run your solution locally
dojo run 1

# 5. Submit to LeetCode, then grade your solution
dojo grade 1 --pass

# 6. Review problems on schedule
dojo review
```

## Commands

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

### Run Solutions

```bash
dojo run 1                   # Run problem #1
dojo run 1 --java            # Run Java version
dojo run --name "Two Sum"    # Search by name
dojo run --last              # Run most recent
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

### Statistics

```bash
dojo stats                   # View progress summary
dojo stats --list            # List all problems
```

## Directory Structure

```
your-project/
├── .dojo/
│   ├── db.sqlite            # Progress database
│   ├── settings.json        # Configuration
│   └── build/               # Compiled artifacts (Java/C++)
│       └── 0001/
│           └── Main.class
├── problems/
│   └── 0001-two-sum/
│       ├── solution.py
│       ├── solution.java
│       └── solution.cpp
└── README.md
```

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

"""
Template content for ByteDojo repository files.
"""

GITIGNORE = """
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# ByteDojo
logs/
*.log
build/
""".strip()

README = """
# ByteDojo Repository

This directory contains your ByteDojo data:

## Structure
```
.dojo/
├── db.sqlite          # Problem tracking database
├── settings.json      # User preferences
├── build/             # Test-run staging area (safe to delete)
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## Database Schema

- **problems**: Fetched problems and their latest status
- **attempts**: Versioned solution attempts (v1, v2, ...)
- **reviews**: Spaced repetition schedule (SM-2)
- **config**: Internal repository bookkeeping

## Usage
```bash
# Fetch a problem
dojo fetch 1

# Test your solution (a pass schedules the review)
dojo test 1

# Review problems that are due
dojo review
```

## Tip

You can commit the `.dojo/` directory to track your progress across machines.
The bundled `.gitignore` already excludes build artifacts and logs.
""".strip()

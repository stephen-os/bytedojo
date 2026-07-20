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
""".strip()

README = """
# ByteDojo Repository

This directory contains your ByteDojo data:

## Structure
```
.dojo/
├── db.sqlite          # Problem tracking database
├── settings.json      # User preferences
├── logs/              # Debug logs (created in --debug mode)
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## Database Schema

- **problems**: Fetched problems and metadata
- **attempts**: Your solution attempts and results
- **reviews**: Spaced repetition schedule
- **stats**: Daily statistics
- **config**: Repository preferences

## Usage
```bash
# Fetch problems
dojo fetch 1

# Grade your solutions
dojo grade 1 --pass

# Review problems that are due
dojo review
```

## Tip

You can commit the `.dojo/` directory to track your progress across machines.
Just make sure to add `.dojo/logs/` to your `.gitignore` if you don't want to commit logs.
""".strip()

"""Setup script for ByteDojo."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

setup(
    name="bytedojo",
    version="0.1.0",
    description="A CLI tool for fetching and solving programming problems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Stephen Watson",
    python_requires=">=3.8",
    packages=find_packages(where="src"),
    package_dir={"": "src"}, 
    install_requires=[
        "click>=8.0.0",
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "sqlalchemy>=2.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bytedojo=bytedojo.main:main",
            "dojo=bytedojo.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
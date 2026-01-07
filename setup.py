#!/usr/bin/env python3
"""Setup script for Sona - The AI-Native Programming Language"""

import os

from setuptools import find_packages, setup


# Read the contents of README.md for long description
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="Sona: AI-Native Programming Language",
    version="0.10.1",
    author="Sona Development Team",
    author_email="sona-dev@hotmail.com",
    description=(
        "The world's first AI-native programming language with "
        "cognitive accessibility features"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Bryantad/Sona.git",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Interpreters",
        "Topic :: Software Development :: Compilers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "lark>=1.1.0",
        "pygls>=1.3.1,<2",
        "openai>=1.0.0",
        "anthropic>=0.9.0",
        "python-dotenv>=0.19.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "flake8>=3.8",
            "black>=21.0",
        ]
    },
    entry_points={
        "console_scripts": [
            # Unified modern CLI
            "sona=sona.cli:main",
            "spm=sona.spm:main",
        ],
    },
    include_package_data=True,
    package_data={
        "sona": [
            "grammar/*.lark",
            "templates/*.sona",
            "examples/*.sona",
        ],
    },
    keywords=(
        "programming-language artificial-intelligence "
        "cognitive-accessibility ai-native"
    ),
    project_urls={
        "Bug Reports": "https://github.com/Bryantad/Sona/issues",
        "Source": "https://github.com/Bryantad/Sona.git",
        "Documentation": "https://github.com/Bryantad/Sona.wiki.git",
    },
)


"""
Keep all config in once place, so it's not scattered throughout the code.
"""
import os
from pathlib import Path

# TODO Right now, this is the root directory of expanded zip. Later, I want to just access
# the zip file directly

# Check for environment variable first (set by start_server.py)
_default_dir = os.environ.get('HEALTH_DATA_DIR', '/Users/tomhill/Downloads/apple_health_export_20260305')
_source_dir: Path = Path(_default_dir)

def get_source_dir() -> Path:
    """Get the current source directory"""
    return _source_dir

def set_source_dir(path: Path) -> None:
    """Set the source directory"""
    global _source_dir
    _source_dir = path


def get_cda_database_path() -> Path:
    """Get path to CDA observations database. This is stored in the current directory, so no path."""
    return Path("cda_observations.db")


def has_cda_database() -> bool:
    """Check if CDA database exists"""
    return get_cda_database_path().exists()


def get_apple_health_database_path() -> Path:
    """Get path to Apple Health database"""
    return Path("apple_health.db")


def has_apple_health_database() -> bool:
    """Check if Apple Health database exists"""
    return get_apple_health_database_path().exists()

import re
import unicodedata

def sanitize_filename_manual(filename, max_length=128):
    normalized = unicodedata.normalize('NFKD', filename)
    cleaned = re.sub(r'[^a-zA-Z0-9.\-_ ]', ' ', normalized)
    sanitized = cleaned.replace(' ', '_')
    sanitized = sanitized[:max_length]
    if not sanitized:
        sanitized = 'unnamed_file'
    return sanitized

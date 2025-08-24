"""
Keep all config in once place, so it's not scattered throughout the code.
"""
import os
from pathlib import Path

# TODO Right now, this is the root directory of expanded zip. Later, I want to just access
# the zip file directly

# Check for environment variable first (set by start_server.py)
_default_dir = os.environ.get('HEALTH_DATA_DIR', '/Users/tomhill/Downloads/apple_health_export')
_source_dir: Path = Path(_default_dir)

def get_source_dir() -> Path:
    """Get the current source directory"""
    return _source_dir

def set_source_dir(path: Path) -> None:
    """Set the source directory"""
    global _source_dir
    _source_dir = path

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
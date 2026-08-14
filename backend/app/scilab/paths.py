"""Shared paths for the Scilab integration."""

from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

SCRIPTS_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "scripts"

RESULT_FILE = "gridflex_results.txt"
INPUT_FILE = "inputs.sci"
OUTPUT_JSON_FILE = "gridflex_results.json"


def script(name: str) -> Path:
    """Return the path to an internal Scilab script by name."""
    path = SCRIPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Internal Scilab script not found: {name}")
    return path


@contextmanager
def temporary_workdir():
    """Create an isolated temporary execution directory for Scilab runs."""
    with tempfile.TemporaryDirectory(prefix="gridflex_scilab_") as directory:
        yield Path(directory)

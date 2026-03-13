"""Shelf framework executable reference implementation."""

from __future__ import annotations

from pathlib import Path
import sys


_SRC_DIR = Path(__file__).resolve().parent

# Compatibility bridge: unittest discovery may import packages as ``src.<pkg>``,
# while the repository runtime historically imports sibling packages from the
# ``src`` directory as top-level modules. Keep both import modes working.
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

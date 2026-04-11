"""
Translation Agent — Handles multi-language metadata for YouTube.
Integrated into title_agent.py but available standalone.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Translation is handled by title_agent.translate_metadata()
# This module re-exports that function for standalone use.

from agents.title_agent import translate_metadata

__all__ = ["translate_metadata"]

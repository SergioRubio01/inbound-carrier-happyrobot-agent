#!/usr/bin/env python3
"""
Main entry point for running CLI module as: python -m src.interfaces.cli
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.interfaces.cli import main  # noqa: E402

if __name__ == "__main__":
    asyncio.run(main())

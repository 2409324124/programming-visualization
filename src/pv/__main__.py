"""Entry point for ``python -m pv``."""

import sys
from pathlib import Path

# Ensure the src/ directory is on sys.path so that ``pv`` is importable
# regardless of where the user runs from.
_src = Path(__file__).resolve().parent.parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from pv.cli import main

main()

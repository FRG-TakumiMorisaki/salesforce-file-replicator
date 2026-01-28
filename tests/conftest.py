# Copyright (c) 2025
# This is a proprietary solution. Redistribution of modified versions is prohibited.
# Open-source dependency licenses are documented in the README table.

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

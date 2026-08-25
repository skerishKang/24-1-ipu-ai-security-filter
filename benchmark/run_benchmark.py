"""CLI entry point for the B63 R0-A benchmark.

Usage:
    python benchmark/run_benchmark.py --systems S0,S1,S3 --out benchmark/reports/R0_canonical
"""

from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from benchmark.runner import main  # noqa: E402 - path bootstrap must run first

if __name__ == "__main__":
    sys.exit(main())

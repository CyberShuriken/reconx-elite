#!/usr/bin/env python3
"""Run backend unit tests with cwd=backend (safe from repo root)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"


def main() -> int:
    if not (BACKEND / "tests").is_dir():
        print("Expected backend/tests under repo root.", file=sys.stderr)
        return 1

    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    proc = subprocess.run(cmd, cwd=str(BACKEND))
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())

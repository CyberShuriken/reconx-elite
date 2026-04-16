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
        print("Error: Expected backend/tests directory", file=sys.stderr)
        return 1

    try:
        cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
        proc = subprocess.run(cmd, cwd=str(BACKEND), check=False)
        if proc.returncode != 0:
            print(f"Test execution failed with return code {proc.returncode}.", file=sys.stderr)
        return proc.returncode
    except subprocess.SubprocessError as e:
        print(f"Test execution failed due to subprocess error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Test execution failed due to unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

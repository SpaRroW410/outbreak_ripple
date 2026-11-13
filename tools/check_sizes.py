"""Enforce the maintainability size rules (SDD section 10).

- Source files: target 300 lines (hard limit 500 fails the check; over 300 fails
  too unless listed in ALLOWED_OVER_TARGET with a reason).
- Card handlers in engine/actions/handlers.py: at most 40 lines each.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDERS = ("engine", "tools", "tests", "web")
SUFFIXES = (".py", ".js", ".mjs", ".css", ".html")
TARGET, HARD_LIMIT, HANDLER_LIMIT = 300, 500, 40
ALLOWED_OVER_TARGET: dict[str, str] = {}


def main() -> int:
    """Print violations; exit 1 if there are any."""
    problems: list[str] = []
    for folder in FOLDERS:
        for path in sorted((ROOT / folder).rglob("*")):
            if path.suffix not in SUFFIXES or "node_modules" in path.parts:
                continue
            lines = len(path.read_text(encoding="utf-8").splitlines())
            name = str(path.relative_to(ROOT))
            if lines > HARD_LIMIT or (lines > TARGET and name not in ALLOWED_OVER_TARGET):
                problems.append(f"{name}: {lines} lines (target {TARGET}, hard limit {HARD_LIMIT})")
    handlers = ROOT / "engine" / "actions" / "handlers.py"
    for node in ast.parse(handlers.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.FunctionDef):
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > HANDLER_LIMIT:
                problems.append(f"handler {node.name}: {length} lines (limit {HANDLER_LIMIT})")
    for problem in problems:
        print(f"SIZE ERROR: {problem}")
    print("sizes INVALID" if problems else "sizes OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

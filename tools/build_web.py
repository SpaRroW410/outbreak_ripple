"""Build the static web app into dist/ (SDD section 12).

dist/ = web/ files + pyodide/ (vendored from node_modules, no CDN) +
engine.zip (the Python engine) + content.json (the content bundle) + build.json.
Run `npm install` once before building. Nothing in dist/ calls the network.
"""

from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

import engine
from tools.content_io import load_bundle
from tools.validate_content import validate

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
PYODIDE_SOURCE = ROOT / "node_modules" / "pyodide"
PYODIDE_FILES = ("pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm", "python_stdlib.zip",
                 "pyodide-lock.json")
ZIP_DATE = (2020, 1, 1, 0, 0, 0)  # fixed timestamp so the build is reproducible


def build() -> int:
    """Create dist/. Returns a process exit code."""
    bundle = load_bundle()
    problems = validate(bundle)
    if problems:
        print("refusing to build: content is invalid (run python -m tools.validate_content)")
        return 1
    if not PYODIDE_SOURCE.exists():
        print("node_modules/pyodide not found: run `npm install` first")
        return 1
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ROOT / "web", DIST)
    (DIST / "pyodide").mkdir()
    for name in PYODIDE_FILES:
        shutil.copy(PYODIDE_SOURCE / name, DIST / "pyodide" / name)
    with zipfile.ZipFile(DIST / "engine.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / "engine").rglob("*.py")):
            info = zipfile.ZipInfo(str(path.relative_to(ROOT)), ZIP_DATE)
            archive.writestr(info, path.read_bytes(), zipfile.ZIP_DEFLATED)
    (DIST / "content.json").write_text(json.dumps(bundle, sort_keys=True), encoding="utf-8")
    versions = {"engine_version": engine.__version__, "content_version": bundle["version"]}
    (DIST / "build.json").write_text(json.dumps(versions), encoding="utf-8")
    size = sum(path.stat().st_size for path in DIST.rglob("*") if path.is_file())
    print(f"built {DIST} ({size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(build())

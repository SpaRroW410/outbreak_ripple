"""Dependency direction (SDD 3): imports point downward only; domains never import each other."""

import ast
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent.parent / "engine"
LAYERS = ["core", "world", "domains", "actions", "scoring", "assess"]  # low to high
STDLIB_ONLY_ALLOWED = {"__future__", "collections", "dataclasses", "hashlib", "json", "math",
                       "random", "statistics", "typing"}


def imports_of(path: Path) -> list[str]:
    names: list[str] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def test_engine_uses_only_listed_stdlib_modules_and_itself() -> None:
    for path in sorted(ENGINE.rglob("*.py")):
        for name in imports_of(path):
            top = name.split(".")[0]
            assert top == "engine" or top in STDLIB_ONLY_ALLOWED, f"{path}: imports {name}"


def test_layers_import_downward_only() -> None:
    for index, layer in enumerate(LAYERS):
        higher = LAYERS[index + 1:]
        top_level = ("api", "api_views", "content", "game", "registry", "results", "runner")
        for path in sorted((ENGINE / layer).rglob("*.py")):
            for name in imports_of(path):
                parts = name.split(".")
                if parts[0] != "engine" or len(parts) < 2:
                    continue
                assert parts[1] not in higher, f"{path}: {layer} imports higher layer {name}"
                assert parts[1] not in top_level, f"{path}: {layer} imports top-level {name}"


def test_domains_never_import_each_other() -> None:
    for domain_dir in sorted((ENGINE / "domains").iterdir()):
        if not domain_dir.is_dir() or domain_dir.name.startswith("__"):
            continue
        for path in sorted(domain_dir.rglob("*.py")):
            for name in imports_of(path):
                if name.startswith("engine.domains."):
                    assert name.split(".")[2] == domain_dir.name, f"{path}: imports {name}"

"""Local static server for dist/ (SDD section 12): `python -m tools.serve [port]`.

Serves on 127.0.0.1 only. Build first with `python -m tools.build_web`.
"""

from __future__ import annotations

import functools
import http.server
import sys
from pathlib import Path

DIST = Path(__file__).resolve().parent.parent / "dist"


class Handler(http.server.SimpleHTTPRequestHandler):
    """Static files with the MIME types Pyodide needs."""

    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".mjs": "text/javascript", ".wasm": "application/wasm"}

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Stay quiet (the UI test starts this server)."""


def main() -> None:
    """Serve dist/ until interrupted."""
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = functools.partial(Handler, directory=str(DIST))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"serving {DIST} at http://127.0.0.1:{port}/", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()

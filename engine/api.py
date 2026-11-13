"""The JSON API between the UI and the engine (documented in docs/API.md).

One `Session` object lives in the web worker. `handle_json` takes a request
`{"cmd": ..., "args": {...}}` and returns `{"ok": true, "result": ...}` or
`{"ok": false, "error": "..."}`. This is the only coupling point with `web/`.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import engine
from engine.api_views import chain_view, results_view, state_view
from engine.assess.export import build_export
from engine.content import Content, parse_content
from engine.game import Game, InvalidPlayError
from engine.results import Results, compute_results
from engine.runner import run


class Session:
    """Holds the content and the game in progress."""

    def __init__(self, bundle: Mapping[str, Any]) -> None:
        self.content: Content = parse_content(bundle)
        self.game: Game | None = None
        self.results: Results | None = None

    def handle_json(self, request_json: str) -> str:
        """Entry point used by the web worker."""
        try:
            request = json.loads(request_json)
            result = self.handle(str(request["cmd"]), request.get("args", {}))
            return json.dumps({"ok": True, "result": result})
        except (InvalidPlayError, KeyError, ValueError) as error:
            return json.dumps({"ok": False, "error": str(error)})

    def handle(self, cmd: str, args: Mapping[str, Any]) -> Any:
        """Dispatch one command."""
        if cmd == "new_game":
            self.game = Game(self.content, str(args["seed"]))
            self.results = None
            return state_view(self.game, [])
        if cmd == "benchmark":
            result = run(self.content, str(args["seed"]), [])
            return {"events": len(result.log), "digest": result.log.digest()}
        game = self._game()
        if cmd == "get_state":
            return state_view(game, [])
        if cmd == "play_turn":
            choices = [(str(play["card_id"]), str(play["target"])) for play in args["plays"]]
            feed = game.play_turn(choices)
            return state_view(game, feed)
        if cmd == "get_chain":
            return chain_view(game, int(args["event_id"]))
        if cmd == "get_diff":
            return results_view(self.content, game, self._results())
        if cmd == "export_session":
            return self._export(args)
        raise ValueError(f"unknown command: {cmd}")

    def _game(self) -> Game:
        if self.game is None:
            raise ValueError("no game in progress; call new_game first")
        return self.game

    def _results(self) -> Results:
        game = self._game()
        if not game.finished:
            raise ValueError("results are available after the last turn")
        if self.results is None:
            self.results = compute_results(self.content, game.sim.result())
        return self.results

    def _export(self, args: Mapping[str, Any]) -> dict[str, Any]:
        game = self._game()
        scores: dict[str, Any] = {}
        if game.finished:
            results = self._results()
            scores = {"health": results.health.to_dict(), "ripple": results.ripple.to_dict(),
                      "ripple_size": results.diff.ripple_size}
        plays = [{"turn": play.turn, "card_id": play.card_id, "target": play.target}
                 for play in game.plays]
        families = {card.id: card.family for card in self.content.cards.values()}
        return build_export(engine.__version__, self.content.version, game.seed_text, plays,
                            families, scores, [str(c) for c in args.get("concepts_viewed", [])])

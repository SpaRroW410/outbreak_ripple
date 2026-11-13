"""Validate everything under `content/` (run by `make check` and CI).

Checks the schema described in docs/CONTENT_GUIDE.md plus cross-references:
every concept has a competency, every parameter has a source or TODO, cards
only touch state keys that exist, and nothing refers to a missing id.
Exit code 1 if any problem is found.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from typing import Any

from engine.actions.cards import FAMILIES, TARGET_KINDS
from engine.actions.handlers import HANDLERS
from engine.actions.ops import OPS, WHERE
from engine.registry import build_domains
from tools.content_io import load_bundle

STATUSES = ("illustrative", "sourced", "reviewed")
SCHEDULABLE_KINDS = ("systems.stock_arrival", "systems.rumour_spread",
                     "infectious.school_reopens")
OP_FIELDS = {"set_state": ("key", "value"), "add_state": ("key", "amount"),
             "schedule_event": ("delay", "kind"), "inject_rumour": ("amount",),
             "handler": ("name",)}


def _require(item: Mapping[str, Any], fields: Mapping[str, type | tuple[type, ...]],
             label: str, problems: list[str]) -> bool:
    """Check that `item` has the fields with the right types."""
    ok = True
    for name, kind in fields.items():
        if name not in item:
            problems.append(f"{label}: missing field {name!r}")
            ok = False
        elif not isinstance(item[name], kind) or (kind is int and isinstance(item[name], bool)):
            problems.append(f"{label}: field {name!r} has the wrong type")
            ok = False
    return ok


def _unique_ids(items: list[Mapping[str, Any]], label: str, problems: list[str]) -> set[str]:
    ids = [str(item.get("id", "")) for item in items]
    for item_id in sorted(set(ids)):
        if ids.count(item_id) > 1 or not item_id:
            problems.append(f"{label}: missing or duplicate id {item_id!r}")
    return set(ids)


def check_parameters(bundle: Mapping[str, Any], problems: list[str]) -> None:
    """value, unit, source, status on every parameter; TODO sources stay illustrative."""
    for name, entry in sorted(bundle["parameters"].items()):
        label = f"parameter {name}"
        fields: dict[str, type | tuple[type, ...]] = {
            "value": (int, float), "unit": str, "source": str, "status": str}
        if not _require(entry, fields, label, problems):
            continue
        if isinstance(entry["value"], bool):
            problems.append(f"{label}: value must be a number")
        if not entry["unit"].strip() or not entry["source"].strip():
            problems.append(f"{label}: unit and source must not be empty (use \"TODO\")")
        if entry["status"] not in STATUSES:
            problems.append(f"{label}: status must be one of {STATUSES}")
        if entry["source"].strip().upper() == "TODO" and entry["status"] != "illustrative":
            problems.append(f"{label}: a parameter without a source must be illustrative")


def check_competencies(bundle: Mapping[str, Any], problems: list[str]) -> set[str]:
    """Competency entries; unverified ones must not carry an invented code."""
    for entry in bundle["competencies"]:
        label = f"competency {entry.get('id')}"
        fields = {"id": str, "code": str, "official_text": str, "verified": bool}
        if _require(entry, fields, label, problems) and not entry["verified"]:
            if entry["code"] != "TODO" or entry["official_text"] != "TODO":
                problems.append(f"{label}: unverified entries keep code and official_text "
                                "as \"TODO\" (only the owner fills them in)")
    return _unique_ids(bundle["competencies"], "competencies", problems)


def check_concepts(bundle: Mapping[str, Any], competencies: set[str],
                   problems: list[str]) -> set[str]:
    """Concept cards: text, competency id, parameter references."""
    for concept in bundle["concepts"]:
        label = f"concept {concept.get('id')}"
        fields = {"id": str, "title": str, "body": str, "competency": str, "parameters": list,
                  "status": str}
        if not _require(concept, fields, label, problems):
            continue
        if concept["competency"] not in competencies:
            problems.append(f"{label}: unknown competency {concept['competency']!r}")
        if concept["status"] not in ("draft", "reviewed"):
            problems.append(f"{label}: status must be draft or reviewed")
        for name in concept["parameters"]:
            if name not in bundle["parameters"]:
                problems.append(f"{label}: unknown parameter {name!r}")
    return _unique_ids(bundle["concepts"], "concepts", problems)


def check_effect(effect: Mapping[str, Any], label: str, state_keys: set[str],
                 problems: list[str]) -> None:
    """One declarative effect of a card."""
    op = effect.get("op")
    if op not in OPS:
        problems.append(f"{label}: unknown op {op!r}")
        return
    for name in OP_FIELDS[str(op)]:
        if name not in effect:
            problems.append(f"{label}: op {op} needs field {name!r}")
    if effect.get("where", "target") not in WHERE:
        problems.append(f"{label}: unknown where {effect.get('where')!r}")
    if "key" in effect and effect["key"] not in state_keys:
        problems.append(f"{label}: unknown state key {effect['key']!r}")
    if op == "handler" and effect.get("name") not in HANDLERS:
        problems.append(f"{label}: unknown handler {effect.get('name')!r}")
    if op == "schedule_event":
        if effect.get("kind") not in SCHEDULABLE_KINDS:
            problems.append(f"{label}: no domain handles scheduled kind {effect.get('kind')!r}")
        if not isinstance(effect.get("delay"), int) or effect.get("delay", 0) < 1:
            problems.append(f"{label}: delay must be a whole number of at least 1")


def check_cards(bundle: Mapping[str, Any], concepts: set[str], problems: list[str]) -> None:
    """Action cards: fields, costs, effects, concept references."""
    state_keys = {key for domain in build_domains() for key in domain.writes}
    for card in bundle["cards"]:
        label = f"card {card.get('id')}"
        fields = {"id": str, "name": str, "family": str, "description": str, "cost": dict,
                  "targets": str, "effects": list, "concepts": list}
        if not _require(card, fields, label, problems):
            continue
        if card["family"] not in FAMILIES:
            problems.append(f"{label}: unknown family {card['family']!r}")
        if card["targets"] not in TARGET_KINDS:
            problems.append(f"{label}: unknown target kind {card['targets']!r}")
        cost_fields = {"budget": int, "action_points": int}
        if _require(card["cost"], cost_fields, label, problems):
            if card["cost"]["budget"] < 0 or card["cost"]["action_points"] < 1:
                problems.append(f"{label}: budget >= 0 and action_points >= 1")
        if not card["effects"]:
            problems.append(f"{label}: a card needs at least one effect")
        for effect in card["effects"]:
            check_effect(effect, label, state_keys, problems)
        if not card["concepts"]:
            problems.append(f"{label}: a card demonstrates at least one concept")
        for concept in card["concepts"]:
            if concept not in concepts:
                problems.append(f"{label}: unknown concept {concept!r}")
    _unique_ids(bundle["cards"], "cards", problems)


def check_themes_and_strings(bundle: Mapping[str, Any], concepts: set[str],
                             problems: list[str]) -> None:
    """Themes, concept triggers and i18n strings."""
    for theme_id, theme in sorted(bundle["themes"].items()):
        for section in ("clock", "turn", "world", "scoring"):
            if section not in theme:
                problems.append(f"theme {theme_id}: missing section {section!r}")
    if "en" not in bundle["i18n"]:
        problems.append("i18n: content/i18n/en.json is required")
    strings = bundle["i18n"].get("en", {})
    for key, text in sorted(strings.items()):
        if not isinstance(text, str) or not text.strip():
            problems.append(f"i18n en: {key!r} must be non-empty text")
    for theme in bundle["themes"].values():
        for kind in theme.get("scoring", {}).get("chain_event_weights", {}):
            if f"event.{kind}" not in strings:
                problems.append(f"i18n en: no text for event kind {kind!r}")
    for domain in build_domains():
        for trigger in domain.concept_triggers():
            if trigger.concept_id not in concepts:
                problems.append(f"domain {domain.name}: trigger for unknown concept "
                                f"{trigger.concept_id!r}")
            if f"event.{trigger.event_kind}" not in strings:
                problems.append(f"i18n en: no text for event kind {trigger.event_kind!r}")


def check_quizzes(bundle: Mapping[str, Any], competencies: set[str],
                  problems: list[str]) -> None:
    """Quiz items (Phase 3). Agent-drafted items must be marked draft."""
    for item in bundle["quizzes"]:
        label = f"quiz {item.get('id')}"
        fields = {"id": str, "stem": str, "options": list, "answer": int, "rationale": str,
                  "competency": str, "difficulty": str, "form": str, "status": str}
        if not _require(item, fields, label, problems):
            continue
        if item["form"] not in ("A", "B") or item["status"] not in ("draft", "reviewed"):
            problems.append(f"{label}: form is A or B; status is draft or reviewed")
        if item["competency"] not in competencies:
            problems.append(f"{label}: unknown competency {item['competency']!r}")
        if not 0 <= item["answer"] < len(item["options"]):
            problems.append(f"{label}: answer must index an option")
    _unique_ids(bundle["quizzes"], "quizzes", problems)


def validate(bundle: Mapping[str, Any]) -> list[str]:
    """All problems found in a bundle (empty list = valid)."""
    problems: list[str] = []
    check_parameters(bundle, problems)
    competencies = check_competencies(bundle, problems)
    concepts = check_concepts(bundle, competencies, problems)
    check_cards(bundle, concepts, problems)
    check_themes_and_strings(bundle, concepts, problems)
    check_quizzes(bundle, competencies, problems)
    return problems


def summary(bundle: Mapping[str, Any]) -> str:
    """One line of counts, including how much content is still unreviewed."""
    statuses = [entry["status"] for entry in bundle["parameters"].values()]
    verified = sum(1 for entry in bundle["competencies"] if entry.get("verified"))
    return (f"{len(statuses)} parameters ({statuses.count('illustrative')} illustrative, "
            f"{statuses.count('sourced')} sourced, {statuses.count('reviewed')} reviewed), "
            f"{len(bundle['cards'])} cards, {len(bundle['concepts'])} concepts, "
            f"{len(bundle['competencies'])} competencies ({verified} verified), "
            f"{len(bundle['quizzes'])} quiz items")


def main() -> int:
    """Command-line entry point."""
    bundle = load_bundle()
    problems = validate(bundle)
    for problem in problems:
        print(f"CONTENT ERROR: {problem}")
    print(("content INVALID: " if problems else "content OK: ") + summary(bundle))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

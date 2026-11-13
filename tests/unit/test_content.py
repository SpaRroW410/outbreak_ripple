"""Content validation: the repository content is valid and the validator catches mistakes."""

import copy
from typing import Any

import pytest

from tools.content_io import load_bundle
from tools.validate_content import validate


@pytest.fixture(scope="module")
def bundle() -> dict[str, Any]:
    return load_bundle()


def test_repository_content_is_valid(bundle: dict[str, Any]) -> None:
    assert validate(bundle) == []


def test_phase_2_content_minimums(bundle: dict[str, Any]) -> None:
    assert len(bundle["cards"]) == 20
    assert sum(1 for card in bundle["cards"] if card["family"] == "meddle") >= 6
    assert len(bundle["concepts"]) >= 15


def test_governance_defaults(bundle: dict[str, Any]) -> None:
    """Agents never mark content reviewed or verified; unknown sources say TODO."""
    assert all(p["status"] != "reviewed" for p in bundle["parameters"].values())
    assert all(p["source"] == "TODO" or p["status"] == "sourced"
               for p in bundle["parameters"].values())
    assert all(entry["verified"] is False for entry in bundle["competencies"])
    assert all(concept["status"] == "draft" for concept in bundle["concepts"])


def broken(bundle: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(bundle)


def test_validator_catches_parameter_problems(bundle: dict[str, Any]) -> None:
    bad = broken(bundle)
    del bad["parameters"]["infectious.r0"]["source"]
    bad["parameters"]["infectious.case_fatality"]["status"] = "sourced"  # but source is TODO
    problems = "\n".join(validate(bad))
    assert "infectious.r0: missing field 'source'" in problems
    assert "infectious.case_fatality: a parameter without a source must be illustrative" in problems


def test_validator_catches_orphan_references(bundle: dict[str, Any]) -> None:
    bad = broken(bundle)
    bad["cards"][0]["concepts"] = ["no_such_concept"]
    bad["cards"][1]["effects"] = [{"op": "add_state", "key": "no.such_key", "amount": 1}]
    bad["cards"][2]["effects"] = [{"op": "handler", "name": "no_such_handler"}]
    bad["concepts"][0]["competency"] = "comp.none"
    bad["concepts"][1]["parameters"] = ["no.such.parameter"]
    problems = "\n".join(validate(bad))
    for expected in ("unknown concept 'no_such_concept'", "unknown state key 'no.such_key'",
                     "unknown handler 'no_such_handler'", "unknown competency 'comp.none'",
                     "unknown parameter 'no.such.parameter'"):
        assert expected in problems


def test_validator_rejects_invented_competency_codes(bundle: dict[str, Any]) -> None:
    bad = broken(bundle)
    bad["competencies"][0]["code"] = "XX 1.1"
    assert any("unverified entries keep code" in problem for problem in validate(bad))

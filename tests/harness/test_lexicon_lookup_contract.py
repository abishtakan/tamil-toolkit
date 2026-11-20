"""Review identities retain their recorded meaning in public lookup responses."""

import json

import pytest
from jsonschema import Draft202012Validator

from tools.lexicon import ROOT


def acceptance_validator():
    schema = json.loads((ROOT / "specs/021-lexicon-curation/contracts/lookup-response.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator({"$ref": "#/$defs/Acceptance", "$defs": schema["$defs"]})


@pytest.mark.parametrize("kind,actor,method", [
    ("accepted_human", "human.reviewer", None),
    ("accepted_auto_source", None, "source-check:v1"),
])
def test_lookup_acceptance_preserves_real_review_identity(kind, actor, method):
    acceptance_validator().validate({"decision_id": "dec_review:1", "kind": kind,
        "actor_id": actor, "method": method, "decided_on": "2026-11-14"})


@pytest.mark.parametrize("kind,actor,method", [
    ("accepted_human", None, None),
    ("accepted_human", "", None),
    ("accepted_auto_source", None, ""),
])
def test_lookup_acceptance_rejects_missing_human_or_automatic_method(kind, actor, method):
    value = {"decision_id": "dec_review", "kind": kind,
        "actor_id": actor, "method": method, "decided_on": "2026-11-14"}
    assert list(acceptance_validator().iter_errors(value))

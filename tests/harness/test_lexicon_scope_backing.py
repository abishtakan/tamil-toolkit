"""Backing references must remain valid even for unknown and inapplicable scopes."""
import pytest
from tests.harness.test_lexicon_curation import _make_valid_tables
from tools.lexicon_tables import validate_relations

@pytest.mark.parametrize("state", ["unknown", "not_applicable"])
@pytest.mark.parametrize("mutation", ["decision_only", "assertion_only", "wrong_owner", "wrong_property"])
def test_optional_scope_backing_is_complete_and_owned(state, mutation):
    tables = _make_valid_tables()
    scope = tables["scopes"][-1]
    scope.update(state=state, supporting_assertion_id="asr_scope_1", decision_id="dec_scope_1")
    if mutation == "decision_only":
        scope["supporting_assertion_id"] = None
    elif mutation == "assertion_only":
        scope["decision_id"] = None
    elif mutation == "wrong_owner":
        scope["subject_id"] = "ent_2"
        scope["dimension"] = "region"
    # asr_scope_1 supports region, while this row is register.
    findings = validate_relations(tables)
    expected = {
        "decision_only": "partial_scope_backing",
        "assertion_only": "partial_scope_backing",
        "wrong_owner": "scope_assertion_owner_mismatch",
        "wrong_property": "scope_assertion_property_mismatch",
    }[mutation]
    assert any(f["code"] == expected for f in findings), findings

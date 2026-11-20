"""Identity stability, homograph separation, and repeat-import tests (Feature 021 T011)."""

from __future__ import annotations

import uuid

import pytest

import tools.lexicon as lexicon
from tools.lexicon import LexiconError, allocate_id

DATASET_NS = uuid.UUID("bb042cb4-42a5-5d01-b301-8dbff142452a")


def test_allocate_id_is_typed_deterministic_and_independent_of_mutable_attributes():
    # Allocation key encodes source lineage and legacy identity only, not spelling/POS/row order.
    id_v1 = allocate_id("ent", DATASET_NS, "tamil-lexicon:legacy:L001")
    id_v2 = allocate_id("ent", str(DATASET_NS), "tamil-lexicon:legacy:L001")
    assert id_v1 == id_v2
    assert id_v1.startswith("ent_")
    uuid_part = id_v1.split("_", 1)[1]
    assert uuid.UUID(uuid_part).version == 5


def test_allocate_id_keeps_homographs_with_same_spelling_and_pos_distinct():
    first = allocate_id("ent", DATASET_NS, "tamil-lexicon:legacy:L001")
    second = allocate_id("ent", DATASET_NS, "tamil-lexicon:legacy:L002")
    assert first != second


@pytest.mark.parametrize(
    "kind,ns,key",
    [
        ("", DATASET_NS, "k"),
        ("bad-kind!", DATASET_NS, "k"),
        ("\u0b85", DATASET_NS, "k"),
        ("ent", "not-a-uuid", "k"),
    ],
)
def test_allocate_id_rejects_invalid_kind_or_namespace(kind, ns, key):
    with pytest.raises(LexiconError):
        allocate_id(kind, ns, key)


def test_repeat_stage_preserves_identities_and_rejects_allocation_conflicts(tmp_path):
    import csv
    from tools.lexicon_tables import read_rows

    source = tmp_path / "source"
    source.mkdir()
    (source / "primary_lemmas.csv").write_text("word_id,headword_ta,part_of_speech\n1,same,NOUN\n2,same,NOUN\n", encoding="utf-8")
    (source / "unified_master_30col.csv").write_text("word_id,headword_ta,extra\n1,same,keep-me\n2,same,also-keep\n", encoding="utf-8")
    (source / "derived.fst").write_bytes(b"not-an-authoritative-index")
    inv, workspace = tmp_path / "inventory", tmp_path / "editorial"
    lexicon.inventory(source, inv)
    first = lexicon.stage(inv, workspace)
    before = {p.name: p.read_bytes() for p in workspace.iterdir()}
    assert lexicon.stage(inv, workspace) == first
    assert before == {p.name: p.read_bytes() for p in workspace.iterdir()}
    identities = list(read_rows(workspace / "identities.csv"))
    assert len(identities) == 2  # same spelling and POS retain separate legacy IDs
    assert len(list(read_rows(workspace / "source_records.csv"))) == 4
    claims = list(read_rows(workspace / "assertions.csv"))
    assert len(claims) == 4
    assert sum(c["property_code"] == "imported_master_fields" for c in claims) == 2
    assert any("keep-me" in c["value_json"] for c in claims)
    assert first["eligible_assertions"] == 0
    assert first["file_dispositions"][0]["disposition"] == "quarantined"
    path = workspace / "identities.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    rows[1][0] = "ent_00000000-0000-5000-8000-000000000000"
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)
    conflict_before = {p.name: p.read_bytes() for p in workspace.iterdir()}
    with pytest.raises(LexiconError, match="allocation conflict"):
        lexicon.stage(inv, workspace)
    assert conflict_before == {p.name: p.read_bytes() for p in workspace.iterdir()}


def test_repeat_stage_merges_evidence_by_full_five_tuple_and_serialized_locator_order(tmp_path):
    from tools.lexicon_tables import read_rows, write_rows

    source = tmp_path / "source"
    source.mkdir()
    (source / "primary_lemmas.csv").write_text("word_id,headword_ta,part_of_speech\n1,\u0b85\u0bae\u0bcd\u0bae\u0bbe,NOUN\n", encoding="utf-8")
    inv, workspace = tmp_path / "inventory", tmp_path / "editorial"
    lexicon.inventory(source, inv)
    lexicon.stage(inv, workspace)

    ev_rows = list(read_rows(workspace / "evidence.csv"))
    assert len(ev_rows) == 1
    base = ev_rows[0]
    # Include a distinct evidence_role on the same 4-key AND locators whose decoded order
    # differs from serialized CSV order ('\t' < ' ' decoded, but '"\\t...' > '" ...' serialized).
    supports_row = dict(base, evidence_role="supports")
    tab_loc = dict(base, locator_json="\t" + base["locator_json"], evidence_role="supports")
    space_loc = dict(base, locator_json=" " + base["locator_json"], evidence_role="supports")
    zwj_loc = dict(base, locator_json=chr(0x200D) + base["locator_json"], evidence_role="supports")
    tamil_loc = dict(base, locator_json="\u0b85" + base["locator_json"], evidence_role="supports")
    write_rows(
        workspace / "evidence.csv",
        "evidence",
        [base, supports_row, tab_loc, space_loc, zwj_loc, tamil_loc],
        source_root=source,
    )

    lexicon.stage(inv, workspace)
    after = list(read_rows(workspace / "evidence.csv"))
    assert len(after) == 6
    assert {r["evidence_role"] for r in after if r["locator_json"] == base["locator_json"]} == {"transcribes", "supports"}

    # Conflicting extraction_sha256 on the exact same 5-tuple must still be fatal.
    conflicting = [
        dict(r, extraction_sha256="f" * 64) if r == base else r
        for r in after
    ]
    write_rows(workspace / "evidence.csv", "evidence", conflicting, source_root=source)
    with pytest.raises(LexiconError, match="conflicts"):
        lexicon.stage(inv, workspace)

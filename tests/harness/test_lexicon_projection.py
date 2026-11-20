"""Projection is a pending editorial proposal, never a source approval."""

from tools.lexicon import inventory, stage


def test_projection_keeps_homographs_and_unsplit_source_components(tmp_path):
    from tools.lexicon_curate import project
    from tools.lexicon_tables import read_rows
    source = tmp_path / "source"
    source.mkdir()
    (source / "primary_lemmas.csv").write_text("word_id,headword_ta,part_of_speech\n1,same,NOUN\n2,same,NOUN\n", encoding="utf-8")
    (source / "primary_meanings.csv").write_text('meaning_id,word_id,meaning_en,meaning_ta\n1,1,"1. first; 2. second",\n2,2,other,\n', encoding="utf-8")
    inv, workspace = tmp_path / "inventory", tmp_path / "editorial"
    inventory(source, inv)
    stage(inv, workspace)
    records = {r["record_id"] for r in read_rows(workspace / "source_records.csv")}
    result = project(workspace, records, source=source)
    assert result["eligible_assertions"] == 0
    assert len(list(read_rows(workspace / "entries.csv"))) == 2
    assert len(list(read_rows(workspace / "senses.csv"))) == 2
    texts = list(read_rows(workspace / "texts.csv"))
    assert len(texts) == 2
    assert all(t["component"] == "unparsed" for t in texts)
    claims = list(read_rows(workspace / "assertions.csv"))
    assert any(c["value_json"] == "1. first; 2. second" for c in claims)
    assert not list(read_rows(workspace / "decisions.csv"))
    before = {p.name: p.read_bytes() for p in workspace.glob("*.csv")}
    assert project(workspace, records, source=source) == result
    assert before == {p.name: p.read_bytes() for p in workspace.glob("*.csv")}
    stage(inv, workspace)
    assert before == {p.name: p.read_bytes() for p in workspace.glob("*.csv")}


def test_project_rejects_source_overlap_before_writes(tmp_path):
    import pytest
    from tools.lexicon import LexiconError
    from tools.lexicon_curate import project

    source = tmp_path / "source"
    source.mkdir()
    (source / "primary_lemmas.csv").write_text("word_id,headword_ta,part_of_speech\n1,\u0b85\u0bae\u0bcd\u0bae\u0bbe,NOUN\n", encoding="utf-8")
    before = {p.name: p.read_bytes() for p in source.iterdir()}

    with pytest.raises(LexiconError, match="overlaps"):
        project(source, set(), source=source)
    with pytest.raises(LexiconError, match="overlaps"):
        project(source / "nested", set(), source=source)
    assert before == {p.name: p.read_bytes() for p in source.iterdir()}


def test_project_uses_dataset_id_namespace_while_keeping_source_record_global_namespace(tmp_path):
    import uuid
    from tools.lexicon import NAMESPACE, allocate_id, digest
    from tools.lexicon_curate import project
    from tools.lexicon_tables import read_rows

    custom_ns = str(uuid.uuid5(uuid.NAMESPACE_URL, "https://example.invalid/custom-lexicon-ns"))
    source = tmp_path / "source"
    source.mkdir()
    lemma_path = source / "primary_lemmas.csv"
    lemma_path.write_text("word_id,headword_ta,part_of_speech\n1,\u0b85\u0bae\u0bcd\u0bae\u0bbe,NOUN\n", encoding="utf-8")
    inv, workspace = tmp_path / "inventory", tmp_path / "editorial"
    workspace.mkdir()
    (workspace / "dataset.toml").write_text(
        f'schema_version = 1\ntext_codec = "json-string-utf8-v1"\nid_namespace = "{custom_ns}"\n',
        encoding="ascii",
    )
    inventory(source, inv)
    stage(inv, workspace)

    src_recs = list(read_rows(workspace / "source_records.csv"))
    assert len(src_recs) == 1
    rec_id = src_recs[0]["record_id"]
    assert rec_id.startswith("rec_")
    assert allocate_id("rec", NAMESPACE, f"{digest(lemma_path)}:2:{src_recs[0]['raw_row_sha256']}") == rec_id

    result = project(workspace, {rec_id}, source=source)
    assert result["entries"] == 1
    entries = list(read_rows(workspace / "entries.csv"))
    assert entries[0]["entry_id"] == allocate_id("ent", custom_ns, "primary:word:1")
    assertions = list(read_rows(workspace / "assertions.csv"))
    assert any(a["assertion_id"] == allocate_id("ast", custom_ns, f"{rec_id}:field:headword") for a in assertions)


def test_project_preserves_distinct_evidence_roles_and_locators(tmp_path):
    import pytest
    from tools.lexicon import LexiconError
    from tools.lexicon_curate import project
    from tools.lexicon_tables import read_rows, write_rows

    source = tmp_path / "source"
    source.mkdir()
    (source / "primary_lemmas.csv").write_text("word_id,headword_ta,part_of_speech\n1,\u0b85\u0bae\u0bcd\u0bae\u0bbe,NOUN\n", encoding="utf-8")
    inv, workspace = tmp_path / "inventory", tmp_path / "editorial"
    inventory(source, inv)
    stage(inv, workspace)
    records = {r["record_id"] for r in read_rows(workspace / "source_records.csv")}
    project(workspace, records, source=source)

    ev_rows = list(read_rows(workspace / "evidence.csv"))
    hw_ev = next(e for e in ev_rows if e["locator_json"].endswith(":field=headword"))
    supports_ev = dict(hw_ev, evidence_role="supports")
    alt_loc_ev = dict(hw_ev, locator_json=hw_ev["locator_json"] + "#alt")
    write_rows(workspace / "evidence.csv", "evidence", [*ev_rows, supports_ev, alt_loc_ev], source_root=source)

    # Re-projecting must preserve distinct roles and locators on the same assertion/source_record.
    project(workspace, records, source=source)
    after = list(read_rows(workspace / "evidence.csv"))
    assert len(after) == len(ev_rows) + 2
    assert any(e["assertion_id"] == hw_ev["assertion_id"] and e["evidence_role"] == "supports" for e in after)
    assert any(e["assertion_id"] == hw_ev["assertion_id"] and e["locator_json"] == alt_loc_ev["locator_json"] for e in after)

    # Conflicting metadata on the exact same 5-tuple must still fail.
    bad = [
        dict(e, extraction_version="conflicting-v2") if e == hw_ev else e
        for e in after
    ]
    write_rows(workspace / "evidence.csv", "evidence", bad, source_root=source)
    with pytest.raises(LexiconError, match="conflicts"):
        project(workspace, records, source=source)

"""Canonical unions must preserve accepted claims and reject identity conflicts."""

import shutil

import pytest

from tools.lexicon_merge import ROOT, copy_notices, merge_packs, merge_rows


def test_merge_rows_rejects_conflicting_identity_and_scope():
    with pytest.raises(ValueError, match="conflicting"):
        merge_rows("entries", [[{"entry_id": "ent_x", "revision": "a"}], [{"entry_id": "ent_x", "revision": "b"}]])
    with pytest.raises(ValueError, match="conflicting"):
        merge_rows("scopes", [[{"subject_kind": "entry", "subject_id": "ent_x", "dimension": "region", "label_code": None, "state": "unknown"}], [{"subject_kind": "entry", "subject_id": "ent_x", "dimension": "region", "label_code": None, "state": "unrestricted"}]])


def test_label_evidence_retains_existing_definition_but_rejects_semantic_change():
    original = {"registry_id": "r", "registry_version": "1", "code": "TN", "category": "region", "parent_code": None, "display_label_json": "Tamil Nadu", "definition_json": "original", "evidence_reference": "ast_original"}
    later = dict(original, definition_json="new capture", evidence_reference="ast_new")
    assert merge_rows("labels", [[original], [later]]) == [original]
    with pytest.raises(ValueError, match="conflicting"):
        merge_rows("labels", [[original], [dict(later, parent_code="SL")]])


def test_register_alias_uses_existing_finite_source_mapping_only():
    original = {"registry_id": "enwiktionary-ta-qualifiers", "registry_version": "1", "code": "informal", "category": "register", "parent_code": None, "display_label_json": "informal", "definition_json": "original", "evidence_reference": "ast_original"}
    assert merge_rows("labels", [[original], [dict(original, display_label_json="casual")]]) == [original]
    with pytest.raises(ValueError, match="conflicting"):
        merge_rows("labels", [[original], [dict(original, display_label_json="formal")]])


def test_small_canonical_merge_is_idempotent_and_preserves_inputs(small_core_canonical, tmp_path):
    before = {p.relative_to(small_core_canonical): p.read_bytes() for p in small_core_canonical.rglob("*") if p.is_file()}
    report = merge_packs([small_core_canonical, small_core_canonical], tmp_path / "merge", pack="core", support_workspaces=[ROOT / "data/curation/wiktionary-core-reviewed"])
    assert report["entry_count"] == report["preserved_base_entries"] == 6
    assert report["added_entries"] == 0
    assert report["base_entry_revisions_preserved"] is True
    terms = (tmp_path / "merge/canonical/ATTRIBUTION_AND_TERMS.md").read_text(encoding="utf-8")
    assert "28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5" in terms
    assert before == {p.relative_to(small_core_canonical): p.read_bytes() for p in small_core_canonical.rglob("*") if p.is_file()}


def test_merge_refuses_tampered_pack_before_writing(small_core_canonical, tmp_path):
    incoming = tmp_path / "tampered"
    shutil.copytree(small_core_canonical, incoming)
    with (incoming / "assertions.csv").open("ab") as handle:
        handle.write(b"\n")
    with pytest.raises(ValueError, match="invalid canonical"):
        merge_packs([small_core_canonical, incoming], tmp_path / "merge", pack="core")
    assert not (tmp_path / "merge").exists()


def test_merge_never_discards_unresolved_private_evidence(small_core_canonical, tmp_path):
    with pytest.raises(ValueError, match="Missing private source-record support"):
        merge_packs([small_core_canonical, small_core_canonical], tmp_path / "merge")
    assert not (tmp_path / "merge").exists()


def test_attribution_blocks_survive_without_expanding_release_file_layout(tmp_path):
    original = tmp_path / "original"
    added = tmp_path / "added"
    target = tmp_path / "target"
    original.mkdir(); added.mkdir()
    (original / "ATTRIBUTION_AND_LICENSE.md").write_bytes(b"Original contributors\n")
    (added / "ATTRIBUTION_AND_LICENSE.md").write_bytes(b"Additional contributors\n")
    copy_notices(original, target)
    refs = copy_notices(added, target)
    first = (target / "ATTRIBUTION_AND_LICENSE.md").read_bytes()
    assert first.startswith(b"Original contributors\n")
    assert first.endswith(b"Additional contributors\n")
    copy_notices(added, target)
    assert (target / "ATTRIBUTION_AND_LICENSE.md").read_bytes() == first
    assert refs == {"notices/ATTRIBUTION_AND_LICENSE.md": "notices/ATTRIBUTION_AND_LICENSE.md"}
    assert len(list(target.iterdir())) == 1


def test_space_separated_license_basis_preserves_pinned_legal_checksum(tmp_path):
    import hashlib
    from tools.lexicon_packs import promote
    from tools.lexicon_tables import read_rows, write_rows
    from tools.lexicon_wiktionary_bulk import _build_bulk_pack_workspace, parse_wiktionary_page
    text = "==Tamil==\n===Noun===\n# mother\n"
    page = {"pageid": 1, "revid": 2, "title": "\u0b85\u0bae\u0bcd\u0bae\u0bbe", "wikitext": text, "revision_timestamp": "2026-11-16T00:00:00Z", "wikitext_sha256": hashlib.sha256(text.encode()).hexdigest(), "permalink_url": "https://en.wiktionary.org/w/index.php?oldid=2", "history_url": "https://en.wiktionary.org/w/index.php?action=history"}
    candidate = parse_wiktionary_page(page)["entries"][0]
    workspace = tmp_path / "workspace"
    _build_bulk_pack_workspace("core", [(page["title"], candidate)], manifest={"pages_jsonl_gz_sha256": "a" * 64}, workspace_dir=workspace, legalcode_src=ROOT / "data/curation/wiktionary-core-reviewed/notices/cc_by_sa_4_0_legalcode.txt")
    sources = list(read_rows(workspace / "sources.csv", "sources"))
    for source in sources:
        source["reuse_basis_json"] = "CC BY-SA 4.0; attribution and ShareAlike required"
    write_rows(workspace / "sources.csv", "sources", sources)
    canonical = tmp_path / "canonical"
    promote(workspace, output=canonical)
    merge_packs([canonical, canonical], tmp_path / "merged", support_workspaces=[ROOT / "data/curation/wiktionary-core-reviewed"])
    assert "28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5" in (tmp_path / "merged/canonical/ATTRIBUTION_AND_TERMS.md").read_text(encoding="utf-8")

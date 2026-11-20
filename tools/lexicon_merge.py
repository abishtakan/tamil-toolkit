"""Merge validated canonical additions into a new staging pack, preserving base IDs.

This is host data bookkeeping. It neither approves historical claims nor changes
linguistic behavior, and never overwrites any input canonical directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tomllib

from tools.audit_lexicon_readiness import ROOT
from tools.lexicon_packs import CANONICAL_CSV_TABLES, _render_vocabularies_toml, _source_requires_cc_by_sa_4, promote, validate_canonical_dir
from tools.lexicon_tables import PRIMARY_ID_COLS, read_rows, write_rows


COMPOSITE_KEYS = {
    "labels": ("registry_id", "registry_version", "code"),
    "scopes": ("subject_kind", "subject_id", "dimension", "label_code"),
    "evidence": ("assertion_id", "source_id", "source_record_id", "locator_json", "evidence_role"),
    "pack_members": ("pack_id", "entry_id"),
    "unicode_exceptions": ("assertion_id", "kind", "scalar_position", "value_sha256"),
    "identities": ("entity_id",),
}


def merge_rows(table: str, groups: list[list[dict]]) -> list[dict]:
    keys = COMPOSITE_KEYS.get(table)
    if keys is None:
        keys = (PRIMARY_ID_COLS[table],)
    merged = {}
    for group in groups:
        for row in group:
            key = tuple(row[k] for k in keys)
            existing = merged.get(key)
            if existing is not None and row != existing:
                if table == "labels" and compatible_label(row, existing):
                    # The existing registry definition remains authoritative.
                    # Incoming scope assertions retain their independent evidence.
                    continue
                raise ValueError(f"conflicting {table} identity: {key!r}")
            merged[key] = dict(row)
    return sorted(merged.values(), key=lambda row: json.dumps(row, ensure_ascii=True, sort_keys=True))


def compatible_label(incoming: dict, existing: dict) -> bool:
    if any(incoming[k] != existing[k] for k in ("category", "parent_code")):
        return False
    if incoming["display_label_json"] == existing["display_label_json"]:
        return True
    if incoming["registry_id"] == "enwiktionary-ta-qualifiers" and incoming["registry_version"] == "1" and incoming["category"] == "register":
        from tools.lexicon_wiktionary_bulk import REGISTER_LABEL_MAP
        return all(REGISTER_LABEL_MAP.get(row["display_label_json"].strip().lower()) == row["code"] for row in (incoming, existing))
    return False


def merge_vocabularies(vocabs: list[dict]) -> dict:
    result = {}
    for vocab in vocabs:
        for field, value in vocab.items():
            if field not in result:
                result[field] = value.copy() if isinstance(value, list) else value
            elif field == "regions":
                existing = {r["code"]: r for r in result[field]}
                for region in value:
                    if region["code"] in existing and region != existing[region["code"]]:
                        raise ValueError("conflicting finite region hierarchy")
                    existing[region["code"]] = region
                result[field] = [existing[key] for key in sorted(existing)]
            elif isinstance(value, list) and all(isinstance(v, str) for v in value):
                result[field] = sorted(set(result[field]) | set(value))
            elif result[field] != value:
                raise ValueError(f"conflicting vocabulary field {field}")
    return result


def copy_notices(source: Path, destination: Path) -> dict[str, str]:
    """Preserve complete attribution blocks within the approved notice layout."""
    rewrites = {}
    destination.mkdir(parents=True, exist_ok=True)
    for original in sorted(source.iterdir()):
        if not original.is_file() or original.suffix != ".md":
            raise ValueError("Canonical notices must be Markdown files")
        content = original.read_bytes()
        target = destination / original.name
        if target.exists() and target.read_bytes() != content:
            if original.name == "ATTRIBUTION_AND_LICENSE.md":
                marker = ("\n\n---\n\n## Additional source capture " + hashlib.sha256(content).hexdigest() + "\n\n").encode("ascii")
                existing = target.read_bytes()
                if marker not in existing:
                    target.write_bytes(existing + marker + content)
                rewrites["notices/" + original.name] = "notices/" + original.name
                continue
            if original.name == "CC-BY-SA-4.0.md":
                raise ValueError("conflicting canonical legal-code notices")
            target = destination / (hashlib.sha256(content).hexdigest()[:16] + "-" + original.name)
        if target.exists():
            if target.read_bytes() != content:
                raise ValueError("Notice digest-name collision")
        else:
            target.write_bytes(content)
        rewrites["notices/" + original.name] = "notices/" + target.name
    return rewrites


def merge_packs(inputs: list[Path], output: Path, *, pack="core", support_workspaces=()) -> dict:
    if len(inputs) < 2:
        raise ValueError("At least base and addition canonical packs are required")
    paths = [path.resolve() for path in inputs]
    output = output.resolve()
    for path in paths:
        if output.is_relative_to(path) or path.is_relative_to(output):
            raise ValueError("Merge output overlaps an input canonical pack")
        findings = validate_canonical_dir(path)
        if findings:
            raise ValueError(f"invalid canonical input {path}: {findings}")
        manifest = tomllib.loads((path / "packs.toml").read_text(encoding="utf-8"))
        if manifest["pack_id"] != pack:
            raise ValueError("Canonical input pack IDs must match the requested merge")
    if output.exists():
        raise ValueError("Merge output already exists; choose a fresh staging directory")
    for protected in (ROOT / "data", ROOT / "lexicon", ROOT / "crates"):
        if output.is_relative_to(protected.resolve()):
            raise ValueError("Merge output must not overwrite source, curation or runtime inputs")

    groups = {table: [] for table in CANONICAL_CSV_TABLES}
    vocabs = []
    base_manifest = tomllib.loads((paths[0] / "packs.toml").read_text(encoding="utf-8"))
    for path in paths:
        for table in groups:
            groups[table].append(list(read_rows(path / f"{table}.csv", table)))
        vocabs.append(tomllib.loads((path / "vocabularies.toml").read_text(encoding="utf-8")))
    # Validate identity/vocabulary unions before producing any merge output.
    for table, table_groups in groups.items():
        merge_rows(table, table_groups)
    vocab = merge_vocabularies(vocabs)
    # Canonical archives retain private record/snapshot references but omit the
    # private tables. Resolve them from supplied original workspaces; never drop
    # those references or invent surrogate records to make validation pass.
    records_by_id = {}
    snapshots_by_id = {}
    for support in support_workspaces:
        for table, key, index in (("source_records", "record_id", records_by_id), ("snapshots", "snapshot_id", snapshots_by_id)):
            for row in read_rows(Path(support) / f"{table}.csv", table):
                if row[key] in index and index[row[key]] != row:
                    raise ValueError(f"conflicting private {table} support")
                index[row[key]] = row
    required_records = {row["source_record_id"] for group in groups["evidence"] for row in group if row["source_record_id"]}
    if required_records - records_by_id.keys():
        raise ValueError("Missing private source-record support; provide the original curation workspace")
    selected_records = [records_by_id[key] for key in sorted(required_records)]
    required_snapshots = {row["snapshot_id"] for group in groups["sources"] for row in group if row["snapshot_id"]}
    required_snapshots.update(row["snapshot_id"] for row in selected_records)
    if required_snapshots - snapshots_by_id.keys():
        raise ValueError("Missing private snapshot support; provide the original curation workspace")
    legal_files = [Path(support) / "notices/cc_by_sa_4_0_legalcode.txt" for support in support_workspaces]
    legal_files = [path for path in legal_files if path.is_file()]
    needs_cc = any(_source_requires_cc_by_sa_4(row) for group in groups["sources"] for row in group)
    if needs_cc:
        if not legal_files:
            raise ValueError("Missing pinned source legal text; supply the original curation workspace")
        legal_bytes = legal_files[0].read_bytes()
        if any(path.read_bytes() != legal_bytes for path in legal_files):
            raise ValueError("conflicting source legal text")
        legal_sha = hashlib.sha256(legal_bytes).hexdigest()
        for i, path in enumerate(paths):
            if not any(_source_requires_cc_by_sa_4(row) for row in groups["sources"][i]):
                continue
            if legal_sha not in (path / "notices/CC-BY-SA-4.0.md").read_text(encoding="utf-8"):
                raise ValueError("Pinned legal-text digest differs from input canonical legal notice")
    workspace = output / "workspace"
    workspace.mkdir(parents=True)
    for i, path in enumerate(paths):
        rewrites = copy_notices(path / "notices", workspace / "notices")
        for source in groups["sources"][i]:
            reference = source["attribution_reference_json"]
            if isinstance(reference, str) and reference in rewrites:
                source["attribution_reference_json"] = rewrites[reference]
    if needs_cc:
        (workspace / "notices/cc_by_sa_4_0_legalcode.txt").write_bytes(legal_bytes)
    merged_tables = {table: merge_rows(table, table_groups) for table, table_groups in groups.items()}
    for table, records in merged_tables.items():
        write_rows(workspace / f"{table}.csv", table, records)
    write_rows(workspace / "findings.csv", "findings", [])
    write_rows(workspace / "source_records.csv", "source_records", selected_records)
    write_rows(workspace / "snapshots.csv", "snapshots", [snapshots_by_id[key] for key in sorted(required_snapshots)])
    (workspace / "vocabularies.toml").write_text(_render_vocabularies_toml(vocab), encoding="utf-8", newline="\n")
    canonical = output / "canonical"
    result = promote(workspace, pack=pack, output=canonical)
    merged_manifest = tomllib.loads((canonical / "packs.toml").read_text(encoding="utf-8"))
    for entry_id, revision in base_manifest["entry_revisions"].items():
        if merged_manifest["entry_revisions"].get(entry_id) != revision:
            raise ValueError(f"Base entry revision changed during merge: {entry_id}")
    # Every pre-existing row, except generated pack/revision metadata, must remain exact.
    for table in CANONICAL_CSV_TABLES:
        resulting = {json.dumps(row, ensure_ascii=True, sort_keys=True) for row in read_rows(canonical / f"{table}.csv", table)}
        for row in groups[table][0]:
            if json.dumps(row, ensure_ascii=True, sort_keys=True) not in resulting:
                raise ValueError(f"Base {table} row lost or altered")
    report = {
        "schema_version": 1, "pack": pack,
        "canonical": str(canonical), "entry_count": result["entry_count"], "sense_count": result["sense_count"],
        "preserved_base_entries": base_manifest["entry_count"],
        "added_entries": result["entry_count"] - base_manifest["entry_count"],
        "base_entry_revisions_preserved": True,
        "dataset_version": result["dataset_version"], "manifest_sha256": result["manifest_sha256"],
        "runtime_installed": False,
    }
    (output / "merge-proof.json").write_text(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pack", default="core", choices=("core", "terminology", "names_taxa", "regional"))
    parser.add_argument("--support-workspace", action="append", type=Path, default=[])
    args = parser.parse_args()
    print(json.dumps(merge_packs(args.input, args.output, pack=args.pack, support_workspaces=args.support_workspace), ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()

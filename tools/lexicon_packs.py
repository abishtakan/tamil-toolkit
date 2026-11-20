"""Feature 021 release closure validator, deterministic pack promotion, and canonical manifest APIs.

Canonical promoted pack layout (e.g. ``target/lexicon/<pack>-canonical/``):
  All files are strictly deterministic and use ONLY ``.csv``, ``.toml``, and ``.md`` extensions
  (never ``.json``, preserving repository Unicode/storage policy invariants):

  - ``packs.toml``: Pack manifest with ``schema_version = 1``, ``pack_id``, ``dataset_version``,
    ``manifest_sha256`` (SHA-256 over sorted ``[[files]]`` records), ``[entry_revisions]``,
    ``[coverage]``, ``[[omitted_relations]]``, and per-file ``[[files]]`` SHA-256 + row counts.
  - ``schema.toml``: Canonical schema metadata declaring ``json-string-utf8-v1`` CSV encoding,
    ``LookupResponse`` ID pattern ``^[A-Za-z][A-Za-z0-9_.:-]*$``, ``undirected -> symmetric``
    relation projection, nullable ``Acceptance.actor_id`` for ``accepted_auto_source``, and exact
    ordered columns for every promoted CSV table.
  - ``vocabularies.toml``: Finite versioned vocabularies (``language_ids``, ``parts_of_speech``,
    ``relation_codes``, ``annotation_properties``, ``registers``, ``domains``, ``temporals``,
    ``varieties``, ``[[regions]]``) enforced offline on all canonical rows.
  - ``ATTRIBUTION_AND_TERMS.md``: Deterministic source attribution and reuse basis summary for every
    verified source referenced by promoted evidence.
  - Canonical filtered CSVs reusing exact ``schemas/lexicon/*.schema.json`` columns:
    ``identities.csv``, ``entries.csv``, ``forms.csv``, ``senses.csv``, ``texts.csv``,
    ``relations.csv``, ``assertions.csv``, ``evidence.csv``, ``decisions.csv`` (sanitized with
    ``note_json=""`` and ``predecessor_decision_id=None``), ``sources.csv``, ``scopes.csv``,
    ``labels.csv``, ``unicode_exceptions.csv``, ``pack_members.csv``.

Stable downstream integration APIs (e.g. CLDF exporter & lookup runtime builders):
  - ``validate_release(workspace, pack="core", output=None)`` -> L3 release closure report dict
  - ``promote(workspace, pack="core", output=None, report_output=None)`` -> deterministic promotion
  - ``validate_canonical_dir(canonical_dir)`` -> list of offline canonical integrity finding strings
  - ``load_canonical_pack(canonical_dir)`` -> parsed manifest, vocabularies, schema, and decoded CSV tables
  - ``build_lookup_entry_projection(canonical_dir_or_loaded, entry_id)`` -> ``LookupResponse`` Entry object
"""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tomllib

from tools.lexicon import LexiconError, ROOT, SOURCE, atomic_json, digest, json_text, native_audit_batch, native_inspect

_ORIG_NATIVE_INSPECT = native_inspect

ALLOWED_CANONICAL_SUFFIXES = frozenset({".csv", ".toml", ".md"})
PRIVATE_NOTICE_RE = re.compile(r"\b(?:fetch_manifest|[A-Za-z0-9_.-]+_api)\.json\b", re.IGNORECASE)
PRIVATE_PATH_LEAK_RE = re.compile(
    r"(?:data[\\/](?:curation|sources)|/tmp/|\b[A-Za-z0-9_.-]+\.jsonl\b)",
    re.IGNORECASE,
)
WINDOWS_PATH_RE = re.compile(r"(?:(?<![A-Za-z0-9+.-])[A-Za-z]:(?:\\|/)|\\\\[A-Za-z0-9_.-]+\\)")
CC_BY_SA_URL = "https://creativecommons.org/licenses/by-sa/4.0/legalcode"
URL_REF_RE = re.compile(r"^(?:https?://|mailto:|urn:)", re.IGNORECASE)
FILE_LIKE_SUFFIXES = frozenset({".md", ".txt", ".toml", ".csv", ".json", ".rst", ".html", ".htm"})

PACK_IDS = frozenset({"core", "terminology", "names_taxa", "regional"})
RELATION_POLICIES = frozenset({"omit_cross_pack", "evidence_only_external", "require_same_pack", "strict"})
OMITTING_POLICIES = frozenset({"omit_cross_pack", "evidence_only_external"})
PRIMARY_TEXT_COMPONENTS = frozenset({"definition", "gloss", "translation", "citation"})
ALLOWED_TEXT_COMPONENTS = PRIMARY_TEXT_COMPONENTS | frozenset({"example"})
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
DEFAULT_CANONICAL_ROOT = ROOT / "target/lexicon"
PACK_DESCRIPTIONS = {
    "core": "Core Tamil lexicon pack",
    "terminology": "Domain terminology lexicon pack",
    "names_taxa": "Proper names and taxa lexicon pack",
    "regional": "Pluricentric regional variety lexicon pack",
}
CANONICAL_CSV_TABLES = (
    "identities",
    "entries",
    "forms",
    "senses",
    "texts",
    "relations",
    "assertions",
    "evidence",
    "decisions",
    "sources",
    "scopes",
    "labels",
    "unicode_exceptions",
    "pack_members",
)
CORE_STRUCTURAL_PROPERTIES = frozenset({
    "headword",
    "part_of_speech",
    "relation_code",
    "definition",
    "gloss",
    "translation",
    "citation",
    "example",
    "region_scope",
    "register_scope",
    "domain_scope",
    "period_scope",
    "temporal_scope",
    "social_usage_scope",
    "grammar_system_scope",
    "variety_scope",
    "scope_attestation",
    "unparsed_text",
    "pronunciation_ipa",
    "transliteration",
    "orthography_convention",
})


def _scope_dim_matches_property(dim: str, prop: str | None) -> bool:
    """Return True when a claim's property_code can substantiate a scope dimension."""
    if prop == "scope_attestation":
        return True
    if dim == "period":
        return prop in {"period_scope", "temporal_scope"}
    return prop == f"{dim}_scope"


def _read_opt_csv(directory: Path, name: str) -> list[dict] | None:
    from tools.lexicon_tables import read_rows
    path = directory / f"{name}.csv"
    if not path.is_file():
        return None
    return list(read_rows(path))


def _paths_overlap(a: Path, b: Path) -> bool:
    ra, rb = a.resolve(), b.resolve()
    return ra == rb or ra.is_relative_to(rb) or rb.is_relative_to(ra)


def _check_safe_dir(target: Path, protected: list[Path], label: str) -> Path:
    resolved = Path(target).resolve()
    for base in protected:
        if _paths_overlap(resolved, base):
            raise LexiconError(f"{label} overlaps protected directory: {resolved}", code=2)
    return resolved


def _toml_str(value: str) -> str:
    return json.dumps(str(value), ensure_ascii=True)


def _toml_scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return _toml_str(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_toml_scalar(v) for v in value) + "]"
    raise LexiconError(f"unsupported TOML value type: {type(value).__name__}")


def _parse_vocabularies_toml(path: Path) -> dict:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise LexiconError(f"invalid vocabularies.toml: {exc}", code=2) from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise LexiconError("vocabularies.toml requires schema_version = 1", code=2)
    ver = data.get("vocabulary_version")
    if not isinstance(ver, str) or not ver.strip():
        raise LexiconError("vocabularies.toml requires non-empty vocabulary_version", code=2)
    for list_key in ("language_ids", "parts_of_speech", "relation_codes", "annotation_properties", "registers"):
        if list_key in data:
            vals = data[list_key]
            if not isinstance(vals, list) or not all(isinstance(v, str) and v for v in vals):
                raise LexiconError(f"vocabularies.toml {list_key} must be a list of strings", code=2)
    for opt_list in ("domains", "temporals", "varieties"):
        if opt_list in data:
            vals = data[opt_list]
            if not isinstance(vals, list) or not all(isinstance(v, str) and v for v in vals):
                raise LexiconError(f"vocabularies.toml {opt_list} must be a list of strings", code=2)
    regions = data.get("regions", [])
    if not isinstance(regions, list):
        raise LexiconError("vocabularies.toml regions must be an array of tables", code=2)
    seen_reg = set()
    parent_map = {}
    for item in regions:
        if not isinstance(item, dict) or not isinstance(item.get("code"), str) or not item["code"]:
            raise LexiconError("vocabularies.toml region entry requires non-empty code", code=2)
        code = item["code"]
        if code in seen_reg:
            raise LexiconError(f"duplicate region code in vocabularies.toml: {code}", code=2)
        seen_reg.add(code)
        if "parent_code" in item and item["parent_code"] is not None:
            if not isinstance(item["parent_code"], str) or not item["parent_code"]:
                raise LexiconError(f"invalid parent_code in vocabularies.toml for {code}", code=2)
            parent_map[code] = item["parent_code"]
    for code, parent in parent_map.items():
        if parent not in seen_reg:
            raise LexiconError(f"unknown region parent_code in vocabularies.toml: {parent}", code=2)
        visited = {code}
        cur = parent
        while cur:
            if cur in visited:
                raise LexiconError(f"cycle in vocabularies.toml regions at {cur}", code=2)
            visited.add(cur)
            cur = parent_map.get(cur)
    return data


def _check_label_hierarchy(labels: list[dict], add_finding) -> dict[tuple[str, str], dict]:
    by_key = {}
    for row in labels:
        k = (row["registry_id"], row["registry_version"], row["code"])
        if k in by_key:
            add_finding("DUPLICATE_LABEL", row["code"], "Duplicate (registry_id, registry_version, code) label")
        by_key[k] = row
    by_cat_code: dict[tuple[str, str], dict] = {}
    for row in labels:
        cat_code = (row["category"], row["code"])
        if cat_code in by_cat_code and by_cat_code[cat_code] != row:
            add_finding("DUPLICATE_LABEL_CODE", row["code"], f"Conflicting label definitions for {cat_code}")
        by_cat_code[cat_code] = row
        seen = {(row["registry_id"], row["registry_version"], row["code"])}
        parent = row.get("parent_code")
        while parent:
            pkey = (row["registry_id"], row["registry_version"], parent)
            if pkey in seen:
                add_finding("LABEL_HIERARCHY_CYCLE", row["code"], "Cycle in labels.csv parent hierarchy")
                break
            prow = by_key.get(pkey)
            if prow is None:
                add_finding("DANGLING_LABEL_PARENT", row["code"], f"Unknown label parent_code: {parent}")
                break
            if prow["category"] != row["category"]:
                add_finding("LABEL_CATEGORY_MISMATCH", row["code"], f"Parent {parent} category mismatch")
                break
            seen.add(pkey)
            parent = prow.get("parent_code")
    return by_cat_code


def _classify_attribution_ref(ref: str | None) -> tuple[str, str | None]:
    if ref is None or not str(ref).strip():
        return ("none", None)
    s = str(ref).strip()
    if URL_REF_RE.match(s):
        return ("url", s)
    if re.match(r"^file:", s, re.IGNORECASE) or re.match(r"^[A-Za-z]:", s) or s.startswith(("/", "\\")) or "\\" in s:
        return ("unsafe", s)
    suffix = Path(s).suffix.lower()
    if "/" in s or s.startswith(".") or suffix in FILE_LIKE_SUFFIXES:
        parts = PurePosixPath(s).parts
        if ".." in parts or "." in parts or not parts:
            return ("unsafe", s)
        norm = PurePosixPath(s).as_posix()
        if suffix not in {".md", ".toml"} or PRIVATE_NOTICE_RE.search(norm) or norm.endswith(".json"):
            return ("unsafe", s)
        return ("local_file", norm)
    return ("bibliographic", s)


def _check_public_text_safety(text: str, rel_path: str, subject_id: str, add_finding) -> bool:
    ok = True
    if not text.strip():
        add_finding("EMPTY_NOTICE", subject_id, f"Notice {rel_path} must not be empty")
        return False
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in text):
        add_finding("INVALID_NOTICE_UNICODE", subject_id, f"Notice {rel_path} contains lone surrogates")
        return False
    if native_inspect is not _ORIG_NATIVE_INSPECT:
        is_nfc = bool(native_inspect(text)["is_nfc"])
    else:
        audited = native_audit_batch((text,))[0]
        is_nfc = bool(audited[0]) if audited is not None else False
    if not is_nfc:
        add_finding("NON_NFC_NOTICE", subject_id, f"Notice {rel_path} must be UTF-8 NFC normalized")
        ok = False
    if WINDOWS_PATH_RE.search(text):
        add_finding("UNSAFE_NOTICE_CONTENT", subject_id, f"Notice {rel_path} exposes local Windows path")
        ok = False
    if PRIVATE_PATH_LEAK_RE.search(text):
        add_finding("UNSAFE_NOTICE_CONTENT", subject_id, f"Notice {rel_path} exposes private workspace or source path")
        ok = False
    if PRIVATE_NOTICE_RE.search(text):
        add_finding("PRIVATE_NOTICE_REFERENCE", subject_id, f"Notice {rel_path} references private editorial JSON")
        ok = False
    return ok


def _project_notice_markdown(raw_text: str, legal_meta: dict | None) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    marker = "## 3. Preserved Official Notice Files"
    if marker in text:
        head = text.split(marker, 1)[0].rstrip()
        section = [
            "",
            "## 3. Canonical Public Notice & License Files",
            "",
        ]
        if legal_meta:
            section.append(
                f"- `{legal_meta['canonical_path']}` — Creative Commons Attribution-ShareAlike 4.0 International "
                f"(`{legal_meta['uri']}`, source SHA-256 `{legal_meta['source_sha256']}`)"
            )
        section.extend([
            "- Upstream Wikimedia Terms of Use: https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use",
            "- Upstream Wiktionary Copyrights: https://en.wiktionary.org/wiki/Wiktionary:Copyrights",
        ])
        text = head + "\n" + "\n".join(section) + "\n"
    else:
        kept_lines = [
            line for line in text.splitlines()
            if not PRIVATE_NOTICE_RE.search(line) and "cc_by_sa_4_0_legalcode.txt" not in line
        ]
        text = "\n".join(kept_lines).rstrip() + "\n"
        if legal_meta and legal_meta["canonical_path"] not in text:
            text += (
                f"\n- License text: [{legal_meta['canonical_path']}]({Path(legal_meta['canonical_path']).name}) "
                f"(source SHA-256 `{legal_meta['source_sha256']}`, {legal_meta['uri']})\n"
            )
    return text


def _source_requires_cc_by_sa_4(src: dict) -> bool:
    basis = str(src.get("reuse_basis_json") or "").lower()
    return "cc-by-sa-4.0" in basis or "cc by-sa 4.0" in basis


def _collect_public_notices(
    workspace: Path,
    used_sources: list[dict],
    add_finding,
) -> tuple[dict[str, str], dict | None]:
    ws_resolved = workspace.resolve()
    notice_files: dict[str, str] = {}
    legal_meta: dict | None = None

    cc_src = None
    for candidate in ("notices/cc_by_sa_4_0_legalcode.txt", "notices/CC-BY-SA-4.0.md"):
        p = workspace / candidate
        try:
            rp = p.resolve()
        except OSError:
            continue
        if rp.is_file() and rp.is_relative_to(ws_resolved):
            cc_src = (candidate, rp)
            break

    needs_cc = any(_source_requires_cc_by_sa_4(s) for s in used_sources)
    if cc_src is not None:
        cand_rel, rp = cc_src
        src_sha = digest(rp)
        try:
            raw_cc = rp.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
        except UnicodeDecodeError as exc:
            add_finding("INVALID_NOTICE_ENCODING", cand_rel, f"License file {cand_rel} is not valid UTF-8: {exc}")
            raw_cc = ""
        if raw_cc:
            if cand_rel.endswith(".txt"):
                cc_md = (
                    "# Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)\n\n"
                    f"- Canonical License URI: {CC_BY_SA_URL}\n"
                    f"- Source Legal Text File: `{cand_rel}`\n"
                    f"- Source SHA-256: `{src_sha}`\n\n"
                    "---\n\n"
                    + raw_cc.rstrip()
                    + "\n"
                )
            else:
                cc_md = raw_cc if raw_cc.endswith("\n") else raw_cc + "\n"
            legal_meta = {
                "canonical_path": "notices/CC-BY-SA-4.0.md",
                "uri": CC_BY_SA_URL,
                "source_sha256": src_sha,
            }
            if needs_cc and ("Attribution-ShareAlike 4.0 International" not in cc_md or CC_BY_SA_URL not in cc_md):
                add_finding(
                    "MISSING_CC_LEGAL_CODE",
                    "notices/CC-BY-SA-4.0.md",
                    "notices/CC-BY-SA-4.0.md incomplete legal text or canonical URI",
                )
            elif _check_public_text_safety(cc_md, legal_meta["canonical_path"], "notices", add_finding):
                notice_files[legal_meta["canonical_path"]] = cc_md
    elif needs_cc:
        add_finding(
            "MISSING_CC_LEGAL_CODE",
            "notices/CC-BY-SA-4.0.md",
            "CC-BY-SA-4.0 source requires pinned legal text (notices/cc_by_sa_4_0_legalcode.txt or notices/CC-BY-SA-4.0.md)",
        )

    for src in used_sources:
        sid = src["source_id"]
        kind, ref_val = _classify_attribution_ref(src.get("attribution_reference_json"))
        if kind == "unsafe":
            add_finding("UNSAFE_ATTRIBUTION_REFERENCE", sid, f"Unsafe or non-canonical attribution_reference_json: {ref_val!r}")
            continue
        if kind != "local_file":
            continue
        src_path = (workspace / ref_val).resolve()
        if not src_path.is_relative_to(ws_resolved):
            add_finding("UNSAFE_ATTRIBUTION_REFERENCE", sid, f"Attribution reference escapes workspace: {ref_val!r}")
            continue
        if not src_path.is_file():
            add_finding("MISSING_SOURCE_NOTICE_FILE", sid, f"Referenced local notice file missing: {ref_val}")
            continue
        try:
            raw_notice = src_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            add_finding("INVALID_NOTICE_ENCODING", sid, f"Notice {ref_val} is not valid UTF-8: {exc}")
            continue
        if WINDOWS_PATH_RE.search(raw_notice):
            add_finding("UNSAFE_NOTICE_CONTENT", sid, f"Notice {ref_val} exposes local Windows path")
            continue
        projected = _project_notice_markdown(raw_notice, legal_meta)
        if _check_public_text_safety(projected, ref_val, sid, add_finding):
            notice_files[ref_val] = projected

    return notice_files, legal_meta


def _evaluate_workspace(workspace: Path, pack: str) -> dict:
    from tools.lexicon_review import _current_decisions, claim_revision, eligibility, unicode_findings, validate_history
    from tools.lexicon_tables import ACCEPTED_OUTCOMES, read_rows, validate_relations

    assertions = list(read_rows(workspace / "assertions.csv"))
    evidence = list(read_rows(workspace / "evidence.csv"))
    sources = list(read_rows(workspace / "sources.csv"))
    decisions = list(read_rows(workspace / "decisions.csv"))
    findings_tbl = list(read_rows(workspace / "findings.csv"))

    optional_names = (
        "snapshots", "source_records", "dispositions", "record_targets",
        "identities", "entries", "forms", "senses", "texts", "relations",
        "unicode_exceptions", "labels", "scopes", "pack_members", "changes", "successors",
    )
    opt = {name: _read_opt_csv(workspace, name) for name in optional_names}

    vocab = None
    vocab_path = workspace / "vocabularies.toml"
    if vocab_path.is_file():
        vocab = _parse_vocabularies_toml(vocab_path)

    ev_by_aid = defaultdict(list)
    for e in evidence:
        ev_by_aid[e["assertion_id"]].append(e)
    dec_by_aid = defaultdict(list)
    for d in decisions:
        dec_by_aid[d["assertion_id"]].append(d)
    has_dup_decision_id = len({d.get("decision_id") for d in decisions}) != len(decisions)
    exc_by_aid = defaultdict(list)
    for ex in (opt["unicode_exceptions"] or ()):
        exc_by_aid[ex["assertion_id"]].append(ex)

    findings_by_aid = defaultdict(list)
    findings_by_rec = defaultdict(list)
    global_findings = []
    for f in findings_tbl:
        faid = f.get("assertion_id")
        frid = f.get("record_id")
        if faid not in (None, ""):
            findings_by_aid[faid].append(f)
        elif frid not in (None, "") and f.get("scope") != "global":
            findings_by_rec[frid].append(f)
        else:
            global_findings.append(f)

    elig_by_aid = {}
    u_findings_by_aid = {}
    claims_by_aid = {}
    eligible_aids = set()
    terminal_dec_by_aid = {}
    for claim in assertions:
        aid = claim["assertion_id"]
        claims_by_aid[aid] = claim
        rel_ev = ev_by_aid.get(aid, ())
        rel_dec = decisions if has_dup_decision_id else dec_by_aid.get(aid, ())
        rel_exc = exc_by_aid.get(aid, ())
        uf = unicode_findings(claim, rel_exc, rel_dec)
        u_findings_by_aid[aid] = uf
        linked_records = {r.get("source_record_id") for r in rel_ev if r.get("source_record_id")}
        relevant_f = list(global_findings) + list(findings_by_aid.get(aid, ()))
        for rid in linked_records:
            relevant_f.extend(findings_by_rec.get(rid, ()))
        res = eligibility(claim, rel_ev, sources, rel_dec, relevant_f + uf)
        elig_by_aid[aid] = res
        if res["eligible"]:
            eligible_aids.add(aid)
        cur = _current_decisions(rel_dec)
        if len(cur) == 1:
            terminal_dec_by_aid[aid] = cur[0]

    eligible_count = len(eligible_aids)
    report_findings = []
    seen_finding_keys = set()

    def add_finding(code: str, subject_id: str, reason: str, severity: str = "error") -> None:
        key = (code, subject_id, reason, severity)
        if key not in seen_finding_keys:
            seen_finding_keys.add(key)
            report_findings.append({"code": code, "severity": severity, "subject_id": subject_id, "reason": reason})

    if eligible_count == 0:
        add_finding(
            "NONEMPTY_ELIGIBLE_PACK_REQUIRED",
            pack,
            "Positive L3 acceptance requires nonempty eligible assertions and approved pack closure.",
        )

    required_closure_tables = ("identities", "entries", "forms", "senses", "texts", "pack_members")
    missing_tables = [name for name in required_closure_tables if opt[name] is None]
    for name in missing_tables:
        add_finding("MISSING_RELEASE_TABLE", name, f"Required release closure table unavailable: {name}.csv")

    pack_members_all = opt["pack_members"] or []
    pack_members_for_pack = [r for r in pack_members_all if r["pack_id"] == pack]
    if eligible_count > 0 and opt["pack_members"] is not None and not pack_members_for_pack:
        add_finding("EMPTY_PACK_MEMBERS", pack, f"Pack {pack!r} has zero member entries")

    # Early return when core tables aren't present yet (preserves early-guard compatibility cleanly).
    if missing_tables:
        ordered = sorted(report_findings, key=lambda f: (0 if f["code"] == "NONEMPTY_ELIGIBLE_PACK_REQUIRED" else 1, json_text(f)))
        return {
            "report": {
                "schema_version": 1,
                "command": "release",
                "mode": "release",
                "pack": pack,
                "eligible_assertions": eligible_count,
                "omitted_relation_count": 0,
                "omitted_relations": [],
                "l2_structural_accepted": False,
                "l3_pack_eligible": False,
                "runtime_verified": None,
                "findings": ordered,
            }
        }

    entries = opt["entries"]
    forms = opt["forms"]
    senses = opt["senses"]
    texts = opt["texts"]
    relations = opt["relations"] or []
    identities = opt["identities"]
    labels = opt["labels"] or []
    scopes = opt["scopes"] or []
    changes = opt["changes"] or []
    successors = opt["successors"] or []

    # Check IDs conform to LookupResponse ID pattern ^[A-Za-z][A-Za-z0-9_.:-]*$.
    ident_by_id = {r["entity_id"]: r for r in identities}
    entries_by_id = {r["entry_id"]: r for r in entries}
    forms_by_id = {r["form_id"]: r for r in forms}
    senses_by_id = {r["sense_id"]: r for r in senses}
    texts_by_id = {r["text_id"]: r for r in texts}
    relations_by_id = {r["relation_id"]: r for r in relations}

    # Check structural history & relational integrity.
    for hf in validate_history(identities, changes, successors, assertions, decisions):
        add_finding("RELEASE_HISTORY_ERROR", hf.get("entity_id") or pack, f"{hf['issue_code']}: {hf['reason']}")

    rel_tables = {
        "sources": sources,
        "assertions": assertions,
        "evidence": evidence,
        "decisions": decisions,
        "findings": findings_tbl,
        "identities": identities,
        "entries": entries,
        "forms": forms,
        "senses": senses,
        "texts": texts,
        "relations": relations,
        "unicode_exceptions": opt["unicode_exceptions"] or [],
        "labels": labels,
        "scopes": scopes,
        "pack_members": pack_members_all,
        "changes": changes,
        "successors": successors,
    }
    for optional_src in ("snapshots", "source_records", "dispositions", "record_targets"):
        if opt[optional_src] is not None:
            rel_tables[optional_src] = opt[optional_src]
    for rf in validate_relations(rel_tables):
        add_finding(
            f"RELEASE_RELATION_{str(rf.get('code', 'ERROR')).upper()}",
            str(rf.get("subject_id") or pack),
            str(rf.get("reason") or "Relation validation error"),
            severity=str(rf.get("severity") or "error"),
        )

    # Label hierarchy integrity.
    labels_by_cat_code = _check_label_hierarchy(labels, add_finding)

    # Check pack_members across ALL packs for duplicates, active status, revision matches, cross-pack conflicts.
    seen_pm = set()
    rev_by_entry: dict[str, str] = {}
    pm_for_pack_by_entry: dict[str, dict] = {}
    for row in pack_members_all:
        key = (row["pack_id"], row["entry_id"])
        if key in seen_pm:
            add_finding("DUPLICATE_PACK_MEMBER", row["entry_id"], f"Duplicate pack_members row for {key}")
        seen_pm.add(key)
        eid = row["entry_id"]
        entry = entries_by_id.get(eid)
        ident = ident_by_id.get(eid)
        if entry is None:
            add_finding("UNKNOWN_PACK_ENTRY", eid, f"pack_members entry {eid} missing in entries.csv")
        else:
            if row["included_revision"] != entry["revision"]:
                add_finding("STALE_PACK_REVISION", eid, "pack_members included_revision does not match entries.revision")
        if ident is None or ident.get("kind") != "entry" or ident.get("lifecycle") != "active":
            add_finding("INACTIVE_PACK_ENTRY", eid, "pack_members entry must be an active entry identity")
        prev_rev = rev_by_entry.setdefault(eid, row["included_revision"])
        if prev_rev != row["included_revision"]:
            add_finding("CROSS_PACK_REVISION_CONFLICT", eid, "Entry has conflicting included_revision across packs")
        if row["pack_id"] == pack:
            pol = row.get("relation_inclusion_policy")
            if pol is not None and pol not in RELATION_POLICIES:
                add_finding("INVALID_RELATION_POLICY", eid, f"Unsupported relation_inclusion_policy: {pol}")
            pm_for_pack_by_entry[eid] = row

    pack_entry_ids = sorted(pm_for_pack_by_entry)
    pack_entry_set = set(pack_entry_ids)

    # Global check: any assertion claiming accepted_* must be eligible and pass claim_revision.
    for aid, dec in terminal_dec_by_aid.items():
        if dec.get("outcome") in ACCEPTED_OUTCOMES and aid not in eligible_aids:
            add_finding(
                "INELIGIBLE_ACCEPTED_CLAIM",
                aid,
                f"Assertion claims {dec['outcome']} but fails eligibility: {elig_by_aid[aid]['reasons']}",
            )
        claim = claims_by_aid.get(aid)
        if claim is not None and dec.get("outcome") in ACCEPTED_OUTCOMES and not ID_RE.match(aid):
            add_finding("INVALID_LOOKUP_ID", aid, "Assertion ID does not satisfy LookupResponse pattern")

    forms_by_entry = defaultdict(list)
    for f in forms:
        forms_by_entry[f["entry_id"]].append(f)
    senses_by_entry = defaultdict(list)
    for s in senses:
        senses_by_entry[s["entry_id"]].append(s)
    texts_by_owner = defaultdict(list)
    for t in texts:
        texts_by_owner[(t["owner_kind"], t["owner_id"])].append(t)
    assertions_by_subject = defaultdict(list)
    for c in assertions:
        assertions_by_subject[(c["subject_kind"], c["subject_id"])].append(c)
    scopes_by_subject = defaultdict(list)
    for sc in scopes:
        scopes_by_subject[(sc["subject_kind"], sc["subject_id"])].append(sc)

    vocab_langs = set(vocab.get("language_ids", ())) if vocab is not None else None
    vocab_pos = set(vocab.get("parts_of_speech", ())) if vocab is not None else None
    vocab_rels = set(vocab.get("relation_codes", ())) if vocab is not None else None
    vocab_ann = set(vocab.get("annotation_properties", ())) if vocab is not None else None
    vocab_reg_parents = (
        {r["code"]: r.get("parent_code") for r in vocab.get("regions", ())}
        if vocab is not None
        else None
    )
    vocab_regs = set(vocab_reg_parents) if vocab_reg_parents is not None else None
    vocab_registers = set(vocab.get("registers", ())) if vocab is not None else None
    vocab_domains = set(vocab.get("domains", ())) if vocab is not None else None
    vocab_periods = set(vocab.get("temporals", ())) if vocab is not None else None
    vocab_varieties = set(vocab.get("varieties", ())) if vocab is not None else None
    vocab_dims = {
        "region": vocab_regs,
        "register": vocab_registers,
        "domain": vocab_domains,
        "period": vocab_periods,
        "variety": vocab_varieties,
    }

    included_forms: list[dict] = []
    included_senses: list[dict] = []
    included_texts: list[dict] = []
    subject_owner_entry: dict[str, str] = {}

    for eid in pack_entry_ids:
        entry = entries_by_id.get(eid)
        if entry is None:
            continue
        subject_owner_entry[eid] = eid
        entry_failed = False

        if not ID_RE.match(eid) or not ID_RE.match(entry["language_id"]):
            add_finding("INVALID_LOOKUP_ID", eid, "Entry or language ID violates LookupResponse ID pattern")
            entry_failed = True
        if vocab_langs is not None and entry["language_id"] not in vocab_langs:
            add_finding("UNKNOWN_VOCABULARY_LANGUAGE", eid, f"Entry language_id {entry['language_id']!r} not in vocabularies.toml")
            entry_failed = True
        vid = entry.get("variety_id")
        if vid is not None:
            if not ID_RE.match(vid):
                add_finding("INVALID_LOOKUP_ID", eid, "Entry variety_id violates LookupResponse ID pattern")
                entry_failed = True
            if vocab_varieties is not None and vid not in vocab_varieties:
                add_finding("UNKNOWN_VOCABULARY_VARIETY", eid, f"Entry variety_id {vid!r} not in vocabularies.toml")
                entry_failed = True

        # Reject accepted/eligible entry-owned texts.
        for et in texts_by_owner.get(("entry", eid), ()):
            taid = et["text_assertion_id"]
            if taid in eligible_aids or terminal_dec_by_aid.get(taid, {}).get("outcome") in ACCEPTED_OUTCOMES:
                add_finding("ACCEPTED_ENTRY_OWNED_TEXT", et["text_id"], "Accepted entry-owned text without sense attribution is forbidden")
                entry_failed = True

        # Canonical written headword check: exactly one eligible canonical written form matching entry.canonical_form_id.
        cf_id = entry.get("canonical_form_id")
        entry_forms = forms_by_entry.get(eid, [])
        eligible_canonical_written = []
        for frm in entry_forms:
            fid = frm["form_id"]
            subject_owner_entry[fid] = eid
            taid = frm["text_assertion_id"]
            f_ident = ident_by_id.get(fid)
            caid = frm.get("convention_assertion_id")
            if taid in eligible_aids:
                if f_ident is None or f_ident.get("kind") != "form" or f_ident.get("lifecycle") != "active":
                    add_finding("INACTIVE_FORM", fid, "Eligible form lacks active form identity")
                    entry_failed = True
                if not ID_RE.match(fid):
                    add_finding("INVALID_LOOKUP_ID", fid, "Form ID violates LookupResponse ID pattern")
                if caid and caid not in eligible_aids:
                    add_finding("INELIGIBLE_CONVENTION", fid, "Eligible form requires eligible convention_assertion_id")
                    entry_failed = True
                included_forms.append(frm)
                if frm["representation"] == "written" and frm["role"] == "canonical":
                    eligible_canonical_written.append(frm)
            elif fid == cf_id:
                add_finding("INELIGIBLE_CANONICAL_FORM", eid, f"Canonical form {cf_id} headword assertion is ineligible")
                entry_failed = True

        if not cf_id:
            add_finding("MISSING_CANONICAL_FORM", eid, "Entry lacks canonical_form_id")
            entry_failed = True
        elif cf_id not in forms_by_id or forms_by_id[cf_id]["entry_id"] != eid:
            add_finding("DANGLING_CANONICAL_FORM", eid, f"Canonical form {cf_id} does not belong to entry {eid}")
            entry_failed = True
        elif len(eligible_canonical_written) != 1 or eligible_canonical_written[0]["form_id"] != cf_id:
            add_finding("INVALID_CANONICAL_FORM_SET", eid, "Entry must have exactly one eligible written canonical form")
            entry_failed = True

        # Required eligible part_of_speech.
        pos_aid = entry.get("pos_assertion_id")
        if not pos_aid:
            add_finding("MISSING_POS_ASSERTION", eid, "Entry lacks required pos_assertion_id")
            entry_failed = True
        elif pos_aid not in eligible_aids:
            add_finding("INELIGIBLE_POS_ASSERTION", eid, f"Entry POS assertion {pos_aid} is not eligible")
            entry_failed = True
        else:
            pos_claim = claims_by_aid.get(pos_aid)
            if pos_claim is None or pos_claim["subject_kind"] != "entry" or pos_claim["subject_id"] != eid or pos_claim["property_code"] != "part_of_speech":
                add_finding("INVALID_POS_ASSERTION", eid, "pos_assertion_id does not reference entry part_of_speech claim")
                entry_failed = True
            elif vocab_pos is not None and pos_claim.get("value_json") not in vocab_pos:
                add_finding("UNKNOWN_VOCABULARY_POS", eid, f"POS value {pos_claim.get('value_json')!r} not in vocabularies.toml")
                entry_failed = True

        # Senses & primary components + DAG acyclicity.
        active_senses = []
        for sen in senses_by_entry.get(eid, []):
            sid = sen["sense_id"]
            subject_owner_entry[sid] = eid
            s_ident = ident_by_id.get(sid)
            if s_ident is None or s_ident.get("kind") != "sense" or s_ident.get("lifecycle") != "active":
                add_finding("INACTIVE_SENSE", sid, "Entry sense lacks active sense identity")
                entry_failed = True
                continue
            if not ID_RE.match(sid):
                add_finding("INVALID_LOOKUP_ID", sid, "Sense ID violates LookupResponse ID pattern")
            active_senses.append(sen)

        if not active_senses:
            add_finding("MISSING_ACCEPTED_SENSE", eid, "Entry requires at least one active sense")
            entry_failed = True

        sense_map = {s["sense_id"]: s for s in active_senses}
        for sen in active_senses:
            visited = {sen["sense_id"]}
            cur = sen.get("parent_sense_id")
            while cur:
                if cur in visited:
                    add_finding("SENSE_HIERARCHY_CYCLE", sen["sense_id"], "Cycle detected in parent_sense_id chain")
                    entry_failed = True
                    break
                if cur not in sense_map:
                    add_finding("INVALID_PARENT_SENSE", sen["sense_id"], f"parent_sense_id {cur} missing or belongs to another entry")
                    entry_failed = True
                    break
                visited.add(cur)
                cur = sense_map[cur].get("parent_sense_id")

            sid = sen["sense_id"]
            primary_ok = 0
            for txt in texts_by_owner.get(("sense", sid), ()):
                tid = txt["text_id"]
                taid = txt["text_assertion_id"]
                subject_owner_entry[tid] = eid
                comp = txt["component"]
                if comp == "unparsed":
                    if taid in eligible_aids or terminal_dec_by_aid.get(taid, {}).get("outcome") in ACCEPTED_OUTCOMES:
                        add_finding("ACCEPTED_UNPARSED_TEXT", tid, "Accepted unparsed text is forbidden in canonical packs")
                        entry_failed = True
                    continue
                if taid in eligible_aids:
                    t_ident = ident_by_id.get(tid)
                    if t_ident is None or t_ident.get("kind") != "text" or t_ident.get("lifecycle") != "active":
                        add_finding("INACTIVE_TEXT", tid, "Eligible text lacks active text identity")
                        entry_failed = True
                        continue
                    if not ID_RE.match(tid) or not ID_RE.match(txt["language_id"]):
                        add_finding("INVALID_LOOKUP_ID", tid, "Text or language ID violates LookupResponse ID pattern")
                    if comp not in ALLOWED_TEXT_COMPONENTS:
                        add_finding("UNSUPPORTED_TEXT_COMPONENT", tid, f"Unsupported sense text component: {comp}")
                        entry_failed = True
                    if vocab_langs is not None and txt["language_id"] not in vocab_langs:
                        add_finding("UNKNOWN_VOCABULARY_LANGUAGE", tid, f"Text language_id {txt['language_id']!r} not in vocabularies.toml")
                        entry_failed = True
                    if txt.get("paired_translation_id"):
                        pt = texts_by_id.get(txt["paired_translation_id"])
                        if pt is None or pt["text_assertion_id"] not in eligible_aids or pt["owner_id"] != sid:
                            add_finding("INVALID_PAIRED_TRANSLATION", tid, "paired_translation_id must refer to eligible sibling text")
                            entry_failed = True
                    included_texts.append(txt)
                    if comp in PRIMARY_TEXT_COMPONENTS:
                        primary_ok += 1
            if primary_ok == 0:
                add_finding("MISSING_SENSE_DEFINITION_OR_GLOSS", sid, "Sense requires at least one eligible non-unparsed definition/gloss/translation/citation")
                entry_failed = True
            included_senses.append(sen)

        # Optional annotations cannot rescue an entry with ineligible required claims, and custom properties must match vocabularies.
        entry_subject_ids = {("entry", eid)} | {("form", f["form_id"]) for f in entry_forms} | {("sense", s["sense_id"]) for s in active_senses}
        for skind, sid in sorted(entry_subject_ids):
            for cl in assertions_by_subject.get((skind, sid), ()):
                aid = cl["assertion_id"]
                if aid not in eligible_aids:
                    continue
                prop = cl["property_code"]
                if prop not in CORE_STRUCTURAL_PROPERTIES:
                    if entry_failed:
                        add_finding("OPTIONAL_ANNOTATION_CANNOT_LICENSE_INELIGIBLE", aid, "Accepted optional annotation cannot license entry lacking eligible core claims")
                    if vocab_ann is not None and prop not in vocab_ann:
                        add_finding("UNKNOWN_VOCABULARY_ANNOTATION", aid, f"Annotation property {prop!r} not in vocabularies.toml")

    # Scopes closure & finite vocab checks for all included pack subjects.
    included_subject_kinds = {eid: "entry" for eid in pack_entry_ids}
    for f in included_forms:
        included_subject_kinds[f["form_id"]] = "form"
    for s in included_senses:
        included_subject_kinds[s["sense_id"]] = "sense"
    for t in included_texts:
        included_subject_kinds[t["text_id"]] = "text"
    included_subject_ids = set(included_subject_kinds)

    # Pre-check relations that involve included subjects.
    included_relations = []
    omitted_relations = []
    base_subject_ids = set(included_subject_ids)
    for rel in relations:
        src_in = rel["source_id"] in base_subject_ids
        tgt_in = rel["target_id"] in base_subject_ids
        if not (src_in or tgt_in):
            continue
        raid = rel["relation_code_assertion_id"]
        if raid not in eligible_aids:
            # Ineligible relation claiming accepted was already caught above; pending optional relation is excluded.
            continue
        # Basic editorial integrity always applies to pack-touching relations.
        if rel.get("source_kind") not in {"entry", "sense"} or rel.get("target_kind") not in {"entry", "sense"}:
            add_finding("INVALID_RELATION_ENDPOINT", rel["relation_id"], f"Relation {rel['relation_id']} has invalid endpoint kind")
        if src_in and included_subject_kinds.get(rel["source_id"]) != rel.get("source_kind"):
            add_finding(
                "INVALID_RELATION_ENDPOINT",
                rel["relation_id"],
                f"Relation source_kind {rel.get('source_kind')!r} mismatches subject kind for {rel['source_id']}",
            )
        if tgt_in and included_subject_kinds.get(rel["target_id"]) != rel.get("target_kind"):
            add_finding(
                "INVALID_RELATION_ENDPOINT",
                rel["relation_id"],
                f"Relation target_kind {rel.get('target_kind')!r} mismatches subject kind for {rel['target_id']}",
            )
        rclaim = claims_by_aid.get(raid)
        if rclaim is not None and (
            rclaim.get("property_code") != "relation_code"
            or rclaim.get("subject_kind") != "relation"
            or rclaim.get("subject_id") != rel["relation_id"]
        ):
            add_finding(
                "INVALID_RELATION_ASSERTION",
                rel["relation_id"],
                f"Relation assertion {raid} must have property_code='relation_code' and subject relation:{rel['relation_id']}",
            )
        # Determine selected-pack relation membership and cross-pack omission BEFORE applying
        # published LookupResponse shape / vocabulary restrictions to actually included relations.
        src_entry = subject_owner_entry.get(rel["source_id"])
        tgt_entry = subject_owner_entry.get(rel["target_id"])
        is_internal = src_in and tgt_in and src_entry in pack_entry_set and tgt_entry in pack_entry_set
        if not is_internal:
            # Cross-pack / external endpoint. Find governing policy on included pack member entry.
            inc_entry = src_entry if (src_in and src_entry in pack_entry_set) else tgt_entry
            policy = pm_for_pack_by_entry.get(inc_entry, {}).get("relation_inclusion_policy")
            if policy in OMITTING_POLICIES:
                omitted_relations.append({
                    "relation_id": rel["relation_id"],
                    "source_id": rel["source_id"],
                    "target_id": rel["target_id"],
                    "policy": policy,
                    "reason": "cross_pack_endpoint_omitted",
                })
            else:
                add_finding(
                    "CROSS_PACK_RELATION_UNRESOLVED",
                    rel["relation_id"],
                    f"Relation {rel['relation_id']} crosses pack boundary and member policy is {policy!r}",
                )
            continue
        if rel.get("source_kind") != "sense":
            add_finding(
                "UNSUPPORTED_RELATION_SOURCE_KIND",
                rel["relation_id"],
                f"Relation {rel['relation_id']} unsupported source_kind {rel.get('source_kind')!r}: LookupResponse only projects sense-anchored relations",
            )
        if vocab_rels is not None and rclaim is not None and rclaim.get("value_json") not in vocab_rels:
            add_finding("UNKNOWN_VOCABULARY_RELATION", rel["relation_id"], f"Relation code {rclaim.get('value_json')!r} not in vocabularies.toml")
        if not ID_RE.match(rel["relation_id"]):
            add_finding("INVALID_LOOKUP_ID", rel["relation_id"], "Relation ID violates LookupResponse ID pattern")
        inv_id = rel.get("inverse_relation_id")
        if inv_id:
            inv_rel = relations_by_id.get(inv_id)
            if inv_rel is None or inv_rel["relation_code_assertion_id"] not in eligible_aids or inv_rel["source_id"] not in base_subject_ids or inv_rel["target_id"] not in base_subject_ids:
                add_finding("DANGLING_INVERSE_RELATION", rel["relation_id"], "Eligible internal relation references non-promoted inverse relation")
        included_relations.append(rel)
        included_subject_ids.add(rel["relation_id"])
        included_subject_kinds[rel["relation_id"]] = "relation"

    included_scopes = []
    referenced_label_keys = set()
    for (skind, sid), sc_rows in scopes_by_subject.items():
        if sid not in included_subject_ids:
            continue
        if included_subject_kinds.get(sid) != skind:
            add_finding(
                "SCOPE_SUBJECT_KIND_MISMATCH",
                sid,
                f"Scope subject_kind {skind!r} mismatches subject kind {included_subject_kinds.get(sid)!r} for {sid}",
            )
            continue
        dim_states = defaultdict(set)
        dim_counts = defaultdict(int)
        for sc in sc_rows:
            dim = sc["dimension"]
            st = sc["state"]
            dim_states[dim].add(st)
            dim_counts[dim] += 1
            said = sc.get("supporting_assertion_id")
            did = sc.get("decision_id")
            if st == "not_applicable" and dim != "register":
                add_finding(
                    "INVALID_SCOPE_STATE",
                    sid,
                    f"Scope state 'not_applicable' is permitted only for dimension 'register', not {dim!r}",
                )
                continue
            if st != "attested" and sc.get("label_code") is not None:
                add_finding("INVALID_SCOPE_LABEL", sid, f"Scope {dim}={st} forbids label_code")
                continue
            if st in {"attested", "unrestricted"} or said or did:
                if not said or said not in eligible_aids:
                    add_finding("INELIGIBLE_SCOPE_ASSERTION", sid, f"Scope {dim}={st} requires eligible supporting_assertion_id")
                    continue
                sclaim = claims_by_aid.get(said)
                if sclaim is None or sclaim.get("subject_kind") != skind or sclaim.get("subject_id") != sid or not _scope_dim_matches_property(dim, sclaim.get("property_code")):
                    add_finding("INVALID_SCOPE_ASSERTION", sid, f"Scope assertion {said} mismatches subject or scope property for {skind}:{sid} ({dim})")
                    continue
                tdec = terminal_dec_by_aid.get(said)
                if tdec is None or tdec["decision_id"] != did:
                    add_finding("STALE_SCOPE_DECISION", sid, f"Scope decision_id {did} does not match current accepted decision for {said}")
                    continue
            if st == "attested":
                code = sc.get("label_code")
                if not code or (dim, code) not in labels_by_cat_code:
                    add_finding("UNKNOWN_SCOPE_LABEL", sid, f"Attested scope label {dim}:{code} missing from labels.csv")
                    continue
                if not ID_RE.match(code):
                    add_finding("INVALID_LOOKUP_ID", code, "Scope label_code violates LookupResponse ID pattern")
                allowed_dim = vocab_dims.get(dim)
                if allowed_dim is not None and code not in allowed_dim:
                    add_finding("UNKNOWN_VOCABULARY_SCOPE_LABEL", sid, f"Scope label {dim}:{code!r} not in vocabularies.toml")
                    continue
                lbl = labels_by_cat_code[(dim, code)]
                if dim == "region" and vocab_reg_parents is not None and code in vocab_reg_parents:
                    if lbl.get("parent_code") != vocab_reg_parents[code]:
                        add_finding("VOCABULARY_REGION_PARENT_MISMATCH", code, "labels.csv region parent_code mismatches vocabularies.toml")
                evref = lbl.get("evidence_reference")
                if evref and evref not in eligible_aids:
                    add_finding("INELIGIBLE_LABEL_EVIDENCE", code, "Label evidence_reference is not eligible")
                referenced_label_keys.add((lbl["registry_id"], lbl["registry_version"], lbl["code"]))
            included_scopes.append(sc)
        for dim, states in dim_states.items():
            if len(states) > 1 or (dim_counts[dim] > 1 and (dim == "register" or any(s != "attested" for s in states))):
                add_finding("CONFLICTING_SCOPE_STATES", sid, f"Conflicting scope states for dimension {dim}")

    # Verify source notice & legal text closure for promoted evidence sources.
    labels_by_key = {(l["registry_id"], l["registry_version"], l["code"]): l for l in labels}
    closure_label_keys = set(referenced_label_keys)
    lbl_pending = list(closure_label_keys)
    while lbl_pending:
        rk = lbl_pending.pop()
        lbl = labels_by_key.get(rk)
        if lbl:
            evref = lbl.get("evidence_reference")
            if evref and evref not in eligible_aids:
                add_finding("INELIGIBLE_LABEL_EVIDENCE", lbl["code"], "Label evidence_reference is not eligible")
            if lbl.get("category") == "region" and vocab_reg_parents is not None:
                lcode = lbl["code"]
                if lcode not in vocab_reg_parents:
                    add_finding("UNKNOWN_VOCABULARY_SCOPE_LABEL", lcode, f"Region label {lcode!r} not in vocabularies.toml")
                elif lbl.get("parent_code") != vocab_reg_parents[lcode]:
                    add_finding("VOCABULARY_REGION_PARENT_MISMATCH", lcode, "labels.csv region parent_code mismatches vocabularies.toml")
        if lbl and lbl.get("parent_code"):
            pk = (lbl["registry_id"], lbl["registry_version"], lbl["parent_code"])
            if pk not in closure_label_keys:
                closure_label_keys.add(pk)
                lbl_pending.append(pk)
    pack_claim_ids = {
        aid for aid, cl in claims_by_aid.items()
        if aid in eligible_aids and cl["subject_id"] in included_subject_ids
    }
    for sc in included_scopes:
        if sc.get("supporting_assertion_id"):
            pack_claim_ids.add(sc["supporting_assertion_id"])
    for lk in closure_label_keys:
        lbl = labels_by_key.get(lk)
        if lbl and lbl.get("evidence_reference"):
            pack_claim_ids.add(lbl["evidence_reference"])
    used_source_ids = {
        e["source_id"]
        for aid in pack_claim_ids
        for e in ev_by_aid.get(aid, ())
    }
    used_sources = sorted([s for s in sources if s["source_id"] in used_source_ids], key=lambda s: s["source_id"])
    notice_files, legal_meta = _collect_public_notices(workspace, used_sources, add_finding)

    l3_ok = bool(
        eligible_count > 0
        and pack_entry_ids
        and not any(f["severity"] == "error" for f in report_findings)
    )
    ordered_findings = sorted(
        report_findings,
        key=lambda f: (0 if f["code"] == "NONEMPTY_ELIGIBLE_PACK_REQUIRED" else 1, json_text(f)),
    )
    omitted_sorted = sorted(omitted_relations, key=lambda r: r["relation_id"])
    return {
        "report": {
            "schema_version": 1,
            "command": "release",
            "mode": "release",
            "pack": pack,
            "eligible_assertions": eligible_count,
            "included_entries": len(pack_entry_ids),
            "omitted_relation_count": len(omitted_sorted),
            "omitted_relations": omitted_sorted,
            "l2_structural_accepted": False,
            "l3_pack_eligible": l3_ok,
            "runtime_verified": None,
            "findings": ordered_findings,
        },
        "closure": {
            "pack_members": sorted(pack_members_for_pack, key=lambda r: (r["pack_id"], r["entry_id"])),
            "entries": sorted([entries_by_id[e] for e in pack_entry_ids], key=lambda r: r["entry_id"]),
            "forms": sorted(included_forms, key=lambda r: (r["entry_id"], r["form_id"])),
            "senses": sorted(included_senses, key=lambda r: (r["entry_id"], r["display_order"], r["sense_id"])),
            "texts": sorted(included_texts, key=lambda r: (r["owner_id"], r["component"], r["text_id"])),
            "relations": sorted(included_relations, key=lambda r: r["relation_id"]),
            "scopes": sorted(included_scopes, key=lambda r: (r["subject_kind"], r["subject_id"], r["dimension"], r["state"], r["label_code"] or "")),
            "labels": labels,
            "referenced_label_keys": referenced_label_keys,
            "identities": ident_by_id,
            "claims_by_aid": claims_by_aid,
            "eligible_aids": eligible_aids,
            "included_subject_ids": included_subject_ids,
            "ev_by_aid": ev_by_aid,
            "sources": sources,
            "terminal_dec_by_aid": terminal_dec_by_aid,
            "exc_by_aid": exc_by_aid,
            "vocab": vocab,
            "omitted_relations": omitted_sorted,
            "notice_files": notice_files,
            "legal_meta": legal_meta,
        },
    }


def validate_release(workspace, pack="core", output=None):
    """Evaluate complete L3 release closure without modifying workspace or fabricating approvals."""
    from tools.lexicon_pilot import _report_output
    workspace = Path(workspace)
    out = _report_output(workspace, output)
    if pack not in PACK_IDS or not workspace.is_dir():
        raise LexiconError("unknown pack or unavailable workspace", code=2)
    for name in ("assertions", "evidence", "sources", "decisions", "findings"):
        if not (workspace / f"{name}.csv").is_file():
            raise LexiconError(f"required release input table unavailable: {name}", code=2)
    evaluated = _evaluate_workspace(workspace, pack)
    report = evaluated["report"]
    if out:
        atomic_json(out, report)
    return report


def _render_schema_toml(pack: str) -> str:
    from tools.lexicon_tables import fields
    lines = [
        "schema_version = 1",
        'format = "tamil-toolkit-canonical-lexicon-v1"',
        'csv_encoding = "json-string-utf8-v1"',
        f"pack_id = {_toml_str(pack)}",
        f"lookup_id_pattern = {_toml_str(ID_RE.pattern)}",
        'undirected_lookup_directionality = "symmetric"',
        "acceptance_auto_source_nullable_actor = true",
        "acceptance_human_requires_nonempty_actor = true",
        'entry_provenance_rule = "dedup_union(canonical_headword, pos_assertion, entry_annotations)"',
        'sense_provenance_rule = "dedup_union(accepted_components, examples, sense_annotations)"',
        "",
        "[tables]",
    ]
    for tbl in CANONICAL_CSV_TABLES:
        lines.append(f"{tbl} = {_toml_scalar(fields(tbl))}")
    text = "\n".join(lines) + "\n"
    tomllib.loads(text)
    return text


def _build_canonical_vocab(closure: dict) -> dict:
    existing_vocab = closure["vocab"]
    if existing_vocab is not None:
        return dict(existing_vocab)
    claims_by_aid = closure["claims_by_aid"]
    lang_ids = sorted({e["language_id"] for e in closure["entries"]} | {t["language_id"] for t in closure["texts"]})
    pos_vals = sorted({
        claims_by_aid[e["pos_assertion_id"]]["value_json"]
        for e in closure["entries"]
    })
    rel_vals = sorted({
        claims_by_aid[r["relation_code_assertion_id"]]["value_json"]
        for r in closure["relations"]
    })
    reg_labels = {}
    registers = set()
    domains = set()
    temporals = set()
    varieties = {e["variety_id"] for e in closure["entries"] if e.get("variety_id")}
    dim_sets = {"register": registers, "domain": domains, "period": temporals, "variety": varieties}
    labels_by_key = {(l["registry_id"], l["registry_version"], l["code"]): l for l in closure["labels"]}
    labels_by_cat = {(l["category"], l["code"]): l for l in closure["labels"]}
    for sc in closure["scopes"]:
        if sc["state"] != "attested" or not sc.get("label_code"):
            continue
        dim, code = sc["dimension"], sc["label_code"]
        if dim == "region":
            lbl = labels_by_cat[(dim, code)]
            cur = lbl
            while cur:
                reg_labels[cur["code"]] = cur.get("parent_code")
                p = cur.get("parent_code")
                cur = labels_by_key.get((cur["registry_id"], cur["registry_version"], p)) if p else None
        elif dim in dim_sets:
            dim_sets[dim].add(code)
    ann_props = sorted({
        c["property_code"]
        for c in claims_by_aid.values()
        if c["assertion_id"] in closure["included_claim_ids"] and c["property_code"] not in CORE_STRUCTURAL_PROPERTIES
    })
    return {
        "schema_version": 1,
        "vocabulary_version": "1",
        "language_ids": lang_ids,
        "parts_of_speech": pos_vals,
        "relation_codes": rel_vals,
        "annotation_properties": ann_props,
        "registers": sorted(registers),
        "domains": sorted(domains),
        "temporals": sorted(temporals),
        "varieties": sorted(varieties),
        "regions": [
            ({"code": c, "parent_code": reg_labels[c]} if reg_labels[c] else {"code": c})
            for c in sorted(reg_labels)
        ],
    }


def _render_vocabularies_toml(vocab: dict) -> str:
    lines = [
        "schema_version = 1",
        f"vocabulary_version = {_toml_scalar(vocab['vocabulary_version'])}",
        f"language_ids = {_toml_scalar(sorted(vocab.get('language_ids', ())))}",
        f"parts_of_speech = {_toml_scalar(sorted(vocab.get('parts_of_speech', ())))}",
        f"relation_codes = {_toml_scalar(sorted(vocab.get('relation_codes', ())))}",
        f"annotation_properties = {_toml_scalar(sorted(vocab.get('annotation_properties', ())))}",
        f"registers = {_toml_scalar(sorted(vocab.get('registers', ())))}",
    ]
    for opt_k in ("domains", "temporals", "varieties"):
        if vocab.get(opt_k):
            lines.append(f"{opt_k} = {_toml_scalar(sorted(vocab[opt_k]))}")
    for reg in sorted(vocab.get("regions", ()), key=lambda r: r["code"]):
        lines.append("")
        lines.append("[[regions]]")
        lines.append(f"code = {_toml_scalar(reg['code'])}")
        if reg.get("parent_code"):
            lines.append(f"parent_code = {_toml_scalar(reg['parent_code'])}")
    text = "\n".join(lines) + "\n"
    _ = tomllib.loads(text)
    return text


def _render_attribution_md(
    pack: str,
    can_sources: list[dict],
    notice_files: dict[str, str] | None = None,
    legal_meta: dict | None = None,
) -> str:
    lines = [
        f"# Attribution and Reuse Terms: `{pack}`",
        "",
        "Generated from verified editorial source records; does not authorize unreviewed distribution.",
        "Any external license (such as CC-BY-SA-4.0) applies solely to its indicated data pack records and",
        "does not relicense the toolkit runtime engine code.",
        "",
    ]
    if notice_files:
        lines.append("## Included Canonical Notice Files")
        lines.append("")
        for rel in sorted(notice_files):
            lines.append(f"- [`{rel}`]({rel})")
        if legal_meta:
            lines.append(
                f"- Canonical CC-BY-SA-4.0 URI: {legal_meta['uri']} "
                f"(source legal text SHA-256 `{legal_meta['source_sha256']}`)"
            )
        lines.append("")
    for src in can_sources:
        lines.append(f"## Source `{src['source_id']}`")
        lines.append(f"- Label: {src['label_json']}")
        lines.append(f"- Verification State: `{src['evidence_verification_state']}`")
        lines.append(f"- Reuse State: `{src['reuse_state']}`")
        lines.append(f"- Reuse Basis: {src['reuse_basis_json']}")
        if src.get("url_json"):
            lines.append(f"- URL: {src['url_json']}")
        if src.get("attribution_text_json"):
            lines.append(f"- Attribution Text: {src['attribution_text_json']}")
        if src.get("attribution_reference_json"):
            ref = src["attribution_reference_json"]
            if notice_files and ref in notice_files:
                lines.append(f"- Attribution Reference: [`{ref}`]({ref})")
            else:
                lines.append(f"- Attribution Reference: {ref}")
        lines.append("")
    return "\n".join(lines)


def _compute_coverage(entries: list[dict], scopes: list[dict]) -> dict:
    lang_ids = sorted({e["language_id"] for e in entries})
    reg_codes = sorted({
        sc["label_code"] for sc in scopes
        if sc["dimension"] == "region" and sc["state"] == "attested" and sc.get("label_code")
    })
    register_codes = sorted({
        sc["label_code"] for sc in scopes
        if sc["dimension"] == "register" and sc["state"] == "attested" and sc.get("label_code")
    })
    reg_states = defaultdict(set)
    for sc in scopes:
        if sc["subject_kind"] == "entry" and sc["dimension"] == "region":
            reg_states[sc["subject_id"]].add(sc["state"])
    unknown_region_entries = sum(
        1
        for e in entries
        if "attested" not in reg_states.get(e["entry_id"], ())
        and "unrestricted" not in reg_states.get(e["entry_id"], ())
    )
    return {
        "language_ids": lang_ids,
        "region_codes": reg_codes,
        "register_codes": register_codes,
        "unknown_region_entries": unknown_region_entries,
    }


def _render_packs_toml(
    pack: str,
    dataset_version: str,
    vocabulary_version: str,
    manifest_sha256: str,
    file_entries: list[dict],
    entries: list[dict],
    senses: list[dict],
    forms: list[dict],
    texts: list[dict],
    relations: list[dict],
    assertions: list[dict],
    entry_revisions: dict[str, str],
    coverage: dict,
    omitted_relations: list[dict],
) -> str:
    lines = [
        "schema_version = 1",
        f"pack_id = {_toml_str(pack)}",
        f"dataset_version = {_toml_str(dataset_version)}",
        f"description = {_toml_str(PACK_DESCRIPTIONS[pack])}",
        f"vocabulary_version = {_toml_str(vocabulary_version)}",
        "l3_pack_eligible = true",
        "l2_structural_accepted = false",
        "index_format_version = 1",
        f"manifest_sha256 = {_toml_str(manifest_sha256)}",
        f"entry_count = {len(entries)}",
        f"sense_count = {len(senses)}",
        f"form_count = {len(forms)}",
        f"text_count = {len(texts)}",
        f"relation_count = {len(relations)}",
        f"assertion_count = {len(assertions)}",
        f"omitted_relation_count = {len(omitted_relations)}",
        "",
        "[coverage]",
        f"language_ids = {_toml_scalar(coverage['language_ids'])}",
        f"region_codes = {_toml_scalar(coverage['region_codes'])}",
        f"register_codes = {_toml_scalar(coverage['register_codes'])}",
        f"unknown_region_entries = {coverage['unknown_region_entries']}",
        "",
        "[entry_revisions]",
    ]
    for eid in sorted(entry_revisions):
        lines.append(f"{eid} = {_toml_str(entry_revisions[eid])}")
    for om in omitted_relations:
        lines.append("")
        lines.append("[[omitted_relations]]")
        lines.append(f"relation_id = {_toml_str(om['relation_id'])}")
        lines.append(f"source_id = {_toml_str(om['source_id'])}")
        lines.append(f"target_id = {_toml_str(om['target_id'])}")
        lines.append(f"policy = {_toml_str(om['policy'])}")
        lines.append(f"reason = {_toml_str(om['reason'])}")
    for f in file_entries:
        lines.append("")
        lines.append("[[files]]")
        lines.append(f"path = {_toml_str(f['path'])}")
        lines.append(f"sha256 = {_toml_str(f['sha256'])}")
        lines.append(f"bytes = {f['bytes']}")
        if f["rows"] is not None:
            lines.append(f"rows = {f['rows']}")
    text = "\n".join(lines) + "\n"
    tomllib.loads(text)
    return text


def promote(workspace, pack="core", output=None, report_output=None):
    """Deterministically promote a validated pack closure to a standalone canonical directory."""
    from tools.lexicon_tables import write_rows

    workspace = Path(workspace).resolve()
    if pack not in PACK_IDS or not workspace.is_dir():
        raise LexiconError("unknown pack or unavailable workspace", code=2)

    target_dir = (DEFAULT_CANONICAL_ROOT / f"{pack}-canonical") if output is None else Path(output).resolve()
    target_dir = _check_safe_dir(target_dir, [SOURCE, workspace, ROOT / "data"], "promotion output")
    if target_dir.exists() and not target_dir.is_dir():
        raise LexiconError(f"promotion output exists and is not a directory: {target_dir}", code=2)
    if report_output is not None:
        report_path = Path(report_output).resolve()
        if _paths_overlap(report_path, target_dir) or _paths_overlap(report_path, SOURCE):
            raise LexiconError("report output overlaps canonical target or frozen source", code=2)

    for name in ("assertions", "evidence", "sources", "decisions", "findings"):
        if not (workspace / f"{name}.csv").is_file():
            raise LexiconError(f"required release input table unavailable: {name}", code=2)

    evaluated = _evaluate_workspace(workspace, pack)
    report = evaluated["report"]
    if not report["l3_pack_eligible"]:
        if report_output is not None:
            atomic_json(Path(report_output).resolve(), dict(report, command="promote", output=str(target_dir)))
        raise LexiconError("release validation failed; promotion blocked", code=1)

    closure = evaluated["closure"]
    included_subj = closure["included_subject_ids"]
    claims_by_aid = closure["claims_by_aid"]
    eligible_aids = closure["eligible_aids"]

    # Collect referenced labels including ancestors.
    labels_by_key = {(l["registry_id"], l["registry_version"], l["code"]): l for l in closure["labels"]}
    can_label_keys = set(closure["referenced_label_keys"])
    pending = list(can_label_keys)
    while pending:
        rk = pending.pop()
        lbl = labels_by_key.get(rk)
        if lbl and lbl.get("parent_code"):
            pk = (lbl["registry_id"], lbl["registry_version"], lbl["parent_code"])
            if pk not in can_label_keys:
                can_label_keys.add(pk)
                pending.append(pk)
    can_labels = sorted(
        [labels_by_key[k] for k in can_label_keys],
        key=lambda r: (r["registry_id"], r["registry_version"], r["category"], r["code"]),
    )

    # Collect eligible assertions owned by promoted subjects, plus scope/label evidence references.
    can_assertion_ids = {
        aid for aid, cl in claims_by_aid.items()
        if aid in eligible_aids and cl["subject_id"] in included_subj
    }
    for sc in closure["scopes"]:
        if sc.get("supporting_assertion_id"):
            can_assertion_ids.add(sc["supporting_assertion_id"])
    for lbl in can_labels:
        if lbl.get("evidence_reference"):
            can_assertion_ids.add(lbl["evidence_reference"])
    closure["included_claim_ids"] = can_assertion_ids

    can_assertions = sorted([claims_by_aid[aid] for aid in can_assertion_ids], key=lambda r: r["assertion_id"])
    can_evidence = sorted(
        [e for aid in can_assertion_ids for e in closure["ev_by_aid"].get(aid, ())],
        key=lambda e: (e["assertion_id"], e["source_id"], e["source_record_id"] or "", e["locator_json"], e["evidence_role"]),
    )
    used_source_ids = {e["source_id"] for e in can_evidence}
    can_sources = sorted([s for s in closure["sources"] if s["source_id"] in used_source_ids], key=lambda r: r["source_id"])
    can_decisions = sorted(
        [
            dict(closure["terminal_dec_by_aid"][aid], note_json="", predecessor_decision_id=None)
            for aid in can_assertion_ids
        ],
        key=lambda r: r["decision_id"],
    )
    can_dec_ids = {d["decision_id"] for d in can_decisions}
    can_unicode_exceptions = sorted(
        [
            ex for aid in can_assertion_ids
            for ex in closure["exc_by_aid"].get(aid, ())
            if ex["decision_id"] in can_dec_ids
        ],
        key=lambda r: (r["assertion_id"], r["kind"], r["scalar_position"], r["value_sha256"]),
    )
    can_identities = sorted(
        [
            dict(closure["identities"][sid], identity_decision_id=None)
            for sid in included_subj
            if sid in closure["identities"]
        ],
        key=lambda r: r["entity_id"],
    )

    table_rows = {
        "identities": can_identities,
        "entries": closure["entries"],
        "forms": closure["forms"],
        "senses": closure["senses"],
        "texts": closure["texts"],
        "relations": closure["relations"],
        "assertions": can_assertions,
        "evidence": can_evidence,
        "decisions": can_decisions,
        "sources": can_sources,
        "scopes": closure["scopes"],
        "labels": can_labels,
        "unicode_exceptions": can_unicode_exceptions,
        "pack_members": closure["pack_members"],
    }

    vocab = _build_canonical_vocab(closure)
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = target_dir.parent / f".promote-staging-{target_dir.name}-{os.getpid()}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)
    try:
        file_entries = []
        for tbl in CANONICAL_CSV_TABLES:
            rel_path = f"{tbl}.csv"
            dest = staging / rel_path
            write_rows(dest, tbl, table_rows[tbl])
            file_entries.append({
                "path": rel_path,
                "sha256": digest(dest),
                "bytes": dest.stat().st_size,
                "rows": len(table_rows[tbl]),
            })

        notice_files = closure.get("notice_files") or {}
        legal_meta = closure.get("legal_meta")
        meta_files = {
            "schema.toml": _render_schema_toml(pack),
            "vocabularies.toml": _render_vocabularies_toml(vocab),
            "ATTRIBUTION_AND_TERMS.md": _render_attribution_md(pack, can_sources, notice_files, legal_meta),
        }
        meta_files.update(notice_files)
        for fname, content in sorted(meta_files.items()):
            dest = staging / fname
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content.encode("utf-8"))
            file_entries.append({
                "path": fname,
                "sha256": digest(dest),
                "bytes": dest.stat().st_size,
                "rows": None,
            })

        file_entries.sort(key=lambda f: f["path"])
        manifest_sha = hashlib.sha256(
            json_text([{"path": f["path"], "sha256": f["sha256"], "bytes": f["bytes"]} for f in file_entries]).encode("ascii")
        ).hexdigest()
        dataset_version = f"0.1.0+{manifest_sha[:12]}"
        coverage = _compute_coverage(closure["entries"], closure["scopes"])
        entry_revisions = {e["entry_id"]: e["revision"] for e in closure["entries"]}
        packs_content = _render_packs_toml(
            pack=pack,
            dataset_version=dataset_version,
            vocabulary_version=vocab["vocabulary_version"],
            manifest_sha256=manifest_sha,
            file_entries=file_entries,
            entries=closure["entries"],
            senses=closure["senses"],
            forms=closure["forms"],
            texts=closure["texts"],
            relations=closure["relations"],
            assertions=can_assertions,
            entry_revisions=entry_revisions,
            coverage=coverage,
            omitted_relations=closure["omitted_relations"],
        )
        (staging / "packs.toml").write_bytes(packs_content.encode("utf-8"))

        # Self-validate staged canonical bundle offline before touching destination.
        canonical_findings = validate_canonical_dir(staging)
        if canonical_findings:
            raise LexiconError("staged canonical validation failed: " + "; ".join(canonical_findings), code=2)

        staged_bytes = {
            p.relative_to(staging).as_posix(): p.read_bytes()
            for p in sorted(staging.rglob("*")) if p.is_file()
        }
        if target_dir.exists():
            existing_bytes = {
                p.relative_to(target_dir).as_posix(): p.read_bytes()
                for p in sorted(target_dir.rglob("*")) if p.is_file()
            }
            if existing_bytes != staged_bytes:
                raise LexiconError(
                    f"conflicting canonical contents at {target_dir}; manual or modified files preserved without overwrite",
                    code=2,
                )
        else:
            staging.replace(target_dir)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    pack_info = {
        "id": pack,
        "dataset_version": dataset_version,
        "schema_version": 1,
        "index_format_version": 1,
        "manifest_sha256": manifest_sha,
        "available": True,
        "coverage": coverage,
    }
    result = {
        "schema_version": 1,
        "command": "promote",
        "pack": pack,
        "output": str(target_dir),
        "dataset_version": dataset_version,
        "manifest_sha256": manifest_sha,
        "entry_count": len(closure["entries"]),
        "sense_count": len(closure["senses"]),
        "omitted_relation_count": len(closure["omitted_relations"]),
        "omitted_relations": closure["omitted_relations"],
        "pack_info": pack_info,
        "l2_structural_accepted": False,
        "l3_pack_eligible": True,
        "runtime_verified": None,
    }
    if report_output is not None:
        atomic_json(Path(report_output).resolve(), result)
    return result


def load_canonical_pack(canonical_dir: Path | str) -> dict:
    """Load and structurally decode a canonical promoted pack directory."""
    from tools.lexicon_tables import read_rows
    cdir = Path(canonical_dir)
    if not cdir.is_dir():
        raise LexiconError(f"canonical directory does not exist: {cdir}", code=2)
    packs = tomllib.loads((cdir / "packs.toml").read_text(encoding="utf-8"))
    vocab = tomllib.loads((cdir / "vocabularies.toml").read_text(encoding="utf-8"))
    schema = tomllib.loads((cdir / "schema.toml").read_text(encoding="utf-8"))
    tables = {}
    for tbl in CANONICAL_CSV_TABLES:
        p = cdir / f"{tbl}.csv"
        if p.is_file():
            tables[tbl] = list(read_rows(p))
    notices = {}
    notices_dir = cdir / "notices"
    if notices_dir.is_dir():
        for p in sorted(notices_dir.rglob("*.md")):
            notices[p.relative_to(cdir).as_posix()] = p.read_text(encoding="utf-8")
    return {"packs": packs, "vocabularies": vocab, "schema": schema, "tables": tables, "notices": notices}


def validate_canonical_dir(
    canonical_dir: Path | str,
    *,
    preloaded_tables: dict[str, list[dict]] | None = None,
    prevalidated_schema: bool = False,
) -> list[str]:
    """Offline validation of a canonical promoted directory without requiring editorial history."""
    from tools.lexicon_review import (
        batch_claim_revisions,
        build_text_audit_cache,
        eligibility,
        evidence_hash,
        unicode_findings,
    )
    from tools.lexicon_tables import ACCEPTED_OUTCOMES, fields, read_rows, validate_relations

    cdir = Path(canonical_dir)
    cdir_resolved = cdir.resolve()
    failures: list[str] = []
    if not cdir.is_dir():
        return [f"canonical directory unavailable: {cdir}"]

    unexpected_ext = [
        p.relative_to(cdir).as_posix()
        for p in sorted(cdir.rglob("*"))
        if p.is_file() and p.suffix.lower() not in ALLOWED_CANONICAL_SUFFIXES
    ]
    if unexpected_ext:
        failures.append("canonical directory allows only .csv, .toml, and .md files: " + ", ".join(unexpected_ext))
    for req_meta in ("packs.toml", "vocabularies.toml", "schema.toml", "ATTRIBUTION_AND_TERMS.md"):
        if not (cdir / req_meta).is_file():
            failures.append(f"missing required canonical metadata file: {req_meta}")
    if failures:
        return sorted(set(failures))

    try:
        packs = tomllib.loads((cdir / "packs.toml").read_text(encoding="utf-8"))
        vocab = _parse_vocabularies_toml(cdir / "vocabularies.toml")
        schema = tomllib.loads((cdir / "schema.toml").read_text(encoding="utf-8"))
    except (LexiconError, OSError, tomllib.TOMLDecodeError) as exc:
        return [f"canonical metadata parse error: {exc}"]

    if packs.get("schema_version") != 1 or not packs.get("l3_pack_eligible") or packs.get("l2_structural_accepted") is not False:
        failures.append("packs.toml: invalid release metadata flags")
    if schema.get("schema_version") != 1 or schema.get("undirected_lookup_directionality") != "symmetric":
        failures.append("schema.toml: invalid canonical schema metadata")

    # Verify exact manifest SHA-256 and file hashes against disk (including notices/*.md).
    manifest_files = packs.get("files", [])
    declared_paths = {f.get("path") for f in manifest_files}
    required_base_paths = {f"{tbl}.csv" for tbl in CANONICAL_CSV_TABLES} | {"schema.toml", "vocabularies.toml", "ATTRIBUTION_AND_TERMS.md"}
    actual_paths = {p.relative_to(cdir).as_posix() for p in cdir.rglob("*") if p.is_file()} - {"packs.toml"}
    if not required_base_paths.issubset(declared_paths) or declared_paths != actual_paths:
        failures.append("packs.toml: file inventory mismatch with canonical directory contents")

    digest_basis = []
    for fentry in sorted(manifest_files, key=lambda item: str(item.get("path", ""))):
        rel = fentry.get("path", "")
        fpath = cdir / rel
        if not fpath.is_file():
            failures.append(f"packs.toml: declared file missing on disk: {rel}")
            continue
        actual_sha = digest(fpath)
        actual_bytes = fpath.stat().st_size
        if actual_sha != fentry.get("sha256") or actual_bytes != fentry.get("bytes"):
            failures.append(f"packs.toml: digest or byte size mismatch for {rel}")
        digest_basis.append({"path": rel, "sha256": actual_sha, "bytes": actual_bytes})

    computed_manifest = hashlib.sha256(json_text(digest_basis).encode("ascii")).hexdigest()
    if computed_manifest != packs.get("manifest_sha256"):
        failures.append("packs.toml: manifest_sha256 mismatch")

    def add_can_finding(_code: str, _subject: str, reason: str) -> None:
        failures.append(reason)

    # Check Markdown notices for clean UTF-8 NFC and absence of private JSON / local Windows paths.
    attr_path = cdir / "ATTRIBUTION_AND_TERMS.md"
    attr_text = ""
    try:
        attr_text = attr_path.read_text(encoding="utf-8")
        _check_public_text_safety(attr_text, "ATTRIBUTION_AND_TERMS.md", "ATTRIBUTION_AND_TERMS.md", add_can_finding)
    except UnicodeDecodeError as exc:
        failures.append(f"ATTRIBUTION_AND_TERMS.md: invalid UTF-8: {exc}")

    for npath in sorted((cdir / "notices").rglob("*")) if (cdir / "notices").is_dir() else ():
        if npath.is_file() and npath.suffix != ".md":
            rel_bad = npath.relative_to(cdir).as_posix()
            failures.append(f"{rel_bad}: only .md files allowed under canonical notices/")

    for npath in sorted(cdir.rglob("*.md")):
        if npath == attr_path:
            continue
        rel_n = npath.relative_to(cdir).as_posix()
        try:
            ntext = npath.read_text(encoding="utf-8")
            _check_public_text_safety(ntext, rel_n, rel_n, add_can_finding)
        except UnicodeDecodeError as exc:
            failures.append(f"{rel_n}: invalid UTF-8: {exc}")

    tables = {}
    rows_validated_by_read = prevalidated_schema
    for tbl in CANONICAL_CSV_TABLES:
        fpath = cdir / f"{tbl}.csv"
        if not fpath.is_file():
            failures.append(f"missing canonical CSV table: {tbl}.csv")
            continue
        if preloaded_tables is not None and tbl in preloaded_tables:
            tables[tbl] = preloaded_tables[tbl]
        else:
            try:
                rows = list(read_rows(fpath, tbl))
                rows_validated_by_read = True
            except (LexiconError, OSError, ValueError) as exc:
                failures.append(f"{tbl}.csv: {exc}")
                continue
            tables[tbl] = rows
        tbl_meta = schema.get("tables", {}).get(tbl)
        if tbl_meta != fields(tbl):
            failures.append(f"schema.toml: column list mismatch for {tbl}")

    if failures:
        return sorted(set(failures))

    # Empty pack check + entry revision consistency.
    pack_id = packs.get("pack_id")
    if pack_id not in PACK_IDS or not tables["entries"] or not tables["pack_members"]:
        failures.append("canonical pack must have valid pack_id and nonempty entries/pack_members")
    if len(tables["entries"]) != packs.get("entry_count"):
        failures.append("packs.toml: entry_count mismatch")
    revs = packs.get("entry_revisions", {})
    if {e["entry_id"]: e["revision"] for e in tables["entries"]} != revs:
        failures.append("packs.toml: entry_revisions map mismatch")

    for rf in validate_relations(tables):
        if rf.get("severity", "error") == "error":
            failures.append(
                f"canonical relations error ({rf.get('code')} on {rf.get('subject_id')}): {rf.get('reason')}"
            )

    # Verify every source's permission/verification state, attribution reference, and CC-BY-SA-4.0 legal text closure.
    if not tables["sources"]:
        failures.append("canonical pack must have nonempty sources")
    for src in tables["sources"]:
        sid = src["source_id"]
        has_attr_text = bool(str(src.get("attribution_text_json") or "").strip())
        has_attr_ref = bool(str(src.get("attribution_reference_json") or "").strip())
        if (
            src.get("reuse_state") != "permitted"
            or src.get("evidence_verification_state") != "verified"
            or not str(src.get("reuse_basis_json") or "").strip()
            or not (has_attr_text or has_attr_ref)
        ):
            failures.append(
                f"sources.csv: unverified or non-permitted source {sid} "
                f"(reuse_state={src.get('reuse_state')!r}, verification={src.get('evidence_verification_state')!r})"
            )
        if sid not in attr_text:
            failures.append(f"ATTRIBUTION_AND_TERMS.md: missing source entry {sid}")
        kind, ref_val = _classify_attribution_ref(src.get("attribution_reference_json"))
        if kind == "unsafe":
            failures.append(f"sources.csv: unsafe or non-canonical attribution reference on {sid}: {ref_val!r}")
        elif kind == "local_file":
            ref_path = (cdir / ref_val).resolve()
            if not ref_path.is_relative_to(cdir_resolved) or not ref_path.is_file():
                failures.append(f"sources.csv: missing referenced canonical notice file: {ref_val}")
            elif ref_val not in declared_paths:
                failures.append(f"packs.toml: referenced notice file missing from manifest: {ref_val}")

    if any(_source_requires_cc_by_sa_4(src) for src in tables["sources"]):
        legal_path = cdir / "notices/CC-BY-SA-4.0.md"
        if not legal_path.is_file() or "notices/CC-BY-SA-4.0.md" not in declared_paths:
            failures.append("notices/CC-BY-SA-4.0.md: missing or unmanifested CC-BY-SA-4.0 legal text")
        else:
            ltext = legal_path.read_text(encoding="utf-8")
            if "Attribution-ShareAlike 4.0 International" not in ltext or CC_BY_SA_URL not in ltext:
                failures.append("notices/CC-BY-SA-4.0.md: incomplete legal text or canonical URI")

    # Offline verification of every claim, evidence bundle, source reuse/attribution, decision, and Unicode gate.
    ev_by_aid = defaultdict(list)
    for ev in tables["evidence"]:
        ev_by_aid[ev["assertion_id"]].append(ev)
    dec_by_aid = defaultdict(list)
    for dec in tables["decisions"]:
        if dec.get("note_json") not in ("", None) or dec.get("predecessor_decision_id") is not None:
            failures.append(f"decisions.csv: unsanitized private note or history pointer on {dec['decision_id']}")
        if dec.get("outcome") not in ACCEPTED_OUTCOMES:
            failures.append(f"decisions.csv: non-accepted decision present: {dec['decision_id']}")
        dec_by_aid[dec["assertion_id"]].append(dec)
    exc_by_aid = defaultdict(list)
    for ex in tables["unicode_exceptions"]:
        exc_by_aid[ex["assertion_id"]].append(ex)

    claims_by_aid = {c["assertion_id"]: c for c in tables["assertions"]}
    ident_kind_by_id = {row["entity_id"]: row["kind"] for row in tables["identities"]}
    vocab_langs = set(vocab.get("language_ids", ()))
    vocab_pos = set(vocab.get("parts_of_speech", ()))
    vocab_rels = set(vocab.get("relation_codes", ()))
    vocab_ann = set(vocab.get("annotation_properties", ()))
    vocab_reg_parents = {r["code"]: r.get("parent_code") for r in vocab.get("regions", ())}
    vocab_regs = set(vocab_reg_parents)
    vocab_registers = set(vocab.get("registers", ()))
    vocab_domains = set(vocab.get("domains", ()))
    vocab_periods = set(vocab.get("temporals", ()))
    vocab_varieties = set(vocab.get("varieties", ()))
    vocab_dims = {
        "region": vocab_regs,
        "register": vocab_registers,
        "domain": vocab_domains,
        "period": vocab_periods,
        "variety": vocab_varieties,
    }

    labels_by_cat_code = _check_label_hierarchy(tables["labels"], add_can_finding)
    for lbl in tables["labels"]:
        evref = lbl.get("evidence_reference")
        if not evref or evref not in claims_by_aid:
            failures.append(
                f"labels.csv: label {lbl['code']!r} evidence_reference {evref!r} not in canonical assertions"
            )
        if lbl["category"] == "region" and lbl["code"] in vocab_reg_parents:
            if lbl.get("parent_code") != vocab_reg_parents[lbl["code"]]:
                failures.append(
                    f"labels.csv: region {lbl['code']!r} parent_code {lbl.get('parent_code')!r} "
                    f"disagrees with vocabularies.toml {vocab_reg_parents[lbl['code']]!r}"
                )

    audit_cache = build_text_audit_cache(tables["assertions"])
    claim_revs = batch_claim_revisions(tables["assertions"])
    sources_by_id = {s.get("source_id"): s for s in tables["sources"]}
    sources_unique = len(sources_by_id) == len(tables["sources"])
    for claim, computed_rev in zip(tables["assertions"], claim_revs):
        aid = claim["assertion_id"]
        if claim["claim_revision_sha256"] != computed_rev:
            failures.append(f"assertions.csv: claim_revision mismatch for {aid}")
        rel_ev = ev_by_aid.get(aid, ())
        rel_dec = dec_by_aid.get(aid, ())
        rel_exc = exc_by_aid.get(aid, ())
        uf = unicode_findings(claim, rel_exc, rel_dec, _audit_cache=audit_cache, _revision=computed_rev)
        res = eligibility(
            claim,
            rel_ev,
            tables["sources"],
            rel_dec,
            uf,
            _revision=computed_rev,
            _assertion_valid=True if rows_validated_by_read else None,
            _source_index=sources_by_id if sources_unique else None,
            _evidence_valid=True if rows_validated_by_read else None,
        )
        if not res["eligible"]:
            failures.append(f"assertions.csv: ineligible canonical claim {aid}: {','.join(res['reasons'])}")
        if rel_dec and rel_dec[0]["evidence_bundle_sha256"] != evidence_hash(rel_ev):
            failures.append(f"decisions.csv: evidence_bundle_sha256 mismatch for {aid}")
        if claim["property_code"] == "part_of_speech" and claim["value_json"] not in vocab_pos:
            failures.append(f"vocabularies.toml: POS {claim['value_json']!r} not in finite registry")
        if claim["property_code"] == "relation_code" and claim["value_json"] not in vocab_rels:
            failures.append(f"vocabularies.toml: relation {claim['value_json']!r} not in finite registry")
        if claim["property_code"] not in CORE_STRUCTURAL_PROPERTIES and claim["property_code"] not in vocab_ann:
            failures.append(f"vocabularies.toml: annotation property {claim['property_code']!r} not in finite registry")

    for row in tables["texts"]:
        if row["owner_kind"] != "sense" or row["component"] == "unparsed":
            failures.append(f"texts.csv: forbidden owner_kind/component on {row['text_id']}")
        if row["language_id"] not in vocab_langs:
            failures.append(f"vocabularies.toml: text language_id {row['language_id']!r} not in registry")

    for e in tables["entries"]:
        if e["language_id"] not in vocab_langs:
            failures.append(f"vocabularies.toml: entry language_id {e['language_id']!r} not in registry")
        if e.get("variety_id") and e["variety_id"] not in vocab_varieties:
            failures.append(f"vocabularies.toml: entry variety_id {e['variety_id']!r} not in registry")

    for rel in tables["relations"]:
        rid = rel["relation_id"]
        if rel.get("source_kind") not in {"entry", "sense"} or rel.get("target_kind") not in {"entry", "sense"}:
            failures.append(f"relations.csv: invalid endpoint kind on {rid}")
        if rel.get("source_kind") != "sense":
            failures.append(
                f"relations.csv: relation {rid} unsupported source_kind {rel.get('source_kind')!r}: "
                "LookupResponse only projects sense-anchored relations"
            )
        if ident_kind_by_id.get(rel["source_id"]) != rel.get("source_kind"):
            failures.append(f"relations.csv: source_kind {rel.get('source_kind')!r} mismatches identity kind for {rel['source_id']}")
        if ident_kind_by_id.get(rel["target_id"]) != rel.get("target_kind"):
            failures.append(f"relations.csv: target_kind {rel.get('target_kind')!r} mismatches identity kind for {rel['target_id']}")
        rclaim = claims_by_aid.get(rel["relation_code_assertion_id"])
        if (
            rclaim is None
            or rclaim.get("property_code") != "relation_code"
            or rclaim.get("subject_kind") != "relation"
            or rclaim.get("subject_id") != rid
        ):
            failures.append(f"relations.csv: relation_code_assertion_id mismatch on {rid}")

    scopes_by_subject_dim = defaultdict(list)
    for sc in tables["scopes"]:
        skind, sid, dim, st = sc["subject_kind"], sc["subject_id"], sc["dimension"], sc["state"]
        scopes_by_subject_dim[(skind, sid, dim)].append(sc)
        if ident_kind_by_id.get(sid) != skind:
            failures.append(f"scopes.csv: subject_kind {skind!r} mismatches identity kind for {sid}")
        if st == "not_applicable" and dim != "register":
            failures.append(f"scopes.csv: state 'not_applicable' is permitted only for dimension 'register', not {dim!r}")
        if st != "attested" and sc.get("label_code") is not None:
            failures.append(f"scopes.csv: {dim}={st} forbids label_code on {skind}:{sid}")
        said = sc.get("supporting_assertion_id")
        did = sc.get("decision_id")
        if st in {"attested", "unrestricted"} and (not said or not did):
            failures.append(f"scopes.csv: {dim}={st} requires supporting_assertion_id and decision_id on {skind}:{sid}")
        elif said or did:
            if not said or not did:
                failures.append(f"scopes.csv: partial assertion/decision binding on {skind}:{sid} ({dim})")
            else:
                sclaim = claims_by_aid.get(said)
                tdec = dec_by_aid.get(said, [None])[0]
                if (
                    sclaim is None
                    or sclaim.get("subject_kind") != skind
                    or sclaim.get("subject_id") != sid
                    or not _scope_dim_matches_property(dim, sclaim.get("property_code"))
                ):
                    failures.append(f"scopes.csv: supporting_assertion_id {said} mismatches subject/property on {skind}:{sid} ({dim})")
                elif tdec is None or tdec.get("decision_id") != did:
                    failures.append(f"scopes.csv: decision_id {did} mismatches current accepted decision for {said}")
        if st == "attested":
            code = sc.get("label_code")
            allowed_dim = vocab_dims.get(dim)
            if allowed_dim is not None and code not in allowed_dim:
                failures.append(f"vocabularies.toml: {dim} {code!r} not in finite registry")
            lbl = labels_by_cat_code.get((dim, code)) if code else None
            if lbl is None:
                failures.append(f"scopes.csv: attested {dim}:{code!r} missing from labels.csv")
            elif dim == "region" and code in vocab_reg_parents:
                if lbl.get("parent_code") != vocab_reg_parents[code]:
                    failures.append(
                        f"labels.csv: region {code!r} parent_code {lbl.get('parent_code')!r} "
                        f"disagrees with vocabularies.toml {vocab_reg_parents[code]!r}"
                    )
    for (skind, sid, dim), sc_rows in scopes_by_subject_dim.items():
        states = {r["state"] for r in sc_rows}
        if len(states) > 1 or (len(sc_rows) > 1 and (dim == "register" or any(s != "attested" for s in states))):
            failures.append(f"scopes.csv: conflicting scope states or cardinality on {skind}:{sid} dimension={dim}")

    return sorted(set(failures))


def _make_provenance_list(aid: str, claims_by_aid: dict, ev_by_aid: dict, dec_by_aid: dict) -> list[dict]:
    dec = dec_by_aid[aid]
    claim = claims_by_aid[aid]
    acceptance = {
        "decision_id": dec["decision_id"],
        "kind": dec["outcome"],
        "actor_id": dec.get("actor_id"),
        "method": dec.get("method_version"),
        "decided_on": dec["decision_date"],
    }
    provs = []
    for ev in sorted(
        ev_by_aid.get(aid, ()),
        key=lambda e: (e["source_id"], e["locator_json"], e["evidence_role"]),
    ):
        if ev.get("evidence_role") != "supports":
            continue
        loc = ev["locator_json"]
        locator_str = loc if isinstance(loc, str) else json_text(loc)
        provs.append({
            "assertion_id": aid,
            "revision_sha256": claim["claim_revision_sha256"],
            "source_id": ev["source_id"],
            "locator": locator_str,
            "acceptance": acceptance,
        })
    return provs


def _dedup_provenance(items: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for item in sorted(items, key=lambda p: (p["assertion_id"], p["source_id"], p["locator"])):
        key = (item["assertion_id"], item["revision_sha256"], item["source_id"], item["locator"], item["acceptance"]["decision_id"])
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def build_lookup_entry_projection(canonical_or_loaded: Path | str | dict, entry_id: str) -> dict:
    """Project one canonical entry into a ``LookupResponse`` ``Entry`` conforming to ``contracts/lookup.md``."""
    data = canonical_or_loaded if isinstance(canonical_or_loaded, dict) and "tables" in canonical_or_loaded else load_canonical_pack(canonical_or_loaded)
    tables = data["tables"]
    entries_by_id = {r["entry_id"]: r for r in tables["entries"]}
    entry = entries_by_id.get(entry_id)
    if entry is None:
        raise LexiconError(f"entry not found in canonical pack: {entry_id}", code=2)

    claims_by_aid = {c["assertion_id"]: c for c in tables["assertions"]}
    ev_by_aid = defaultdict(list)
    for ev in tables["evidence"]:
        ev_by_aid[ev["assertion_id"]].append(ev)
    dec_by_aid = {d["assertion_id"]: d for d in tables["decisions"]}
    scopes_by_subject = defaultdict(list)
    for sc in tables["scopes"]:
        scopes_by_subject[(sc["subject_kind"], sc["subject_id"])].append(sc)

    for rel in tables["relations"]:
        if rel.get("source_kind") != "sense":
            raise LexiconError(
                f"relation {rel.get('relation_id')} unsupported source_kind {rel.get('source_kind')!r}: "
                "LookupResponse only projects sense-anchored relations",
                code=2,
            )

    entry_forms = [f for f in tables["forms"] if f["entry_id"] == entry_id]
    projected_forms = []
    canonical_headword = None
    canonical_hw_prov = []
    for f in sorted(entry_forms, key=lambda row: (0 if row["role"] == "canonical" else 1, row["form_id"])):
        aid = f["text_assertion_id"]
        txt_val = str(claims_by_aid[aid]["value_json"])
        prov = _make_provenance_list(aid, claims_by_aid, ev_by_aid, dec_by_aid)
        conv = None
        if f.get("convention_assertion_id"):
            conv = str(claims_by_aid[f["convention_assertion_id"]]["value_json"])
        if f["form_id"] == entry["canonical_form_id"]:
            canonical_headword = txt_val
            canonical_hw_prov = prov
        projected_forms.append({
            "form_id": f["form_id"],
            "representation": f["representation"],
            "role": f["role"],
            "text": txt_val,
            "convention": conv,
            "provenance": prov,
        })

    def build_scope_obj(kind: str, sid: str) -> dict:
        rows = [r for r in scopes_by_subject.get((kind, sid), ()) if r["dimension"] == "region"]
        if not rows:
            return {"state": "unknown", "codes": [], "provenance": []}
        states = {r["state"] for r in rows}
        if "attested" in states:
            codes = sorted({r["label_code"] for r in rows if r["state"] == "attested" and r.get("label_code")})
            provs = []
            for r in rows:
                if r.get("supporting_assertion_id"):
                    provs.extend(_make_provenance_list(r["supporting_assertion_id"], claims_by_aid, ev_by_aid, dec_by_aid))
            return {"state": "attested", "codes": codes, "provenance": _dedup_provenance(provs)}
        if "unrestricted" in states:
            provs = []
            for r in rows:
                if r.get("supporting_assertion_id"):
                    provs.extend(_make_provenance_list(r["supporting_assertion_id"], claims_by_aid, ev_by_aid, dec_by_aid))
            return {"state": "unrestricted", "codes": [], "provenance": _dedup_provenance(provs)}
        return {"state": "unknown", "codes": [], "provenance": []}

    def build_register_field(kind: str, sid: str) -> dict:
        rows = [r for r in scopes_by_subject.get((kind, sid), ()) if r["dimension"] == "register"]
        if not rows:
            return {"availability": "unknown", "value": None, "convention": None, "provenance": []}
        first = rows[0]
        st = first["state"]
        if st == "attested":
            provs = _make_provenance_list(first["supporting_assertion_id"], claims_by_aid, ev_by_aid, dec_by_aid)
            return {"availability": "available", "value": first["label_code"], "convention": None, "provenance": provs}
        if st == "unrestricted":
            provs = _make_provenance_list(first["supporting_assertion_id"], claims_by_aid, ev_by_aid, dec_by_aid)
            return {"availability": "available", "value": "unrestricted", "convention": None, "provenance": provs}
        avail = "not_applicable" if st == "not_applicable" else "unknown"
        return {"availability": avail, "value": None, "convention": None, "provenance": []}

    def build_annotations(kind: str, sid: str) -> list[dict]:
        anns = []
        for c in sorted(claims_by_aid.values(), key=lambda x: (x["property_code"], x["assertion_id"])):
            if c["subject_kind"] == kind and c["subject_id"] == sid and c["property_code"] not in CORE_STRUCTURAL_PROPERTIES:
                provs = _make_provenance_list(c["assertion_id"], claims_by_aid, ev_by_aid, dec_by_aid)
                anns.append({
                    "property": c["property_code"],
                    "field": {
                        "availability": "available",
                        "value": c["value_json"],
                        "convention": c.get("convention_reference"),
                        "provenance": provs,
                    },
                })
        return anns

    pos_aid = entry["pos_assertion_id"]
    pos_prov = _make_provenance_list(pos_aid, claims_by_aid, ev_by_aid, dec_by_aid)
    pos_field = {
        "availability": "available",
        "value": str(claims_by_aid[pos_aid]["value_json"]),
        "convention": None,
        "provenance": pos_prov,
    }
    entry_annotations = build_annotations("entry", entry_id)
    entry_ann_prov = [p for a in entry_annotations for p in a["field"]["provenance"]]

    entry_region = build_scope_obj("entry", entry_id)
    entry_register = build_register_field("entry", entry_id)

    entry_senses = sorted(
        [s for s in tables["senses"] if s["entry_id"] == entry_id],
        key=lambda row: (row["display_order"], row["sense_id"]),
    )
    projected_senses = []
    for sen in entry_senses:
        sid = sen["sense_id"]
        stexts = [t for t in tables["texts"] if t["owner_kind"] == "sense" and t["owner_id"] == sid]
        comps = []
        examples = []
        sense_prov = []
        for t in sorted(stexts, key=lambda r: (r["component"], r["text_id"])):
            aid = t["text_assertion_id"]
            tprov = _make_provenance_list(aid, claims_by_aid, ev_by_aid, dec_by_aid)
            obj = {
                "text_id": t["text_id"],
                "kind": t["component"],
                "language_id": t["language_id"],
                "text": str(claims_by_aid[aid]["value_json"]),
                "provenance": tprov,
            }
            if t["component"] == "example":
                examples.append(obj)
                sense_prov.extend(tprov)
            else:
                comps.append(obj)
                sense_prov.extend(tprov)

        srels = []
        for rel in sorted(tables["relations"], key=lambda r: r["relation_id"]):
            if rel["source_kind"] == "sense" and rel["source_id"] == sid:
                rprov = _make_provenance_list(rel["relation_code_assertion_id"], claims_by_aid, ev_by_aid, dec_by_aid)
                dir_out = "symmetric" if rel["directionality"] == "undirected" else "directed"
                srels.append({
                    "relation_id": rel["relation_id"],
                    "code": str(claims_by_aid[rel["relation_code_assertion_id"]]["value_json"]),
                    "directionality": dir_out,
                    "source": {"kind": rel["source_kind"], "id": rel["source_id"]},
                    "target": {"kind": rel["target_kind"], "id": rel["target_id"]},
                    "provenance": rprov,
                })

        s_anns = build_annotations("sense", sid)
        sense_prov.extend(p for a in s_anns for p in a["field"]["provenance"])
        sense_scopes = scopes_by_subject.get(("sense", sid), ())
        has_sense_region = any(r["dimension"] == "region" for r in sense_scopes)
        has_sense_register = any(r["dimension"] == "register" for r in sense_scopes)
        sense_region = (
            build_scope_obj("sense", sid)
            if has_sense_region
            else {
                "state": entry_region["state"],
                "codes": list(entry_region["codes"]),
                "provenance": [dict(p) for p in entry_region["provenance"]],
            }
        )
        sense_register = (
            build_register_field("sense", sid)
            if has_sense_register
            else {
                "availability": entry_register["availability"],
                "value": entry_register["value"],
                "convention": entry_register["convention"],
                "provenance": [dict(p) for p in entry_register["provenance"]],
            }
        )
        projected_senses.append({
            "sense_id": sid,
            "display_order": sen["display_order"],
            "parent_sense_id": sen.get("parent_sense_id"),
            "components": comps,
            "examples": examples,
            "relations": srels,
            "region": sense_region,
            "register": sense_register,
            "annotations": s_anns,
            "provenance": _dedup_provenance(sense_prov),
        })

    return {
        "entry_id": entry_id,
        "revision": entry["revision"],
        "headword": canonical_headword,
        "language_id": entry["language_id"],
        "part_of_speech": pos_field,
        "forms": projected_forms,
        "senses": projected_senses,
        "region": entry_region,
        "register": entry_register,
        "annotations": entry_annotations,
        "provenance": _dedup_provenance(canonical_hw_prov + pos_prov + entry_ann_prov),
    }

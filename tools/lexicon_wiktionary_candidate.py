"""Build and verify isolated pending Wiktionary candidate datasets.

Reads strictly from checked-in official English Wiktionary revision snapshots
under ``data/curation/wiktionary-candidate/snapshots/`` or
``data/curation/wiktionary-homograph-candidate/snapshots/``, projects them into
all 21 curation tables via ``tools.lexicon_tables``, preserves provenance and
exclusion manifests, and verifies zero accepted/runtime claims.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from tools.lexicon import (
    MANIFEST as SOURCE_MANIFEST,
    ROOT,
    allocate_id,
    data_json,
    digest,
    json_text,
    native_inspect,
    safe_output,
)
from tools.lexicon_pilot import release_guard
from tools.lexicon_review import (
    _current_decisions,
    claim_revision,
    eligibility,
    evidence_hash,
    unicode_findings,
    validate_history,
)
from tools.lexicon_tables import read_rows, write_rows
from tools.lexicon_validate import check_curated_csv

WORKSPACE_TABLES: tuple[str, ...] = (
    "snapshots",
    "sources",
    "identities",
    "source_records",
    "dispositions",
    "record_targets",
    "entries",
    "forms",
    "senses",
    "texts",
    "relations",
    "assertions",
    "evidence",
    "decisions",
    "changes",
    "successors",
    "findings",
    "unicode_exceptions",
    "labels",
    "scopes",
    "pack_members",
)

CANDIDATE_DIR = ROOT / "data/curation/wiktionary-candidate"
CANDIDATE_DATASET_ID = "wiktionary-en-tamil-candidate"
CANDIDATE_NAMESPACE = "7a5a7f6c-7f1e-5b2e-94c8-2f4b8e6b4f01"
HOMOGRAPH_DIR = ROOT / "data/curation/wiktionary-homograph-candidate"
HOMOGRAPH_DATASET_ID = "wiktionary-en-tamil-homograph-candidate"
HOMOGRAPH_NAMESPACE = "4f8c3162-a2c9-5a18-9d25-6d8d2d37b110"
REVIEWED_DIR = ROOT / "data/curation/wiktionary-core-reviewed"
REVIEWED_DATASET_ID = "wiktionary-core-reviewed"
REVIEWED_NAMESPACE = "a3f5c8e2-910b-5d4e-b772-19e4e8d316c7"
REVIEWED_METHOD_VERSION = "wiktionary-core-reviewed-v1"
DEFAULT_APPROVAL_RECEIPT = ROOT / "docs/reviews/wiktionary-core-approval-2026-11-14.json"
DEFAULT_REVIEW_PACKET = ROOT / "data/curation/wiktionary-candidate/provenance/core_review_packet.json"
LABEL_REGISTRY_ID = "enwiktionary-ta-qualifiers"

PINNED_NOTICE_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "wikimedia_tou_api.json": {
        "pageid": 21261,
        "revid": 598588,
        "timestamp": "2026-10-25T01:07:30Z",
        "sha256": "c3e0bff8b859941468d6895dff392d893bd13cfae2ea0ae8565db74aaaab1123",
    },
    "wiktionary_copyrights_api.json": {
        "pageid": 1503,
        "revid": 87545419,
        "timestamp": "2025-10-22T20:09:50Z",
        "sha256": "049a09491de163dc85b77e6f260705bb5e59052c27b4e0f75ea49dd5d3e4fe4c",
    },
    "cc_by_sa_4_0_legalcode.txt": {
        "required_text": "Attribution-ShareAlike 4.0 International",
        "sha256": "28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5",
    },
}

METHOD_NAME = "wiktionary-candidate-allowlist"
PRIOR_METHOD_VERSION = "wiktionary-candidate-v1"
PRIOR_EXTRACTION_VERSION = "wiktionary-candidate-v1+utf8-v1"
METHOD_VERSION = "wiktionary-candidate-v2"
EXTRACTION_VERSION = "wiktionary-candidate-v2+utf8-v1"
RETRIEVAL_DATE = "2026-11-14"

WIKILINK_RE = re.compile(r"\[\[([^|\]]+\|)?([^\]]+)\]\]")
NG_TEMPLATE_RE = re.compile(r"^\{\{ng\|(.+)\}\}$", re.DOTALL)
QUALIFIER_PREFIX_RE = re.compile(r"^\{\{q\|([^}]+)\}\}\s*")
LABEL_PREFIX_RE = re.compile(r"^\{\{lb\|ta\|([^}]+)\}\}\s*")
GENERIC_TEMPLATE_RE = re.compile(r"\{\{([^|}]+)(?:\|([^}]*))?\}\}")

QUALIFIER_LABEL_METADATA: dict[str, dict[str, str]] = {
    "written": {
        "category": "register",
        "display_label": "written",
        "definition": "Written usage qualifier preserved literally from pinned {{q|written}} template; pending human review.",
    },
    "catholicism": {
        "category": "domain",
        "display_label": "Catholicism",
        "definition": "Catholicism religious-domain label preserved literally from pinned {{lb|ta|catholicism}} template; pending human review.",
    },
}

# Strictly pinned official en.wiktionary.org revision allowlist.
PINNED_ALLOWLIST: dict[int, dict[str, Any]] = {
    85842017: {
        "legacy_word_id": "1921",
        "slug": "atataa",
        "title": "\u0b85\u0b9f\u0b9f\u0bbe",
        "pageid": 11100687,
        "revision_timestamp": "2025-08-09T18:54:09Z",
        "wikitext_sha256": "ffa17f0eaa27f7ccf3b6bb55f9e7da0532e7e7f634fa4b9afb993847c609d063",
        "wikitext_sha1": "be7d19fd0b2aa1bdb479f598a976d7eb242c9364",
        "legacy_meanings_ids": ["1607"],
    },
    89903937: {
        "legacy_word_id": "3906",
        "slug": "annilai",
        "title": "\u0b85\u0ba8\u0bcd\u0ba8\u0bbf\u0bb2\u0bc8",
        "pageid": 7769127,
        "revision_timestamp": "2026-03-20T08:41:52Z",
        "wikitext_sha256": "527c5be08b52b9db426a1da8fb5b143e4faebb310be12375995a4d4392ecefa3",
        "wikitext_sha1": "58fc9a3c1d280567dc7ffd8c1390799e00cd7214",
        "legacy_meanings_ids": ["3376"],
    },
    88382210: {
        "legacy_word_id": "8218",
        "slug": "arikkai",
        "title": "\u0b85\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0bc8",
        "pageid": 9685129,
        "revision_timestamp": "2025-12-05T06:44:33Z",
        "wikitext_sha256": "8bf77bf23d7c241f236575fcff535bc24d71d00287e288ab4d2238f857ccbed8",
        "wikitext_sha1": "5c45d3bf0320891acd5a52e78e1f25cb3c008618",
        "legacy_meanings_ids": ["7031", "7032", "7033"],
    },
    61485513: {
        "legacy_word_id": "28857",
        "slug": "ceppam",
        "title": "\u0b9a\u0bc6\u0baa\u0bcd\u0baa\u0bae\u0bcd",
        "pageid": 7902117,
        "revision_timestamp": "2021-01-04T16:15:52Z",
        "wikitext_sha256": "844ff53b3d33176f07d8a92189b3b08f23ce5cb259fbea9f27581d0e66f1846e",
        "wikitext_sha1": "41cad97af6ea02537aac4b231fda2b2f778c154f",
        "legacy_meanings_ids": ["25949", "25950", "25951", "25952", "25953", "25954", "25955", "25956", "25957", "25958", "25959"],
    },
}

# Pinned official single-page multi-POS Tamil homograph allowlist.
HOMOGRAPH_ALLOWLIST: dict[int, dict[str, Any]] = {
    93647113: {
        "legacy_word_id": "32793",
        "slug": "nanri",
        "title": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf",
        "pageid": 4593930,
        "revision_timestamp": "2026-10-17T21:53:52Z",
        "wikitext_sha256": "d0c85376de17daab66cdce055a36ca1d208dcd0135edfa44856ae31ea6dabbad",
        "wikitext_sha1": "0fcd30dd8b964da923d3b42a2734fdea03a01239",
        "legacy_meanings_ids": ["59633", "59634", "59635"],
        "allow_multiple_pos": True,
    },
}


@dataclass(frozen=True)
class CandidateDatasetSpec:
    """Configuration binding a candidate workspace to its isolated namespace and pin set."""

    key: str
    default_dir: Path
    dataset_id: str
    namespace: str
    allowlist: dict[int, dict[str, Any]]
    structural_kind: str


DATASET_SPECS: dict[str, CandidateDatasetSpec] = {
    "candidate": CandidateDatasetSpec(
        key="candidate",
        default_dir=CANDIDATE_DIR,
        dataset_id=CANDIDATE_DATASET_ID,
        namespace=CANDIDATE_NAMESPACE,
        allowlist=PINNED_ALLOWLIST,
        structural_kind="proposed_wiktionary_candidate",
    ),
    "homograph": CandidateDatasetSpec(
        key="homograph",
        default_dir=HOMOGRAPH_DIR,
        dataset_id=HOMOGRAPH_DATASET_ID,
        namespace=HOMOGRAPH_NAMESPACE,
        allowlist=HOMOGRAPH_ALLOWLIST,
        structural_kind="proposed_wiktionary_homograph_candidate",
    ),
}

POS_HEADING_MAP: dict[str, str] = {
    "===Interjection===": "INTJ",
    "===Noun===": "NOUN",
}

FORBIDDEN_RUNTIME_TEMPLATES = (
    "{{ta-IPA",
    "{{ety",
    "{{com",
    "{{af",
    "{{suf",
    "{{m|",
    "{{syn",
    "{{ta-decl",
    "{{col3",
    "{{ux",
    "{{audio",
)


def _line_offsets(text: str) -> list[tuple[int, str, int, int, int, int]]:
    """Return 1-based line metadata: (line_no, line, char_start, char_end, byte_start, byte_end)."""
    rows: list[tuple[int, str, int, int, int, int]] = []
    char_pos = 0
    byte_pos = 0
    for idx, line in enumerate(text.splitlines(keepends=False), start=1):
        char_end = char_pos + len(line)
        line_bytes = len(line.encode("utf-8"))
        byte_end = byte_pos + line_bytes
        rows.append((idx, line, char_pos, char_end, byte_pos, byte_end))
        newline_chars = 1 if char_end < len(text) else 0
        char_pos = char_end + newline_chars
        byte_pos = byte_end + newline_chars
    return rows


def _unwrap_wikilinks(text: str) -> tuple[str, list[str]]:
    """Replace ``[[target]]`` / ``[[target|display]]`` with visible text, recording raw matches."""
    links = [m.group(0) for m in WIKILINK_RE.finditer(text)]
    unwrapped = WIKILINK_RE.sub(r"\2", text)
    return unwrapped, links


def _parse_sense_line(line_no: int, line: str, c_start: int, c_end: int, b_start: int, b_end: int, ordinal: int, revid: int) -> dict[str, Any]:
    """Parse one allowlisted wikitext sense line while preserving qualifiers and raw provenance."""
    body = line[2:]
    for bad in FORBIDDEN_RUNTIME_TEMPLATES:
        if bad in body:
            raise ValueError(f"Forbidden unpinned template {bad!r} inside sense line for revid={revid}")

    templates_used: list[dict[str, Any]] = []
    transformation_steps: list[str] = []
    pending_reasons: list[str] = ["PENDING_GENUINE_HUMAN_REVIEW"]
    qualifiers: list[dict[str, str]] = []
    component = "definition"
    ambiguity_state = "unknown"

    working = body
    ng_match = NG_TEMPLATE_RE.match(working)
    if ng_match:
        raw_arg = ng_match.group(1)
        templates_used.append({
            "template": "ng",
            "raw_invocation": working,
            "args": [raw_arg],
            "pinned_expansion": False,
        })
        working = raw_arg
        component = "gloss"
        ambiguity_state = "ambiguous"
        transformation_steps.append("unwrap_ng_template_argument")
        pending_reasons.append("NG_TEMPLATE_UNWRAPPED_AND_TRAILING_PUNCTUATION_UNEDITED")

    prefix_parts: list[str] = []
    q_match = QUALIFIER_PREFIX_RE.match(working)
    if q_match:
        q_arg = q_match.group(1)
        raw_inv = f"{{{{q|{q_arg}}}}}"
        templates_used.append({
            "template": "q",
            "raw_invocation": raw_inv,
            "args": [q_arg],
            "pinned_expansion": False,
        })
        meta = QUALIFIER_LABEL_METADATA.get(q_arg, {
            "category": "register",
            "display_label": q_arg,
            "definition": f"Qualifier preserved literally from pinned {raw_inv} template; pending human review.",
        })
        qualifiers.append({
            "code": q_arg,
            "dimension": meta["category"],
            "display_label": meta["display_label"],
            "definition": meta["definition"],
            "raw_template": raw_inv,
        })
        prefix_parts.append(f"({q_arg})")
        working = working[q_match.end():]
        ambiguity_state = "ambiguous"
        transformation_steps.append("preserve_literal_qualifier_prefix")
        pending_reasons.append("QUALIFIER_TEMPLATE_REQUIRES_REVIEW")

    lb_match = LABEL_PREFIX_RE.match(working)
    if lb_match:
        lb_arg = lb_match.group(1)
        raw_inv = f"{{{{lb|ta|{lb_arg}}}}}"
        templates_used.append({
            "template": "lb",
            "raw_invocation": raw_inv,
            "args": ["ta", lb_arg],
            "pinned_expansion": False,
        })
        meta = QUALIFIER_LABEL_METADATA.get(lb_arg, {
            "category": "domain",
            "display_label": lb_arg,
            "definition": f"Label preserved literally from pinned {raw_inv} template; pending human review.",
        })
        qualifiers.append({
            "code": lb_arg,
            "dimension": meta["category"],
            "display_label": meta["display_label"],
            "definition": meta["definition"],
            "raw_template": raw_inv,
        })
        prefix_parts.append(f"({lb_arg})")
        working = working[lb_match.end():]
        ambiguity_state = "ambiguous"
        transformation_steps.append("preserve_literal_label_prefix")
        pending_reasons.append("LABEL_TEMPLATE_REQUIRES_REVIEW")

    if GENERIC_TEMPLATE_RE.search(working):
        raise ValueError(f"Unallowlisted template in sense body for revid={revid}: {working!r}")

    unqualified_text, raw_links = _unwrap_wikilinks(working)
    v1_stripped_text = unqualified_text if qualifiers else None
    candidate_text = f"{' '.join(prefix_parts)} {unqualified_text}" if prefix_parts else unqualified_text
    if raw_links:
        transformation_steps.append("unwrap_wikilink_markup")
        pending_reasons.append("WIKILINK_MARKUP_UNWRAPPED")
    if "," in candidate_text or ";" in candidate_text:
        ambiguity_state = "ambiguous"
        pending_reasons.append("MULTI_GLOSS_OR_COMPOUND_CLAUSE_SENSE")
    if "]]" in body and re.search(r"\]\][A-Za-z]+", body):
        ambiguity_state = "ambiguous"
        pending_reasons.append("POSTFIX_INFLECTION_OUTSIDE_WIKILINK")

    return {
        "ordinal": ordinal,
        "line_number": line_no,
        "char_range": [c_start, c_end],
        "byte_range": [b_start, b_end],
        "raw_line": line,
        "component": component,
        "candidate_text": candidate_text,
        "v1_stripped_text": v1_stripped_text,
        "qualifiers": qualifiers,
        "ambiguity_state": ambiguity_state,
        "templates": templates_used,
        "wikilinks": raw_links,
        "transformation_method": "+".join(transformation_steps) if transformation_steps else "verbatim_sense_line",
        "cleanup_applied": "none_beyond_markup_and_literal_qualifier_preservation",
        "pending_human_review_reasons": sorted(set(pending_reasons)),
    }


def _extract_pinned_revision(
    entry_meta: dict[str, Any],
    snap_dir: Path,
    allowlist: dict[int, dict[str, Any]] = PINNED_ALLOWLIST,
) -> dict[str, Any]:
    """Validate snapshot hashes/pins and extract allowlisted Tamil headword, POS sections, senses, and exclusions."""
    revid = entry_meta["revid"]
    if revid not in allowlist:
        raise ValueError(f"Unpinned revid rejected: {revid!r}")
    pin = allowlist[revid]

    api_path = snap_dir / entry_meta["api_response_file"]
    wt_path = snap_dir / entry_meta["wikitext_file"]
    if not api_path.exists() or not wt_path.exists():
        raise FileNotFoundError(f"Missing checked-in snapshot files for revid={revid}")

    api_bytes = api_path.read_bytes()
    wt_bytes = wt_path.read_bytes()
    api_sha256 = hashlib.sha256(api_bytes).hexdigest()
    wt_sha256 = hashlib.sha256(wt_bytes).hexdigest()
    wt_sha1 = hashlib.sha1(wt_bytes).hexdigest()

    if api_sha256 != entry_meta["api_response_sha256"]:
        raise ValueError(f"API snapshot SHA-256 mismatch for revid={revid}")
    if wt_sha256 != entry_meta["wikitext_sha256"] or wt_sha256 != pin["wikitext_sha256"]:
        raise ValueError(f"Wikitext SHA-256 mismatch for revid={revid}")
    if wt_sha1 != pin["wikitext_sha1"]:
        raise ValueError(f"Wikitext SHA-1 mismatch for revid={revid}")

    api_obj = json.loads(api_bytes.decode("utf-8"))
    pages = api_obj.get("query", {}).get("pages", [])
    if len(pages) != 1:
        raise ValueError(f"Expected 1 page in API snapshot for revid={revid}")
    page = pages[0]
    revs = [r for r in page.get("revisions", []) if r.get("revid") == revid]
    if len(revs) != 1:
        raise ValueError(f"Expected exact pinned revision revid={revid} in API snapshot")
    rev = revs[0]

    api_wt = rev["slots"]["main"]["content"]
    wt_text = wt_bytes.decode("utf-8")
    if api_wt != wt_text:
        raise ValueError(f"API slot wikitext diverges from checked-in .wikitext for revid={revid}")
    if (
        page.get("pageid") != pin["pageid"]
        or page.get("title") != pin["title"]
        or rev.get("revid") != revid
        or rev.get("timestamp") != pin["revision_timestamp"]
        or ("sha1" in rev and rev["sha1"] != pin["wikitext_sha1"])
        or entry_meta.get("legacy_word_id") != pin["legacy_word_id"]
    ):
        raise ValueError(f"Pinned revision metadata mismatch for revid={revid}")

    lines = _line_offsets(wt_text)
    if not lines or lines[0][1] != "==Tamil==":
        raise ValueError(f"Expected ==Tamil== language header at line 1 for revid={revid}")

    in_tamil = True
    in_pos = False
    allow_multiple_pos = bool(pin.get("allow_multiple_pos", False))
    pos_sections: list[dict[str, Any]] = []
    current_pos: dict[str, Any] | None = None
    exclusions: list[dict[str, Any]] = []

    for line_no, line, c_start, c_end, b_start, b_end in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("==") and not stripped.startswith("==="):
            in_tamil = stripped == "==Tamil=="
            in_pos = False
            current_pos = None
            exclusions.append({
                "line_number": line_no,
                "char_range": [c_start, c_end],
                "byte_range": [b_start, b_end],
                "raw_line": line,
                "reason_code": "NON_TAMIL_SECTION_EXCLUDED",
            })
            continue
        if not in_tamil:
            exclusions.append({
                "line_number": line_no,
                "char_range": [c_start, c_end],
                "byte_range": [b_start, b_end],
                "raw_line": line,
                "reason_code": "OUT_OF_LANGUAGE_SCOPE_EXCLUDED",
            })
            continue

        if stripped in POS_HEADING_MAP:
            if pos_sections and not allow_multiple_pos:
                raise ValueError(f"Multiple POS headings in single-entry allowlist for revid={revid}")
            current_pos = {
                "pos_heading": stripped,
                "pos_code": POS_HEADING_MAP[stripped],
                "pos_line": {
                    "line_number": line_no,
                    "raw_line": line,
                    "char_range": [c_start, c_end],
                    "byte_range": [b_start, b_end],
                },
                "senses": [],
            }
            pos_sections.append(current_pos)
            in_pos = True
            continue

        if stripped.startswith("==="):
            in_pos = False
            current_pos = None
            reason = "SECTION_EXCLUDED_UNPINNED_OR_NON_DEFINITION"
            if stripped == "===Pronunciation===":
                reason = "PRONUNCIATION_SECTION_EXCLUDED_UNPINNED_TA_IPA"
            elif stripped == "===Etymology===":
                reason = "ETYMOLOGY_SECTION_EXCLUDED"
            elif stripped == "===References===":
                reason = "REFERENCES_SECTION_EXCLUDED"
            elif stripped == "===See also===":
                reason = "SEE_ALSO_SECTION_EXCLUDED"
            elif stripped == "===Alternative forms===":
                reason = "ALTERNATIVE_FORMS_SECTION_EXCLUDED"
            elif stripped.startswith("===="):
                reason = "SUBSECTION_EXCLUDED"
            exclusions.append({
                "line_number": line_no,
                "char_range": [c_start, c_end],
                "byte_range": [b_start, b_end],
                "raw_line": line,
                "reason_code": reason,
            })
            continue

        if in_pos and current_pos is not None and line.startswith("# ") and not line.startswith("#:"):
            current_pos["senses"].append(
                _parse_sense_line(
                    line_no, line, c_start, c_end, b_start, b_end, len(current_pos["senses"]) + 1, revid
                )
            )
            continue

        reason = "NON_DEFINITION_LINE_EXCLUDED"
        if "{{ta-IPA" in stripped:
            reason = "TEMPLATE_GENERATED_TA_IPA_EXCLUDED_UNPINNED"
        elif stripped.startswith("#: {{ux"):
            reason = "USAGE_EXAMPLE_TEMPLATE_EXCLUDED"
        elif stripped.startswith("#: {{syn"):
            reason = "SYNONYM_TEMPLATE_EXCLUDED"
        elif stripped.startswith("#* {{quote-"):
            reason = "QUOTATION_TEMPLATE_EXCLUDED"
        elif stripped.startswith("{{ta-decl"):
            reason = "DECLENSION_TEMPLATE_EXCLUDED"
        elif stripped.startswith("{{C|") or stripped.startswith("{{cln|"):
            reason = "CATEGORY_TEMPLATE_EXCLUDED"
        elif stripped.startswith("{{col"):
            reason = "DERIVED_TERMS_TEMPLATE_EXCLUDED"
        elif stripped in {"{{ta-interj}}", "{{ta-noun}}"}:
            reason = "HEADWORD_TEMPLATE_IGNORED_UNPINNED"
        elif stripped.startswith("{{phrasebook|"):
            reason = "PHRASEBOOK_TEMPLATE_EXCLUDED"
        elif stripped == "{{reflist}}":
            reason = "REFERENCE_TEMPLATE_EXCLUDED"
        exclusions.append({
            "line_number": line_no,
            "char_range": [c_start, c_end],
            "byte_range": [b_start, b_end],
            "raw_line": line,
            "reason_code": reason,
        })

    if not pos_sections:
        raise ValueError(f"Missing allowlisted POS heading for revid={revid}")
    for section in pos_sections:
        if not section["senses"]:
            raise ValueError(f"No senses extracted for revid={revid} heading={section['pos_heading']}")

    first = pos_sections[0]
    return {
        "entry_meta": entry_meta,
        "pin": pin,
        "page": page,
        "revision": rev,
        "wikitext": wt_text,
        "wikitext_sha256": wt_sha256,
        "wikitext_bytes": len(wt_bytes),
        "api_response_sha256": api_sha256,
        "api_response_bytes": len(api_bytes),
        "pos_sections": pos_sections,
        "pos_heading": first["pos_heading"],
        "pos_code": first["pos_code"],
        "pos_line": first["pos_line"],
        "senses": [s for sec in pos_sections for s in sec["senses"]],
        "exclusions": exclusions,
    }


def _check_unicode_assertions(assertions: list[dict[str, Any]], context: str) -> None:
    """Validate Tamil text claims through the native Rust Unicode inspection path."""
    for assertion in assertions:
        if assertion["property_code"] in {"headword", "gloss", "definition"}:
            text = str(assertion["value_json"])
            inspected = native_inspect(text)
            if not inspected["is_nfc"]:
                raise ValueError(f"{context}: non-NFC string in {assertion['assertion_id']}")
            findings = unicode_findings(assertion)
            if findings:
                raise ValueError(f"{context}: unexpected Unicode finding in {assertion['assertion_id']}: {findings}")


def _resolve_spec(candidate_dir: Path, dataset: str | None = None) -> CandidateDatasetSpec:
    """Resolve the candidate dataset specification from explicit CLI name or snapshot manifest."""
    if dataset is not None:
        if dataset not in DATASET_SPECS:
            raise ValueError(f"Unknown candidate dataset {dataset!r}")
        return DATASET_SPECS[dataset]
    manifest_path = candidate_dir / "snapshots" / "snapshots_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        revids = {entry.get("revid") for entry in manifest.get("entries", [])}
        if revids & set(HOMOGRAPH_ALLOWLIST):
            return DATASET_SPECS["homograph"]
    return DATASET_SPECS["candidate"]


def build_candidate_workspace(
    candidate_dir: Path = CANDIDATE_DIR,
    *,
    dataset: str | None = None,
) -> dict[str, Any]:
    """Deterministically project checked-in snapshots into all 21 workspace tables."""
    candidate_dir = safe_output(candidate_dir)
    safe_output(candidate_dir, ROOT / "data/curation/tamil-lexicon")
    spec = _resolve_spec(candidate_dir, dataset)
    ns = spec.namespace
    allowlist = spec.allowlist
    dataset_version = "2" if spec.key == "candidate" else "1"

    snap_dir = candidate_dir / "snapshots"
    manifest_path = snap_dir / "snapshots_manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    manifest = json.loads(manifest_bytes.decode("utf-8"))

    extracted_entries = [_extract_pinned_revision(item, snap_dir, allowlist=allowlist) for item in manifest["entries"]]
    if len(extracted_entries) != len(allowlist):
        raise ValueError(f"Expected {len(allowlist)} snapshot pages, got {len(extracted_entries)}")

    tables: dict[str, list[dict[str, Any]]] = {name: [] for name in WORKSPACE_TABLES}
    provenance_entries: list[dict[str, Any]] = []
    exclusion_entries: list[dict[str, Any]] = []
    seen_labels: set[tuple[str, str, str]] = set()

    def add_identity(kind: str, key: str) -> str:
        prefix = {
            "entry": "ent",
            "form": "frm",
            "sense": "sen",
            "text": "txt",
            "relation": "rel",
            "assertion": "ast",
        }[kind]
        eid = allocate_id(prefix, ns, key)
        tables["identities"].append({
            "entity_id": eid,
            "kind": kind,
            "allocation_key": key,
            "lifecycle": "active",
            "identity_decision_id": None,
        })
        return eid

    def add_claim_and_review(
        *,
        rec_id: str,
        src_id: str,
        subject_kind: str,
        subject_id: str,
        property_code: str,
        value: Any,
        origin: str,
        fidelity: str,
        ambiguity: str,
        locator: str,
        decision_outcome: str,
        decision_note: str,
        issue_codes: list[str],
        claim_key_suffix: str = "",
        method_version: str = METHOD_VERSION,
        extraction_version: str = EXTRACTION_VERSION,
        predecessor_decision_id: str | None = None,
    ) -> tuple[str, str]:
        aid = allocate_id(
            "ast",
            ns,
            f"{rec_id}:claim:{subject_kind}:{subject_id}:{property_code}{claim_key_suffix}",
        )
        assertion = {
            "assertion_id": aid,
            "subject_kind": subject_kind,
            "subject_id": subject_id,
            "property_code": property_code,
            "value_state": "known",
            "value_json": value,
            "origin": origin,
            "source_fidelity_state": fidelity,
            "ambiguity_state": ambiguity,
            "algorithm_reference": None if origin == "verbatim_source" else METHOD_NAME,
            "convention_reference": None,
            "imported_status_json": None,
            "imported_confidence_json": None,
            "claim_revision_sha256": "0" * 64,
        }
        assertion["claim_revision_sha256"] = claim_revision(assertion)
        tables["assertions"].append(assertion)

        ev_row = {
            "assertion_id": aid,
            "source_id": src_id,
            "source_record_id": rec_id,
            "locator_json": locator,
            "evidence_role": "supports",
            "extraction_version": extraction_version,
            "extraction_sha256": hashlib.sha256(
                json_text({"locator": locator, "value": value, "property_code": property_code}).encode("utf-8")
            ).hexdigest(),
        }
        tables["evidence"].append(ev_row)

        did = allocate_id("dec", ns, f"{aid}:pending-initial")
        tables["decisions"].append({
            "decision_id": did,
            "assertion_id": aid,
            "assertion_revision_sha256": assertion["claim_revision_sha256"],
            "evidence_bundle_sha256": evidence_hash([ev_row]),
            "outcome": decision_outcome,
            "actor_type": "automated",
            "actor_id": None,
            "method_version": method_version,
            "decision_date": RETRIEVAL_DATE,
            "note_json": decision_note,
            "predecessor_decision_id": predecessor_decision_id,
        })

        for code in issue_codes:
            tables["findings"].append({
                "finding_id": allocate_id("fnd", ns, f"{aid}:{code}"),
                "record_id": rec_id,
                "assertion_id": aid,
                "issue_code": code,
                "severity": "warning",
                "scalar_positions": [],
                "status": "open",
                "resolution_reason_json": None,
            })
        return aid, did

    for ext in extracted_entries:
        meta = ext["entry_meta"]
        pin = ext["pin"]
        revid = meta["revid"]
        legacy_id = pin["legacy_word_id"]

        snap_json_id = allocate_id("snp", ns, f"snapshot:json:{revid}")
        snap_wt_id = allocate_id("snp", ns, f"snapshot:wikitext:{revid}")
        tables["snapshots"].append({
            "snapshot_id": snap_json_id,
            "dataset_id": spec.dataset_id,
            "relative_path": f"snapshots/{meta['api_response_file']}",
            "byte_length": ext["api_response_bytes"],
            "sha256": ext["api_response_sha256"],
            "media_type": "application/json",
            "logical_row_count": None,
        })
        tables["snapshots"].append({
            "snapshot_id": snap_wt_id,
            "dataset_id": spec.dataset_id,
            "relative_path": f"snapshots/{meta['wikitext_file']}",
            "byte_length": ext["wikitext_bytes"],
            "sha256": ext["wikitext_sha256"],
            "media_type": "text/plain; charset=utf-8",
            "logical_row_count": len(ext["wikitext"].splitlines()),
        })

        src_id = allocate_id("src", ns, f"enwiktionary:page:{pin['pageid']}:rev:{revid}")
        tables["sources"].append({
            "source_id": src_id,
            "label_json": f"enwiktionary_rev_{revid}_{pin['slug']}",
            "publication_json": "English Wiktionary (Wikimedia Foundation)",
            "url_json": meta["permalink_url"],
            "edition_json": f"pageid={pin['pageid']};oldid={revid};timestamp={pin['revision_timestamp']}",
            "locator_json": json_text({
                "pageid": pin["pageid"],
                "revid": revid,
                "timestamp": pin["revision_timestamp"],
                "wikitext_sha256": ext["wikitext_sha256"],
                "history_url": meta["history_url"],
                "api_url": meta["api_url"],
            }),
            "snapshot_id": snap_json_id,
            "retrieval_date_state": "known",
            "retrieval_date_json": RETRIEVAL_DATE,
            "extraction_method": METHOD_NAME,
            "extraction_version": EXTRACTION_VERSION,
            "evidence_verification_state": "verified",
            "reuse_basis_json": "CC-BY-SA-4.0 (proposed; upstream dual-licensed CC-BY-SA-4.0/GFDL; ShareAlike & attribution policy clearance pending L3 review)",
            "reuse_state": "restricted",
            "attribution_text_json": f"English Wiktionary contributors, '{pin['title']}' (oldid {revid}, {pin['revision_timestamp']}), CC BY-SA 4.0; history: {meta['history_url']}",
            "attribution_reference_json": "notices/ATTRIBUTION_AND_LICENSE.md",
        })

        rec_id = allocate_id("rec", ns, f"enwiktionary:rev:{revid}:wikitext")
        wt_lines = ext["wikitext"].splitlines()
        tables["source_records"].append({
            "record_id": rec_id,
            "snapshot_id": snap_wt_id,
            "ordinal": 2,
            "physical_line_start": 1,
            "physical_line_end": max(1, len(wt_lines)),
            "legacy_key_json": json_text({
                "legacy_word_id": legacy_id,
                "legacy_meanings_ids": pin["legacy_meanings_ids"],
                "enwikt_pageid": pin["pageid"],
                "enwikt_revid": revid,
            }),
            "raw_row_sha256": ext["wikitext_sha256"],
        })

        allow_multi = bool(pin.get("allow_multiple_pos", False))
        for sec_idx, sec in enumerate(ext["pos_sections"], start=1):
            if allow_multi:
                entry_key = f"enwiktionary:page:{pin['pageid']}:rev:{revid}:tam:{sec['pos_code'].lower()}:{sec_idx}"
            else:
                entry_key = f"enwiktionary:page:{pin['pageid']}:rev:{revid}:tam"
            entry_id = add_identity("entry", entry_key)
            form_id = add_identity("form", f"{entry_key}:canonical-written")

            headword_aid, _ = add_claim_and_review(
                rec_id=rec_id,
                src_id=src_id,
                subject_kind="form",
                subject_id=form_id,
                property_code="headword",
                value=pin["title"],
                origin="verbatim_source",
                fidelity="verified",
                ambiguity="unambiguous",
                locator=f"pageid={pin['pageid']}&oldid={revid}&field=page.title",
                decision_outcome="pending",
                decision_note="Pinned official page.title verified against API; pending human curation approval.",
                issue_codes=[],
            )

            tables["forms"].append({
                "form_id": form_id,
                "entry_id": entry_id,
                "representation": "written",
                "role": "canonical",
                "text_assertion_id": headword_aid,
                "convention_assertion_id": None,
            })

            pos_aid, _ = add_claim_and_review(
                rec_id=rec_id,
                src_id=src_id,
                subject_kind="entry",
                subject_id=entry_id,
                property_code="part_of_speech",
                value=sec["pos_code"],
                origin="verbatim_source",
                fidelity="changed",
                ambiguity="ambiguous",
                locator=json_text({
                    "revid": revid,
                    "line_number": sec["pos_line"]["line_number"],
                    "char_range": sec["pos_line"]["char_range"],
                    "byte_range": sec["pos_line"]["byte_range"],
                    "raw_heading": sec["pos_heading"],
                    "mapped_pos": sec["pos_code"],
                }),
                decision_outcome="needs_review",
                decision_note=f"Proposed source claim mapping {sec['pos_heading']} -> {sec['pos_code']}; pending genuine human review.",
                issue_codes=["POS_HEADING_MAPPING_REQUIRES_REVIEW"],
            )

            tables["entries"].append({
                "entry_id": entry_id,
                "language_id": "tam",
                "variety_id": None,
                "canonical_form_id": form_id,
                "pos_assertion_id": pos_aid,
                "structural_kind": spec.structural_kind,
                "revision": hashlib.sha256(
                    json_text({"entry_id": entry_id, "revid": revid, "headword": pin["title"], "pos": sec["pos_code"]}).encode("utf-8")
                ).hexdigest(),
            })

            tables["record_targets"].append({
                "record_id": rec_id,
                "entity_id": entry_id,
                "target_role": f"candidate_entry_{sec['pos_code'].lower()}" if allow_multi else "candidate_entry",
            })

            for dim in ["region", "register", "domain", "social_usage", "period", "grammar_system"]:
                tables["scopes"].append({
                    "subject_kind": "entry",
                    "subject_id": entry_id,
                    "dimension": dim,
                    "state": "unknown",
                    "label_code": None,
                    "supporting_assertion_id": None,
                    "decision_id": None,
                })

            sense_prov_list: list[dict[str, Any]] = []
            for sense in sec["senses"]:
                sense_key = f"{entry_key}:sense:{sense['ordinal']}"
                sense_id = add_identity("sense", sense_key)
                tables["senses"].append({
                    "sense_id": sense_id,
                    "entry_id": entry_id,
                    "display_order": sense["ordinal"],
                    "parent_sense_id": None,
                })
                tables["record_targets"].append({
                    "record_id": rec_id,
                    "entity_id": sense_id,
                    "target_role": (
                        f"candidate_sense_{sec['pos_code'].lower()}_{sense['ordinal']}"
                        if allow_multi
                        else f"candidate_sense_{sense['ordinal']}"
                    ),
                })

                text_key = f"{sense_key}:{sense['component']}"
                text_id = add_identity("text", text_key)
                sense_locator = json_text({
                    "revid": revid,
                    "line_number": sense["line_number"],
                    "char_range": sense["char_range"],
                    "byte_range": sense["byte_range"],
                    "transformation_method": sense["transformation_method"],
                    "templates": [t["template"] for t in sense["templates"]],
                })

                if sense["v1_stripped_text"] is not None:
                    v1_locator = json_text({
                        "revid": revid,
                        "line_number": sense["line_number"],
                        "char_range": sense["char_range"],
                        "byte_range": sense["byte_range"],
                        "transformation_method": "+".join(
                            (
                                ["strip_unpinned_qualifier_template_for_review"]
                                if any(q["raw_template"].startswith("{{q|") for q in sense["qualifiers"])
                                else ["strip_unpinned_label_template_for_review"]
                            )
                            + (["unwrap_wikilink_markup"] if sense["wikilinks"] else [])
                        ),
                        "templates": [t["template"] for t in sense["templates"]],
                    })
                    v1_aid, v1_dec_id = add_claim_and_review(
                        rec_id=rec_id,
                        src_id=src_id,
                        subject_kind="text",
                        subject_id=text_id,
                        property_code=sense["component"],
                        value=sense["v1_stripped_text"],
                        origin="derived",
                        fidelity="changed",
                        ambiguity="ambiguous",
                        locator=v1_locator,
                        decision_outcome="needs_review",
                        decision_note=(
                            f"Wikitext line {sense['line_number']} unwrapped in v1 with qualifier/label stripped; "
                            "superseded by wiktionary-candidate-v2 literal-qualifier preservation."
                        ),
                        issue_codes=[],
                        method_version=PRIOR_METHOD_VERSION,
                        extraction_version=PRIOR_EXTRACTION_VERSION,
                    )
                    v1_rev = tables["assertions"][-1]["claim_revision_sha256"]
                    v1_ev_hash = tables["decisions"][-1]["evidence_bundle_sha256"]
                    tables["decisions"].append({
                        "decision_id": allocate_id("dec", ns, f"{v1_aid}:superseded-v2"),
                        "assertion_id": v1_aid,
                        "assertion_revision_sha256": v1_rev,
                        "evidence_bundle_sha256": v1_ev_hash,
                        "outcome": "rejected",
                        "actor_type": "automated",
                        "actor_id": None,
                        "method_version": METHOD_VERSION,
                        "decision_date": RETRIEVAL_DATE,
                        "note_json": (
                            f"Superseded in {METHOD_VERSION}: source qualifier/label template was stripped in v1; "
                            "literal qualifier preserved in replacement assertion."
                        ),
                        "predecessor_decision_id": v1_dec_id,
                    })
                    text_aid, text_dec_id = add_claim_and_review(
                        rec_id=rec_id,
                        src_id=src_id,
                        subject_kind="text",
                        subject_id=text_id,
                        property_code=sense["component"],
                        value=sense["candidate_text"],
                        origin="correction",
                        fidelity="changed",
                        ambiguity=sense["ambiguity_state"],
                        locator=sense_locator,
                        decision_outcome="needs_review",
                        decision_note=(
                            f"Wikitext line {sense['line_number']} corrected via {sense['transformation_method']} "
                            "to preserve literal qualifier; pending genuine human review."
                        ),
                        issue_codes=sense["pending_human_review_reasons"],
                        claim_key_suffix=":v2",
                    )
                    tables["changes"].append({
                        "change_id": allocate_id("chg", ns, f"{text_id}:v1-to-v2"),
                        "subject_id": text_id,
                        "old_assertion_id": v1_aid,
                        "new_assertion_id": text_aid,
                        "reason_json": (
                            f"Preserved raw qualifier/label template literally in {METHOD_VERSION} "
                            "after v1 stripped source scope."
                        ),
                        "evidence_reference": text_aid,
                        "decision_id": text_dec_id,
                        "inverse_change_id": None,
                    })
                else:
                    text_aid, _ = add_claim_and_review(
                        rec_id=rec_id,
                        src_id=src_id,
                        subject_kind="text",
                        subject_id=text_id,
                        property_code=sense["component"],
                        value=sense["candidate_text"],
                        origin="derived",
                        fidelity="changed",
                        ambiguity=sense["ambiguity_state"],
                        locator=sense_locator,
                        decision_outcome="needs_review",
                        decision_note=(
                            f"Wikitext line {sense['line_number']} unwrapped via {sense['transformation_method']}; "
                            "pending genuine human review."
                        ),
                        issue_codes=sense["pending_human_review_reasons"],
                    )

                tables["texts"].append({
                    "text_id": text_id,
                    "owner_kind": "sense",
                    "owner_id": sense_id,
                    "component": sense["component"],
                    "language_id": "eng",
                    "text_assertion_id": text_aid,
                    "paired_translation_id": None,
                    "cited_source_locator_json": sense_locator,
                })

                qual_prov: list[dict[str, Any]] = []
                for qual in sense["qualifiers"]:
                    scope_aid, scope_dec_id = add_claim_and_review(
                        rec_id=rec_id,
                        src_id=src_id,
                        subject_kind="sense",
                        subject_id=sense_id,
                        property_code=f"scope_proposal_{qual['dimension']}",
                        value={
                            "dimension": qual["dimension"],
                            "label_code": qual["code"],
                            "raw_template": qual["raw_template"],
                        },
                        origin="derived",
                        fidelity="changed",
                        ambiguity="ambiguous",
                        locator=sense_locator,
                        decision_outcome="needs_review",
                        decision_note=(
                            f"Pending scope proposal {qual['dimension']}={qual['code']!r} from "
                            f"{qual['raw_template']}; requires human review before attested promotion."
                        ),
                        issue_codes=["SCOPE_QUALIFIER_REQUIRES_REVIEW"],
                    )
                    lbl_key = (LABEL_REGISTRY_ID, "1", qual["code"])
                    if lbl_key not in seen_labels:
                        seen_labels.add(lbl_key)
                        tables["labels"].append({
                            "registry_id": LABEL_REGISTRY_ID,
                            "registry_version": "1",
                            "code": qual["code"],
                            "category": qual["dimension"],
                            "display_label_json": qual["display_label"],
                            "definition_json": qual["definition"],
                            "evidence_reference": scope_aid,
                            "parent_code": None,
                        })
                    tables["scopes"].append({
                        "subject_kind": "sense",
                        "subject_id": sense_id,
                        "dimension": qual["dimension"],
                        "state": "unknown",
                        "label_code": None,
                        "supporting_assertion_id": None,
                        "decision_id": None,
                    })
                    qual_prov.append({
                        **qual,
                        "scope_proposal_assertion_id": scope_aid,
                        "scope_proposal_decision_id": scope_dec_id,
                        "scope_state_until_reviewed": "unknown",
                    })

                sense_prov_list.append({
                    "sense_id": sense_id,
                    "text_id": text_id,
                    "text_assertion_id": text_aid,
                    **{k: v for k, v in sense.items() if k != "qualifiers"},
                    "qualifiers": qual_prov,
                })

            provenance_entries.append({
                "legacy_word_id": legacy_id,
                "page_title": pin["title"],
                "pageid": pin["pageid"],
                "revid": revid,
                "revision_timestamp": pin["revision_timestamp"],
                "wikitext_sha256": ext["wikitext_sha256"],
                "source_id": src_id,
                "record_id": rec_id,
                "entry_id": entry_id,
                "form_id": form_id,
                "headword_assertion_id": headword_aid,
                "pos_assertion_id": pos_aid,
                "pos_heading": sec["pos_heading"],
                "pos_code": sec["pos_code"],
                "pos_line": sec["pos_line"],
                "senses": sense_prov_list,
            })

        rec_findings = [f for f in tables["findings"] if f["record_id"] == rec_id]
        tables["dispositions"].append({
            "record_id": rec_id,
            "disposition": "mapped",
            "structural_state": "pending",
            "reason_code": "CANDIDATE_WIKTIONARY_PINNED_EXTRACTION",
            "note_json": (
                f"Mapped {len(ext['senses'])} literal sense lines across {len(ext['pos_sections'])} POS section(s) "
                f"from pinned enwiktionary revid={revid} (excluded {len(ext['exclusions'])} non-definition/unpinned lines); "
                "all claims pending human review."
            ),
            "finding_set_sha256": hashlib.sha256(json_text(sorted(rec_findings, key=json_text)).encode("utf-8")).hexdigest(),
            "method": METHOD_NAME,
            "method_version": METHOD_VERSION,
        })

        exclusion_entries.append({
            "legacy_word_id": legacy_id,
            "page_title": pin["title"],
            "revid": revid,
            "excluded_wikitext_lines": ext["exclusions"],
            "excluded_legacy_unverified_claims": [
                "phonetic_transcription / {{ta-IPA}} (Module:ta-IPA unpinned by oldid; known historical drift)",
                "etymology ({{ety}}, {{com}}, {{af}}, {{suf}}, {{m}}) & synthetic proto-forms (*aṯ-V-, *PDr-2747)",
                "DEDR citations (DEDR 314, DEDR 2747) & external reference templates ({{R:TAL}}, {{R:Cre-A 1992}}, {{R:Winslow}})",
                "usage examples ({{ux}}), quotations ({{quote-book}}), audio ({{audio}}), synonyms ({{syn}}), declension ({{ta-decl}}), derived terms ({{col}}/{{col3}}), categories ({{C}}/{{cln}})",
                "unverified legacy grammar/domain/region classifications from external snapshot",
            ],
        })

    _check_unicode_assertions(tables["assertions"], spec.dataset_id)

    # Check every existing table before writing any table. A rebuild must never
    # reset later editorial decisions or corrections to the generated proposals.
    for name in WORKSPACE_TABLES:
        existing = candidate_dir / f"{name}.csv"
        if existing.exists():
            actual = sorted(json_text(row) for row in read_rows(existing, name))
            expected = sorted(json_text(row) for row in tables[name])
            if actual != expected:
                raise ValueError(f"Conflicting candidate edits; rebuild refused: {name}.csv")

    for name in WORKSPACE_TABLES:
        write_rows(candidate_dir / f"{name}.csv", name, tables[name], source_root=snap_dir)

    dataset_toml = "\n".join([
        "schema_version = 1",
        f'dataset_id = "{spec.dataset_id}"',
        f'dataset_version = "{dataset_version}"',
        f'id_namespace = "{ns}"',
        'text_codec = "json-string-utf8-v1"',
        "registry_version = 1",
        f'transformation_version = "{EXTRACTION_VERSION}"',
        f'snapshots_manifest_sha256 = "{manifest_sha256}"',
        "",
    ])
    (candidate_dir / "dataset.toml").write_text(dataset_toml, encoding="utf-8", newline="\n")

    prov_dir = candidate_dir / "provenance"
    prov_dir.mkdir(parents=True, exist_ok=True)
    (prov_dir / "extraction_provenance.json").write_text(
        data_json({
            "schema": "wiktionary-candidate-provenance-v1",
            "entry_count": len(provenance_entries),
            "sense_count": sum(len(e["senses"]) for e in provenance_entries),
            "entries": provenance_entries,
        }) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (prov_dir / "exclusions.json").write_text(
        json.dumps(
            {
                "schema": "wiktionary-candidate-exclusions-v1",
                "entries": exclusion_entries,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (prov_dir / "schema_gaps.json").write_text(
        json.dumps(
            {
                "schema": "wiktionary-candidate-schema-gaps-v1",
                "gaps": [
                    {
                        "id": "GAP_SOURCE_RECORDS_NON_CSV_ORDINAL",
                        "table": "source_records",
                        "description": (
                            "intake.schema.json enforces ordinal >= 2 (assuming line 1 CSV header) and unique "
                            "(snapshot_id, ordinal). Single-page wikitext snapshots have no CSV header, so ordinal=2 "
                            "is recorded for the whole pinned wikitext revision file while line spans record 1..N."
                        ),
                    },
                    {
                        "id": "GAP_SOURCES_NO_DEDICATED_REVID_PAGEID_COLUMNS",
                        "table": "sources",
                        "description": (
                            "intake.schema.json has no dedicated columns for MediaWiki pageid, revid, revision_timestamp, "
                            "wikitext_sha256, permalink_url, history_url, or dual-license notice (GFDL). These are "
                            "stored deterministically in edition_json / locator_json and snapshots/snapshots_manifest.json."
                        ),
                    },
                    {
                        "id": "GAP_TEXTS_ASSERTIONS_NO_SPAN_OR_TEMPLATE_ARGS_COLUMNS",
                        "table": "texts/assertions",
                        "description": (
                            "lexical.schema.json/review.schema.json have no dedicated columns for raw wikitext "
                            "byte/char ranges, template names (ng/q/lb), or wikilink unwrapping transforms. These "
                            "are preserved in cited_source_locator_json, evidence.locator_json, and "
                            "provenance/extraction_provenance.json."
                        ),
                    },
                    {
                        "id": "GAP_RELEASE_GUARD_REQUIRES_CANONICAL_OR_ACCEPTED_PACK",
                        "table": "pack_members/decisions",
                        "description": (
                            "release_guard blocks L3 promotion when eligible_assertions == 0. Pending candidate "
                            "deliberately keeps accepted decisions == 0 and reuse_state == 'restricted' pending "
                            "human review and CC-BY-SA-4.0 pack policy clearance."
                        ),
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    try:
        candidate_rel = str(candidate_dir.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        candidate_rel = str(candidate_dir).replace("\\", "/")

    return {
        "candidate_dir": candidate_rel,
        "entry_count": len(tables["entries"]),
        "sense_count": len(tables["senses"]),
        "assertion_count": len(tables["assertions"]),
        "finding_count": len(tables["findings"]),
        "accepted_decisions": 0,
    }


def _verify_frozen_originals() -> int:
    """Verify the 12 frozen canonical Tamil Lexicon original files against MANIFEST.json."""
    manifest_data = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    if len(manifest_data) != 12:
        raise ValueError(f"Expected 12 original source entries, got {len(manifest_data)}")
    for file_entry in manifest_data:
        rel = file_entry["file"]
        src_path = ROOT / "data/sources/tamil-lexicon" / rel
        if src_path.stat().st_size != file_entry["bytes"]:
            raise ValueError(f"Original source byte length mismatch: {rel}")
        actual = digest(src_path)
        if actual != file_entry["sha256"]:
            raise ValueError(f"Original source SHA-256 mismatch: {rel}")
    return len(manifest_data)


def _verify_license_notices(notices_dir: Path) -> dict[str, dict[str, Any]]:
    """Verify pinned Wikimedia ToU, Wiktionary:Copyrights, and CC-BY-SA-4.0 notice files."""
    if not notices_dir.is_dir():
        raise ValueError(f"Missing notices directory: {notices_dir}")
    attr_md = notices_dir / "ATTRIBUTION_AND_LICENSE.md"
    if not attr_md.is_file() or not attr_md.read_text(encoding="utf-8").strip():
        raise ValueError(f"Missing or empty attribution notice: {attr_md}")

    verified: dict[str, dict[str, Any]] = {}
    for filename, req in PINNED_NOTICE_REQUIREMENTS.items():
        path = notices_dir / filename
        if not path.is_file():
            raise ValueError(f"Missing pinned license notice file: {path}")
        actual_sha = digest(path)
        if actual_sha != req["sha256"]:
            raise ValueError(
                f"Notice digest mismatch for {filename}: expected {req['sha256']}, got {actual_sha}"
            )
        if filename.endswith(".json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            pages = payload.get("query", {}).get("pages", [])
            if not pages:
                raise ValueError(f"Invalid Wikimedia API notice payload in {filename}: missing query.pages")
            page = pages[0]
            revs = page.get("revisions", [])
            if not revs:
                raise ValueError(f"Invalid Wikimedia API notice payload in {filename}: missing revisions")
            rev = revs[0]
            if page.get("pageid") != req["pageid"] or rev.get("revid") != req["revid"]:
                raise ValueError(
                    f"Pinned notice revision mismatch in {filename}: pageid={page.get('pageid')} revid={rev.get('revid')}"
                )
            if rev.get("timestamp") != req["timestamp"]:
                raise ValueError(
                    f"Pinned notice timestamp mismatch in {filename}: {rev.get('timestamp')} != {req['timestamp']}"
                )
        else:
            text = path.read_text(encoding="utf-8")
            if req["required_text"] not in text:
                raise ValueError(f"License notice {filename} missing required text {req['required_text']!r}")

        verified[filename] = {
            "sha256": actual_sha,
            "bytes": path.stat().st_size,
        }
    return verified


def _validate_approval_receipt(
    receipt_path: Path,
    packet_path: Path,
    assertions: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Validate an immutable human review receipt against the review packet, claims, and evidence."""
    if not receipt_path.is_file():
        raise ValueError(f"Missing approval receipt: {receipt_path}")
    if not packet_path.is_file():
        raise ValueError(f"Missing review packet: {packet_path}")

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    actual_packet_sha = digest(packet_path)
    if receipt.get("review_packet_sha256") != actual_packet_sha:
        raise ValueError(
            f"Approval receipt review_packet_sha256 mismatch: {receipt.get('review_packet_sha256')} != {actual_packet_sha}"
        )

    if receipt.get("actor_type") != "human":
        raise ValueError(f"Approval receipt requires actor_type='human', got {receipt.get('actor_type')!r}")
    reviewer_id = receipt.get("reviewer_id")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        raise ValueError(f"Approval receipt requires non-empty reviewer_id, got {reviewer_id!r}")
    decision_date = receipt.get("decision_date")
    if not isinstance(decision_date, str):
        raise ValueError(f"Approval receipt missing decision_date: {decision_date!r}")
    date.fromisoformat(decision_date)

    policy = receipt.get("approved_policy")
    if not isinstance(policy, str) or "CC-BY-SA-4.0" not in policy:
        raise ValueError(f"Approval receipt approved_policy must authorize CC-BY-SA-4.0 data pack, got {policy!r}")
    if receipt.get("pack_policy_response_verbatim") != "Approve separate CC data packs":
        raise ValueError(
            f"Approval receipt pack_policy_response_verbatim unexpected: {receipt.get('pack_policy_response_verbatim')!r}"
        )
    if receipt.get("linguistic_response_verbatim") != "Approve as written":
        raise ValueError(
            f"Approval receipt linguistic_response_verbatim unexpected: {receipt.get('linguistic_response_verbatim')!r}"
        )
    if receipt.get("registry_publication_authorized") is not False:
        raise ValueError(
            f"Approval receipt registry_publication_authorized must remain false: {receipt.get('registry_publication_authorized')!r}"
        )

    approved_claims = receipt.get("approved_claims")
    if not isinstance(approved_claims, list) or not approved_claims:
        raise ValueError("Approval receipt must contain non-empty approved_claims list")

    packet_entries = [*packet.get("candidate_entries", []), *packet.get("homograph_entries", [])]
    if receipt.get("entry_count") != len(packet_entries):
        raise ValueError(
            f"Entry count mismatch between receipt ({receipt.get('entry_count')}) and packet ({len(packet_entries)})"
        )
    packet_sense_count = sum(len(e.get("senses", [])) for e in packet_entries)
    if receipt.get("sense_count") != packet_sense_count:
        raise ValueError(
            f"Sense count mismatch between receipt ({receipt.get('sense_count')}) and packet ({packet_sense_count})"
        )

    packet_claim_ids: set[str] = set()
    for pentry in packet_entries:
        packet_claim_ids.add(pentry["headword_assertion_id"])
        packet_claim_ids.add(pentry["pos_assertion_id"])
        for psense in pentry.get("senses", []):
            packet_claim_ids.add(psense["assertion_id"])

    if len(approved_claims) != len(packet_claim_ids):
        raise ValueError(
            f"Approved claim count mismatch: receipt_list={len(approved_claims)}, packet_core={len(packet_claim_ids)}"
        )

    assertion_by_id = {row["assertion_id"]: row for row in assertions}
    evidence_by_aid: dict[str, list[dict[str, Any]]] = {}
    for ev in evidence:
        evidence_by_aid.setdefault(ev["assertion_id"], []).append(ev)

    approved_by_id: dict[str, dict[str, Any]] = {}
    binding_checks: dict[str, dict[str, Any]] = {}
    for item in approved_claims:
        aid = item.get("assertion_id")
        if not isinstance(aid, str) or aid in approved_by_id:
            raise ValueError(f"Invalid or duplicate approved assertion_id in receipt: {aid!r}")
        if aid not in assertion_by_id:
            raise ValueError(f"Approved assertion_id not found in merged claims: {aid}")
        assertion = assertion_by_id[aid]
        prop = assertion["property_code"]
        if prop not in {"headword", "part_of_speech", "gloss", "definition"}:
            raise ValueError(f"Unapproved property_code {prop!r} cannot be approved as core claim: {aid}")
        if assertion.get("value_state") != "known":
            raise ValueError(f"Approved claim {aid} does not have value_state='known'")

        actual_claim_rev = claim_revision(assertion)
        if assertion["claim_revision_sha256"] != actual_claim_rev:
            raise ValueError(
                f"Stored claim_revision_sha256 mismatch on {aid}: {assertion['claim_revision_sha256']} != {actual_claim_rev}"
            )
        if item.get("claim_revision_sha256") != actual_claim_rev:
            raise ValueError(
                f"Receipt claim_revision_sha256 mismatch on {aid}: {item.get('claim_revision_sha256')} != {actual_claim_rev}"
            )

        ev_rows = evidence_by_aid.get(aid, [])
        if not ev_rows:
            raise ValueError(f"Missing evidence rows for approved claim {aid}")
        actual_ev_sha = evidence_hash(ev_rows)
        if item.get("evidence_bundle_sha256") != actual_ev_sha:
            raise ValueError(
                f"Evidence bundle SHA-256 mismatch on {aid}: {item.get('evidence_bundle_sha256')} != {actual_ev_sha}"
            )

        ufindings = unicode_findings(assertion)
        if ufindings:
            raise ValueError(f"Approved claim {aid} has Unicode findings: {ufindings}")
        if prop in {"headword", "gloss", "definition"}:
            inspected = native_inspect(str(assertion["value_json"]))
            if not inspected["is_nfc"]:
                raise ValueError(f"Approved claim {aid} is not NFC: {assertion['value_json']!r}")

        approved_by_id[aid] = item
        binding_checks[aid] = {
            "property_code": prop,
            "claim_revision_sha256": actual_claim_rev,
            "receipt_evidence_bundle_sha256": item["evidence_bundle_sha256"],
            "actual_evidence_bundle_sha256": actual_ev_sha,
        }

    if set(approved_by_id) != packet_claim_ids:
        raise ValueError(
            f"Approved claims set does not match packet claims set: "
            f"extra={sorted(set(approved_by_id) - packet_claim_ids)}, "
            f"missing={sorted(packet_claim_ids - set(approved_by_id))}"
        )

    return receipt, approved_by_id, binding_checks


def _build_reviewed_attribution_md(
    snapshot_entries: list[dict[str, Any]],
    receipt: dict[str, Any],
) -> str:
    """Build deterministic ATTRIBUTION_AND_LICENSE.md for the reviewed Wiktionary core pack."""
    lines = [
        "# Attribution, License Notices, and Disclaimers (Reviewed Wiktionary Core Data Pack)",
        "",
        "> **Scope & Separation Notice:**",
        "> `CC-BY-SA-4.0` applies **only to the Wiktionary source snapshots and reviewed lexical data** in this separate data pack.",
        "> It does **not** relicense the MIT-licensed Rust core crates (`crates/*`) or toolkit runtime engine.",
        "> This notice records engineering attribution and upstream license terms; it is not legal advice.",
        "",
        "## 1. Human-Reviewed Data Pack Policy Closure",
        "",
        f"- **Pack ID:** `core` (separate `CC-BY-SA-4.0` data pack; {receipt['pack_policy_response_verbatim']})",
        f"- **Reviewer / Decision Date:** `{receipt['reviewer_id']}` on `{receipt['decision_date']}` (`actor_type = {receipt['actor_type']}`)",
        f"- **Review Packet SHA-256:** `{receipt['review_packet_sha256']}`",
        "- **Attribution & ShareAlike:** Upstream English Wiktionary pages remain under `CC-BY-SA-4.0` (with upstream historical GFDL notice per Wikimedia Terms of Use §7); attribution to contributors, pinned `oldid`, permalink, and revision history is preserved in `sources.csv` and this file.",
        "- **Deferred / Excluded Material:** Structured qualifier scopes (`written`, `catholicism`) remain `unknown` / `needs_review`; unpinned IPA, etymologies, references, usage examples, and external historical aggregations remain excluded.",
        "",
        "## 2. Official Pinned Revisions & Contributor Attribution",
        "",
        "| Legacy `word_id` | Headword (`tam`) | `pageid` | Pinned `oldid` | Revision Timestamp (UTC) | Revision User (API) | Permalink & History |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for entry in snapshot_entries:
        lines.append(
            f"| `{entry['legacy_word_id']}` | {entry['title']} | `{entry['pageid']}` | `{entry['revid']}` | "
            f"`{entry['revision_timestamp']}` | `{entry['user']}` | "
            f"[Permalink]({entry['permalink_url']}) · [History]({entry['history_url']}) |"
        )
    lines.extend([
        "",
        "## 3. Preserved Official Notice Files",
        "",
        "- `cc_by_sa_4_0_legalcode.txt` — Creative Commons Attribution-ShareAlike 4.0 International Legal Code",
        "- `wikimedia_tou_api.json` — Wikimedia Foundation `Policy:Terms_of_Use` (`pageid=21261`, `revid=598588`, `2026-10-25T01:07:30Z`)",
        "- `wiktionary_copyrights_api.json` — English Wiktionary `Wiktionary:Copyrights` (`pageid=1503`, `revid=87545419`, `2025-10-22T20:09:50Z`)",
        "- `fetch_manifest.json` — Retrieval manifest from pinned official notice fetch",
        "",
    ])
    return "\n".join(lines)


def _merge_pending_tables(candidate_dir: Path, homograph_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """Deterministically merge the 21 CSV curation tables from both pending workspaces, asserting disjoint IDs."""
    merged: dict[str, list[dict[str, Any]]] = {name: [] for name in WORKSPACE_TABLES}
    unique_key_cols: dict[str, tuple[str, ...]] = {
        "snapshots": ("snapshot_id",),
        "sources": ("source_id",),
        "identities": ("entity_id",),
        "source_records": ("record_id",),
        "dispositions": ("record_id",),
        "record_targets": ("record_id", "entity_id"),
        "entries": ("entry_id",),
        "forms": ("form_id",),
        "senses": ("sense_id",),
        "texts": ("text_id",),
        "relations": ("relation_id",),
        "assertions": ("assertion_id",),
        "evidence": ("assertion_id", "source_id", "source_record_id", "locator_json"),
        "decisions": ("decision_id",),
        "changes": ("change_id",),
        "findings": ("finding_id",),
        "labels": ("registry_id", "registry_version", "code"),
        "pack_members": ("pack_id", "entry_id"),
    }
    seen_keys: dict[str, set[tuple[Any, ...]]] = {name: set() for name in unique_key_cols}

    for src_dir in (candidate_dir, homograph_dir):
        for name in WORKSPACE_TABLES:
            rows = list(read_rows(src_dir / f"{name}.csv", name))
            if name in unique_key_cols:
                cols = unique_key_cols[name]
                for row in rows:
                    key = tuple(row[col] for col in cols)
                    if key in seen_keys[name]:
                        raise ValueError(f"Duplicate merge key in {name}.csv: {key!r}")
                    seen_keys[name].add(key)
            merged[name].extend(rows)
    return merged


def build_reviewed_workspace(
    reviewed_dir: Path = REVIEWED_DIR,
    *,
    candidate_dir: Path = CANDIDATE_DIR,
    homograph_dir: Path = HOMOGRAPH_DIR,
    receipt_path: Path = DEFAULT_APPROVAL_RECEIPT,
    packet_path: Path = DEFAULT_REVIEW_PACKET,
    canonical: Path | None = None,
) -> dict[str, Any]:
    """Deterministically merge pending Wiktionary workspaces and apply an immutable human approval receipt."""
    reviewed_dir = safe_output(reviewed_dir)
    for protected in (
        ROOT / "data/curation/tamil-lexicon",
        CANDIDATE_DIR,
        HOMOGRAPH_DIR,
        candidate_dir,
        homograph_dir,
    ):
        safe_output(reviewed_dir, protected)

    original_count = _verify_frozen_originals()

    for pending_dir, spec in ((candidate_dir, DATASET_SPECS["candidate"]), (homograph_dir, DATASET_SPECS["homograph"])):
        snap_manifest = json.loads((pending_dir / "snapshots" / "snapshots_manifest.json").read_text(encoding="utf-8"))
        for entry_meta in snap_manifest["entries"]:
            _extract_pinned_revision(entry_meta, pending_dir / "snapshots", allowlist=spec.allowlist)
        _verify_license_notices(pending_dir / "notices")
        pending_check = check_curated_csv(workspace=pending_dir, canonical=canonical)
        if pending_check.get("findings"):
            raise ValueError(f"Input pending workspace failed validation ({pending_dir}): {pending_check}")

    tables = _merge_pending_tables(candidate_dir, homograph_dir)
    receipt, approved_by_id, binding_checks = _validate_approval_receipt(
        receipt_path, packet_path, tables["assertions"], tables["evidence"]
    )

    reviewer_id = receipt["reviewer_id"]
    decision_date = receipt["decision_date"]
    packet_sha256 = receipt["review_packet_sha256"]
    receipt_sha256 = digest(receipt_path)

    for row in tables["snapshots"]:
        row["dataset_id"] = REVIEWED_DATASET_ID

    for row in tables["sources"]:
        if row.get("evidence_verification_state") != "verified":
            raise ValueError(f"Source {row['source_id']} is not verified; cannot mark reuse_state='permitted'")
        row["reuse_state"] = "permitted"
        row["reuse_basis_json"] = (
            f"CC-BY-SA-4.0 (human-reviewed separate data pack 'core' approved {decision_date} by {reviewer_id}; "
            "dual-licensed CC-BY-SA-4.0/GFDL upstream; attribution & ShareAlike required)"
        )

    for row in tables["entries"]:
        row["structural_kind"] = "reviewed_wiktionary_core"

    current_by_aid = {d["assertion_id"]: d for d in _current_decisions(tables["decisions"])}
    new_decisions_meta: dict[str, dict[str, str]] = {}
    for assertion in tables["assertions"]:
        aid = assertion["assertion_id"]
        if aid not in approved_by_id:
            continue
        pred = current_by_aid.get(aid)
        if pred is None:
            raise ValueError(f"Missing predecessor decision for approved assertion {aid}")
        new_did = allocate_id("dec", REVIEWED_NAMESPACE, f"review:{decision_date}:{reviewer_id}:{aid}")
        tables["decisions"].append({
            "decision_id": new_did,
            "assertion_id": aid,
            "assertion_revision_sha256": assertion["claim_revision_sha256"],
            "evidence_bundle_sha256": binding_checks[aid]["actual_evidence_bundle_sha256"],
            "outcome": "accepted_human",
            "actor_type": "human",
            "actor_id": reviewer_id,
            "method_version": REVIEWED_METHOD_VERSION,
            "decision_date": decision_date,
            "note_json": (
                f"Human approval by {reviewer_id} on {decision_date} per receipt "
                f"review_packet_sha256={packet_sha256[:12]}...; separate CC-BY-SA-4.0 core pack."
            ),
            "predecessor_decision_id": pred["decision_id"],
        })
        new_decisions_meta[aid] = {
            "decision_id": new_did,
            "predecessor_decision_id": pred["decision_id"],
        }

    for row in tables["findings"]:
        if row["assertion_id"] in approved_by_id:
            row["status"] = "resolved"
            row["resolution_reason_json"] = (
                f"Accepted by human reviewer {reviewer_id} on {decision_date} via reviewed packet "
                f"{packet_sha256}; literal Wiktionary text verified against pinned oldid."
            )

    entry_ids = {row["entry_id"] for row in tables["entries"]}
    entry_targets_by_rec: dict[str, list[str]] = {}
    for target in tables["record_targets"]:
        if target["entity_id"] in entry_ids:
            entry_targets_by_rec.setdefault(target["record_id"], []).append(target["entity_id"])

    approved_aids_by_rec: dict[str, set[str]] = {}
    for ev in tables["evidence"]:
        if ev["assertion_id"] in approved_by_id:
            approved_aids_by_rec.setdefault(ev["source_record_id"], set()).add(ev["assertion_id"])

    for disp in tables["dispositions"]:
        rec_id = disp["record_id"]
        rec_findings = [f for f in tables["findings"] if f["record_id"] == rec_id]
        disp["finding_set_sha256"] = hashlib.sha256(
            json_text(sorted(rec_findings, key=json_text)).encode("utf-8")
        ).hexdigest()
        disp["structural_state"] = "validated"
        disp["method"] = REVIEWED_DATASET_ID
        disp["method_version"] = REVIEWED_METHOD_VERSION
        target_entries = entry_targets_by_rec.get(rec_id, [])
        approved_rec_claims = len(approved_aids_by_rec.get(rec_id, set()))
        open_rec_findings = sum(1 for f in rec_findings if f["status"] == "open")
        if len(target_entries) > 1:
            disp["disposition"] = "split"
            disp["reason_code"] = "REVIEWED_WIKTIONARY_HOMOGRAPH_SPLIT"
            disp["note_json"] = (
                f"Validated homograph split into {len(target_entries)} core entries ({approved_rec_claims} accepted "
                f"core claims by {reviewer_id} on {decision_date}; {open_rec_findings} unreviewed scope finding open)."
            )
        else:
            disp["disposition"] = "mapped"
            disp["reason_code"] = "REVIEWED_WIKTIONARY_CORE_VALIDATED"
            disp["note_json"] = (
                f"Validated {approved_rec_claims} accepted core claims by {reviewer_id} on {decision_date}; "
                f"{open_rec_findings} unreviewed scope finding(s) remain open/pending."
            )

    tables["pack_members"] = [
        {
            "pack_id": "core",
            "entry_id": entry["entry_id"],
            "included_revision": entry["revision"],
            "relation_inclusion_policy": "omit_cross_pack",
        }
        for entry in tables["entries"]
    ]

    _check_unicode_assertions(tables["assertions"], REVIEWED_DATASET_ID)

    # Refuse to overwrite manual/conflicting edits to reviewed CSV tables before writing any file.
    for name in WORKSPACE_TABLES:
        existing = reviewed_dir / f"{name}.csv"
        if existing.exists():
            actual = sorted(json_text(row) for row in read_rows(existing, name))
            expected = sorted(json_text(row) for row in tables[name])
            if actual != expected:
                raise ValueError(f"Conflicting reviewed edits; rebuild refused: {name}.csv")

    snap_dir = reviewed_dir / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    merged_snap_entries: list[dict[str, Any]] = []
    for src_dir in (candidate_dir, homograph_dir):
        src_snap_dir = src_dir / "snapshots"
        src_manifest = json.loads((src_snap_dir / "snapshots_manifest.json").read_text(encoding="utf-8"))
        for item in src_manifest["entries"]:
            for fname in (item["api_response_file"], item["wikitext_file"]):
                shutil.copyfile(src_snap_dir / fname, snap_dir / fname)
            merged_snap_entries.append(item)

    merged_snap_manifest = {
        "schema": "wiktionary-reviewed-snapshots-v1",
        "entries": merged_snap_entries,
    }
    snap_manifest_bytes = (
        json.dumps(merged_snap_manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    (snap_dir / "snapshots_manifest.json").write_bytes(snap_manifest_bytes)
    manifest_sha256 = hashlib.sha256(snap_manifest_bytes).hexdigest()

    notices_dir = reviewed_dir / "notices"
    notices_dir.mkdir(parents=True, exist_ok=True)
    for fname in (
        "cc_by_sa_4_0_legalcode.txt",
        "wikimedia_tou_api.json",
        "wiktionary_copyrights_api.json",
        "fetch_manifest.json",
    ):
        shutil.copyfile(candidate_dir / "notices" / fname, notices_dir / fname)
    (notices_dir / "ATTRIBUTION_AND_LICENSE.md").write_text(
        _build_reviewed_attribution_md(merged_snap_entries, receipt),
        encoding="utf-8",
        newline="\n",
    )
    notice_digests = _verify_license_notices(notices_dir)

    for name in WORKSPACE_TABLES:
        write_rows(reviewed_dir / f"{name}.csv", name, tables[name], source_root=snap_dir)

    dataset_toml = "\n".join([
        "schema_version = 1",
        f'dataset_id = "{REVIEWED_DATASET_ID}"',
        'dataset_version = "1"',
        f'id_namespace = "{REVIEWED_NAMESPACE}"',
        'text_codec = "json-string-utf8-v1"',
        "registry_version = 1",
        f'transformation_version = "{REVIEWED_METHOD_VERSION}"',
        f'snapshots_manifest_sha256 = "{manifest_sha256}"',
        "",
    ])
    (reviewed_dir / "dataset.toml").write_text(dataset_toml, encoding="utf-8", newline="\n")

    cand_prov = json.loads((candidate_dir / "provenance" / "extraction_provenance.json").read_text(encoding="utf-8"))
    homo_prov = json.loads((homograph_dir / "provenance" / "extraction_provenance.json").read_text(encoding="utf-8"))
    cand_excl = json.loads((candidate_dir / "provenance" / "exclusions.json").read_text(encoding="utf-8"))
    homo_excl = json.loads((homograph_dir / "provenance" / "exclusions.json").read_text(encoding="utf-8"))

    prov_dir = reviewed_dir / "provenance"
    prov_dir.mkdir(parents=True, exist_ok=True)
    merged_prov_entries = [*cand_prov["entries"], *homo_prov["entries"]]
    (prov_dir / "extraction_provenance.json").write_text(
        data_json({
            "schema": "wiktionary-reviewed-provenance-v1",
            "entry_count": len(merged_prov_entries),
            "sense_count": sum(len(e["senses"]) for e in merged_prov_entries),
            "entries": merged_prov_entries,
        }) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (prov_dir / "exclusions.json").write_text(
        json.dumps(
            {
                "schema": "wiktionary-reviewed-exclusions-v1",
                "entries": [*cand_excl["entries"], *homo_excl["entries"]],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (prov_dir / "schema_gaps.json").write_text(
        json.dumps(
            {
                "schema": "wiktionary-reviewed-schema-gaps-v1",
                "gaps": [
                    {
                        "id": "GAP_SOURCE_RECORDS_NON_CSV_ORDINAL",
                        "table": "source_records",
                        "description": (
                            "intake.schema.json enforces ordinal >= 2 (assuming line 1 CSV header) and unique "
                            "(snapshot_id, ordinal). Single-page wikitext snapshots have no CSV header, so ordinal=2 "
                            "is recorded for the whole pinned wikitext revision file while line spans record 1..N."
                        ),
                    },
                    {
                        "id": "GAP_SOURCES_NO_DEDICATED_REVID_PAGEID_COLUMNS",
                        "table": "sources",
                        "description": (
                            "intake.schema.json has no dedicated columns for MediaWiki pageid, revid, revision_timestamp, "
                            "wikitext_sha256, permalink_url, history_url, or dual-license notice (GFDL). These are "
                            "stored deterministically in edition_json / locator_json and snapshots/snapshots_manifest.json."
                        ),
                    },
                    {
                        "id": "GAP_PACK_UNREVIEWED_SCOPES_DEFERRED",
                        "table": "scopes/findings",
                        "description": (
                            "Structured scope proposals (written, catholicism) remain outcome='needs_review' with open "
                            "SCOPE_QUALIFIER_REQUIRES_REVIEW findings and scopes.csv state='unknown'; core pack L3 "
                            "promotion admits only the 31 receipt-approved headword, POS, and definition/gloss claims."
                        ),
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    unapproved_claims = []
    for assertion in tables["assertions"]:
        aid = assertion["assertion_id"]
        if aid not in approved_by_id:
            cur = current_by_aid.get(aid, {})
            unapproved_claims.append({
                "assertion_id": aid,
                "property_code": assertion["property_code"],
                "subject_id": assertion["subject_id"],
                "outcome": cur.get("outcome"),
            })

    closure_manifest = {
        "schema": "wiktionary-reviewed-closure-v1",
        "dataset_id": REVIEWED_DATASET_ID,
        "pack_id": "core",
        "license_spdx": "CC-BY-SA-4.0",
        "approved_policy": receipt["approved_policy"],
        "registry_publication_authorized": receipt["registry_publication_authorized"],
        "actor_type": receipt["actor_type"],
        "reviewer_id": reviewer_id,
        "decision_date": decision_date,
        "original_12_count": original_count,
        "approval_receipt_path": str(receipt_path.relative_to(ROOT)).replace("\\", "/") if receipt_path.is_relative_to(ROOT) else str(receipt_path).replace("\\", "/"),
        "approval_receipt_sha256": receipt_sha256,
        "review_packet_sha256": packet_sha256,
        "snapshots_manifest_sha256": manifest_sha256,
        "sources_csv_sha256": digest(reviewed_dir / "sources.csv"),
        "notice_digests": notice_digests,
        "counts": {
            "entries": len(tables["entries"]),
            "senses": len(tables["senses"]),
            "assertions_total": len(tables["assertions"]),
            "approved_assertions": len(approved_by_id),
            "unapproved_assertions": len(unapproved_claims),
            "pack_members": len(tables["pack_members"]),
            "open_findings": sum(1 for f in tables["findings"] if f["status"] == "open"),
            "resolved_findings": sum(1 for f in tables["findings"] if f["status"] == "resolved"),
            "ipa_forms": sum(1 for f in tables["forms"] if f["representation"] == "ipa"),
        },
        "approved_claim_bindings": [
            {
                "assertion_id": aid,
                **binding_checks[aid],
                **new_decisions_meta[aid],
            }
            for aid in [a["assertion_id"] for a in tables["assertions"] if a["assertion_id"] in approved_by_id]
        ],
        "unapproved_claims": unapproved_claims,
    }
    (prov_dir / "reviewed_closure_manifest.json").write_text(
        json.dumps(closure_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    try:
        reviewed_rel = str(reviewed_dir.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        reviewed_rel = str(reviewed_dir).replace("\\", "/")

    return {
        "reviewed_dir": reviewed_rel,
        "dataset_id": REVIEWED_DATASET_ID,
        "entry_count": len(tables["entries"]),
        "sense_count": len(tables["senses"]),
        "assertion_count": len(tables["assertions"]),
        "approved_assertions": len(approved_by_id),
        "accepted_human_decisions": len(new_decisions_meta),
        "pack_member_count": len(tables["pack_members"]),
        "open_findings": closure_manifest["counts"]["open_findings"],
        "resolved_findings": closure_manifest["counts"]["resolved_findings"],
        "approval_receipt_sha256": receipt_sha256,
        "review_packet_sha256": packet_sha256,
    }


def verify_reviewed_workspace(
    reviewed_dir: Path = REVIEWED_DIR,
    *,
    receipt_path: Path = DEFAULT_APPROVAL_RECEIPT,
    packet_path: Path = DEFAULT_REVIEW_PACKET,
    canonical: Path | None = None,
) -> dict[str, Any]:
    """Run full integrity, source/notice closure, receipt-binding, history, and eligibility checks."""
    original_count = _verify_frozen_originals()

    snap_dir = reviewed_dir / "snapshots"
    snap_manifest = json.loads((snap_dir / "snapshots_manifest.json").read_text(encoding="utf-8"))
    merged_allowlist = {**PINNED_ALLOWLIST, **HOMOGRAPH_ALLOWLIST}
    if len(snap_manifest["entries"]) != len(merged_allowlist):
        raise ValueError(f"Expected {len(merged_allowlist)} reviewed snapshot pages, got {len(snap_manifest['entries'])}")
    for entry_meta in snap_manifest["entries"]:
        _extract_pinned_revision(entry_meta, snap_dir, allowlist=merged_allowlist)

    notice_digests = _verify_license_notices(reviewed_dir / "notices")

    validation = check_curated_csv(workspace=reviewed_dir, canonical=canonical)
    if validation.get("findings"):
        raise ValueError(f"Reviewed workspace failed check_curated_csv: {validation}")

    tables = {name: list(read_rows(reviewed_dir / f"{name}.csv", name)) for name in WORKSPACE_TABLES}
    _check_unicode_assertions(tables["assertions"], f"verify-{REVIEWED_DATASET_ID}")

    receipt, approved_by_id, _ = _validate_approval_receipt(
        receipt_path, packet_path, tables["assertions"], tables["evidence"]
    )
    reviewer_id = receipt["reviewer_id"]
    decision_date = receipt["decision_date"]

    history_findings = validate_history(
        tables["identities"],
        tables["changes"],
        tables["successors"],
        tables["assertions"],
        tables["decisions"],
    )
    if history_findings:
        raise ValueError(f"Reviewed history validation failed: {history_findings}")

    sources_by_id = {s["source_id"]: s for s in tables["sources"]}
    if len(sources_by_id) != len(merged_allowlist):
        raise ValueError(f"Expected {len(merged_allowlist)} sources, got {len(sources_by_id)}")
    for src in tables["sources"]:
        if src["evidence_verification_state"] != "verified" or src["reuse_state"] != "permitted":
            raise ValueError(f"Source {src['source_id']} lacks permitted/verified reuse closure: {src}")

    current_decisions = _current_decisions(tables["decisions"])
    current_by_aid = {d["assertion_id"]: d for d in current_decisions}
    accepted = [d for d in current_decisions if d["outcome"] == "accepted_human"]
    if len(accepted) != len(approved_by_id):
        raise ValueError(f"Expected {len(approved_by_id)} accepted_human current decisions, got {len(accepted)}")
    for dec in accepted:
        if dec["assertion_id"] not in approved_by_id:
            raise ValueError(f"Unexpected accepted_human decision outside approval receipt: {dec['assertion_id']}")
        if dec["actor_type"] != "human" or dec["actor_id"] != reviewer_id or dec["decision_date"] != decision_date:
            raise ValueError(f"Invalid human decision attribution on {dec['decision_id']}: {dec}")

    evidence_by_aid: dict[str, list[dict[str, Any]]] = {}
    for ev in tables["evidence"]:
        evidence_by_aid.setdefault(ev["assertion_id"], []).append(ev)
    findings_by_aid: dict[str, list[dict[str, Any]]] = {}
    for fnd in tables["findings"]:
        findings_by_aid.setdefault(fnd["assertion_id"], []).append(fnd)

    eligible_ids: list[str] = []
    ineligible_ids: list[str] = []
    for assertion in tables["assertions"]:
        aid = assertion["assertion_id"]
        elig = eligibility(
            assertion,
            evidence_by_aid.get(aid, ()),
            sources_by_id,
            tables["decisions"],
            findings_by_aid.get(aid, ()),
        )
        if aid in approved_by_id:
            if not elig["eligible"]:
                raise ValueError(f"Approved assertion {aid} is not eligible: {elig}")
            eligible_ids.append(aid)
        else:
            if elig["eligible"]:
                raise ValueError(f"Unapproved assertion {aid} must remain ineligible: {elig}")
            ineligible_ids.append(aid)

    rejected_count = sum(1 for d in current_decisions if d["outcome"] == "rejected")
    needs_review_count = sum(1 for d in current_decisions if d["outcome"] == "needs_review")
    if rejected_count != 2 or needs_review_count != 2:
        raise ValueError(
            f"Expected 2 rejected v1 claims and 2 needs_review scope proposals, got rejected={rejected_count}, needs_review={needs_review_count}"
        )

    open_findings = [f for f in tables["findings"] if f["status"] == "open"]
    if len(open_findings) != 2 or any(f["issue_code"] != "SCOPE_QUALIFIER_REQUIRES_REVIEW" for f in open_findings):
        raise ValueError(f"Expected exactly 2 open SCOPE_QUALIFIER_REQUIRES_REVIEW findings, got {open_findings}")

    for sc in tables["scopes"]:
        if sc["state"] != "unknown" or sc["label_code"] is not None:
            raise ValueError(f"Unreviewed scopes must remain unknown/null, found {sc}")

    ipa_forms = [f for f in tables["forms"] if f["representation"] == "ipa"]
    if ipa_forms:
        raise ValueError(f"Template-generated IPA forms must remain excluded, found {len(ipa_forms)}")

    entry_rev = {e["entry_id"]: e["revision"] for e in tables["entries"]}
    if len(tables["pack_members"]) != len(entry_rev):
        raise ValueError(f"Expected {len(entry_rev)} pack_members, got {len(tables['pack_members'])}")
    for pm in tables["pack_members"]:
        if (
            pm["pack_id"] != "core"
            or pm["included_revision"] != entry_rev.get(pm["entry_id"])
            or pm["relation_inclusion_policy"] != "omit_cross_pack"
        ):
            raise ValueError(f"Invalid pack_members row: {pm}")

    dispositions = {d["record_id"]: d for d in tables["dispositions"]}
    if any(d["structural_state"] != "validated" for d in dispositions.values()):
        raise ValueError("All reviewed dispositions must have structural_state='validated'")
    split_count = sum(1 for d in dispositions.values() if d["disposition"] == "split")
    mapped_count = sum(1 for d in dispositions.values() if d["disposition"] == "mapped")
    if split_count != 1 or mapped_count != 4:
        raise ValueError(f"Expected 1 split + 4 mapped dispositions, got split={split_count}, mapped={mapped_count}")

    guard = release_guard(workspace=reviewed_dir, pack="core")
    if (
        not guard["l3_pack_eligible"]
        or guard["findings"]
        or guard["eligible_assertions"] != len(approved_by_id)
        or guard["included_entries"] != len(entry_rev)
    ):
        raise ValueError(f"release_guard failed L3 pack eligibility check: {guard}")

    return {
        "ok": True,
        "dataset": "reviewed",
        "dataset_id": REVIEWED_DATASET_ID,
        "original_12_verified": True,
        "original_12_count": original_count,
        "snapshot_count": len(snap_manifest["entries"]),
        "notice_digests": notice_digests,
        "entry_count": len(tables["entries"]),
        "sense_count": len(tables["senses"]),
        "form_count": len(tables["forms"]),
        "ipa_form_count": len(ipa_forms),
        "pack_member_count": len(tables["pack_members"]),
        "eligible_assertions": len(eligible_ids),
        "ineligible_assertions": len(ineligible_ids),
        "accepted_human_decisions": len(accepted),
        "rejected_current_decisions": rejected_count,
        "needs_review_current_decisions": needs_review_count,
        "open_findings": len(open_findings),
        "reviewer_id": reviewer_id,
        "decision_date": decision_date,
        "approval_receipt_sha256": digest(receipt_path),
        "review_packet_sha256": receipt["review_packet_sha256"],
        "sources_csv_sha256": digest(reviewed_dir / "sources.csv"),
        "validation": validation,
        "release_guard": guard,
    }


def check_reviewed_idempotent_replay(
    reviewed_dir: Path = REVIEWED_DIR,
    *,
    candidate_dir: Path = CANDIDATE_DIR,
    homograph_dir: Path = HOMOGRAPH_DIR,
    receipt_path: Path = DEFAULT_APPROVAL_RECEIPT,
    packet_path: Path = DEFAULT_REVIEW_PACKET,
    canonical: Path | None = None,
) -> dict[str, Any]:
    """Rebuild the reviewed workspace into an isolated temporary directory and confirm byte-identical outputs."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp) / REVIEWED_DIR.name
        build_reviewed_workspace(
            tmp_dir,
            candidate_dir=candidate_dir,
            homograph_dir=homograph_dir,
            receipt_path=receipt_path,
            packet_path=packet_path,
            canonical=canonical,
        )
        diffs: list[str] = []
        checked: list[str] = []
        for name in WORKSPACE_TABLES:
            rel = f"{name}.csv"
            checked.append(rel)
            if (reviewed_dir / rel).read_bytes() != (tmp_dir / rel).read_bytes():
                diffs.append(rel)
        for rel in [
            "dataset.toml",
            "snapshots/snapshots_manifest.json",
            "notices/ATTRIBUTION_AND_LICENSE.md",
            "provenance/extraction_provenance.json",
            "provenance/exclusions.json",
            "provenance/schema_gaps.json",
            "provenance/reviewed_closure_manifest.json",
        ]:
            checked.append(rel)
            if (reviewed_dir / rel).read_bytes() != (tmp_dir / rel).read_bytes():
                diffs.append(rel)
        if diffs:
            raise ValueError(f"Non-deterministic reviewed replay mismatch on: {diffs}")
        return {"ok": True, "dataset": "reviewed", "checked_files": len(checked), "diffs": diffs}


def verify_candidate_workspace(
    candidate_dir: Path = CANDIDATE_DIR,
    *,
    dataset: str | None = None,
    canonical: Path | None = None,
) -> dict[str, Any]:
    """Run integrity, original-12 immutability, schema/Unicode, and non-eligibility checks."""
    spec = _resolve_spec(candidate_dir, dataset)
    original_count = _verify_frozen_originals()

    snap_dir = candidate_dir / "snapshots"
    snap_manifest = json.loads((snap_dir / "snapshots_manifest.json").read_text(encoding="utf-8"))
    for entry_meta in snap_manifest["entries"]:
        _extract_pinned_revision(entry_meta, snap_dir, allowlist=spec.allowlist)

    validation = check_curated_csv(workspace=candidate_dir, canonical=canonical)
    if validation.get("findings"):
        raise ValueError(f"Candidate workspace failed check_curated_csv: {validation}")

    assertions = list(read_rows(candidate_dir / "assertions.csv", "assertions"))
    _check_unicode_assertions(assertions, f"verify-{spec.key}")

    decisions = list(read_rows(candidate_dir / "decisions.csv", "decisions"))
    accepted = [d for d in decisions if d["outcome"] in {"accepted_human", "accepted_auto_source"}]
    if accepted:
        raise ValueError(f"Accepted decisions forbidden in pending candidate: {len(accepted)}")

    entries = list(read_rows(candidate_dir / "entries.csv", "entries"))
    senses = list(read_rows(candidate_dir / "senses.csv", "senses"))
    forms = list(read_rows(candidate_dir / "forms.csv", "forms"))
    ipa_forms = [f for f in forms if f["representation"] == "ipa"]
    if ipa_forms:
        raise ValueError(f"Template-generated IPA forms must be excluded, found {len(ipa_forms)}")

    guard = release_guard(workspace=candidate_dir)
    if guard["l3_pack_eligible"] or guard["eligible_assertions"] != 0 or guard["runtime_verified"] is not None:
        raise ValueError(f"Candidate must not be L3 pack eligible: {guard}")

    return {
        "ok": True,
        "dataset": spec.key,
        "dataset_id": spec.dataset_id,
        "original_12_verified": True,
        "original_12_count": original_count,
        "snapshot_count": len(snap_manifest["entries"]),
        "entry_count": len(entries),
        "sense_count": len(senses),
        "form_count": len(forms),
        "ipa_form_count": len(ipa_forms),
        "accepted_decisions": len(accepted),
        "decision_outcomes": {
            k: sum(1 for d in decisions if d["outcome"] == k)
            for k in sorted({d["outcome"] for d in decisions})
        },
        "validation": validation,
        "release_guard": guard,
    }


def check_idempotent_replay(
    candidate_dir: Path = CANDIDATE_DIR,
    *,
    dataset: str | None = None,
) -> dict[str, Any]:
    """Rebuild into an isolated temporary copy of snapshots and confirm byte-identical CSV/JSON outputs."""
    spec = _resolve_spec(candidate_dir, dataset)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp) / spec.default_dir.name
        shutil.copytree(candidate_dir / "snapshots", tmp_dir / "snapshots")
        build_candidate_workspace(tmp_dir, dataset=spec.key)

        diffs: list[str] = []
        checked: list[str] = []
        for name in WORKSPACE_TABLES:
            rel = f"{name}.csv"
            a = (candidate_dir / rel).read_bytes()
            b = (tmp_dir / rel).read_bytes()
            checked.append(rel)
            if a != b:
                diffs.append(rel)
        for rel in [
            "dataset.toml",
            "provenance/extraction_provenance.json",
            "provenance/exclusions.json",
            "provenance/schema_gaps.json",
        ]:
            checked.append(rel)
            if (candidate_dir / rel).read_bytes() != (tmp_dir / rel).read_bytes():
                diffs.append(rel)
        if diffs:
            raise ValueError(f"Non-deterministic replay mismatch on: {diffs}")
        return {"ok": True, "dataset": spec.key, "checked_files": len(checked), "diffs": diffs}


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for building, verifying, and replay-checking Wiktionary candidate and reviewed datasets."""
    parser = argparse.ArgumentParser(description="Build and verify isolated Wiktionary candidate and reviewed datasets.")
    parser.add_argument("action", choices=["build", "verify", "replay-check"], help="Operation to run.")
    parser.add_argument(
        "--dataset",
        choices=[*sorted(DATASET_SPECS), "reviewed"],
        default=None,
        help="Dataset key ('candidate', 'homograph', or 'reviewed').",
    )
    parser.add_argument("--workspace", type=Path, default=None, help="Target workspace directory.")
    args = parser.parse_args(argv)

    if args.dataset == "reviewed":
        workspace = args.workspace if args.workspace is not None else REVIEWED_DIR
        if args.action == "build":
            res = build_reviewed_workspace(workspace)
        elif args.action == "verify":
            res = verify_reviewed_workspace(workspace)
        else:
            res = check_reviewed_idempotent_replay(workspace)
    else:
        workspace = (
            args.workspace
            if args.workspace is not None
            else (DATASET_SPECS[args.dataset].default_dir if args.dataset else CANDIDATE_DIR)
        )
        if args.action == "build":
            res = build_candidate_workspace(workspace, dataset=args.dataset)
        elif args.action == "verify":
            res = verify_candidate_workspace(workspace, dataset=args.dataset)
        else:
            res = check_idempotent_replay(workspace, dataset=args.dataset)
    print(json.dumps(res, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

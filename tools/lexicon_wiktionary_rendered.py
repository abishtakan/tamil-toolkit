"""Source-backed recovery of blocked Wiktionary gaps using official MediaWiki action=parse HTML.

Acquires bounded pinned-revision rendered HTML (<= 384 pages) from ``en.wiktionary.org``,
records truthful capture timestamps, SHA-256 digests, and template/module dependency metadata
(never attributing rendered output to original wikitext verbatim), preserves Tamil/etymology/POS/
direct-sense boundaries, retains Tamil-in-English-gloss rejection, and emits bulk-compatible
candidate JSON with zero acceptance decisions or canonical promotion.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import urllib.parse
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.lexicon import allocate_id, digest, json_text, native_inspect  # noqa: E402
from tools.lexicon_wiktionary_bulk import (  # noqa: E402
    API_ENDPOINT,
    DOMAIN_LABEL_IGNORE,
    FORBIDDEN_SENSE_MARKERS,
    NEGATING_REGION_PREFIXES,
    NON_DEFINITION_SECTIONS,
    POS_HEADING_MAP,
    TAMIL_CHAR_RE,
    _api_get_json as _bulk_api_get_json,
    _classify_label_token,
    assign_pack,
    check_unicode_scalar_integrity,
)

MAX_RENDERED_PAGES = 384
RENDERED_NAMESPACE = "d9a1c347-8b2f-5c44-9e71-3a6b8c9d0e12"
RENDERED_SOURCE_DIR = ROOT / "data/sources/enwiktionary-tamil-rendered-2026-11-16"
RENDERED_OUTPUT_DIR = ROOT / "target/lexicon/wiktionary-rendered-2026-11-16"
RENDERED_EXTRACTION_METHOD = "wiktionary-rendered-parser"
RENDERED_EXTRACTION_VERSION = "wiktionary-rendered-v1+utf8-v1"
RENDERED_SOURCE_ORIGIN = "rendered_template_expansion"
RENDERED_ATTRIBUTION = "rendered_by_mediawiki_current_templates_at_capture_time"
RENDERED_LIMITS_CAVEAT = (
    "MediaWiki action=parse evaluates pinned oldid wikitext against live templates/modules "
    "at capture_timestamp_utc; template/module revisions are not individually pinned by oldid."
)

DEFAULT_RECONCILIATION_PATH = ROOT / "docs/audits/wiktionary-gap-reconciliation-2026-11-16.json"
DEFAULT_BULK_SNAPSHOT_DIR = ROOT / "data/sources/enwiktionary-tamil"
DEFAULT_SUPPLEMENTAL_DIR = ROOT / "data/sources/enwiktionary-tamil-gap-2026-11-16"

_API_PROPS = "text|templates|modules|revid|displaytitle|sections|parsewarnings|properties"
_VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})
_RAW_TEXT_TAGS = frozenset({"style", "script"})
_DISALLOWED_DIRECT_SENSE_TAGS = frozenset({
    "sup", "sub", "script", "table", "figure", "math", "img",
    "audio", "video", "div", "iframe", "object", "embed", "svg",
})
_BLOCKED_BATCH_RE = re.compile(r"batch-[0-9]{3,}\.json")


def _api_get_json(params: dict[str, str], retries: int = 3) -> dict[str, Any]:
    """Bounded MediaWiki API call wrapper (isolated for monkeypatching in tests)."""
    return _bulk_api_get_json(params, retries=retries)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if path.exists() and path.read_bytes() == encoded:
        return
    path.write_bytes(encoded)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_canonical_json(payload: Any) -> str:
    return hashlib.sha256(json_text(payload).encode("utf-8")).hexdigest()


def _dependencies_digest(
    template_deps: list[str],
    module_deps: list[str],
    other_deps: list[str],
    rl_modules: list[str],
    rl_modulestyles: list[str],
) -> str:
    payload = {
        "templates": template_deps,
        "modules": module_deps,
        "other": other_deps,
        "rl_modules": rl_modules,
        "rl_modulestyles": rl_modulestyles,
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def validate_rendered_source_dir(directory: Path) -> Path:
    """Confine rendered captures to a dedicated directory under data/sources/."""
    target = directory.resolve()
    sources_root = (ROOT / "data/sources").resolve()
    protected = (
        (sources_root / "enwiktionary-tamil").resolve(),
        (sources_root / "enwiktionary-tamil-gap-2026-11-16").resolve(),
        (sources_root / "tamil-lexicon").resolve(),
    )
    if not target.is_relative_to(sources_root) or target == sources_root or any(target.is_relative_to(p) for p in protected):
        raise ValueError("Rendered source directory must be a separate directory beneath data/sources")
    return target


def verify_rendered_raw_files(directory: Path, expected: dict[str, Any]) -> None:
    """Verify every registered batch file digest and reject unregistered batches."""
    for filename, expected_sha in expected.items():
        if _BLOCKED_BATCH_RE.fullmatch(filename) is None:
            raise ValueError(f"Invalid cached rendered batch filename: {filename!r}")
        path = directory / filename
        if not path.is_file() or digest(path) != expected_sha:
            raise ValueError(f"Cached rendered batch digest mismatch: {filename}")
    if {p.name for p in directory.glob("batch-*.json")} != set(expected):
        raise ValueError("Unregistered cached rendered batches; no hash evidence")


def verify_rendered_page(page: dict[str, Any]) -> None:
    """Validate pinned identity, capture attribution, URL safety, and HTML/dependency digests."""
    for key in ("pageid", "revid"):
        if type(page.get(key)) is not int or page[key] <= 0:
            raise ValueError(f"Invalid pinned rendered page {key}")
    if not isinstance(page.get("title"), str) or not page["title"]:
        raise ValueError("Invalid rendered page title")
    if not isinstance(page.get("capture_timestamp_utc"), str) or not page["capture_timestamp_utc"]:
        raise ValueError("Missing capture_timestamp_utc on rendered page")
    if page.get("rendering_attribution") != RENDERED_ATTRIBUTION:
        raise ValueError("Invalid rendering attribution; rendered pages cannot claim verbatim_source")
    if not isinstance(page.get("rendered_html"), str):
        raise ValueError("Missing rendered_html string")
    if _sha256_text(page["rendered_html"]) != page.get("rendered_html_sha256"):
        raise ValueError("Rendered HTML digest mismatch")
    expected_deps_sha = _dependencies_digest(
        list(page.get("template_dependencies", [])),
        list(page.get("module_dependencies", [])),
        list(page.get("other_dependencies", [])),
        list(page.get("rl_modules", [])),
        list(page.get("rl_modulestyles", [])),
    )
    if expected_deps_sha != page.get("dependencies_sha256"):
        raise ValueError("Rendered template/module dependencies digest mismatch")
    for key in ("wikitext_sha256", "raw_api_response_sha256"):
        if not isinstance(page.get(key), str) or re.fullmatch(r"[0-9a-f]{64}", page[key]) is None:
            raise ValueError(f"Invalid pinned {key} on rendered page")
    for key in ("permalink_url", "history_url"):
        url = urllib.parse.urlsplit(str(page.get(key, "")))
        query = urllib.parse.parse_qs(url.query)
        if url.scheme != "https" or url.netloc != "en.wiktionary.org" or url.path != "/w/index.php":
            raise ValueError("Unsafe rendered source attribution URL")
        if key == "permalink_url" and query.get("oldid") != [str(page["revid"])]:
            raise ValueError("Rendered source attribution revision mismatch")
        if key == "history_url" and query.get("action") != ["history"]:
            raise ValueError("Rendered source attribution history mismatch")


def verify_rendered_capture(directory: Path) -> dict[str, Any]:
    """Verify manifest, raw batch hashes, gzipped JSONL digests, and every page record."""
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("rendering_attribution") != RENDERED_ATTRIBUTION:
        raise ValueError("Invalid rendered capture manifest attribution")
    verify_rendered_raw_files(directory, manifest["raw_files"])
    gz_path = directory / "pages.jsonl.gz"
    if not gz_path.is_file() or digest(gz_path) != manifest["pages_jsonl_gz_sha256"]:
        raise ValueError("Cached rendered pages.jsonl.gz digest mismatch")
    raw_bytes = gzip.decompress(gz_path.read_bytes())
    if hashlib.sha256(raw_bytes).hexdigest() != manifest["pages_uncompressed_sha256"]:
        raise ValueError("Cached rendered uncompressed digest mismatch")
    count = 0
    batches = {}
    for line in raw_bytes.decode("utf-8").splitlines():
        if not line.strip():
            continue
        page = json.loads(line)
        verify_rendered_page(page)
        locator = page.get("raw_capture_file_locator", {})
        batch_file = locator.get("batch_file", "")
        if _BLOCKED_BATCH_RE.fullmatch(batch_file) is None or locator.get("batch_sha256") != manifest["raw_files"].get(batch_file):
            raise ValueError("Rendered source batch locator digest mismatch")
        if batch_file not in batches:
            batches[batch_file] = json.loads((directory / batch_file).read_text(encoding="utf-8"))["records"]
        index = locator.get("record_index")
        if type(index) is not int or not 0 <= index < len(batches[batch_file]):
            raise ValueError("Rendered source batch record index mismatch")
        if {key: value for key, value in page.items() if key != "raw_capture_file_locator"} != batches[batch_file][index]:
            raise ValueError("Rendered projection differs from registered source batch record")
        count += 1
    if count != manifest.get("total_fetched_pages"):
        raise ValueError("Cached rendered page count mismatch against manifest")
    return manifest


def load_rendered_capture(directory: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Verify and load all captured rendered pages keyed by exact title."""
    manifest = verify_rendered_capture(directory)
    pages: dict[str, dict[str, Any]] = {}
    with gzip.open(directory / "pages.jsonl.gz", "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            page = json.loads(line)
            title = page["title"]
            if title in pages:
                raise ValueError(f"Duplicate title in rendered capture: {title!r}")
            pages[title] = page
    return pages, manifest


def build_rendered_queue(
    *,
    reconciliation_path: Path = DEFAULT_RECONCILIATION_PATH,
    bulk_snapshot_dir: Path = DEFAULT_BULK_SNAPSHOT_DIR,
    supplemental_dir: Path = DEFAULT_SUPPLEMENTAL_DIR,
    only_blocked: bool = False,
) -> list[dict[str, Any]]:
    """Build deterministic pinned queue (<= 384 items) cross-checked against original snapshots."""
    rec = json.loads(reconciliation_path.read_text(encoding="utf-8"))

    bulk_manifest = json.loads((bulk_snapshot_dir / "snapshots_manifest.json").read_text(encoding="utf-8"))
    bulk_gz = bulk_snapshot_dir / "pages.jsonl.gz"
    if digest(bulk_gz) != bulk_manifest["pages_jsonl_gz_sha256"]:
        raise ValueError("Bulk snapshot pages.jsonl.gz digest mismatch")
    pinned_pages: dict[str, dict[str, Any]] = {}
    with gzip.open(bulk_gz, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            page = json.loads(line)
            pinned_pages[page["title"]] = page

    supp_manifest = json.loads((supplemental_dir / "manifest.json").read_text(encoding="utf-8"))
    supp_pages_path = supplemental_dir / "pages.json"
    expected_pages_file = supp_manifest["pages_file"]
    expected_sha = expected_pages_file["sha256"] if isinstance(expected_pages_file, dict) else expected_pages_file
    if digest(supp_pages_path) != expected_sha or (
        isinstance(expected_pages_file, dict) and supp_pages_path.stat().st_size != expected_pages_file["bytes"]
    ):
        raise ValueError("Supplemental pages.json digest mismatch")
    for page in json.loads(supp_pages_path.read_text(encoding="utf-8")):
        pinned_pages[page["title"]] = page

    queue: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    seen_revids: set[int] = set()
    for row in rec["records"]:
        src = row.get("source")
        if not src:
            continue
        if only_blocked and row.get("status") != "source_present_parser_blocked":
            continue
        title = row["headword"]
        if title in seen_titles:
            raise ValueError(f"Duplicate title in reconciliation queue: {title!r}")
        page = pinned_pages.get(title)
        if page is None:
            raise ValueError(f"Pinned source missing for queue title: {title!r}")
        if int(page["pageid"]) != int(src["pageid"]) or int(page["revid"]) != int(src["revid"]):
            raise ValueError(f"Pinned pageid/revid mismatch for {title!r}")
        if page["wikitext_sha256"] != src["wikitext_sha256"]:
            raise ValueError(f"Pinned wikitext_sha256 mismatch for {title!r}")
        revid = int(page["revid"])
        if revid in seen_revids:
            raise ValueError(f"Duplicate revid in rendered queue: {revid}")
        seen_titles.add(title)
        seen_revids.add(revid)
        queue.append({
            "title": title,
            "pageid": int(page["pageid"]),
            "revid": revid,
            "wikitext_sha256": page["wikitext_sha256"],
            "revision_timestamp": page["revision_timestamp"],
            "user": page.get("user", ""),
            "sha1": page.get("sha1", ""),
            "categories": list(page.get("categories", [])),
            "permalink_url": page["permalink_url"],
            "history_url": page["history_url"],
        })

    if len(queue) > MAX_RENDERED_PAGES:
        raise ValueError(f"Queue size {len(queue)} exceeds hard cap {MAX_RENDERED_PAGES}")
    return sorted(queue, key=lambda item: (item["title"], item["pageid"], item["revid"]))


def _fetch_single_rendered_item(item: dict[str, Any]) -> dict[str, Any]:
    """Fetch and verify one pinned oldid via MediaWiki action=parse."""
    api_params = {
        "action": "parse",
        "oldid": str(item["revid"]),
        "prop": _API_PROPS,
        "disableeditsection": "1",
        "disablelimitreport": "1",
        "format": "json",
        "formatversion": "2",
    }
    payload = _api_get_json(api_params, retries=3)
    if "error" in payload or "parse" not in payload:
        raise ValueError(f"Official API action=parse failed for revid={item['revid']}: {payload.get('error')}")
    parse_obj = payload["parse"]
    if not isinstance(parse_obj.get("text"), str):
        raise ValueError(f"Official API action=parse omitted HTML text for revid={item['revid']}")
    if int(parse_obj.get("revid", -1)) != int(item["revid"]):
        raise ValueError(f"API parse revid mismatch: {parse_obj.get('revid')} != {item['revid']}")
    if int(parse_obj.get("pageid", -1)) != int(item["pageid"]):
        raise ValueError(f"API parse pageid mismatch: {parse_obj.get('pageid')} != {item['pageid']}")
    if str(parse_obj.get("title", "")) != str(item["title"]):
        raise ValueError(f"API parse title mismatch: {parse_obj.get('title')!r} != {item['title']!r}")

    capture_ts = datetime.now(timezone.utc).isoformat()
    raw_sha = _sha256_canonical_json(payload)
    html_text = parse_obj["text"]
    html_sha = _sha256_text(html_text)
    raw_templates = list(parse_obj.get("templates", []))
    template_deps = sorted({str(t["title"]) for t in raw_templates if t.get("ns") == 10 and "title" in t})
    module_deps = sorted({str(t["title"]) for t in raw_templates if t.get("ns") == 828 and "title" in t})
    other_deps = sorted({str(t["title"]) for t in raw_templates if t.get("ns") not in {10, 828} and "title" in t})
    rl_modules = sorted(str(m) for m in parse_obj.get("modules", []))
    rl_modulestyles = sorted(str(m) for m in parse_obj.get("modulestyles", []))
    deps_sha = _dependencies_digest(template_deps, module_deps, other_deps, rl_modules, rl_modulestyles)

    qtitle = urllib.parse.quote(item["title"].replace(" ", "_"), safe="")
    permalink_url = item.get("permalink_url") or f"https://en.wiktionary.org/w/index.php?title={qtitle}&oldid={item['revid']}"
    history_url = item.get("history_url") or f"https://en.wiktionary.org/w/index.php?title={qtitle}&action=history"

    record = {
        "title": item["title"],
        "pageid": int(item["pageid"]),
        "revid": int(item["revid"]),
        "revision_timestamp": str(item.get("revision_timestamp") or ""),
        "user": str(item.get("user") or ""),
        "sha1": str(item.get("sha1") or ""),
        "wikitext_sha256": item["wikitext_sha256"],
        "categories": list(item.get("categories", [])),
        "permalink_url": permalink_url,
        "history_url": history_url,
        "capture_timestamp_utc": capture_ts,
        "api_endpoint": API_ENDPOINT,
        "api_params": api_params,
        "raw_api_response_sha256": raw_sha,
        "rendered_html": html_text,
        "rendered_html_sha256": html_sha,
        "template_dependencies": template_deps,
        "module_dependencies": module_deps,
        "other_dependencies": other_deps,
        "rl_modules": rl_modules,
        "rl_modulestyles": rl_modulestyles,
        "dependencies_sha256": deps_sha,
        "sections": list(parse_obj.get("sections", [])),
        "parsewarnings": list(parse_obj.get("parsewarnings", [])),
        "displaytitle": str(parse_obj.get("displaytitle") or ""),
        "properties": dict(parse_obj.get("properties") or {}),
        "rendering_attribution": RENDERED_ATTRIBUTION,
    }
    verify_rendered_page(record)
    return record


def _queue_fingerprint(queue: list[dict[str, Any]]) -> str:
    compact = [
        {"title": item["title"], "pageid": int(item["pageid"]), "revid": int(item["revid"]), "wikitext_sha256": item["wikitext_sha256"]}
        for item in queue
    ]
    return _sha256_canonical_json(compact)


def verify_rendered_queue_binding(queue: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
    if manifest.get("queue_sha256") != _queue_fingerprint(queue):
        raise ValueError("Rendered capture queue fingerprint differs from requested pinned queue")


def _write_rendered_notices(directory: Path, manifest: dict[str, Any]) -> None:
    readme = "\n".join([
        "# English Wiktionary Rendered Gap Capture (2026-11-16)",
        "",
        "Bounded official MediaWiki `action=parse&oldid=<revid>` capture for pinned",
        "revisions in the 410-spelling historical Wiktionary gap queue.",
        "",
        "## Truthful Attribution & Verification Boundary",
        "",
        "- `rendered_html` was rendered by MediaWiki using upstream templates and Lua",
        "  modules active at `capture_timestamp_utc`, **not** original wikitext verbatim.",
        "- Every record preserves pinned `pageid`, `revid`, `wikitext_sha256`,",
        "  `capture_timestamp_utc`, `raw_api_response_sha256`, `rendered_html_sha256`,",
        "  `dependencies_sha256`, `template_dependencies`, `module_dependencies`,",
        "  `raw_capture_file_locator`, `permalink_url`, and `history_url`.",
        f"- Total pinned pages captured: `{manifest['total_fetched_pages']}` (hard cap `{MAX_RENDERED_PAGES}`).",
        "- Upstream content remains licensed under CC-BY-SA-4.0 / GFDL per",
        "  https://en.wiktionary.org/wiki/Wiktionary:Copyrights.",
        "- Extraction-ready / proposed candidates only: zero human acceptance decisions,",
        "  zero canonical promotion, and zero historical bundle permissions confirmed",
        "  (user confirmed none; no rights waived).",
        "",
    ])
    (directory / "README.md").write_text(readme, encoding="utf-8", newline="\n")


def acquire_rendered_pages(
    queue: list[dict[str, Any]],
    directory: Path,
    *,
    batch_size: int = 24,
    max_workers: int = 4,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Capture <= 384 exact pinned rendered pages into a resumable hash-verified directory."""
    if len(queue) > MAX_RENDERED_PAGES:
        raise ValueError(f"Requested {len(queue)} pages exceeds MAX_RENDERED_PAGES={MAX_RENDERED_PAGES}")
    if batch_size <= 0 or max_workers <= 0 or max_workers > 4:
        raise ValueError("Bounded batch_size (>0) and max_workers (1..4) required")

    seen_titles: set[str] = set()
    for item in queue:
        if item["title"] in seen_titles:
            raise ValueError(f"Duplicate title in queue: {item['title']!r}")
        seen_titles.add(item["title"])

    directory.mkdir(parents=True, exist_ok=True)
    queue_sha = _queue_fingerprint(queue)
    manifest_path = directory / "manifest.json"
    checkpoint_path = directory / "capture-checkpoint.json"
    raw_files: dict[str, Any] = {}

    if manifest_path.exists():
        previous = verify_rendered_capture(directory)
        if previous.get("queue_sha256") != queue_sha:
            raise ValueError("Existing rendered capture belongs to a different queue")
        pages, manifest = load_rendered_capture(directory)
        return pages, manifest
    elif checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("queue_sha256") != queue_sha:
            raise ValueError("Partial rendered capture belongs to a different queue")
        verify_rendered_raw_files(directory, checkpoint["raw_files"])
        raw_files = dict(checkpoint["raw_files"])
    elif any(directory.glob("batch-*.json")):
        raise ValueError("Cached rendered batches have no manifest or checkpoint hash evidence")

    records_by_title: dict[str, dict[str, Any]] = {}
    capture_dates: set[str] = set()

    for batch_idx, start in enumerate(range(0, len(queue), batch_size)):
        batch_items = queue[start : start + batch_size]
        batch_name = f"batch-{batch_idx:03d}.json"
        batch_path = directory / batch_name
        expected_ids = [(it["title"], int(it["pageid"]), int(it["revid"])) for it in batch_items]

        if batch_path.exists():
            saved = json.loads(batch_path.read_text(encoding="utf-8"))
            saved_ids = [(r["title"], int(r["pageid"]), int(r["revid"])) for r in saved.get("records", [])]
            if saved_ids != expected_ids:
                raise ValueError(f"Existing batch {batch_name} belongs to a different queue slice")
            batch_records = saved["records"]
        else:
            if max_workers == 1 or len(batch_items) == 1:
                batch_records = [_fetch_single_rendered_item(item) for item in batch_items]
            else:
                fetched_map: dict[str, dict[str, Any]] = {}
                with ThreadPoolExecutor(max_workers=max_workers) as pool:
                    fut_map = {pool.submit(_fetch_single_rendered_item, item): item["title"] for item in batch_items}
                    for fut in as_completed(fut_map):
                        rec = fut.result()
                        fetched_map[rec["title"]] = rec
                batch_records = [fetched_map[item["title"]] for item in batch_items]
            saved = {
                "batch_idx": batch_idx,
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                "records": batch_records,
            }
            _write_json(batch_path, saved)

        batch_sha = digest(batch_path)
        raw_files[batch_name] = batch_sha
        _write_json(checkpoint_path, {"queue_sha256": queue_sha, "raw_files": raw_files})

        for rec_idx, rec in enumerate(batch_records):
            rec_with_loc = {
                **rec,
                "raw_capture_file_locator": {
                    "batch_file": batch_name,
                    "batch_sha256": batch_sha,
                    "record_index": rec_idx,
                },
            }
            verify_rendered_page(rec_with_loc)
            records_by_title[rec_with_loc["title"]] = rec_with_loc
            capture_dates.add(rec_with_loc["capture_timestamp_utc"][:10])

    sorted_titles = sorted(records_by_title)
    encoded = "".join(json.dumps(records_by_title[t], ensure_ascii=True, sort_keys=True) + "\n" for t in sorted_titles).encode("utf-8")
    gz_path = directory / "pages.jsonl.gz"
    with gz_path.open("wb") as raw_out:
        with gzip.GzipFile(filename="pages.jsonl", mode="wb", fileobj=raw_out, mtime=0) as gz:
            gz.write(encoded)

    manifest = {
        "schema_version": 1,
        "schema": "enwiktionary-tamil-rendered-capture-v1",
        "api_endpoint": API_ENDPOINT,
        "rendering_attribution": RENDERED_ATTRIBUTION,
        "max_rendered_pages": MAX_RENDERED_PAGES,
        "queue_sha256": queue_sha,
        "requested_page_count": len(queue),
        "total_fetched_pages": len(sorted_titles),
        "capture_dates": sorted(capture_dates),
        "snapshot_date": max(capture_dates, default=""),
        "raw_files": raw_files,
        "pages_jsonl_gz_sha256": digest(gz_path),
        "pages_uncompressed_sha256": hashlib.sha256(encoded).hexdigest(),
        "license_evidence": "https://en.wiktionary.org/wiki/Wiktionary:Copyrights",
        "historical_bundle_permissions_confirmed": "none",
        "reuse_note": (
            "MediaWiki action=parse rendered output evaluated against upstream templates/modules "
            "at capture_timestamp_utc; not original wikitext verbatim; zero acceptance decisions."
        ),
    }
    _write_json(manifest_path, manifest)
    _write_rendered_notices(directory, manifest)
    verify_rendered_capture(directory)
    return records_by_title, manifest


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[_Node | str] = field(default_factory=list)

    def classes(self) -> set[str]:
        cls = self.attrs.get("class", "")
        return set(cls.split()) if cls else set()


class _DomBuilder(HTMLParser):
    """Lightweight deterministic DOM builder using stdlib HTMLParser."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("root")
        self.stack: list[_Node] = [self.root]
        self._raw_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        attr_map = {k.lower(): ("" if v is None else v) for k, v in attrs}
        node = _Node(t, attr_map)
        self.stack[-1].children.append(node)
        if t in _VOID_TAGS:
            return
        self.stack.append(node)
        if t in _RAW_TEXT_TAGS:
            self._raw_tag = t

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        attr_map = {k.lower(): ("" if v is None else v) for k, v in attrs}
        self.stack[-1].children.append(_Node(t, attr_map))

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if self._raw_tag is not None:
            if t != self._raw_tag:
                return
            self._raw_tag = None
        for idx in range(len(self.stack) - 1, 0, -1):
            if self.stack[idx].tag == t:
                del self.stack[idx:]
                break

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].children.append(data)


def _parse_html_dom(html: str) -> _Node:
    parser = _DomBuilder()
    parser.feed(html)
    parser.close()
    return parser.root


def _plain_text(node: _Node | str) -> str:
    if isinstance(node, str):
        return node
    if node.tag in _RAW_TEXT_TAGS:
        return ""
    return "".join(_plain_text(ch) for ch in node.children)


def _find_first(node: _Node, predicate) -> _Node | None:
    for ch in node.children:
        if isinstance(ch, _Node):
            if predicate(ch):
                return ch
            found = _find_first(ch, predicate)
            if found is not None:
                return found
    return None


def _find_all(node: _Node, predicate) -> list[_Node]:
    out: list[_Node] = []
    for ch in node.children:
        if isinstance(ch, _Node):
            if predicate(ch):
                out.append(ch)
            out.extend(_find_all(ch, predicate))
    return out


def _extract_heading(node: _Node) -> tuple[int, str, str] | None:
    if node.tag in {"h2", "h3", "h4", "h5", "h6"}:
        txt = re.sub(r"\s+", " ", _plain_text(node)).strip()
        txt = re.sub(r"\[\s*edit\s*\]$", "", txt).strip()
        return int(node.tag[1]), txt, node.attrs.get("id", "")
    if node.tag == "div" and "mw-heading" in node.classes():
        for ch in node.children:
            if isinstance(ch, _Node) and ch.tag in {"h2", "h3", "h4", "h5", "h6"}:
                txt = re.sub(r"\s+", " ", _plain_text(ch)).strip()
                txt = re.sub(r"\[\s*edit\s*\]$", "", txt).strip()
                return int(ch.tag[1]), txt, ch.attrs.get("id", "")
    return None


def _split_ib_content_tokens(ib_node: _Node, *, split_on_commas: bool) -> list[str]:
    """Split an ib-content span cleanly on <span class='ib-comma'> and optional commas."""
    segments: list[str] = []
    buf: list[str] = []
    for ch in ib_node.children:
        if isinstance(ch, str):
            buf.append(ch)
        elif ch.tag == "span" and "ib-comma" in ch.classes():
            seg = re.sub(r"\s+", " ", "".join(buf)).strip()
            if seg:
                segments.append(seg)
            buf.clear()
        else:
            buf.append(_plain_text(ch))
    tail = re.sub(r"\s+", " ", "".join(buf)).strip()
    if tail:
        segments.append(tail)

    if not split_on_commas:
        return segments

    tokens: list[str] = []
    for seg in segments:
        for part in seg.split(","):
            cleaned = re.sub(r"\s+", " ", part).strip()
            if cleaned:
                tokens.append(cleaned)
    return tokens


def _classify_rendered_ib_content(
    ib_node: _Node,
    *,
    allow_bang: bool,
    raw_template: str,
    line_number: int | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Classify rendered label-content or qualifier-content tokens into reviewed dimensions."""
    mapped_list: list[dict[str, Any]] = []
    unmapped_list: list[dict[str, Any]] = []
    tokens = _split_ib_content_tokens(ib_node, split_on_commas=allow_bang)
    negated_region = False

    def classify_one(tok: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        nonlocal negated_region
        norm_tok = re.sub(r"\s+", " ", tok.strip().lower())
        if not norm_tok or norm_tok in DOMAIN_LABEL_IGNORE:
            return None, None
        if norm_tok in NEGATING_REGION_PREFIXES:
            negated_region = True
        _, mapped, unmapped = _classify_label_token(
            tok,
            raw_template=raw_template,
            allow_bang=allow_bang,
            negated_region_context=negated_region,
        )
        return mapped, unmapped

    for tok in tokens:
        mapped, unmapped = classify_one(tok)
        if mapped is not None:
            if line_number is not None:
                mapped["line_number"] = line_number
            mapped_list.append(mapped)
            continue
        if unmapped is None:
            continue

        recovered = False
        if allow_bang:
            conj_parts = [p.strip() for p in re.split(r"\s+(?:and|or)\s+", tok, flags=re.IGNORECASE) if p.strip()]
            if len(conj_parts) > 1:
                probe_mapped: list[dict[str, Any]] = []
                probe_ok = True
                local_neg = negated_region
                for part in conj_parts:
                    p_norm = re.sub(r"\s+", " ", part.lower())
                    if p_norm in NEGATING_REGION_PREFIXES:
                        local_neg = True
                    if p_norm in DOMAIN_LABEL_IGNORE:
                        continue
                    _, pm, _ = _classify_label_token(
                        part,
                        raw_template=raw_template,
                        allow_bang=True,
                        negated_region_context=local_neg,
                    )
                    if pm is None:
                        probe_ok = False
                        break
                    probe_mapped.append(pm)
                if probe_ok and probe_mapped:
                    negated_region = local_neg
                    for pm in probe_mapped:
                        if line_number is not None:
                            pm["line_number"] = line_number
                        mapped_list.append(pm)
                    recovered = True

            if not recovered and " " in tok:
                words = tok.split()
                for split_idx in range(1, len(words)):
                    prefix = " ".join(words[:split_idx]).lower()
                    suffix = " ".join(words[split_idx:])
                    if prefix in DOMAIN_LABEL_IGNORE and prefix not in NEGATING_REGION_PREFIXES:
                        _, sm, _ = _classify_label_token(
                            suffix,
                            raw_template=raw_template,
                            allow_bang=True,
                            negated_region_context=negated_region,
                        )
                        if sm is not None:
                            if line_number is not None:
                                sm["line_number"] = line_number
                            mapped_list.append(sm)
                            recovered = True
                            break

        if not recovered:
            if line_number is not None:
                unmapped["line_number"] = line_number
            unmapped_list.append(unmapped)

    return mapped_list, unmapped_list


def _collect_direct_sense_from_li(li_node: _Node, li_index: int) -> dict[str, Any]:
    """Extract direct sense gloss & qualifiers from one <li>, excluding nested lists/citations."""
    text_parts: list[str] = []
    qualifiers: list[dict[str, Any]] = []
    unmapped_qualifiers: list[dict[str, Any]] = []
    nested_lists = {"dl": 0, "ul": 0, "ol": 0}
    ref_markers_excluded = 0
    saw_error: str | None = None

    def walk(node: _Node | str) -> None:
        nonlocal ref_markers_excluded, saw_error
        if saw_error is not None:
            return
        if isinstance(node, str):
            text_parts.append(node)
            return

        cls = node.classes()
        if "scribunto-error" in cls or (node.tag == "strong" and "error" in cls):
            saw_error = "WIKTIONARY_SCRIPT_ERROR_REJECTED"
            return
        if "maintenance-box" in cls or "request-box" in cls:
            saw_error = "UNSUPPORTED_RENDERED_MAINTENANCE_BOX"
            return

        if node.tag in {"dl", "ul", "ol"}:
            nested_lists[node.tag] += 1
            return
        if node.tag == "style":
            return
        if node.tag == "sup" and "reference" in cls:
            ref_markers_excluded += 1
            return
        if node.tag in _DISALLOWED_DIRECT_SENSE_TAGS:
            saw_error = f"UNSUPPORTED_RENDERED_HTML_ELEMENT:{node.tag}"
            return

        if node.tag == "span" and "ib-content" in cls:
            if "label-content" in cls:
                m_q, u_q = _classify_rendered_ib_content(
                    node,
                    allow_bang=True,
                    raw_template="rendered:usage-label-sense",
                    line_number=li_index,
                )
                qualifiers.extend(m_q)
                unmapped_qualifiers.extend(u_q)
            elif "qualifier-content" in cls:
                m_q, u_q = _classify_rendered_ib_content(
                    node,
                    allow_bang=False,
                    raw_template="rendered:qualifier",
                    line_number=li_index,
                )
                qualifiers.extend(m_q)
                unmapped_qualifiers.extend(u_q)

        for ch in node.children:
            walk(ch)

    for child in li_node.children:
        walk(child)

    if saw_error is not None:
        return {"ok": False, "reason_code": saw_error, "nested_lists_excluded": nested_lists}

    raw_gloss = "".join(text_parts)
    cleaned = re.sub(r"\s+", " ", raw_gloss).strip()
    if not cleaned:
        return {"ok": False, "reason_code": "EMPTY_GLOSS_REJECTED", "nested_lists_excluded": nested_lists}
    if "{{" in cleaned or "}}" in cleaned or "[[" in cleaned or "]]" in cleaned or "<!--" in cleaned:
        return {"ok": False, "reason_code": "RESIDUAL_MARKUP_REJECTED", "nested_lists_excluded": nested_lists}
    for marker, reason in FORBIDDEN_SENSE_MARKERS:
        if marker in cleaned:
            return {"ok": False, "reason_code": reason, "nested_lists_excluded": nested_lists}
    if TAMIL_CHAR_RE.search(cleaned):
        return {"ok": False, "reason_code": "TAMIL_IN_ENGLISH_GLOSS_REJECTED", "nested_lists_excluded": nested_lists}

    u_ok, u_err, u_meta = check_unicode_scalar_integrity(cleaned)
    if not u_ok:
        return {"ok": False, "reason_code": f"SENSE_{u_err}", "unicode_detail": u_meta, "nested_lists_excluded": nested_lists}

    return {
        "ok": True,
        "component": "definition",
        "meaning_en": u_meta["normalized_text"],
        "nfc_normalized": u_meta["nfc_normalized"],
        "qualifiers": qualifiers,
        "unmapped_qualifiers": unmapped_qualifiers,
        "reference_markers_excluded": ref_markers_excluded,
        "nested_lists_excluded": nested_lists,
    }


def _build_rendered_evidence(
    page: dict[str, Any],
    *,
    manifest_sha256: str | None = None,
    manifest_path: str | None = None,
    pages_jsonl_gz_sha256: str | None = None,
) -> dict[str, Any]:
    """Construct per-entry rendered_evidence provenance without representing HTML as original wikitext."""
    raw_locator = dict(page.get("raw_capture_file_locator") or {})
    if manifest_path is not None:
        raw_locator["manifest_path"] = manifest_path
    if pages_jsonl_gz_sha256 is not None:
        raw_locator["pages_jsonl_gz_sha256"] = pages_jsonl_gz_sha256

    return {
        "source_kind": "rendered_html",
        "source_origin": RENDERED_SOURCE_ORIGIN,
        "extraction_method": RENDERED_EXTRACTION_METHOD,
        "extraction_version": RENDERED_EXTRACTION_VERSION,
        "rendering_attribution": page["rendering_attribution"],
        "capture_timestamp_utc": page["capture_timestamp_utc"],
        "api_endpoint": page["api_endpoint"],
        "api_params": page.get("api_params", {}),
        "raw_api_response_sha256": page["raw_api_response_sha256"],
        "html_sha256": page["rendered_html_sha256"],
        "raw_capture_manifest_sha256": manifest_sha256,
        "raw_capture_file_locator": raw_locator,
        "template_module_dependencies": {
            "dependencies_sha256": page["dependencies_sha256"],
            "template_dependencies": list(page.get("template_dependencies", [])),
            "module_dependencies": list(page.get("module_dependencies", [])),
            "other_dependencies": list(page.get("other_dependencies", [])),
            "rl_modules": list(page.get("rl_modules", [])),
            "rl_modulestyles": list(page.get("rl_modulestyles", [])),
            "limits_and_caveats": RENDERED_LIMITS_CAVEAT,
        },
    }


def parse_rendered_page(
    page: dict[str, Any],
    *,
    check_native: bool = False,
    manifest_sha256: str | None = None,
    manifest_path: str | None = None,
    pages_jsonl_gz_sha256: str | None = None,
) -> dict[str, Any]:
    """Parse one verified rendered Wiktionary page fail-closed with full provenance."""
    verify_rendered_page(page)
    pageid = int(page["pageid"])
    revid = int(page["revid"])
    raw_title = str(page["title"])
    html = str(page["rendered_html"])
    categories = list(page.get("categories", []))

    exclusions: list[dict[str, Any]] = []
    extracted_entries: list[dict[str, Any]] = []
    pos_occurrence_counts: Counter[str] = Counter()

    u_ok, u_err, u_meta = check_unicode_scalar_integrity(raw_title)
    if not u_ok:
        exclusions.append({"pageid": pageid, "revid": revid, "title": raw_title, "reason_code": f"HEADWORD_{u_err}", "detail": u_meta})
        return {"pageid": pageid, "revid": revid, "entries": [], "exclusions": exclusions}

    headword = u_meta["normalized_text"]
    if not TAMIL_CHAR_RE.search(headword):
        exclusions.append({"pageid": pageid, "revid": revid, "title": headword, "reason_code": "NON_TAMIL_HEADWORD_REJECTED"})
        return {"pageid": pageid, "revid": revid, "entries": [], "exclusions": exclusions}

    if check_native:
        inspected = native_inspect(headword)
        if not inspected.get("is_nfc"):
            exclusions.append({"pageid": pageid, "revid": revid, "title": headword, "reason_code": "HEADWORD_RUST_NON_NFC_REJECTED"})
            return {"pageid": pageid, "revid": revid, "entries": [], "exclusions": exclusions}

    dom = _parse_html_dom(html)
    container = _find_first(dom, lambda n: n.tag == "div" and "mw-parser-output" in n.classes()) or dom

    in_tamil = False
    found_tamil_section = False
    in_pos = False
    current_pos: str | None = None
    current_entry: dict[str, Any] | None = None
    current_etymology_index = 0
    current_etymology_heading = ""

    rendered_ev = _build_rendered_evidence(
        page,
        manifest_sha256=manifest_sha256,
        manifest_path=manifest_path,
        pages_jsonl_gz_sha256=pages_jsonl_gz_sha256,
    )

    for child in container.children:
        if not isinstance(child, _Node):
            continue

        if child.tag == "hr":
            in_tamil = False
            in_pos = False
            current_pos = None
            current_entry = None
            continue

        heading_info = _extract_heading(child)
        if heading_info is not None:
            level, heading_text, anchor = heading_info
            if level == 2:
                in_tamil = heading_text == "Tamil"
                if in_tamil:
                    found_tamil_section = True
                else:
                    exclusions.append({
                        "pageid": pageid,
                        "revid": revid,
                        "reason_code": "NON_TAMIL_SECTION_EXCLUDED",
                        "heading": heading_text,
                    })
                in_pos = False
                current_pos = None
                current_entry = None
                continue

            if not in_tamil:
                continue

            base_heading = re.sub(r"\s+\d+$", "", heading_text)
            if base_heading == "Etymology":
                current_etymology_index += 1
                current_etymology_heading = heading_text

            if heading_text in POS_HEADING_MAP:
                pos_code = POS_HEADING_MAP[heading_text]
                pos_occ_idx = pos_occurrence_counts[pos_code]
                pos_occurrence_counts[pos_code] += 1
                current_pos = pos_code
                in_pos = True
                current_entry = {
                    "pageid": pageid,
                    "revid": revid,
                    "revision_timestamp": page.get("revision_timestamp", ""),
                    "user": page.get("user", ""),
                    "sha1": page.get("sha1", ""),
                    "wikitext_sha256": page["wikitext_sha256"],
                    "permalink_url": page["permalink_url"],
                    "history_url": page["history_url"],
                    "categories": categories,
                    "headword": headword,
                    "headword_nfc_normalized": u_meta["nfc_normalized"],
                    "pos_code": pos_code,
                    "pos_heading": heading_text,
                    "pos_anchor": anchor,
                    "pos_line": None,
                    "pos_lines": [],
                    "etymology_index": current_etymology_index,
                    "etymology_heading": current_etymology_heading,
                    "pos_occurrence_index": pos_occ_idx,
                    "entry_qualifiers": [],
                    "unmapped_entry_qualifiers": [],
                    "senses": [],
                    "source_origin": RENDERED_SOURCE_ORIGIN,
                    "extraction_method": RENDERED_EXTRACTION_METHOD,
                    "extraction_version": RENDERED_EXTRACTION_VERSION,
                    "rendering_attribution": page["rendering_attribution"],
                    "capture_timestamp_utc": page["capture_timestamp_utc"],
                    "api_endpoint": page["api_endpoint"],
                    "raw_api_response_sha256": page["raw_api_response_sha256"],
                    "rendered_html_sha256": page["rendered_html_sha256"],
                    "dependencies_sha256": page["dependencies_sha256"],
                    "template_dependency_count": len(page.get("template_dependencies", [])),
                    "module_dependency_count": len(page.get("module_dependencies", [])),
                    "rendered_evidence": rendered_ev,
                }
                extracted_entries.append(current_entry)
            else:
                in_pos = False
                current_pos = None
                current_entry = None
                reason = NON_DEFINITION_SECTIONS.get(base_heading, f"UNMAPPED_SUBSECTION_EXCLUDED:{base_heading}")
                exclusions.append({
                    "pageid": pageid,
                    "revid": revid,
                    "reason_code": reason,
                    "heading": heading_text,
                })
            continue

        if not (in_tamil and in_pos and current_entry is not None):
            continue

        if child.tag == "p":
            hw_span = _find_first(child, lambda n: n.tag == "span" and "headword-line" in n.classes())
            if hw_span is not None:
                for term_label in _find_all(child, lambda n: n.tag == "span" and "usage-label-term" in n.classes()):
                    for ib in _find_all(term_label, lambda n: n.tag == "span" and "ib-content" in n.classes() and "label-content" in n.classes()):
                        m_eq, u_eq = _classify_rendered_ib_content(ib, allow_bang=True, raw_template="rendered:usage-label-term")
                        current_entry["entry_qualifiers"].extend(m_eq)
                        current_entry["unmapped_entry_qualifiers"].extend(u_eq)
            continue

        if child.tag == "ol" and "references" not in child.classes():
            li_idx = 0
            for li in child.children:
                if not isinstance(li, _Node) or li.tag != "li":
                    continue
                if "mw-empty-elt" in li.classes() and not re.sub(r"\s+", "", _plain_text(li)):
                    continue
                li_idx += 1
                parsed_sense = _collect_direct_sense_from_li(li, li_idx)
                nested_counts = parsed_sense.get("nested_lists_excluded") or {}
                if nested_counts.get("ol", 0) > 0:
                    exclusions.append({
                        "pageid": pageid,
                        "revid": revid,
                        "pos_code": current_pos,
                        "li_index": li_idx,
                        "reason_code": "SUBSENSE_LIST_EXCLUDED",
                    })
                if not parsed_sense["ok"]:
                    exclusions.append({
                        "pageid": pageid,
                        "revid": revid,
                        "pos_code": current_pos,
                        "li_index": li_idx,
                        "reason_code": parsed_sense["reason_code"],
                    })
                    continue

                ordinal = len(current_entry["senses"]) + 1
                current_entry["senses"].append({
                    "ordinal": ordinal,
                    "li_index": li_idx,
                    "section_anchor": current_entry["pos_anchor"],
                    "line_number": None,
                    "char_range": None,
                    "byte_range": None,
                    "component": parsed_sense["component"],
                    "meaning_en": parsed_sense["meaning_en"],
                    "qualifiers": parsed_sense["qualifiers"],
                    "unmapped_qualifiers": parsed_sense["unmapped_qualifiers"],
                    "templates_used": ["rendered_html"],
                    "reference_markers_excluded": parsed_sense["reference_markers_excluded"],
                    "nested_lists_excluded": nested_counts,
                    "rendered_html_sha256": page["rendered_html_sha256"],
                })

    if not found_tamil_section:
        exclusions.append({"pageid": pageid, "revid": revid, "title": headword, "reason_code": "NO_TAMIL_SECTION_EXCLUDED"})
        return {"pageid": pageid, "revid": revid, "entries": [], "exclusions": exclusions}

    valid_entries: list[dict[str, Any]] = []
    for entry_obj in extracted_entries:
        pos_code = entry_obj["pos_code"]
        if not entry_obj["senses"]:
            exclusions.append({
                "pageid": pageid,
                "revid": revid,
                "title": headword,
                "pos_code": pos_code,
                "pos_occurrence_index": entry_obj["pos_occurrence_index"],
                "etymology_index": entry_obj["etymology_index"],
                "reason_code": "ENTRY_NO_VALID_SENSES_REMAINING",
            })
            continue
        alloc_key = (
            f"enwiktionary:rendered:page:{pageid}:rev:{revid}:tam:{pos_code}"
            f":ety:{entry_obj['etymology_index']}:occ:{entry_obj['pos_occurrence_index']}"
        )
        entry_id = allocate_id("ent", RENDERED_NAMESPACE, alloc_key)
        pack_id, pack_reason = assign_pack(entry_obj)
        entry_obj["entry_id"] = entry_id
        entry_obj["pack_id"] = pack_id
        entry_obj["pack_reason"] = pack_reason
        valid_entries.append(entry_obj)

    return {"pageid": pageid, "revid": revid, "entries": valid_entries, "exclusions": exclusions}


def reconcile_rendered_queue(
    queue_records: list[dict[str, Any]],
    pages: dict[str, dict[str, Any]],
    *,
    check_native: bool = False,
    manifest_sha256: str | None = None,
    manifest_path: str | None = None,
    pages_jsonl_gz_sha256: str | None = None,
) -> dict[str, Any]:
    """Extract candidates from rendered pages and emit bulk-compatible JSON with blocked reasons."""
    records: list[dict[str, Any]] = []
    candidate_entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    blocker_page_counts: Counter[str] = Counter()
    pack_counts: Counter[str] = Counter()
    pos_counts: Counter[str] = Counter()

    for item in sorted(queue_records, key=lambda r: r["headword"]):
        title = item["headword"]
        if title in seen:
            raise ValueError(f"Duplicate headword in rendered reconciliation: {title!r}")
        seen.add(title)
        row = {**item, "historical_claims_approved": False}
        page = pages.get(title)
        if page is None:
            row.update(status="missing_from_snapshot", blocker_counts={})
            records.append(row)
            continue

        if page["title"] != title:
            raise ValueError("Rendered source page title mismatch")
        source = item.get("source", {})
        if item.get("status") == "missing_from_snapshot" or any(page.get(key) != source.get(key) for key in ("pageid", "revid", "wikitext_sha256")):
            raise ValueError("Rendered source identity differs from pinned reconciliation record")
        parsed = parse_rendered_page(
            page,
            check_native=check_native,
            manifest_sha256=manifest_sha256,
            manifest_path=manifest_path,
            pages_jsonl_gz_sha256=pages_jsonl_gz_sha256,
        )
        b_counts = dict(sorted(Counter(e["reason_code"] for e in parsed["exclusions"]).items()))
        if parsed["entries"]:
            status = "rendered_recoverable_candidate"
            for entry in parsed["entries"]:
                pack_counts[entry["pack_id"]] += 1
                pos_counts[entry["pos_code"]] += 1
        else:
            status = "rendered_parser_blocked"
            for code in b_counts:
                blocker_page_counts[code] += 1

        row.update(
            status=status,
            rendered_source={
                "source_kind": "rendered_html",
                "pageid": page["pageid"],
                "revid": page["revid"],
                "wikitext_sha256": page["wikitext_sha256"],
                "capture_timestamp_utc": page["capture_timestamp_utc"],
                "raw_api_response_sha256": page["raw_api_response_sha256"],
                "rendered_html_sha256": page["rendered_html_sha256"],
                "dependencies_sha256": page["dependencies_sha256"],
                "raw_capture_manifest_sha256": manifest_sha256,
                "raw_capture_file_locator": page.get("raw_capture_file_locator"),
                "template_dependency_count": len(page.get("template_dependencies", [])),
                "module_dependency_count": len(page.get("module_dependencies", [])),
                "rendering_attribution": page["rendering_attribution"],
                "permalink_url": page["permalink_url"],
                "history_url": page["history_url"],
            },
            blocker_counts=b_counts,
            extracted_entry_ids=[e["entry_id"] for e in parsed["entries"]],
            extracted_senses=sum(len(e["senses"]) for e in parsed["entries"]),
        )
        candidate_entries.extend(parsed["entries"])
        records.append(row)

    candidate_entries.sort(
        key=lambda e: (
            e["headword"],
            e["pos_code"],
            e["pageid"],
            int(e.get("pos_occurrence_index") or 0),
            int(e.get("etymology_index") or 0),
        )
    )
    return {
        "schema_version": 1,
        "schema": "wiktionary-rendered-candidate-report-v1",
        "source_kind": "rendered_html",
        "source_origin": RENDERED_SOURCE_ORIGIN,
        "extraction_method": RENDERED_EXTRACTION_METHOD,
        "extraction_version": RENDERED_EXTRACTION_VERSION,
        "verification_stage": "extraction_ready_proposed_only",
        "acceptance_decisions": 0,
        "canonical_promoted": False,
        "historical_bundle_permissions_confirmed": "none",
        "status_counts": dict(sorted(Counter(r["status"] for r in records).items())),
        "pack_counts": dict(sorted(pack_counts.items())),
        "pos_counts": dict(sorted(pos_counts.items())),
        "blocked_page_reason_counts": dict(blocker_page_counts.most_common()),
        "candidate_entry_count": len(candidate_entries),
        "candidate_senses": sum(len(e["senses"]) for e in candidate_entries),
        "candidate_entries": candidate_entries,
        "records": records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconciliation", type=Path, default=DEFAULT_RECONCILIATION_PATH)
    parser.add_argument("--bulk-snapshot-dir", type=Path, default=DEFAULT_BULK_SNAPSHOT_DIR)
    parser.add_argument("--supplemental-dir", type=Path, default=DEFAULT_SUPPLEMENTAL_DIR)
    parser.add_argument("--source-dir", type=Path, default=RENDERED_SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=RENDERED_OUTPUT_DIR)
    parser.add_argument("--only-blocked", action="store_true")
    parser.add_argument("--fetch", action="store_true", help="Acquire rendered pages via official action=parse if not cached")
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--check-native", action="store_true")
    args = parser.parse_args(argv)

    source_dir = validate_rendered_source_dir(args.source_dir)
    output_dir = args.output_dir.resolve()
    if not output_dir.is_relative_to((ROOT / "target/lexicon").resolve()):
        parser.error("Rendered candidate outputs must stay under target/lexicon")

    queue = build_rendered_queue(
        reconciliation_path=args.reconciliation,
        bulk_snapshot_dir=args.bulk_snapshot_dir,
        supplemental_dir=args.supplemental_dir,
        only_blocked=args.only_blocked,
    )
    if args.fetch:
        pages, manifest = acquire_rendered_pages(
            queue,
            source_dir,
            batch_size=args.batch_size,
            max_workers=args.workers,
        )
    else:
        pages, manifest = load_rendered_capture(source_dir)

    verify_rendered_queue_binding(queue, manifest)

    manifest_sha = digest(source_dir / "manifest.json")
    manifest_rel = source_dir.relative_to(ROOT).as_posix() + "/manifest.json"
    gz_sha = manifest["pages_jsonl_gz_sha256"]

    rec_data = json.loads(args.reconciliation.read_text(encoding="utf-8"))
    queue_records = [r for r in rec_data["records"] if not (args.only_blocked and r.get("status") != "source_present_parser_blocked")]
    report = reconcile_rendered_queue(
        queue_records,
        pages,
        check_native=args.check_native,
        manifest_sha256=manifest_sha,
        manifest_path=manifest_rel,
        pages_jsonl_gz_sha256=gz_sha,
    )
    report["capture_manifest"] = manifest
    report["capture_manifest_sha256"] = manifest_sha
    report["parser_sha256"] = digest(Path(__file__))
    _write_json(output_dir / "rendered-reconciliation.json", report)
    _write_json(output_dir / "rendered-candidates.json", {
        "schema_version": 1,
        "schema": "wiktionary-rendered-candidates-v1",
        "source_kind": "rendered_html",
        "source_origin": RENDERED_SOURCE_ORIGIN,
        "extraction_method": RENDERED_EXTRACTION_METHOD,
        "extraction_version": RENDERED_EXTRACTION_VERSION,
        "verification_stage": "extraction_ready_proposed_only",
        "acceptance_decisions": 0,
        "canonical_promoted": False,
        "historical_bundle_permissions_confirmed": "none",
        "capture_manifest_sha256": manifest_sha,
        "candidate_entries": report["candidate_entries"],
    })
    print(json.dumps({
        "status_counts": report["status_counts"],
        "pack_counts": report["pack_counts"],
        "pos_counts": report["pos_counts"],
        "candidate_entries": report["candidate_entry_count"],
        "candidate_senses": report["candidate_senses"],
    }, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

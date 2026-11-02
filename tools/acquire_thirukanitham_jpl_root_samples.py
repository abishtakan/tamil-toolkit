#!/usr/bin/env python3
"""Acquire pinned JPL samples around Thirukanitham civil-day and solar roots.

Run from the repository root. This downloads raw public Horizons responses;
it does not import or invoke the toolkit calculation engine.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path("tests/reference/calendar-thirukanitham-v1")
RAW = ROOT / "horizons"
INPUT = ROOT / "derived-civil-day-and-month-reports.json"
MANIFEST = ROOT / "horizons-root-request-manifest.json"
ENDPOINT = "https://ssd.jpl.nasa.gov/api/horizons.api"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def stamp(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%b-%d %H:%M:%S.000")


def windows(data: dict[str, object]) -> list[dict[str, object]]:
    result: dict[tuple[str, int], dict[str, object]] = {}
    for month in data["month_coverage"]:
        epoch = int(month["ingress_utc_seconds"])
        result[("solar_ingress", epoch)] = {
            "kind": "solar_ingress",
            "root_utc_seconds": epoch,
            "half_width_seconds": 5,
            "evidence_key": f"solar-year-{month['solar_year']}-month-{month['month']:02}",
            "bodies": ["10"],
        }
    # The next ingress after the final recorded month is the exclusive end of
    # public coverage. It is not another public month row, but it still needs
    # an independent physical root bracket.
    terminal = data["month_coverage"][-1]
    terminal_epoch = int(terminal["next_ingress_utc_seconds"])
    terminal_month = int(terminal["month"]) + 1
    terminal_year = int(terminal["solar_year"])
    if terminal_month > 12:
        terminal_month = 1
        terminal_year += 1
    result[("solar_ingress", terminal_epoch)] = {
        "kind": "solar_ingress",
        "root_utc_seconds": terminal_epoch,
        "half_width_seconds": 5,
        "evidence_key": f"solar-year-{terminal_year}-month-{terminal_month:02}-terminal",
        "bodies": ["10"],
        "terminal_after_public_coverage": True,
        "solar_year": terminal_year,
        "month": terminal_month,
    }
    for report in data["civil_day_reports"]:
        for event in report["transitions"]:
            epoch = int(event["instant_utc_seconds"])
            key = ("limb_transition", epoch)
            window = result.setdefault(
                key,
                {
                    "kind": "limb_transition",
                    "root_utc_seconds": epoch,
                    "half_width_seconds": 30,
                    "evidence_key": "selected-civil-day-reports",
                    "bodies": ["10", "301"],
                    "transitions": [],
                },
            )
            window["transitions"].append(
                {
                    "date": report["date"],
                    "region": report["region"],
                    "elevation_meters": report["elevation_meters"],
                    "limb": event["limb"],
                    "from_index": event["from_index"],
                    "to_index": event["to_index"],
                }
            )
    return sorted(result.values(), key=lambda row: (row["root_utc_seconds"], row["kind"]))


def request_parameters(body: str, start: int, stop: int, intervals: int) -> list[tuple[str, str]]:
    return [
        ("format", "json"),
        ("COMMAND", f"'{body}'"),
        ("OBJ_DATA", "'YES'"),
        ("MAKE_EPHEM", "'YES'"),
        ("EPHEM_TYPE", "'OBSERVER'"),
        ("CENTER", "'500@399'"),
        ("START_TIME", f"'{stamp(start)}'"),
        ("STOP_TIME", f"'{stamp(stop)}'"),
        ("STEP_SIZE", f"'{intervals}'"),
        ("TIME_TYPE", "'UT'"),
        ("TIME_DIGITS", "'FRACSEC'"),
        ("QUANTITIES", "'31'"),
        ("APPARENT", "'AIRLESS'"),
        ("REF_SYSTEM", "'ICRF'"),
        ("CSV_FORMAT", "'YES'"),
        ("CAL_TYPE", "'GREGORIAN'"),
    ]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    projection = json.loads(INPUT.read_text(encoding="utf-8"))
    root_windows = windows(projection)
    projection_hash = sha256(INPUT.read_bytes())
    old_manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    if (
        old_manifest.get("input_projection_sha256") not in (None, projection_hash)
        and old_manifest.get("root_windows") != root_windows
    ):
        raise ValueError("existing root manifest selects different root windows")
    manifest: dict[str, object] = {
        "title": "JPL Horizons second-cadence root sample manifest",
        "acquisition_script": str(Path(__file__)).replace("\\", "/"),
        "acquisition_script_sha256": sha256(Path(__file__).read_bytes()),
        "api_documentation": "https://ssd-api.jpl.nasa.gov/doc/horizons.html",
        "coordinate_output": "DE441 geocentric observer apparent-airless ecliptic longitude/latitude; center 500@399; UTC/UT; quantity 31",
        "input_projection": str(INPUT).replace("\\", "/"),
        "input_projection_sha256": projection_hash,
        "root_windows": root_windows,
        "sample_definition": "One-second JPL samples cover ±5 seconds around each public month ingress and the terminal ingress immediately after public coverage, plus ±30 seconds around each selected limb transition. The windows select samples; independent roots are classified from JPL positions and ERFA/P03 transforms.",
        "queries": old_manifest.get("queries", []),
    }
    request_rows = manifest["queries"]
    existing_by_path = {row["response_path"]: row for row in request_rows}
    existing_count = len(request_rows)
    for index, window in enumerate(root_windows, start=1):
        root = int(window["root_utc_seconds"])
        half_width = int(window["half_width_seconds"])
        start, stop = root - half_width, root + half_width
        intervals = stop - start
        for body in window["bodies"]:
            params = request_parameters(body, start, stop, intervals)
            url = ENDPOINT + "?" + urlencode(params)
            body_name = "sun" if body == "10" else "moon"
            path = RAW / f"horizons_root_{body_name}_{window['kind']}_{root}.json"
            path_key = str(path).replace("\\", "/")
            if path_key in existing_by_path:
                saved = path.read_bytes()
                if sha256(saved) != existing_by_path[path_key]["response_sha256"]:
                    raise ValueError(f"saved raw JPL response digest mismatch: {path}")
                continue
            with urlopen(url, timeout=90) as response:
                body_bytes = response.read()
            result = json.loads(body_bytes)
            if result.get("error"):
                raise RuntimeError(f"Horizons error for body {body}, root {root}: {result['error']}")
            path.write_bytes(body_bytes)
            row = {
                    "body_id": body,
                    "body": body_name,
                    "window_index": index,
                    "window_kind": window["kind"],
                    "evidence_key": window["evidence_key"],
                    "root_utc_seconds_used_to_select_window": root,
                    "endpoint": ENDPOINT,
                    "parameters": dict(params),
                    "request_url": url,
                    "request_url_sha256": sha256(url.encode("utf-8")),
                    "response_path": path_key,
                    "response_sha256": sha256(body_bytes),
                    "response_bytes": len(body_bytes),
                    "expected_records": intervals + 1,
                    "api_version": result.get("signature", {}).get("version"),
                }
            request_rows.append(row)
            existing_by_path[path_key] = row
            time.sleep(0.1)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        f"verified {existing_count} cached and acquired {len(request_rows) - existing_count} new raw Horizons responses "
        f"across {len(root_windows)} windows"
    )
    print(f"manifest: {MANIFEST}")


if __name__ == "__main__":
    main()

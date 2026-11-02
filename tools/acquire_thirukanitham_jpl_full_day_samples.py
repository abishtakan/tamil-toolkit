#!/usr/bin/env python3
"""Acquire independent one-minute JPL samples for selected full civil days."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path("tests/reference/calendar-thirukanitham-v1")
RAW = ROOT / "horizons"
INPUT = ROOT / "derived-civil-day-and-month-reports.json"
MANIFEST = ROOT / "horizons-full-day-request-manifest.json"
ENDPOINT = "https://ssd.jpl.nasa.gov/api/horizons.api"
UTC_OFFSET_SECONDS = 19_800


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def stamp(value: datetime) -> str:
    return value.strftime("%Y-%b-%d %H:%M:%S.000")


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    projection = json.loads(INPUT.read_text(encoding="utf-8"))
    dates = sorted(
        {
            (int(row["date"]["year"]), int(row["date"]["month"]), int(row["date"]["day"]))
            for row in projection["civil_day_reports"]
        }
    )
    projection_hash = sha256(INPUT.read_bytes())
    old_manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    old_dates = [row["local_date"] for row in old_manifest.get("dates", [])]
    new_dates = [f"{year:04}-{month:02}-{day:02}" for year, month, day in dates]
    if old_manifest.get("input_projection_sha256") not in (None, projection_hash) and old_dates != new_dates:
        raise ValueError("existing full-day manifest selects different civil dates")
    manifest: dict[str, object] = {
        "title": "JPL Horizons full civil-day sample manifest",
        "acquisition_script": str(Path(__file__)).replace("\\", "/"),
        "acquisition_script_sha256": sha256(Path(__file__).read_bytes()),
        "api_documentation": "https://ssd-api.jpl.nasa.gov/doc/horizons.html",
        "coordinate_output": "DE441 geocentric observer apparent-airless ecliptic-of-date; center 500@399; UTC/UT; quantity 31",
        "input_projection": str(INPUT).replace("\\", "/"),
        "input_projection_sha256": projection_hash,
        "local_day_definition": "Each Gregorian date is sampled over [local midnight,next local midnight) in the recorded fixed UTC+05:30 zones; one-minute samples include the next midnight endpoint for a complete crossing bracket.",
        "sample_interval_seconds": 60,
        "dates": [],
        "queries": old_manifest.get("queries", []),
    }
    existing_by_path = {row["response_path"]: row for row in manifest["queries"]}
    date_rows = manifest["dates"]
    for year, month, day in dates:
        local_start = datetime(year, month, day, tzinfo=timezone.utc)
        start = local_start - timedelta(seconds=UTC_OFFSET_SECONDS)
        stop = start + timedelta(days=1)
        date_text = f"{year:04}-{month:02}-{day:02}"
        date_query_rows: list[dict[str, object]] = []
        for body_id, body_name in (("10", "sun"), ("301", "moon")):
            parameters = [
                ("format", "json"),
                ("COMMAND", f"'{body_id}'"),
                ("OBJ_DATA", "'YES'"),
                ("MAKE_EPHEM", "'YES'"),
                ("EPHEM_TYPE", "'OBSERVER'"),
                ("CENTER", "'500@399'"),
                ("START_TIME", f"'{stamp(start)}'"),
                ("STOP_TIME", f"'{stamp(stop)}'"),
                ("STEP_SIZE", "'1440'"),
                ("TIME_TYPE", "'UT'"),
                ("TIME_DIGITS", "'FRACSEC'"),
                ("QUANTITIES", "'31'"),
                ("APPARENT", "'AIRLESS'"),
                ("REF_SYSTEM", "'ICRF'"),
                ("CSV_FORMAT", "'YES'"),
                ("CAL_TYPE", "'GREGORIAN'"),
            ]
            request_url = ENDPOINT + "?" + urlencode(parameters)
            path = RAW / f"horizons_full_day_{body_name}_{date_text}.json"
            path_key = str(path).replace("\\", "/")
            if path_key in existing_by_path:
                raw = path.read_bytes()
                if sha256(raw) != existing_by_path[path_key]["response_sha256"]:
                    raise ValueError(f"saved raw JPL response digest mismatch: {path}")
                date_query_rows.append(existing_by_path[path_key])
                continue
            with urlopen(request_url, timeout=90) as response:
                raw = response.read()
            result = json.loads(raw)
            if result.get("error"):
                raise RuntimeError(f"Horizons error for {body_name} on {date_text}: {result['error']}")
            path.write_bytes(raw)
            query = {
                "body_id": body_id,
                "body": body_name,
                "date": date_text,
                "center": "500@399",
                "endpoint": ENDPOINT,
                "parameters": dict(parameters),
                "request_url": request_url,
                "request_url_sha256": sha256(request_url.encode("utf-8")),
                "response_path": path_key,
                "response_sha256": sha256(raw),
                "response_bytes": len(raw),
                "expected_records": 1_441,
                "api_version": result.get("signature", {}).get("version"),
            }
            manifest["queries"].append(query)
            existing_by_path[path_key] = query
            date_query_rows.append(query)
            time.sleep(0.1)
        date_rows.append(
            {
                "local_date": date_text,
                "local_start_utc_seconds": int(start.timestamp()),
                "local_end_utc_seconds_exclusive": int(stop.timestamp()),
                "report_context_count": sum(
                    1
                    for row in projection["civil_day_reports"]
                    if row["date"] == {"year": year, "month": month, "day": day}
                ),
                "query_paths": [row["response_path"] for row in date_query_rows],
            }
        )
        print(f"retained full-day samples for {date_text}")
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"saved {len(manifest['queries'])} full-day raw responses")
    print(f"manifest: {MANIFEST}")


if __name__ == "__main__":
    main()

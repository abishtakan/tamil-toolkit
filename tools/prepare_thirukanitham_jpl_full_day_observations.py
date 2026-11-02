#!/usr/bin/env python3
"""Classify complete sampled civil days from raw JPL/ERFA references."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from pathlib import Path

import erfa


ROOT = Path("tests/reference/calendar-thirukanitham-v1")
MANIFEST = ROOT / "horizons-full-day-request-manifest.json"
INPUT = ROOT / "derived-civil-day-and-month-reports.json"
OUT = ROOT / "independent-full-day-observations.json"
J2000_JD = 2_451_545.0
ANCHOR_JD = Decimal("2435553.5")
TT_MINUS_UTC = Decimal("69.184")
TRUE_ANCHOR_ARCSECONDS = Decimal("83700.658")
P03 = tuple(
    map(Decimal, ("0", "5028.796195", "1.1054348", "0.00007964", "-0.000023857", "-0.0000000383"))
)
ROW_RE = re.compile(
    r"^\s*(\d{4}-[A-Z][a-z]{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)"
    r"\s*,\s*,\s*,\s*([+-]?[\d.]+),\s*([+-]?[\d.]+),?\s*$"
)
LIMBS = ("tithi", "karana", "nakshatra", "yoga")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def p03_arcseconds(jd_tt: Decimal) -> Decimal:
    centuries = (jd_tt - Decimal("2451545.0")) / Decimal("36525")
    return sum(
        coefficient * (centuries**power if power else Decimal(1))
        for power, coefficient in enumerate(P03)
    )


def jd_tt(epoch: int) -> Decimal:
    return Decimal("2440587.5") + (Decimal(epoch) + TT_MINUS_UTC) / Decimal(86400)


def erfa_dpsi_arcseconds(jd: Decimal) -> float:
    value = float(jd)
    dpsi, _ = erfa.nut00a(J2000_JD, value - J2000_JD)
    return dpsi * 180.0 * 3600.0 / math.pi


def true_ayanamsa_arcseconds(epoch: int) -> float:
    jd = jd_tt(epoch)
    mean_anchor = float(TRUE_ANCHOR_ARCSECONDS) - erfa_dpsi_arcseconds(ANCHOR_JD)
    mean = mean_anchor + float(p03_arcseconds(jd) - p03_arcseconds(ANCHOR_JD))
    return mean + erfa_dpsi_arcseconds(jd)


def parse_response(path: Path) -> list[tuple[int, float, float]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    result: list[tuple[int, float, float]] = []
    for line in raw["result"].splitlines():
        match = ROW_RE.match(line)
        if not match:
            continue
        stamp, longitude, latitude = match.groups()
        instant = datetime.strptime(stamp, "%Y-%b-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
        result.append((int(instant.timestamp()), float(longitude), float(latitude)))
    return result


def indices(epoch: int, sun_lon: float, moon_lon: float) -> dict[str, int]:
    elongation = (moon_lon - sun_lon) % 360.0
    aya = true_ayanamsa_arcseconds(epoch) / 3600.0
    sid_sun = (sun_lon - aya) % 360.0
    sid_moon = (moon_lon - aya) % 360.0
    return {
        "tithi": int(elongation // 12.0) + 1,
        "karana": int(elongation // 6.0),
        "nakshatra": int(sid_moon // (40.0 / 3.0)) + 1,
        "yoga": int(((sid_sun + sid_moon) % 360.0) // (40.0 / 3.0)) + 1,
    }


def main() -> None:
    getcontext().prec = 50
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    projection = json.loads(INPUT.read_text(encoding="utf-8"))
    if sha256(INPUT.read_bytes()) != manifest["input_projection_sha256"]:
        raise ValueError("derived report projection digest differs from full-day manifest")
    queries = {query["date"]: {} for query in manifest["queries"]}
    for query in manifest["queries"]:
        path = Path(query["response_path"])
        raw = path.read_bytes()
        if sha256(raw) != query["response_sha256"]:
            raise ValueError(f"raw JPL response digest mismatch: {path}")
        parsed = parse_response(path)
        if len(parsed) != query["expected_records"]:
            raise ValueError(f"unexpected JPL record count in {path}: {len(parsed)}")
        if any(after[0] - before[0] != 60 for before, after in zip(parsed, parsed[1:])):
            raise ValueError(f"non-60-second JPL cadence in {path}")
        queries[query["date"]][query["body"]] = parsed

    all_days: list[dict[str, object]] = []
    for date_manifest in manifest["dates"]:
        date_text = date_manifest["local_date"]
        start = int(date_manifest["local_start_utc_seconds"])
        end = int(date_manifest["local_end_utc_seconds_exclusive"])
        sun_rows = {row[0]: row for row in queries[date_text]["sun"]}
        moon_rows = {row[0]: row for row in queries[date_text]["moon"]}
        epochs = sorted(set(sun_rows) & set(moon_rows))
        if len(epochs) != 1_441 or epochs[0] != start or epochs[-1] != end:
            raise ValueError(f"incomplete full-day JPL coverage for {date_text}")
        samples = [
            {
                "epoch": epoch,
                "sun": sun_rows[epoch][1],
                "moon": moon_rows[epoch][1],
            }
            for epoch in epochs
        ]
        observed: list[dict[str, object]] = []
        for before, after in zip(samples, samples[1:]):
            before_indices = indices(before["epoch"], before["sun"], before["moon"])
            after_indices = indices(after["epoch"], after["sun"], after["moon"])
            for limb in LIMBS:
                if before_indices[limb] != after_indices[limb]:
                    observed.append(
                        {
                            "limb": limb,
                            "from_index": before_indices[limb],
                            "to_index": after_indices[limb],
                            "jpl_before_utc_seconds": before["epoch"],
                            "jpl_after_utc_seconds": after["epoch"],
                            "bracket_width_seconds": after["epoch"] - before["epoch"],
                        }
                    )

        year, month, day = map(int, date_text.split("-"))
        report_rows = [
            row
            for row in projection["civil_day_reports"]
            if row["date"] == {"year": year, "month": month, "day": day}
        ]
        expected_by_key: dict[tuple[str, int, int], set[int]] = {}
        for report in report_rows:
            for event in report["transitions"]:
                key = (event["limb"], int(event["from_index"]), int(event["to_index"]))
                expected_by_key.setdefault(key, set()).add(int(event["instant_utc_seconds"]))
        observed_by_key: dict[tuple[str, int, int], list[dict[str, object]]] = {}
        for event in observed:
            key = (str(event["limb"]), int(event["from_index"]), int(event["to_index"]))
            observed_by_key.setdefault(key, []).append(event)
        if set(expected_by_key) != set(observed_by_key):
            raise ValueError(
                f"full-day independent transition set differs on {date_text}: "
                f"profile-only={sorted(set(expected_by_key) - set(observed_by_key))}; "
                f"JPL-only={sorted(set(observed_by_key) - set(expected_by_key))}"
            )
        expected_roots: list[dict[str, object]] = []
        for key, profile_roots in expected_by_key.items():
            brackets = observed_by_key[key]
            if len(profile_roots) != 1 or len(brackets) != 1:
                raise ValueError(f"ambiguous duplicate limb transition on {date_text}: {key}")
            bracket = brackets[0]
            profile_root = next(iter(profile_roots))
            before = int(bracket["jpl_before_utc_seconds"])
            after = int(bracket["jpl_after_utc_seconds"])
            if min(abs(profile_root - before), abs(profile_root - after)) > 60:
                raise ValueError(f"profile root is not adjacent to independent JPL bracket: {date_text} {key}")
            expected_roots.append(
                {
                    **bracket,
                    "profile_root_utc_seconds": profile_root,
                    "profile_root_minus_jpl_after_seconds": profile_root - after,
                }
            )
        all_days.append(
            {
                "local_date": date_text,
                "utc_interval": {"start_inclusive": start, "end_exclusive": end},
                "report_context_count": date_manifest["report_context_count"],
                "sample_interval_seconds": 60,
                "independent_transition_count": len(observed),
                "transition_set_matches_all_derived_report_contexts": True,
                "transitions": sorted(
                    expected_roots,
                    key=lambda row: (row["jpl_before_utc_seconds"], row["limb"]),
                ),
            }
        )

    output = {
        "evidence_class": "independent full-day transition-set checks derived from raw JPL DE441 apparent coordinates plus ERFA/SOFA IAU 2000A nutation and Decimal IAU 2006 P03; the comparison reports the profile's event set and does not use Rust to classify JPL samples",
        "time_scales": {
            "jpl_observation_times": "UT/UTC",
            "ERFA_and_P03_epoch": "TT = UTC + 69.184 seconds",
            "JPL_coordinates": "geocentric apparent-airless ecliptic-of-date; center 500@399; Horizons quantity 31",
            "sidereal_transform": "ERFA/SOFA IAU 2000A nutation plus independent Decimal P03 and true Lahiri anchor; subtract true aya from JPL apparent coordinates",
        },
        "provenance": {
            "jpl_manifest": str(MANIFEST).replace("\\", "/"),
            "jpl_manifest_sha256": sha256(MANIFEST.read_bytes()),
            "input_derived_report_sha256": manifest["input_projection_sha256"],
            "erfa_version": erfa.__version__,
            "pyerfa_requirement": "tools/requirements-thirukanitham-reference.txt",
            "transform_script": "tools/prepare_thirukanitham_jpl_full_day_observations.py",
            "transform_script_sha256": sha256(Path(__file__).read_bytes()),
        },
        "statistics": {
            "independent_full_local_days": len(all_days),
            "derived_location_and_elevation_contexts": sum(day["report_context_count"] for day in all_days),
            "independent_jpl_classified_limb_transitions": sum(day["independent_transition_count"] for day in all_days),
            "sample_interval_seconds": 60,
            "maximum_bracket_width_seconds": 60,
        },
        "days": all_days,
    }
    OUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"full days: {len(all_days)}; transitions: {output['statistics']['independent_jpl_classified_limb_transitions']}")
    print(f"output: {OUT} sha256={sha256(OUT.read_bytes())}")


if __name__ == "__main__":
    main()

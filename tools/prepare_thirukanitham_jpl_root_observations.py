#!/usr/bin/env python3
"""Derive independent root brackets from retained JPL and ERFA inputs.

This tool does not import the Rust implementation. Input windows are selected
from a separately labeled derived Rust report; every expected crossing below
is classified from JPL positions and an independent Decimal P03/ERFA transform.
"""

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
MANIFEST = ROOT / "horizons-root-request-manifest.json"
INPUT = ROOT / "derived-civil-day-and-month-reports.json"
OUT = ROOT / "independent-root-observations.json"
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


def erfa_nutation_arcseconds(jd: Decimal) -> tuple[float, float]:
    value = float(jd)
    dpsi, deps = erfa.nut00a(J2000_JD, value - J2000_JD)
    scale = 180.0 * 3600.0 / math.pi
    return dpsi * scale, deps * scale


def true_ayanamsa_arcseconds(epoch: int) -> float:
    jd = jd_tt(epoch)
    anchor_dpsi, _ = erfa_nutation_arcseconds(float(ANCHOR_JD))
    mean_anchor = float(TRUE_ANCHOR_ARCSECONDS) - anchor_dpsi
    mean = mean_anchor + float(p03_arcseconds(jd) - p03_arcseconds(ANCHOR_JD))
    dpsi, _ = erfa_nutation_arcseconds(jd)
    return mean + dpsi


def parse_response(path: Path, body: str) -> list[tuple[int, float, float]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    result: list[tuple[int, float, float]] = []
    for line in raw["result"].splitlines():
        match = ROW_RE.match(line)
        if not match:
            continue
        stamp, longitude, latitude = match.groups()
        dt = datetime.strptime(stamp, "%Y-%b-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
        result.append((int(dt.timestamp()), float(longitude), float(latitude)))
    return result


def signed_error(angle: float, boundary: float) -> float:
    return (angle - boundary + 180.0) % 360.0 - 180.0


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


def crossing(
    samples: list[dict[str, float]], limb: str, from_index: int, to_index: int
) -> dict[str, object]:
    for before, after in zip(samples, samples[1:]):
        before_index = indices(before["epoch"], before["sun"], before["moon"])[limb]
        after_index = indices(after["epoch"], after["sun"], after["moon"])[limb]
        if before_index == from_index and after_index == to_index:
            aya_before = true_ayanamsa_arcseconds(before["epoch"]) / 3600.0
            aya_after = true_ayanamsa_arcseconds(after["epoch"]) / 3600.0
            elong_before = (before["moon"] - before["sun"]) % 360.0
            elong_after = (after["moon"] - after["sun"]) % 360.0
            sid_sun_before = (before["sun"] - aya_before) % 360.0
            sid_sun_after = (after["sun"] - aya_after) % 360.0
            sid_moon_before = (before["moon"] - aya_before) % 360.0
            sid_moon_after = (after["moon"] - aya_after) % 360.0
            if limb == "tithi":
                boundary = ((to_index - 1) * 12.0) % 360.0
                angle_before, angle_after = elong_before, elong_after
            elif limb == "karana":
                boundary = (to_index * 6.0) % 360.0
                angle_before, angle_after = elong_before, elong_after
            elif limb == "nakshatra":
                boundary = ((to_index - 1) * (40.0 / 3.0)) % 360.0
                angle_before, angle_after = sid_moon_before, sid_moon_after
            else:
                boundary = ((to_index - 1) * (40.0 / 3.0)) % 360.0
                angle_before = (sid_sun_before + sid_moon_before) % 360.0
                angle_after = (sid_sun_after + sid_moon_after) % 360.0
            return {
                "jpl_before_utc_seconds": int(before["epoch"]),
                "jpl_after_utc_seconds": int(after["epoch"]),
                "bracket_width_seconds": int(after["epoch"] - before["epoch"]),
                "jpl_index_before": before_index,
                "jpl_index_after": after_index,
                "boundary_degrees": boundary,
                "jpl_signed_boundary_error_before_arcseconds": signed_error(angle_before, boundary) * 3600.0,
                "jpl_signed_boundary_error_after_arcseconds": signed_error(angle_after, boundary) * 3600.0,
                "jpl_apparent_sun_longitude_before_deg": before["sun"],
                "jpl_apparent_sun_longitude_after_deg": after["sun"],
                "jpl_apparent_moon_longitude_before_deg": before["moon"],
                "jpl_apparent_moon_longitude_after_deg": after["moon"],
            }
    raise ValueError(f"no JPL {limb} crossing {from_index}->{to_index} in selected window")


def main() -> None:
    getcontext().prec = 50
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    projection = json.loads(INPUT.read_text(encoding="utf-8"))
    if sha256(INPUT.read_bytes()) != manifest["input_projection_sha256"]:
        raise ValueError("derived report projection digest differs from request manifest")
    records: dict[int, dict[str, float]] = {}
    for query in manifest["queries"]:
        path = Path(query["response_path"])
        raw = path.read_bytes()
        if sha256(raw) != query["response_sha256"]:
            raise ValueError(f"raw JPL response digest mismatch: {path}")
        parsed = parse_response(path, query["body"])
        if len(parsed) != query["expected_records"]:
            raise ValueError(f"unexpected JPL record count: {path}")
        for epoch, longitude, latitude in parsed:
            row = records.setdefault(epoch, {"epoch": epoch})
            row[query["body"]] = longitude
            row[f"{query['body']}_latitude"] = latitude

    event_roots: list[dict[str, object]] = []
    ingress_roots: list[dict[str, object]] = []
    max_event_difference = 0
    max_ingress_difference = 0
    months_by_root: dict[int, list[tuple[int, int]]] = {}
    for month in projection["month_coverage"]:
        months_by_root.setdefault(int(month["ingress_utc_seconds"]), []).append(
            (int(month["solar_year"]), int(month["month"]))
        )
    terminal = projection["month_coverage"][-1]
    terminal_month = int(terminal["month"]) + 1
    terminal_year = int(terminal["solar_year"])
    if terminal_month > 12:
        terminal_month = 1
        terminal_year += 1
    months_by_root.setdefault(int(terminal["next_ingress_utc_seconds"]), []).append(
        (terminal_year, terminal_month)
    )

    for window in manifest["root_windows"]:
        epoch = int(window["root_utc_seconds"])
        half_width = int(window["half_width_seconds"])
        low, high = epoch - half_width, epoch + half_width
        samples = [records[sec] for sec in sorted(records) if low <= sec <= high]
        if window["kind"] == "solar_ingress":
            months = months_by_root.get(epoch, [])
            if not months:
                raise ValueError(f"no solar month metadata for ingress root {epoch}")
            year, month = months[0]
            solar_rows = [row for row in samples if "sun" in row]
            target_sign = int(month)
            bracket = None
            for before, after in zip(solar_rows, solar_rows[1:]):
                aya_before = true_ayanamsa_arcseconds(before["epoch"]) / 3600.0
                aya_after = true_ayanamsa_arcseconds(after["epoch"]) / 3600.0
                before_sign = int(((before["sun"] - aya_before) % 360.0) // 30.0) + 1
                after_sign = int(((after["sun"] - aya_after) % 360.0) // 30.0) + 1
                if before_sign != target_sign and after_sign == target_sign:
                    boundary = ((target_sign - 1) * 30.0) % 360.0
                    before_sid = (before["sun"] - aya_before) % 360.0
                    after_sid = (after["sun"] - aya_after) % 360.0
                    bracket = {
                        "jpl_before_utc_seconds": int(before["epoch"]),
                        "jpl_after_utc_seconds": int(after["epoch"]),
                        "bracket_width_seconds": int(after["epoch"] - before["epoch"]),
                        "sign_before": before_sign,
                        "sign_after": after_sign,
                        "boundary_degrees": boundary,
                        "jpl_signed_boundary_error_before_arcseconds": signed_error(before_sid, boundary) * 3600.0,
                        "jpl_signed_boundary_error_after_arcseconds": signed_error(after_sid, boundary) * 3600.0,
                    }
                    break
            if bracket is None:
                raise ValueError(f"no independent JPL solar ingress for solar year {year}, month {month}")
            root = {
                "solar_year": year,
                "month": month,
                "terminal_after_public_coverage": bool(window.get("terminal_after_public_coverage", False)),
                "profile_root_utc_seconds_used_to_select_window": epoch,
                **bracket,
                "profile_root_minus_jpl_after_seconds": bracket["jpl_after_utc_seconds"] - epoch,
            }
            max_ingress_difference = max(max_ingress_difference, abs(root["profile_root_minus_jpl_after_seconds"]))
            ingress_roots.append(root)
        else:
            expected = {
                (row["limb"], int(row["from_index"]), int(row["to_index"]))
                for row in window["transitions"]
            }
            if any("sun" not in row or "moon" not in row for row in samples):
                raise ValueError(f"missing Sun/Moon samples around civil root {epoch}")
            for limb, from_index, to_index in sorted(expected):
                bracket = crossing(samples, limb, from_index, to_index)
                root = {
                    "limb": limb,
                    "from_index": from_index,
                    "to_index": to_index,
                    "profile_root_utc_seconds_used_to_select_window": epoch,
                    "contexts": window["transitions"],
                    **bracket,
                    "profile_root_minus_jpl_after_seconds": bracket["jpl_after_utc_seconds"] - epoch,
                }
                delta = abs(int(root["profile_root_minus_jpl_after_seconds"]))
                max_event_difference = max(max_event_difference, delta)
                event_roots.append(root)

    if len(ingress_roots) != len(projection["month_coverage"]) + 1:
        raise ValueError("not all public and terminal month ingress roots were independently checked")
    output = {
        "evidence_class": "independent expected root brackets derived from raw JPL DE441 apparent coordinates plus ERFA/SOFA IAU 2000A nutation and Decimal IAU 2006 P03; window centers are derived profile outputs and are not treated as expected values",
        "time_scales": {
            "jpl_observation_times": "UT/UTC",
            "ERFA_and_P03_epoch": "TT = UTC + 69.184 seconds",
            "JPL_coordinates": "geocentric apparent-airless ecliptic-of-date; JPL's observer quantities use its documented IAU 1976/1980 apparent model",
            "sidereal_transform": "ERFA/SOFA IAU 2000A nutation plus independent Decimal P03 and true Lahiri anchor; subtract true aya from JPL apparent coordinates",
        },
        "provenance": {
            "jpl_manifest": str(MANIFEST).replace("\\", "/"),
            "jpl_manifest_sha256": sha256(MANIFEST.read_bytes()),
            "input_derived_report_sha256": manifest["input_projection_sha256"],
            "erfa_version": erfa.__version__,
            "pyerfa_requirement": "tools/requirements-thirukanitham-reference.txt",
            "transform_script": "tools/prepare_thirukanitham_jpl_root_observations.py",
            "transform_script_sha256": sha256(Path(__file__).read_bytes()),
        },
        "statistics": {
            "independently_checked_public_solar_ingresses": len(ingress_roots) - 1,
            "independently_checked_terminal_solar_ingresses": 1,
            "independently_checked_limb_roots": len(event_roots),
            "maximum_absolute_solar_ingress_profile_minus_jpl_after_seconds": max_ingress_difference,
            "maximum_absolute_limb_profile_minus_jpl_after_seconds": max_event_difference,
            "jpl_root_bracket_width_seconds": 1,
        },
        "solar_ingresses": ingress_roots,
        "civil_day_limb_roots": event_roots,
    }
    OUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"solar ingresses: {len(ingress_roots)}; civil limb roots: {len(event_roots)}")
    print(f"maximum profile/JPL second difference: ingress={max_ingress_difference}s, limbs={max_event_difference}s")
    print(f"output: {OUT} sha256={sha256(OUT.read_bytes())}")


if __name__ == "__main__":
    main()

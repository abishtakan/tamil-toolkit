#!/usr/bin/env python3
"""Extract and independently transform the pinned JPL Horizons samples.

Requires pyerfa==2.0.1.5 (ERFA/SOFA IAU 2000A nutation). It never imports the
toolkit or the astro crate. Run from the repository root.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, getcontext
from pathlib import Path

import erfa


ROOT = Path("tests/reference/calendar-thirukanitham-v1")
HORIZONS = ROOT / "horizons"
OUT = ROOT / "independent-transforms.json"
ANCHOR_JD_TT = 2_435_553.5
J2000_JD_TT = 2_451_545.0
TT_MINUS_UTC_SECONDS = Decimal("69.184")
TRUE_ANCHOR_ARCSECONDS = Decimal("83700658") / Decimal(1000)
P03_ARCSECONDS = tuple(
    map(Decimal, ("0", "5028.796195", "1.1054348", "0.00007964", "-0.000023857", "-0.0000000383"))
)
ROW_RE = re.compile(
    r"^\s*(\d{4}-[A-Z][a-z]{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)"
    r"\s*,\s*,\s*,\s*([+-]?[\d.]+),\s*([+-]?[\d.]+),?\s*$"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def p03_arcseconds(jd_tt: Decimal) -> Decimal:
    centuries = (jd_tt - Decimal("2451545.0")) / Decimal("36525")
    return sum(
        coefficient * (centuries**power if power else Decimal(1))
        for power, coefficient in enumerate(P03_ARCSECONDS)
    )


def nutation_iau2000a_arcseconds(jd_tt: float) -> tuple[float, float]:
    # Two-part JD keeps subsecond precision for the ERFA/SOFA routine.
    dpsi, deps = erfa.nut00a(J2000_JD_TT, jd_tt - J2000_JD_TT)
    arcseconds_per_radian = 180.0 * 3600.0 / math.pi
    return dpsi * arcseconds_per_radian, deps * arcseconds_per_radian


def parse_file(path: Path, body: str) -> dict[int, dict[str, object]]:
    rows: dict[int, dict[str, object]] = {}
    text = json.loads(path.read_text(encoding="utf-8"))["result"]
    for line in text.splitlines():
        match = ROW_RE.match(line)
        if not match:
            continue
        stamp, longitude, latitude = match.groups()
        utc = datetime.strptime(stamp, "%Y-%b-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
        epoch = int(utc.timestamp())
        row = rows.setdefault(epoch, {"utc": stamp, "unix_utc_seconds": epoch})
        row[body] = {"longitude_deg": float(longitude), "latitude_deg": float(latitude)}
    return rows


def jd_tt_from_unix(unix_seconds: int) -> Decimal:
    return (
        Decimal("2440587.5")
        + Decimal(unix_seconds) / Decimal(86400)
        + TT_MINUS_UTC_SECONDS / Decimal(86400)
    )


def p03_anchor_mean() -> dict[str, object]:
    dpsi, deps = nutation_iau2000a_arcseconds(float(ANCHOR_JD_TT))
    mean_arcseconds = float(TRUE_ANCHOR_ARCSECONDS) - dpsi
    mean_microarcseconds = round(mean_arcseconds * 1_000_000)
    return {
        "jd_tt": ANCHOR_JD_TT,
        "true_anchor_arcseconds": float(TRUE_ANCHOR_ARCSECONDS),
        "erfa_iau2000a_nutation_longitude_arcseconds": round(dpsi, 9),
        "erfa_iau2000a_nutation_obliquity_arcseconds": round(deps, 9),
        "mean_anchor_arcseconds": round(mean_arcseconds, 9),
        "mean_anchor_microarcseconds_rounded": mean_microarcseconds,
    }


def main() -> None:
    getcontext().prec = 50
    sun_path = HORIZONS / "horizons_de441_geocentric_apparent_sun_reacquired_2026-11-02.json"
    moon_path = HORIZONS / "horizons_de441_geocentric_apparent_moon_reacquired_2026-11-02.json"
    rows = parse_file(sun_path, "sun")
    for epoch, row in parse_file(moon_path, "moon").items():
        rows.setdefault(epoch, {"unix_utc_seconds": epoch}).update(row)

    anchor_mean = p03_anchor_mean()
    anchor_p03 = p03_arcseconds(Decimal(str(ANCHOR_JD_TT)))
    samples: list[dict[str, object]] = []
    for epoch in sorted(rows):
        row = rows[epoch]
        jd_tt = jd_tt_from_unix(epoch)
        dpsi, deps = nutation_iau2000a_arcseconds(float(jd_tt))
        mean_ayanamsa_arcseconds = (
            Decimal(str(anchor_mean["mean_anchor_arcseconds"]))
            + p03_arcseconds(jd_tt)
            - anchor_p03
        )
        true_ayanamsa_arcseconds = float(mean_ayanamsa_arcseconds) + dpsi
        true_ayanamsa_deg = true_ayanamsa_arcseconds / 3600.0
        sun = row["sun"]
        moon = row["moon"]
        sun_apparent = float(sun["longitude_deg"])
        moon_apparent = float(moon["longitude_deg"])
        sidereal_sun = (sun_apparent - true_ayanamsa_deg) % 360.0
        sidereal_moon = (moon_apparent - true_ayanamsa_deg) % 360.0
        samples.append(
            {
                "utc": row["utc"],
                "unix_utc_seconds": epoch,
                "jd_tt": float(jd_tt),
                "jpl_apparent": {
                    "sun_longitude_deg": sun_apparent,
                    "moon_longitude_deg": moon_apparent,
                    "elongation_deg": (moon_apparent - sun_apparent) % 360.0,
                },
                "erfa_iau2000a": {
                    "nutation_longitude_arcseconds": round(dpsi, 9),
                    "nutation_obliquity_arcseconds": round(deps, 9),
                },
                "p03_lahiri_true": {
                    "mean_ayanamsa_arcseconds": round(float(mean_ayanamsa_arcseconds), 9),
                    "true_ayanamsa_arcseconds": round(true_ayanamsa_arcseconds, 9),
                    "true_ayanamsa_deg": round(true_ayanamsa_deg, 12),
                    "sidereal_sun_longitude_deg": round(sidereal_sun, 12),
                    "sidereal_moon_longitude_deg": round(sidereal_moon, 12),
                    "sidereal_yoga_sum_deg": round((sidereal_sun + sidereal_moon) % 360.0, 12),
                },
            }
        )

    checkpoints = []
    checkpoint_epochs = [
        ("J2000.0", 2_451_545.0),
        ("2024-01-01T00:00:00Z", float(jd_tt_from_unix(1704067200))),
        ("2024-08-01T00:00:00Z", float(jd_tt_from_unix(1722470400))),
        ("2025-04-14T00:00:00Z", float(jd_tt_from_unix(1744588800))),
        ("2026-11-01T00:00:00Z", float(jd_tt_from_unix(1793491200))),
        ("2027-12-31T23:00:00Z", float(jd_tt_from_unix(1830294000))),
    ]
    for label, jd_tt in checkpoint_epochs:
        dpsi, deps = nutation_iau2000a_arcseconds(jd_tt)
        mean_ayanamsa_arcseconds = (
            float(anchor_mean["mean_anchor_arcseconds"])
            + float(p03_arcseconds(Decimal(str(jd_tt))) - anchor_p03)
        )
        checkpoints.append(
            {
                "epoch": label,
                "jd_tt": jd_tt,
                "nutation_longitude_arcseconds": round(dpsi, 9),
                "nutation_obliquity_arcseconds": round(deps, 9),
                "mean_ayanamsa_arcseconds": round(mean_ayanamsa_arcseconds, 9),
                "true_ayanamsa_arcseconds": round(mean_ayanamsa_arcseconds + dpsi, 9),
            }
        )

    result = {
        "reference": "NASA/JPL Horizons DE441 observer ephemeris, geocenter, apparent airless ecliptic-of-date",
        "transform": "ERFA 2.0.1.5 / SOFA IAU 2000A nutation + independent Decimal evaluation of the IAU 2006 P03 longitude polynomial",
        "time": {
            "jpl_table_scale": "UT/UTC",
            "toolkit_tt_minus_utc_seconds": 69.184,
            "nutation_epoch_scale": "TT",
            "true_anchor_jd_tt": ANCHOR_JD_TT,
        },
        "sidereal_anchor": anchor_mean,
        "sidereal_checkpoints": checkpoints,
        "samples": samples,
        "raw_inputs": [
            {"path": str(sun_path).replace("\\", "/"), "sha256": sha256(sun_path), "body": "Sun (10)"},
            {"path": str(moon_path).replace("\\", "/"), "sha256": sha256(moon_path), "body": "Moon (301)"},
        ],
        "extraction_script": {
            "path": "tools/prepare_thirukanitham_reference.py",
            "sha256": sha256(Path("tools/prepare_thirukanitham_reference.py")),
        },
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(samples)} samples), mean anchor {anchor_mean['mean_anchor_arcseconds']} arcsec")


if __name__ == "__main__":
    main()

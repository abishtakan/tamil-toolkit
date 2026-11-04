"""Calendar sub-namespace for tamil_toolkit."""

from typing import Any

from . import execute

THIRUKANITHAM_DEFINITION = "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2"
VAKYA_CIVIL_DEFINITION = "vakyakarana-1962-laghuprakashika-civil-ujjain-mean-sunrise-v1"


def profile_info(definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Return the selected finite calendar model, coverage, station, and sources."""
    return execute({"op": "calendar_profile_info", "input": {"definition_id": definition_id}})


def gregorian_to_tamil_date(date: dict[str, int], context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Convert a Gregorian date with the selected definition and its context."""
    return execute({"op": "gregorian_to_tamil_date", "input": {
        "definition_id": definition_id, "date": date, "context": context,
    }})


def tamil_to_gregorian_date(date: dict[str, int], context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Convert a solar Tamil date with the selected definition and context."""
    return execute({"op": "tamil_to_gregorian_date", "input": {
        "definition_id": definition_id,
        "date": {"solar_year": date["solar_year"], "month": date["month"], "day": date["day"]},
        "context": context,
    }})


def tamil_month_info(solar_year: int, month: int, context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    return execute({"op": "tamil_month_info", "input": {
        "definition_id": definition_id,
        "solar_year": solar_year, "month": month, "context": context,
    }})


def tamil_year_info(solar_year: int, context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Enumerate all twelve source-profile month intervals in one solar year."""
    return execute({"op": "tamil_year_info", "input": {
        "definition_id": definition_id, "solar_year": solar_year, "context": context,
    }})


def tamil_year_cycle_info(solar_year: int, context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Return the sourced romanized 60-year title for a supported solar year."""
    return execute({"op": "tamil_year_cycle_info", "input": {
        "definition_id": definition_id, "solar_year": solar_year, "context": context,
    }})


def official_holidays(jurisdiction: str, year: int) -> dict[str, Any]:
    """Return an authority-published named-holiday schedule for a supported year."""
    return execute({"op": "calendar_official_holidays", "input": {
        "jurisdiction": jurisdiction, "year": year,
    }})


def observances(
    gregorian_year: int, context: dict[str, Any],
    rule_set: str = "thirukanitham-tamil-named-observances-v1",
    definition_id: str = THIRUKANITHAM_DEFINITION,
    month: int | None = None,
) -> dict[str, Any]:
    """Calculate the named source-limited Tamil Nadu observance subset."""
    return execute({"op": "calendar_observances", "input": {
        "definition_id": definition_id, "rule_set": rule_set,
        "gregorian_year": gregorian_year, "context": context,
        **({"month": month} if month is not None else {}),
    }})


def add_tamil_date(
    date: dict[str, int], unit: str, amount: int, context: dict[str, Any],
    overflow: str = "reject", definition_id: str = THIRUKANITHAM_DEFINITION,
) -> dict[str, Any]:
    """Add days, months, or years using the selected profile's date boundaries."""
    return execute({"op": "add_tamil_date", "input": {
        "definition_id": definition_id,
        "date": {"solar_year": date["solar_year"], "month": date["month"], "day": date["day"]},
        "unit": unit, "amount": amount, "overflow": overflow, "context": context,
    }})


def panchangam_at(instant_unix_seconds: int, context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Return the five limb values at an integer Unix UTC second."""
    return execute({"op": "panchangam_at", "input": {
        "definition_id": definition_id,
        "instant_unix_seconds": instant_unix_seconds, "context": context,
    }})


def panchangam_day(date: dict[str, int], context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Return rise/set and every limb transition over the local civil day."""
    return execute({"op": "panchangam_day", "input": {
        "definition_id": definition_id, "date": date, "context": context,
    }})


def lunar_phase_events(
    start_unix_seconds: int,
    end_unix_seconds: int,
    definition_id: str = THIRUKANITHAM_DEFINITION,
) -> dict[str, Any]:
    """Return bounded Thirukanitham geocentric primary phases in UTC."""
    return execute({"op": "lunar_phase_events", "input": {
        "definition_id": definition_id,
        "start_unix_seconds": start_unix_seconds,
        "end_unix_seconds": end_unix_seconds,
    }})


def daylight_periods(
    date: dict[str, int], context: dict[str, Any],
    definition_id: str = THIRUKANITHAM_DEFINITION,
) -> dict[str, Any]:
    """Return source-defined weekday intervals within computed daylight."""
    return execute({"op": "calendar_daylight_periods", "input": {
        "definition_id": definition_id, "date": date, "context": context,
    }})


def format_tamil_date(
    date: dict[str, int], context: dict[str, Any], script: str = "tamil",
    digits: str = "latin", style: str = "weekday_day_month_year",
    definition_id: str = THIRUKANITHAM_DEFINITION,
) -> str:
    """Format a validated solar date with explicitly selected script and digits."""
    return execute({"op": "format_tamil_date", "input": {
        "definition_id": definition_id, "date": date, "context": context,
        "script": script, "digits": digits, "style": style,
    }})


def display_info(
    date: dict[str, int], context: dict[str, Any], script: str = "tamil",
    digits: str = "latin",
    definition_id: str = THIRUKANITHAM_DEFINITION,
) -> dict[str, Any]:
    """Return formatted date, year-cycle and panchangam labels with provenance."""
    return execute({"op": "calendar_display_info", "input": {
        "definition_id": definition_id, "date": date, "context": context,
        "script": script, "digits": digits,
    }})


def compare_profiles(
    thirukanitham_context: dict[str, Any], vakya_context: dict[str, Any], *,
    date: dict[str, int] | None = None,
    instant_unix_seconds: int | None = None,
) -> dict[str, Any]:
    """Compare both declared profiles at one date or one UTC instant."""
    input_value: dict[str, Any] = {
        "thirukanitham_context": thirukanitham_context,
        "vakya_context": vakya_context,
    }
    if date is not None:
        input_value["date"] = date
    if instant_unix_seconds is not None:
        input_value["instant_unix_seconds"] = instant_unix_seconds
    return execute({"op": "compare_calendar_profiles", "input": input_value})


def thiruvalluvar_year_info(
    date: dict[str, int], context: dict[str, Any],
    convention_id: str = "tn-thiruvalluvar-thai1-thirukanitham-v1",
) -> dict[str, Any]:
    """Return the named Thirukanitham Thai-1 era convention, not a Gazette lookup."""
    return execute({"op": "thiruvalluvar_year_info", "input": {
        "convention_id": convention_id, "date": date, "context": context,
    }})


def vakya_solar_transits(saka_year_elapsed: int) -> dict[str, Any]:
    """Return source-pinned 1962 Vakyakarana solar transit arithmetic."""
    return execute({
        "op": "vakya_solar_transits",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-solar-transits-v1",
            "saka_year_elapsed": saka_year_elapsed,
        },
    })


def vakya_true_sun_from_mesha_elapsed(elapsed_days: int, nadi: int, vinadi: int) -> dict[str, Any]:
    """Apply the 1962 Vakyakarana Bhupadi table to time elapsed from Mesha."""
    return execute({
        "op": "vakya_true_sun_from_mesha_elapsed",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-solar-transits-v1",
            "elapsed_days": elapsed_days,
            "nadi": nadi,
            "vinadi": vinadi,
        },
    })


def vakya_true_moon_from_kali_day(kali_day: int) -> dict[str, Any]:
    """Return the 1962 Vakyakarana Candra-vakya true Moon for a Kali day."""
    return execute({
        "op": "vakya_true_moon_from_kali_day",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-true-moon-v1",
            "kali_day": kali_day,
        },
    })


def vakya_reduce_to_local_true_sunrise(
    true_position: dict[str, int],
    daily_motion: dict[str, int],
    cara_half_vinadi_tenths: int,
    desantara_vinadi_tenths: int,
    bhujaantara_vinadi_tenths: int,
) -> dict[str, Any]:
    """Apply the 1962 source's signed local true-sunrise correction."""
    return execute({
        "op": "vakya_reduce_to_local_true_sunrise",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-local-sunrise-v1",
            "true_position": true_position,
            "daily_motion": daily_motion,
            "cara_half_vinadi_tenths": cara_half_vinadi_tenths,
            "desantara_vinadi_tenths": desantara_vinadi_tenths,
            "bhujaantara_vinadi_tenths": bhujaantara_vinadi_tenths,
        },
    })


def vakya_cara_from_sayana_sun(
    sayana_sun: dict[str, int], equinoctial_shadow_tenths: int,
) -> dict[str, Any]:
    """Compute the 1962 Vakyakarana Cara interval from Sayana Sun and shadow."""
    return execute({
        "op": "vakya_cara_from_sayana_sun",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-cara-v1",
            "sayana_sun": sayana_sun,
            "equinoctial_shadow_tenths": equinoctial_shadow_tenths,
        },
    })


def vakya_desantara_from_yojana_distance(
    east_west_distance_tenths_yojana: int,
) -> dict[str, Any]:
    """Convert the 1962 Ujjain yojana distance to Desantara vinadis."""
    return execute({
        "op": "vakya_desantara_from_yojana_distance",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-desantara-v1",
            "east_west_distance_tenths_yojana": east_west_distance_tenths_yojana,
        },
    })


def vakya_bhujaantara_from_true_sun(
    sun_rasi: int, sun_rasi_progress_arcseconds: int,
) -> dict[str, Any]:
    """Interpolate the 1962 Bhujaantara table within a source rasi."""
    return execute({
        "op": "vakya_bhujaantara_from_true_sun",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-bhujaantara-linear-experimental-v1",
            "sun_rasi": sun_rasi,
            "sun_rasi_progress_arcseconds": sun_rasi_progress_arcseconds,
        },
    })

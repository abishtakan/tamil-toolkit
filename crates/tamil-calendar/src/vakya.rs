use crate::{tables, SolarVakya};

const WEEKDAYS: [&str; 7] = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
];

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Ahargana {
    pub days: i64,
    pub nadi: u8,
    pub vinadi: u8,
    pub weekday: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SolarTransit {
    pub rasi: &'static str,
    pub day_field: i64,
    pub weekday: &'static str,
    pub nadi: u8,
    pub vinadi: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VakyaSolarYear {
    pub definition_id: &'static str,
    pub saka_year_elapsed: i64,
    pub kali_year: i64,
    pub ahargana: Ahargana,
    pub transits: Vec<SolarTransit>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DmsAngle {
    pub degrees: i64,
    pub minutes: u8,
    pub seconds: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VakyaTrueSun {
    pub definition_id: &'static str,
    pub elapsed_days: i64,
    pub nadi: u8,
    pub vinadi: u8,
    pub approximate_sun: DmsAngle,
    pub bhupadi_correction: DmsAngle,
    pub true_sun: DmsAngle,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct RasiDmsAngle {
    pub rasi: u8,
    pub degrees: u8,
    pub minutes: u8,
    pub seconds: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VakyaTrueMoon {
    pub definition_id: &'static str,
    pub kali_day: i64,
    pub quotient_12372: i64,
    pub quotient_3031: i64,
    pub quotient_248: i64,
    pub moon_vakya_number: i64,
    pub uncorrected_true_moon: RasiDmsAngle,
    pub daily_motion: DmsAngle,
    pub vinadi_adjustment: i64,
    pub correction_seconds: i64,
    pub true_moon: RasiDmsAngle,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VakyaLocalSunriseReduction {
    pub definition_id: &'static str,
    pub true_position: RasiDmsAngle,
    pub daily_motion: DmsAngle,
    pub cara_half_vinadi_tenths: i64,
    pub desantara_vinadi_tenths: i64,
    pub bhujaantara_vinadi_tenths: i64,
    pub total_vinadi_tenths: i64,
    pub correction_arcseconds: i64,
    pub local_true_position: RasiDmsAngle,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VakyaCara {
    pub definition_id: &'static str,
    pub sayana_sun: RasiDmsAngle,
    pub bhuja: RasiDmsAngle,
    pub equinoctial_shadow_tenths: i64,
    pub cara_vinadi_tenths: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VakyaDesantara {
    pub definition_id: &'static str,
    pub east_west_distance_tenths_yojana: i64,
    pub desantara_vinadi_tenths: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VakyaBhujaantara {
    pub definition_id: &'static str,
    pub sun_rasi: u8,
    pub sun_rasi_progress_arcseconds: i64,
    pub bracketing_endpoint_vinadi: [i64; 2],
    pub bhujaantara_vinadi_tenths: i64,
}

struct MoonBase {
    quotient_12372: i128,
    quotient_3031: i128,
    quotient_248: i128,
    moon_vakya_number: i128,
    angle_arcseconds: i128,
}

const MOON_CIRCLE_ARCSECONDS: i128 = 360 * 3_600;
const MAX_SAFE_JSON_INTEGER: i128 = 9_007_199_254_740_991;

fn ensure_safe_calendar_input(value: i64) -> Result<(), String> {
    if i128::from(value).abs() > MAX_SAFE_JSON_INTEGER {
        return Err("outside supported calendar coverage".into());
    }
    Ok(())
}

fn safe_calendar_output(value: i128) -> Result<i64, String> {
    if value.abs() > MAX_SAFE_JSON_INTEGER {
        return Err("outside supported calendar coverage".into());
    }
    i64::try_from(value).map_err(|_| "outside supported calendar coverage".into())
}

fn moon_base(kali_day: i128) -> MoonBase {
    let elapsed = kali_day - i128::from(tables::VAKYA_MOON_KALI_EPOCH_DAY);
    let quotient_12372 = elapsed.div_euclid(i128::from(tables::VAKYA_MOON_CYCLE_1_DAYS));
    let remainder_12372 = elapsed.rem_euclid(i128::from(tables::VAKYA_MOON_CYCLE_1_DAYS));
    let quotient_3031 = remainder_12372 / i128::from(tables::VAKYA_MOON_CYCLE_2_DAYS);
    let remainder_3031 = remainder_12372 % i128::from(tables::VAKYA_MOON_CYCLE_2_DAYS);
    let quotient_248 = remainder_3031 / i128::from(tables::VAKYA_MOON_CYCLE_3_DAYS);
    let remainder_248 = remainder_3031 % i128::from(tables::VAKYA_MOON_CYCLE_3_DAYS);
    let (angle_cycle_248, moon_vakya_number) = if remainder_248 == 0 {
        (
            quotient_248 - 1,
            i128::from(tables::VAKYA_MOON_CYCLE_3_DAYS),
        )
    } else {
        (quotient_248, remainder_248)
    };
    let vakya_index = (moon_vakya_number - 1) as usize;
    let angle_arcseconds = (quotient_12372 * i128::from(tables::VAKYA_MOON_CYCLE_1_ARCSECONDS)
        + quotient_3031 * i128::from(tables::VAKYA_MOON_CYCLE_2_ARCSECONDS)
        + angle_cycle_248 * i128::from(tables::VAKYA_MOON_CYCLE_3_ARCSECONDS)
        + i128::from(tables::VAKYA_MOON_DHRUVA_ARCSECONDS)
        + i128::from(tables::VAKYA_MOON_VAKYAS_ARCSECONDS[vakya_index]))
    .rem_euclid(MOON_CIRCLE_ARCSECONDS);
    MoonBase {
        quotient_12372,
        quotient_3031,
        quotient_248,
        moon_vakya_number,
        angle_arcseconds,
    }
}

fn rasi_dms(total_arcseconds: i128) -> RasiDmsAngle {
    let normalized = total_arcseconds.rem_euclid(MOON_CIRCLE_ARCSECONDS);
    let rasi = normalized / 108_000;
    let within_rasi = normalized % 108_000;
    RasiDmsAngle {
        rasi: rasi as u8,
        degrees: (within_rasi / 3_600) as u8,
        minutes: ((within_rasi % 3_600) / 60) as u8,
        seconds: (within_rasi % 60) as u8,
    }
}

/// Compute the source-pinned Candra-vakya true Moon for a Kali day number.
pub fn vakya_true_moon_from_kali_day(kali_day: i64) -> Result<VakyaTrueMoon, String> {
    if kali_day < tables::VAKYA_MOON_KALI_EPOCH_DAY || i128::from(kali_day) > MAX_SAFE_JSON_INTEGER
    {
        return Err("outside supported calendar coverage".into());
    }
    let base = moon_base(i128::from(kali_day));
    let previous = moon_base(i128::from(kali_day) - 1);
    let daily_motion_arcseconds =
        (base.angle_arcseconds - previous.angle_arcseconds).rem_euclid(MOON_CIRCLE_ARCSECONDS);
    let vinadi_adjustment = base.quotient_248 * i128::from(tables::VAKYA_MOON_CYCLE_3_VINADIS)
        - base.quotient_3031 * i128::from(tables::VAKYA_MOON_CYCLE_2_VINADIS);
    let defect_arcseconds =
        daily_motion_arcseconds - i128::from(tables::VAKYA_MOON_DAILY_MOTION_BASELINE_ARCSECONDS);
    let correction_seconds = (defect_arcseconds * vinadi_adjustment) / 3_600;
    let true_moon_arcseconds =
        (base.angle_arcseconds + correction_seconds).rem_euclid(MOON_CIRCLE_ARCSECONDS);

    let quotient_12372 = safe_calendar_output(base.quotient_12372)?;
    let quotient_3031 = safe_calendar_output(base.quotient_3031)?;
    let quotient_248 = safe_calendar_output(base.quotient_248)?;
    let moon_vakya_number = safe_calendar_output(base.moon_vakya_number)?;
    let daily_motion_arcseconds = safe_calendar_output(daily_motion_arcseconds)?;
    let vinadi_adjustment = safe_calendar_output(vinadi_adjustment)?;
    let correction_seconds = safe_calendar_output(correction_seconds)?;

    Ok(VakyaTrueMoon {
        definition_id: tables::VAKYA_MOON_PROFILE,
        kali_day,
        quotient_12372,
        quotient_3031,
        quotient_248,
        moon_vakya_number,
        uncorrected_true_moon: rasi_dms(base.angle_arcseconds),
        daily_motion: dms(daily_motion_arcseconds),
        vinadi_adjustment,
        correction_seconds,
        true_moon: rasi_dms(true_moon_arcseconds),
    })
}

/// Apply the 1962 edition's signed reduction from a true longitude to local true sunrise.
/// The source-time terms are supplied by the caller in tenths of a vinadi.
pub fn vakya_reduce_to_local_true_sunrise(
    true_position: RasiDmsAngle,
    daily_motion: DmsAngle,
    cara_half_vinadi_tenths: i64,
    desantara_vinadi_tenths: i64,
    bhujaantara_vinadi_tenths: i64,
) -> Result<VakyaLocalSunriseReduction, String> {
    if true_position.rasi >= 12
        || true_position.degrees >= 30
        || true_position.minutes >= 60
        || true_position.seconds >= 60
        || !(0..360).contains(&daily_motion.degrees)
        || daily_motion.minutes >= 60
        || daily_motion.seconds >= 60
    {
        return Err("invalid calendar angle".into());
    }

    for term in [
        cara_half_vinadi_tenths,
        desantara_vinadi_tenths,
        bhujaantara_vinadi_tenths,
    ] {
        ensure_safe_calendar_input(term)?;
    }

    let total_vinadi_tenths = i128::from(cara_half_vinadi_tenths)
        + i128::from(desantara_vinadi_tenths)
        + i128::from(bhujaantara_vinadi_tenths);
    let daily_motion_arcseconds = i128::from(daily_motion.degrees) * 3_600
        + i128::from(daily_motion.minutes) * 60
        + i128::from(daily_motion.seconds);
    let correction_arcseconds = daily_motion_arcseconds * total_vinadi_tenths / 36_000;
    let total_vinadi_tenths = safe_calendar_output(total_vinadi_tenths)?;
    let correction_arcseconds = safe_calendar_output(correction_arcseconds)?;
    let true_position_arcseconds = i128::from(true_position.rasi) * 108_000
        + i128::from(true_position.degrees) * 3_600
        + i128::from(true_position.minutes) * 60
        + i128::from(true_position.seconds);

    Ok(VakyaLocalSunriseReduction {
        definition_id: "vakyakarana-1962-laghuprakashika-local-sunrise-v1",
        true_position,
        daily_motion,
        cara_half_vinadi_tenths,
        desantara_vinadi_tenths,
        bhujaantara_vinadi_tenths,
        total_vinadi_tenths,
        correction_arcseconds,
        local_true_position: rasi_dms(true_position_arcseconds + i128::from(correction_arcseconds)),
    })
}

/// Compute the 1962 edition's signed Cara interval from Sayana Sun and shadow.
pub fn vakya_cara_from_sayana_sun(
    sayana_sun: RasiDmsAngle,
    equinoctial_shadow_tenths: i64,
) -> Result<VakyaCara, String> {
    if sayana_sun.rasi >= 12
        || sayana_sun.degrees >= 30
        || sayana_sun.minutes >= 60
        || sayana_sun.seconds >= 60
    {
        return Err("invalid calendar angle".into());
    }
    if equinoctial_shadow_tenths < 0 {
        return Err("invalid calendar input".into());
    }
    if i128::from(equinoctial_shadow_tenths) > MAX_SAFE_JSON_INTEGER {
        return Err("outside supported calendar coverage".into());
    }

    let longitude = i128::from(sayana_sun.rasi) * 108_000
        + i128::from(sayana_sun.degrees) * 3_600
        + i128::from(sayana_sun.minutes) * 60
        + i128::from(sayana_sun.seconds);
    let half_circle = 180 * 3_600;
    let quarter_circle = 90 * 3_600;
    let longitude_in_half = longitude % half_circle;
    let bhuja_arcseconds = if longitude_in_half <= quarter_circle {
        longitude_in_half
    } else {
        half_circle - longitude_in_half
    };
    let sign = if longitude < half_circle {
        -1_i128
    } else {
        1_i128
    };

    let segment_arcseconds = 30 * 3_600;
    let shadow = i128::from(equinoctial_shadow_tenths);
    let common_coefficient_denominator = tables::VAKYA_SOLAR_CARA_INTERVAL_COEFFICIENTS
        .iter()
        .map(|(_, denominator)| i128::from(*denominator))
        .product::<i128>();
    let coefficient_arcseconds = tables::VAKYA_SOLAR_CARA_INTERVAL_COEFFICIENTS
        .iter()
        .enumerate()
        .map(|(index, (numerator, denominator))| {
            let segment_start = index as i128 * i128::from(segment_arcseconds);
            let overlap =
                (bhuja_arcseconds - segment_start).clamp(0, i128::from(segment_arcseconds));
            i128::from(*numerator)
                * (common_coefficient_denominator / i128::from(*denominator))
                * overlap
        })
        .sum::<i128>();
    let exact_numerator = shadow * coefficient_arcseconds;
    let exact_denominator = common_coefficient_denominator * i128::from(segment_arcseconds);
    // Accumulate every segment as an exact rational. Truncate only the final
    // tenths-of-a-vinadi result, as documented from the edition's precision.
    let cara_vinadi_tenths = exact_numerator / exact_denominator;
    let signed_cara_vinadi_tenths = sign * cara_vinadi_tenths;
    let cara_vinadi_tenths = safe_calendar_output(signed_cara_vinadi_tenths)?;
    if i128::from(cara_vinadi_tenths).abs() > MAX_SAFE_JSON_INTEGER {
        return Err("outside supported calendar coverage".into());
    }

    Ok(VakyaCara {
        definition_id: tables::VAKYA_SOLAR_CARA_PROFILE,
        sayana_sun,
        bhuja: rasi_dms(bhuja_arcseconds),
        equinoctial_shadow_tenths,
        cara_vinadi_tenths,
    })
}

/// Convert an east/west distance from Ujjain to tenths of a vinadi.
pub fn vakya_desantara_from_yojana_distance(
    east_west_distance_tenths_yojana: i64,
) -> Result<VakyaDesantara, String> {
    ensure_safe_calendar_input(east_west_distance_tenths_yojana)?;
    let numerator = i128::from(east_west_distance_tenths_yojana).abs()
        * i128::from(tables::VAKYA_SOLAR_VINADIS_PER_NADI);
    let denominator = i128::from(tables::VAKYA_SOLAR_DESANTARA_YOJANAS_PER_NADI);
    let rounded_magnitude = (numerator + denominator / 2) / denominator;
    if rounded_magnitude > MAX_SAFE_JSON_INTEGER {
        return Err("outside supported calendar coverage".into());
    }
    let signed_result = if east_west_distance_tenths_yojana > 0 {
        -rounded_magnitude
    } else {
        rounded_magnitude
    };
    let desantara_vinadi_tenths = safe_calendar_output(signed_result)?;

    Ok(VakyaDesantara {
        definition_id: tables::VAKYA_SOLAR_DESANTARA_PROFILE,
        east_west_distance_tenths_yojana,
        desantara_vinadi_tenths,
    })
}

/// Interpolate the 1962 edition's Bhujaantara table by within-rasi longitude.
/// The source says to interpolate for a date but does not state the parameter;
/// this definition pins linear interpolation over each 30-degree rasi.
pub fn vakya_bhujaantara_from_true_sun(
    sun_rasi: u8,
    sun_rasi_progress_arcseconds: i64,
) -> Result<VakyaBhujaantara, String> {
    ensure_safe_calendar_input(sun_rasi_progress_arcseconds)?;
    if sun_rasi >= 12 || !(0..=108_000).contains(&sun_rasi_progress_arcseconds) {
        return Err("invalid calendar angle".into());
    }

    let index = usize::from(sun_rasi);
    let previous_index = (index + tables::VAKYA_SOLAR_BHUJAANTARA_END_OF_RASI_VINADIS.len() - 1)
        % tables::VAKYA_SOLAR_BHUJAANTARA_END_OF_RASI_VINADIS.len();
    let previous = tables::VAKYA_SOLAR_BHUJAANTARA_END_OF_RASI_VINADIS[previous_index];
    let current = tables::VAKYA_SOLAR_BHUJAANTARA_END_OF_RASI_VINADIS[index];
    let denominator = 108_000_i128;
    let progress = i128::from(sun_rasi_progress_arcseconds);
    let numerator =
        i128::from(previous) * 10 * denominator + i128::from(current - previous) * 10 * progress;
    let magnitude = (numerator.abs() + denominator / 2) / denominator;
    let rounded = if numerator < 0 { -magnitude } else { magnitude };
    let bhujaantara_vinadi_tenths = safe_calendar_output(rounded)?;

    Ok(VakyaBhujaantara {
        definition_id: tables::VAKYA_SOLAR_BHUJAANTARA_PROFILE,
        sun_rasi,
        sun_rasi_progress_arcseconds,
        bracketing_endpoint_vinadi: [previous, current],
        bhujaantara_vinadi_tenths,
    })
}

fn dms(total_arcseconds: i64) -> DmsAngle {
    DmsAngle {
        degrees: total_arcseconds / 3600,
        minutes: ((total_arcseconds % 3600) / 60) as u8,
        seconds: (total_arcseconds % 60) as u8,
    }
}

fn weekday_for_days_after_epoch(days: i64) -> &'static str {
    debug_assert_eq!(
        WEEKDAYS[tables::VAKYA_SOLAR_KALI_EPOCH_WEEKDAY_INDEX],
        tables::VAKYA_SOLAR_KALI_EPOCH_WEEKDAY
    );
    let index = (tables::VAKYA_SOLAR_KALI_EPOCH_WEEKDAY_INDEX as i64 + days.rem_euclid(7)) % 7;
    WEEKDAYS[index as usize]
}

fn ahargana(kali_year: i64) -> Ahargana {
    let denominator = i128::from(tables::VAKYA_SOLAR_AHARGANA_COMMON_DENOMINATOR);
    let year = i128::from(kali_year);
    let quarter_denominator = i128::from(tables::VAKYA_SOLAR_AHARGANA_QUARTER_DENOMINATOR);
    let adjustment_denominator = i128::from(tables::VAKYA_SOLAR_AHARGANA_ADJUSTMENT_DENOMINATOR);
    let adjustment = i128::from(tables::VAKYA_SOLAR_AHARGANA_ADJUSTMENT_MULTIPLIER) * year
        - i128::from(tables::VAKYA_SOLAR_AHARGANA_ADJUSTMENT_SUBTRAHEND);
    let numerator = i128::from(tables::VAKYA_SOLAR_AHARGANA_YEAR_DAYS) * year * denominator
        + i128::from(tables::VAKYA_SOLAR_AHARGANA_QUARTER_NUMERATOR)
            * year
            * (denominator / quarter_denominator)
        + adjustment * (denominator / adjustment_denominator);

    let mut days = (numerator / denominator) as i64;
    let fractional_numerator = numerator % denominator;
    let exact_vinadis = fractional_numerator * 3600;
    let mut rounded_vinadis = (exact_vinadis + denominator / 2) / denominator;
    if rounded_vinadis == 3600 {
        days += 1;
        rounded_vinadis = 0;
    }
    let rounded_vinadis = rounded_vinadis as i64;
    Ahargana {
        days,
        nadi: (rounded_vinadis / tables::VAKYA_SOLAR_VINADIS_PER_NADI) as u8,
        vinadi: (rounded_vinadis % tables::VAKYA_SOLAR_VINADIS_PER_NADI) as u8,
        weekday: weekday_for_days_after_epoch(days),
    }
}

pub(super) fn vakya_ahargana(kali_year: i64) -> Ahargana {
    ahargana(kali_year)
}

fn solar_transit(dhruva: &Ahargana, vakya: &SolarVakya) -> SolarTransit {
    let vinadis = i64::from(dhruva.nadi) * tables::VAKYA_SOLAR_VINADIS_PER_NADI
        + i64::from(dhruva.vinadi)
        + vakya.nadis * tables::VAKYA_SOLAR_VINADIS_PER_NADI
        + vakya.vinadis;
    let carry_days =
        vinadis / (tables::VAKYA_SOLAR_NADIS_PER_DAY * tables::VAKYA_SOLAR_VINADIS_PER_NADI);
    let remaining =
        vinadis % (tables::VAKYA_SOLAR_NADIS_PER_DAY * tables::VAKYA_SOLAR_VINADIS_PER_NADI);
    let day_field = dhruva.days.rem_euclid(7) + vakya.days + carry_days;
    SolarTransit {
        rasi: vakya.rasi,
        day_field,
        weekday: weekday_for_days_after_epoch(day_field),
        nadi: (remaining / tables::VAKYA_SOLAR_VINADIS_PER_NADI) as u8,
        vinadi: (remaining % tables::VAKYA_SOLAR_VINADIS_PER_NADI) as u8,
    }
}

/// Reproduce the bounded annual solar-vakya arithmetic from the 1962 edition.
pub fn vakya_solar_transits(saka_year_elapsed: i64) -> Result<VakyaSolarYear, String> {
    if !(tables::VAKYA_SOLAR_MIN_SAKA_YEAR..=tables::VAKYA_SOLAR_MAX_SAKA_YEAR)
        .contains(&saka_year_elapsed)
    {
        return Err("outside supported calendar coverage".into());
    }
    let kali_year = saka_year_elapsed + tables::VAKYA_SOLAR_SAKA_TO_KALI_YEAR;
    let year_start = ahargana(kali_year);
    let transits = tables::VAKYA_SOLAR_VAKYAS
        .iter()
        .map(|vakya| solar_transit(&year_start, vakya))
        .collect();
    Ok(VakyaSolarYear {
        definition_id: tables::VAKYA_SOLAR_PROFILE,
        saka_year_elapsed,
        kali_year,
        ahargana: year_start,
        transits,
    })
}

/// Compute the 1962 Vakyakarana table correction from elapsed time at Meṣa.
pub fn vakya_true_sun_from_mesha_elapsed(
    elapsed_days: i64,
    nadi: i64,
    vinadi: i64,
) -> Result<VakyaTrueSun, String> {
    if !(0..tables::VAKYA_SOLAR_NADIS_PER_DAY).contains(&nadi)
        || !(0..tables::VAKYA_SOLAR_VINADIS_PER_NADI).contains(&vinadi)
    {
        return Err("invalid calendar time".into());
    }
    if !(0..=370).contains(&elapsed_days) || (elapsed_days == 370 && (nadi != 0 || vinadi != 0)) {
        return Err("outside supported calendar coverage".into());
    }

    let approximate_arcseconds = elapsed_days * 3600 + nadi * 60 + vinadi;
    let segment = (elapsed_days / 10) as usize;
    let correction_arcseconds = if segment == tables::VAKYA_SOLAR_BHUPADI_CORRECTION_MINUTES.len() {
        tables::VAKYA_SOLAR_BHUPADI_CORRECTION_MINUTES[segment - 1] * 60
    } else {
        let left = if segment == 0 {
            0
        } else {
            tables::VAKYA_SOLAR_BHUPADI_CORRECTION_MINUTES[segment - 1] * 60
        };
        let right = tables::VAKYA_SOLAR_BHUPADI_CORRECTION_MINUTES[segment] * 60;
        let elapsed_in_segment = (elapsed_days % 10) * 3600 + nadi * 60 + vinadi;
        let interval_vinadis = 10 * 3600;
        let numerator = left * interval_vinadis + (right - left) * elapsed_in_segment;
        (numerator + interval_vinadis / 2) / interval_vinadis
    };
    let circle = 360 * 3600;
    let true_arcseconds = (approximate_arcseconds - correction_arcseconds).rem_euclid(circle);
    Ok(VakyaTrueSun {
        definition_id: tables::VAKYA_SOLAR_PROFILE,
        elapsed_days,
        nadi: nadi as u8,
        vinadi: vinadi as u8,
        approximate_sun: dms(approximate_arcseconds),
        bhupadi_correction: dms(correction_arcseconds),
        true_sun: dms(true_arcseconds),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::{prelude::*, test_runner::Config as ProptestConfig};

    #[test]
    fn source_anchors_match_the_printed_worked_years() {
        let older = vakya_solar_transits(1869).unwrap();
        assert_eq!(older.kali_year, 5048);
        assert_eq!(older.ahargana.days, 1_843_823);
        assert_eq!((older.ahargana.nadi, older.ahargana.vinadi), (40, 19));
        assert_eq!(older.ahargana.weekday, "Sunday");

        let later = vakya_solar_transits(1890).unwrap();
        assert_eq!(later.kali_year, 5069);
        assert_eq!(later.ahargana.days, 1_851_494);
        assert_eq!((later.ahargana.nadi, later.ahargana.vinadi), (6, 15));
        assert_eq!(later.ahargana.weekday, "Saturday");
        assert_eq!(
            later
                .transits
                .iter()
                .map(|event| (event.day_field, event.nadi, event.vinadi))
                .collect::<Vec<_>>(),
            vec![
                (4, 1, 47),
                (7, 25, 59),
                (4, 2, 37),
                (7, 30, 49),
                (3, 32, 59),
                (6, 0, 21),
                (7, 54, 28),
                (2, 24, 52),
                (3, 45, 45),
                (5, 13, 1),
                (7, 1, 25),
                (2, 21, 46),
            ]
        );

        let sun = vakya_true_sun_from_mesha_elapsed(180, 19, 41).unwrap();
        assert_eq!(
            sun.approximate_sun,
            DmsAngle {
                degrees: 180,
                minutes: 19,
                seconds: 41
            }
        );
        assert_eq!(
            sun.bhupadi_correction,
            DmsAngle {
                degrees: 6,
                minutes: 51,
                seconds: 8
            }
        );
        assert_eq!(
            sun.true_sun,
            DmsAngle {
                degrees: 173,
                minutes: 28,
                seconds: 33
            }
        );

        let moon = vakya_true_moon_from_kali_day(1_844_004).unwrap();
        assert_eq!(
            (moon.quotient_12372, moon.quotient_3031, moon.quotient_248),
            (19, 2, 7)
        );
        assert_eq!(moon.moon_vakya_number, 154);
        assert_eq!(
            moon.uncorrected_true_moon,
            RasiDmsAngle {
                rasi: 4,
                degrees: 11,
                minutes: 14,
                seconds: 1
            }
        );
        assert_eq!(
            moon.daily_motion,
            DmsAngle {
                degrees: 14,
                minutes: 12,
                seconds: 0
            }
        );
        assert_eq!(
            (moon.vinadi_adjustment, moon.correction_seconds),
            (208, 211)
        );
        assert_eq!(
            moon.true_moon,
            RasiDmsAngle {
                rasi: 4,
                degrees: 11,
                minutes: 17,
                seconds: 32
            }
        );

        let local_sunrise = vakya_reduce_to_local_true_sunrise(
            RasiDmsAngle {
                rasi: 4,
                degrees: 11,
                minutes: 17,
                seconds: 32,
            },
            DmsAngle {
                degrees: 14,
                minutes: 12,
                seconds: 0,
            },
            130,
            -266,
            -210,
        )
        .unwrap();
        assert_eq!(local_sunrise.total_vinadi_tenths, -346);
        assert_eq!(local_sunrise.correction_arcseconds, -491);
        assert_eq!(
            local_sunrise.local_true_position,
            RasiDmsAngle {
                rasi: 4,
                degrees: 11,
                minutes: 9,
                seconds: 21,
            }
        );

        let cara = vakya_cara_from_sayana_sun(
            RasiDmsAngle {
                rasi: 4,
                degrees: 22,
                minutes: 30,
                seconds: 0,
            },
            30,
        )
        .unwrap();
        assert_eq!(
            cara.bhuja,
            RasiDmsAngle {
                rasi: 1,
                degrees: 7,
                minutes: 30,
                seconds: 0,
            }
        );
        assert_eq!(cara.cara_vinadi_tenths, -720);
        assert_eq!(
            vakya_cara_from_sayana_sun(
                RasiDmsAngle {
                    rasi: 0,
                    degrees: 15,
                    minutes: 0,
                    seconds: 0,
                },
                9_007_199_254_740_991,
            )
            .unwrap_err(),
            "outside supported calendar coverage"
        );

        let desantara = vakya_desantara_from_yojana_distance(244).unwrap();
        assert_eq!(desantara.desantara_vinadi_tenths, -266);
        assert_eq!(
            vakya_desantara_from_yojana_distance(8_256_599_316_845_908)
                .unwrap()
                .desantara_vinadi_tenths,
            -9_007_199_254_740_991
        );
        assert_eq!(
            vakya_desantara_from_yojana_distance(8_256_599_316_845_909).unwrap_err(),
            "outside supported calendar coverage"
        );
        assert_eq!(
            vakya_desantara_from_yojana_distance(MAX_SAFE_JSON_INTEGER as i64).unwrap_err(),
            "outside supported calendar coverage"
        );
        assert_eq!(
            vakya_desantara_from_yojana_distance((MAX_SAFE_JSON_INTEGER + 1) as i64).unwrap_err(),
            "outside supported calendar coverage"
        );

        let epoch = vakya_true_moon_from_kali_day(1_600_984).unwrap();
        assert_eq!(
            epoch.uncorrected_true_moon,
            RasiDmsAngle {
                rasi: 7,
                degrees: 2,
                minutes: 0,
                seconds: 1
            }
        );
        let cycle_end = vakya_true_moon_from_kali_day(1_601_232).unwrap();
        assert_eq!(cycle_end.moon_vakya_number, 248);
        assert_eq!(
            cycle_end.true_moon,
            RasiDmsAngle {
                rasi: 7,
                degrees: 29,
                minutes: 43,
                seconds: 31
            }
        );
        assert_eq!(
            vakya_true_moon_from_kali_day((MAX_SAFE_JSON_INTEGER + 1) as i64).unwrap_err(),
            "outside supported calendar coverage"
        );
        assert_eq!(
            vakya_reduce_to_local_true_sunrise(
                RasiDmsAngle {
                    rasi: 0,
                    degrees: 0,
                    minutes: 0,
                    seconds: 0
                },
                DmsAngle {
                    degrees: 359,
                    minutes: 0,
                    seconds: 0
                },
                MAX_SAFE_JSON_INTEGER as i64,
                2,
                0,
            )
            .unwrap_err(),
            "outside supported calendar coverage"
        );
        assert_eq!(
            vakya_bhujaantara_from_true_sun(0, (MAX_SAFE_JSON_INTEGER + 1) as i64).unwrap_err(),
            "outside supported calendar coverage"
        );
        assert_eq!(
            vakya_solar_transits((MAX_SAFE_JSON_INTEGER + 1) as i64).unwrap_err(),
            "outside supported calendar coverage"
        );
        assert_eq!(
            vakya_true_sun_from_mesha_elapsed((MAX_SAFE_JSON_INTEGER + 1) as i64, 0, 0)
                .unwrap_err(),
            "outside supported calendar coverage"
        );
    }

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]

        #[test]
        fn every_supported_year_has_normalized_ordered_transits(year in 1869i64..=1890) {
            let result = vakya_solar_transits(year).unwrap();
            prop_assert_eq!(result.transits.len(), 12);
            prop_assert_eq!(result.kali_year, year + tables::VAKYA_SOLAR_SAKA_TO_KALI_YEAR);
            prop_assert!((0..60).contains(&result.ahargana.nadi));
            prop_assert!((0..60).contains(&result.ahargana.vinadi));
            prop_assert_eq!(result.ahargana.weekday,
                weekday_for_days_after_epoch(result.ahargana.days));
            for (index, transit) in result.transits.iter().enumerate() {
                prop_assert_eq!(transit.rasi, tables::VAKYA_SOLAR_VAKYAS[index].rasi);
                prop_assert!((0..60).contains(&transit.nadi));
                prop_assert!((0..60).contains(&transit.vinadi));
                prop_assert_eq!(transit.weekday,
                    weekday_for_days_after_epoch(transit.day_field));
            }
        }

        #[test]
        fn true_sun_interpolation_returns_normalized_sexagesimal_angles(
            days in 0i64..370,
            nadi in 0i64..60,
            vinadi in 0i64..60,
        ) {
            let result = vakya_true_sun_from_mesha_elapsed(days, nadi, vinadi).unwrap();
            for angle in [result.bhupadi_correction, result.true_sun] {
                prop_assert!((0..60).contains(&angle.minutes));
                prop_assert!((0..60).contains(&angle.seconds));
            }
            prop_assert!((0..360).contains(&result.true_sun.degrees));
            prop_assert_eq!(result.approximate_sun.degrees, days);
        }

        #[test]
        fn true_moon_results_are_normalized_and_have_bounded_daily_motion(
            kali_day in 1_600_984i64..=1_625_728i64,
        ) {
            let result = vakya_true_moon_from_kali_day(kali_day).unwrap();
            for angle in [result.uncorrected_true_moon, result.true_moon] {
                prop_assert!((0..12).contains(&angle.rasi));
                prop_assert!((0..30).contains(&angle.degrees));
                prop_assert!((0..60).contains(&angle.minutes));
                prop_assert!((0..60).contains(&angle.seconds));
            }
            prop_assert!((0..30).contains(&result.daily_motion.degrees));
            prop_assert!((0..60).contains(&result.daily_motion.minutes));
            prop_assert!((0..60).contains(&result.daily_motion.seconds));
            prop_assert!((1..=248).contains(&result.moon_vakya_number));
        }

        #[test]
        fn every_safe_json_kali_day_has_only_safe_integer_outputs(
            kali_day in 1_600_984i64..=9_007_199_254_740_991,
        ) {
            let result = vakya_true_moon_from_kali_day(kali_day).unwrap();
            let safe = MAX_SAFE_JSON_INTEGER as i64;
            prop_assert!(result.kali_day <= safe);
            prop_assert!(result.quotient_12372 <= safe);
            prop_assert!(result.quotient_3031 <= safe);
            prop_assert!(result.quotient_248 <= safe);
            prop_assert!(result.moon_vakya_number <= safe);
            prop_assert!(result.daily_motion.degrees <= safe);
            prop_assert!(result.vinadi_adjustment.abs() <= safe);
            prop_assert!(result.correction_seconds.abs() <= safe);
        }

        #[test]
        fn local_sunrise_reduction_preserves_normalized_longitudes(
            rasi in 0u8..12,
            degrees in 0u8..30,
            minutes in 0u8..60,
            seconds in 0u8..60,
            motion_degrees in 0i64..360,
            motion_minutes in 0u8..60,
            motion_seconds in 0u8..60,
            cara in -10_000i64..10_001,
            desantara in -10_000i64..10_001,
            bhujaantara in -10_000i64..10_001,
        ) {
            let result = vakya_reduce_to_local_true_sunrise(
                RasiDmsAngle { rasi, degrees, minutes, seconds },
                DmsAngle { degrees: motion_degrees, minutes: motion_minutes, seconds: motion_seconds },
                cara,
                desantara,
                bhujaantara,
            ).unwrap();
            prop_assert_eq!(result.true_position, RasiDmsAngle { rasi, degrees, minutes, seconds });
            prop_assert_eq!(result.total_vinadi_tenths, cara + desantara + bhujaantara);
            prop_assert!((0..12).contains(&result.local_true_position.rasi));
            prop_assert!((0..30).contains(&result.local_true_position.degrees));
            prop_assert!((0..60).contains(&result.local_true_position.minutes));
            prop_assert!((0..60).contains(&result.local_true_position.seconds));
        }

        #[test]
        fn local_sunrise_rejects_any_unsafe_numeric_sum_or_correction(
            cara in -9_007_199_254_740_991i64..=9_007_199_254_740_991,
            desantara in -9_007_199_254_740_991i64..=9_007_199_254_740_991,
            bhujaantara in -9_007_199_254_740_991i64..=9_007_199_254_740_991,
            motion_degrees in 0i64..360,
            motion_minutes in 0u8..60,
            motion_seconds in 0u8..60,
        ) {
            let sum = i128::from(cara) + i128::from(desantara) + i128::from(bhujaantara);
            let motion = i128::from(motion_degrees) * 3_600
                + i128::from(motion_minutes) * 60
                + i128::from(motion_seconds);
            let correction = motion * sum / 36_000;
            let expected_safe = sum.abs() <= MAX_SAFE_JSON_INTEGER
                && correction.abs() <= MAX_SAFE_JSON_INTEGER;
            let result = vakya_reduce_to_local_true_sunrise(
                RasiDmsAngle { rasi: 0, degrees: 0, minutes: 0, seconds: 0 },
                DmsAngle { degrees: motion_degrees, minutes: motion_minutes, seconds: motion_seconds },
                cara,
                desantara,
                bhujaantara,
            );
            if expected_safe {
                let result = result.unwrap();
                prop_assert_eq!(i128::from(result.total_vinadi_tenths), sum);
                prop_assert_eq!(i128::from(result.correction_arcseconds), correction);
            } else {
                prop_assert_eq!(result.unwrap_err(), "outside supported calendar coverage");
            }
        }

        #[test]
        fn cara_is_antisymmetric_across_the_solar_half_circle(
            longitude in 0i64..(180 * 3600),
            shadow in 0i64..100_000,
        ) {
            let angle = |arcseconds: i64| RasiDmsAngle {
                rasi: (arcseconds / 108_000) as u8,
                degrees: ((arcseconds % 108_000) / 3600) as u8,
                minutes: ((arcseconds % 3600) / 60) as u8,
                seconds: (arcseconds % 60) as u8,
            };
            let first = vakya_cara_from_sayana_sun(angle(longitude), shadow).unwrap();
            let second = vakya_cara_from_sayana_sun(angle(longitude + 180 * 3600), shadow).unwrap();
            prop_assert_eq!(first.bhuja, second.bhuja);
            prop_assert_eq!(first.cara_vinadi_tenths, -second.cara_vinadi_tenths);
            let bhuja_arcseconds = i128::from(first.bhuja.rasi) * 108_000
                + i128::from(first.bhuja.degrees) * 3_600
                + i128::from(first.bhuja.minutes) * 60
                + i128::from(first.bhuja.seconds);
            let common_denominator = 3_i128;
            let segment_arcseconds = 108_000_i128;
            let exact_coefficient_sum = [(20_i128, 1_i128), (16, 1), (20, 3)]
                .iter()
                .enumerate()
                .map(|(index, (numerator, denominator))| {
                    let start = index as i128 * segment_arcseconds;
                    let overlap = (bhuja_arcseconds - start).clamp(0, segment_arcseconds);
                    numerator * (common_denominator / denominator) * overlap
                })
                .sum::<i128>();
            let expected = -(i128::from(shadow) * exact_coefficient_sum
                / (common_denominator * segment_arcseconds));
            prop_assert_eq!(i128::from(first.cara_vinadi_tenths), expected);
        }

        #[test]
        fn desantara_is_antisymmetric_and_bounded(distance in -1_000_000i64..=1_000_000) {
            let east = vakya_desantara_from_yojana_distance(distance).unwrap();
            let west = vakya_desantara_from_yojana_distance(-distance).unwrap();
            prop_assert_eq!(east.desantara_vinadi_tenths, -west.desantara_vinadi_tenths);
            prop_assert!(east.desantara_vinadi_tenths.abs() <= 1_090_910);
        }

        #[test]
        fn bhujaantara_interpolation_stays_between_adjacent_source_values(
            rasi in 0u8..12,
            progress in 0i64..=108_000,
        ) {
            let result = vakya_bhujaantara_from_true_sun(rasi, progress).unwrap();
            let [left, right] = result.bracketing_endpoint_vinadi;
            let lower = left.min(right) * 10;
            let upper = left.max(right) * 10;
            prop_assert!((lower..=upper).contains(&result.bhujaantara_vinadi_tenths));
            if progress == 0 {
                prop_assert_eq!(result.bhujaantara_vinadi_tenths, left * 10);
            }
            if progress == 108_000 {
                prop_assert_eq!(result.bhujaantara_vinadi_tenths, right * 10);
            }
        }
    }
}

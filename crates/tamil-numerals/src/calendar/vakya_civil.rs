use super::super::tables;
use super::vakya::{
    vakya_true_moon_from_kali_day, vakya_true_sun_from_mesha_elapsed, Ahargana, DmsAngle,
};
use crate::numeric::{date_from_ordinal, ordinal_day};
use crate::GregorianDate;

const DAY_VINADIS: i64 = 3_600;
const SAFE_JSON_INTEGER: i64 = 9_007_199_254_740_991;
const KALI_EPOCH_WEEKDAY_INDEX: i64 = 4; // Monday=0, Friday=4.
const SECONDS_PER_LONGITUDE_DEGREE: i64 = 240;
// Gregorian ordinal for 1970-01-01, shared with the Unix timestamp epoch.
const UTC_EPOCH_ORDINAL: i64 = 719_162;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VakyaCivilContext {
    time_zone: &'static str,
}

impl VakyaCivilContext {
    pub fn new(reference_station: &str, time_zone: &str) -> Result<Self, String> {
        if reference_station != tables::VAKYA_CIVIL_REFERENCE_STATION {
            return Err("unsupported location".into());
        }
        if !tables::VAKYA_CIVIL_TIMEZONE_IDS.contains(&time_zone) {
            return Err("unsupported time zone".into());
        }
        let time_zone = if time_zone == "Asia/Kolkata" {
            "Asia/Kolkata"
        } else {
            "Asia/Colombo"
        };
        Ok(Self { time_zone })
    }

    pub fn reference_station(self) -> &'static str {
        tables::VAKYA_CIVIL_REFERENCE_STATION
    }

    pub fn time_zone(self) -> &'static str {
        self.time_zone
    }

    fn minimum_instant_year(self) -> i64 {
        if self.time_zone == "Asia/Kolkata" {
            tables::VAKYA_CIVIL_KOLKATA_INSTANT_MIN_YEAR
        } else {
            tables::VAKYA_CIVIL_COLOMBO_INSTANT_MIN_YEAR
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VakyaCivilProfileInfo {
    pub profile: &'static str,
    pub definition_id: &'static str,
    pub solar_date_start: GregorianDate,
    pub solar_date_end: GregorianDate,
    pub kali_epoch_ordinal: i64,
    pub reference_station: &'static str,
    pub latitude_microdegrees: i64,
    pub longitude_microdegrees: i64,
    pub timezone_utc_offset_seconds: i64,
    pub ujjain_lmt_offset_from_ist_seconds: i64,
    pub vinadi_seconds: i64,
    pub daytime_end_nadi: i64,
    pub sources: Vec<&'static str>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VakyaCivilTamilDate {
    pub solar_year: i64,
    pub month: u8,
    pub month_name: &'static str,
    pub day: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VakyaCivilDateConversion {
    pub definition_id: &'static str,
    pub gregorian_date: GregorianDate,
    pub tamil_date: VakyaCivilTamilDate,
    pub reference_station: &'static str,
    pub day_boundary: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VakyaCivilDateReverse {
    pub definition_id: &'static str,
    pub tamil_date: VakyaCivilTamilDate,
    pub gregorian_date: GregorianDate,
    pub reference_station: &'static str,
    pub day_boundary: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VakyaCivilMonthInfo {
    pub definition_id: &'static str,
    pub solar_year: i64,
    pub month: u8,
    pub month_name: &'static str,
    pub start_date: GregorianDate,
    pub end_date_exclusive: GregorianDate,
    pub days: i64,
    pub reference_station: &'static str,
    pub day_boundary: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VakyaCivilLimb {
    pub index: u8,
    pub name: &'static str,
    pub paksha: Option<&'static str>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VakyaCivilLimbs {
    pub tithi: VakyaCivilLimb,
    pub nakshatra: VakyaCivilLimb,
    pub yoga: VakyaCivilLimb,
    pub karana: VakyaCivilLimb,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VakyaCivilTime {
    pub hour: u8,
    pub minute: u8,
    pub second: u8,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VakyaCivilPanchangamAt {
    pub definition_id: &'static str,
    pub local_date: GregorianDate,
    pub local_time: VakyaCivilTime,
    pub vara: &'static str,
    pub limbs: VakyaCivilLimbs,
    pub reference_station: &'static str,
    pub position_basis: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VakyaCivilTransition {
    pub limb: &'static str,
    pub from_index: u8,
    pub to_index: u8,
    pub day_offset: i64,
    pub minute_of_day: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VakyaCivilPanchangamDay {
    pub definition_id: &'static str,
    pub date: GregorianDate,
    pub sunrise_minute_of_day: i64,
    pub sunrise_basis: &'static str,
    pub sunset_minute_of_day: Option<i64>,
    pub sunset_status: &'static str,
    pub vara: &'static str,
    pub limbs_at_sunrise: VakyaCivilLimbs,
    pub transitions: Vec<VakyaCivilTransition>,
}

#[derive(Debug, Clone, Copy)]
struct YearStart {
    solar_year: i64,
    ahargana: Ahargana,
    sunrise_day: i64,
}

#[derive(Debug, Clone, Copy)]
struct MeanSunriseTime {
    kali_day: i64,
    vinadi_after_sunrise: i64,
    // Civil day identity must not carry with rounded astronomical positions.
    vara_kali_day: i64,
}

pub fn vakya_civil_profile_info() -> Result<VakyaCivilProfileInfo, String> {
    let first_start = year_start(1)?.sunrise_day;
    let start_date = date_from_kali_day(first_start)?;
    let end_date = GregorianDate::new(tables::VAKYA_CIVIL_SOLAR_DATE_MAX_YEAR, 12, 31)
        .map_err(|_| "outside supported calendar coverage")?;
    Ok(VakyaCivilProfileInfo {
        profile: tables::VAKYA_CIVIL_PROFILE,
        definition_id: tables::VAKYA_CIVIL_DEFINITION_ID,
        solar_date_start: start_date,
        solar_date_end: end_date,
        kali_epoch_ordinal: tables::VAKYA_CIVIL_KALI_EPOCH_GREGORIAN_ORDINAL,
        reference_station: tables::VAKYA_CIVIL_REFERENCE_STATION,
        latitude_microdegrees: tables::VAKYA_CIVIL_REFERENCE_STATION_LATITUDE_MICRODEGREES,
        longitude_microdegrees: tables::VAKYA_CIVIL_REFERENCE_STATION_LONGITUDE_MICRODEGREES,
        timezone_utc_offset_seconds: tables::VAKYA_CIVIL_TIMEZONE_OFFSET_SECONDS,
        ujjain_lmt_offset_from_ist_seconds: ujjain_lmt_offset_from_ist_seconds(),
        vinadi_seconds: tables::VAKYA_CIVIL_VINADI_SECONDS,
        daytime_end_nadi: tables::VAKYA_CIVIL_DAYTIME_END_NADI,
        sources: tables::VAKYA_CIVIL_SOURCE_URLS.to_vec(),
    })
}

pub fn vakya_gregorian_to_tamil_date(
    date: GregorianDate,
    _context: VakyaCivilContext,
) -> Result<VakyaCivilDateConversion, String> {
    let kali_day = kali_day_from_gregorian(date)?;
    let (solar_year, starts) = solar_year_for_kali_day(kali_day)?;
    let month_index = (0..12)
        .filter(|index| starts[*index] <= kali_day)
        .max()
        .ok_or("outside supported calendar coverage")?;
    let month = u8::try_from(month_index + 1).map_err(|_| "outside supported calendar coverage")?;
    let day = kali_day - starts[month_index] + 1;
    Ok(VakyaCivilDateConversion {
        definition_id: tables::VAKYA_CIVIL_DEFINITION_ID,
        gregorian_date: date,
        tamil_date: VakyaCivilTamilDate {
            solar_year,
            month,
            month_name: tables::VAKYA_CIVIL_MONTH_NAMES[month_index],
            day,
        },
        reference_station: tables::VAKYA_CIVIL_REFERENCE_STATION,
        day_boundary: "ujjain_mean_sunrise",
    })
}

pub fn vakya_tamil_to_gregorian_date(
    solar_year: i64,
    month: i64,
    day: i64,
    context: VakyaCivilContext,
) -> Result<VakyaCivilDateReverse, String> {
    if !(tables::VAKYA_CIVIL_SOLAR_DATE_MIN_YEAR..=tables::VAKYA_CIVIL_SOLAR_DATE_MAX_YEAR)
        .contains(&solar_year)
        || !(1..=12).contains(&month)
        || !(1..=35).contains(&day)
    {
        return Err("invalid Tamil date".into());
    }
    let starts = solar_month_starts(solar_year)?;
    let index = usize::try_from(month - 1).map_err(|_| "invalid Tamil date")?;
    let length = starts[index + 1] - starts[index];
    if day > length {
        return Err("invalid Tamil date".into());
    }
    let gregorian_date = date_from_kali_day(starts[index] + day - 1)?;
    let tamil_date = vakya_gregorian_to_tamil_date(gregorian_date, context)?.tamil_date;
    if tamil_date.solar_year != solar_year || i64::from(tamil_date.month) != month {
        return Err("outside supported calendar coverage".into());
    }
    Ok(VakyaCivilDateReverse {
        definition_id: tables::VAKYA_CIVIL_DEFINITION_ID,
        tamil_date,
        gregorian_date,
        reference_station: tables::VAKYA_CIVIL_REFERENCE_STATION,
        day_boundary: "ujjain_mean_sunrise",
    })
}

pub fn vakya_month_info(
    solar_year: i64,
    month: i64,
    _context: VakyaCivilContext,
) -> Result<VakyaCivilMonthInfo, String> {
    if !(tables::VAKYA_CIVIL_SOLAR_DATE_MIN_YEAR..=tables::VAKYA_CIVIL_SOLAR_DATE_MAX_YEAR)
        .contains(&solar_year)
        || !(1..=12).contains(&month)
    {
        return Err("invalid Tamil date".into());
    }
    let index = usize::try_from(month - 1).map_err(|_| "invalid Tamil date")?;
    let starts = solar_month_starts(solar_year)?;
    let start_date = date_from_kali_day(starts[index])?;
    let end_date_exclusive = date_from_kali_day(starts[index + 1])?;
    Ok(VakyaCivilMonthInfo {
        definition_id: tables::VAKYA_CIVIL_DEFINITION_ID,
        solar_year,
        month: month as u8,
        month_name: tables::VAKYA_CIVIL_MONTH_NAMES[index],
        start_date,
        end_date_exclusive,
        days: starts[index + 1] - starts[index],
        reference_station: tables::VAKYA_CIVIL_REFERENCE_STATION,
        day_boundary: "ujjain_mean_sunrise",
    })
}

pub(super) fn vakya_month_length(solar_year: i64, month: i64) -> Result<i64, String> {
    if !(tables::VAKYA_CIVIL_SOLAR_DATE_MIN_YEAR..=tables::VAKYA_CIVIL_SOLAR_DATE_MAX_YEAR)
        .contains(&solar_year)
        || !(1..=12).contains(&month)
    {
        return Err("invalid Tamil date".into());
    }
    let starts = solar_month_starts(solar_year)?;
    let index = (month - 1) as usize;
    Ok(starts[index + 1] - starts[index])
}

fn year_start(solar_year: i64) -> Result<YearStart, String> {
    if !(tables::VAKYA_CIVIL_SOLAR_DATE_MIN_YEAR..=tables::VAKYA_CIVIL_SOLAR_DATE_MAX_YEAR + 1)
        .contains(&solar_year)
    {
        return Err("outside supported calendar coverage".into());
    }
    let saka_year_elapsed = solar_year - 78;
    let kali_year = saka_year_elapsed + tables::VAKYA_SOLAR_SAKA_TO_KALI_YEAR;
    if kali_year <= 0 {
        return Err("outside supported calendar coverage".into());
    }
    let ahargana = super::vakya::vakya_ahargana(kali_year);
    let time = i64::from(ahargana.nadi) * 60 + i64::from(ahargana.vinadi);
    let sunrise_day = ahargana.days + i64::from(time > 0);
    Ok(YearStart {
        solar_year,
        ahargana,
        sunrise_day,
    })
}

fn solar_month_starts(solar_year: i64) -> Result<[i64; 13], String> {
    if !(tables::VAKYA_CIVIL_SOLAR_DATE_MIN_YEAR..=tables::VAKYA_CIVIL_SOLAR_DATE_MAX_YEAR)
        .contains(&solar_year)
    {
        return Err("outside supported calendar coverage".into());
    }
    let start = year_start(solar_year)?;
    let time_vinadis = i64::from(start.ahargana.nadi) * 60 + i64::from(start.ahargana.vinadi);
    let mut starts = [0_i64; 13];
    starts[0] = start.sunrise_day;
    for (month_index, start_day) in starts.iter_mut().enumerate().take(12).skip(1) {
        let target_arcseconds = i64::try_from(month_index).unwrap() * 30 * 3_600;
        let elapsed_vinadis = find_solar_crossing(target_arcseconds)?;
        *start_day =
            assign_ingress_sunrise_day(start.ahargana.days, time_vinadis + elapsed_vinadis);
    }
    starts[12] = year_start(solar_year + 1)?.sunrise_day;
    if !starts.windows(2).all(|pair| pair[0] < pair[1]) {
        return Err("outside supported calendar coverage".into());
    }
    Ok(starts)
}

fn find_solar_crossing(target_arcseconds: i64) -> Result<i64, String> {
    let mut low = 0_i64;
    let mut high = 360 * DAY_VINADIS;
    if true_sun_arcseconds(high)? < target_arcseconds {
        return Err("outside supported calendar coverage".into());
    }
    while low < high {
        let middle = low + (high - low) / 2;
        if true_sun_arcseconds(middle)? >= target_arcseconds {
            high = middle;
        } else {
            low = middle + 1;
        }
    }
    Ok(low)
}

fn true_sun_arcseconds(elapsed_vinadis: i64) -> Result<i64, String> {
    if !(0..=370 * DAY_VINADIS).contains(&elapsed_vinadis) {
        return Err("outside supported calendar coverage".into());
    }
    let day = elapsed_vinadis / DAY_VINADIS;
    let remainder = elapsed_vinadis % DAY_VINADIS;
    let nadi = remainder / 60;
    let vinadi = remainder % 60;
    let sun = vakya_true_sun_from_mesha_elapsed(day, nadi, vinadi)?;
    Ok(dms_arcseconds(sun.true_sun))
}

fn assign_ingress_sunrise_day(day: i64, vinadi_of_day: i64) -> i64 {
    let day_carry = vinadi_of_day.div_euclid(DAY_VINADIS);
    let time = vinadi_of_day.rem_euclid(DAY_VINADIS);
    day + day_carry + i64::from(time > 0)
}

fn kali_day_from_gregorian(date: GregorianDate) -> Result<i64, String> {
    let ordinal = ordinal_day(date);
    let kali_day = ordinal - tables::VAKYA_CIVIL_KALI_EPOCH_GREGORIAN_ORDINAL;
    if !(0..=SAFE_JSON_INTEGER).contains(&kali_day) {
        return Err("outside supported calendar coverage".into());
    }
    let first_supported = year_start(tables::VAKYA_CIVIL_SOLAR_DATE_MIN_YEAR)?.sunrise_day;
    if kali_day < first_supported {
        return Err("outside supported calendar coverage".into());
    }
    Ok(kali_day)
}

fn date_from_kali_day(kali_day: i64) -> Result<GregorianDate, String> {
    let ordinal = kali_day + tables::VAKYA_CIVIL_KALI_EPOCH_GREGORIAN_ORDINAL;
    date_from_ordinal(ordinal).map_err(|_| "outside supported calendar coverage".into())
}

pub fn vakya_panchangam_at(
    instant_unix_seconds: i64,
    context: VakyaCivilContext,
) -> Result<VakyaCivilPanchangamAt, String> {
    if i128::from(instant_unix_seconds).abs() > i128::from(SAFE_JSON_INTEGER) {
        return Err("outside supported calendar coverage".into());
    }
    let (local_date, local_time, mean_sunrise) =
        mean_sunrise_time_for_instant(instant_unix_seconds, context)?;
    ensure_lunar_coverage(mean_sunrise.kali_day)?;
    let sun = solar_angle_at_mean_time(mean_sunrise)?;
    let moon = moon_angle_at_mean_time(mean_sunrise)?;
    Ok(VakyaCivilPanchangamAt {
        definition_id: tables::VAKYA_CIVIL_DEFINITION_ID,
        local_date,
        local_time,
        vara: weekday_for_kali_day(mean_sunrise.vara_kali_day),
        limbs: limbs_from_positions(sun, moon),
        reference_station: tables::VAKYA_CIVIL_REFERENCE_STATION,
        position_basis: "ujjain_mean_solar_time",
    })
}

pub fn vakya_panchangam_day(
    date: GregorianDate,
    context: VakyaCivilContext,
) -> Result<VakyaCivilPanchangamDay, String> {
    ensure_civil_instant_date(date, context)?;
    let ordinal = ordinal_day(date);
    let days_from_unix_epoch = ordinal - UTC_EPOCH_ORDINAL;
    let local_midnight = days_from_unix_epoch
        .checked_mul(tables::VAKYA_CIVIL_SECONDS_PER_DAY)
        .ok_or("outside supported calendar coverage")?;
    let utc_start = local_midnight - tables::VAKYA_CIVIL_TIMEZONE_OFFSET_SECONDS;
    let utc_end = utc_start + tables::VAKYA_CIVIL_SECONDS_PER_DAY;

    let mean_sunrise_utc = local_midnight + tables::VAKYA_CIVIL_MEAN_SUNRISE_HOUR * 3_600
        - tables::VAKYA_CIVIL_TIMEZONE_OFFSET_SECONDS
        - ujjain_lmt_offset_from_ist_seconds();
    let sunrise_panchangam = vakya_panchangam_at(mean_sunrise_utc, context)?;
    let sunrise_minute = rounded_minute_of_day(
        i64::from(sunrise_panchangam.local_time.hour) * 3_600
            + i64::from(sunrise_panchangam.local_time.minute) * 60
            + i64::from(sunrise_panchangam.local_time.second),
    );

    let mut transitions = Vec::new();
    let first = vakya_panchangam_at(utc_start, context)?.limbs;
    let mut previous = first;
    let mut cursor = utc_start;
    while cursor < utc_end - 1 {
        let probe = (cursor + 60).min(utc_end - 1);
        let current = vakya_panchangam_at(probe, context)?.limbs;
        for (name, from, to) in changed_limb_indices(previous, current) {
            let crossing = find_limb_change(cursor, probe, name, from, context)?;
            let (day_offset, minute_of_day) = rounded_transition_label(crossing - utc_start);
            transitions.push((
                crossing,
                VakyaCivilTransition {
                    limb: name,
                    from_index: from,
                    to_index: to,
                    day_offset,
                    minute_of_day,
                },
            ));
        }
        previous = current;
        cursor = probe;
    }
    transitions.sort_by_key(|event| {
        (
            event.0,
            match event.1.limb {
                "tithi" => 0,
                "nakshatra" => 1,
                "yoga" => 2,
                "karana" => 3,
                _ => 4,
            },
        )
    });
    Ok(VakyaCivilPanchangamDay {
        definition_id: tables::VAKYA_CIVIL_DEFINITION_ID,
        date,
        sunrise_minute_of_day: sunrise_minute,
        sunrise_basis: "ujjain_mean_sunrise_not_local_horizon_sunrise",
        sunset_minute_of_day: None,
        sunset_status: "unavailable_source_bhujaantara_interpolation_unresolved",
        vara: sunrise_panchangam.vara,
        limbs_at_sunrise: sunrise_panchangam.limbs,
        transitions: transitions.into_iter().map(|(_, event)| event).collect(),
    })
}

fn ensure_civil_instant_date(
    date: GregorianDate,
    context: VakyaCivilContext,
) -> Result<(), String> {
    if date.year() < context.minimum_instant_year() {
        return Err("outside supported calendar coverage".into());
    }
    let kali_day = kali_day_from_gregorian(date)?;
    ensure_lunar_coverage(kali_day)
}

fn ensure_lunar_coverage(kali_day: i64) -> Result<(), String> {
    if !(tables::VAKYA_MOON_KALI_EPOCH_DAY..=SAFE_JSON_INTEGER).contains(&kali_day) {
        return Err("outside supported calendar coverage".into());
    }
    Ok(())
}

fn mean_sunrise_time_for_instant(
    instant_unix_seconds: i64,
    context: VakyaCivilContext,
) -> Result<(GregorianDate, VakyaCivilTime, MeanSunriseTime), String> {
    let local_seconds = instant_unix_seconds
        .checked_add(tables::VAKYA_CIVIL_TIMEZONE_OFFSET_SECONDS)
        .ok_or("outside supported calendar coverage")?;
    let local_unix_day = local_seconds.div_euclid(86_400);
    let local_day_seconds = local_seconds.rem_euclid(86_400);
    let local_date = date_from_ordinal(UTC_EPOCH_ORDINAL + local_unix_day)
        .map_err(|_| "outside supported calendar coverage")?;
    if local_date.year() < context.minimum_instant_year() {
        return Err("outside supported calendar coverage".into());
    }

    let ujjain_mean_seconds = local_seconds + ujjain_lmt_offset_from_ist_seconds();
    let since_mean_sunrise = ujjain_mean_seconds - tables::VAKYA_CIVIL_MEAN_SUNRISE_HOUR * 3_600;
    let mean_day = since_mean_sunrise.div_euclid(86_400);
    let seconds_after_sunrise = since_mean_sunrise.rem_euclid(86_400);
    let mut kali_day =
        UTC_EPOCH_ORDINAL + mean_day - tables::VAKYA_CIVIL_KALI_EPOCH_GREGORIAN_ORDINAL;
    let vara_kali_day = kali_day;
    let mut vinadi = (seconds_after_sunrise + tables::VAKYA_CIVIL_VINADI_SECONDS / 2)
        / tables::VAKYA_CIVIL_VINADI_SECONDS;
    if vinadi == DAY_VINADIS {
        kali_day += 1;
        vinadi = 0;
    }
    ensure_lunar_coverage(kali_day)?;
    let local_time = VakyaCivilTime {
        hour: (local_day_seconds / 3_600) as u8,
        minute: ((local_day_seconds % 3_600) / 60) as u8,
        second: (local_day_seconds % 60) as u8,
    };
    Ok((
        local_date,
        local_time,
        MeanSunriseTime {
            kali_day,
            vinadi_after_sunrise: vinadi,
            vara_kali_day,
        },
    ))
}

fn solar_angle_at_mean_time(time: MeanSunriseTime) -> Result<i64, String> {
    let mut start = solar_year_start_for_kali_day(time.kali_day)?;
    let mut elapsed_vinadis = (time.kali_day - start.ahargana.days) * DAY_VINADIS
        + time.vinadi_after_sunrise
        - (i64::from(start.ahargana.nadi) * 60 + i64::from(start.ahargana.vinadi));
    if elapsed_vinadis < 0 {
        start = year_start(start.solar_year - 1)?;
        elapsed_vinadis = (time.kali_day - start.ahargana.days) * DAY_VINADIS
            + time.vinadi_after_sunrise
            - (i64::from(start.ahargana.nadi) * 60 + i64::from(start.ahargana.vinadi));
    }
    if !(0..=370 * DAY_VINADIS).contains(&elapsed_vinadis) {
        return Err("outside supported calendar coverage".into());
    }
    true_sun_arcseconds(elapsed_vinadis)
}

fn moon_angle_at_mean_time(time: MeanSunriseTime) -> Result<i64, String> {
    let moon = vakya_true_moon_from_kali_day(time.kali_day)?;
    let position = rasi_dms_arcseconds(moon.true_moon);
    let motion = dms_arcseconds(moon.daily_motion);
    let advancement =
        i128::from(motion) * i128::from(time.vinadi_after_sunrise) / i128::from(DAY_VINADIS);
    let total = i128::from(position) + advancement;
    Ok(total.rem_euclid(360 * 3_600) as i64)
}

fn solar_year_start_for_kali_day(kali_day: i64) -> Result<YearStart, String> {
    let date = date_from_kali_day(kali_day)?;
    for solar_year in [date.year() - 1, date.year(), date.year() + 1] {
        if !(tables::VAKYA_CIVIL_SOLAR_DATE_MIN_YEAR..=tables::VAKYA_CIVIL_SOLAR_DATE_MAX_YEAR)
            .contains(&solar_year)
        {
            continue;
        }
        let current = year_start(solar_year)?;
        let next = year_start(solar_year + 1)?;
        if (current.sunrise_day..next.sunrise_day).contains(&kali_day) {
            return Ok(current);
        }
    }
    Err("outside supported calendar coverage".into())
}

fn solar_year_for_kali_day(kali_day: i64) -> Result<(i64, [i64; 13]), String> {
    let start = solar_year_start_for_kali_day(kali_day)?;
    Ok((start.solar_year, solar_month_starts(start.solar_year)?))
}

fn limbs_from_positions(sun: i64, moon: i64) -> VakyaCivilLimbs {
    let elongation = (moon - sun).rem_euclid(360 * 3_600);
    let tithi_index = (elongation / (12 * 3_600) + 1) as u8;
    let nakshatra_index = (moon / 48_000 + 1) as u8;
    let yoga_index = ((sun + moon).rem_euclid(360 * 3_600) / 48_000 + 1) as u8;
    let karana_index = (elongation / (6 * 3_600)) as u8;
    VakyaCivilLimbs {
        tithi: VakyaCivilLimb {
            index: tithi_index,
            name: if tithi_index == 30 {
                "Amavasya"
            } else {
                tables::DRIK_TITHI_NAMES[usize::from((tithi_index - 1) % 15)]
            },
            paksha: Some(if tithi_index <= 15 {
                "shukla"
            } else {
                "krishna"
            }),
        },
        nakshatra: VakyaCivilLimb {
            index: nakshatra_index,
            name: tables::DRIK_NAKSHATRA_NAMES[usize::from(nakshatra_index - 1)],
            paksha: None,
        },
        yoga: VakyaCivilLimb {
            index: yoga_index,
            name: tables::DRIK_YOGA_NAMES[usize::from(yoga_index - 1)],
            paksha: None,
        },
        karana: VakyaCivilLimb {
            index: karana_index,
            name: karana_name(karana_index),
            paksha: None,
        },
    }
}

fn karana_name(index: u8) -> &'static str {
    match index {
        0 => tables::DRIK_KARANA_NAMES[0],
        1..=56 => tables::DRIK_KARANA_NAMES[1 + usize::from((index - 1) % 7)],
        57..=59 => tables::DRIK_KARANA_NAMES[8 + usize::from(index - 57)],
        _ => unreachable!("karaṇa index always lies in 0..=59"),
    }
}

fn weekday_for_kali_day(kali_day: i64) -> &'static str {
    const WEEKDAYS: [&str; 7] = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ];
    WEEKDAYS[(KALI_EPOCH_WEEKDAY_INDEX + kali_day.rem_euclid(7)).rem_euclid(7) as usize]
}

fn find_limb_change(
    mut low: i64,
    mut high: i64,
    limb: &'static str,
    from_index: u8,
    context: VakyaCivilContext,
) -> Result<i64, String> {
    while low + 1 < high {
        let middle = low + (high - low) / 2;
        let indices = vakya_panchangam_at(middle, context)?.limbs;
        if limb_index(indices, limb) == from_index {
            low = middle;
        } else {
            high = middle;
        }
    }
    Ok(high)
}

fn changed_limb_indices(
    before: VakyaCivilLimbs,
    after: VakyaCivilLimbs,
) -> Vec<(&'static str, u8, u8)> {
    [
        ("tithi", before.tithi.index, after.tithi.index),
        ("nakshatra", before.nakshatra.index, after.nakshatra.index),
        ("yoga", before.yoga.index, after.yoga.index),
        ("karana", before.karana.index, after.karana.index),
    ]
    .into_iter()
    .filter(|(_, from, to)| from != to)
    .collect()
}

fn limb_index(limbs: VakyaCivilLimbs, limb: &str) -> u8 {
    match limb {
        "tithi" => limbs.tithi.index,
        "nakshatra" => limbs.nakshatra.index,
        "yoga" => limbs.yoga.index,
        "karana" => limbs.karana.index,
        _ => unreachable!("limb name was selected from the fixed list"),
    }
}

fn rounded_minute_of_day(seconds: i64) -> i64 {
    (seconds + 30).div_euclid(60)
}

fn rounded_transition_label(seconds_from_midnight: i64) -> (i64, i64) {
    let minute = rounded_minute_of_day(seconds_from_midnight);
    (minute.div_euclid(1_440), minute.rem_euclid(1_440))
}

fn ujjain_lmt_offset_from_ist_seconds() -> i64 {
    (tables::VAKYA_CIVIL_REFERENCE_STATION_LONGITUDE_MICRODEGREES
        - tables::VAKYA_CIVIL_IST_MERIDIAN_LONGITUDE_MICRODEGREES)
        * SECONDS_PER_LONGITUDE_DEGREE
        / 1_000_000
}

fn dms_arcseconds(angle: DmsAngle) -> i64 {
    angle.degrees * 3_600 + i64::from(angle.minutes) * 60 + i64::from(angle.seconds)
}

fn rasi_dms_arcseconds(angle: super::vakya::RasiDmsAngle) -> i64 {
    i64::from(angle.rasi) * 108_000
        + i64::from(angle.degrees) * 3_600
        + i64::from(angle.minutes) * 60
        + i64::from(angle.seconds)
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use proptest::test_runner::Config as ProptestConfig;

    fn reference_context() -> VakyaCivilContext {
        VakyaCivilContext::new("ujjain", "Asia/Kolkata").unwrap()
    }

    #[test]
    fn review_regression_transition_labels_carry_only_after_rounding() {
        assert_eq!(rounded_transition_label(86_384), (1, 0));
        assert_eq!(rounded_transition_label(86_369), (0, 1_439));
        assert_eq!(rounded_transition_label(86_370), (1, 0));
        assert_eq!(rounded_transition_label(4), (0, 0));
    }

    #[test]
    fn review_regression_civil_report_includes_crossings_in_the_final_minute() {
        let context = reference_context();
        let date = GregorianDate::new(2026, 6, 8).unwrap();
        let midnight = (ordinal_day(date) - UTC_EPOCH_ORDINAL) * 86_400
            - tables::VAKYA_CIVIL_TIMEZONE_OFFSET_SECONDS;
        let before = vakya_panchangam_at(midnight + 86_343, context).unwrap();
        let after = vakya_panchangam_at(midnight + 86_344, context).unwrap();
        assert_eq!(
            (before.limbs.tithi.index, after.limbs.tithi.index),
            (23, 24)
        );
        assert_eq!(
            (before.limbs.karana.index, after.limbs.karana.index),
            (45, 46)
        );
        let report = vakya_panchangam_day(date, context).unwrap();
        for (limb, from, to) in [("tithi", 23, 24), ("karana", 45, 46)] {
            assert!(
                report.transitions.iter().any(|event| {
                    event.limb == limb
                        && event.from_index == from
                        && event.to_index == to
                        && event.day_offset == 0
                        && event.minute_of_day == 1_439
                }),
                "missing final-minute {limb} crossing"
            );
        }
    }

    #[test]
    fn review_regression_vara_uses_the_exact_mean_sunrise_boundary() {
        let context = reference_context();
        let date = GregorianDate::new(2026, 6, 9).unwrap();
        let midnight = (ordinal_day(date) - UTC_EPOCH_ORDINAL) * 86_400
            - tables::VAKYA_CIVIL_TIMEZONE_OFFSET_SECONDS;
        for (second, expected) in [
            (39, "Monday"),
            (40, "Monday"),
            (51, "Monday"),
            (52, "Tuesday"),
            (53, "Tuesday"),
        ] {
            let at = vakya_panchangam_at(midnight + 6 * 3_600 + 26 * 60 + second, context).unwrap();
            assert_eq!(at.vara, expected, "06:26:{second}");
        }
    }

    #[test]
    fn printed_kali_day_and_candra_vakya_example_form_a_civil_round_trip() {
        let context = reference_context();
        let date = GregorianDate::new(1947, 10, 11).unwrap();
        let forward = vakya_gregorian_to_tamil_date(date, context).unwrap();
        assert_eq!(
            forward.tamil_date,
            VakyaCivilTamilDate {
                solar_year: 1947,
                month: 6,
                month_name: "Purattasi",
                day: 24,
            }
        );
        let reverse = vakya_tamil_to_gregorian_date(1947, 6, 24, context).unwrap();
        assert_eq!(reverse.gregorian_date, date);
        assert_eq!(kali_day_from_gregorian(date).unwrap(), 1_844_004);
        assert_eq!(
            vakya_true_sun_from_mesha_elapsed(180, 19, 41)
                .unwrap()
                .true_sun,
            DmsAngle {
                degrees: 173,
                minutes: 28,
                seconds: 33,
            }
        );
    }

    #[test]
    fn printed_true_sun_and_moon_example_gives_the_five_expected_limbs() {
        let context = reference_context();
        let at = vakya_panchangam_at(-701_391_788, context).unwrap();
        assert_eq!(
            (
                at.local_date.year(),
                at.local_date.month(),
                at.local_date.day()
            ),
            (1947, 10, 11)
        );
        assert_eq!(
            at.local_time,
            VakyaCivilTime {
                hour: 6,
                minute: 26,
                second: 52,
            }
        );
        assert_eq!(at.vara, "Saturday");
        assert_eq!(at.limbs.tithi.index, 27);
        assert_eq!(at.limbs.tithi.name, "Dwadashi");
        assert_eq!(at.limbs.tithi.paksha, Some("krishna"));
        assert_eq!(at.limbs.nakshatra.index, 10);
        assert_eq!(at.limbs.nakshatra.name, "Magha");
        assert_eq!(at.limbs.yoga.index, 23);
        assert_eq!(at.limbs.yoga.name, "Shubha");
        assert_eq!(at.limbs.karana.index, 52);
        assert_eq!(at.limbs.karana.name, "Kaulava");
    }

    #[test]
    fn every_classical_month_in_the_supported_witness_years_round_trips() {
        let context = reference_context();
        for solar_year in 1947..=1968 {
            let starts = solar_month_starts(solar_year).unwrap();
            assert_eq!(starts.len(), 13);
            assert!(starts
                .windows(2)
                .all(|pair| (29..=32).contains(&(pair[1] - pair[0]))));
            for month in 1_u8..=12 {
                let month_index = usize::from(month - 1);
                let info = vakya_month_info(solar_year, i64::from(month), context).unwrap_or_else(
                    |error| panic!("solar year {solar_year}, month {month}: {error}"),
                );
                assert_eq!(info.days, starts[month_index + 1] - starts[month_index]);
                let first = vakya_gregorian_to_tamil_date(info.start_date, context).unwrap();
                let last = vakya_gregorian_to_tamil_date(
                    date_from_kali_day(starts[month_index + 1] - 1).unwrap(),
                    context,
                )
                .unwrap();
                assert_eq!(
                    (
                        first.tamil_date.solar_year,
                        first.tamil_date.month,
                        first.tamil_date.day
                    ),
                    (solar_year, month, 1)
                );
                assert_eq!(last.tamil_date.solar_year, solar_year);
                assert_eq!(last.tamil_date.month, month);
                assert_eq!(last.tamil_date.day, info.days);
                assert_eq!(
                    vakya_tamil_to_gregorian_date(solar_year, i64::from(month), 1, context)
                        .unwrap()
                        .gregorian_date,
                    info.start_date
                );
            }
        }
        // The same source equations are defined beyond the two printed worked years.
        let current_date = GregorianDate::new(2026, 11, 2).unwrap();
        let converted = vakya_gregorian_to_tamil_date(current_date, context).unwrap();
        assert_eq!(
            vakya_tamil_to_gregorian_date(
                converted.tamil_date.solar_year,
                i64::from(converted.tamil_date.month),
                converted.tamil_date.day,
                context
            )
            .unwrap()
            .gregorian_date,
            current_date
        );
    }

    #[test]
    fn civil_day_reports_reference_mean_sunrise_and_real_limb_transitions() {
        let context = reference_context();
        let report =
            vakya_panchangam_day(GregorianDate::new(1947, 10, 11).unwrap(), context).unwrap();
        assert_eq!(report.sunrise_minute_of_day, 387);
        assert_eq!(
            report.sunrise_basis,
            "ujjain_mean_sunrise_not_local_horizon_sunrise"
        );
        assert_eq!(report.sunset_minute_of_day, None);
        assert_eq!(
            report.sunset_status,
            "unavailable_source_bhujaantara_interpolation_unresolved"
        );
        assert!(!report.transitions.is_empty());
        assert!(report
            .transitions
            .windows(2)
            .all(|pair| pair[0].minute_of_day <= pair[1].minute_of_day));
    }

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]

        #[test]
        fn ingress_date_is_the_first_mean_sunrise_at_or_after_the_event(
            day in -2_000_000i64..=2_000_000,
            time in 0i64..=DAY_VINADIS,
        ) {
            let assigned = assign_ingress_sunrise_day(day, time);
            let expected = day + i64::from(time > 0);
            prop_assert_eq!(assigned, expected);
        }
    }
}

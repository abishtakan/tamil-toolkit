use crate::tables;
use crate::tables::{
    DRIK_DEFINITION_ID, DRIK_DISPLAY_ROUNDING_SECONDS, DRIK_EARTH_RADIUS_METERS,
    DRIK_EPHEMERIS_ARCHIVE_SHA256, DRIK_EPHEMERIS_LICENSE, DRIK_EPHEMERIS_PROVIDER,
    DRIK_EPHEMERIS_VERSION, DRIK_HORIZON_DEFINITION, DRIK_KARANA_NAMES,
    DRIK_LAHIRI_ANCHOR_JD_CENTIDAYS, DRIK_LAHIRI_ANCHOR_MILLIARCSECONDS,
    DRIK_LAHIRI_MEAN_ANCHOR_MICROARCSECONDS, DRIK_LUNAR_COORDINATE_DEFINITION, DRIK_MONTH_NAMES,
    DRIK_MOON_MODEL, DRIK_NAKSHATRA_NAMES, DRIK_NUTATION_MODEL, DRIK_PRECESSION_CENTURY_DAYS,
    DRIK_PRECESSION_EPOCH_JD_MILLIDAYS, DRIK_PRECESSION_PICOARCSECONDS, DRIK_PROFILE_NAME,
    DRIK_PUBLIC_END_YEAR, DRIK_PUBLIC_START_YEAR, DRIK_REFERENCE_STATIONS,
    DRIK_REFRACTION_ARCMINUTES, DRIK_REGION_RULES, DRIK_ROOT_SCAN_STEP_SECONDS,
    DRIK_SIDEREAL_COORDINATE_DEFINITION, DRIK_SIDEREAL_DEFINITION,
    DRIK_SOLAR_COORDINATE_DEFINITION, DRIK_SOLAR_MONTH_RULE, DRIK_SOLAR_SEMIDIAMETER_ARCMINUTES,
    DRIK_SOLAR_YEAR_END, DRIK_SOLAR_YEAR_START, DRIK_SOURCE_URLS,
    DRIK_SUNRISE_CENTER_ALTITUDE_ARCMINUTES, DRIK_SUN_MODEL, DRIK_TITHI_NAMES,
    DRIK_TT_MINUS_UTC_MILLIS, DRIK_TZ_DATABASE_RELEASE, DRIK_UT1_MINUS_UTC_ASSUMED_MILLIS,
    DRIK_UT1_MINUS_UTC_MAX_ABS_MILLIS, DRIK_VARA_DEFINITION, DRIK_WEEKDAYS, DRIK_YOGA_NAMES,
};
use astro::{aberr, ecliptic, lunar, nutation, sun, time};
use std::collections::BTreeSet;
use std::f64::consts::{PI, TAU};
use tamil_numerals::{add_gregorian_date, date_difference, GregorianDate};

const SECONDS_PER_DAY: i64 = 86_400;
const UNIX_EPOCH_JD: f64 = 2_440_587.5;
const DEG_TO_RAD: f64 = PI / 180.0;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamContext {
    region: &'static str,
    time_zone: &'static str,
    utc_offset_seconds: i64,
    latitude_microdegrees: i64,
    longitude_microdegrees: i64,
    elevation_meters: i64,
}

impl ThirukanithamContext {
    pub fn new(
        region: &str,
        latitude_microdegrees: i64,
        longitude_microdegrees: i64,
        elevation_meters: i64,
        time_zone: &str,
    ) -> Result<Self, String> {
        let rule = DRIK_REGION_RULES
            .iter()
            .find(|rule| rule.0 == region)
            .ok_or("invalid calendar context")?;
        if rule.1 != time_zone {
            return Err("unsupported time zone".into());
        }
        if !(rule.3..=rule.4).contains(&latitude_microdegrees)
            || !(rule.5..=rule.6).contains(&longitude_microdegrees)
            || !(-100..=3_000).contains(&elevation_meters)
        {
            return Err("unsupported location".into());
        }
        Ok(Self {
            region: rule.0,
            time_zone: rule.1,
            utc_offset_seconds: rule.2,
            latitude_microdegrees,
            longitude_microdegrees,
            elevation_meters,
        })
    }

    pub fn region(self) -> &'static str {
        self.region
    }

    pub fn time_zone(self) -> &'static str {
        self.time_zone
    }

    pub fn utc_offset_seconds(self) -> i64 {
        self.utc_offset_seconds
    }

    pub fn latitude_microdegrees(self) -> i64 {
        self.latitude_microdegrees
    }

    pub fn longitude_microdegrees(self) -> i64 {
        self.longitude_microdegrees
    }

    pub fn elevation_meters(self) -> i64 {
        self.elevation_meters
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamRegionInfo {
    pub region: &'static str,
    pub time_zone: &'static str,
    pub utc_offset_seconds: i64,
    pub latitude_min_microdegrees: i64,
    pub latitude_max_microdegrees: i64,
    pub longitude_min_microdegrees: i64,
    pub longitude_max_microdegrees: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamStationInfo {
    pub id: &'static str,
    pub region: &'static str,
    pub latitude_microdegrees: i64,
    pub longitude_microdegrees: i64,
    pub elevation_meters: i64,
    pub source: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ThirukanithamProfileInfo {
    pub profile: &'static str,
    pub definition_id: &'static str,
    pub sidereal_definition: &'static str,
    pub public_start_year: i64,
    pub public_end_year: i64,
    pub solar_year_start: i64,
    pub solar_year_end: i64,
    pub tt_minus_utc_millis: i64,
    pub ut1_minus_utc_assumed_millis: i64,
    pub ut1_minus_utc_max_abs_millis: i64,
    pub sunrise_center_altitude_arcminutes: i64,
    pub refraction_arcminutes: i64,
    pub solar_semidiameter_arcminutes: i64,
    pub earth_radius_meters: i64,
    pub horizon_definition: &'static str,
    pub ephemeris_provider: &'static str,
    pub ephemeris_version: &'static str,
    pub ephemeris_license: &'static str,
    pub ephemeris_archive_sha256: &'static str,
    pub sun_model: &'static str,
    pub moon_model: &'static str,
    pub nutation_model: &'static str,
    pub solar_coordinate_definition: &'static str,
    pub lunar_coordinate_definition: &'static str,
    pub sidereal_coordinate_definition: &'static str,
    pub vara_definition: &'static str,
    pub lahiri_true_anchor_milliarcseconds: i64,
    pub lahiri_mean_anchor_microarcseconds: i64,
    pub lahiri_anchor_jd_centidays: i64,
    pub precession_picoarcseconds_per_power: [i64; 6],
    pub precession_epoch_jd_millidays: i64,
    pub precession_century_days: i64,
    pub time_zone_database_release: &'static str,
    pub solar_month_rule: &'static str,
    pub sources: Vec<&'static str>,
    pub regions: Vec<ThirukanithamRegionInfo>,
    pub reference_stations: Vec<ThirukanithamStationInfo>,
}

pub fn thirukanitham_profile_info() -> ThirukanithamProfileInfo {
    ThirukanithamProfileInfo {
        profile: DRIK_PROFILE_NAME,
        definition_id: DRIK_DEFINITION_ID,
        sidereal_definition: DRIK_SIDEREAL_DEFINITION,
        public_start_year: DRIK_PUBLIC_START_YEAR,
        public_end_year: DRIK_PUBLIC_END_YEAR,
        solar_year_start: DRIK_SOLAR_YEAR_START,
        solar_year_end: DRIK_SOLAR_YEAR_END,
        tt_minus_utc_millis: DRIK_TT_MINUS_UTC_MILLIS,
        ut1_minus_utc_assumed_millis: DRIK_UT1_MINUS_UTC_ASSUMED_MILLIS,
        ut1_minus_utc_max_abs_millis: DRIK_UT1_MINUS_UTC_MAX_ABS_MILLIS,
        sunrise_center_altitude_arcminutes: DRIK_SUNRISE_CENTER_ALTITUDE_ARCMINUTES,
        refraction_arcminutes: DRIK_REFRACTION_ARCMINUTES,
        solar_semidiameter_arcminutes: DRIK_SOLAR_SEMIDIAMETER_ARCMINUTES,
        earth_radius_meters: DRIK_EARTH_RADIUS_METERS,
        horizon_definition: DRIK_HORIZON_DEFINITION,
        ephemeris_provider: DRIK_EPHEMERIS_PROVIDER,
        ephemeris_version: DRIK_EPHEMERIS_VERSION,
        ephemeris_license: DRIK_EPHEMERIS_LICENSE,
        ephemeris_archive_sha256: DRIK_EPHEMERIS_ARCHIVE_SHA256,
        sun_model: DRIK_SUN_MODEL,
        moon_model: DRIK_MOON_MODEL,
        nutation_model: DRIK_NUTATION_MODEL,
        solar_coordinate_definition: DRIK_SOLAR_COORDINATE_DEFINITION,
        lunar_coordinate_definition: DRIK_LUNAR_COORDINATE_DEFINITION,
        sidereal_coordinate_definition: DRIK_SIDEREAL_COORDINATE_DEFINITION,
        vara_definition: DRIK_VARA_DEFINITION,
        lahiri_true_anchor_milliarcseconds: DRIK_LAHIRI_ANCHOR_MILLIARCSECONDS,
        lahiri_mean_anchor_microarcseconds: DRIK_LAHIRI_MEAN_ANCHOR_MICROARCSECONDS,
        lahiri_anchor_jd_centidays: DRIK_LAHIRI_ANCHOR_JD_CENTIDAYS,
        precession_picoarcseconds_per_power: DRIK_PRECESSION_PICOARCSECONDS,
        precession_epoch_jd_millidays: DRIK_PRECESSION_EPOCH_JD_MILLIDAYS,
        precession_century_days: DRIK_PRECESSION_CENTURY_DAYS,
        time_zone_database_release: DRIK_TZ_DATABASE_RELEASE,
        solar_month_rule: DRIK_SOLAR_MONTH_RULE,
        sources: DRIK_SOURCE_URLS.to_vec(),
        regions: DRIK_REGION_RULES
            .iter()
            .map(|rule| ThirukanithamRegionInfo {
                region: rule.0,
                time_zone: rule.1,
                utc_offset_seconds: rule.2,
                latitude_min_microdegrees: rule.3,
                latitude_max_microdegrees: rule.4,
                longitude_min_microdegrees: rule.5,
                longitude_max_microdegrees: rule.6,
            })
            .collect(),
        reference_stations: DRIK_REFERENCE_STATIONS
            .iter()
            .map(|station| ThirukanithamStationInfo {
                id: station.0,
                region: station.1,
                latitude_microdegrees: station.2,
                longitude_microdegrees: station.3,
                elevation_meters: station.4,
                source: station.5,
            })
            .collect(),
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamTamilDate {
    pub solar_year: i64,
    pub month: u8,
    pub month_name: &'static str,
    pub day: u8,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamDateConversion {
    pub definition_id: &'static str,
    pub gregorian_date: GregorianDate,
    pub tamil_date: ThirukanithamTamilDate,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamDateReverse {
    pub definition_id: &'static str,
    pub tamil_date: ThirukanithamTamilDate,
    pub gregorian_date: GregorianDate,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamMonthInfo {
    pub definition_id: &'static str,
    pub solar_year: i64,
    pub month: u8,
    pub month_name: &'static str,
    pub start_date: GregorianDate,
    pub end_date_exclusive: GregorianDate,
    pub days: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamLimb {
    pub index: u8,
    pub name: &'static str,
    pub paksha: Option<&'static str>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamLimbs {
    pub tithi: ThirukanithamLimb,
    pub nakshatra: ThirukanithamLimb,
    pub yoga: ThirukanithamLimb,
    pub karana: ThirukanithamLimb,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamLocalTime {
    pub year: i64,
    pub month: u32,
    pub day: u32,
    pub hour: u8,
    pub minute: u8,
    pub second: u8,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamPanchangamAt {
    pub definition_id: &'static str,
    pub local_date: GregorianDate,
    pub local_time: ThirukanithamLocalTime,
    pub vara: &'static str,
    pub limbs: ThirukanithamLimbs,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamTransition {
    pub limb: &'static str,
    pub from_index: u8,
    pub to_index: u8,
    pub day_offset: i64,
    pub minute_of_day: i64,
    instant_unix_seconds: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ThirukanithamPanchangamDay {
    pub definition_id: &'static str,
    pub date: GregorianDate,
    pub sunrise_minute_of_day: i64,
    pub sunset_minute_of_day: i64,
    pub vara: &'static str,
    pub limbs_at_sunrise: ThirukanithamLimbs,
    pub transitions: Vec<ThirukanithamTransition>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamDaylightInterval {
    pub period: &'static str,
    pub eighth_part: u8,
    pub start_local_seconds_of_day: i64,
    pub end_local_seconds_of_day: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ThirukanithamDaylightPeriods {
    pub definition_id: &'static str,
    pub date: GregorianDate,
    pub weekday: &'static str,
    pub rule_id: &'static str,
    pub source: &'static str,
    pub source_sha256: &'static str,
    pub sunrise_local_seconds_of_day: i64,
    pub sunset_local_seconds_of_day: i64,
    pub intervals: Vec<ThirukanithamDaylightInterval>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamUtcMinute {
    pub year: i64,
    pub month: u8,
    pub day: u8,
    pub hour: u8,
    pub minute: u8,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThirukanithamLunarPhaseEvent {
    pub phase: &'static str,
    pub ecliptic_longitude_difference_degrees: u16,
    pub utc_minute: ThirukanithamUtcMinute,
    pub instant_utc_seconds: i64,
}

#[derive(Debug, Clone, Copy)]
struct EphemerisPosition {
    sun_apparent_longitude_deg: f64,
    sun_apparent_latitude_rad: f64,
    moon_apparent_longitude_deg: f64,
    moon_apparent_latitude_rad: f64,
    moon_distance_km: f64,
    nutation_longitude_rad: f64,
    true_obliquity_rad: f64,
}

#[derive(Debug, Clone, Copy)]
struct SolarIngress {
    month: u8,
    instant_utc_seconds: i64,
}

#[derive(Debug, Clone, Copy)]
struct SolarMonthStart {
    solar_year: i64,
    month: u8,
    date: GregorianDate,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct LimbIndices {
    tithi: u8,
    nakshatra: u8,
    yoga: u8,
    karana: u8,
}

pub fn thirukanitham_gregorian_to_tamil_date(
    date: GregorianDate,
    context: ThirukanithamContext,
) -> Result<ThirukanithamDateConversion, String> {
    ensure_public_date(date)?;
    let starts = solar_month_starts_near_date(date, context)?;
    let start = starts
        .into_iter()
        .filter(|start| date_difference(start.date, date) >= 0)
        .max_by_key(|start| (start.date.year(), start.date.month(), start.date.day()))
        .ok_or("outside supported calendar coverage")?;
    let day = date_difference(start.date, date) + 1;
    if !(1..=35).contains(&day) {
        return Err("outside supported calendar coverage".into());
    }
    Ok(ThirukanithamDateConversion {
        definition_id: DRIK_DEFINITION_ID,
        gregorian_date: date,
        tamil_date: tamil_date(start.solar_year, start.month, day as u8),
    })
}

pub fn thirukanitham_tamil_to_gregorian_date(
    solar_year: i64,
    month: i64,
    day: i64,
    context: ThirukanithamContext,
) -> Result<ThirukanithamDateReverse, String> {
    if !(DRIK_SOLAR_YEAR_START..=DRIK_SOLAR_YEAR_END).contains(&solar_year) {
        return Err("outside supported calendar coverage".into());
    }
    if !(1..=12).contains(&month) || day < 1 {
        return Err("invalid Tamil date".into());
    }
    let start = solar_month_start(solar_year, month as u8, context)?;
    let next_year = if month == 12 {
        solar_year + 1
    } else {
        solar_year
    };
    let next_month = if month == 12 { 1 } else { month as u8 + 1 };
    let end = solar_month_start(next_year, next_month, context)?;
    let days = date_difference(start, end);
    if day > days {
        return Err("invalid Tamil date".into());
    }
    let gregorian_date = add_gregorian_date(start, "days", day - 1, "reject")
        .map_err(|_| "outside supported calendar coverage")?;
    ensure_public_date(gregorian_date)?;
    Ok(ThirukanithamDateReverse {
        definition_id: DRIK_DEFINITION_ID,
        tamil_date: tamil_date(solar_year, month as u8, day as u8),
        gregorian_date,
    })
}

pub fn thirukanitham_month_info(
    solar_year: i64,
    month: i64,
    context: ThirukanithamContext,
) -> Result<ThirukanithamMonthInfo, String> {
    if !(DRIK_SOLAR_YEAR_START..=DRIK_SOLAR_YEAR_END).contains(&solar_year) {
        return Err("outside supported calendar coverage".into());
    }
    if !(1..=12).contains(&month) {
        return Err("invalid Tamil date".into());
    }
    let month = month as u8;
    let start_date = solar_month_start(solar_year, month, context)?;
    ensure_public_date(start_date)?;
    let (next_year, next_month) = if month == 12 {
        (solar_year + 1, 1)
    } else {
        (solar_year, month + 1)
    };
    let end_date_exclusive = solar_month_start(next_year, next_month, context)?;
    let days = date_difference(start_date, end_date_exclusive);
    if !(29..=32).contains(&days) {
        return Err("outside supported calendar coverage".into());
    }
    Ok(ThirukanithamMonthInfo {
        definition_id: DRIK_DEFINITION_ID,
        solar_year,
        month,
        month_name: DRIK_MONTH_NAMES[usize::from(month - 1)],
        start_date,
        end_date_exclusive,
        days,
    })
}

pub fn thirukanitham_panchangam_at(
    instant_unix_seconds: i64,
    context: ThirukanithamContext,
) -> Result<ThirukanithamPanchangamAt, String> {
    let local_time = local_datetime(instant_unix_seconds, context)?;
    let local_date = GregorianDate::new(
        local_time.year,
        i64::from(local_time.month),
        i64::from(local_time.day),
    )
    .map_err(|_| "outside supported calendar coverage")?;
    ensure_public_date(local_date)?;
    let position = position_at(instant_unix_seconds);
    Ok(ThirukanithamPanchangamAt {
        definition_id: DRIK_DEFINITION_ID,
        local_date,
        local_time,
        vara: vara_for_date(local_date),
        limbs: limb_values(instant_unix_seconds, position),
    })
}

pub fn thirukanitham_panchangam_day(
    date: GregorianDate,
    context: ThirukanithamContext,
) -> Result<ThirukanithamPanchangamDay, String> {
    ensure_public_date(date)?;
    let (sunrise, sunset) = solar_events_for_date(date, context)?;
    let sunrise_local_minute = rounded_local_minute(sunrise, date, context)?;
    let sunset_local_minute = rounded_local_minute(sunset, date, context)?;
    let limbs_at_sunrise = limb_values(sunrise, position_at(sunrise));
    let start = local_midnight_unix(date, context)?;
    let end = start + SECONDS_PER_DAY;
    let transitions = limb_transitions(start, end, context)?;
    Ok(ThirukanithamPanchangamDay {
        definition_id: DRIK_DEFINITION_ID,
        date,
        sunrise_minute_of_day: sunrise_local_minute,
        sunset_minute_of_day: sunset_local_minute,
        vara: vara_for_date(date),
        limbs_at_sunrise,
        transitions,
    })
}

pub fn thirukanitham_daylight_periods(
    date: GregorianDate,
    context: ThirukanithamContext,
) -> Result<ThirukanithamDaylightPeriods, String> {
    ensure_public_date(date)?;
    let (sunrise, sunset) = solar_events_for_date(date, context)?;
    let midnight = unix_midnight(date)?;
    let sunrise_local = sunrise
        .checked_add(context.utc_offset_seconds)
        .and_then(|seconds| seconds.checked_sub(midnight))
        .ok_or("outside supported calendar coverage")?;
    let sunset_local = sunset
        .checked_add(context.utc_offset_seconds)
        .and_then(|seconds| seconds.checked_sub(midnight))
        .ok_or("outside supported calendar coverage")?;
    let daylight = sunset_local - sunrise_local;
    if !(0..SECONDS_PER_DAY).contains(&daylight) {
        return Err("solar event unavailable".into());
    }
    let weekday_index = (date_difference(
        GregorianDate::new(1970, 1, 1).expect("Unix epoch is valid"),
        date,
    ) + 4)
        .rem_euclid(7) as usize;
    let mut intervals = vec![
        daylight_interval(
            "rahukalam",
            tables::DRIK_RAHU_EIGHTH_BY_WEEKDAY[weekday_index],
            sunrise_local,
            daylight,
        ),
        daylight_interval(
            "yamagandam",
            tables::DRIK_YAMAGANDAM_EIGHTH_BY_WEEKDAY[weekday_index],
            sunrise_local,
            daylight,
        ),
        daylight_interval(
            "kuligai",
            tables::DRIK_KULIGAI_EIGHTH_BY_WEEKDAY[weekday_index],
            sunrise_local,
            daylight,
        ),
    ];
    intervals.sort_by_key(|interval| interval.start_local_seconds_of_day);
    Ok(ThirukanithamDaylightPeriods {
        definition_id: DRIK_DEFINITION_ID,
        date,
        weekday: vara_for_date(date),
        rule_id: tables::DRIK_DAYLIGHT_PERIOD_RULE,
        source: tables::DRIK_DAYLIGHT_PERIOD_SOURCE,
        source_sha256: tables::DRIK_DAYLIGHT_PERIOD_SOURCE_SHA256,
        sunrise_local_seconds_of_day: sunrise_local,
        sunset_local_seconds_of_day: sunset_local,
        intervals,
    })
}

fn daylight_interval(
    period: &'static str,
    eighth_part: u8,
    sunrise: i64,
    daylight: i64,
) -> ThirukanithamDaylightInterval {
    let index = i64::from(eighth_part);
    ThirukanithamDaylightInterval {
        period,
        eighth_part,
        start_local_seconds_of_day: sunrise + daylight * (index - 1) / 8,
        end_local_seconds_of_day: sunrise + daylight * index / 8,
    }
}

/// Return the four geocentric apparent ecliptic phase crossings in a half-open
/// UTC interval. The public phase label is rounded to the nearest minute;
/// `instant_utc_seconds` retains the one-second root for ordering and tests.
pub fn thirukanitham_lunar_phase_events(
    start_utc_seconds: i64,
    end_utc_seconds: i64,
) -> Result<Vec<ThirukanithamLunarPhaseEvent>, String> {
    let max_interval = 35 * SECONDS_PER_DAY;
    if end_utc_seconds <= start_utc_seconds || end_utc_seconds - start_utc_seconds > max_interval {
        return Err("invalid calendar input".into());
    }
    let first_date = date_from_unix_seconds(start_utc_seconds)?;
    let last_date = date_from_unix_seconds(end_utc_seconds - 1)?;
    ensure_public_date(first_date)?;
    ensure_public_date(last_date)?;

    const SCAN_STEP_SECONDS: i64 = 6 * 60 * 60;
    let mut cursor = start_utc_seconds - 1;
    let mut before = phase_sector_at(cursor);
    let mut events = Vec::new();
    while cursor < end_utc_seconds - 1 {
        let probe = (cursor + SCAN_STEP_SECONDS).min(end_utc_seconds - 1);
        let after = phase_sector_at(probe);
        if after != before {
            let root = bisect_predicate(cursor, probe, |candidate| {
                phase_sector_at(candidate) != before
            });
            if root >= start_utc_seconds && root < end_utc_seconds {
                let sector = phase_sector_at(root);
                let (phase, degrees) = match sector {
                    0 => ("new_moon", 0),
                    1 => ("first_quarter", 90),
                    2 => ("full_moon", 180),
                    3 => ("last_quarter", 270),
                    _ => unreachable!("phase sectors are modulo four"),
                };
                let rounded_utc_minute = (root + 30).div_euclid(60) * 60;
                let date = date_from_unix_seconds(rounded_utc_minute)?;
                let seconds_of_day = rounded_utc_minute.rem_euclid(SECONDS_PER_DAY);
                events.push(ThirukanithamLunarPhaseEvent {
                    phase,
                    ecliptic_longitude_difference_degrees: degrees,
                    utc_minute: ThirukanithamUtcMinute {
                        year: date.year(),
                        month: date.month() as u8,
                        day: date.day() as u8,
                        hour: (seconds_of_day / 3_600) as u8,
                        minute: ((seconds_of_day % 3_600) / 60) as u8,
                    },
                    instant_utc_seconds: root,
                });
            }
            cursor = root;
            before = phase_sector_at(root);
        } else {
            cursor = probe;
            before = after;
        }
    }
    events.sort_by_key(|event| event.instant_utc_seconds);
    Ok(events)
}

fn tamil_date(solar_year: i64, month: u8, day: u8) -> ThirukanithamTamilDate {
    ThirukanithamTamilDate {
        solar_year,
        month,
        month_name: DRIK_MONTH_NAMES[usize::from(month - 1)],
        day,
    }
}

fn ensure_public_date(date: GregorianDate) -> Result<(), String> {
    if (DRIK_PUBLIC_START_YEAR..=DRIK_PUBLIC_END_YEAR).contains(&date.year()) {
        Ok(())
    } else {
        Err("outside supported calendar coverage".into())
    }
}

fn unix_midnight(date: GregorianDate) -> Result<i64, String> {
    let epoch = GregorianDate::new(1970, 1, 1).expect("Unix epoch is a valid Gregorian date");
    date_difference(epoch, date)
        .checked_mul(SECONDS_PER_DAY)
        .ok_or_else(|| "outside supported calendar coverage".into())
}

fn date_from_unix_seconds(seconds: i64) -> Result<GregorianDate, String> {
    let epoch = GregorianDate::new(1970, 1, 1).expect("Unix epoch is a valid Gregorian date");
    add_gregorian_date(epoch, "days", seconds.div_euclid(SECONDS_PER_DAY), "reject")
        .map_err(|_| "outside supported calendar coverage".into())
}

fn local_midnight_unix(date: GregorianDate, context: ThirukanithamContext) -> Result<i64, String> {
    unix_midnight(date)?
        .checked_sub(context.utc_offset_seconds)
        .ok_or_else(|| "outside supported calendar coverage".into())
}

fn local_datetime(
    instant_unix_seconds: i64,
    context: ThirukanithamContext,
) -> Result<ThirukanithamLocalTime, String> {
    let local_seconds = instant_unix_seconds
        .checked_add(context.utc_offset_seconds)
        .ok_or_else(|| "outside supported calendar coverage".to_owned())?;
    let date = date_from_unix_seconds(local_seconds)?;
    let second_of_day = local_seconds.rem_euclid(SECONDS_PER_DAY);
    Ok(ThirukanithamLocalTime {
        year: date.year(),
        month: date.month(),
        day: date.day(),
        hour: (second_of_day / 3_600) as u8,
        minute: ((second_of_day % 3_600) / 60) as u8,
        second: (second_of_day % 60) as u8,
    })
}

fn julian_day_utc(instant_unix_seconds: i64) -> f64 {
    UNIX_EPOCH_JD + instant_unix_seconds as f64 / SECONDS_PER_DAY as f64
}

fn julian_ephemeris_day(instant_unix_seconds: i64) -> f64 {
    julian_day_utc(instant_unix_seconds) + DRIK_TT_MINUS_UTC_MILLIS as f64 / 86_400_000.0
}

fn wrap_degrees(angle: f64) -> f64 {
    angle.rem_euclid(360.0)
}

fn forward_delta_degrees(from: f64, to: f64) -> f64 {
    (to - from).rem_euclid(360.0)
}

fn precession_arcseconds(centuries: f64) -> f64 {
    DRIK_PRECESSION_PICOARCSECONDS
        .iter()
        .rev()
        .fold(0.0, |value, coefficient| {
            value * centuries + *coefficient as f64 / 1.0e12
        })
}

fn lahiri_mean_ayanamsa_degrees(jde: f64) -> f64 {
    let j2000 = DRIK_PRECESSION_EPOCH_JD_MILLIDAYS as f64 / 1_000.0;
    let centuries = (jde - j2000) / DRIK_PRECESSION_CENTURY_DAYS as f64;
    let anchor_jd = DRIK_LAHIRI_ANCHOR_JD_CENTIDAYS as f64 / 100.0;
    let anchor_centuries = (anchor_jd - j2000) / DRIK_PRECESSION_CENTURY_DAYS as f64;
    DRIK_LAHIRI_MEAN_ANCHOR_MICROARCSECONDS as f64 / 3_600_000_000.0
        + (precession_arcseconds(centuries) - precession_arcseconds(anchor_centuries)) / 3_600.0
}

fn lahiri_true_ayanamsa_degrees(jde: f64) -> f64 {
    lahiri_mean_ayanamsa_degrees(jde) + nutation::nutation(jde).0.to_degrees()
}

fn position_at(instant_unix_seconds: i64) -> EphemerisPosition {
    let jde = julian_ephemeris_day(instant_unix_seconds);
    let (sun_mean, sun_distance_au) = sun::geocent_ecl_pos(jde);
    let (moon_mean, moon_distance_km) = lunar::geocent_ecl_pos(jde);
    let (nutation_longitude_rad, nutation_obliquity_rad) = nutation::nutation(jde);
    let (sun_fk5_longitude_rad, sun_fk5_latitude_rad) =
        sun::ecl_coords_to_FK5(jde, sun_mean.long, sun_mean.lat);
    let sun_apparent_longitude_rad =
        sun_fk5_longitude_rad + nutation_longitude_rad + aberr::sol_aberr(sun_distance_au);
    let sun_apparent_latitude_rad = sun_fk5_latitude_rad;
    let true_obliquity_rad = ecliptic::mn_oblq_laskar(jde) + nutation_obliquity_rad;
    EphemerisPosition {
        sun_apparent_longitude_deg: wrap_degrees(sun_apparent_longitude_rad.to_degrees()),
        sun_apparent_latitude_rad,
        moon_apparent_longitude_deg: wrap_degrees(
            moon_mean.long.to_degrees() + nutation_longitude_rad.to_degrees(),
        ),
        moon_apparent_latitude_rad: moon_mean.lat,
        moon_distance_km,
        nutation_longitude_rad,
        true_obliquity_rad,
    }
}

fn sidereal_longitude_true(apparent_longitude_deg: f64, jde: f64) -> f64 {
    wrap_degrees(apparent_longitude_deg - lahiri_true_ayanamsa_degrees(jde))
}

fn limb_indices(position: EphemerisPosition, jde: f64) -> LimbIndices {
    let elongation =
        wrap_degrees(position.moon_apparent_longitude_deg - position.sun_apparent_longitude_deg);
    let tithi = (elongation / 12.0).floor() as u8 + 1;
    let sidereal_sun = sidereal_longitude_true(position.sun_apparent_longitude_deg, jde);
    let sidereal_moon = sidereal_longitude_true(position.moon_apparent_longitude_deg, jde);
    let nakshatra = (sidereal_moon / (40.0 / 3.0)).floor() as u8 + 1;
    let yoga_sum = wrap_degrees(sidereal_sun + sidereal_moon);
    let yoga = (yoga_sum / (40.0 / 3.0)).floor() as u8 + 1;
    let karana = (elongation / 6.0).floor() as u8;
    LimbIndices {
        tithi,
        nakshatra,
        yoga,
        karana,
    }
}

fn phase_sector_at(instant_utc_seconds: i64) -> u8 {
    let position = position_at(instant_utc_seconds);
    let elongation =
        wrap_degrees(position.moon_apparent_longitude_deg - position.sun_apparent_longitude_deg);
    (elongation / 90.0).floor() as u8
}

fn limb_values(instant_unix_seconds: i64, position: EphemerisPosition) -> ThirukanithamLimbs {
    let indices = limb_indices(position, julian_ephemeris_day(instant_unix_seconds));
    let tithi = indices.tithi;
    let tithi_name = if tithi == 30 {
        "Amavasya"
    } else {
        DRIK_TITHI_NAMES[usize::from((tithi - 1) % 15)]
    };
    let karana_name = karana_name(indices.karana);
    ThirukanithamLimbs {
        tithi: ThirukanithamLimb {
            index: indices.tithi,
            name: tithi_name,
            paksha: Some(if tithi <= 15 { "shukla" } else { "krishna" }),
        },
        nakshatra: ThirukanithamLimb {
            index: indices.nakshatra,
            name: DRIK_NAKSHATRA_NAMES[usize::from(indices.nakshatra - 1)],
            paksha: None,
        },
        yoga: ThirukanithamLimb {
            index: indices.yoga,
            name: DRIK_YOGA_NAMES[usize::from(indices.yoga - 1)],
            paksha: None,
        },
        karana: ThirukanithamLimb {
            index: indices.karana,
            name: karana_name,
            paksha: None,
        },
    }
}

fn karana_name(index: u8) -> &'static str {
    match index {
        0 => DRIK_KARANA_NAMES[0],
        1..=56 => DRIK_KARANA_NAMES[1 + usize::from((index - 1) % 7)],
        57..=59 => DRIK_KARANA_NAMES[8 + usize::from(index - 57)],
        _ => unreachable!("karana index always lies in 0..=59"),
    }
}

fn vara_for_date(date: GregorianDate) -> &'static str {
    let unix_epoch = GregorianDate::new(1970, 1, 1).expect("Unix epoch is valid");
    let index = (date_difference(unix_epoch, date) + 4).rem_euclid(7) as usize;
    DRIK_WEEKDAYS[index]
}

fn solar_altitude_degrees(instant_unix_seconds: i64, context: ThirukanithamContext) -> f64 {
    let position = position_at(instant_unix_seconds);
    let longitude = position.sun_apparent_longitude_deg.to_radians();
    let latitude = position.sun_apparent_latitude_rad;
    let obliquity = position.true_obliquity_rad;
    let x = latitude.cos() * longitude.cos();
    let y = latitude.cos() * longitude.sin() * obliquity.cos() - latitude.sin() * obliquity.sin();
    let z = latitude.cos() * longitude.sin() * obliquity.sin() + latitude.sin() * obliquity.cos();
    let right_ascension = y.atan2(x);
    let declination = z.clamp(-1.0, 1.0).asin();
    let ut1 = julian_day_utc(instant_unix_seconds)
        + DRIK_UT1_MINUS_UTC_ASSUMED_MILLIS as f64 / 86_400_000.0;
    let mean_sidereal = time::mn_sidr(ut1);
    let apparent_sidereal = mean_sidereal + position.nutation_longitude_rad * obliquity.cos();
    let longitude_rad = context.longitude_microdegrees as f64 / 1_000_000.0 * DEG_TO_RAD;
    let latitude_rad = context.latitude_microdegrees as f64 / 1_000_000.0 * DEG_TO_RAD;
    let hour_angle =
        (apparent_sidereal + longitude_rad - right_ascension + PI).rem_euclid(TAU) - PI;
    let altitude_sine = latitude_rad.sin() * declination.sin()
        + latitude_rad.cos() * declination.cos() * hour_angle.cos();
    altitude_sine.clamp(-1.0, 1.0).asin().to_degrees()
}

fn horizon_dip_degrees(elevation_meters: i64) -> f64 {
    let radius = DRIK_EARTH_RADIUS_METERS as f64;
    let height = elevation_meters as f64;
    if height >= 0.0 {
        (radius / (radius + height))
            .clamp(-1.0, 1.0)
            .acos()
            .to_degrees()
    } else {
        -(-2.0 * height / radius).sqrt().to_degrees()
    }
}

fn moonrise_margin_degrees(instant_unix_seconds: i64, context: ThirukanithamContext) -> f64 {
    let position = position_at(instant_unix_seconds);
    let longitude = position.moon_apparent_longitude_deg.to_radians();
    let latitude = position.moon_apparent_latitude_rad;
    let obliquity = position.true_obliquity_rad;
    let x = latitude.cos() * longitude.cos();
    let y = latitude.cos() * longitude.sin() * obliquity.cos() - latitude.sin() * obliquity.sin();
    let z = latitude.cos() * longitude.sin() * obliquity.sin() + latitude.sin() * obliquity.cos();
    let right_ascension = y.atan2(x);
    let declination = z.clamp(-1.0, 1.0).asin();
    let ut1 = julian_day_utc(instant_unix_seconds)
        + DRIK_UT1_MINUS_UTC_ASSUMED_MILLIS as f64 / 86_400_000.0;
    let mean_sidereal = time::mn_sidr(ut1);
    let apparent_sidereal = mean_sidereal + position.nutation_longitude_rad * obliquity.cos();
    let longitude_rad = context.longitude_microdegrees as f64 / 1_000_000.0 * DEG_TO_RAD;
    let latitude_rad = context.latitude_microdegrees as f64 / 1_000_000.0 * DEG_TO_RAD;
    let hour_angle =
        (apparent_sidereal + longitude_rad - right_ascension + PI).rem_euclid(TAU) - PI;
    let altitude_sine = latitude_rad.sin() * declination.sin()
        + latitude_rad.cos() * declination.cos() * hour_angle.cos();
    let geocentric_altitude = altitude_sine.clamp(-1.0, 1.0).asin().to_degrees();

    let earth_radius_kilometers = DRIK_EARTH_RADIUS_METERS as f64 / 1_000.0;
    let horizontal_parallax = (earth_radius_kilometers / position.moon_distance_km)
        .clamp(-1.0, 1.0)
        .asin();
    let lunar_semidiameter = lunar::semidiameter(position.moon_distance_km);
    let standard_refraction_degrees = DRIK_REFRACTION_ARCMINUTES as f64 / 60.0;
    let threshold = horizontal_parallax.to_degrees()
        - standard_refraction_degrees
        - lunar_semidiameter.to_degrees()
        - horizon_dip_degrees(context.elevation_meters);
    geocentric_altitude - threshold
}

fn moonrise_for_date(date: GregorianDate, context: ThirukanithamContext) -> Result<i64, String> {
    let start = local_midnight_unix(date, context)?;
    let end = start + SECONDS_PER_DAY;
    let margin = |instant| moonrise_margin_degrees(instant, context);
    let step = (DRIK_ROOT_SCAN_STEP_SECONDS / 4).max(60);
    let mut cursor = start;
    let mut previous = margin(cursor);
    while cursor < end - 1 {
        let next = (cursor + step).min(end - 1);
        let current = margin(next);
        if previous < 0.0 && current >= 0.0 {
            return Ok(bisect_predicate(cursor, next, |candidate| {
                margin(candidate) >= 0.0
            }));
        }
        cursor = next;
        previous = current;
    }
    Err("lunar event unavailable".into())
}

fn solar_events_for_date(
    date: GregorianDate,
    context: ThirukanithamContext,
) -> Result<(i64, i64), String> {
    let start = local_midnight_unix(date, context)?;
    let end = start + SECONDS_PER_DAY;
    let target_altitude = DRIK_SUNRISE_CENTER_ALTITUDE_ARCMINUTES as f64 / 60.0
        - horizon_dip_degrees(context.elevation_meters);
    let altitude = |instant| solar_altitude_degrees(instant, context) - target_altitude;
    let step = (DRIK_ROOT_SCAN_STEP_SECONDS / 4).max(60);
    let mut cursor = start;
    let mut previous = altitude(cursor);
    let mut sunrise = None;
    let mut sunset = None;
    while cursor < end - 1 {
        let next = (cursor + step).min(end - 1);
        let current = altitude(next);
        if previous < 0.0 && current >= 0.0 && sunrise.is_none() {
            sunrise = Some(bisect_predicate(cursor, next, |candidate| {
                altitude(candidate) >= 0.0
            }));
        }
        if previous > 0.0 && current <= 0.0 && sunset.is_none() {
            sunset = Some(bisect_predicate(cursor, next, |candidate| {
                altitude(candidate) <= 0.0
            }));
        }
        cursor = next;
        previous = current;
    }
    match (sunrise, sunset) {
        (Some(sunrise), Some(sunset)) if sunrise < sunset => Ok((sunrise, sunset)),
        _ => Err("solar event unavailable".into()),
    }
}

pub(crate) fn thirukanitham_aparahna_tithi_dates(
    gregorian_year: i64,
    month: Option<u8>,
    tithi_index: u8,
    context: ThirukanithamContext,
) -> Result<Vec<GregorianDate>, String> {
    if !(1..=30).contains(&tithi_index) {
        return Err("invalid calendar input".into());
    }
    ensure_public_date(GregorianDate::new(gregorian_year, 1, 1)?)?;
    let (query_start, query_end) = observance_query_range(gregorian_year, month)?;
    let scan_start_date = add_gregorian_date(query_start, "days", -2, "reject")
        .map_err(|_| "outside supported calendar coverage")?;
    let scan_end_date = add_gregorian_date(query_end, "days", 2, "reject")
        .map_err(|_| "outside supported calendar coverage")?;
    let scan_start = local_midnight_unix(scan_start_date, context)?;
    let scan_end = local_midnight_unix(scan_end_date, context)?;
    let tithi_transitions = limb_transitions(scan_start, scan_end, context)?
        .into_iter()
        .filter(|transition| transition.limb == "tithi")
        .collect::<Vec<_>>();
    let mut selected_dates = BTreeSet::new();

    for (index, transition) in tithi_transitions.iter().enumerate() {
        if transition.to_index != tithi_index {
            continue;
        }
        let Some(next_transition) = tithi_transitions.get(index + 1) else {
            continue;
        };
        let tithi_start = transition.instant_unix_seconds;
        let tithi_end = next_transition.instant_unix_seconds;
        if tithi_end <= tithi_start {
            continue;
        }
        let first_date = date_from_unix_seconds(tithi_start + context.utc_offset_seconds)?;
        let last_date = date_from_unix_seconds(tithi_end - 1 + context.utc_offset_seconds)?;
        let mut aparahna_dates = Vec::new();
        let mut sunrise_dates = Vec::new();

        for day_offset in 0..=date_difference(first_date, last_date) {
            let date = add_gregorian_date(first_date, "days", day_offset, "reject")
                .map_err(|_| "outside supported calendar coverage")?;
            let (sunrise, sunset) = solar_events_for_date(date, context)?;
            let daylight = sunset - sunrise;
            if daylight <= 0 {
                return Err("solar event unavailable".into());
            }
            let aparahna_start = sunrise + daylight * 3 / 5;
            let aparahna_end = sunrise + daylight * 4 / 5;
            if half_open_intervals_intersect(tithi_start, tithi_end, aparahna_start, aparahna_end) {
                aparahna_dates.push(date);
            }
            if half_open_interval_contains(tithi_start, tithi_end, sunrise) {
                sunrise_dates.push(date);
            }
        }

        if let Some(date) = select_aparahna_then_sunrise(&aparahna_dates, &sunrise_dates) {
            if date.year() == gregorian_year {
                selected_dates.insert((date.year(), date.month(), date.day()));
            }
        }
    }

    selected_dates
        .into_iter()
        .map(|(year, month, day)| GregorianDate::new(year, i64::from(month), i64::from(day)))
        .collect()
}

pub(crate) fn thirukanitham_sri_vaishnava_ekadashi_dates(
    gregorian_year: i64,
    month: Option<u8>,
    context: ThirukanithamContext,
) -> Result<Vec<(GregorianDate, u8)>, String> {
    ensure_public_date(GregorianDate::new(gregorian_year, 1, 1)?)?;
    if month.is_some_and(|month| !(1..=12).contains(&month)) {
        return Err("invalid calendar input".into());
    }
    let (query_start, query_end) = observance_query_range(gregorian_year, month)?;
    let scan_start_date = add_gregorian_date(query_start, "days", -2, "reject")
        .map_err(|_| "outside supported calendar coverage")?;
    let scan_end_date = add_gregorian_date(query_end, "days", 2, "reject")
        .map_err(|_| "outside supported calendar coverage")?;
    let scan_start = local_midnight_unix(scan_start_date, context)?;
    let scan_end = local_midnight_unix(scan_end_date, context)?;
    let tithi_transitions = limb_transitions(scan_start, scan_end, context)?
        .into_iter()
        .filter(|transition| transition.limb == "tithi")
        .collect::<Vec<_>>();
    let mut selected_dates = BTreeSet::new();

    for (index, transition) in tithi_transitions.iter().enumerate() {
        let tithi_index = transition.to_index;
        if !matches!(tithi_index, 11 | 26) {
            continue;
        }
        let Some(next_transition) = tithi_transitions.get(index + 1) else {
            continue;
        };
        let tithi_start = transition.instant_unix_seconds;
        let tithi_end = next_transition.instant_unix_seconds;
        if tithi_end <= tithi_start {
            continue;
        }
        let first_date = date_from_unix_seconds(tithi_start + context.utc_offset_seconds)?;
        let last_date = date_from_unix_seconds(tithi_end - 1 + context.utc_offset_seconds)?;
        let mut arunodaya_dates = Vec::new();
        let mut sunrise_dates = Vec::new();

        for day_offset in 0..=date_difference(first_date, last_date) {
            let date = add_gregorian_date(first_date, "days", day_offset, "reject")
                .map_err(|_| "outside supported calendar coverage")?;
            let (sunrise, _) = solar_events_for_date(date, context)?;
            let arunodaya = sunrise - 4 * 24 * 60;
            if half_open_interval_contains(tithi_start, tithi_end, arunodaya) {
                arunodaya_dates.push(date);
            }
            if half_open_interval_contains(tithi_start, tithi_end, sunrise) {
                sunrise_dates.push(date);
            }
        }

        let selected = select_sri_vaishnava_ekadashi_day(&arunodaya_dates, &sunrise_dates)?;
        if let Some(date) = selected {
            selected_dates.insert((date.year(), date.month(), date.day(), tithi_index));
        }
    }

    selected_dates
        .into_iter()
        .map(|(year, month, day, tithi_index)| {
            Ok((
                GregorianDate::new(year, i64::from(month), i64::from(day))?,
                tithi_index,
            ))
        })
        .collect()
}

pub(crate) fn thirukanitham_sankatahara_chaturthi_dates(
    gregorian_year: i64,
    month: Option<u8>,
    context: ThirukanithamContext,
) -> Result<Vec<GregorianDate>, String> {
    ensure_public_date(GregorianDate::new(gregorian_year, 1, 1)?)?;
    if month.is_some_and(|month| !(1..=12).contains(&month)) {
        return Err("invalid calendar input".into());
    }
    let (query_start, query_end) = observance_query_range(gregorian_year, month)?;
    let scan_start_date = add_gregorian_date(query_start, "days", -2, "reject")
        .map_err(|_| "outside supported calendar coverage")?;
    let scan_end_date = add_gregorian_date(query_end, "days", 2, "reject")
        .map_err(|_| "outside supported calendar coverage")?;
    let scan_start = local_midnight_unix(scan_start_date, context)?;
    let scan_end = local_midnight_unix(scan_end_date, context)?;
    let tithi_transitions = limb_transitions(scan_start, scan_end, context)?
        .into_iter()
        .filter(|transition| transition.limb == "tithi")
        .collect::<Vec<_>>();
    let mut selected_dates = BTreeSet::new();

    for (index, transition) in tithi_transitions.iter().enumerate() {
        if transition.to_index != 19 {
            continue;
        }
        let Some(next_transition) = tithi_transitions.get(index + 1) else {
            continue;
        };
        let tithi_start = transition.instant_unix_seconds;
        let tithi_end = next_transition.instant_unix_seconds;
        if tithi_end <= tithi_start {
            continue;
        }
        let first_date = date_from_unix_seconds(tithi_start + context.utc_offset_seconds)?;
        let last_date = date_from_unix_seconds(tithi_end - 1 + context.utc_offset_seconds)?;
        let second_date = add_gregorian_date(first_date, "days", 1, "reject")
            .map_err(|_| "outside supported calendar coverage")?;
        let mut moonrise_dates = Vec::new();
        let mut date = first_date;
        while date_difference(date, last_date) >= 0 {
            let moonrise = moonrise_for_date(date, context)?;
            if half_open_interval_contains(tithi_start, tithi_end, moonrise) {
                moonrise_dates.push(date);
            }
            date = add_gregorian_date(date, "days", 1, "reject")
                .map_err(|_| "outside supported calendar coverage")?;
        }

        let selected = select_sankatahara_date(first_date, second_date, &moonrise_dates)?;
        if selected.year() == gregorian_year
            && month.is_none_or(|month| selected.month() == u32::from(month))
        {
            selected_dates.insert((selected.year(), selected.month(), selected.day()));
        }
    }

    selected_dates
        .into_iter()
        .map(|(year, month, day)| GregorianDate::new(year, i64::from(month), i64::from(day)))
        .collect()
}

pub(crate) fn thirukanitham_krishna_jayanthi_dates(
    gregorian_year: i64,
    query_month: Option<u8>,
    tithi_index: u8,
    nakshatra_index: u8,
    context: ThirukanithamContext,
) -> Result<Vec<GregorianDate>, String> {
    ensure_public_date(GregorianDate::new(gregorian_year, 1, 1)?)?;
    if tithi_index != 23
        || nakshatra_index != 4
        || query_month.is_some_and(|month| !(1..=12).contains(&month))
    {
        return Err("invalid calendar input".into());
    }

    let (query_start, query_end) = observance_query_range(gregorian_year, query_month)?;
    let scan_start_date = add_gregorian_date(query_start, "days", -2, "reject")
        .map_err(|_| "outside supported calendar coverage")?;
    let scan_end_date = add_gregorian_date(query_end, "days", 2, "reject")
        .map_err(|_| "outside supported calendar coverage")?;
    let transitions = limb_transitions(
        local_midnight_unix(scan_start_date, context)?,
        local_midnight_unix(scan_end_date, context)?,
        context,
    )?
    .into_iter()
    .filter(|transition| transition.limb == "tithi")
    .collect::<Vec<_>>();
    let mut selected_dates = BTreeSet::new();

    for (index, transition) in transitions.iter().enumerate() {
        if transition.to_index != tithi_index {
            continue;
        }
        let Some(next_transition) = transitions.get(index + 1) else {
            continue;
        };
        let tithi_start = transition.instant_unix_seconds;
        let tithi_end = next_transition.instant_unix_seconds;
        if tithi_end <= tithi_start {
            continue;
        }

        let first_night = date_from_unix_seconds(tithi_start + context.utc_offset_seconds)?;
        let second_night = add_gregorian_date(first_night, "days", 1, "reject")
            .map_err(|_| "outside supported calendar coverage")?;
        let candidate_nights = [first_night, second_night];
        let mut ashtami_nishita_dates = Vec::new();
        let mut jayanti_nishita_dates = Vec::new();

        for night_date in candidate_nights {
            let (_, sunset) = solar_events_for_date(night_date, context)?;
            let next_date = add_gregorian_date(night_date, "days", 1, "reject")
                .map_err(|_| "outside supported calendar coverage")?;
            let (next_sunrise, _) = solar_events_for_date(next_date, context)?;
            let (nishita_start, nishita_end) = eighth_night_muhurta(sunset, next_sunrise)?;
            if limb_intersects(nishita_start, nishita_end, Some(tithi_index), None, context)? {
                ashtami_nishita_dates.push(night_date);
                if limb_intersects(
                    nishita_start,
                    nishita_end,
                    Some(tithi_index),
                    Some(nakshatra_index),
                    context,
                )? {
                    jayanti_nishita_dates.push(night_date);
                }
            }
        }

        let selected = select_smarta_janmashtami_date(
            first_night,
            &ashtami_nishita_dates,
            &jayanti_nishita_dates,
        )?;
        if selected.year() == gregorian_year
            && query_month.is_none_or(|month| selected.month() == u32::from(month))
        {
            selected_dates.insert((selected.year(), selected.month(), selected.day()));
        }
    }

    selected_dates
        .into_iter()
        .map(|(year, month, day)| GregorianDate::new(year, i64::from(month), i64::from(day)))
        .collect()
}

pub(crate) fn thirukanitham_nava_pradosham_dates(
    gregorian_year: i64,
    month: Option<u8>,
    context: ThirukanithamContext,
) -> Result<Vec<(GregorianDate, u8)>, String> {
    ensure_public_date(GregorianDate::new(gregorian_year, 1, 1)?)?;
    if month.is_some_and(|month| !(1..=12).contains(&month)) {
        return Err("invalid calendar input".into());
    }
    let (query_start, query_end) = observance_query_range(gregorian_year, month)?;
    let scan_start_date = add_gregorian_date(query_start, "days", -2, "reject")
        .map_err(|_| "outside supported calendar coverage")?;
    let scan_end_date = add_gregorian_date(query_end, "days", 2, "reject")
        .map_err(|_| "outside supported calendar coverage")?;
    let scan_start = local_midnight_unix(scan_start_date, context)?;
    let scan_end = local_midnight_unix(scan_end_date, context)?;
    let tithi_transitions = limb_transitions(scan_start, scan_end, context)?
        .into_iter()
        .filter(|transition| transition.limb == "tithi")
        .collect::<Vec<_>>();
    let mut selected_dates = BTreeSet::new();

    for (index, transition) in tithi_transitions.iter().enumerate() {
        let tithi_index = transition.to_index;
        if !matches!(tithi_index, 13 | 28) {
            continue;
        }
        let Some(next_transition) = tithi_transitions.get(index + 1) else {
            continue;
        };
        let tithi_start = transition.instant_unix_seconds;
        let tithi_end = next_transition.instant_unix_seconds;
        if tithi_end <= tithi_start {
            continue;
        }
        let first_date = date_from_unix_seconds(tithi_start + context.utc_offset_seconds)?;
        let last_date = date_from_unix_seconds(tithi_end - 1 + context.utc_offset_seconds)?;
        let mut pradosha_dates = Vec::new();

        for day_offset in 0..=date_difference(first_date, last_date) {
            let date = add_gregorian_date(first_date, "days", day_offset, "reject")
                .map_err(|_| "outside supported calendar coverage")?;
            let (_, sunset) = solar_events_for_date(date, context)?;
            let pradosha_end = sunset
                .checked_add(90 * 60)
                .ok_or("outside supported calendar coverage")?;
            if half_open_intervals_intersect(tithi_start, tithi_end, sunset, pradosha_end) {
                pradosha_dates.push(date);
            }
        }

        if let Some(date) = select_nava_pradosha_day(&pradosha_dates) {
            if date.year() == gregorian_year {
                selected_dates.insert((date.year(), date.month(), date.day(), tithi_index));
            }
        }
    }

    selected_dates
        .into_iter()
        .map(|(year, month, day, tithi_index)| {
            Ok((
                GregorianDate::new(year, i64::from(month), i64::from(day))?,
                tithi_index,
            ))
        })
        .collect()
}

pub(crate) fn thirukanitham_nakshatra_observance_dates(
    gregorian_year: i64,
    month: Option<u8>,
    tamil_month: u8,
    tithi_index: u8,
    nakshatra_index: u8,
    window: &str,
    context: ThirukanithamContext,
) -> Result<Vec<(GregorianDate, Option<u8>)>, String> {
    ensure_public_date(GregorianDate::new(gregorian_year, 1, 1)?)?;
    if !(1..=12).contains(&tamil_month)
        || !(1..=27).contains(&nakshatra_index)
        || tithi_index > 30
        || month.is_some_and(|month| !(1..=12).contains(&month))
        || !matches!(
            window,
            "sunrise"
                | "arunodaya"
                | "night"
                | "sunset"
                | "thai_purnima_pushya"
                | "panguni_purnima_uthiram"
                | "sunrise_nearest_purnima"
        )
        || (matches!(
            window,
            "thai_purnima_pushya" | "panguni_purnima_uthiram" | "sunrise_nearest_purnima"
        ) && tithi_index != 15)
        || (!matches!(
            window,
            "thai_purnima_pushya" | "panguni_purnima_uthiram" | "sunrise_nearest_purnima"
        ) && tithi_index != 0)
    {
        return Err("invalid calendar input".into());
    }

    let (query_start, query_end) = observance_query_range(gregorian_year, month)?;
    let mut selected_dates = BTreeSet::new();
    for solar_year in (query_start.year() - 1)..=query_start.year() {
        if !(DRIK_SOLAR_YEAR_START..=DRIK_SOLAR_YEAR_END).contains(&solar_year) {
            continue;
        }
        if (tamil_month <= 8 && solar_year != query_start.year())
            || (tamil_month >= 10 && solar_year != query_start.year() - 1)
        {
            continue;
        }
        let solar_month = thirukanitham_month_info(solar_year, i64::from(tamil_month), context)?;
        let last_date = add_gregorian_date(solar_month.end_date_exclusive, "days", -1, "reject")
            .map_err(|_| "outside supported calendar coverage")?;
        if date_difference(last_date, query_start) > 0
            || date_difference(query_end, solar_month.start_date) >= 0
        {
            continue;
        }

        let mut candidates = Vec::new();
        let mut thai_purnima_pushya_days = Vec::new();
        let mut thai_purnima_days = Vec::new();
        let mut panguni_purnima_uthiram_days = Vec::new();
        let mut date = solar_month.start_date;
        while date_difference(date, last_date) >= 0 {
            let (sunrise, sunset) = solar_events_for_date(date, context)?;
            if matches!(
                window,
                "thai_purnima_pushya" | "panguni_purnima_uthiram" | "sunrise_nearest_purnima"
            ) && limb_intersects(sunrise, sunset, Some(tithi_index), None, context)?
            {
                thai_purnima_days.push(date);
            }
            if window == "panguni_purnima_uthiram"
                && limb_intersects(
                    sunrise,
                    sunset,
                    Some(tithi_index),
                    Some(nakshatra_index),
                    context,
                )?
            {
                panguni_purnima_uthiram_days.push(date);
            }
            let target = match window {
                "sunrise" => {
                    limb_indices(position_at(sunrise), julian_ephemeris_day(sunrise)).nakshatra
                        == nakshatra_index
                }
                "arunodaya" => {
                    let arunodaya = sunrise - 4 * 24 * 60;
                    limb_indices(position_at(arunodaya), julian_ephemeris_day(arunodaya)).nakshatra
                        == nakshatra_index
                }
                "night" => {
                    let next_date = add_gregorian_date(date, "days", 1, "reject")
                        .map_err(|_| "outside supported calendar coverage")?;
                    let (next_sunrise, _) = solar_events_for_date(next_date, context)?;
                    nakshatra_intersects(sunset, next_sunrise, nakshatra_index, context)?
                }
                "sunset" => {
                    let next_date = add_gregorian_date(date, "days", 1, "reject")
                        .map_err(|_| "outside supported calendar coverage")?;
                    let (next_sunrise, _) = solar_events_for_date(next_date, context)?;
                    let pradosha_end = sunset + (next_sunrise - sunset) / 5;
                    nakshatra_intersects(sunset, pradosha_end, nakshatra_index, context)?
                }
                "thai_purnima_pushya" => {
                    let pushya_in_day =
                        limb_intersects(sunrise, sunset, None, Some(nakshatra_index), context)?;
                    if pushya_in_day
                        && limb_intersects(
                            sunrise,
                            sunset,
                            Some(tithi_index),
                            Some(nakshatra_index),
                            context,
                        )?
                    {
                        thai_purnima_pushya_days.push(date);
                    }
                    limb_indices(position_at(sunrise), julian_ephemeris_day(sunrise)).nakshatra
                        == nakshatra_index
                }
                "sunrise_nearest_purnima" => {
                    limb_indices(position_at(sunrise), julian_ephemeris_day(sunrise)).nakshatra
                        == nakshatra_index
                }
                "panguni_purnima_uthiram" => {
                    limb_indices(position_at(sunrise), julian_ephemeris_day(sunrise)).nakshatra
                        == nakshatra_index
                }
                _ => unreachable!("window is validated above"),
            };
            if target {
                candidates.push(date);
            }
            date = add_gregorian_date(date, "days", 1, "reject")
                .map_err(|_| "outside supported calendar coverage")?;
        }

        let (selected, selected_tithi) = if matches!(
            window,
            "thai_purnima_pushya" | "sunrise_nearest_purnima" | "panguni_purnima_uthiram"
        ) {
            let preferred = match window {
                "thai_purnima_pushya" if !thai_purnima_pushya_days.is_empty() => {
                    &thai_purnima_pushya_days
                }
                "panguni_purnima_uthiram" if !panguni_purnima_uthiram_days.is_empty() => {
                    &panguni_purnima_uthiram_days
                }
                _ => &candidates,
            };
            if window == "panguni_purnima_uthiram" {
                if !panguni_purnima_uthiram_days.is_empty() {
                    match preferred.as_slice() {
                        [only] => (*only, Some(15)),
                        _ => return Err("unsupported observance nakshatra selection".into()),
                    }
                } else {
                    let nearest = candidates
                        .iter()
                        .map(|candidate| {
                            let distance = thai_purnima_days
                                .iter()
                                .map(|purnima| date_difference(*candidate, *purnima).abs())
                                .min()
                                .ok_or("unsupported observance nakshatra selection")?;
                            Ok((*candidate, distance))
                        })
                        .collect::<Result<Vec<_>, String>>()?;
                    let best_distance = nearest
                        .iter()
                        .map(|(_, distance)| *distance)
                        .min()
                        .ok_or("unsupported observance nakshatra selection")?;
                    let nearest_days = nearest
                        .iter()
                        .filter(|(_, distance)| *distance == best_distance)
                        .map(|(candidate, _)| *candidate)
                        .collect::<Vec<_>>();
                    match nearest_days.as_slice() {
                        [only] => (*only, None),
                        _ => return Err("unsupported observance nakshatra selection".into()),
                    }
                }
            } else {
                let nearest = preferred
                    .iter()
                    .map(|candidate| {
                        let distance = thai_purnima_days
                            .iter()
                            .map(|purnima| date_difference(*candidate, *purnima).abs())
                            .min()
                            .ok_or("unsupported observance nakshatra selection")?;
                        Ok((*candidate, distance))
                    })
                    .collect::<Result<Vec<_>, String>>()?;
                let best_distance = nearest
                    .iter()
                    .map(|(_, distance)| *distance)
                    .min()
                    .ok_or("unsupported observance nakshatra selection")?;
                let nearest_days = nearest
                    .iter()
                    .filter(|(_, distance)| *distance == best_distance)
                    .map(|(candidate, _)| *candidate)
                    .collect::<Vec<_>>();
                match nearest_days.as_slice() {
                    [only] => (
                        *only,
                        (window == "thai_purnima_pushya" && !thai_purnima_pushya_days.is_empty())
                            .then_some(tithi_index),
                    ),
                    _ => return Err("unsupported observance nakshatra selection".into()),
                }
            }
        } else {
            match (window, candidates.as_slice()) {
                ("sunset", [first]) => (*first, None),
                ("sunset", [_, later]) => (*later, None),
                (_, [only]) => (*only, None),
                _ => return Err("unsupported observance nakshatra selection".into()),
            }
        };
        if date_difference(query_start, selected) >= 0
            && date_difference(selected, query_end) > 0
            && selected.year() == gregorian_year
        {
            selected_dates.insert((
                selected.year(),
                selected.month(),
                selected.day(),
                selected_tithi,
            ));
        }
    }

    selected_dates
        .into_iter()
        .map(|(year, month, day, tithi)| {
            GregorianDate::new(year, i64::from(month), i64::from(day)).map(|date| (date, tithi))
        })
        .collect()
}

pub(crate) fn thirukanitham_tithi_observance_dates(
    gregorian_year: i64,
    month: Option<u8>,
    tamil_month: u8,
    tithi_index: u8,
    window: &str,
    context: ThirukanithamContext,
) -> Result<Vec<GregorianDate>, String> {
    ensure_public_date(GregorianDate::new(gregorian_year, 1, 1)?)?;
    if !(1..=12).contains(&tamil_month)
        || !(1..=30).contains(&tithi_index)
        || month.is_some_and(|month| !(1..=12).contains(&month))
        || !matches!(
            window,
            "sunrise"
                | "madhyahna_first"
                | "nishita_then_sunset"
                | "brahma_muhurta"
                | "first_third"
        )
    {
        return Err("invalid calendar input".into());
    }

    let (query_start, query_end) = observance_query_range(gregorian_year, month)?;
    let mut selected_dates = BTreeSet::new();
    for solar_year in (query_start.year() - 1)..=query_start.year() {
        if !(DRIK_SOLAR_YEAR_START..=DRIK_SOLAR_YEAR_END).contains(&solar_year) {
            continue;
        }
        if (tamil_month <= 8 && solar_year != query_start.year())
            || (tamil_month >= 10 && solar_year != query_start.year() - 1)
        {
            continue;
        }
        let solar_month = thirukanitham_month_info(solar_year, i64::from(tamil_month), context)?;
        let last_date = add_gregorian_date(solar_month.end_date_exclusive, "days", -1, "reject")
            .map_err(|_| "outside supported calendar coverage")?;
        if date_difference(last_date, query_start) > 0
            || date_difference(query_end, solar_month.start_date) >= 0
        {
            continue;
        }

        let mut sunrise_dates = Vec::new();
        let mut madhyahna_dates = Vec::new();
        let mut nishita_dates = Vec::new();
        let mut sunset_dates = Vec::new();
        let mut brahma_muhurta_dates = Vec::new();
        let mut first_third_dates = Vec::new();
        let mut date = solar_month.start_date;
        while date_difference(date, last_date) >= 0 {
            let (sunrise, sunset) = solar_events_for_date(date, context)?;
            let daylight = sunset - sunrise;
            if daylight <= 0 {
                return Err("solar event unavailable".into());
            }
            match window {
                "sunrise" => {
                    if limb_indices(position_at(sunrise), julian_ephemeris_day(sunrise)).tithi
                        == tithi_index
                    {
                        sunrise_dates.push(date);
                    }
                }
                "madhyahna_first" => {
                    let start = sunrise + daylight * 2 / 5;
                    let end = sunrise + daylight * 3 / 5;
                    if limb_intersects(start, end, Some(tithi_index), None, context)? {
                        madhyahna_dates.push(date);
                    }
                }
                "nishita_then_sunset" => {
                    let next_date = add_gregorian_date(date, "days", 1, "reject")
                        .map_err(|_| "outside supported calendar coverage")?;
                    let (next_sunrise, _) = solar_events_for_date(next_date, context)?;
                    let nishita = sunset + (next_sunrise - sunset) / 2;
                    if limb_indices(position_at(nishita), julian_ephemeris_day(nishita)).tithi
                        == tithi_index
                    {
                        nishita_dates.push(date);
                    }
                    if limb_indices(position_at(sunset), julian_ephemeris_day(sunset)).tithi
                        == tithi_index
                    {
                        sunset_dates.push(date);
                    }
                }
                "brahma_muhurta" => {
                    let start = sunrise - 96 * 60;
                    let end = sunrise - 48 * 60;
                    if limb_intersects(start, end, Some(tithi_index), None, context)? {
                        brahma_muhurta_dates.push(date);
                    }
                }
                "first_third" => {
                    let end = sunrise + daylight / 3;
                    if limb_intersects(sunrise, end, Some(tithi_index), None, context)? {
                        first_third_dates.push(date);
                    }
                }
                _ => unreachable!("window is validated above"),
            }
            date = add_gregorian_date(date, "days", 1, "reject")
                .map_err(|_| "outside supported calendar coverage")?;
        }

        let selected = match window {
            "sunrise" => match sunrise_dates.as_slice() {
                [only] => *only,
                _ => return Err("unsupported observance tithi selection".into()),
            },
            "madhyahna_first" => {
                let local_start = local_midnight_unix(solar_month.start_date, context)?;
                let local_end = local_midnight_unix(solar_month.end_date_exclusive, context)?;
                let starts = limb_transitions(local_start, local_end, context)?
                    .into_iter()
                    .filter(|transition| {
                        transition.limb == "tithi" && transition.to_index == tithi_index
                    })
                    .map(|transition| {
                        date_from_unix_seconds(
                            transition.instant_unix_seconds + context.utc_offset_seconds,
                        )
                    })
                    .filter(|date| {
                        date.as_ref().is_ok_and(|date| {
                            date_difference(solar_month.start_date, *date) >= 0
                                && date_difference(*date, last_date) >= 0
                        })
                    })
                    .collect::<Result<Vec<_>, _>>()?;
                if madhyahna_dates.len() == 1 {
                    madhyahna_dates[0]
                } else {
                    match starts.as_slice() {
                        [only] => *only,
                        _ => return Err("unsupported observance tithi selection".into()),
                    }
                }
            }
            "nishita_then_sunset" => {
                let preferred = if nishita_dates.is_empty() {
                    &sunset_dates
                } else {
                    &nishita_dates
                };
                match preferred.as_slice() {
                    [only] => *only,
                    _ => return Err("unsupported observance tithi selection".into()),
                }
            }
            "brahma_muhurta" => match brahma_muhurta_dates.as_slice() {
                [only] => *only,
                _ => return Err("unsupported observance tithi selection".into()),
            },
            "first_third" => match first_third_dates.as_slice() {
                [only] => *only,
                _ => return Err("unsupported observance tithi selection".into()),
            },
            _ => unreachable!("window is validated above"),
        };

        if date_difference(query_start, selected) >= 0
            && date_difference(selected, query_end) > 0
            && selected.year() == gregorian_year
        {
            selected_dates.insert((selected.year(), selected.month(), selected.day()));
        }
    }

    selected_dates
        .into_iter()
        .map(|(year, month, day)| GregorianDate::new(year, i64::from(month), i64::from(day)))
        .collect()
}

pub(crate) fn thirukanitham_ayudha_puja_date(
    gregorian_year: i64,
    month: Option<u8>,
    context: ThirukanithamContext,
) -> Result<Option<GregorianDate>, String> {
    let navaratri_start = match thirukanitham_tithi_observance_dates(
        gregorian_year,
        None,
        6,
        1,
        "first_third",
        context,
    )?
    .as_slice()
    {
        [only] => *only,
        _ => return Err("unsupported observance tithi selection".into()),
    };
    let mut navami_sunrise_dates = Vec::new();
    for offset in 0..=12 {
        let date = add_gregorian_date(navaratri_start, "days", offset, "reject")
            .map_err(|_| "outside supported calendar coverage")?;
        let (sunrise, _) = solar_events_for_date(date, context)?;
        if limb_indices(position_at(sunrise), julian_ephemeris_day(sunrise)).tithi == 9 {
            navami_sunrise_dates.push(date);
        }
    }
    match navami_sunrise_dates.as_slice() {
        [only]
            if only.year() == gregorian_year
                && month.is_none_or(|month| only.month() == u32::from(month)) =>
        {
            Ok(Some(*only))
        }
        [_] => Ok(None),
        _ => Err("unsupported observance tithi selection".into()),
    }
}

pub(crate) fn thirukanitham_vijayadashami_date(
    gregorian_year: i64,
    month: Option<u8>,
    context: ThirukanithamContext,
) -> Result<Option<GregorianDate>, String> {
    ensure_public_date(GregorianDate::new(gregorian_year, 1, 1)?)?;
    if month.is_some_and(|month| !(1..=12).contains(&month)) {
        return Err("invalid calendar input".into());
    }
    let navaratri_start = match thirukanitham_tithi_observance_dates(
        gregorian_year,
        None,
        6,
        1,
        "first_third",
        context,
    )?
    .as_slice()
    {
        [only] => *only,
        _ => return Err("unsupported observance tithi selection".into()),
    };

    let mut candidates = Vec::new();
    for offset in 0..=12 {
        let date = add_gregorian_date(navaratri_start, "days", offset, "reject")
            .map_err(|_| "outside supported calendar coverage")?;
        let (sunrise, sunset) = solar_events_for_date(date, context)?;
        let next_date = add_gregorian_date(date, "days", 1, "reject")
            .map_err(|_| "outside supported calendar coverage")?;
        let (next_sunrise, _) = solar_events_for_date(next_date, context)?;
        let daylight = sunset - sunrise;
        if daylight <= 0 {
            return Err("solar event unavailable".into());
        }
        if limb_intersects(sunrise, next_sunrise, Some(10), None, context)? {
            let aparahna_start = sunrise + daylight * 3 / 5;
            let aparahna_end = sunrise + daylight * 4 / 5;
            let overlap = tithi_overlap_seconds(aparahna_start, aparahna_end, 10, context)?;
            candidates.push((date, overlap, aparahna_end - aparahna_start));
        }
    }
    if candidates.is_empty() {
        return Ok(None);
    }
    candidates.sort_by_key(|(date, _, _)| (date.year(), date.month(), date.day()));
    if candidates.len() > 2 {
        return Err("unsupported observance tithi selection".into());
    }

    let full = candidates
        .iter()
        .filter(|(_, overlap, duration)| overlap == duration)
        .map(|(date, _, _)| *date)
        .collect::<Vec<_>>();
    let mut selected = if !full.is_empty() {
        full[0]
    } else {
        let touched = candidates
            .iter()
            .filter(|(_, overlap, _)| *overlap > 0)
            .collect::<Vec<_>>();
        match touched.as_slice() {
            [only] => only.0,
            [first, second] => {
                let difference = (first.1 - second.1).abs();
                if difference < 24 * 60 || first.1 >= second.1 {
                    first.0
                } else {
                    second.0
                }
            }
            [] => candidates[0].0,
            _ => return Err("unsupported observance tithi selection".into()),
        }
    };

    let first_day = candidates[0].0;
    if selected == first_day && candidates.len() == 2 {
        let next_day = candidates[1].0;
        let (next_sunrise, _) = solar_events_for_date(next_day, context)?;
        let three_muhurtas_after_sunrise = next_sunrise + 3 * 48 * 60;
        let tithi_continues = limb_indices(
            position_at(three_muhurtas_after_sunrise - 1),
            julian_ephemeris_day(three_muhurtas_after_sunrise - 1),
        )
        .tithi
            == 10;
        if tithi_continues {
            let (first_sunrise, first_sunset) = solar_events_for_date(first_day, context)?;
            let (next_sunrise, next_sunset) = solar_events_for_date(next_day, context)?;
            let first_ap_start = first_sunrise + (first_sunset - first_sunrise) * 3 / 5;
            let first_ap_end = first_sunrise + (first_sunset - first_sunrise) * 4 / 5;
            let next_ap_start = next_sunrise + (next_sunset - next_sunrise) * 3 / 5;
            let next_ap_end = next_sunrise + (next_sunset - next_sunrise) * 4 / 5;
            let first_has_shravana =
                limb_intersects(first_ap_start, first_ap_end, None, Some(21), context)?;
            let next_has_shravana =
                limb_intersects(next_ap_start, next_ap_end, None, Some(21), context)?;
            if next_has_shravana && !first_has_shravana {
                selected = next_day;
            }
        }
    }

    if selected.year() == gregorian_year
        && month.is_none_or(|month| selected.month() == u32::from(month))
    {
        Ok(Some(selected))
    } else {
        Ok(None)
    }
}

fn tithi_overlap_seconds(
    start: i64,
    end: i64,
    tithi_index: u8,
    context: ThirukanithamContext,
) -> Result<i64, String> {
    if end <= start {
        return Ok(0);
    }
    let mut current_tithi = limb_indices(position_at(start), julian_ephemeris_day(start)).tithi;
    let mut cursor = start;
    let mut overlap = 0_i64;
    for transition in limb_transitions(start, end, context)?
        .into_iter()
        .filter(|transition| transition.limb == "tithi")
    {
        let instant = transition.instant_unix_seconds.clamp(start, end);
        if current_tithi == tithi_index {
            overlap += instant - cursor;
        }
        current_tithi = transition.to_index;
        cursor = instant;
    }
    if current_tithi == tithi_index {
        overlap += end - cursor;
    }
    Ok(overlap)
}

fn limb_intersects(
    start: i64,
    end: i64,
    tithi_index: Option<u8>,
    nakshatra_index: Option<u8>,
    context: ThirukanithamContext,
) -> Result<bool, String> {
    if start >= end || (tithi_index.is_none() && nakshatra_index.is_none()) {
        return Err("solar event unavailable".into());
    }
    let mut boundaries = vec![start, end];
    boundaries.extend(
        limb_transitions(start, end, context)?
            .into_iter()
            .filter(|transition| {
                transition.instant_unix_seconds > start
                    && transition.instant_unix_seconds < end
                    && (transition.limb == "tithi" && tithi_index.is_some()
                        || transition.limb == "nakshatra" && nakshatra_index.is_some())
            })
            .map(|transition| transition.instant_unix_seconds),
    );
    boundaries.sort_unstable();
    boundaries.dedup();
    for interval in boundaries.windows(2) {
        if interval[0] >= interval[1] {
            continue;
        }
        let indices = limb_indices(position_at(interval[0]), julian_ephemeris_day(interval[0]));
        if tithi_index.is_none_or(|index| indices.tithi == index)
            && nakshatra_index.is_none_or(|index| indices.nakshatra == index)
        {
            return Ok(true);
        }
    }
    Ok(false)
}

fn nakshatra_intersects(
    start: i64,
    end: i64,
    nakshatra_index: u8,
    context: ThirukanithamContext,
) -> Result<bool, String> {
    if start >= end {
        return Err("solar event unavailable".into());
    }
    if limb_indices(position_at(start), julian_ephemeris_day(start)).nakshatra == nakshatra_index {
        return Ok(true);
    }
    Ok(limb_transitions(start, end, context)?
        .into_iter()
        .any(|transition| {
            transition.limb == "nakshatra"
                && transition.to_index == nakshatra_index
                && transition.instant_unix_seconds < end
        }))
}

fn select_sri_vaishnava_ekadashi_day(
    arunodaya_dates: &[GregorianDate],
    sunrise_dates: &[GregorianDate],
) -> Result<Option<GregorianDate>, String> {
    match arunodaya_dates {
        [date] => Ok(Some(*date)),
        [_, next_arunodaya_date] => add_gregorian_date(*next_arunodaya_date, "days", 1, "reject")
            .map(Some)
            .map_err(|_| "outside supported calendar coverage".into()),
        [] => sunrise_dates
            .last()
            .copied()
            .map(|date| add_gregorian_date(date, "days", 1, "reject"))
            .transpose()
            .map_err(|_| "outside supported calendar coverage".into()),
        _ => Err("outside supported calendar coverage".into()),
    }
}

fn select_nava_pradosha_day(pradosha_dates: &[GregorianDate]) -> Option<GregorianDate> {
    pradosha_dates.last().copied()
}

fn observance_query_range(
    gregorian_year: i64,
    month: Option<u8>,
) -> Result<(GregorianDate, GregorianDate), String> {
    let (query_start, query_end) = match month {
        Some(month) if (1..=12).contains(&month) => {
            let query_start = GregorianDate::new(gregorian_year, i64::from(month), 1)?;
            let (next_year, next_month) = if month == 12 {
                (gregorian_year + 1, 1)
            } else {
                (gregorian_year, i64::from(month) + 1)
            };
            (query_start, GregorianDate::new(next_year, next_month, 1)?)
        }
        Some(_) => return Err("invalid calendar input".into()),
        None => (
            GregorianDate::new(gregorian_year, 1, 1)?,
            GregorianDate::new(gregorian_year + 1, 1, 1)?,
        ),
    };
    Ok((query_start, query_end))
}

fn half_open_intervals_intersect(start: i64, end: i64, other_start: i64, other_end: i64) -> bool {
    start < other_end && end > other_start
}

fn half_open_interval_contains(start: i64, end: i64, instant: i64) -> bool {
    start <= instant && instant < end
}

fn select_aparahna_then_sunrise(
    aparahna_dates: &[GregorianDate],
    sunrise_dates: &[GregorianDate],
) -> Option<GregorianDate> {
    aparahna_dates
        .last()
        .or_else(|| sunrise_dates.last())
        .copied()
}

fn select_sankatahara_date(
    first_tithi_date: GregorianDate,
    second_tithi_date: GregorianDate,
    moonrise_dates: &[GregorianDate],
) -> Result<GregorianDate, String> {
    if date_difference(first_tithi_date, second_tithi_date) != 1 {
        return Err("unsupported Sankatahara Chaturthi moonrise selection".into());
    }
    match moonrise_dates {
        [] => Ok(second_tithi_date),
        [only] => Ok(*only),
        [first, second] if date_difference(*first, *second) == 1 => Ok(*first),
        _ => Err("unsupported Sankatahara Chaturthi moonrise selection".into()),
    }
}

fn select_smarta_janmashtami_date(
    first_night: GregorianDate,
    ashtami_nishita_dates: &[GregorianDate],
    jayanti_nishita_dates: &[GregorianDate],
) -> Result<GregorianDate, String> {
    let second_night = add_gregorian_date(first_night, "days", 1, "reject")
        .map_err(|_| "outside supported calendar coverage")?;
    if jayanti_nishita_dates
        .iter()
        .any(|date| !ashtami_nishita_dates.contains(date))
    {
        return Err("unsupported Krishna Jayanthi Nishita selection".into());
    }
    match ashtami_nishita_dates {
        [] => Ok(second_night),
        [only] if *only == first_night || *only == second_night => Ok(*only),
        [first, second] if *first == first_night && *second == second_night => {
            let first_is_jayanti = jayanti_nishita_dates.contains(&first_night);
            let second_is_jayanti = jayanti_nishita_dates.contains(&second_night);
            if first_is_jayanti ^ second_is_jayanti {
                Ok(if first_is_jayanti {
                    first_night
                } else {
                    second_night
                })
            } else {
                Ok(second_night)
            }
        }
        _ => Err("unsupported Krishna Jayanthi Nishita selection".into()),
    }
}

fn eighth_night_muhurta(sunset: i64, next_sunrise: i64) -> Result<(i64, i64), String> {
    let night_seconds = next_sunrise - sunset;
    if night_seconds <= 0 {
        return Err("solar event unavailable".into());
    }
    Ok((
        sunset + night_seconds * 7 / 15,
        sunset + night_seconds * 8 / 15,
    ))
}

fn bisect_predicate(
    mut false_side: i64,
    mut true_side: i64,
    mut after: impl FnMut(i64) -> bool,
) -> i64 {
    while true_side - false_side > 1 {
        let middle = false_side + (true_side - false_side) / 2;
        if after(middle) {
            true_side = middle;
        } else {
            false_side = middle;
        }
    }
    true_side
}

fn rounded_local_minute(
    instant_utc_seconds: i64,
    date: GregorianDate,
    context: ThirukanithamContext,
) -> Result<i64, String> {
    let local_seconds = instant_utc_seconds
        .checked_add(context.utc_offset_seconds)
        .ok_or_else(|| "outside supported calendar coverage".to_owned())?;
    let date_start = unix_midnight(date)?;
    let seconds_from_midnight = local_seconds - date_start;
    let rounded = (seconds_from_midnight + DRIK_DISPLAY_ROUNDING_SECONDS / 2)
        .div_euclid(DRIK_DISPLAY_ROUNDING_SECONDS);
    Ok(rounded.rem_euclid(1_440))
}

fn solar_ingresses_for_gregorian_year(calendar_year: i64) -> Result<Vec<SolarIngress>, String> {
    let year_start = unix_midnight(GregorianDate::new(calendar_year, 1, 1)?)?;
    let year_end = unix_midnight(GregorianDate::new(calendar_year + 1, 1, 1)?)?;
    let mut previous_time = year_start;
    let mut previous_angle = sidereal_sun_longitude(previous_time);
    let mut previous_unwrapped = previous_angle;
    let mut next_boundary = (previous_unwrapped / 30.0).floor() * 30.0 + 30.0;
    let mut ingresses = Vec::with_capacity(12);
    while previous_time < year_end {
        let current_time = (previous_time + SECONDS_PER_DAY).min(year_end);
        let current_angle = sidereal_sun_longitude(current_time);
        let current_unwrapped =
            previous_unwrapped + forward_delta_degrees(previous_angle, current_angle);
        while next_boundary <= current_unwrapped {
            let boundary = next_boundary;
            let root = bisect_predicate(previous_time, current_time, |candidate| {
                let angle = sidereal_sun_longitude(candidate);
                previous_unwrapped + forward_delta_degrees(previous_angle, angle) >= boundary
            });
            let sign = ((boundary / 30.0).round() as i64).rem_euclid(12) as u8;
            ingresses.push(SolarIngress {
                month: sign + 1,
                instant_utc_seconds: root,
            });
            next_boundary += 30.0;
        }
        previous_time = current_time;
        previous_angle = current_angle;
        previous_unwrapped = current_unwrapped;
    }
    if ingresses.len() != 12 {
        return Err("outside supported calendar coverage".into());
    }
    Ok(ingresses)
}

fn sidereal_sun_longitude(instant_utc_seconds: i64) -> f64 {
    let position = position_at(instant_utc_seconds);
    sidereal_longitude_true(
        position.sun_apparent_longitude_deg,
        julian_ephemeris_day(instant_utc_seconds),
    )
}

fn local_month_start(
    ingress: SolarIngress,
    context: ThirukanithamContext,
) -> Result<GregorianDate, String> {
    let local = local_datetime(ingress.instant_utc_seconds, context)?;
    let local_date = GregorianDate::new(local.year, i64::from(local.month), i64::from(local.day))
        .map_err(|_| "outside supported calendar coverage")?;
    let (_, sunset) = solar_events_for_date(local_date, context)?;
    if ingress.instant_utc_seconds <= sunset {
        Ok(local_date)
    } else {
        add_gregorian_date(local_date, "days", 1, "reject")
            .map_err(|_| "outside supported calendar coverage".into())
    }
}

fn solar_month_start(
    solar_year: i64,
    month: u8,
    context: ThirukanithamContext,
) -> Result<GregorianDate, String> {
    let calendar_year = if month >= 10 {
        solar_year + 1
    } else {
        solar_year
    };
    let ingress = solar_ingresses_for_gregorian_year(calendar_year)?
        .into_iter()
        .find(|ingress| ingress.month == month)
        .ok_or("outside supported calendar coverage")?;
    local_month_start(ingress, context)
}

fn solar_month_starts_near_date(
    date: GregorianDate,
    context: ThirukanithamContext,
) -> Result<Vec<SolarMonthStart>, String> {
    let mut roots = Vec::with_capacity(24);
    for calendar_year in [date.year() - 1, date.year()] {
        roots.extend(solar_ingresses_for_gregorian_year(calendar_year)?);
    }
    roots.sort_by_key(|root| root.instant_utc_seconds);
    let mut starts = Vec::with_capacity(roots.len());
    for root in roots {
        let ingress_year = date_from_unix_seconds(root.instant_utc_seconds)?.year();
        let assigned_solar_year = if root.month >= 10 {
            ingress_year - 1
        } else {
            ingress_year
        };
        starts.push(SolarMonthStart {
            solar_year: assigned_solar_year,
            month: root.month,
            date: local_month_start(root, context)?,
        });
    }
    Ok(starts)
}

fn limb_transitions(
    start_utc_seconds: i64,
    end_utc_seconds: i64,
    context: ThirukanithamContext,
) -> Result<Vec<ThirukanithamTransition>, String> {
    let step = DRIK_ROOT_SCAN_STEP_SECONDS;
    let mut cursor = start_utc_seconds - 1;
    let mut before = indices_at(cursor);
    let mut transitions = Vec::new();
    while cursor < end_utc_seconds - 1 {
        let probe = (cursor + step).min(end_utc_seconds - 1);
        let after = indices_at(probe);
        if after != before {
            let transition =
                bisect_predicate(cursor, probe, |candidate| indices_at(candidate) != before);
            let next = indices_at(transition);
            let report_date =
                date_from_unix_seconds(start_utc_seconds + context.utc_offset_seconds)?;
            let (day_offset, minute_of_day) =
                rounded_local_label_for_day(transition, report_date, context)?;
            if before.tithi != next.tithi {
                transitions.push(ThirukanithamTransition {
                    limb: "tithi",
                    from_index: before.tithi,
                    to_index: next.tithi,
                    day_offset,
                    minute_of_day,
                    instant_unix_seconds: transition,
                });
            }
            if before.nakshatra != next.nakshatra {
                transitions.push(ThirukanithamTransition {
                    limb: "nakshatra",
                    from_index: before.nakshatra,
                    to_index: next.nakshatra,
                    day_offset,
                    minute_of_day,
                    instant_unix_seconds: transition,
                });
            }
            if before.yoga != next.yoga {
                transitions.push(ThirukanithamTransition {
                    limb: "yoga",
                    from_index: before.yoga,
                    to_index: next.yoga,
                    day_offset,
                    minute_of_day,
                    instant_unix_seconds: transition,
                });
            }
            if before.karana != next.karana {
                transitions.push(ThirukanithamTransition {
                    limb: "karana",
                    from_index: before.karana,
                    to_index: next.karana,
                    day_offset,
                    minute_of_day,
                    instant_unix_seconds: transition,
                });
            }
            cursor = transition;
            before = next;
        } else {
            cursor = probe;
            before = after;
        }
    }
    transitions.sort_by_key(|transition| {
        (
            transition.instant_unix_seconds,
            match transition.limb {
                "tithi" => 0,
                "nakshatra" => 1,
                "yoga" => 2,
                "karana" => 3,
                _ => 4,
            },
        )
    });
    Ok(transitions)
}

fn rounded_local_label_for_day(
    instant_utc_seconds: i64,
    report_date: GregorianDate,
    context: ThirukanithamContext,
) -> Result<(i64, i64), String> {
    let local = instant_utc_seconds + context.utc_offset_seconds;
    let rounded_local = ((local + DRIK_DISPLAY_ROUNDING_SECONDS / 2)
        .div_euclid(DRIK_DISPLAY_ROUNDING_SECONDS))
        * DRIK_DISPLAY_ROUNDING_SECONDS;
    let rounded_date = date_from_unix_seconds(rounded_local)?;
    let day_offset = date_difference(report_date, rounded_date);
    let minute_of_day = rounded_local
        .rem_euclid(SECONDS_PER_DAY)
        .div_euclid(DRIK_DISPLAY_ROUNDING_SECONDS);
    Ok((day_offset, minute_of_day))
}

fn indices_at(instant_utc_seconds: i64) -> LimbIndices {
    let position = position_at(instant_utc_seconds);
    limb_indices(position, julian_ephemeris_day(instant_utc_seconds))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn observance_tithi_windows_are_half_open_and_aparahna_has_precedence() {
        assert!(half_open_intervals_intersect(10, 21, 20, 30));
        assert!(!half_open_intervals_intersect(10, 20, 20, 30));
        assert!(!half_open_intervals_intersect(10, 20, 5, 10));
        assert!(half_open_interval_contains(10, 20, 10));
        assert!(!half_open_interval_contains(10, 20, 20));

        let first = GregorianDate::new(2027, 3, 7).unwrap();
        let later = GregorianDate::new(2027, 3, 8).unwrap();
        assert_eq!(
            select_aparahna_then_sunrise(&[first, later], &[first]),
            Some(later)
        );
        assert_eq!(select_aparahna_then_sunrise(&[], &[first]), Some(first));
        assert_eq!(select_aparahna_then_sunrise(&[], &[]), None);
    }

    #[test]
    fn sankatahara_double_and_skipped_moonrise_precedence_is_explicit() {
        let first = GregorianDate::new(2026, 8, 2).unwrap();
        let second = GregorianDate::new(2026, 8, 3).unwrap();
        let third = GregorianDate::new(2026, 8, 4).unwrap();

        assert_eq!(select_sankatahara_date(first, second, &[]), Ok(second));
        assert_eq!(select_sankatahara_date(first, second, &[first]), Ok(first));
        assert_eq!(
            select_sankatahara_date(first, second, &[first, second]),
            Ok(first)
        );
        assert!(select_sankatahara_date(first, second, &[first, second, third]).is_err());
        assert!(select_sankatahara_date(first, third, &[]).is_err());
    }

    #[test]
    fn smarta_janmashtami_selects_single_double_or_skipped_nishita() {
        let first = GregorianDate::new(2027, 8, 24).unwrap();
        let second = GregorianDate::new(2027, 8, 25).unwrap();
        let third = GregorianDate::new(2027, 8, 26).unwrap();

        assert_eq!(select_smarta_janmashtami_date(first, &[], &[]), Ok(second));
        assert_eq!(
            select_smarta_janmashtami_date(first, &[first], &[]),
            Ok(first)
        );
        assert_eq!(
            select_smarta_janmashtami_date(first, &[second], &[]),
            Ok(second)
        );
        assert_eq!(
            select_smarta_janmashtami_date(first, &[first, second], &[first]),
            Ok(first)
        );
        assert_eq!(
            select_smarta_janmashtami_date(first, &[first, second], &[second]),
            Ok(second)
        );
        assert_eq!(
            select_smarta_janmashtami_date(first, &[first, second], &[]),
            Ok(second)
        );
        assert_eq!(
            select_smarta_janmashtami_date(first, &[first, second], &[first, second]),
            Ok(second)
        );
        assert!(select_smarta_janmashtami_date(first, &[third], &[]).is_err());
        assert!(select_smarta_janmashtami_date(first, &[first, third], &[]).is_err());
        assert!(select_smarta_janmashtami_date(first, &[first], &[second]).is_err());
    }

    #[test]
    fn nishita_is_the_eighth_of_fifteen_equal_night_parts() {
        let (start, end) = eighth_night_muhurta(10_000, 100_000).unwrap();
        assert_eq!((start, end), (52_000, 58_000));
        assert!(half_open_intervals_intersect(start, end, end - 1, end + 1));
        assert!(!half_open_intervals_intersect(start, end, end, end + 1));
        assert!(eighth_night_muhurta(100, 100).is_err());
    }

    #[test]
    fn chennai_krishna_jayanthi_month_slices_apply_the_selected_smarta_rule() {
        let context =
            ThirukanithamContext::new("TN", 13_087_840, 80_278_470, 14, "Asia/Kolkata").unwrap();
        for (year, month, expected) in [
            (2025, 8, GregorianDate::new(2025, 8, 15).unwrap()),
            (2026, 9, GregorianDate::new(2026, 9, 4).unwrap()),
            (2027, 8, GregorianDate::new(2027, 8, 24).unwrap()),
        ] {
            assert_eq!(
                thirukanitham_krishna_jayanthi_dates(year, Some(month), 23, 4, context).unwrap(),
                [expected],
                "Krishna Jayanthi {year}-{month:02}"
            );
        }
    }

    #[test]
    fn chennai_moonrise_root_is_a_rising_crossing_and_month_slice_keeps_both_dates() {
        let context =
            ThirukanithamContext::new("TN", 13_087_840, 80_278_470, 14, "Asia/Kolkata").unwrap();
        let date = GregorianDate::new(2026, 8, 2).unwrap();
        let moonrise = moonrise_for_date(date, context).unwrap();
        assert!(moonrise_margin_degrees(moonrise - 1, context) < 0.0);
        assert!(moonrise_margin_degrees(moonrise, context) >= 0.0);
        assert_eq!(
            date_from_unix_seconds(moonrise + context.utc_offset_seconds).unwrap(),
            date
        );
        assert_eq!(
            thirukanitham_sankatahara_chaturthi_dates(2026, Some(8), context).unwrap(),
            [date, GregorianDate::new(2026, 8, 31).unwrap()]
        );
    }

    #[test]
    fn nava_pradosha_uses_a_half_open_ninety_minute_sunset_window_and_later_evening() {
        let sunset = 10_000;
        let window_end = sunset + 90 * 60;
        assert!(half_open_intervals_intersect(
            sunset,
            sunset + 1,
            sunset,
            window_end
        ));
        assert!(half_open_intervals_intersect(
            sunset - 1,
            sunset + 1,
            sunset,
            window_end
        ));
        assert!(half_open_intervals_intersect(
            window_end - 1,
            window_end + 1,
            sunset,
            window_end
        ));
        assert!(!half_open_intervals_intersect(
            window_end,
            window_end + 1,
            sunset,
            window_end
        ));
        assert!(!half_open_intervals_intersect(
            sunset - 1,
            sunset,
            sunset,
            window_end
        ));

        let first = GregorianDate::new(2027, 3, 7).unwrap();
        let later = GregorianDate::new(2027, 3, 8).unwrap();
        assert_eq!(select_nava_pradosha_day(&[first, later]), Some(later));
        assert_eq!(select_nava_pradosha_day(&[first]), Some(first));
        assert_eq!(select_nava_pradosha_day(&[]), None);
    }

    #[test]
    fn vaishnava_arunodaya_selection_defers_veddha_and_repeated_tithis_once() {
        let first = GregorianDate::new(2026, 10, 22).unwrap();
        let next = GregorianDate::new(2026, 10, 23).unwrap();
        let following = GregorianDate::new(2026, 10, 24).unwrap();

        assert_eq!(
            select_sri_vaishnava_ekadashi_day(&[first], &[first]).unwrap(),
            Some(first)
        );
        assert_eq!(
            select_sri_vaishnava_ekadashi_day(&[first, next], &[first, next]).unwrap(),
            Some(following)
        );
        assert_eq!(
            select_sri_vaishnava_ekadashi_day(&[], &[first]).unwrap(),
            Some(next)
        );
        assert_eq!(select_sri_vaishnava_ekadashi_day(&[], &[]).unwrap(), None);
        assert_eq!(
            select_sri_vaishnava_ekadashi_day(&[first, next, following], &[]),
            Err("outside supported calendar coverage".into())
        );
    }

    #[test]
    fn daylight_slots_reproduce_printed_sunday_and_monday_table() {
        let sunrise = 6 * 3_600;
        let daylight = 12 * 3_600;
        assert_eq!(
            daylight_interval(
                "rahukalam",
                tables::DRIK_RAHU_EIGHTH_BY_WEEKDAY[0],
                sunrise,
                daylight
            ),
            ThirukanithamDaylightInterval {
                period: "rahukalam",
                eighth_part: 8,
                start_local_seconds_of_day: 16 * 3_600 + 30 * 60,
                end_local_seconds_of_day: 18 * 3_600,
            }
        );
        assert_eq!(
            daylight_interval(
                "kuligai",
                tables::DRIK_KULIGAI_EIGHTH_BY_WEEKDAY[0],
                sunrise,
                daylight
            )
            .start_local_seconds_of_day,
            15 * 3_600
        );
        assert_eq!(
            daylight_interval(
                "yamagandam",
                tables::DRIK_YAMAGANDAM_EIGHTH_BY_WEEKDAY[0],
                sunrise,
                daylight,
            )
            .start_local_seconds_of_day,
            12 * 3_600
        );
        assert_eq!(
            daylight_interval(
                "rahukalam",
                tables::DRIK_RAHU_EIGHTH_BY_WEEKDAY[1],
                sunrise,
                daylight
            )
            .start_local_seconds_of_day,
            7 * 3_600 + 30 * 60
        );
        assert_eq!(
            daylight_interval(
                "kuligai",
                tables::DRIK_KULIGAI_EIGHTH_BY_WEEKDAY[1],
                sunrise,
                daylight
            )
            .start_local_seconds_of_day,
            13 * 3_600 + 30 * 60
        );
        assert_eq!(
            daylight_interval(
                "yamagandam",
                tables::DRIK_YAMAGANDAM_EIGHTH_BY_WEEKDAY[1],
                sunrise,
                daylight,
            )
            .start_local_seconds_of_day,
            10 * 3_600 + 30 * 60
        );
    }
    use proptest::prelude::*;

    #[test]
    fn karana_sequence_places_fixed_and_cyclic_names_at_source_boundaries() {
        let actual = (0..60).map(karana_name).collect::<Vec<_>>();
        assert_eq!(actual[0], "Kimstughna");
        assert_eq!(actual[1], "Bava");
        assert_eq!(actual[7], "Vishti");
        assert_eq!(actual[8], "Bava");
        assert_eq!(actual[56], "Vishti");
        assert_eq!(actual[57], "Sakuni");
        assert_eq!(actual[58], "Chatushpada");
        assert_eq!(actual[59], "Naga");
    }

    #[test]
    fn solar_month_ingresses_are_monotone_and_each_gregorian_year_has_twelve() {
        for year in 2023..=2028 {
            let ingresses = solar_ingresses_for_gregorian_year(year).unwrap();
            assert_eq!(ingresses.len(), 12);
            assert!(ingresses.windows(2).all(|pair| {
                pair[0].instant_utc_seconds < pair[1].instant_utc_seconds
                    && pair[0].month % 12 + 1 == pair[1].month
            }));
        }
    }

    #[test]
    fn phase_events_are_ordered_and_the_query_interval_is_half_open() {
        let events = thirukanitham_lunar_phase_events(1_736_121_600, 1_738_195_200).unwrap();
        assert_eq!(
            events.iter().map(|event| event.phase).collect::<Vec<_>>(),
            ["first_quarter", "full_moon", "last_quarter", "new_moon"]
        );
        assert!(events
            .windows(2)
            .all(|pair| pair[0].instant_utc_seconds < pair[1].instant_utc_seconds));
        let first = events[0].instant_utc_seconds;
        assert_eq!(
            thirukanitham_lunar_phase_events(first, first + 1).unwrap(),
            [events[0]]
        );
        assert!(thirukanitham_lunar_phase_events(first - 1, first)
            .unwrap()
            .is_empty());
    }

    #[test]
    fn lahiri_anchor_and_p03_advance_are_applied_at_the_declared_powers() {
        let anchor = 2_435_553.5;
        let anchor_ayanamsa = lahiri_mean_ayanamsa_degrees(anchor);
        let expected_anchor = 23.0 + 14.0 / 60.0 + 43.889_520 / 3_600.0;
        assert!((anchor_ayanamsa - expected_anchor).abs() < 1.0e-12);
        let true_anchor = lahiri_true_ayanamsa_degrees(anchor);
        assert!((true_anchor - 23.0 - 15.0 / 60.0 - 0.658 / 3_600.0).abs() < 1.0e-9);
    }

    #[test]
    fn p03_lahiri_transform_matches_independent_erfa_epoch_checkpoints() {
        let reference: serde_json::Value = serde_json::from_str(include_str!(
            "../../../tests/reference/calendar-thirukanitham-v1/independent-transforms.json"
        ))
        .unwrap();
        let checkpoints = reference["sidereal_checkpoints"].as_array().unwrap();
        assert_eq!(checkpoints.len(), 6);
        for checkpoint in checkpoints {
            let jde = checkpoint["jd_tt"].as_f64().unwrap();
            let independent_mean_arcseconds =
                checkpoint["mean_ayanamsa_arcseconds"].as_f64().unwrap();
            let independent_true_arcseconds =
                checkpoint["true_ayanamsa_arcseconds"].as_f64().unwrap();
            let selected_mean_arcseconds = lahiri_mean_ayanamsa_degrees(jde) * 3_600.0;
            let selected_true_arcseconds = lahiri_true_ayanamsa_degrees(jde) * 3_600.0;
            assert!(
                (selected_mean_arcseconds - independent_mean_arcseconds).abs() < 0.010,
                "{} mean transform differs by {:.6} arcsec",
                checkpoint["epoch"],
                selected_mean_arcseconds - independent_mean_arcseconds
            );
            assert!(
                (selected_true_arcseconds - independent_true_arcseconds).abs() < 0.03,
                "{} true transform differs by {:.6} arcsec",
                checkpoint["epoch"],
                selected_true_arcseconds - independent_true_arcseconds
            );
            let date_nutation = nutation::nutation(jde).0.to_degrees();
            let apparent_test_longitude = wrap_degrees(200.0 + date_nutation);
            let transformed_apparent = sidereal_longitude_true(apparent_test_longitude, jde);
            let transformed_mean = wrap_degrees(200.0 - lahiri_mean_ayanamsa_degrees(jde));
            assert!(angular_error_arcseconds(transformed_apparent, transformed_mean) < 1.0e-6);
        }
    }

    #[test]
    fn reverse_dates_resolve_before_public_coverage_and_validate_true_month_length() {
        let contexts = [
            ThirukanithamContext::new("TN", 13_087_840, 80_278_470, 14, "Asia/Kolkata").unwrap(),
            ThirukanithamContext::new("SL", 6_935_480, 79_848_680, 7, "Asia/Colombo").unwrap(),
        ];

        for context in contexts {
            for day in 1..=13 {
                let gregorian = GregorianDate::new(2024, 1, day).unwrap();
                let forward = thirukanitham_gregorian_to_tamil_date(gregorian, context).unwrap();
                assert_eq!(forward.tamil_date.solar_year, 2023);
                assert_eq!(forward.tamil_date.month, 9);
                assert_eq!(forward.tamil_date.day, day as u8 + 16);
                let reverse = thirukanitham_tamil_to_gregorian_date(
                    forward.tamil_date.solar_year,
                    i64::from(forward.tamil_date.month),
                    i64::from(forward.tamil_date.day),
                    context,
                )
                .unwrap();
                assert_eq!(reverse.gregorian_date, gregorian);
            }

            for date in [
                GregorianDate::new(2024, 1, 1).unwrap(),
                GregorianDate::new(2027, 12, 31).unwrap(),
            ] {
                let tamil = thirukanitham_gregorian_to_tamil_date(date, context).unwrap();
                let reverse = thirukanitham_tamil_to_gregorian_date(
                    tamil.tamil_date.solar_year,
                    i64::from(tamil.tamil_date.month),
                    i64::from(tamil.tamil_date.day),
                    context,
                )
                .unwrap();
                assert_eq!(reverse.gregorian_date, date);
            }

            assert_eq!(
                thirukanitham_gregorian_to_tamil_date(
                    GregorianDate::new(2023, 12, 31).unwrap(),
                    context
                )
                .unwrap_err(),
                "outside supported calendar coverage"
            );
            assert_eq!(
                thirukanitham_tamil_to_gregorian_date(2023, 9, 31, context).unwrap_err(),
                "invalid Tamil date"
            );
            assert_eq!(
                thirukanitham_tamil_to_gregorian_date(2023, 8, 31, context).unwrap_err(),
                "invalid Tamil date"
            );
            assert_eq!(
                thirukanitham_tamil_to_gregorian_date(2027, 9, 31, context).unwrap_err(),
                "invalid Tamil date"
            );
            assert_eq!(
                thirukanitham_tamil_to_gregorian_date(2027, 9, 17, context).unwrap_err(),
                "outside supported calendar coverage"
            );
        }
    }

    #[test]
    fn civil_day_transition_labels_derive_from_rounded_local_root_timestamp() {
        let context =
            ThirukanithamContext::new("TN", 13_087_840, 80_278_470, 14, "Asia/Kolkata").unwrap();
        let date = GregorianDate::new(2027, 10, 16).unwrap();
        let day = thirukanitham_panchangam_day(date, context).unwrap();
        let interval_start = local_midnight_unix(date, context).unwrap();
        let interval_end = interval_start + SECONDS_PER_DAY;
        let transition = day
            .transitions
            .iter()
            .find(|transition| transition.limb == "nakshatra" && transition.from_index == 1)
            .unwrap();

        // The review's pre-fix root at 23:59:44 rounded to next-day 00:00
        // while retaining day_offset 0. Keep that exact display case as a
        // helper regression, independent of the corrected ephemeris root.
        assert!(interval_start <= transition.instant_unix_seconds);
        assert!(transition.instant_unix_seconds < interval_end);
        let review_root_utc =
            unix_midnight(date).unwrap() + 23 * 3_600 + 59 * 60 + 44 - context.utc_offset_seconds;
        assert_eq!(
            rounded_local_label_for_day(review_root_utc, date, context).unwrap(),
            (1, 0)
        );
        assert_eq!(
            rounded_local_label_for_day(
                unix_midnight(date).unwrap() + 12 * 3_600 + 30 - context.utc_offset_seconds,
                date,
                context,
            )
            .unwrap(),
            (0, 12 * 60 + 1)
        );
        assert_eq!(
            rounded_local_label_for_day(
                unix_midnight(date).unwrap() + 23 * 3_600 + 59 * 60 + 30
                    - context.utc_offset_seconds,
                date,
                context,
            )
            .unwrap(),
            (1, 0)
        );
        let early_date = GregorianDate::new(2024, 1, 9).unwrap();
        assert_eq!(
            rounded_local_label_for_day(
                unix_midnight(early_date).unwrap() + 14 - context.utc_offset_seconds,
                early_date,
                context,
            )
            .unwrap(),
            (0, 0)
        );

        let early = thirukanitham_panchangam_day(early_date, context).unwrap();
        assert!(early
            .transitions
            .windows(2)
            .all(|pair| { pair[0].instant_unix_seconds <= pair[1].instant_unix_seconds }));
        assert!(early.transitions.windows(2).any(|pair| {
            pair[0].day_offset == pair[1].day_offset
                && pair[0].minute_of_day == pair[1].minute_of_day
        }));
        assert!(early.transitions.windows(2).all(|pair| {
            pair[0].instant_unix_seconds != pair[1].instant_unix_seconds
                || limb_tie_order(pair[0].limb) <= limb_tie_order(pair[1].limb)
        }));
    }

    #[test]
    fn civil_day_transitions_are_right_continuous_at_the_first_utc_second() {
        let context =
            ThirukanithamContext::new("TN", 13_087_840, 80_278_470, 14, "Asia/Kolkata").unwrap();
        let date = GregorianDate::new(2026, 11, 1).unwrap();
        let day = thirukanitham_panchangam_day(date, context).unwrap();
        assert_eq!(day.transitions.len(), 5);
        for transition in day.transitions {
            let before = limb_indices(
                position_at(transition.instant_unix_seconds - 1),
                julian_ephemeris_day(transition.instant_unix_seconds - 1),
            );
            let after = limb_indices(
                position_at(transition.instant_unix_seconds),
                julian_ephemeris_day(transition.instant_unix_seconds),
            );
            let (before_index, after_index) = match transition.limb {
                "tithi" => (before.tithi, after.tithi),
                "nakshatra" => (before.nakshatra, after.nakshatra),
                "yoga" => (before.yoga, after.yoga),
                "karana" => (before.karana, after.karana),
                _ => unreachable!(),
            };
            assert_eq!(before_index, transition.from_index);
            assert_eq!(after_index, transition.to_index);
        }
    }

    #[test]
    #[ignore = "slow derived evidence exporter; run with --ignored to regenerate projection rows"]
    fn dump_independent_transition_reference_candidates() {
        let context =
            ThirukanithamContext::new("TN", 13_087_840, 80_278_470, 14, "Asia/Kolkata").unwrap();
        let mut found = [false; 6];
        let mut nearest_sunrise: Option<(i64, GregorianDate, i64, Vec<ThirukanithamTransition>)> =
            None;
        let mut nearest_midnight: Option<(i64, GregorianDate, i64, Vec<ThirukanithamTransition>)> =
            None;
        for year in 2024..=2027 {
            let days_in_year = if year == 2024 || year == 2026 {
                366
            } else {
                365
            };
            let jan1 = GregorianDate::new(year, 1, 1).unwrap();
            for day_of_year in 0..days_in_year {
                let date = add_gregorian_date(jan1, "days", day_of_year, "reject").unwrap();
                let start = local_midnight_unix(date, context).unwrap();
                let transitions =
                    limb_transitions(start, start + SECONDS_PER_DAY, context).unwrap();
                if transitions.is_empty() {
                    continue;
                }
                let (sunrise, _) = solar_events_for_date(date, context).unwrap();
                let sunrise_delta = transitions
                    .iter()
                    .map(|event| (event.instant_unix_seconds - sunrise).abs())
                    .min()
                    .unwrap();
                if nearest_sunrise
                    .as_ref()
                    .is_none_or(|(delta, _, _, _)| sunrise_delta < *delta)
                {
                    nearest_sunrise = Some((sunrise_delta, date, sunrise, transitions.clone()));
                }
                let midnight_delta = transitions
                    .iter()
                    .map(|event| (event.instant_unix_seconds - start).abs())
                    .min()
                    .unwrap();
                if nearest_midnight
                    .as_ref()
                    .is_none_or(|(delta, _, _, _)| midnight_delta < *delta)
                {
                    nearest_midnight = Some((midnight_delta, date, start, transitions.clone()));
                }
                for event in &transitions {
                    let candidate = match (event.limb, event.from_index, event.to_index) {
                        ("tithi", 30, 1) if !found[0] => Some((0, "new_moon_wrap")),
                        ("tithi", 15, 16) if !found[1] => Some((1, "full_moon_wrap")),
                        ("karana", 56, 57) if !found[2] => Some((2, "fixed_karana_57")),
                        ("karana", 57, 58) if !found[3] => Some((3, "fixed_karana_58")),
                        ("karana", 58, 59) if !found[4] => Some((4, "fixed_karana_59")),
                        ("karana", 59, 0) if !found[5] => Some((5, "karana_wrap_0")),
                        _ => None,
                    };
                    if let Some((index, label)) = candidate {
                        found[index] = true;
                        let (sunrise, sunset) = solar_events_for_date(date, context).unwrap();
                        let events = transitions.iter().map(|event| serde_json::json!({
                            "limb": event.limb,
                            "from_index": event.from_index,
                            "to_index": event.to_index,
                            "instant_utc_seconds": event.instant_unix_seconds,
                            "local": {
                                "year": local_datetime(event.instant_unix_seconds, context).unwrap().year,
                                "month": local_datetime(event.instant_unix_seconds, context).unwrap().month,
                                "day": local_datetime(event.instant_unix_seconds, context).unwrap().day,
                                "hour": local_datetime(event.instant_unix_seconds, context).unwrap().hour,
                                "minute": local_datetime(event.instant_unix_seconds, context).unwrap().minute,
                                "second": local_datetime(event.instant_unix_seconds, context).unwrap().second,
                            },
                            "day_offset": event.day_offset,
                            "minute_of_day": event.minute_of_day,
                        })).collect::<Vec<_>>();
                        println!(
                            "CANDIDATE {}",
                            serde_json::json!({
                                "case": label,
                                "date": {"year": date.year(), "month": date.month(), "day": date.day()},
                                "sunrise_utc_seconds": sunrise,
                                "sunset_utc_seconds": sunset,
                                "transitions": events,
                            })
                        );
                    }
                }
            }
        }
        for (label, (delta, date, anchor, events)) in [
            ("sunrise_adjacent", nearest_sunrise.unwrap()),
            ("nearest_midnight", nearest_midnight.unwrap()),
        ] {
            let selected = events
                .iter()
                .min_by_key(|event| (event.instant_unix_seconds - anchor).abs())
                .unwrap();
            println!(
                "CANDIDATE {}",
                serde_json::json!({
                    "case": label,
                    "date": {"year": date.year(), "month": date.month(), "day": date.day()},
                    "distance_seconds": delta,
                    "limb": selected.limb,
                    "from_index": selected.from_index,
                    "to_index": selected.to_index,
                    "instant_utc_seconds": selected.instant_unix_seconds,
                    "local": {
                        "year": local_datetime(selected.instant_unix_seconds, context).unwrap().year,
                        "month": local_datetime(selected.instant_unix_seconds, context).unwrap().month,
                        "day": local_datetime(selected.instant_unix_seconds, context).unwrap().day,
                        "hour": local_datetime(selected.instant_unix_seconds, context).unwrap().hour,
                        "minute": local_datetime(selected.instant_unix_seconds, context).unwrap().minute,
                        "second": local_datetime(selected.instant_unix_seconds, context).unwrap().second,
                    },
                    "day_offset": selected.day_offset,
                    "minute_of_day": selected.minute_of_day,
                })
            );
        }
        let colombo =
            ThirukanithamContext::new("SL", 6_935_480, 79_848_680, 7, "Asia/Colombo").unwrap();
        let jaffna =
            ThirukanithamContext::new("SL", 9_668_450, 80_007_420, 7, "Asia/Colombo").unwrap();
        let jaffna_low =
            ThirukanithamContext::new("SL", 9_668_450, 80_007_420, -100, "Asia/Colombo").unwrap();
        let jaffna_high =
            ThirukanithamContext::new("SL", 9_668_450, 80_007_420, 3_000, "Asia/Colombo").unwrap();
        let report_dates = [
            (2024, 1, 1),
            (2024, 1, 3),
            (2024, 1, 10),
            (2024, 1, 11),
            (2024, 1, 25),
            (2025, 7, 15),
            (2026, 11, 1),
            (2027, 12, 31),
        ];
        for (year, month, day) in report_dates {
            let date = GregorianDate::new(year, month, day).unwrap();
            for report_context in [context, colombo, jaffna, jaffna_low, jaffna_high] {
                let start = local_midnight_unix(date, report_context).unwrap();
                let transitions =
                    limb_transitions(start, start + SECONDS_PER_DAY, report_context).unwrap();
                let (sunrise, sunset) = solar_events_for_date(date, report_context).unwrap();
                let event_rows = transitions
                    .iter()
                    .map(|event| {
                        let local = local_datetime(event.instant_unix_seconds, report_context).unwrap();
                        serde_json::json!({
                            "limb": event.limb,
                            "from_index": event.from_index,
                            "to_index": event.to_index,
                            "instant_utc_seconds": event.instant_unix_seconds,
                            "local": {"year":local.year,"month":local.month,"day":local.day,"hour":local.hour,"minute":local.minute,"second":local.second},
                            "day_offset": event.day_offset,
                            "minute_of_day": event.minute_of_day,
                        })
                    })
                    .collect::<Vec<_>>();
                let sunrise_local = local_datetime(sunrise, report_context).unwrap();
                let sunset_local = local_datetime(sunset, report_context).unwrap();
                println!(
                    "DAYREPORT {}",
                    serde_json::json!({
                        "date": {"year":year,"month":month,"day":day},
                        "region": report_context.region,
                        "latitude_microdegrees": report_context.latitude_microdegrees,
                        "longitude_microdegrees": report_context.longitude_microdegrees,
                        "elevation_meters": report_context.elevation_meters,
                        "sunrise_utc_seconds": sunrise,
                        "sunset_utc_seconds": sunset,
                        "sunrise_local": {"hour":sunrise_local.hour,"minute":sunrise_local.minute,"second":sunrise_local.second},
                        "sunset_local": {"hour":sunset_local.hour,"minute":sunset_local.minute,"second":sunset_local.second},
                        "transitions": event_rows,
                    })
                );
            }
        }
        let mut ingresses = Vec::new();
        for year in 2023..=2028 {
            ingresses.extend(solar_ingresses_for_gregorian_year(year).unwrap());
        }
        ingresses.sort_by_key(|ingress| ingress.instant_utc_seconds);
        for pair in ingresses.windows(2) {
            let ingress = pair[0];
            let next = pair[1];
            let ingress_date = date_from_unix_seconds(ingress.instant_utc_seconds).unwrap();
            let solar_year = if ingress.month >= 10 {
                ingress_date.year() - 1
            } else {
                ingress_date.year()
            };
            if !((solar_year == 2023 && ingress.month >= 9)
                || (2024..=2026).contains(&solar_year)
                || (solar_year == 2027 && ingress.month <= 9))
            {
                continue;
            }
            let regions = [context, colombo, jaffna]
                .into_iter()
                .map(|region| {
                    let start_date = local_month_start(ingress, region).unwrap();
                    let end_date = local_month_start(next, region).unwrap();
                    serde_json::json!({
                        "region": region.region,
                        "start_date": {"year":start_date.year(),"month":start_date.month(),"day":start_date.day()},
                        "end_date_exclusive": {"year":end_date.year(),"month":end_date.month(),"day":end_date.day()},
                        "days": date_difference(start_date, end_date),
                    })
                })
                .collect::<Vec<_>>();
            println!(
                "MONTHREF {}",
                serde_json::json!({
                    "solar_year": solar_year,
                    "month": ingress.month,
                    "ingress_utc_seconds": ingress.instant_utc_seconds,
                    "next_ingress_utc_seconds": next.instant_utc_seconds,
                    "regions": regions,
                })
            );
        }
        assert!(found.into_iter().all(|value| value));
    }

    #[test]
    fn geocentric_apparent_longitudes_match_saved_jpl_de441_samples() {
        // JPL Horizons DE441, center 500@399, UTC, apparent airless ecliptic
        // coordinates. Raw records and SHA-256 digests live in
        // tests/reference/calendar-thirukanitham-v1/horizons/.
        let samples = [
            (2024, 1, 1, 0, 0, 280.0389812, 155.9921866),
            (2024, 4, 13, 18, 0, 24.2939470, 90.1380670),
            (2024, 4, 14, 0, 0, 24.5389381, 93.4140791),
            (2025, 4, 13, 18, 0, 24.0528747, 212.0193733),
            (2025, 4, 14, 0, 0, 24.2977508, 214.9755905),
            (2026, 4, 13, 18, 0, 23.8156451, 334.9709442),
            (2026, 4, 14, 0, 0, 24.0607132, 338.2914490),
            (2026, 11, 1, 0, 0, 218.5768804, 117.4706196),
            (2026, 11, 1, 18, 30, 219.3478915, 128.2852965),
            (2027, 1, 15, 0, 0, 294.5912943, 14.2272259),
            (2027, 4, 13, 18, 0, 23.5889569, 110.8810625),
            (2027, 4, 14, 0, 0, 23.8340070, 114.4121023),
            (2027, 12, 31, 23, 0, 280.0345724, 325.1510152),
        ];
        let mut maximum_sun_error_arcseconds: f64 = 0.0;
        let mut maximum_moon_error_arcseconds: f64 = 0.0;
        for (year, month, day, hour, minute, expected_sun, expected_moon) in samples {
            let instant = unix_midnight(GregorianDate::new(year, month, day).unwrap()).unwrap()
                + hour * 3_600
                + minute * 60;
            let position = position_at(instant);
            let apparent_moon = position.moon_apparent_longitude_deg;
            let sun_error = (wrap_degrees(position.sun_apparent_longitude_deg - expected_sun)
                + 180.0)
                .rem_euclid(360.0)
                - 180.0;
            let moon_error =
                (wrap_degrees(apparent_moon - expected_moon) + 180.0).rem_euclid(360.0) - 180.0;
            maximum_sun_error_arcseconds =
                maximum_sun_error_arcseconds.max(sun_error.abs() * 3_600.0);
            maximum_moon_error_arcseconds =
                maximum_moon_error_arcseconds.max(moon_error.abs() * 3_600.0);
        }
        assert!(
            maximum_sun_error_arcseconds <= 1.0,
            "Sun error: {maximum_sun_error_arcseconds} arcsec"
        );
        assert!(
            maximum_moon_error_arcseconds <= 10.0,
            "Moon error: {maximum_moon_error_arcseconds} arcsec"
        );
    }

    #[test]
    fn production_limb_and_sidereal_coordinates_match_independent_jpl_transforms() {
        let reference: serde_json::Value = serde_json::from_str(include_str!(
            "../../../tests/reference/calendar-thirukanitham-v1/independent-transforms.json"
        ))
        .unwrap();
        let samples = reference["samples"].as_array().unwrap();
        let mut max_limb_sun_error = 0.0_f64;
        let mut max_limb_moon_error = 0.0_f64;
        let mut max_elongation_error = 0.0_f64;
        let mut max_sidereal_sun_error = 0.0_f64;
        let mut max_sidereal_moon_error = 0.0_f64;

        for sample in samples {
            let instant = sample["unix_utc_seconds"].as_i64().unwrap();
            let jde = julian_ephemeris_day(instant);
            let position = position_at(instant);
            let expected_sun = sample["jpl_apparent"]["sun_longitude_deg"]
                .as_f64()
                .unwrap();
            let expected_moon = sample["jpl_apparent"]["moon_longitude_deg"]
                .as_f64()
                .unwrap();
            let expected_elongation = sample["jpl_apparent"]["elongation_deg"].as_f64().unwrap();
            let expected_sidereal_sun = sample["p03_lahiri_true"]["sidereal_sun_longitude_deg"]
                .as_f64()
                .unwrap();
            let expected_sidereal_moon = sample["p03_lahiri_true"]["sidereal_moon_longitude_deg"]
                .as_f64()
                .unwrap();

            // These are the coordinates actually consumed by production
            // tithi, karana, nakshatra, and yoga calculations.
            let production_sun = position.sun_apparent_longitude_deg;
            let production_moon = position.moon_apparent_longitude_deg;
            let production_elongation = wrap_degrees(production_moon - production_sun);
            let production_sidereal_sun = sidereal_longitude_true(production_sun, jde);
            let production_sidereal_moon = sidereal_longitude_true(production_moon, jde);

            max_limb_sun_error =
                max_limb_sun_error.max(angular_error_arcseconds(production_sun, expected_sun));
            max_limb_moon_error =
                max_limb_moon_error.max(angular_error_arcseconds(production_moon, expected_moon));
            max_elongation_error = max_elongation_error.max(angular_error_arcseconds(
                production_elongation,
                expected_elongation,
            ));
            max_sidereal_sun_error = max_sidereal_sun_error.max(angular_error_arcseconds(
                production_sidereal_sun,
                expected_sidereal_sun,
            ));
            max_sidereal_moon_error = max_sidereal_moon_error.max(angular_error_arcseconds(
                production_sidereal_moon,
                expected_sidereal_moon,
            ));
        }

        assert!(
            max_limb_sun_error <= 1.0,
            "production Sun error: {max_limb_sun_error} arcsec"
        );
        assert!(
            max_limb_moon_error <= 10.0,
            "production Moon error: {max_limb_moon_error} arcsec"
        );
        assert!(
            max_elongation_error <= 11.0,
            "production elongation error: {max_elongation_error} arcsec"
        );
        assert!(
            max_sidereal_sun_error <= 1.0,
            "production sidereal Sun error: {max_sidereal_sun_error} arcsec"
        );
        assert!(
            max_sidereal_moon_error <= 10.0,
            "production sidereal Moon error: {max_sidereal_moon_error} arcsec"
        );
        eprintln!("production apparent/JPL maxima arcsec: Sun={max_limb_sun_error:.6}, Moon={max_limb_moon_error:.6}, elongation={max_elongation_error:.6}, sidereal Sun={max_sidereal_sun_error:.6}, sidereal Moon={max_sidereal_moon_error:.6}");
    }

    #[test]
    fn production_roots_match_independent_jpl_second_cadence_brackets() {
        let reference: serde_json::Value = serde_json::from_str(include_str!(
            "../../../tests/reference/calendar-thirukanitham-v1/independent-root-observations.json"
        ))
        .unwrap();
        let solar_roots = reference["solar_ingresses"].as_array().unwrap();
        assert_eq!(solar_roots.len(), 50);
        let mut maximum_solar_delta = 0_i64;
        for expected in solar_roots {
            let solar_year = expected["solar_year"].as_i64().unwrap();
            let month = expected["month"].as_u64().unwrap() as u8;
            let calendar_year = if month >= 10 {
                solar_year + 1
            } else {
                solar_year
            };
            let actual = solar_ingresses_for_gregorian_year(calendar_year)
                .unwrap()
                .into_iter()
                .find(|ingress| ingress.month == month)
                .unwrap()
                .instant_utc_seconds;
            assert_eq!(
                actual,
                expected["profile_root_utc_seconds_used_to_select_window"]
                    .as_i64()
                    .unwrap(),
                "solar ingress {solar_year}/{month}"
            );
            let before = expected["jpl_before_utc_seconds"].as_i64().unwrap();
            let after = expected["jpl_after_utc_seconds"].as_i64().unwrap();
            assert_eq!(after - before, 1);
            let delta = (actual - after).abs();
            maximum_solar_delta = maximum_solar_delta.max(delta);
            assert!(
                delta <= 3,
                "solar ingress {solar_year}/{month}: {delta}s from JPL bracket"
            );
        }

        let event_roots = reference["civil_day_limb_roots"].as_array().unwrap();
        assert_eq!(event_roots.len(), 43);
        let mut maximum_limb_delta = 0_i64;
        for expected in event_roots {
            let context_row = &expected["contexts"][0];
            let region = context_row["region"].as_str().unwrap();
            let (latitude, longitude, time_zone) = match region {
                "TN" => (13_082_700, 80_278_470, "Asia/Kolkata"),
                "SL" => (6_935_480, 79_848_680, "Asia/Colombo"),
                _ => panic!("unexpected region in independent root data: {region}"),
            };
            let elevation = context_row["elevation_meters"].as_i64().unwrap();
            let context =
                ThirukanithamContext::new(region, latitude, longitude, elevation, time_zone)
                    .unwrap();
            let date_row = &context_row["date"];
            let date = GregorianDate::new(
                date_row["year"].as_i64().unwrap(),
                date_row["month"].as_i64().unwrap(),
                date_row["day"].as_i64().unwrap(),
            )
            .unwrap();
            let start = local_midnight_unix(date, context).unwrap();
            let transitions = limb_transitions(start, start + SECONDS_PER_DAY, context).unwrap();
            let limb = expected["limb"].as_str().unwrap();
            let from_index = expected["from_index"].as_u64().unwrap() as u8;
            let to_index = expected["to_index"].as_u64().unwrap() as u8;
            let actual = transitions
                .iter()
                .find(|event| {
                    event.limb == limb
                        && event.from_index == from_index
                        && event.to_index == to_index
                })
                .unwrap_or_else(|| panic!("missing production {limb} {from_index}->{to_index}"))
                .instant_unix_seconds;
            assert_eq!(
                actual,
                expected["profile_root_utc_seconds_used_to_select_window"]
                    .as_i64()
                    .unwrap(),
                "production {limb} {from_index}->{to_index} on {date:?}"
            );
            let before = expected["jpl_before_utc_seconds"].as_i64().unwrap();
            let after = expected["jpl_after_utc_seconds"].as_i64().unwrap();
            assert_eq!(after - before, 1);
            let delta = (actual - after).abs();
            maximum_limb_delta = maximum_limb_delta.max(delta);
            assert!(
                delta <= 4,
                "{limb} {from_index}->{to_index} on {date:?}: {delta}s from JPL bracket"
            );
        }
        assert_eq!(maximum_solar_delta, 3);
        assert_eq!(maximum_limb_delta, 4);
    }

    #[test]
    fn complete_civil_day_reports_match_independent_full_day_jpl_transition_sets() {
        let expected: serde_json::Value = serde_json::from_str(include_str!(
            "../../../tests/reference/calendar-thirukanitham-v1/independent-full-day-observations.json"
        ))
        .unwrap();
        let derived: serde_json::Value = serde_json::from_str(include_str!(
            "../../../tests/reference/calendar-thirukanitham-v1/derived-civil-day-and-month-reports.json"
        ))
        .unwrap();
        let expected_days = expected["days"].as_array().unwrap();
        let reports = derived["civil_day_reports"].as_array().unwrap();
        assert_eq!(expected_days.len(), 8);
        assert_eq!(reports.len(), 40);
        let mut checked_contexts = 0;
        for report in reports {
            let date_row = &report["date"];
            let date = GregorianDate::new(
                date_row["year"].as_i64().unwrap(),
                date_row["month"].as_i64().unwrap(),
                date_row["day"].as_i64().unwrap(),
            )
            .unwrap();
            let date_text = format!("{:04}-{:02}-{:02}", date.year(), date.month(), date.day());
            let jpl_day = expected_days
                .iter()
                .find(|day| day["local_date"] == date_text)
                .unwrap_or_else(|| panic!("missing full-day JPL samples for {date_text}"));
            let context = ThirukanithamContext::new(
                report["region"].as_str().unwrap(),
                report["latitude_microdegrees"].as_i64().unwrap(),
                report["longitude_microdegrees"].as_i64().unwrap(),
                report["elevation_meters"].as_i64().unwrap(),
                if report["region"] == "TN" {
                    "Asia/Kolkata"
                } else {
                    "Asia/Colombo"
                },
            )
            .unwrap();
            let start = local_midnight_unix(date, context).unwrap();
            let actual = limb_transitions(start, start + SECONDS_PER_DAY, context).unwrap();
            let expected_transitions = jpl_day["transitions"].as_array().unwrap();
            let mut actual_keys = actual
                .iter()
                .map(|event| (event.limb, event.from_index, event.to_index))
                .collect::<Vec<_>>();
            let mut expected_keys = expected_transitions
                .iter()
                .map(|event| {
                    (
                        event["limb"].as_str().unwrap(),
                        event["from_index"].as_u64().unwrap() as u8,
                        event["to_index"].as_u64().unwrap() as u8,
                    )
                })
                .collect::<Vec<_>>();
            actual_keys.sort_unstable();
            expected_keys.sort_unstable();
            assert_eq!(
                actual_keys, expected_keys,
                "complete transition set for {date_text}"
            );
            for event in &actual {
                let bracket = expected_transitions
                    .iter()
                    .find(|row| {
                        row["limb"] == event.limb
                            && row["from_index"] == event.from_index
                            && row["to_index"] == event.to_index
                    })
                    .unwrap();
                let before = bracket["jpl_before_utc_seconds"].as_i64().unwrap();
                let after = bracket["jpl_after_utc_seconds"].as_i64().unwrap();
                assert_eq!(after - before, 60);
                assert!(
                    (before - 4..=after + 4).contains(&event.instant_unix_seconds),
                    "{} {}->{} on {date_text}: profile root {} outside JPL minute bracket {}..{}",
                    event.limb,
                    event.from_index,
                    event.to_index,
                    event.instant_unix_seconds,
                    before,
                    after
                );
            }
            checked_contexts += 1;
        }
        assert_eq!(checked_contexts, 40);
        assert_eq!(
            expected["statistics"]["independent_jpl_classified_limb_transitions"],
            43
        );
    }

    #[test]
    fn publisher_comparison_component_deltas_are_measured_separately() {
        let evidence: serde_json::Value = serde_json::from_str(include_str!(
            "../../../tests/reference/calendar-thirukanitham-v1/publisher-correction-components-2026-11-01.json"
        ))
        .unwrap();
        let date = GregorianDate::new(2026, 11, 1).unwrap();
        let chennai =
            ThirukanithamContext::new("TN", 13_087_840, 80_278_470, 14, "Asia/Kolkata").unwrap();
        let colombo =
            ThirukanithamContext::new("SL", 6_935_480, 79_848_680, 7, "Asia/Colombo").unwrap();
        for (name, context) in [("Chennai", chennai), ("Colombo", colombo)] {
            let at_reference_elevation = solar_events_for_date(date, context).unwrap();
            let geometric_center = solar_altitude_crossings(
                date,
                context,
                -horizon_dip_degrees(context.elevation_meters),
            );
            let sea_level = ThirukanithamContext::new(
                context.region,
                context.latitude_microdegrees,
                context.longitude_microdegrees,
                0,
                context.time_zone,
            )
            .unwrap();
            let at_sea_level = solar_events_for_date(date, sea_level).unwrap();
            eprintln!(
                "{name} elevation={}m; selected horizon roots={} {}; sea-level roots={} {}; elevation-only delta={}s/{}s",
                context.elevation_meters,
                local_datetime(at_reference_elevation.0, context).unwrap().hour,
                local_datetime(at_reference_elevation.0, context).unwrap().minute,
                local_datetime(at_sea_level.0, context).unwrap().hour,
                local_datetime(at_sea_level.0, context).unwrap().minute,
                at_reference_elevation.0 - at_sea_level.0,
                at_reference_elevation.1 - at_sea_level.1,
            );
            eprintln!(
                "{name} selected horizon versus geometric center: sunrise delta={}s; sunset delta={}s",
                at_reference_elevation.0 - geometric_center.0,
                at_reference_elevation.1 - geometric_center.1,
            );
            let station = if name == "Chennai" {
                "chennai"
            } else {
                "colombo"
            };
            let expected = &evidence["solar_event_sensitivity"][station];
            assert_eq!(
                at_reference_elevation.0 - at_sea_level.0,
                expected["elevation_only_delta_profile_minus_sea_level_seconds"][0]
                    .as_i64()
                    .unwrap()
            );
            assert_eq!(
                at_reference_elevation.1 - at_sea_level.1,
                expected["elevation_only_delta_profile_minus_sea_level_seconds"][1]
                    .as_i64()
                    .unwrap()
            );
            assert_eq!(
                at_reference_elevation.0 - geometric_center.0,
                expected["profile_minus_geometric_center_crossing_seconds"][0]
                    .as_i64()
                    .unwrap()
            );
            assert_eq!(
                at_reference_elevation.1 - geometric_center.1,
                expected["profile_minus_geometric_center_crossing_seconds"][1]
                    .as_i64()
                    .unwrap()
            );
        }

        let tithi_current = limb_transitions(
            local_midnight_unix(date, chennai).unwrap(),
            local_midnight_unix(date, chennai).unwrap() + SECONDS_PER_DAY,
            chennai,
        )
        .unwrap()
        .into_iter()
        .find(|event| event.limb == "tithi" && event.from_index == 22 && event.to_index == 23)
        .unwrap()
        .instant_unix_seconds;
        let yoga_current = limb_transitions(
            local_midnight_unix(date, chennai).unwrap(),
            local_midnight_unix(date, chennai).unwrap() + SECONDS_PER_DAY,
            chennai,
        )
        .unwrap()
        .into_iter()
        .find(|event| event.limb == "yoga" && event.from_index == 22 && event.to_index == 23)
        .unwrap()
        .instant_unix_seconds;
        let nakshatra_current = limb_transitions(
            local_midnight_unix(date, chennai).unwrap(),
            local_midnight_unix(date, chennai).unwrap() + SECONDS_PER_DAY,
            chennai,
        )
        .unwrap()
        .into_iter()
        .find(|event| event.limb == "nakshatra" && event.from_index == 7 && event.to_index == 8)
        .unwrap()
        .instant_unix_seconds;
        for (limb, from, to, current) in [
            ("tithi", 22, 23, tithi_current),
            ("nakshatra", 7, 8, nakshatra_current),
            ("yoga", 22, 23, yoga_current),
        ] {
            let prior = find_model_transition(date, chennai, limb, from, to, false, false);
            let anchor_corrected =
                find_model_transition(date, chennai, limb, from, to, true, false);
            eprintln!(
                "{limb} {from}->{to}: prior={} anchor-corrected={} apparent/true={} delta_anchor={}s delta_apparent={}s",
                prior,
                anchor_corrected,
                current,
                anchor_corrected - prior,
                current - anchor_corrected,
            );
            let expected = evidence["chennai_limb_root_variants"]
                .as_array()
                .unwrap()
                .iter()
                .find(|row| row["limb"] == limb)
                .unwrap();
            assert_eq!(
                prior,
                expected["prior_mean_pipeline_utc_seconds"]
                    .as_i64()
                    .unwrap()
            );
            assert_eq!(
                anchor_corrected,
                expected["corrected_anchor_with_mean_coordinates_utc_seconds"]
                    .as_i64()
                    .unwrap()
            );
            assert_eq!(
                current,
                expected["corrected_profile_utc_seconds"].as_i64().unwrap()
            );
            assert_eq!(
                anchor_corrected - prior,
                expected["anchor_component_delta_seconds"].as_i64().unwrap()
            );
            assert_eq!(
                current - anchor_corrected,
                expected["apparent_coordinate_component_delta_seconds"]
                    .as_i64()
                    .unwrap()
            );
        }

        let jde = julian_ephemeris_day(tithi_current);
        let (sun_mean, sun_distance) = sun::geocent_ecl_pos(jde);
        let (sun_fk5_longitude, _) = sun::ecl_coords_to_FK5(jde, sun_mean.long, sun_mean.lat);
        let (nutation_longitude, _) = nutation::nutation(jde);
        eprintln!(
            "2026-11-01 component longitudes arcsec: FK5={:.6}, nutation={:.6}, solar_aberration={:.6}, anchor_nutation={:.6}",
            (sun_fk5_longitude - sun_mean.long).to_degrees() * 3_600.0,
            nutation_longitude.to_degrees() * 3_600.0,
            aberr::sol_aberr(sun_distance).to_degrees() * 3_600.0,
            16.768_479_927,
        );
        let terms = &evidence["corrected_profile_components"];
        let fk5 = (sun_fk5_longitude - sun_mean.long).to_degrees() * 3_600.0;
        let nutation = nutation_longitude.to_degrees() * 3_600.0;
        let aberration = aberr::sol_aberr(sun_distance).to_degrees() * 3_600.0;
        for (key, actual) in [
            (
                "solar_fk5_longitude_correction_at_tithi_root_arcseconds",
                fk5,
            ),
            ("selected_model_nutation_at_tithi_root_arcseconds", nutation),
            (
                "solar_annual_aberration_at_tithi_root_arcseconds",
                aberration,
            ),
            (
                "net_solar_apparent_minus_mean_at_tithi_root_arcseconds",
                fk5 + nutation + aberration,
            ),
            (
                "tithi_elongation_apparent_minus_mean_at_root_arcseconds",
                -fk5 - aberration,
            ),
        ] {
            let expected = terms[key].as_f64().unwrap();
            assert!(
                (actual - expected).abs() < 0.000_001,
                "{key}: {actual} != {expected}"
            );
        }
        let (anchor_nutation, _) = nutation::nutation(2_435_553.5);
        let anchor_nutation_arcseconds = anchor_nutation.to_degrees() * 3_600.0;
        let expected_anchor_nutation = terms["selected_model_nutation_at_anchor_arcseconds"]
            .as_f64()
            .unwrap();
        assert!((anchor_nutation_arcseconds - expected_anchor_nutation).abs() < 0.000_001);
    }

    fn find_model_transition(
        date: GregorianDate,
        context: ThirukanithamContext,
        limb: &str,
        from: u8,
        to: u8,
        corrected_anchor: bool,
        apparent_coordinates: bool,
    ) -> i64 {
        let select = |indices: LimbIndices| match limb {
            "tithi" => indices.tithi,
            "nakshatra" => indices.nakshatra,
            "yoga" => indices.yoga,
            "karana" => indices.karana,
            _ => unreachable!(),
        };
        let state_at = |instant| {
            if apparent_coordinates {
                let position = position_at(instant);
                let jde = julian_ephemeris_day(instant);
                let aya = lahiri_true_ayanamsa_degrees(jde);
                indices_from_coordinates(
                    position.sun_apparent_longitude_deg,
                    position.moon_apparent_longitude_deg,
                    aya,
                )
            } else {
                let jde = julian_ephemeris_day(instant);
                let (sun, _) = sun::geocent_ecl_pos(jde);
                let (moon, _) = lunar::geocent_ecl_pos(jde);
                let aya = if corrected_anchor {
                    lahiri_mean_ayanamsa_degrees(jde)
                } else {
                    legacy_mean_ayanamsa_degrees(jde)
                };
                indices_from_coordinates(sun.long.to_degrees(), moon.long.to_degrees(), aya)
            }
        };
        let start = local_midnight_unix(date, context).unwrap();
        let end = start + SECONDS_PER_DAY;
        let mut cursor = start;
        let mut before = select(state_at(cursor));
        while cursor < end - 1 {
            let probe = (cursor + DRIK_ROOT_SCAN_STEP_SECONDS).min(end - 1);
            let after = select(state_at(probe));
            if before == from && after == to {
                return bisect_predicate(cursor, probe, |candidate| {
                    select(state_at(candidate)) != before
                });
            }
            cursor = probe;
            before = after;
        }
        panic!("missing {limb} {from}->{to} model transition on {date:?}");
    }

    fn indices_from_coordinates(sun: f64, moon: f64, aya: f64) -> LimbIndices {
        let elongation = wrap_degrees(moon - sun);
        let sidereal_sun = wrap_degrees(sun - aya);
        let sidereal_moon = wrap_degrees(moon - aya);
        LimbIndices {
            tithi: (elongation / 12.0).floor() as u8 + 1,
            karana: (elongation / 6.0).floor() as u8,
            nakshatra: (sidereal_moon / (40.0 / 3.0)).floor() as u8 + 1,
            yoga: (wrap_degrees(sidereal_sun + sidereal_moon) / (40.0 / 3.0)).floor() as u8 + 1,
        }
    }

    fn legacy_mean_ayanamsa_degrees(jde: f64) -> f64 {
        let j2000 = DRIK_PRECESSION_EPOCH_JD_MILLIDAYS as f64 / 1_000.0;
        let centuries = (jde - j2000) / DRIK_PRECESSION_CENTURY_DAYS as f64;
        let anchor_jd = DRIK_LAHIRI_ANCHOR_JD_CENTIDAYS as f64 / 100.0;
        let anchor_centuries = (anchor_jd - j2000) / DRIK_PRECESSION_CENTURY_DAYS as f64;
        DRIK_LAHIRI_ANCHOR_MILLIARCSECONDS as f64 / 3_600_000.0
            + (precession_arcseconds(centuries) - precession_arcseconds(anchor_centuries)) / 3_600.0
    }

    fn solar_altitude_crossings(
        date: GregorianDate,
        context: ThirukanithamContext,
        target_altitude: f64,
    ) -> (i64, i64) {
        let start = local_midnight_unix(date, context).unwrap();
        let end = start + SECONDS_PER_DAY;
        let altitude = |instant| solar_altitude_degrees(instant, context) - target_altitude;
        let step = (DRIK_ROOT_SCAN_STEP_SECONDS / 4).max(60);
        let mut cursor = start;
        let mut previous = altitude(cursor);
        let mut sunrise = None;
        let mut sunset = None;
        while cursor < end - 1 {
            let next = (cursor + step).min(end - 1);
            let current = altitude(next);
            if previous < 0.0 && current >= 0.0 && sunrise.is_none() {
                sunrise = Some(bisect_predicate(cursor, next, |instant| {
                    altitude(instant) >= 0.0
                }));
            }
            if previous > 0.0 && current <= 0.0 && sunset.is_none() {
                sunset = Some(bisect_predicate(cursor, next, |instant| {
                    altitude(instant) <= 0.0
                }));
            }
            cursor = next;
            previous = current;
        }
        (sunrise.unwrap(), sunset.unwrap())
    }

    fn angular_error_arcseconds(actual: f64, expected: f64) -> f64 {
        ((wrap_degrees(actual - expected) + 180.0).rem_euclid(360.0) - 180.0).abs() * 3_600.0
    }

    fn limb_tie_order(limb: &str) -> u8 {
        match limb {
            "tithi" => 0,
            "nakshatra" => 1,
            "yoga" => 2,
            "karana" => 3,
            _ => 4,
        }
    }

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]

        #[test]
        fn supported_instant_limb_sectors_are_normalized_and_consistent(
            instant in 1_704_067_200i64..1_830_297_600i64,
        ) {
            let position = position_at(instant);
            let indices = limb_indices(position, julian_ephemeris_day(instant));
            prop_assert!((1..=30).contains(&indices.tithi));
            prop_assert!((1..=27).contains(&indices.nakshatra));
            prop_assert!((1..=27).contains(&indices.yoga));
            prop_assert!((0..=59).contains(&indices.karana));
            prop_assert_eq!(indices.tithi, indices.karana / 2 + 1);
            prop_assert!((0.0..360.0).contains(&position.sun_apparent_longitude_deg));
            prop_assert!((0.0..360.0).contains(&position.moon_apparent_longitude_deg));
        }
    }
}

use serde::Deserialize;
use std::{collections::BTreeSet, env, fs, path::PathBuf};
use unicode_normalization::is_nfc;

fn literal(text: &str) -> String {
    format!(
        "\"{}\"",
        text.chars()
            .flat_map(char::escape_unicode)
            .collect::<String>()
    )
}

#[derive(Deserialize)]
struct VakyaSolarProfile {
    profile: String,
    min_saka_year_elapsed: i64,
    max_saka_year_elapsed: i64,
    saka_to_kali_year: i64,
    ahargana_year_days: i64,
    ahargana_quarter_numerator: i64,
    ahargana_quarter_denominator: i64,
    ahargana_adjustment_multiplier: i64,
    ahargana_adjustment_subtrahend: i64,
    ahargana_adjustment_denominator: i64,
    kali_epoch_weekday: String,
    nadis_per_day: i64,
    vinadis_per_nadi: i64,
    cara_interval_coefficients: [[i64; 2]; 3],
    desantara_yojanas_per_nadi: i64,
    bhujaantara_end_of_rasi_vinadis: [i64; 12],
    bhupadi_correction_minutes: Vec<i64>,
    solar_vakya: Vec<SolarVakyaData>,
}
#[derive(Deserialize)]
struct SolarVakyaData {
    rasi: String,
    days: i64,
    nadis: i64,
    vinadis: i64,
}
#[derive(Deserialize)]
struct VakyaMoonProfile {
    profile: String,
    kali_epoch_day: i64,
    cycle_1_days: i64,
    cycle_2_days: i64,
    cycle_3_days: i64,
    cycle_1_angle: [i64; 4],
    cycle_2_angle: [i64; 4],
    cycle_3_angle: [i64; 4],
    dhruva: [i64; 4],
    daily_motion_baseline: [i64; 3],
    cycle_3_vinadis: i64,
    cycle_2_vinadis: i64,
    moon_vakya_rasi_degrees_minutes: Vec<[i64; 3]>,
}
#[derive(Deserialize)]
struct VakyaCivilProfile {
    profile: String,
    definition_id: String,
    kali_epoch_gregorian_ordinal: i64,
    reference_station: String,
    reference_station_latitude_microdegrees: i64,
    reference_station_longitude_microdegrees: i64,
    ist_meridian_longitude_microdegrees: i64,
    mean_sunrise_hour: i64,
    timezone_offset_seconds: i64,
    vinadi_seconds: i64,
    seconds_per_day: i64,
    daytime_end_nadi: i64,
    solar_date_min_year: i64,
    solar_date_max_year: i64,
    kolkata_instant_min_year: i64,
    colombo_instant_min_year: i64,
    timezone_ids: Vec<String>,
    month_names: Vec<String>,
    source_urls: Vec<String>,
}
#[derive(Deserialize)]
struct SolarYearCycleProfile {
    profile: String,
    source_id: String,
    source: String,
    source_sha256: String,
    anchor_solar_year: i64,
    anchor_cycle_index: i64,
    cycle_length: usize,
    region_scope: String,
    sources: Vec<String>,
    cycle_names: Vec<String>,
}
#[derive(Deserialize)]
struct CalendarTamilDisplayProfile {
    profile: String,
    tva_source_url: String,
    tva_source_sha256: String,
    tva_source_locator: String,
    tva_reuse_terms_status: String,
    cldr_source_url: String,
    cldr_source_sha256: String,
    cldr_weekday_locator: String,
    msu_weekday_source_url: String,
    msu_weekday_source_sha256: String,
    msu_weekday_source_locator: String,
    msu_weekday_source_license: String,
    cycle_romanized_source_id: String,
    cycle_romanized_source_sha256: String,
    cycle_tamil_crosscheck_url: String,
    display_scope: String,
    karana_source_note: String,
    months_tamil: Vec<String>,
    weekdays_tamil: Vec<String>,
    weekdays_romanized: Vec<String>,
    tithi_names_tamil: Vec<String>,
    tithi_new_moon_tamil: String,
    nakshatra_names_tamil: Vec<String>,
    yoga_names_tamil: Vec<String>,
    karana_names_tamil: Vec<String>,
    cycle_names_tamil: Vec<String>,
}
#[derive(Deserialize)]
struct OfficialHolidayProfile {
    profile: String,
    schedules: Vec<OfficialHolidaySchedule>,
}
#[derive(Deserialize)]
struct OfficialHolidaySchedule {
    id: String,
    jurisdiction: String,
    year: i64,
    source_id: String,
    source: String,
    source_url: String,
    source_sha256: String,
    reuse_terms_status: String,
    scope_note: String,
    holidays: Vec<OfficialHoliday>,
}
#[derive(Deserialize)]
struct OfficialHoliday {
    date: String,
    name: String,
    categories: Vec<String>,
}
#[derive(Deserialize)]
struct CalendarObservancesProfile {
    rule_set_id: String,
    profile_definition_id: String,
    coverage_start_year: i64,
    coverage_end_year: i64,
    jurisdiction: String,
    scope_note: String,
    astronomy_note: String,
    reuse_terms_status: String,
    sources: Vec<CalendarObservanceSource>,
    rules: Vec<CalendarObservanceRule>,
}
#[derive(Deserialize)]
struct CalendarObservanceSource {
    id: String,
    url: String,
    locator: String,
    sha256: String,
    year: i64,
    #[serde(default)]
    coverage_start: String,
    #[serde(default)]
    coverage_end: String,
    #[serde(default)]
    observed_dates: String,
}
#[derive(Deserialize)]
struct CalendarObservanceRule {
    event_id: String,
    display_name: String,
    rule_id: String,
    kind: String,
    month: i64,
    day: i64,
    offset_days: i64,
    tithi_index: i64,
    #[serde(default)]
    nakshatra_index: i64,
    source_ids: String,
}
#[derive(Deserialize)]
struct ThirukanithamProfile {
    profile: String,
    definition_id: String,
    sidereal_definition: String,
    ephemeris_provider: String,
    ephemeris_version: String,
    ephemeris_license: String,
    ephemeris_archive_sha256: String,
    sun_model: String,
    moon_model: String,
    nutation_model: String,
    solar_coordinate_definition: String,
    lunar_coordinate_definition: String,
    sidereal_coordinate_definition: String,
    vara_definition: String,
    time_zone_database_release: String,
    solar_month_rule: String,
    daylight_period_rule: String,
    daylight_period_source: String,
    daylight_period_source_sha256: String,
    rahu_eighth_by_weekday: [i64; 7],
    kuligai_eighth_by_weekday: [i64; 7],
    yamagandam_eighth_by_weekday: [i64; 7],
    horizon_definition: String,
    sources: Vec<String>,
    public_start_year: i64,
    public_end_year: i64,
    solar_year_start: i64,
    solar_year_end: i64,
    tt_minus_utc_millis: i64,
    ut1_minus_utc_assumed_millis: i64,
    ut1_minus_utc_max_abs_millis: i64,
    sunrise_center_altitude_arcminutes: i64,
    refraction_arcminutes: i64,
    solar_semidiameter_arcminutes: i64,
    earth_radius_meters: i64,
    root_scan_step_seconds: i64,
    display_rounding_seconds: i64,
    lahiri_anchor_milliarcseconds: i64,
    lahiri_anchor_jd_centidays: i64,
    lahiri_mean_anchor_microarcseconds: i64,
    precession_picoarcseconds_per_power: [i64; 6],
    precession_epoch_jd_millidays: i64,
    precession_century_days: i64,
    months: Vec<String>,
    tithi_names: Vec<String>,
    nakshatra_names: Vec<String>,
    yoga_names: Vec<String>,
    karana_names: Vec<String>,
    weekdays: Vec<String>,
    regions: Vec<ThirukanithamRegion>,
    stations: Vec<ThirukanithamStation>,
}
#[derive(Deserialize)]
struct ThirukanithamRegion {
    id: String,
    time_zone: String,
    utc_offset_seconds: i64,
    latitude_min_microdegrees: i64,
    latitude_max_microdegrees: i64,
    longitude_min_microdegrees: i64,
    longitude_max_microdegrees: i64,
}
#[derive(Deserialize)]
struct ThirukanithamStation {
    id: String,
    region: String,
    latitude_microdegrees: i64,
    longitude_microdegrees: i64,
    elevation_meters: i64,
    source: String,
}
fn compile_vakya_solar(output: &mut String) {
    let path = "lexicon/calendar-vakya-solar.toml";
    println!("cargo:rerun-if-changed={path}");
    let profile: VakyaSolarProfile =
        toml::from_str(&fs::read_to_string(path).expect("read calendar-vakya-solar.toml"))
            .expect("valid calendar-vakya-solar.toml");
    assert_eq!(
        profile.profile,
        "vakyakarana-1962-laghuprakashika-solar-transits-v1"
    );
    assert_eq!(
        (profile.min_saka_year_elapsed, profile.max_saka_year_elapsed),
        (1869, 1890)
    );
    assert_eq!(profile.saka_to_kali_year, 3179);
    assert_eq!(profile.ahargana_year_days, 365);
    assert_eq!(
        (
            profile.ahargana_quarter_numerator,
            profile.ahargana_quarter_denominator
        ),
        (1, 4)
    );
    assert_eq!(
        (
            profile.ahargana_adjustment_multiplier,
            profile.ahargana_adjustment_subtrahend,
            profile.ahargana_adjustment_denominator
        ),
        (5, 1237, 576)
    );
    assert_eq!(profile.kali_epoch_weekday, "Friday");
    assert_eq!((profile.nadis_per_day, profile.vinadis_per_nadi), (60, 60));
    assert_eq!(
        profile.cara_interval_coefficients,
        [[20, 1], [16, 1], [20, 3]]
    );
    assert!(profile
        .cara_interval_coefficients
        .iter()
        .all(|[numerator, denominator]| *numerator > 0 && *denominator > 0));
    assert_eq!(profile.desantara_yojanas_per_nadi, 55);
    assert_eq!(
        profile.bhujaantara_end_of_rasi_vinadis,
        [16, 7, -5, -15, -21, -21, -14, -6, 4, 14, 20, 21]
    );
    assert_eq!(profile.bhupadi_correction_minutes.len(), 37);
    assert!(profile
        .bhupadi_correction_minutes
        .iter()
        .all(|value| *value >= 0));

    let expected_rasis = [
        "vrishabha",
        "mithuna",
        "karkataka",
        "simha",
        "kanya",
        "tula",
        "vrischika",
        "dhanu",
        "makara",
        "kumbha",
        "mina",
        "mesha",
    ];
    assert_eq!(profile.solar_vakya.len(), expected_rasis.len());
    for (data, expected) in profile.solar_vakya.iter().zip(expected_rasis) {
        assert_eq!(data.rasi, expected, "solar vakya order/name");
        assert!(data.days >= 0);
        assert!((0..profile.nadis_per_day).contains(&data.nadis));
        assert!((0..profile.vinadis_per_nadi).contains(&data.vinadis));
    }

    let gcd = |mut left: i64, mut right: i64| {
        while right != 0 {
            (left, right) = (right, left % right);
        }
        left
    };
    let common_denominator = profile
        .ahargana_quarter_denominator
        .checked_div(gcd(
            profile.ahargana_quarter_denominator,
            profile.ahargana_adjustment_denominator,
        ))
        .and_then(|factor| factor.checked_mul(profile.ahargana_adjustment_denominator))
        .expect("calendar denominator fits");
    let vakyas = profile
        .solar_vakya
        .iter()
        .map(|data| {
            format!(
                "SolarVakya {{rasi: {}, days: {}, nadis: {}, vinadis: {}}}",
                literal(&data.rasi),
                data.days,
                data.nadis,
                data.vinadis
            )
        })
        .collect::<Vec<_>>()
        .join(",");
    let corrections = profile
        .bhupadi_correction_minutes
        .iter()
        .map(i64::to_string)
        .collect::<Vec<_>>()
        .join(",");
    output.push_str(&format!(
        "pub const VAKYA_SOLAR_PROFILE: &str = {};\npub const VAKYA_SOLAR_MIN_SAKA_YEAR: i64 = {};\npub const VAKYA_SOLAR_MAX_SAKA_YEAR: i64 = {};\npub const VAKYA_SOLAR_SAKA_TO_KALI_YEAR: i64 = {};\npub const VAKYA_SOLAR_AHARGANA_YEAR_DAYS: i64 = {};\npub const VAKYA_SOLAR_AHARGANA_QUARTER_NUMERATOR: i64 = {};\npub const VAKYA_SOLAR_AHARGANA_QUARTER_DENOMINATOR: i64 = {};\npub const VAKYA_SOLAR_AHARGANA_ADJUSTMENT_MULTIPLIER: i64 = {};\npub const VAKYA_SOLAR_AHARGANA_ADJUSTMENT_SUBTRAHEND: i64 = {};\npub const VAKYA_SOLAR_AHARGANA_ADJUSTMENT_DENOMINATOR: i64 = {};\npub const VAKYA_SOLAR_AHARGANA_COMMON_DENOMINATOR: i64 = {};\npub const VAKYA_SOLAR_KALI_EPOCH_WEEKDAY: &str = {};\npub const VAKYA_SOLAR_KALI_EPOCH_WEEKDAY_INDEX: usize = 4;\npub const VAKYA_SOLAR_NADIS_PER_DAY: i64 = {};\npub const VAKYA_SOLAR_VINADIS_PER_NADI: i64 = {};\npub const VAKYA_SOLAR_CARA_PROFILE: &str = \"vakyakarana-1962-laghuprakashika-cara-v1\";\npub const VAKYA_SOLAR_CARA_INTERVAL_COEFFICIENTS: &[(i64, i64)] = &[{}];\npub const VAKYA_SOLAR_DESANTARA_PROFILE: &str = \"vakyakarana-1962-laghuprakashika-desantara-v1\";\npub const VAKYA_SOLAR_DESANTARA_YOJANAS_PER_NADI: i64 = {};\npub const VAKYA_SOLAR_VAKYAS: &[SolarVakya] = &[{}];\npub const VAKYA_SOLAR_BHUPADI_CORRECTION_MINUTES: &[i64] = &[{}];\n",
        literal(&profile.profile),
        profile.min_saka_year_elapsed,
        profile.max_saka_year_elapsed,
        profile.saka_to_kali_year,
        profile.ahargana_year_days,
        profile.ahargana_quarter_numerator,
        profile.ahargana_quarter_denominator,
        profile.ahargana_adjustment_multiplier,
        profile.ahargana_adjustment_subtrahend,
        profile.ahargana_adjustment_denominator,
        common_denominator,
        literal(&profile.kali_epoch_weekday),
        profile.nadis_per_day,
        profile.vinadis_per_nadi,
        profile
            .cara_interval_coefficients
            .iter()
            .map(|[numerator, denominator]| format!("({numerator},{denominator})"))
            .collect::<Vec<_>>()
            .join(","),
        profile.desantara_yojanas_per_nadi,
        vakyas,
        corrections
    ));
    let bhujaantara = profile
        .bhujaantara_end_of_rasi_vinadis
        .iter()
        .map(i64::to_string)
        .collect::<Vec<_>>()
        .join(",");
    output.push_str(&format!(
        "pub const VAKYA_SOLAR_BHUJAANTARA_PROFILE: &str = \"vakyakarana-1962-laghuprakashika-bhujaantara-linear-experimental-v1\";\npub const VAKYA_SOLAR_BHUJAANTARA_END_OF_RASI_VINADIS: &[i64] = &[{}];\n",
        bhujaantara
    ));
}

fn compile_vakya_moon(output: &mut String) {
    let path = "lexicon/calendar-vakya-moon.toml";
    println!("cargo:rerun-if-changed={path}");
    let profile: VakyaMoonProfile =
        toml::from_str(&fs::read_to_string(path).expect("read calendar-vakya-moon.toml"))
            .expect("valid calendar-vakya-moon.toml");
    assert_eq!(
        profile.profile,
        "vakyakarana-1962-laghuprakashika-true-moon-v1"
    );
    assert_eq!(profile.kali_epoch_day, 1_600_984);
    assert_eq!(
        (
            profile.cycle_1_days,
            profile.cycle_2_days,
            profile.cycle_3_days
        ),
        (12_372, 3_031, 248)
    );
    assert_eq!((profile.cycle_3_vinadis, profile.cycle_2_vinadis), (32, 8));
    assert_eq!(profile.daily_motion_baseline, [13, 11, 0]);
    assert_eq!(profile.moon_vakya_rasi_degrees_minutes.len(), 248);

    let angle_arcseconds = |parts: [i64; 4]| {
        let [rasis, degrees, minutes, seconds] = parts;
        assert!((0..12).contains(&rasis));
        assert!((0..30).contains(&degrees));
        assert!((0..60).contains(&minutes));
        assert!((0..60).contains(&seconds));
        rasis * 108_000 + degrees * 3_600 + minutes * 60 + seconds
    };
    let moon_vakyas = profile
        .moon_vakya_rasi_degrees_minutes
        .iter()
        .map(|[rasis, degrees, minutes]| {
            assert!((0..12).contains(rasis));
            assert!((0..30).contains(degrees));
            assert!((0..60).contains(minutes));
            rasis * 108_000 + degrees * 3_600 + minutes * 60
        })
        .collect::<Vec<_>>();
    assert_eq!(moon_vakyas[0], 43_380, "first Moon vakya");
    assert_eq!(moon_vakyas[152], 783_360, "Moon vakya 153");
    assert_eq!(moon_vakyas[153], 834_480, "Moon vakya 154");
    assert_eq!(moon_vakyas[246], 56_460, "penultimate Moon vakya");
    assert_eq!(moon_vakyas[247], 99_840, "last Moon vakya");

    assert_eq!(profile.moon_vakya_rasi_degrees_minutes[30], [1, 14, 55]);
    assert_eq!(profile.moon_vakya_rasi_degrees_minutes[82], [0, 13, 15]);
    assert_eq!(profile.moon_vakya_rasi_degrees_minutes[99], [8, 1, 17]);
    assert_eq!(profile.moon_vakya_rasi_degrees_minutes[123], [6, 13, 52]);
    assert_eq!(profile.moon_vakya_rasi_degrees_minutes[147], [4, 26, 17]);
    assert_eq!(profile.moon_vakya_rasi_degrees_minutes[154], [8, 5, 52]);
    assert_eq!(profile.moon_vakya_rasi_degrees_minutes[164], [0, 14, 29]);
    assert_eq!(profile.moon_vakya_rasi_degrees_minutes[206], [6, 27, 53]);
    assert_eq!(profile.moon_vakya_rasi_degrees_minutes[216], [11, 12, 49]);

    let moon_circle_arcseconds = 12 * 108_000;
    let bhavet_sukham_arcseconds = 27 * 3_600 + 44 * 60;
    for number in 1..=124 {
        let complement = 248 - number;
        let pair_sum =
            (moon_vakyas[number - 1] + moon_vakyas[complement - 1]) % moon_circle_arcseconds;
        if number == 100 {
            // Direct printed rows 100 and 148 (pp. 128 and 130) sum to 27°34′,
            // a ten-arcsecond source discrepancy against the p. 134 rule.
            assert_eq!(complement, 148);
            assert_eq!(pair_sum, 27 * 3_600 + 34 * 60);
        } else {
            assert_eq!(
                pair_sum, bhavet_sukham_arcseconds,
                "Moon complement rows {number} and {complement}"
            );
        }
    }

    let values = moon_vakyas
        .iter()
        .map(|value| value.to_string())
        .collect::<Vec<_>>()
        .join(",");
    output.push_str(&format!(
        "pub const VAKYA_MOON_PROFILE: &str = {};\npub const VAKYA_MOON_KALI_EPOCH_DAY: i64 = {};\npub const VAKYA_MOON_CYCLE_1_DAYS: i64 = {};\npub const VAKYA_MOON_CYCLE_2_DAYS: i64 = {};\npub const VAKYA_MOON_CYCLE_3_DAYS: i64 = {};\npub const VAKYA_MOON_CYCLE_1_ARCSECONDS: i64 = {};\npub const VAKYA_MOON_CYCLE_2_ARCSECONDS: i64 = {};\npub const VAKYA_MOON_CYCLE_3_ARCSECONDS: i64 = {};\npub const VAKYA_MOON_DHRUVA_ARCSECONDS: i64 = {};\npub const VAKYA_MOON_DAILY_MOTION_BASELINE_ARCSECONDS: i64 = {};\npub const VAKYA_MOON_CYCLE_3_VINADIS: i64 = {};\npub const VAKYA_MOON_CYCLE_2_VINADIS: i64 = {};\npub const VAKYA_MOON_VAKYAS_ARCSECONDS: &[i64] = &[{}];\n",
        literal(&profile.profile),
        profile.kali_epoch_day,
        profile.cycle_1_days,
        profile.cycle_2_days,
        profile.cycle_3_days,
        angle_arcseconds(profile.cycle_1_angle),
        angle_arcseconds(profile.cycle_2_angle),
        angle_arcseconds(profile.cycle_3_angle),
        angle_arcseconds(profile.dhruva),
        profile.daily_motion_baseline[0] * 3_600
            + profile.daily_motion_baseline[1] * 60
            + profile.daily_motion_baseline[2],
        profile.cycle_3_vinadis,
        profile.cycle_2_vinadis,
        values,
    ));
}

fn rust_string_array(values: &[String]) -> String {
    format!(
        "[{}]",
        values
            .iter()
            .map(|value| format!("{value:?}"))
            .collect::<Vec<_>>()
            .join(", ")
    )
}

fn compile_vakya_civil(output: &mut String) {
    let path = "lexicon/calendar-vakya-civil.toml";
    println!("cargo:rerun-if-changed={path}");
    let profile: VakyaCivilProfile =
        toml::from_str(&fs::read_to_string(path).expect("read calendar-vakya-civil.toml"))
            .expect("valid calendar-vakya-civil.toml");
    assert_eq!(profile.profile, "vakyakarana-1962-laghuprakashika-civil-v1");
    assert_eq!(
        profile.definition_id,
        "vakyakarana-1962-laghuprakashika-civil-ujjain-mean-sunrise-v1"
    );
    assert_eq!(profile.kali_epoch_gregorian_ordinal, -1_132_960);
    assert_eq!(profile.reference_station, "ujjain");
    assert_eq!(profile.mean_sunrise_hour, 6);
    assert_eq!(profile.timezone_offset_seconds, 19_800);
    assert_eq!(profile.vinadi_seconds, 24);
    assert_eq!(profile.seconds_per_day, 86_400);
    assert_eq!(profile.daytime_end_nadi, 30);
    assert_eq!(profile.ist_meridian_longitude_microdegrees, 82_500_000);
    assert_eq!(
        (profile.solar_date_min_year, profile.solar_date_max_year),
        (1, 9999)
    );
    assert_eq!(profile.kolkata_instant_min_year, 1947);
    assert_eq!(profile.colombo_instant_min_year, 2007);
    assert_eq!(profile.timezone_ids, ["Asia/Kolkata", "Asia/Colombo"]);
    assert_eq!(profile.month_names.len(), 12);
    assert!(!profile.source_urls.is_empty());
    let timezones = rust_string_array(&profile.timezone_ids);
    let months = rust_string_array(&profile.month_names);
    let sources = rust_string_array(&profile.source_urls);
    output.push_str(&format!(
        "pub const VAKYA_CIVIL_PROFILE: &str = {};\npub const VAKYA_CIVIL_DEFINITION_ID: &str = {};\npub const VAKYA_CIVIL_KALI_EPOCH_GREGORIAN_ORDINAL: i64 = {};\npub const VAKYA_CIVIL_REFERENCE_STATION: &str = {};\npub const VAKYA_CIVIL_REFERENCE_STATION_LATITUDE_MICRODEGREES: i64 = {};\npub const VAKYA_CIVIL_REFERENCE_STATION_LONGITUDE_MICRODEGREES: i64 = {};\npub const VAKYA_CIVIL_IST_MERIDIAN_LONGITUDE_MICRODEGREES: i64 = {};\npub const VAKYA_CIVIL_MEAN_SUNRISE_HOUR: i64 = {};\npub const VAKYA_CIVIL_TIMEZONE_OFFSET_SECONDS: i64 = {};\npub const VAKYA_CIVIL_VINADI_SECONDS: i64 = {};\npub const VAKYA_CIVIL_SECONDS_PER_DAY: i64 = {};\npub const VAKYA_CIVIL_DAYTIME_END_NADI: i64 = {};\npub const VAKYA_CIVIL_SOLAR_DATE_MIN_YEAR: i64 = {};\npub const VAKYA_CIVIL_SOLAR_DATE_MAX_YEAR: i64 = {};\npub const VAKYA_CIVIL_KOLKATA_INSTANT_MIN_YEAR: i64 = {};\npub const VAKYA_CIVIL_COLOMBO_INSTANT_MIN_YEAR: i64 = {};\npub const VAKYA_CIVIL_TIMEZONE_IDS: &[&str] = &{};\npub const VAKYA_CIVIL_MONTH_NAMES: &[&str] = &{};\npub const VAKYA_CIVIL_SOURCE_URLS: &[&str] = &{};\n",
        literal(&profile.profile),
        literal(&profile.definition_id),
        profile.kali_epoch_gregorian_ordinal,
        literal(&profile.reference_station),
        profile.reference_station_latitude_microdegrees,
        profile.reference_station_longitude_microdegrees,
        profile.ist_meridian_longitude_microdegrees,
        profile.mean_sunrise_hour,
        profile.timezone_offset_seconds,
        profile.vinadi_seconds,
        profile.seconds_per_day,
        profile.daytime_end_nadi,
        profile.solar_date_min_year,
        profile.solar_date_max_year,
        profile.kolkata_instant_min_year,
        profile.colombo_instant_min_year,
        timezones,
        months,
        sources,
    ));
}

fn compile_thirukanitham(output: &mut String) {
    let path = "lexicon/calendar-thirukanitham.toml";
    println!("cargo:rerun-if-changed={path}");
    let profile: ThirukanithamProfile =
        toml::from_str(&fs::read_to_string(path).expect("read calendar-thirukanitham.toml"))
            .expect("valid calendar-thirukanitham.toml");
    assert_eq!(profile.profile, "thirukanitham-calendar-v1");
    assert_eq!(
        profile.definition_id,
        "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2"
    );
    assert_eq!(
        profile.sidereal_definition,
        "lahiri-1956-true-anchor-p03-true-iau1980-v2"
    );
    assert_eq!(profile.ephemeris_provider, "astro");
    assert_eq!(profile.ephemeris_version, "2.0.0");
    assert_eq!(profile.ephemeris_license, "MIT");
    assert_eq!(
        profile.ephemeris_archive_sha256,
        "199632E1A87451CF771DA7ADEBA192CAB923EDE42657AC3DE0133BA6F4AE14BE"
    );
    assert_eq!(profile.sun_model, "VSOP87-D");
    assert_eq!(profile.moon_model, "partial ELP-2000/82");
    assert_eq!(profile.nutation_model, "astro-2.0.0-63-term-iau1980");
    assert!(profile
        .solar_coordinate_definition
        .contains("solar-aberration"));
    assert!(profile
        .solar_coordinate_definition
        .contains("no-separate-light-time"));
    assert!(profile
        .lunar_coordinate_definition
        .contains("no-separate-FK5"));
    assert!(profile
        .sidereal_coordinate_definition
        .contains("true-Lahiri-ayanamsa"));
    assert!(profile
        .sidereal_coordinate_definition
        .contains("same-model-date-nutation"));
    assert!(profile.vara_definition.contains("before-sunrise"));
    assert_eq!(profile.time_zone_database_release, "2026f");
    assert_eq!(
        profile.solar_month_rule,
        "ingress_at_or_before_local_sunset_opens_same_date"
    );
    assert_eq!(
        profile.horizon_definition,
        "apparent_solar_center_altitude_minus_47_arcminutes_with_spherical_elevation_dip"
    );
    assert!(!profile.sources.is_empty());
    assert!(profile
        .sources
        .iter()
        .any(|source| source.contains("astro.com/swisseph")));
    assert!(profile
        .sources
        .iter()
        .any(|source| source.contains("github.com/liberfa/erfa")));
    assert!(profile
        .sources
        .iter()
        .any(|source| source.contains("iauarchive.eso.org/static/resolutions/IAU2006_Resol1.pdf")));
    assert_eq!(
        (profile.public_start_year, profile.public_end_year),
        (2024, 2027)
    );
    assert_eq!(
        (profile.solar_year_start, profile.solar_year_end),
        (2023, 2027)
    );
    assert_eq!(profile.tt_minus_utc_millis, 69_184);
    assert_eq!(profile.ut1_minus_utc_assumed_millis, 0);
    assert_eq!(profile.ut1_minus_utc_max_abs_millis, 900);
    assert_eq!(profile.sunrise_center_altitude_arcminutes, -47);
    assert_eq!(
        profile.sunrise_center_altitude_arcminutes,
        -(profile.refraction_arcminutes + profile.solar_semidiameter_arcminutes)
    );
    assert_eq!(profile.earth_radius_meters, 6_371_000);
    assert_eq!(profile.root_scan_step_seconds, 3_600);
    assert_eq!(profile.display_rounding_seconds, 60);
    assert_eq!(profile.lahiri_anchor_milliarcseconds, 83_700_658);
    assert_eq!(profile.lahiri_anchor_jd_centidays, 243_555_350);
    assert_eq!(profile.lahiri_mean_anchor_microarcseconds, 83_683_889_520);
    assert_eq!(profile.precession_epoch_jd_millidays, 2_451_545_000);
    assert_eq!(profile.precession_century_days, 36_525);
    assert_eq!(
        profile.precession_picoarcseconds_per_power,
        [
            0,
            5_028_796_195_000_000,
            1_105_434_800_000,
            79_640_000,
            -23_857_000,
            -38_300
        ]
    );
    assert_eq!(profile.months.len(), 12);
    assert_eq!(profile.tithi_names.len(), 15);
    assert_eq!(profile.nakshatra_names.len(), 27);
    assert_eq!(profile.yoga_names.len(), 27);
    assert_eq!(profile.karana_names.len(), 11);
    assert_eq!(profile.weekdays.len(), 7);
    assert_eq!(
        profile.daylight_period_rule,
        "south-indian-daylight-eighths-v1"
    );
    assert!(profile.daylight_period_source.contains("printed p. 35"));
    assert_eq!(profile.daylight_period_source_sha256.len(), 64);
    for slots in [
        profile.rahu_eighth_by_weekday,
        profile.kuligai_eighth_by_weekday,
        profile.yamagandam_eighth_by_weekday,
    ] {
        assert!(slots.iter().all(|slot| (1..=8).contains(slot)));
    }
    assert_eq!(profile.regions.len(), 2);
    assert_eq!(profile.stations.len(), 3);

    let tn = &profile.regions[0];
    assert_eq!(tn.id, "TN");
    assert_eq!(tn.time_zone, "Asia/Kolkata");
    assert_eq!(tn.utc_offset_seconds, 19_800);
    assert_eq!(
        (
            tn.latitude_min_microdegrees,
            tn.latitude_max_microdegrees,
            tn.longitude_min_microdegrees,
            tn.longitude_max_microdegrees
        ),
        (8_000_000, 13_700_000, 76_000_000, 80_500_000)
    );
    let sl = &profile.regions[1];
    assert_eq!(sl.id, "SL");
    assert_eq!(sl.time_zone, "Asia/Colombo");
    assert_eq!(sl.utc_offset_seconds, 19_800);
    assert_eq!(
        (
            sl.latitude_min_microdegrees,
            sl.latitude_max_microdegrees,
            sl.longitude_min_microdegrees,
            sl.longitude_max_microdegrees
        ),
        (5_800_000, 9_900_000, 79_400_000, 82_000_000)
    );
    assert!(profile.stations.iter().all(|station| {
        !station.id.is_empty()
            && !station.source.is_empty()
            && matches!(station.region.as_str(), "TN" | "SL")
            && (-100..=3_000).contains(&station.elevation_meters)
    }));
    let jaffna = profile
        .stations
        .iter()
        .find(|station| station.id == "jaffna-geonames-1242833")
        .expect("Jaffna reference station is canonical data");
    assert_eq!(
        (
            jaffna.region.as_str(),
            jaffna.latitude_microdegrees,
            jaffna.longitude_microdegrees,
            jaffna.elevation_meters,
            jaffna.source.as_str()
        ),
        (
            "SL",
            9_668_450,
            80_007_420,
            7,
            "https://www.geonames.org/1242833/jaffna.html"
        )
    );

    output.push_str(&format!(
        "pub(crate) const DRIK_PROFILE_NAME: &str = {:?};\n",
        profile.profile
    ));
    output.push_str(&format!(
        "pub(crate) const DRIK_DEFINITION_ID: &str = {:?};\n",
        profile.definition_id
    ));
    output.push_str(&format!(
        "pub(crate) const DRIK_SIDEREAL_DEFINITION: &str = {:?};\n",
        profile.sidereal_definition
    ));
    for (name, value) in [
        ("DRIK_EPHEMERIS_PROVIDER", &profile.ephemeris_provider),
        ("DRIK_EPHEMERIS_VERSION", &profile.ephemeris_version),
        ("DRIK_EPHEMERIS_LICENSE", &profile.ephemeris_license),
        (
            "DRIK_EPHEMERIS_ARCHIVE_SHA256",
            &profile.ephemeris_archive_sha256,
        ),
        ("DRIK_SUN_MODEL", &profile.sun_model),
        ("DRIK_MOON_MODEL", &profile.moon_model),
        ("DRIK_NUTATION_MODEL", &profile.nutation_model),
        (
            "DRIK_SOLAR_COORDINATE_DEFINITION",
            &profile.solar_coordinate_definition,
        ),
        (
            "DRIK_LUNAR_COORDINATE_DEFINITION",
            &profile.lunar_coordinate_definition,
        ),
        (
            "DRIK_SIDEREAL_COORDINATE_DEFINITION",
            &profile.sidereal_coordinate_definition,
        ),
        ("DRIK_VARA_DEFINITION", &profile.vara_definition),
        (
            "DRIK_TZ_DATABASE_RELEASE",
            &profile.time_zone_database_release,
        ),
        ("DRIK_SOLAR_MONTH_RULE", &profile.solar_month_rule),
        ("DRIK_HORIZON_DEFINITION", &profile.horizon_definition),
    ] {
        output.push_str(&format!("pub(crate) const {name}: &str = {:?};\n", value));
    }
    output.push_str(&format!(
        "pub(crate) const DRIK_SOURCE_URLS: [&str; {}] = {};\n",
        profile.sources.len(),
        rust_string_array(&profile.sources)
    ));
    for (name, value) in [
        ("DRIK_PUBLIC_START_YEAR", profile.public_start_year),
        ("DRIK_PUBLIC_END_YEAR", profile.public_end_year),
        ("DRIK_SOLAR_YEAR_START", profile.solar_year_start),
        ("DRIK_SOLAR_YEAR_END", profile.solar_year_end),
        ("DRIK_TT_MINUS_UTC_MILLIS", profile.tt_minus_utc_millis),
        (
            "DRIK_UT1_MINUS_UTC_ASSUMED_MILLIS",
            profile.ut1_minus_utc_assumed_millis,
        ),
        (
            "DRIK_UT1_MINUS_UTC_MAX_ABS_MILLIS",
            profile.ut1_minus_utc_max_abs_millis,
        ),
        (
            "DRIK_SUNRISE_CENTER_ALTITUDE_ARCMINUTES",
            profile.sunrise_center_altitude_arcminutes,
        ),
        ("DRIK_REFRACTION_ARCMINUTES", profile.refraction_arcminutes),
        (
            "DRIK_SOLAR_SEMIDIAMETER_ARCMINUTES",
            profile.solar_semidiameter_arcminutes,
        ),
        ("DRIK_EARTH_RADIUS_METERS", profile.earth_radius_meters),
        (
            "DRIK_ROOT_SCAN_STEP_SECONDS",
            profile.root_scan_step_seconds,
        ),
        (
            "DRIK_DISPLAY_ROUNDING_SECONDS",
            profile.display_rounding_seconds,
        ),
        (
            "DRIK_LAHIRI_ANCHOR_MILLIARCSECONDS",
            profile.lahiri_anchor_milliarcseconds,
        ),
        (
            "DRIK_LAHIRI_ANCHOR_JD_CENTIDAYS",
            profile.lahiri_anchor_jd_centidays,
        ),
        (
            "DRIK_LAHIRI_MEAN_ANCHOR_MICROARCSECONDS",
            profile.lahiri_mean_anchor_microarcseconds,
        ),
        (
            "DRIK_PRECESSION_EPOCH_JD_MILLIDAYS",
            profile.precession_epoch_jd_millidays,
        ),
        (
            "DRIK_PRECESSION_CENTURY_DAYS",
            profile.precession_century_days,
        ),
    ] {
        output.push_str(&format!("pub(crate) const {name}: i64 = {value};\n"));
    }
    output.push_str(&format!(
        "pub(crate) const DRIK_PRECESSION_PICOARCSECONDS: [i64; 6] = {:?};\n",
        profile.precession_picoarcseconds_per_power
    ));
    for (name, values) in [
        ("DRIK_MONTH_NAMES", &profile.months),
        ("DRIK_TITHI_NAMES", &profile.tithi_names),
        ("DRIK_NAKSHATRA_NAMES", &profile.nakshatra_names),
        ("DRIK_YOGA_NAMES", &profile.yoga_names),
        ("DRIK_KARANA_NAMES", &profile.karana_names),
        ("DRIK_WEEKDAYS", &profile.weekdays),
    ] {
        output.push_str(&format!(
            "pub(crate) const {name}: [&str; {}] = {};\n",
            values.len(),
            rust_string_array(values)
        ));
    }
    output.push_str(&format!(
        "pub(crate) const DRIK_DAYLIGHT_PERIOD_RULE: &str = {:?};\npub(crate) const DRIK_DAYLIGHT_PERIOD_SOURCE: &str = {:?};\npub(crate) const DRIK_DAYLIGHT_PERIOD_SOURCE_SHA256: &str = {:?};\npub(crate) const DRIK_RAHU_EIGHTH_BY_WEEKDAY: [u8; 7] = {:?};\npub(crate) const DRIK_KULIGAI_EIGHTH_BY_WEEKDAY: [u8; 7] = {:?};\npub(crate) const DRIK_YAMAGANDAM_EIGHTH_BY_WEEKDAY: [u8; 7] = {:?};\n",
        profile.daylight_period_rule,
        profile.daylight_period_source,
        profile.daylight_period_source_sha256,
        profile.rahu_eighth_by_weekday.map(|slot| slot as u8),
        profile.kuligai_eighth_by_weekday.map(|slot| slot as u8),
        profile.yamagandam_eighth_by_weekday.map(|slot| slot as u8),
    ));
    output.push_str(
        "pub(crate) const DRIK_REGION_RULES: [(&str, &str, i64, i64, i64, i64, i64); 2] = [\n",
    );
    for region in profile.regions {
        output.push_str(&format!(
            "    ({:?}, {:?}, {}, {}, {}, {}, {}),\n",
            region.id,
            region.time_zone,
            region.utc_offset_seconds,
            region.latitude_min_microdegrees,
            region.latitude_max_microdegrees,
            region.longitude_min_microdegrees,
            region.longitude_max_microdegrees
        ));
    }
    output.push_str("];\n");
    output.push_str(&format!(
        "pub(crate) const DRIK_REFERENCE_STATIONS: [(&str, &str, i64, i64, i64, &str); {}] = [\n",
        profile.stations.len()
    ));
    for station in profile.stations {
        output.push_str(&format!(
            "    ({:?}, {:?}, {}, {}, {}, {:?}),\n",
            station.id,
            station.region,
            station.latitude_microdegrees,
            station.longitude_microdegrees,
            station.elevation_meters,
            station.source
        ));
    }
    output.push_str("];\n");
}

fn compile_solar_year_cycle(output: &mut String) {
    let path = "lexicon/calendar-solar-year-cycle.toml";
    println!("cargo:rerun-if-changed={path}");
    let profile: SolarYearCycleProfile =
        toml::from_str(&fs::read_to_string(path).expect("read calendar-solar-year-cycle.toml"))
            .expect("valid calendar-solar-year-cycle.toml");
    assert_eq!(profile.profile, "south-indian-solar-year-cycle-v1");
    assert_eq!(profile.anchor_solar_year, 187);
    assert_eq!(profile.anchor_cycle_index, 1);
    assert_eq!(profile.cycle_length, 60);
    assert_eq!(profile.cycle_names.len(), profile.cycle_length);
    assert_eq!(profile.sources.len(), 3);
    assert_eq!(profile.source_sha256.len(), 64);
    assert!(profile
        .source_sha256
        .bytes()
        .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase()));
    assert!(profile.source.contains("printed pp. 18-19 / PDF pp. 30-31"));
    assert!(profile.region_scope.contains("Tamil solar-year"));
    for name in &profile.cycle_names {
        assert!(!name.is_empty() && name.is_ascii() && is_nfc(name));
    }
    output.push_str(&format!(
        "pub(crate) const TAMIL_SOLAR_YEAR_CYCLE_SOURCE_ID: &str = {:?};\npub(crate) const TAMIL_SOLAR_YEAR_CYCLE_SOURCE: &str = {:?};\npub(crate) const TAMIL_SOLAR_YEAR_CYCLE_SOURCE_SHA256: &str = {:?};\npub(crate) const TAMIL_SOLAR_YEAR_CYCLE_ANCHOR_YEAR: i64 = {};\npub(crate) const TAMIL_SOLAR_YEAR_CYCLE_ANCHOR_INDEX: i64 = {};\npub(crate) const TAMIL_SOLAR_YEAR_CYCLE_REGION_SCOPE: &str = {:?};\npub(crate) const TAMIL_SOLAR_YEAR_CYCLE_NAMES: [&str; {}] = [{}];\npub(crate) const TAMIL_SOLAR_YEAR_CYCLE_SOURCES: [&str; {}] = [{}];\n",
        profile.source_id,
        profile.source,
        profile.source_sha256,
        profile.anchor_solar_year,
        profile.anchor_cycle_index,
        profile.region_scope,
        profile.cycle_names.len(),
        profile
            .cycle_names
            .iter()
            .map(|value| format!("{value:?}"))
            .collect::<Vec<_>>()
            .join(", "),
        profile.sources.len(),
        profile
            .sources
            .iter()
            .map(|value| format!("{value:?}"))
            .collect::<Vec<_>>()
            .join(", "),
    ));
}

fn compile_calendar_tamil_display(output: &mut String) {
    let path = "lexicon/calendar-tamil-display.toml";
    println!("cargo:rerun-if-changed={path}");
    let profile: CalendarTamilDisplayProfile =
        toml::from_str(&fs::read_to_string(path).expect("read calendar-tamil-display.toml"))
            .expect("valid calendar-tamil-display.toml");
    assert_eq!(profile.profile, "calendar-tamil-display-v1");
    assert_eq!(profile.months_tamil.len(), 12);
    assert_eq!(profile.weekdays_tamil.len(), 7);
    assert_eq!(profile.weekdays_romanized.len(), 7);
    assert_eq!(profile.tithi_names_tamil.len(), 15);
    assert_eq!(profile.nakshatra_names_tamil.len(), 27);
    assert_eq!(profile.yoga_names_tamil.len(), 27);
    assert_eq!(profile.karana_names_tamil.len(), 11);
    assert_eq!(profile.cycle_names_tamil.len(), 60);
    for digest in [
        &profile.tva_source_sha256,
        &profile.cldr_source_sha256,
        &profile.msu_weekday_source_sha256,
        &profile.cycle_romanized_source_sha256,
    ] {
        assert_eq!(digest.len(), 64);
        assert!(digest
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase()));
    }
    for name in profile
        .months_tamil
        .iter()
        .chain(&profile.weekdays_tamil)
        .chain(&profile.weekdays_romanized)
        .chain(&profile.tithi_names_tamil)
        .chain(std::iter::once(&profile.tithi_new_moon_tamil))
        .chain(&profile.nakshatra_names_tamil)
        .chain(&profile.yoga_names_tamil)
        .chain(&profile.karana_names_tamil)
        .chain(&profile.cycle_names_tamil)
    {
        assert!(!name.is_empty() && is_nfc(name));
    }
    output.push_str(&format!(
        "pub(crate) const CALENDAR_TAMIL_DISPLAY_PROFILE: &str = {:?};\npub(crate) const CALENDAR_TVA_SOURCE_URL: &str = {:?};\npub(crate) const CALENDAR_TVA_SOURCE_SHA256: &str = {:?};\npub(crate) const CALENDAR_TVA_SOURCE_LOCATOR: &str = {:?};\npub(crate) const CALENDAR_TVA_REUSE_TERMS_STATUS: &str = {:?};\npub(crate) const CALENDAR_CLDR_SOURCE_URL: &str = {:?};\npub(crate) const CALENDAR_CLDR_SOURCE_SHA256: &str = {:?};\npub(crate) const CALENDAR_CLDR_WEEKDAY_LOCATOR: &str = {:?};\npub(crate) const CALENDAR_MSU_WEEKDAY_SOURCE_URL: &str = {:?};\npub(crate) const CALENDAR_MSU_WEEKDAY_SOURCE_SHA256: &str = {:?};\npub(crate) const CALENDAR_MSU_WEEKDAY_SOURCE_LOCATOR: &str = {:?};\npub(crate) const CALENDAR_MSU_WEEKDAY_SOURCE_LICENSE: &str = {:?};\npub(crate) const CALENDAR_CYCLE_ROMANIZED_SOURCE_ID: &str = {:?};\npub(crate) const CALENDAR_CYCLE_ROMANIZED_SOURCE_SHA256: &str = {:?};\npub(crate) const CALENDAR_CYCLE_TAMIL_CROSSCHECK_URL: &str = {:?};\npub(crate) const CALENDAR_DISPLAY_SCOPE: &str = {:?};\npub(crate) const CALENDAR_KARANA_SOURCE_NOTE: &str = {:?};\n",
        profile.profile,
        profile.tva_source_url,
        profile.tva_source_sha256,
        profile.tva_source_locator,
        profile.tva_reuse_terms_status,
        profile.cldr_source_url,
        profile.cldr_source_sha256,
        profile.cldr_weekday_locator,
        profile.msu_weekday_source_url,
        profile.msu_weekday_source_sha256,
        profile.msu_weekday_source_locator,
        profile.msu_weekday_source_license,
        profile.cycle_romanized_source_id,
        profile.cycle_romanized_source_sha256,
        profile.cycle_tamil_crosscheck_url,
        profile.display_scope,
        profile.karana_source_note,
    ));
    for (constant, values) in [
        ("CALENDAR_MONTH_NAMES_TAMIL", &profile.months_tamil),
        ("CALENDAR_WEEKDAY_NAMES_TAMIL", &profile.weekdays_tamil),
        (
            "CALENDAR_WEEKDAY_NAMES_ROMANIZED",
            &profile.weekdays_romanized,
        ),
        ("CALENDAR_TITHI_NAMES_TAMIL", &profile.tithi_names_tamil),
        (
            "CALENDAR_NAKSHATRA_NAMES_TAMIL",
            &profile.nakshatra_names_tamil,
        ),
        ("CALENDAR_YOGA_NAMES_TAMIL", &profile.yoga_names_tamil),
        ("CALENDAR_KARANA_NAMES_TAMIL", &profile.karana_names_tamil),
        ("CALENDAR_CYCLE_NAMES_TAMIL", &profile.cycle_names_tamil),
    ] {
        output.push_str(&format!(
            "pub(crate) const {constant}: [&str; {}] = [{}];\n",
            values.len(),
            values
                .iter()
                .map(|value| format!("{value:?}"))
                .collect::<Vec<_>>()
                .join(", "),
        ));
    }
    output.push_str(&format!(
        "pub(crate) const CALENDAR_TITHI_NEW_MOON_NAME_TAMIL: &str = {:?};\n",
        profile.tithi_new_moon_tamil
    ));
}

fn compile_calendar_observances(output: &mut String) {
    let path = "lexicon/calendar-observances.toml";
    println!("cargo:rerun-if-changed={path}");
    let profile: CalendarObservancesProfile =
        toml::from_str(&fs::read_to_string(path).expect("read calendar-observances.toml"))
            .expect("valid calendar-observances.toml");
    assert_eq!(
        profile.rule_set_id,
        "thirukanitham-tamil-named-observances-v1"
    );
    assert_eq!(
        profile.profile_definition_id,
        "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2"
    );
    assert_eq!(profile.jurisdiction, "TN");
    assert!(profile.coverage_start_year <= profile.coverage_end_year);
    assert!(!profile.scope_note.is_empty() && is_nfc(&profile.scope_note));
    assert!(!profile.astronomy_note.is_empty() && is_nfc(&profile.astronomy_note));
    assert!(!profile.reuse_terms_status.is_empty() && is_nfc(&profile.reuse_terms_status));

    let mut source_ids = BTreeSet::new();
    let mut source_rows = Vec::new();
    for source in &profile.sources {
        assert!(source_ids.insert(source.id.clone()));
        assert!(source
            .id
            .bytes()
            .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'-'));
        assert!(source.url.starts_with("https://"));
        assert!(!source.locator.is_empty() && is_nfc(&source.locator));
        assert!(
            source.year == 0
                || (profile.coverage_start_year..=profile.coverage_end_year).contains(&source.year)
        );
        assert_eq!(
            source.coverage_start.is_empty(),
            source.coverage_end.is_empty()
        );
        if !source.coverage_start.is_empty() {
            assert!(valid_iso_date(&source.coverage_start));
            assert!(valid_iso_date(&source.coverage_end));
            assert!(source.coverage_start <= source.coverage_end);
        }
        if !source.observed_dates.is_empty() {
            assert!(!source.coverage_start.is_empty());
            let mut observed_dates = BTreeSet::new();
            for observed_date in source.observed_dates.split(',') {
                assert!(valid_iso_date(observed_date));
                assert!(source.coverage_start.as_str() <= observed_date);
                assert!(observed_date <= source.coverage_end.as_str());
                assert!(observed_dates.insert(observed_date));
            }
        }
        if !source.sha256.is_empty() {
            assert_eq!(source.sha256.len(), 64);
            assert!(source
                .sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase()));
        }
        source_rows.push(format!(
            "({:?}, {:?}, {:?}, {:?}, {}i64, {:?}, {:?}, {:?})",
            source.id,
            source.url,
            source.locator,
            source.sha256,
            source.year,
            source.coverage_start,
            source.coverage_end,
            source.observed_dates
        ));
    }
    assert!(!source_rows.is_empty());

    let mut event_ids = BTreeSet::new();
    let mut rule_ids = BTreeSet::new();
    let mut rule_rows = Vec::new();
    for rule in &profile.rules {
        assert!(event_ids.insert(rule.event_id.clone()));
        assert!(rule_ids.insert(rule.rule_id.clone()));
        assert!(!rule.display_name.is_empty() && is_nfc(&rule.display_name));
        assert!(!rule.source_ids.is_empty());
        for source_id in rule.source_ids.split(',') {
            assert!(!source_id.is_empty() && source_ids.contains(source_id));
        }
        match rule.kind.as_str() {
            "solar_month_day" => {
                assert!((1..=12).contains(&rule.month));
                assert!((1..=31).contains(&rule.day));
                assert_eq!(rule.tithi_index, 0);
                assert_eq!(rule.nakshatra_index, 0);
            }
            "tithi_aparahna_then_sunrise" => {
                assert_eq!((rule.month, rule.day, rule.offset_days), (0, 0, 0));
                assert!(matches!(rule.tithi_index, 15 | 30));
                assert_eq!(rule.nakshatra_index, 0);
            }
            "tithi_solar_month_sunrise" => {
                assert_eq!((rule.month, rule.day, rule.offset_days), (1, 0, 0));
                assert_eq!(rule.tithi_index, 15);
                assert_eq!(rule.nakshatra_index, 0);
                assert_eq!(rule.event_id, "chitra_pournami");
                assert_eq!(rule.rule_id, "chithirai_pournami_at_sunrise");
            }
            "tithi_solar_month_brahma_muhurta" => {
                assert_eq!((rule.month, rule.day, rule.offset_days), (7, 0, 0));
                assert_eq!(rule.tithi_index, 29);
                assert_eq!(rule.nakshatra_index, 0);
                assert_eq!(rule.event_id, "deepavali");
                assert_eq!(rule.rule_id, "drik_tn_chaturdashi_brahma_muhurta_unique");
            }
            "tithi_solar_month_first_third" => {
                assert_eq!((rule.month, rule.day, rule.offset_days), (6, 0, 0));
                assert_eq!(rule.tithi_index, 1);
                assert_eq!(rule.nakshatra_index, 0);
                assert_eq!(rule.event_id, "navaratri_ghatasthapana");
                assert_eq!(rule.rule_id, "drik_navaratri_pratipada_first_third_only");
            }
            "tithi_navaratri_navami_sunrise" => {
                assert_eq!((rule.month, rule.day, rule.offset_days), (6, 0, 0));
                assert_eq!(rule.tithi_index, 9);
                assert_eq!(rule.nakshatra_index, 0);
                assert_eq!(rule.event_id, "ayudha_puja");
                assert_eq!(rule.rule_id, "drik_navaratri_navami_at_sunrise_unique");
            }
            "tithi_navaratri_dasara_aparahna" => {
                assert_eq!((rule.month, rule.day, rule.offset_days), (6, 0, 0));
                assert_eq!(rule.tithi_index, 10);
                assert_eq!(rule.nakshatra_index, 21);
                assert_eq!(rule.event_id, "vijayadasami");
                assert_eq!(
                    rule.rule_id,
                    "udyog_smarta_vijayadashami_aparahna_after_navarathiri"
                );
            }
            "tithi_madhyahna_then_start" => {
                assert_eq!((rule.month, rule.day, rule.offset_days), (5, 0, 0));
                assert_eq!(rule.tithi_index, 4);
                assert_eq!(rule.nakshatra_index, 0);
                assert_eq!(rule.event_id, "vinayaka_chaturthi");
                assert_eq!(rule.rule_id, "aavani_shukla_chaturthi_madhyahna_then_start");
            }
            "tithi_nishita_then_sunset" => {
                assert_eq!((rule.month, rule.day, rule.offset_days), (11, 0, 0));
                assert_eq!(rule.tithi_index, 29);
                assert_eq!(rule.nakshatra_index, 0);
                assert_eq!(rule.event_id, "sivarathri");
                assert_eq!(
                    rule.rule_id,
                    "maasi_krishna_chaturdashi_nishita_then_sunset"
                );
            }
            "tithi_arunodaya_defer" => {
                assert_eq!(
                    (rule.month, rule.day, rule.offset_days, rule.tithi_index),
                    (0, 0, 0, 0)
                );
                assert_eq!(rule.nakshatra_index, 0);
                assert_eq!(rule.event_id, "sri_vaishnava_ekadashi");
                assert_eq!(rule.rule_id, "nava_sri_vaishnava_arunodaya_defer");
            }
            "tithi_pradosha_sunset_window" => {
                assert_eq!(
                    (rule.month, rule.day, rule.offset_days, rule.tithi_index),
                    (0, 0, 0, 0)
                );
                assert_eq!(rule.nakshatra_index, 0);
                assert_eq!(rule.event_id, "nava_pradosham");
                assert_eq!(rule.rule_id, "nava_pradosha_sunset_90min_later_if_repeated");
            }
            "tithi_moonrise_first_if_repeated_else_second" => {
                assert_eq!((rule.month, rule.day, rule.offset_days), (0, 0, 0));
                assert_eq!(rule.tithi_index, 19);
                assert_eq!(rule.nakshatra_index, 0);
                assert_eq!(rule.event_id, "sankatahara_chaturthi");
                assert_eq!(
                    rule.rule_id,
                    "dharmasindhu_krishna_chaturthi_moonrise_first_if_repeated_else_second"
                );
            }
            "tithi_nishita_rohini_then_second" => {
                assert_eq!((rule.month, rule.day, rule.offset_days), (0, 0, 0));
                assert_eq!(rule.tithi_index, 23);
                assert_eq!(rule.nakshatra_index, 4);
                assert_eq!(rule.event_id, "krishna_jayanthi");
                assert_eq!(
                    rule.rule_id,
                    "udyog_smarta_janmashtami_nishita_rohini_then_second"
                );
            }
            "nakshatra_sunrise"
            | "nakshatra_arunodaya"
            | "nakshatra_night"
            | "nakshatra_sunset_later_if_repeated" => {
                assert!((1..=12).contains(&rule.month));
                assert_eq!((rule.day, rule.offset_days, rule.tithi_index), (0, 0, 0));
                assert!((1..=27).contains(&rule.nakshatra_index));
            }
            "nakshatra_sunrise_nearest_purnima" => {
                assert_eq!((rule.month, rule.day, rule.offset_days), (9, 0, 0));
                assert_eq!(rule.tithi_index, 15);
                assert_eq!(rule.nakshatra_index, 6);
                assert_eq!(rule.event_id, "arudra_darshan");
                assert_eq!(
                    rule.rule_id,
                    "anudina_margazhi_thiruvathirai_nearest_purnima"
                );
            }
            "nakshatra_sunrise_purnima_then_sunrise" => {
                assert_eq!((rule.month, rule.day, rule.offset_days), (12, 0, 0));
                assert_eq!(rule.tithi_index, 15);
                assert_eq!(rule.nakshatra_index, 12);
                assert_eq!(rule.event_id, "panguni_uthiram");
                assert_eq!(rule.rule_id, "udaya_panguni_uthiram_purnima_then_sunrise");
            }
            "nakshatra_tithi_daytime_then_sunrise" => {
                assert_eq!((rule.month, rule.day, rule.offset_days), (10, 0, 0));
                assert_eq!(rule.tithi_index, 15);
                assert_eq!(rule.nakshatra_index, 8);
                assert_eq!(rule.event_id, "thai_poosam");
                assert_eq!(
                    rule.rule_id,
                    "pujadeep_thai_purnima_pushya_daytime_then_sunrise"
                );
            }
            _ => panic!("unknown calendar observance rule kind: {}", rule.kind),
        }
        rule_rows.push(format!(
            "({:?}, {:?}, {:?}, {:?}, {}u8, {}u8, {}i64, {}u8, {}u8, {:?})",
            rule.event_id,
            rule.display_name,
            rule.rule_id,
            rule.kind,
            rule.month,
            rule.day,
            rule.offset_days,
            rule.tithi_index,
            rule.nakshatra_index,
            rule.source_ids,
        ));
    }
    assert!(!rule_rows.is_empty());

    output.push_str(&format!(
        "pub(crate) const CALENDAR_OBSERVANCES_RULE_SET_ID: &str = {:?};\npub(crate) const CALENDAR_OBSERVANCES_DEFINITION_ID: &str = {:?};\npub(crate) const CALENDAR_OBSERVANCES_START_YEAR: i64 = {};\npub(crate) const CALENDAR_OBSERVANCES_END_YEAR: i64 = {};\npub(crate) const CALENDAR_OBSERVANCES_JURISDICTION: &str = {:?};\npub(crate) const CALENDAR_OBSERVANCES_SCOPE_NOTE: &str = {:?};\npub(crate) const CALENDAR_OBSERVANCES_ASTRONOMY_NOTE: &str = {:?};\npub(crate) const CALENDAR_OBSERVANCES_REUSE_TERMS_STATUS: &str = {:?};\n",
        profile.rule_set_id,
        profile.profile_definition_id,
        profile.coverage_start_year,
        profile.coverage_end_year,
        profile.jurisdiction,
        profile.scope_note,
        profile.astronomy_note,
        profile.reuse_terms_status,
    ));
    output.push_str(&format!(
        "pub(crate) type CalendarObservanceSourceData = (&'static str, &'static str, &'static str, &'static str, i64, &'static str, &'static str, &'static str);\npub(crate) const CALENDAR_OBSERVANCES_SOURCES: &[CalendarObservanceSourceData] = &[{}];\n",
        source_rows.join(",")
    ));
    output.push_str(&format!(
        "pub(crate) type CalendarObservanceRuleData = (&'static str, &'static str, &'static str, &'static str, u8, u8, i64, u8, u8, &'static str);\npub(crate) const CALENDAR_OBSERVANCES_RULES: &[CalendarObservanceRuleData] = &[{}];\n",
        rule_rows.join(",")
    ));
}

fn valid_iso_date(value: &str) -> bool {
    let Some((year, rest)) = value.split_once('-') else {
        return false;
    };
    let Some((month, day)) = rest.split_once('-') else {
        return false;
    };
    if year.len() != 4 || month.len() != 2 || day.len() != 2 {
        return false;
    }
    let (Ok(year), Ok(month), Ok(day)) = (
        year.parse::<i64>(),
        month.parse::<i64>(),
        day.parse::<i64>(),
    ) else {
        return false;
    };
    if !(1..=9999).contains(&year) || !(1..=12).contains(&month) {
        return false;
    }
    let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
    let month_days = match month {
        2 if leap => 29,
        2 => 28,
        4 | 6 | 9 | 11 => 30,
        _ => 31,
    };
    (1..=month_days).contains(&day)
}

fn compile_official_holidays(output: &mut String) {
    let path = "lexicon/calendar-official-holidays.toml";
    println!("cargo:rerun-if-changed={path}");
    let profile: OfficialHolidayProfile =
        toml::from_str(&fs::read_to_string(path).expect("read calendar-official-holidays.toml"))
            .expect("valid calendar-official-holidays.toml");
    assert_eq!(profile.profile, "official-holiday-schedules-v1");
    assert_eq!(profile.schedules.len(), 4);
    let mut schedule_ids = BTreeSet::new();
    let mut schedule_years = BTreeSet::new();
    let mut schedule_rows = Vec::new();
    let mut holiday_rows = Vec::new();
    for schedule in profile.schedules {
        assert!(schedule_ids.insert(schedule.id.clone()));
        assert!(schedule_years.insert((schedule.jurisdiction.clone(), schedule.year)));
        assert!(matches!(schedule.jurisdiction.as_str(), "TN" | "SL"));
        assert!((1..=9999).contains(&schedule.year));
        assert!(schedule.source_url.starts_with("https://"));
        assert_eq!(schedule.reuse_terms_status, "unverified");
        assert!(!schedule.source_id.is_empty() && is_nfc(&schedule.source_id));
        assert!(!schedule.source.is_empty() && is_nfc(&schedule.source));
        assert!(!schedule.scope_note.is_empty() && is_nfc(&schedule.scope_note));
        let digest = if schedule.source_sha256.is_empty() {
            None
        } else {
            assert_eq!(schedule.source_sha256.len(), 64);
            assert!(schedule
                .source_sha256
                .bytes()
                .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase()));
            Some(schedule.source_sha256)
        };
        assert!(!schedule.holidays.is_empty());
        let mut previous_date = (0_i64, 0_i64, 0_i64);
        for holiday in schedule.holidays {
            let parts = holiday.date.split('-').collect::<Vec<_>>();
            assert_eq!(parts.len(), 3);
            assert_eq!(parts[0].len(), 4);
            let year = parts[0].parse::<i64>().expect("holiday year");
            let month = parts[1].parse::<i64>().expect("holiday month");
            let day = parts[2].parse::<i64>().expect("holiday day");
            assert_eq!(year, schedule.year);
            assert!(year >= 1 && (1..=12).contains(&month) && (1..=31).contains(&day));
            let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
            let month_days = match month {
                2 if leap => 29,
                2 => 28,
                4 | 6 | 9 | 11 => 30,
                _ => 31,
            };
            assert!(day <= month_days);
            let date = (year, month, day);
            assert!(date >= previous_date);
            previous_date = date;
            assert!(!holiday.name.is_empty() && is_nfc(&holiday.name));
            assert!(!holiday.categories.is_empty());
            let allowed: &[&str] = if schedule.jurisdiction == "TN" {
                &["state_government", "commercial_banks", "cooperative_banks"]
            } else {
                &["bank", "public", "mercantile"]
            };
            let mut categories = BTreeSet::new();
            for category in &holiday.categories {
                assert!(allowed.contains(&category.as_str()));
                assert!(categories.insert(category.clone()));
            }
            holiday_rows.push(format!(
                "    ({:?}, {}, {}, {}, {:?}, &[{}]),\n",
                schedule.id,
                year,
                month,
                day,
                holiday.name,
                holiday
                    .categories
                    .iter()
                    .map(|category| format!("{category:?}"))
                    .collect::<Vec<_>>()
                    .join(", ")
            ));
        }
        schedule_rows.push(format!(
            "    ({:?}, {:?}, {}, {:?}, {:?}, {:?}, {}, {:?}, {:?}),\n",
            schedule.id,
            schedule.jurisdiction,
            schedule.year,
            schedule.source_id,
            schedule.source,
            schedule.source_url,
            digest
                .map(|value| format!("Some({value:?})"))
                .unwrap_or_else(|| "None".to_owned()),
            schedule.reuse_terms_status,
            schedule.scope_note
        ));
    }
    assert_eq!(
        schedule_years,
        BTreeSet::from([
            ("TN".to_owned(), 2025),
            ("TN".to_owned(), 2026),
            ("SL".to_owned(), 2026),
            ("SL".to_owned(), 2027),
        ])
    );
    output.push_str(&format!(
        "pub(crate) type OfficialHolidayScheduleRow = (&'static str, &'static str, i64, &'static str, &'static str, &'static str, Option<&'static str>, &'static str, &'static str);\npub(crate) type OfficialHolidayRow = (&'static str, i64, i64, i64, &'static str, &'static [&'static str]);\npub(crate) const OFFICIAL_HOLIDAY_SCHEDULES: [OfficialHolidayScheduleRow; {}] = [\n{}];\n",
        schedule_rows.len(),
        schedule_rows.concat()
    ));
    output.push_str(&format!(
        "pub(crate) const OFFICIAL_HOLIDAYS: [OfficialHolidayRow; {}] = [\n{}];\n",
        holiday_rows.len(),
        holiday_rows.concat()
    ));
}

fn main() {
    let mut output = String::new();
    compile_vakya_solar(&mut output);
    compile_vakya_moon(&mut output);
    compile_vakya_civil(&mut output);
    compile_thirukanitham(&mut output);
    compile_solar_year_cycle(&mut output);
    compile_calendar_tamil_display(&mut output);
    compile_calendar_observances(&mut output);
    compile_official_holidays(&mut output);
    fs::write(
        PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR")).join("calendar_tables.rs"),
        output,
    )
    .expect("write calendar tables");
}

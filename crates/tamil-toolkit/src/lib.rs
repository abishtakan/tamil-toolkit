//! Experimental unified entry point for the implemented Tamil modules.
#![forbid(unsafe_code)]

mod calendar_features;

pub use tamil_calendar as calendar;
pub use tamil_codec as codec;
pub use tamil_collate as collate;
pub use tamil_core as core;
pub use tamil_norm as norm;
pub use tamil_numerals as numerals;

use serde_json::{json, Value};

const MAX_SAFE_CALENDAR_JSON_INTEGER: i128 = 9_007_199_254_740_991;

pub(crate) fn calendar_integer(value: &Value) -> Result<i64, String> {
    let number = value.as_number().ok_or(numerals::INTEGER_ERROR)?;
    if let Some(value) = number.as_i64() {
        if i128::from(value).abs() > MAX_SAFE_CALENDAR_JSON_INTEGER {
            return Err("outside supported calendar coverage".into());
        }
        return Ok(value);
    }
    if let Some(value) = number.as_u64() {
        if i128::from(value) > MAX_SAFE_CALENDAR_JSON_INTEGER {
            return Err("outside supported calendar coverage".into());
        }
        return i64::try_from(value).map_err(|_| "outside supported calendar coverage".into());
    }
    if number
        .as_f64()
        .is_some_and(|value| value.abs() > MAX_SAFE_CALENDAR_JSON_INTEGER as f64)
    {
        return Err("outside supported calendar coverage".into());
    }
    Err(numerals::INTEGER_ERROR.into())
}

fn validate_calendar_output(value: &Value) -> Result<(), String> {
    match value {
        Value::Number(number) => {
            let safe = number
                .as_i64()
                .is_some_and(|value| i128::from(value).abs() <= MAX_SAFE_CALENDAR_JSON_INTEGER)
                || number
                    .as_u64()
                    .is_some_and(|value| i128::from(value) <= MAX_SAFE_CALENDAR_JSON_INTEGER);
            if safe {
                Ok(())
            } else {
                Err("outside supported calendar coverage".into())
            }
        }
        Value::Array(values) => {
            for value in values {
                validate_calendar_output(value)?;
            }
            Ok(())
        }
        Value::Object(values) => {
            for value in values.values() {
                validate_calendar_output(value)?;
            }
            Ok(())
        }
        _ => Ok(()),
    }
}

fn calendar_result(result: Result<Value, String>) -> Result<Value, String> {
    let value = result?;
    validate_calendar_output(&value)?;
    Ok(value)
}

pub(crate) fn calendar_exact_object<'a>(
    value: &'a Value,
    fields: &[&str],
    error: &'static str,
) -> Result<&'a serde_json::Map<String, Value>, String> {
    let object = value.as_object().ok_or(error)?;
    if object.len() != fields.len() || fields.iter().any(|field| !object.contains_key(*field)) {
        return Err(error.into());
    }
    Ok(object)
}

pub(crate) fn calendar_date_fields(value: &Value, tamil: bool) -> Result<(i64, i64, i64), String> {
    let names = if tamil {
        ["solar_year", "month", "day"]
    } else {
        ["year", "month", "day"]
    };
    let object = calendar_exact_object(value, &names, "invalid calendar input")?;
    Ok((
        calendar_integer(&object[names[0]])?,
        calendar_integer(&object[names[1]])?,
        calendar_integer(&object[names[2]])?,
    ))
}

pub(crate) fn calendar_context(value: &Value) -> Result<calendar::ThirukanithamContext, String> {
    let names = [
        "region",
        "latitude_microdegrees",
        "longitude_microdegrees",
        "elevation_meters",
        "time_zone",
    ];
    let object = calendar_exact_object(value, &names, "invalid calendar context")?;
    let region = object["region"]
        .as_str()
        .ok_or("invalid calendar context")?;
    let time_zone = object["time_zone"]
        .as_str()
        .ok_or("invalid calendar context")?;
    calendar::ThirukanithamContext::new(
        region,
        calendar_integer(&object["latitude_microdegrees"])?,
        calendar_integer(&object["longitude_microdegrees"])?,
        calendar_integer(&object["elevation_meters"])?,
        time_zone,
    )
}

pub(crate) fn vakya_civil_context(value: &Value) -> Result<calendar::VakyaCivilContext, String> {
    let object = calendar_exact_object(
        value,
        &["reference_station", "time_zone"],
        "invalid calendar context",
    )?;
    let station = object["reference_station"]
        .as_str()
        .ok_or("invalid calendar context")?;
    let time_zone = object["time_zone"]
        .as_str()
        .ok_or("invalid calendar context")?;
    calendar::VakyaCivilContext::new(station, time_zone)
}

pub(crate) const THIRUKANITHAM_DEFINITION: &str =
    "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2";
pub(crate) const VAKYA_CIVIL_DEFINITION: &str =
    "vakyakarana-1962-laghuprakashika-civil-ujjain-mean-sunrise-v1";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum CalendarDefinition {
    Thirukanitham,
    VakyaCivil,
}

pub(crate) fn calendar_definition(value: &Value) -> Result<CalendarDefinition, String> {
    match value.as_str() {
        Some(THIRUKANITHAM_DEFINITION) => Ok(CalendarDefinition::Thirukanitham),
        Some(VAKYA_CIVIL_DEFINITION) => Ok(CalendarDefinition::VakyaCivil),
        _ => Err("unsupported calendar definition".into()),
    }
}

pub(crate) fn calendar_gregorian_date(
    fields: (i64, i64, i64),
) -> Result<numerals::GregorianDate, String> {
    numerals::GregorianDate::new(fields.0, fields.1, fields.2)
        .map_err(|_| "invalid Gregorian date".into())
}

pub(crate) fn calendar_gregorian_json(date: numerals::GregorianDate) -> Value {
    json!({"year":date.year(),"month":date.month(),"day":date.day()})
}

pub(crate) fn calendar_tamil_json(date: calendar::ThirukanithamTamilDate) -> Value {
    json!({"solar_year":date.solar_year,"month":date.month,"month_name":date.month_name,"day":date.day})
}

pub(crate) fn calendar_limb_json(limb: calendar::ThirukanithamLimb) -> Value {
    json!({"index":limb.index,"name":limb.name,"paksha":limb.paksha})
}

pub(crate) fn calendar_limbs_json(limbs: calendar::ThirukanithamLimbs) -> Value {
    json!({
        "tithi":calendar_limb_json(limbs.tithi),
        "nakshatra":calendar_limb_json(limbs.nakshatra),
        "yoga":calendar_limb_json(limbs.yoga),
        "karana":calendar_limb_json(limbs.karana)
    })
}

pub(crate) fn vakya_tamil_json(date: calendar::VakyaCivilTamilDate) -> Value {
    json!({"solar_year":date.solar_year,"month":date.month,"month_name":date.month_name,"day":date.day})
}

pub(crate) fn vakya_limb_json(limb: calendar::VakyaCivilLimb) -> Value {
    json!({"index":limb.index,"name":limb.name,"paksha":limb.paksha})
}

pub(crate) fn vakya_limbs_json(limbs: calendar::VakyaCivilLimbs) -> Value {
    json!({
        "tithi":vakya_limb_json(limbs.tithi),
        "nakshatra":vakya_limb_json(limbs.nakshatra),
        "yoga":vakya_limb_json(limbs.yoga),
        "karana":vakya_limb_json(limbs.karana)
    })
}

fn calendar_profile_info(input: &Value) -> Result<Value, String> {
    let object = calendar_exact_object(input, &["definition_id"], "invalid calendar input")?;
    match calendar_definition(&object["definition_id"])? {
        CalendarDefinition::VakyaCivil => {
            let profile = calendar::vakya_civil_profile_info()?;
            Ok(json!({
                "profile":profile.profile,
                "definition_id":profile.definition_id,
                "coverage":{
                    "gregorian_dates":{"start":calendar_gregorian_json(profile.solar_date_start),"end":calendar_gregorian_json(profile.solar_date_end)},
                    "solar_years":{"start":1,"end":9999,"meaning":"Gregorian year containing the source-model Chithirai 1"},
                    "instant_dates_by_time_zone":[
                        {"time_zone":"Asia/Kolkata","start_date":"1947-01-01","end_date":"9999-12-31"},
                        {"time_zone":"Asia/Colombo","start_date":"2007-01-01","end_date":"9999-12-31"}
                    ],
                    "panchangam_moon_kali_day_start":1600984
                },
                "reference_station":{"id":profile.reference_station,"latitude_microdegrees":profile.latitude_microdegrees,"longitude_microdegrees":profile.longitude_microdegrees,"source":"India Meteorological Department station metadata"},
                "day_boundary":"ujjain_mean_sunrise",
                "epoch":{"kali_day":0,"gregorian_date":"-3101-01-23","astronomical_year":-3101,"weekday":"Friday","reference_station":"ujjain","time":"06:00:00 local mean time","gregorian_ordinal":profile.kali_epoch_ordinal},
                "ahargana_fraction_rounding":{"daytime_end_nadi":profile.daytime_end_nadi,"rule":"omit a daytime new-year fraction; count a nighttime fraction as a full day"},
                "time_zones":[
                    {"id":"Asia/Kolkata","utc_offset_seconds":profile.timezone_utc_offset_seconds,"supported_from":"1947-01-01"},
                    {"id":"Asia/Colombo","utc_offset_seconds":profile.timezone_utc_offset_seconds,"supported_from":"2007-01-01"}
                ],
                "equations":["1962 ahargana rational equation","1962 annual Bhupadi true-Sun correction at 10-day nodes","source mean-sunrise sampling for solar ingress assignment","1962 248/3031/12372-day Candra-vakya true Moon"],
                "precision":{"vinadi_seconds":profile.vinadi_seconds,"time_rounding":"nearest vinadi, ties upward","transition_display":"nearest local minute"},
                "solar_model":{"source_edition":"Vakyakarana with Laghuprakashika (1962)","source_sha256":"27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab","source_pages":"printed pp. 250-256, 267-269; scan PDF pp. 287-293, 304-306","ahargana_equation":"365y + y/4 + (5y - 1237)/576; y = elapsed Saka year + 3179","true_sun":"37 printed Bhupadi corrections, linearly interpolated at 10-day nodes","solar_year_range":{"start":1,"end":9999},"solar_date_range":{"start":calendar_gregorian_json(profile.solar_date_start),"end":calendar_gregorian_json(profile.solar_date_end)}},
                "moon_model":{"source_edition":"Vakyakarana with Laghuprakashika (1962)","source_sha256":"27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab","source_pages":"printed pp. 253-254; scan PDF pp. 290-291","cyclic_periods_kali_days":[12372,3031,248],"coverage_start_kali_day":1600984,"within_day_motion":"printed daily motion scaled to mean-sunrise vinadi"},
                "local_sunrise":{"basis":"Ujjain mean sunrise at 06:00 local mean time","Asia/Kolkata":"06:26:52 at UTC+05:30","Asia/Colombo":"06:26:52 at UTC+05:30","local_horizon_sunrise":"unavailable","reason":"Bhujaantara interpolation parameter is not established by the source evidence"},
                "limitations":["only the Ujjain reference station is supported","true local horizon sunrise and sunset are unavailable","Bhujaantara interpolation remains experimental and is not used","zone offsets are fixed at UTC+05:30 only within the declared v1 periods","five-limb upper coverage is additionally bounded by source equations and safe JSON integers"],
                "sources":profile.sources
            }))
        }
        CalendarDefinition::Thirukanitham => {
            let profile = calendar::thirukanitham_profile_info();
            Ok(json!({
            "profile":profile.profile,
            "definition_id":profile.definition_id,
            "coverage":{"start_date":format!("{:04}-01-01",profile.public_start_year),"end_date":format!("{:04}-12-31",profile.public_end_year)},
            "solar_year":{"start":profile.solar_year_start,"end":profile.solar_year_end,"meaning":"Gregorian year containing Chithirai 1"},
            "ephemeris":{"provider":profile.ephemeris_provider,"version":profile.ephemeris_version,"license":profile.ephemeris_license,"archive_sha256":profile.ephemeris_archive_sha256,"sun_model":profile.sun_model,"moon_model":profile.moon_model,"nutation_model":profile.nutation_model,"solar_coordinate_definition":profile.solar_coordinate_definition,"lunar_coordinate_definition":profile.lunar_coordinate_definition},
            "time_model":{"tt_minus_utc_millis":profile.tt_minus_utc_millis,"ut1_minus_utc_assumed_millis":profile.ut1_minus_utc_assumed_millis,"ut1_minus_utc_max_abs_millis":profile.ut1_minus_utc_max_abs_millis,"time_zone_database_release":profile.time_zone_database_release},
            "sidereal_definition":profile.sidereal_definition,
            "sidereal_coordinate_definition":profile.sidereal_coordinate_definition,
            "sidereal_parameters":{"coordinate_definition":profile.sidereal_coordinate_definition,"true_anchor_milliarcseconds":profile.lahiri_true_anchor_milliarcseconds,"mean_anchor_microarcseconds":profile.lahiri_mean_anchor_microarcseconds,"anchor_jd_centidays":profile.lahiri_anchor_jd_centidays,"p03_picoarcseconds_per_power":profile.precession_picoarcseconds_per_power,"p03_epoch_jd_millidays":profile.precession_epoch_jd_millidays,"p03_century_days":profile.precession_century_days},
            "vara_definition":profile.vara_definition,
            "sunrise":{"center_altitude_arcminutes":profile.sunrise_center_altitude_arcminutes,"refraction_arcminutes":profile.refraction_arcminutes,"solar_semidiameter_arcminutes":profile.solar_semidiameter_arcminutes,"earth_radius_meters":profile.earth_radius_meters,"horizon_definition":profile.horizon_definition},
            "solar_month_rule":profile.solar_month_rule,
            "supported_regions":profile.regions.iter().map(|region| json!({"region":region.region,"time_zone":region.time_zone,"utc_offset_seconds":region.utc_offset_seconds,"latitude_min_microdegrees":region.latitude_min_microdegrees,"latitude_max_microdegrees":region.latitude_max_microdegrees,"longitude_min_microdegrees":region.longitude_min_microdegrees,"longitude_max_microdegrees":region.longitude_max_microdegrees})).collect::<Vec<_>>(),
            "reference_stations":profile.reference_stations.iter().map(|station| json!({"id":station.id,"region":station.region,"latitude_microdegrees":station.latitude_microdegrees,"longitude_microdegrees":station.longitude_microdegrees,"elevation_meters":station.elevation_meters,"source":station.source})).collect::<Vec<_>>(),
            "sources":profile.sources
            }))
        }
    }
}

fn calendar_gregorian_to_tamil(input: &Value) -> Result<Value, String> {
    let object = calendar_exact_object(
        input,
        &["definition_id", "date", "context"],
        "invalid calendar input",
    )?;
    let date_fields = calendar_date_fields(&object["date"], false)?;
    match calendar_definition(&object["definition_id"])? {
        CalendarDefinition::Thirukanitham => {
            let context = calendar_context(&object["context"])?;
            if !(2024..=2027).contains(&date_fields.0) {
                return Err("outside supported calendar coverage".into());
            }
            let date = calendar_gregorian_date(date_fields)?;
            let result = calendar::thirukanitham_gregorian_to_tamil_date(date, context)?;
            Ok(
                json!({"definition_id":result.definition_id,"gregorian_date":calendar_gregorian_json(result.gregorian_date),"tamil_date":calendar_tamil_json(result.tamil_date)}),
            )
        }
        CalendarDefinition::VakyaCivil => {
            let context = vakya_civil_context(&object["context"])?;
            let date = calendar_gregorian_date(date_fields)?;
            let result = calendar::vakya_gregorian_to_tamil_date(date, context)?;
            Ok(
                json!({"definition_id":result.definition_id,"gregorian_date":calendar_gregorian_json(result.gregorian_date),"tamil_date":vakya_tamil_json(result.tamil_date),"reference_station":result.reference_station,"day_boundary":result.day_boundary}),
            )
        }
    }
}

fn calendar_tamil_to_gregorian(input: &Value) -> Result<Value, String> {
    let object = calendar_exact_object(
        input,
        &["definition_id", "date", "context"],
        "invalid calendar input",
    )?;
    let date_fields = calendar_date_fields(&object["date"], true)?;
    match calendar_definition(&object["definition_id"])? {
        CalendarDefinition::Thirukanitham => {
            let context = calendar_context(&object["context"])?;
            if !(2023..=2027).contains(&date_fields.0) {
                return Err("outside supported calendar coverage".into());
            }
            let result = calendar::thirukanitham_tamil_to_gregorian_date(
                date_fields.0,
                date_fields.1,
                date_fields.2,
                context,
            )?;
            Ok(
                json!({"definition_id":result.definition_id,"tamil_date":calendar_tamil_json(result.tamil_date),"gregorian_date":calendar_gregorian_json(result.gregorian_date)}),
            )
        }
        CalendarDefinition::VakyaCivil => {
            let context = vakya_civil_context(&object["context"])?;
            let result = calendar::vakya_tamil_to_gregorian_date(
                date_fields.0,
                date_fields.1,
                date_fields.2,
                context,
            )?;
            Ok(
                json!({"definition_id":result.definition_id,"tamil_date":vakya_tamil_json(result.tamil_date),"gregorian_date":calendar_gregorian_json(result.gregorian_date),"reference_station":result.reference_station,"day_boundary":result.day_boundary}),
            )
        }
    }
}

fn calendar_month_info(input: &Value) -> Result<Value, String> {
    let object = calendar_exact_object(
        input,
        &["definition_id", "solar_year", "month", "context"],
        "invalid calendar input",
    )?;
    let year = calendar_integer(&object["solar_year"])?;
    let month = calendar_integer(&object["month"])?;
    match calendar_definition(&object["definition_id"])? {
        CalendarDefinition::Thirukanitham => {
            let context = calendar_context(&object["context"])?;
            if !(2023..=2027).contains(&year) {
                return Err("outside supported calendar coverage".into());
            }
            let result = calendar::thirukanitham_month_info(year, month, context)?;
            Ok(
                json!({"definition_id":result.definition_id,"solar_year":result.solar_year,"month":result.month,"month_name":result.month_name,"start_date":calendar_gregorian_json(result.start_date),"end_date_exclusive":calendar_gregorian_json(result.end_date_exclusive),"days":result.days}),
            )
        }
        CalendarDefinition::VakyaCivil => {
            let context = vakya_civil_context(&object["context"])?;
            let result = calendar::vakya_month_info(year, month, context)?;
            Ok(
                json!({"definition_id":result.definition_id,"solar_year":result.solar_year,"month":result.month,"month_name":result.month_name,"start_date":calendar_gregorian_json(result.start_date),"end_date_exclusive":calendar_gregorian_json(result.end_date_exclusive),"days":result.days,"reference_station":result.reference_station,"day_boundary":result.day_boundary}),
            )
        }
    }
}

fn calendar_solar_date_json(date: &calendar::CalendarSolarDate) -> Value {
    json!({"solar_year":date.solar_year,"month":date.month,"month_name":date.month_name,"day":date.day})
}

fn calendar_solar_year_cycle_json(info: &calendar::CalendarSolarYearCycleInfo) -> Value {
    json!({
        "solar_year": info.solar_year,
        "cycle_index": info.cycle_index,
        "cycle_name": info.cycle_name,
        "anchor": {
            "solar_year": info.anchor_solar_year,
            "cycle_index": info.anchor_cycle_index,
        },
        "source_id": info.source_id,
        "source": info.source,
        "source_sha256": info.source_sha256,
        "region_scope": info.region_scope,
        "sources": info.sources,
    })
}

fn calendar_tamil_year_cycle_info(input: &Value) -> Result<Value, String> {
    let object = calendar_exact_object(
        input,
        &["definition_id", "solar_year", "context"],
        "invalid calendar input",
    )?;
    let year = calendar_integer(&object["solar_year"])?;
    let definition = calendar_definition(&object["definition_id"])?;
    let definition_id = match definition {
        CalendarDefinition::Thirukanitham => {
            calendar_context(&object["context"])?;
            if !(2023..=2027).contains(&year) {
                return Err("outside supported calendar coverage".into());
            }
            THIRUKANITHAM_DEFINITION
        }
        CalendarDefinition::VakyaCivil => {
            vakya_civil_context(&object["context"])?;
            if !(1..=9_999).contains(&year) {
                return Err("outside supported calendar coverage".into());
            }
            VAKYA_CIVIL_DEFINITION
        }
    };
    let info = calendar::solar_year_cycle_info(year)?;
    let mut result = calendar_solar_year_cycle_json(&info);
    result["definition_id"] = json!(definition_id);
    Ok(result)
}

fn calendar_official_holidays(input: &Value) -> Result<Value, String> {
    let object = calendar_exact_object(input, &["jurisdiction", "year"], "invalid calendar input")?;
    let jurisdiction = object["jurisdiction"]
        .as_str()
        .ok_or("invalid calendar input")?;
    if !matches!(jurisdiction, "TN" | "SL") {
        return Err("unsupported calendar jurisdiction".into());
    }
    let info =
        calendar::calendar_official_holiday_year(jurisdiction, calendar_integer(&object["year"])?)?;
    let holidays = info
        .holidays
        .iter()
        .map(|holiday| {
            json!({
                "date":calendar_gregorian_json(holiday.date),
                "name":holiday.name,
                "categories":holiday.categories,
            })
        })
        .collect::<Vec<_>>();
    Ok(json!({
        "jurisdiction":info.jurisdiction,
        "year":info.year,
        "schedule_id":info.schedule_id,
        "source_id":info.source_id,
        "source":info.source,
        "source_url":info.source_url,
        "source_sha256":info.source_sha256,
        "reuse_terms_status":info.reuse_terms_status,
        "scope_note":info.scope_note,
        "holidays":holidays,
    }))
}

fn calendar_observances(input: &Value) -> Result<Value, String> {
    let object = input.as_object().ok_or("invalid calendar input")?;
    const REQUIRED_FIELDS: [&str; 4] = ["definition_id", "rule_set", "gregorian_year", "context"];
    if REQUIRED_FIELDS
        .iter()
        .any(|field| !object.contains_key(*field))
        || object.len() > REQUIRED_FIELDS.len() + 1
        || object
            .keys()
            .any(|field| !REQUIRED_FIELDS.contains(&field.as_str()) && field != "month")
    {
        return Err("invalid calendar input".into());
    }
    let year = calendar_integer(&object["gregorian_year"])?;
    let month = object
        .get("month")
        .map(|value| {
            let month = calendar_integer(value).map_err(|_| "invalid calendar input")?;
            if !(1..=12).contains(&month) {
                return Err("invalid calendar input".into());
            }
            u8::try_from(month).map_err(|_| "invalid calendar input".to_owned())
        })
        .transpose()?;
    let definition = calendar_definition(&object["definition_id"])?;
    let rule_set = object["rule_set"]
        .as_str()
        .ok_or("invalid calendar input")?;
    if rule_set != "thirukanitham-tamil-named-observances-v1" {
        return Err("unsupported calendar observance rule set".into());
    }
    let info = match definition {
        CalendarDefinition::Thirukanitham => calendar::thirukanitham_observances(
            rule_set,
            year,
            month,
            calendar_context(&object["context"])?,
        )?,
        CalendarDefinition::VakyaCivil => {
            vakya_civil_context(&object["context"])?;
            return Err("observance rule set unsupported for calendar definition".into());
        }
    };
    let context = info.context;
    let sources = info
        .sources
        .iter()
        .map(|source| {
            json!({
                "id":source.id,
                "url":source.url,
                "locator":source.locator,
                "sha256":source.sha256,
                "year":source.year,
            })
        })
        .collect::<Vec<_>>();
    let events = info
        .events
        .iter()
        .map(|event| {
            json!({
                "event_id":event.event_id,
                "display_name":event.display_name,
                "date":calendar_gregorian_json(event.date),
                "rule_id":event.rule_id,
                "tithi_index":event.tithi_index,
                "nakshatra_index":event.nakshatra_index,
                "source_ids":event.source_ids,
            })
        })
        .collect::<Vec<_>>();
    Ok(json!({
        "definition_id":info.definition_id,
        "rule_set_id":info.rule_set_id,
        "gregorian_year":info.gregorian_year,
        "jurisdiction":info.jurisdiction,
        "context":{
            "region":context.region(),
            "latitude_microdegrees":context.latitude_microdegrees(),
            "longitude_microdegrees":context.longitude_microdegrees(),
            "elevation_meters":context.elevation_meters(),
            "time_zone":context.time_zone(),
        },
        "scope_note":info.scope_note,
        "astronomy_note":info.astronomy_note,
        "source_compatibility":info.source_compatibility,
        "reuse_terms_status":info.reuse_terms_status,
        "sources":sources,
        "supported_event_ids":info.supported_event_ids,
        "events":events,
    }))
}

fn calendar_tamil_year_info(input: &Value) -> Result<Value, String> {
    let object = calendar_exact_object(
        input,
        &["definition_id", "solar_year", "context"],
        "invalid calendar input",
    )?;
    let year = calendar_integer(&object["solar_year"])?;
    match calendar_definition(&object["definition_id"])? {
        CalendarDefinition::Thirukanitham => {
            let result = calendar::thirukanitham_solar_year_info(
                year,
                calendar_context(&object["context"])?,
            )?;
            let months = result
                .months
                .iter()
                .map(|month| {
                    json!({
                        "month":month.month,
                        "month_name":month.month_name,
                        "start_date":calendar_gregorian_json(month.start_date),
                        "end_date_exclusive":calendar_gregorian_json(month.end_date_exclusive),
                        "days":month.days,
                    })
                })
                .collect::<Vec<_>>();
            Ok(json!({
                "definition_id":THIRUKANITHAM_DEFINITION,
                "solar_year":result.solar_year,
                "year_cycle":calendar_solar_year_cycle_json(&result.year_cycle),
                "start_date":calendar_gregorian_json(result.start_date),
                "end_date_exclusive":calendar_gregorian_json(result.end_date_exclusive),
                "days":result.days,
                "months":months,
            }))
        }
        CalendarDefinition::VakyaCivil => {
            let result =
                calendar::vakya_solar_year_info(year, vakya_civil_context(&object["context"])?)?;
            let months = result
                .months
                .iter()
                .map(|month| {
                    json!({
                        "month":month.month,
                        "month_name":month.month_name,
                        "start_date":calendar_gregorian_json(month.start_date),
                        "end_date_exclusive":calendar_gregorian_json(month.end_date_exclusive),
                        "days":month.days,
                    })
                })
                .collect::<Vec<_>>();
            Ok(json!({
                "definition_id":VAKYA_CIVIL_DEFINITION,
                "solar_year":result.solar_year,
                "year_cycle":calendar_solar_year_cycle_json(&result.year_cycle),
                "start_date":calendar_gregorian_json(result.start_date),
                "end_date_exclusive":calendar_gregorian_json(result.end_date_exclusive),
                "days":result.days,
                "months":months,
                "reference_station":"ujjain",
                "day_boundary":"ujjain_mean_sunrise",
            }))
        }
    }
}

fn calendar_add_tamil_date(input: &Value) -> Result<Value, String> {
    let object = calendar_exact_object(
        input,
        &[
            "definition_id",
            "date",
            "unit",
            "amount",
            "overflow",
            "context",
        ],
        "invalid calendar input",
    )?;
    let fields = calendar_date_fields(&object["date"], true)?;
    let unit = object["unit"].as_str().ok_or("invalid calendar input")?;
    let amount = calendar_integer(&object["amount"])?;
    let overflow = object["overflow"]
        .as_str()
        .ok_or("invalid calendar input")?;
    match calendar_definition(&object["definition_id"])? {
        CalendarDefinition::Thirukanitham => {
            let result = calendar::thirukanitham_add_solar_date(
                fields.0,
                fields.1,
                fields.2,
                unit,
                amount,
                overflow,
                calendar_context(&object["context"])?,
            )?;
            Ok(json!({
                "definition_id":THIRUKANITHAM_DEFINITION,
                "tamil_date":calendar_solar_date_json(&result.tamil_date),
                "gregorian_date":calendar_gregorian_json(result.gregorian_date),
            }))
        }
        CalendarDefinition::VakyaCivil => {
            let result = calendar::vakya_add_solar_date(
                fields.0,
                fields.1,
                fields.2,
                unit,
                amount,
                overflow,
                vakya_civil_context(&object["context"])?,
            )?;
            Ok(json!({
                "definition_id":VAKYA_CIVIL_DEFINITION,
                "tamil_date":calendar_solar_date_json(&result.tamil_date),
                "gregorian_date":calendar_gregorian_json(result.gregorian_date),
                "reference_station":"ujjain",
                "day_boundary":"ujjain_mean_sunrise",
            }))
        }
    }
}

fn calendar_panchangam_at(input: &Value) -> Result<Value, String> {
    let object = calendar_exact_object(
        input,
        &["definition_id", "instant_unix_seconds", "context"],
        "invalid calendar input",
    )?;
    let instant = calendar_integer(&object["instant_unix_seconds"])?;
    match calendar_definition(&object["definition_id"])? {
        CalendarDefinition::Thirukanitham => {
            let context = calendar_context(&object["context"])?;
            let result = calendar::thirukanitham_panchangam_at(instant, context)?;
            Ok(
                json!({"definition_id":result.definition_id,"local_date":calendar_gregorian_json(result.local_date),"local_time":{"hour":result.local_time.hour,"minute":result.local_time.minute,"second":result.local_time.second},"vara":result.vara,"limbs":calendar_limbs_json(result.limbs)}),
            )
        }
        CalendarDefinition::VakyaCivil => {
            let context = vakya_civil_context(&object["context"])?;
            let result = calendar::vakya_panchangam_at(instant, context)?;
            Ok(
                json!({"definition_id":result.definition_id,"local_date":calendar_gregorian_json(result.local_date),"local_time":{"hour":result.local_time.hour,"minute":result.local_time.minute,"second":result.local_time.second},"vara":result.vara,"limbs":vakya_limbs_json(result.limbs),"reference_station":result.reference_station,"position_basis":"ujjain_mean_solar_time"}),
            )
        }
    }
}

fn calendar_panchangam_day(input: &Value) -> Result<Value, String> {
    let object = calendar_exact_object(
        input,
        &["definition_id", "date", "context"],
        "invalid calendar input",
    )?;
    let fields = calendar_date_fields(&object["date"], false)?;
    match calendar_definition(&object["definition_id"])? {
        CalendarDefinition::Thirukanitham => {
            let context = calendar_context(&object["context"])?;
            if !(2024..=2027).contains(&fields.0) {
                return Err("outside supported calendar coverage".into());
            }
            let date = calendar_gregorian_date(fields)?;
            let result = calendar::thirukanitham_panchangam_day(date, context)?;
            let transitions = result.transitions.iter().map(|event| json!({"limb":event.limb,"from_index":event.from_index,"to_index":event.to_index,"day_offset":event.day_offset,"minute_of_day":event.minute_of_day})).collect::<Vec<_>>();
            Ok(
                json!({"definition_id":result.definition_id,"date":calendar_gregorian_json(result.date),"sunrise_minute_of_day":result.sunrise_minute_of_day,"sunset_minute_of_day":result.sunset_minute_of_day,"vara":result.vara,"limbs_at_sunrise":calendar_limbs_json(result.limbs_at_sunrise),"transitions":transitions}),
            )
        }
        CalendarDefinition::VakyaCivil => {
            let context = vakya_civil_context(&object["context"])?;
            let date = calendar_gregorian_date(fields)?;
            let result = calendar::vakya_panchangam_day(date, context)?;
            let transitions = result.transitions.iter().map(|event| json!({"limb":event.limb,"from_index":event.from_index,"to_index":event.to_index,"day_offset":event.day_offset,"minute_of_day":event.minute_of_day})).collect::<Vec<_>>();
            Ok(
                json!({"definition_id":result.definition_id,"date":calendar_gregorian_json(result.date),"sunrise_minute_of_day":result.sunrise_minute_of_day,"sunrise_basis":result.sunrise_basis,"sunset_minute_of_day":result.sunset_minute_of_day,"sunset_status":result.sunset_status,"vara":result.vara,"limbs_at_sunrise":vakya_limbs_json(result.limbs_at_sunrise),"transitions":transitions}),
            )
        }
    }
}

fn calendar_local_time_from_seconds(seconds: i64) -> Value {
    let seconds = seconds.rem_euclid(86_400);
    json!({
        "hour":seconds / 3_600,
        "minute":seconds % 3_600 / 60,
        "second":seconds % 60,
    })
}

fn calendar_daylight_periods(input: &Value) -> Result<Value, String> {
    let object = calendar_exact_object(
        input,
        &["definition_id", "date", "context"],
        "invalid calendar input",
    )?;
    let date = calendar_gregorian_date(calendar_date_fields(&object["date"], false)?)?;
    match calendar_definition(&object["definition_id"])? {
        CalendarDefinition::Thirukanitham => {
            let result = calendar::thirukanitham_daylight_periods(
                date,
                calendar_context(&object["context"])?,
            )?;
            let intervals = result
                .intervals
                .iter()
                .map(|interval| {
                    json!({
                        "period":interval.period,
                        "eighth_part":interval.eighth_part,
                        "start_local_time":calendar_local_time_from_seconds(interval.start_local_seconds_of_day),
                        "end_local_time":calendar_local_time_from_seconds(interval.end_local_seconds_of_day),
                    })
                })
                .collect::<Vec<_>>();
            Ok(json!({
                "definition_id":result.definition_id,
                "date":calendar_gregorian_json(result.date),
                "weekday":result.weekday,
                "rule_id":result.rule_id,
                "daylight_basis":"computed apparent sunrise to sunset",
                "sunrise_local_time":calendar_local_time_from_seconds(result.sunrise_local_seconds_of_day),
                "sunset_local_time":calendar_local_time_from_seconds(result.sunset_local_seconds_of_day),
                "intervals":intervals,
                "source":result.source,
                "source_sha256":result.source_sha256,
            }))
        }
        CalendarDefinition::VakyaCivil => {
            vakya_civil_context(&object["context"])?;
            Err("source-defined local sunset unavailable for this calendar definition".into())
        }
    }
}

fn calendar_lunar_phase_events(input: &Value) -> Result<Value, String> {
    let object = calendar_exact_object(
        input,
        &["definition_id", "start_unix_seconds", "end_unix_seconds"],
        "invalid calendar input",
    )?;
    if calendar_definition(&object["definition_id"])? != CalendarDefinition::Thirukanitham {
        return Err("unsupported calendar definition".into());
    }
    let start = calendar_integer(&object["start_unix_seconds"])?;
    let end = calendar_integer(&object["end_unix_seconds"])?;
    let events = calendar::thirukanitham_lunar_phase_events(start, end)?
        .into_iter()
        .map(|event| {
            json!({
                "phase":event.phase,
                "ecliptic_longitude_difference_degrees":event.ecliptic_longitude_difference_degrees,
                "utc_minute":{
                    "year":event.utc_minute.year,
                    "month":event.utc_minute.month,
                    "day":event.utc_minute.day,
                    "hour":event.utc_minute.hour,
                    "minute":event.utc_minute.minute
                }
            })
        })
        .collect::<Vec<_>>();
    Ok(json!({
        "definition_id":calendar::thirukanitham_profile_info().definition_id,
        "events":events
    }))
}

pub const OPERATIONS: &[&str] = &[
    "get_letters",
    "normalize_nfc",
    "normalize_nfd",
    "split_uyirmei",
    "compose_uyirmei",
    "inspect_tamil_string",
    "compare",
    "sort_words",
    "sort_key",
    "search_key",
    "to_words",
    "format_currency",
    "currency_to_words",
    "bamini_to_unicode",
    "unicode_to_bamini",
    "anjal_bytes_to_unicode",
    "unicode_to_anjal_bytes",
    "tam_bytes_to_unicode",
    "unicode_to_tam_bytes",
    "tab_bytes_to_unicode",
    "unicode_to_tab_bytes",
    "tscii_bytes_to_unicode",
    "unicode_to_tscii_bytes",
    "lt_tm_codes_to_unicode",
    "lt_tm_text_to_unicode",
    "unicode_to_lt_tm_codes",
    "unicode_to_lt_tm_text",
    "vanavil_codes_to_unicode",
    "vanavil_text_to_unicode",
    "unicode_to_vanavil_codes",
    "unicode_to_vanavil_text",
    "detect_encoding",
    "detect_and_decode",
    "format_fraction",
    "fraction_to_words",
    "fraction_symbol",
    "format_date",
    "convert_digits",
    "parse_decimal",
    "format_decimal",
    "decimal_to_words",
    "ordinal_to_words",
    "digit_sequence_to_words",
    "format_currency_decimal",
    "currency_decimal_to_words",
    "parse_fraction_symbol",
    "symbol_info",
    "format_mixed_fraction",
    "parse_mixed_fraction",
    "format_traditional_integer",
    "parse_traditional_integer",
    "parse_percent",
    "format_percent",
    "ratio_to_percent",
    "percent_to_ratio",
    "format_numeric_range",
    "validate_gregorian_date",
    "parse_gregorian_date",
    "weekday",
    "add_gregorian_date",
    "date_difference",
    "date_interval",
    "vakya_solar_transits",
    "vakya_true_sun_from_mesha_elapsed",
    "vakya_true_moon_from_kali_day",
    "vakya_reduce_to_local_true_sunrise",
    "vakya_cara_from_sayana_sun",
    "vakya_desantara_from_yojana_distance",
    "vakya_bhujaantara_from_true_sun",
    "calendar_profile_info",
    "gregorian_to_tamil_date",
    "tamil_to_gregorian_date",
    "tamil_month_info",
    "tamil_year_info",
    "tamil_year_cycle_info",
    "calendar_official_holidays",
    "calendar_observances",
    "add_tamil_date",
    "panchangam_at",
    "panchangam_day",
    "lunar_phase_events",
    "calendar_daylight_periods",
];

fn string(value: &Value) -> Result<&str, String> {
    value
        .as_str()
        .ok_or_else(|| "expected a string input".to_owned())
}

fn integer(value: &Value, maximum: i64) -> Result<i64, String> {
    // JSON.stringify emits 1 for 1.0, while other serializers keep the .0.
    // Parse whole values identically without floating-point money arithmetic.
    let error = || numerals::INTEGER_ERROR.to_owned();
    let number = value.as_number().ok_or_else(error)?.to_string();
    let parsed = number
        .strip_suffix(".0")
        .unwrap_or(&number)
        .parse::<i64>()
        .map_err(|_| error())?;
    if parsed.unsigned_abs() > maximum as u64 {
        Err(error())
    } else {
        Ok(parsed)
    }
}

fn locale(input: &Value) -> Result<numerals::Locale, String> {
    match input.get("locale") {
        None => Ok(numerals::Locale::TN),
        Some(value) => numerals::Locale::parse(value.as_str().ok_or("unsupported locale")?),
    }
}

fn digit_style(input: &Value) -> Result<numerals::DigitStyle, String> {
    match input.get("digits") {
        None => Ok(numerals::DigitStyle::Latin),
        Some(value) => {
            numerals::DigitStyle::parse(value.as_str().ok_or("unsupported digit style")?)
        }
    }
}

fn numeric_digits(input: &Value) -> Result<&'static str, String> {
    match digit_style(input)? {
        numerals::DigitStyle::Latin => Ok("latin"),
        numerals::DigitStyle::Tamil => Ok("tamil"),
    }
}

fn date_overflow(input: &Value) -> Result<&str, String> {
    match input.get("overflow") {
        None => Ok("reject"),
        Some(value) => value
            .as_str()
            .ok_or_else(|| "unsupported date overflow policy".into()),
    }
}

fn exact_decimal(value: &Value) -> Result<numerals::ExactDecimal, String> {
    let object = value.as_object().ok_or("invalid decimal value")?;
    if object.len() != 3 {
        return Err("invalid decimal value".into());
    }
    let negative = object
        .get("negative")
        .and_then(Value::as_bool)
        .ok_or("invalid decimal value")?;
    let coefficient = object
        .get("coefficient")
        .and_then(Value::as_str)
        .ok_or("invalid decimal value")?
        .to_owned();
    let scale = object
        .get("scale")
        .and_then(Value::as_u64)
        .and_then(|n| u16::try_from(n).ok())
        .ok_or("invalid decimal value")?;
    Ok(numerals::ExactDecimal {
        negative,
        coefficient,
        scale,
    })
}

fn decimal_grouping(input: &Value) -> Result<&str, String> {
    match input.get("grouping") {
        None => Ok("none"),
        Some(value) => value.as_str().ok_or_else(|| "unsupported grouping".into()),
    }
}

fn allow_mixed_digits(input: &Value) -> Result<bool, String> {
    match input.get("allow_mixed_digits") {
        None => Ok(false),
        Some(value) => value
            .as_bool()
            .ok_or_else(|| "invalid decimal string".into()),
    }
}

fn gregorian_date(input: &Value) -> Result<numerals::GregorianDate, String> {
    let component =
        |key: &str| integer(&input[key], 9999).map_err(|_| numerals::INVALID_DATE.to_owned());
    numerals::GregorianDate::new(component("year")?, component("month")?, component("day")?)
}

fn full_integer(value: &Value) -> Result<i64, String> {
    let error = || "Gregorian date arithmetic out of range".to_owned();
    let number = value.as_number().ok_or_else(error)?.to_string();
    number
        .strip_suffix(".0")
        .unwrap_or(&number)
        .parse::<i64>()
        .map_err(|_| error())
}

fn range_endpoint(value: &Value) -> Result<numerals::NumericRangeEndpoint, String> {
    let object = value.as_object().ok_or("invalid numeric range")?;
    match object.get("type").and_then(Value::as_str) {
        Some("decimal") if object.len() == 2 => Ok(numerals::NumericRangeEndpoint::Decimal(
            exact_decimal(object.get("value").ok_or("invalid numeric range")?)
                .map_err(|_| "invalid numeric range")?,
        )),
        Some("fraction") if object.len() == 3 => {
            let numerator = integer(&value["numerator"], numerals::MAX_INTEGER)
                .map_err(|_| "invalid numeric range")?;
            let denominator = integer(&value["denominator"], numerals::MAX_INTEGER)
                .map_err(|_| "invalid numeric range")?;
            if denominator == 0 {
                return Err("invalid numeric range".into());
            }
            Ok(numerals::NumericRangeEndpoint::Fraction {
                numerator,
                denominator: denominator as u64,
            })
        }
        _ => Err("invalid numeric range".into()),
    }
}

fn vakya_solar_transits(input: &Value) -> Result<Value, String> {
    let object = input.as_object().ok_or("invalid calendar input")?;
    if object.len() != 2
        || !object.contains_key("definition_id")
        || !object.contains_key("saka_year_elapsed")
    {
        return Err("invalid calendar input".into());
    }
    let definition_id = object["definition_id"]
        .as_str()
        .ok_or("unsupported calendar definition")?;
    if definition_id != "vakyakarana-1962-laghuprakashika-solar-transits-v1" {
        return Err("unsupported calendar definition".into());
    }
    let saka_year_elapsed = calendar_integer(&object["saka_year_elapsed"])?;
    let year = calendar::vakya_solar_transits(saka_year_elapsed)?;
    Ok(json!({
        "definition_id": year.definition_id,
        "saka_year_elapsed": year.saka_year_elapsed,
        "kali_year": year.kali_year,
        "ahargana": {
            "days": year.ahargana.days,
            "nadi": year.ahargana.nadi,
            "vinadi": year.ahargana.vinadi,
            "weekday": year.ahargana.weekday,
        },
        "transits": year.transits.iter().map(|event| json!({
            "rasi": event.rasi,
            "day_field": event.day_field,
            "weekday": event.weekday,
            "nadi": event.nadi,
            "vinadi": event.vinadi,
        })).collect::<Vec<_>>(),
    }))
}

fn vakya_true_sun_from_mesha_elapsed(input: &Value) -> Result<Value, String> {
    let object = input.as_object().ok_or("invalid calendar input")?;
    if object.len() != 4
        || !object.contains_key("definition_id")
        || !object.contains_key("elapsed_days")
        || !object.contains_key("nadi")
        || !object.contains_key("vinadi")
    {
        return Err("invalid calendar input".into());
    }
    let definition_id = object["definition_id"]
        .as_str()
        .ok_or("unsupported calendar definition")?;
    if definition_id != "vakyakarana-1962-laghuprakashika-solar-transits-v1" {
        return Err("unsupported calendar definition".into());
    }
    let elapsed_days = calendar_integer(&object["elapsed_days"])?;
    let nadi = calendar_integer(&object["nadi"])?;
    let vinadi = calendar_integer(&object["vinadi"])?;
    let result = calendar::vakya_true_sun_from_mesha_elapsed(elapsed_days, nadi, vinadi)?;
    let angle = |value: calendar::DmsAngle| json!({"degrees":value.degrees,"minutes":value.minutes,"seconds":value.seconds});
    Ok(json!({
        "definition_id": result.definition_id,
        "elapsed_from_mesha": {
            "days": result.elapsed_days,
            "nadi": result.nadi,
            "vinadi": result.vinadi,
        },
        "approximate_sun": angle(result.approximate_sun),
        "bhupadi_correction": angle(result.bhupadi_correction),
        "true_sun": angle(result.true_sun),
    }))
}

fn vakya_true_moon_from_kali_day(input: &Value) -> Result<Value, String> {
    let object = input.as_object().ok_or("invalid calendar input")?;
    if object.len() != 2
        || !object.contains_key("definition_id")
        || !object.contains_key("kali_day")
    {
        return Err("invalid calendar input".into());
    }
    let definition_id = object["definition_id"]
        .as_str()
        .ok_or("unsupported calendar definition")?;
    if definition_id != "vakyakarana-1962-laghuprakashika-true-moon-v1" {
        return Err("unsupported calendar definition".into());
    }
    let kali_day = calendar_integer(&object["kali_day"])?;
    let result = calendar::vakya_true_moon_from_kali_day(kali_day)?;
    let rasi_angle = |value: calendar::RasiDmsAngle| json!({"rasi":value.rasi,"degrees":value.degrees,"minutes":value.minutes,"seconds":value.seconds});
    let daily_motion = result.daily_motion;
    Ok(json!({
        "definition_id": result.definition_id,
        "kali_day": result.kali_day,
        "quotients": {
            "period_12372": result.quotient_12372,
            "period_3031": result.quotient_3031,
            "period_248": result.quotient_248
        },
        "moon_vakya_number": result.moon_vakya_number,
        "uncorrected_true_moon": rasi_angle(result.uncorrected_true_moon),
        "daily_motion": {
            "degrees": daily_motion.degrees,
            "minutes": daily_motion.minutes,
            "seconds": daily_motion.seconds
        },
        "vinadi_adjustment": result.vinadi_adjustment,
        "correction_seconds": result.correction_seconds,
        "true_moon": rasi_angle(result.true_moon)
    }))
}

fn vakya_reduce_to_local_true_sunrise(input: &Value) -> Result<Value, String> {
    let object = input.as_object().ok_or("invalid calendar input")?;
    if object.len() != 6
        || !object.contains_key("definition_id")
        || !object.contains_key("true_position")
        || !object.contains_key("daily_motion")
        || !object.contains_key("cara_half_vinadi_tenths")
        || !object.contains_key("desantara_vinadi_tenths")
        || !object.contains_key("bhujaantara_vinadi_tenths")
    {
        return Err("invalid calendar input".into());
    }
    let definition_id = object["definition_id"]
        .as_str()
        .ok_or("unsupported calendar definition")?;
    if definition_id != "vakyakarana-1962-laghuprakashika-local-sunrise-v1" {
        return Err("unsupported calendar definition".into());
    }
    let read_angle_fields = |value: &Value, with_rasi: bool| -> Result<Vec<i64>, String> {
        let angle = value.as_object().ok_or("invalid calendar input")?;
        let names: &[&str] = if with_rasi {
            &["rasi", "degrees", "minutes", "seconds"]
        } else {
            &["degrees", "minutes", "seconds"]
        };
        if angle.len() != names.len() || names.iter().any(|name| !angle.contains_key(*name)) {
            return Err("invalid calendar input".into());
        }
        names
            .iter()
            .map(|name| calendar_integer(&angle[*name]))
            .collect()
    };
    let position = read_angle_fields(&object["true_position"], true)?;
    let daily_motion = read_angle_fields(&object["daily_motion"], false)?;
    let true_position = calendar::RasiDmsAngle {
        rasi: u8::try_from(position[0]).map_err(|_| "invalid calendar angle")?,
        degrees: u8::try_from(position[1]).map_err(|_| "invalid calendar angle")?,
        minutes: u8::try_from(position[2]).map_err(|_| "invalid calendar angle")?,
        seconds: u8::try_from(position[3]).map_err(|_| "invalid calendar angle")?,
    };
    let daily_motion = calendar::DmsAngle {
        degrees: daily_motion[0],
        minutes: u8::try_from(daily_motion[1]).map_err(|_| "invalid calendar angle")?,
        seconds: u8::try_from(daily_motion[2]).map_err(|_| "invalid calendar angle")?,
    };
    let cara = calendar_integer(&object["cara_half_vinadi_tenths"])?;
    let desantara = calendar_integer(&object["desantara_vinadi_tenths"])?;
    let bhujaantara = calendar_integer(&object["bhujaantara_vinadi_tenths"])?;
    let result = calendar::vakya_reduce_to_local_true_sunrise(
        true_position,
        daily_motion,
        cara,
        desantara,
        bhujaantara,
    )?;
    let rasi_angle = |value: calendar::RasiDmsAngle| json!({"rasi":value.rasi,"degrees":value.degrees,"minutes":value.minutes,"seconds":value.seconds});
    Ok(json!({
        "definition_id": result.definition_id,
        "true_position": rasi_angle(result.true_position),
        "daily_motion": {
            "degrees": result.daily_motion.degrees,
            "minutes": result.daily_motion.minutes,
            "seconds": result.daily_motion.seconds
        },
        "adjustment_vinadi_tenths": {
            "cara_half": result.cara_half_vinadi_tenths,
            "desantara": result.desantara_vinadi_tenths,
            "bhujaantara": result.bhujaantara_vinadi_tenths,
            "total": result.total_vinadi_tenths
        },
        "correction_arcseconds": result.correction_arcseconds,
        "local_true_position": rasi_angle(result.local_true_position)
    }))
}

fn vakya_cara_from_sayana_sun(input: &Value) -> Result<Value, String> {
    let object = input.as_object().ok_or("invalid calendar input")?;
    if object.len() != 3
        || !object.contains_key("definition_id")
        || !object.contains_key("sayana_sun")
        || !object.contains_key("equinoctial_shadow_tenths")
    {
        return Err("invalid calendar input".into());
    }
    let definition_id = object["definition_id"]
        .as_str()
        .ok_or("unsupported calendar definition")?;
    if definition_id != "vakyakarana-1962-laghuprakashika-cara-v1" {
        return Err("unsupported calendar definition".into());
    }
    let angle = object["sayana_sun"]
        .as_object()
        .ok_or("invalid calendar input")?;
    if angle.len() != 4
        || !["rasi", "degrees", "minutes", "seconds"]
            .iter()
            .all(|name| angle.contains_key(*name))
    {
        return Err("invalid calendar input".into());
    }
    let read = |field: &str| -> Result<i64, String> { calendar_integer(&angle[field]) };
    let sayana_sun = calendar::RasiDmsAngle {
        rasi: u8::try_from(read("rasi")?).map_err(|_| "invalid calendar angle")?,
        degrees: u8::try_from(read("degrees")?).map_err(|_| "invalid calendar angle")?,
        minutes: u8::try_from(read("minutes")?).map_err(|_| "invalid calendar angle")?,
        seconds: u8::try_from(read("seconds")?).map_err(|_| "invalid calendar angle")?,
    };
    let shadow = calendar_integer(&object["equinoctial_shadow_tenths"])?;
    let result = calendar::vakya_cara_from_sayana_sun(sayana_sun, shadow)?;
    let angle = |value: calendar::RasiDmsAngle| {
        json!({
            "rasi": value.rasi,
            "degrees": value.degrees,
            "minutes": value.minutes,
            "seconds": value.seconds
        })
    };
    Ok(json!({
        "definition_id": result.definition_id,
        "sayana_sun": angle(result.sayana_sun),
        "bhuja": angle(result.bhuja),
        "equinoctial_shadow_tenths": result.equinoctial_shadow_tenths,
        "cara_vinadi_tenths": result.cara_vinadi_tenths
    }))
}

fn vakya_desantara_from_yojana_distance(input: &Value) -> Result<Value, String> {
    let object = input.as_object().ok_or("invalid calendar input")?;
    if object.len() != 2
        || !object.contains_key("definition_id")
        || !object.contains_key("east_west_distance_tenths_yojana")
    {
        return Err("invalid calendar input".into());
    }
    let definition_id = object["definition_id"]
        .as_str()
        .ok_or("unsupported calendar definition")?;
    if definition_id != "vakyakarana-1962-laghuprakashika-desantara-v1" {
        return Err("unsupported calendar definition".into());
    }
    let distance = calendar_integer(&object["east_west_distance_tenths_yojana"])?;
    let result = calendar::vakya_desantara_from_yojana_distance(distance)?;
    Ok(json!({
        "definition_id": result.definition_id,
        "east_west_distance_tenths_yojana": result.east_west_distance_tenths_yojana,
        "desantara_vinadi_tenths": result.desantara_vinadi_tenths
    }))
}

fn vakya_bhujaantara_from_true_sun(input: &Value) -> Result<Value, String> {
    let object = input.as_object().ok_or("invalid calendar input")?;
    if object.len() != 3
        || !object.contains_key("definition_id")
        || !object.contains_key("sun_rasi")
        || !object.contains_key("sun_rasi_progress_arcseconds")
    {
        return Err("invalid calendar input".into());
    }
    let definition_id = object["definition_id"]
        .as_str()
        .ok_or("unsupported calendar definition")?;
    if definition_id != "vakyakarana-1962-laghuprakashika-bhujaantara-linear-experimental-v1" {
        return Err("unsupported calendar definition".into());
    }
    let sun_rasi = calendar_integer(&object["sun_rasi"])?;
    let sun_rasi = u8::try_from(sun_rasi).map_err(|_| "invalid calendar angle")?;
    let progress = calendar_integer(&object["sun_rasi_progress_arcseconds"])?;
    let result = calendar::vakya_bhujaantara_from_true_sun(sun_rasi, progress)?;
    Ok(json!({
        "definition_id": result.definition_id,
        "sun_rasi": result.sun_rasi,
        "sun_rasi_progress_arcseconds": result.sun_rasi_progress_arcseconds,
        "bracketing_endpoint_vinadi": result.bracketing_endpoint_vinadi,
        "bhujaantara_vinadi_tenths": result.bhujaantara_vinadi_tenths
    }))
}

fn cid_codes(input: &Value, name: &str) -> Result<Vec<u16>, String> {
    let error = || format!("expected {name} code array");
    input
        .get("codes")
        .and_then(Value::as_array)
        .ok_or_else(error)?
        .iter()
        .map(|value| {
            let number = value.as_number().ok_or_else(error)?.to_string();
            number
                .strip_suffix(".0")
                .unwrap_or(&number)
                .parse::<u16>()
                .map_err(|_| error())
        })
        .collect()
}

fn codec_error_policy(input: &Value) -> Result<codec::ErrorPolicy, String> {
    match input.get("errors") {
        None => Ok(codec::ErrorPolicy::Strict),
        Some(value) => {
            codec::ErrorPolicy::parse(value.as_str().ok_or("unsupported codec error policy")?)
        }
    }
}

fn extract_byte_array(input: &Value, name: &str) -> Result<Vec<u8>, String> {
    let error = || format!("expected {name} byte array");
    input
        .get("bytes")
        .and_then(Value::as_array)
        .ok_or_else(error)?
        .iter()
        .map(|value| {
            let number = value.as_number().ok_or_else(error)?.to_string();
            let value = number
                .strip_suffix(".0")
                .unwrap_or(&number)
                .parse::<u8>()
                .map_err(|_| error())?;
            Ok(value)
        })
        .collect()
}

fn unified_detect_string(text: &str) -> codec::DetectionResult {
    if text.is_empty() {
        return codec::DetectionResult::uncertain("empty input", Vec::new());
    }
    let non_ws = text.chars().filter(|c| !c.is_whitespace()).count();
    if non_ws < 4 {
        return codec::DetectionResult::uncertain("insufficient input length", Vec::new());
    }

    let bytes_res = codec::detect_encoding(text.as_bytes());
    let utf16_units: Vec<u16> = text.encode_utf16().collect();
    let has_cid_units = utf16_units
        .iter()
        .any(|&c| c > 0x007F || (0xE000..=0xF8FF).contains(&c));

    let cid_res = if has_cid_units {
        codec::detect_encoding_cids(&utf16_units)
    } else {
        codec::DetectionResult::uncertain(
            "no cid code units",
            vec![
                codec::EncodingCandidate {
                    encoding: "lt-tm-cid-v1".into(),
                    confidence: 0.0,
                },
                codec::EncodingCandidate {
                    encoding: "vanavil-avvaiyar-cid-v1".into(),
                    confidence: 0.0,
                },
            ],
        )
    };

    let mut candidates = bytes_res.candidates;
    for cid_cand in cid_res.candidates {
        if !candidates.iter().any(|c| c.encoding == cid_cand.encoding) {
            candidates.push(cid_cand);
        }
    }

    let mut result = codec::DetectionResult::from_scored_candidates(candidates);
    if result.status == codec::DetectionStatus::Uncertain {
        if let Some(r) = bytes_res.reason {
            if r != "low confidence" || result.reason.is_none() {
                result.reason = Some(r);
            }
        }
    }
    result
}

/// Shared dispatcher used by every binding and the oracle CLI.
pub fn execute(request: &Value) -> Result<Value, String> {
    let input = request.get("input").ok_or("missing input")?;
    match request
        .get("op")
        .and_then(Value::as_str)
        .ok_or("missing op")?
    {
        "get_letters" => Ok(json!(core::get_letters(string(input)?))),
        "normalize_nfc" => Ok(json!(norm::normalize_nfc(string(input)?))),
        "normalize_nfd" => Ok(json!(norm::normalize_nfd(string(input)?))),
        "split_uyirmei" => core::split_uyirmei(string(input)?).map(|parts| json!(parts)),
        "compose_uyirmei" => {
            core::compose_uyirmei(string(&input["mei"])?, string(&input["uyir"])?).map(|s| json!(s))
        }
        "inspect_tamil_string" => Ok(json!(core::inspect_tamil_string(string(input)?))),
        "compare" => {
            let order = collate::compare(string(&input["left"])?, string(&input["right"])?);
            Ok(json!(match order {
                std::cmp::Ordering::Less => -1,
                std::cmp::Ordering::Equal => 0,
                std::cmp::Ordering::Greater => 1,
            }))
        }
        "sort_words" => {
            let words = input
                .as_array()
                .ok_or("expected an array of strings")?
                .iter()
                .map(|value| string(value).map(str::to_owned))
                .collect::<Result<Vec<_>, _>>()?;
            Ok(json!(collate::sort_words(&words)))
        }
        "sort_key" => Ok(json!(collate::sort_key(string(input)?))),
        "search_key" => Ok(json!(collate::search_key(string(input)?))),
        "to_words" => {
            let value = integer(&input["value"], numerals::MAX_INTEGER)?;
            numerals::to_words(value, locale(input)?).map(|words| json!(words))
        }
        "convert_digits" => numerals::convert_digits(string(&input["text"])?, string(&input["to"])?).map(|text| json!(text)),
        "parse_decimal" => numerals::parse_decimal(
            string(&input["text"])?,
            string(&input["source_digits"])?,
            decimal_grouping(input)?, allow_mixed_digits(input)?,
        ).map(|value| json!({"negative":value.negative,"coefficient":value.coefficient,"scale":value.scale})),
        "format_decimal" => {
            let value = exact_decimal(&input["value"])?;
            numerals::validate_exact_decimal(&value)?;
            let digits = numeric_digits(input)?;
            numerals::format_decimal(&value,digits,decimal_grouping(input)?).map(|text| json!(text))
        }
        "decimal_to_words" => {
            let value = numerals::parse_decimal(string(&input["text"])?,
                string(&input["source_digits"])?,
                decimal_grouping(input)?,allow_mixed_digits(input)?)?;
            numerals::decimal_to_words(&value,locale(input)?).map(|text| json!(text))
        }
        "ordinal_to_words" => {
            let raw = integer(&input["value"], numerals::MAX_INTEGER).unwrap_or(0);
            if raw <= 0 { return Err("expected a positive integer in the supported range".into()); }
            numerals::ordinal_to_words(raw as u64,locale(input)?).map(|text| json!(text))
        }
        "digit_sequence_to_words" => numerals::digit_sequence_to_words(
            string(&input["text"])?,
            string(&input["source_digits"])?,
            locale(input)?,
        ).map(|text| json!(text)),
        "format_currency_decimal" | "currency_decimal_to_words" => {
            let value = numerals::parse_decimal(string(&input["amount"])?,
                string(&input["source_digits"])?,
                decimal_grouping(input)?,false)?;
            numerals::validate_currency_decimal(&value)?;
            let locale = locale(input)?;
            let currency = numerals::Currency::parse(string(&input["currency"])?)?;
            if request["op"] == "format_currency_decimal" {
                numerals::format_currency_decimal(&value,currency,locale).map(|text| json!(text))
            } else {
                numerals::currency_decimal_to_words(&value,currency,locale).map(|text| json!(text))
            }
        }
        "parse_fraction_symbol" => {
            let value = numerals::parse_fraction_symbol(string(&input["text"])?)?;
            Ok(json!({"numerator":value.numerator(),"denominator":value.denominator()}))
        }
        "symbol_info" => {
            let info = numerals::symbol_info(string(&input["text"])?)?;
            let rational = info.rational.map(|(numerator,denominator)| json!({"numerator":numerator,"denominator":denominator}));
            Ok(json!({"codepoint":info.codepoint,"name":info.name,"kind":info.kind,"rational":rational,
                "canonical_alternative":info.canonical_alternative,"source_version":info.source_version}))
        }
        "format_mixed_fraction" => {
            let number = |name:&str| input.get(name).and_then(Value::as_u64).ok_or("invalid mixed fraction".to_owned());
            let value = numerals::MixedFraction { negative:input.get("negative").and_then(Value::as_bool).ok_or("invalid mixed fraction")?,
                whole:number("whole")?, numerator:number("numerator")?, denominator:number("denominator")? };
            numerals::validate_mixed_fraction(&value)?;
            let digits = numeric_digits(input)?;
            numerals::format_mixed_fraction(&value,digits).map(|text| json!(text))
        }
        "parse_mixed_fraction" => {
            let value = numerals::parse_mixed_fraction(string(&input["text"])?,
                string(&input["source_digits"])?)?;
            Ok(json!({"negative":value.negative,"whole":value.whole,"numerator":value.numerator,"denominator":value.denominator}))
        }
        "format_traditional_integer" => {
            let value = integer(&input["value"],99_999_999).map_err(|_| "expected a traditional Tamil integer in the supported range")?;
            numerals::format_traditional_integer(value).map(|text| json!(text))
        }
        "parse_traditional_integer" => numerals::parse_traditional_integer(string(&input["text"])?) .map(|value| json!(value)),
        "parse_percent" => numerals::parse_percent(string(&input["text"])?,
            string(&input["source_digits"])?,decimal_grouping(input)?)
            .map(|value| json!({"negative":value.negative,"coefficient":value.coefficient,"scale":value.scale})),
        "format_percent" => {
            let value = exact_decimal(&input["value"])?;
            numerals::validate_exact_decimal(&value)?;
            numerals::format_percent(&value,numeric_digits(input)?,decimal_grouping(input)?)
                .map(|text| json!(text))
        }
        "ratio_to_percent" | "percent_to_ratio" => {
            let value = exact_decimal(&input["value"])?;
            let result = if request["op"] == "ratio_to_percent" { numerals::ratio_to_percent(&value) } else { numerals::percent_to_ratio(&value) }?;
            Ok(json!({"negative":result.negative,"coefficient":result.coefficient,"scale":result.scale}))
        }
        "format_numeric_range" => {
            let start = range_endpoint(&input["start"])?;
            let end = range_endpoint(&input["end"])?;
            let start_inclusive = input.get("start_inclusive").and_then(Value::as_bool).ok_or("invalid numeric range")?;
            let end_inclusive = input.get("end_inclusive").and_then(Value::as_bool).ok_or("invalid numeric range")?;
            let separator = input.get("separator").and_then(Value::as_str).ok_or("invalid numeric range")?;
            numerals::validate_numeric_range(&start,&end,separator)?;
            let digits = numeric_digits(input)?;
            numerals::format_numeric_range(&start,&end,start_inclusive,end_inclusive,separator,
                digits).map(|text| json!(text))
        }
        "validate_gregorian_date" => numerals::validate_gregorian_date(
            integer(&input["year"],9999).map_err(|_| numerals::INVALID_DATE)?,
            integer(&input["month"],9999).map_err(|_| numerals::INVALID_DATE)?,
            integer(&input["day"],9999).map_err(|_| numerals::INVALID_DATE)?,
        ).map(|valid| json!(valid)),
        "parse_gregorian_date" => numerals::parse_gregorian_date(string(&input["text"])?) .map(|date| json!({"year":date.year(),"month":date.month(),"day":date.day()})),
        "weekday" => Ok(json!(numerals::weekday(gregorian_date(input)?))),
        "add_gregorian_date" => {
            let date = gregorian_date(input)?;
            let unit = input.get("unit").and_then(Value::as_str).ok_or("unsupported date unit")?;
            let amount = full_integer(&input["amount"])?;
            let overflow = date_overflow(input)?;
            numerals::add_gregorian_date(date,unit,amount,overflow).map(|result| json!({"year":result.year(),"month":result.month(),"day":result.day()}))
        }
        "date_difference" => {
            let start = gregorian_date(&input["start"])?;
            let end = gregorian_date(&input["end"])?;
            Ok(json!(numerals::date_difference(start,end)))
        }
        "date_interval" => {
            let start = numerals::parse_gregorian_date(string(&input["start"])?)?;
            let end = numerals::parse_gregorian_date(string(&input["end"])?)?;
            let (start,end,inclusive_days) = numerals::date_interval(start,end)?;
            Ok(json!({"start":start,"end":end,"inclusive_days":inclusive_days}))
        }
        "vakya_solar_transits" => calendar_result(vakya_solar_transits(input)),
        "vakya_true_sun_from_mesha_elapsed" => {
            calendar_result(vakya_true_sun_from_mesha_elapsed(input))
        }
        "vakya_true_moon_from_kali_day" => calendar_result(vakya_true_moon_from_kali_day(input)),
        "vakya_reduce_to_local_true_sunrise" => {
            calendar_result(vakya_reduce_to_local_true_sunrise(input))
        }
        "vakya_cara_from_sayana_sun" => calendar_result(vakya_cara_from_sayana_sun(input)),
        "vakya_desantara_from_yojana_distance" => {
            calendar_result(vakya_desantara_from_yojana_distance(input))
        }
        "vakya_bhujaantara_from_true_sun" => {
            calendar_result(vakya_bhujaantara_from_true_sun(input))
        }
        "calendar_profile_info" => calendar_result(calendar_profile_info(input)),
        "calendar_display_info" => {
            calendar_result(calendar_features::calendar_display_info(input))
        }
        "format_tamil_date" => calendar_result(calendar_features::format_tamil_date(input)),
        "compare_calendar_profiles" => {
            calendar_result(calendar_features::compare_calendar_profiles(input))
        }
        "thiruvalluvar_year_info" => {
            calendar_result(calendar_features::thiruvalluvar_year_info(input))
        }
        "gregorian_to_tamil_date" => calendar_result(calendar_gregorian_to_tamil(input)),
        "tamil_to_gregorian_date" => calendar_result(calendar_tamil_to_gregorian(input)),
        "tamil_month_info" => calendar_result(calendar_month_info(input)),
        "tamil_year_info" => calendar_result(calendar_tamil_year_info(input)),
        "tamil_year_cycle_info" => calendar_result(calendar_tamil_year_cycle_info(input)),
        "calendar_official_holidays" => calendar_result(calendar_official_holidays(input)),
        "calendar_observances" => calendar_result(calendar_observances(input)),
        "add_tamil_date" => calendar_result(calendar_add_tamil_date(input)),
        "panchangam_at" => calendar_result(calendar_panchangam_at(input)),
        "panchangam_day" => calendar_result(calendar_panchangam_day(input)),
        "lunar_phase_events" => calendar_result(calendar_lunar_phase_events(input)),
        "calendar_daylight_periods" => calendar_result(calendar_daylight_periods(input)),
        "format_currency" | "currency_to_words" => {
            let value = integer(&input["amount_minor"], numerals::MAX_MINOR)?;
            let locale = locale(input)?;
            let currency = numerals::Currency::parse(
                input["currency"].as_str().ok_or("unsupported currency")?,
            )?;
            if request["op"] == "format_currency" {
                numerals::format_currency(value, currency, locale).map(|s| json!(s))
            } else {
                numerals::currency_to_words(value, currency, locale).map(|s| json!(s))
            }
        }
        "bamini_to_unicode" => {
            let text = string(&input["text"])?;
            let policy = match input.get("errors") {
                None => codec::ErrorPolicy::Strict,
                Some(value) => codec::ErrorPolicy::parse(
                    value.as_str().ok_or("unsupported codec error policy")?,
                )?,
            };
            codec::bamini_to_unicode(text, policy).map(|text| json!(text))
        }
        "unicode_to_bamini" => {
            codec::unicode_to_bamini(string(&input["text"])?).map(|text| json!(text))
        }
        "lt_tm_codes_to_unicode" => {
            codec::lt_tm_codes_to_unicode(&cid_codes(input, "LT-TM")?, codec_error_policy(input)?)
                .map(|text| json!(text))
        }
        "lt_tm_text_to_unicode" => {
            codec::lt_tm_text_to_unicode(string(&input["text"])?, codec_error_policy(input)?)
                .map(|text| json!(text))
        }
        "unicode_to_lt_tm_codes" => {
            codec::unicode_to_lt_tm_codes(string(&input["text"])?).map(|codes| json!(codes))
        }
        "unicode_to_lt_tm_text" => {
            codec::unicode_to_lt_tm_text(string(&input["text"])?).map(|text| json!(text))
        }
        "vanavil_codes_to_unicode" => codec::vanavil_codes_to_unicode(
            &cid_codes(input, "Vanavil")?,
            codec_error_policy(input)?,
        )
        .map(|text| json!(text)),
        "vanavil_text_to_unicode" => {
            codec::vanavil_text_to_unicode(string(&input["text"])?, codec_error_policy(input)?)
                .map(|text| json!(text))
        }
        "unicode_to_vanavil_codes" => {
            codec::unicode_to_vanavil_codes(string(&input["text"])?).map(|codes| json!(codes))
        }
        "unicode_to_vanavil_text" => {
            codec::unicode_to_vanavil_text(string(&input["text"])?).map(|text| json!(text))
        }
        "unicode_to_anjal_bytes" => {
            codec::unicode_to_anjal_bytes(string(&input["text"])?).map(|bytes| json!(bytes))
        }
        "unicode_to_tam_bytes" => {
            codec::unicode_to_tam_bytes(string(&input["text"])?).map(|bytes| json!(bytes))
        }
        "unicode_to_tab_bytes" => {
            codec::unicode_to_tab_bytes(string(&input["text"])?).map(|bytes| json!(bytes))
        }
        "unicode_to_tscii_bytes" => {
            codec::unicode_to_tscii_bytes(string(&input["text"])?).map(|bytes| json!(bytes))
        }
        "tscii_bytes_to_unicode"
        | "tab_bytes_to_unicode"
        | "tam_bytes_to_unicode"
        | "anjal_bytes_to_unicode" => {
            let operation = request["op"].as_str().expect("validated op");
            let error = || {
                match operation {
                    "tab_bytes_to_unicode" => "expected TAB byte array",
                    "tam_bytes_to_unicode" => "expected TAM byte array",
                    "anjal_bytes_to_unicode" => "expected ANJAL byte array",
                    _ => "expected TSCII byte array",
                }
                .to_owned()
            };
            let bytes = input
                .get("bytes")
                .and_then(Value::as_array)
                .ok_or_else(error)?
                .iter()
                .map(|value| {
                    let number = value.as_number().ok_or_else(error)?.to_string();
                    let value = number
                        .strip_suffix(".0")
                        .unwrap_or(&number)
                        .parse::<u8>()
                        .map_err(|_| error())?;
                    Ok(value)
                })
                .collect::<Result<Vec<_>, String>>()?;
            match operation {
                "tab_bytes_to_unicode" => codec::tab_bytes_to_unicode(&bytes),
                "tam_bytes_to_unicode" => codec::tam_bytes_to_unicode(&bytes),
                "anjal_bytes_to_unicode" => codec::anjal_bytes_to_unicode(&bytes),
                _ => codec::tscii_bytes_to_unicode(&bytes),
            }
            .map(|text| json!(text))
        }
        "detect_encoding" => {
            let res = if input.get("bytes").is_some() {
                let bytes = extract_byte_array(input, "detect_encoding")?;
                codec::detect_encoding(&bytes)
            } else if input.get("codes").is_some() {
                let codes = cid_codes(input, "detect_encoding")?;
                codec::detect_encoding_cids(&codes)
            } else if input.get("text").is_some() {
                let text = string(&input["text"])?;
                unified_detect_string(text)
            } else {
                return Err("detect_encoding requires 'bytes', 'codes', or 'text'".into());
            };
            serde_json::to_value(&res).map_err(|e| e.to_string())
        }
        "detect_and_decode" => {
            if input.get("bytes").is_some() {
                let bytes = extract_byte_array(input, "detect_and_decode")?;
                codec::detect_and_decode(&bytes).map(|text| json!(text))
            } else if input.get("text").is_some() {
                let text = string(&input["text"])?;
                let res = unified_detect_string(text);
                if res.status == codec::DetectionStatus::Detected {
                    match res.encoding.as_deref() {
                        Some("utf-8") => Ok(json!(norm::normalize_nfc(text))),
                        Some("bamini-v1") => {
                            codec::bamini_to_unicode(text, codec::ErrorPolicy::Strict)
                                .map(|t| json!(t))
                        }
                        Some("tscii-1.7-v1") => {
                            codec::tscii_bytes_to_unicode(text.as_bytes()).map(|t| json!(t))
                        }
                        Some("tab-v1") => {
                            codec::tab_bytes_to_unicode(text.as_bytes()).map(|t| json!(t))
                        }
                        Some("tam-v1") => {
                            codec::tam_bytes_to_unicode(text.as_bytes()).map(|t| json!(t))
                        }
                        Some("anjal-v1") => {
                            codec::anjal_bytes_to_unicode(text.as_bytes()).map(|t| json!(t))
                        }
                        Some("lt-tm-cid-v1") => {
                            codec::lt_tm_text_to_unicode(text, codec::ErrorPolicy::Strict)
                                .map(|t| json!(t))
                        }
                        Some("vanavil-avvaiyar-cid-v1") => {
                            codec::vanavil_text_to_unicode(text, codec::ErrorPolicy::Strict)
                                .map(|t| json!(t))
                        }
                        Some(other) => Err(format!("unsupported decoding profile: {other}")),
                        None => Err("missing detected encoding profile".into()),
                    }
                } else {
                    Err(format!(
                        "uncertain encoding: {}",
                        res.reason.as_deref().unwrap_or("low confidence")
                    ))
                }
            } else {
                Err("detect_and_decode requires 'bytes' or 'text'".into())
            }
        }
        "format_fraction" | "fraction_to_words" | "fraction_symbol" => {
            let value = numerals::Fraction::new(
                integer(&input["numerator"], numerals::MAX_INTEGER)?,
                integer(&input["denominator"], numerals::MAX_INTEGER)?,
            )?;
            match request["op"].as_str().expect("validated op") {
                "format_fraction" => {
                    Ok(json!(numerals::format_fraction(value, digit_style(input)?)))
                }
                "fraction_to_words" => {
                    numerals::fraction_to_words(value, locale(input)?).map(|text| json!(text))
                }
                _ => numerals::fraction_symbol(value).map(|text| json!(text)),
            }
        }
        "format_date" => {
            let component = |key: &str| {
                integer(&input[key], 9999).map_err(|_| numerals::INVALID_DATE.to_owned())
            };
            let date = numerals::GregorianDate::new(
                component("year")?,
                component("month")?,
                component("day")?,
            )?;
            let locale = locale(input)?;
            let style = match input.get("style") {
                None => numerals::DateStyle::Long,
                Some(value) => {
                    numerals::DateStyle::parse(value.as_str().ok_or("unsupported date style")?)?
                }
            };
            Ok(json!(numerals::format_date(
                date,
                locale,
                style,
                digit_style(input)?
            )))
        }
        op => Err(format!("unsupported operation: {op}")),
    }
}

pub fn execute_json(request: &str) -> Result<String, String> {
    let request = serde_json::from_str(request).map_err(|e| e.to_string())?;
    execute(&request).map(|result| result.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn errors_are_explicit() {
        for request in [
            json!({}),
            json!({"op":"to_words","input":1000}),
            json!({"op":"get_letters","input":1}),
        ] {
            assert!(execute(&request).is_err());
        }
        assert!(execute_json("invalid JSON").is_err());
    }
}

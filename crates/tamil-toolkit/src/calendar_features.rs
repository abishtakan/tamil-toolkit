use crate::{
    calendar_context, calendar_date_fields, calendar_definition, calendar_exact_object,
    calendar_gregorian_date, calendar_gregorian_json, calendar_integer, numerals, calendar,
    vakya_civil_context, CalendarDefinition, THIRUKANITHAM_DEFINITION, VAKYA_CIVIL_DEFINITION,
};
use serde_json::{json, Value};

struct DisplayRequest {
    date: numerals::GregorianDate,
    context_value: Value,
    context: DisplayContext,
    script: String,
    digits: String,
    names: calendar::CalendarDisplayNames,
}

enum DisplayContext {
    Thirukanitham(calendar::ThirukanithamContext),
    VakyaCivil(calendar::VakyaCivilContext),
}

struct SolarDisplayDate {
    solar_year: i64,
    month: u8,
    month_name: &'static str,
    day: i64,
    definition_id: &'static str,
    model_sources: Vec<&'static str>,
    solar_month_basis: &'static str,
    day_boundary: &'static str,
    position_basis: &'static str,
}

fn parse_display_request(input: &Value, include_style: bool) -> Result<DisplayRequest, String> {
    let fields: &[&str] = if include_style {
        &[
            "definition_id",
            "date",
            "context",
            "script",
            "digits",
            "style",
        ]
    } else {
        &["definition_id", "date", "context", "script", "digits"]
    };
    let object = calendar_exact_object(input, fields, "invalid calendar input")?;
    let definition = calendar_definition(&object["definition_id"])?;
    let context_value = object["context"].clone();
    let context = match definition {
        CalendarDefinition::Thirukanitham => {
            DisplayContext::Thirukanitham(calendar_context(&object["context"])?)
        }
        CalendarDefinition::VakyaCivil => {
            DisplayContext::VakyaCivil(vakya_civil_context(&object["context"])?)
        }
    };
    let date = calendar_gregorian_date(calendar_date_fields(&object["date"], false)?)?;
    let script = object["script"]
        .as_str()
        .ok_or("unsupported calendar display script")?
        .to_owned();
    let names = calendar::calendar_display_names(&script)?;
    let digits = object["digits"]
        .as_str()
        .ok_or("unsupported digit style")?
        .to_owned();
    numerals::convert_digits("", &digits)?;
    Ok(DisplayRequest {
        date,
        context_value,
        context,
        script,
        digits,
        names,
    })
}

fn solar_display_date(request: &DisplayRequest) -> Result<SolarDisplayDate, String> {
    match &request.context {
        DisplayContext::Thirukanitham(context) => {
            let converted =
                calendar::thirukanitham_gregorian_to_tamil_date(request.date, *context)?;
            let profile = calendar::thirukanitham_profile_info();
            Ok(SolarDisplayDate {
                solar_year: converted.tamil_date.solar_year,
                month: converted.tamil_date.month,
                month_name: converted.tamil_date.month_name,
                day: i64::from(converted.tamil_date.day),
                definition_id: converted.definition_id,
                model_sources: profile.sources,
                solar_month_basis: profile.solar_month_rule,
                day_boundary: "computed_local_apparent_sunrise_for_panchangam_day",
                position_basis: "geocentric_apparent_solar_and_lunar_longitudes",
            })
        }
        DisplayContext::VakyaCivil(context) => {
            let converted = calendar::vakya_gregorian_to_tamil_date(request.date, *context)?;
            let profile = calendar::vakya_civil_profile_info()?;
            Ok(SolarDisplayDate {
                solar_year: converted.tamil_date.solar_year,
                month: converted.tamil_date.month,
                month_name: converted.tamil_date.month_name,
                day: converted.tamil_date.day,
                definition_id: converted.definition_id,
                model_sources: profile.sources,
                solar_month_basis: "1962 source-model ingress assigned at the first Ujjain mean sunrise at or after crossing",
                day_boundary: converted.day_boundary,
                position_basis: "ujjain_mean_solar_time",
            })
        }
    }
}

fn weekday_index(weekday: &str) -> Result<usize, String> {
    [
        "sunday",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
    ]
    .iter()
    .position(|day| *day == weekday.to_ascii_lowercase())
    .ok_or("invalid calendar weekday".into())
}

fn format_solar_date(
    date: &SolarDisplayDate,
    date_weekday_index: usize,
    names: &calendar::CalendarDisplayNames,
    digits: &str,
    style: &str,
) -> Result<String, String> {
    let month = names
        .months
        .get(usize::from(date.month - 1))
        .ok_or("outside supported calendar coverage")?;
    let day = numerals::convert_digits(&date.day.to_string(), digits)?;
    let year = numerals::convert_digits(&date.solar_year.to_string(), digits)?;
    match style {
        "day_month_year" => Ok(format!("{day} {month} {year}")),
        "weekday_day_month_year" => {
            let weekday = names
                .weekdays
                .get(date_weekday_index)
                .ok_or("invalid calendar weekday")?;
            Ok(format!("{weekday}, {day} {month} {year}"))
        }
        _ => Err("unsupported calendar date style".into()),
    }
}

pub(crate) fn format_tamil_date(input: &Value) -> Result<Value, String> {
    let request = parse_display_request(input, true)?;
    let object = input.as_object().expect("display input was validated");
    let style = object["style"]
        .as_str()
        .ok_or("unsupported calendar date style")?;
    let date = solar_display_date(&request)?;
    let weekday = weekday_index(numerals::weekday(request.date))?;
    format_solar_date(&date, weekday, &request.names, &request.digits, style)
        .map(|text| json!(text))
}

fn limb_display_json(
    limb: Value,
    kind: &str,
    names: &calendar::CalendarDisplayNames,
) -> Result<Value, String> {
    let index = limb
        .get("index")
        .and_then(Value::as_u64)
        .and_then(|value| usize::try_from(value).ok())
        .ok_or("invalid calendar limb")?;
    let romanized_name = limb
        .get("name")
        .and_then(Value::as_str)
        .ok_or("invalid calendar limb")?;
    let name = match kind {
        "tithi" if index == 30 => names.new_moon_tithi,
        "tithi" => names
            .tithis
            .get((index - 1) % 15)
            .copied()
            .ok_or("invalid calendar limb")?,
        "nakshatra" => names
            .nakshatras
            .get(index.checked_sub(1).ok_or("invalid calendar limb")?)
            .copied()
            .ok_or("invalid calendar limb")?,
        "yoga" => names
            .yogas
            .get(index.checked_sub(1).ok_or("invalid calendar limb")?)
            .copied()
            .ok_or("invalid calendar limb")?,
        "karana" => {
            let roman_index = names
                .romanized_karanas
                .iter()
                .position(|name| *name == romanized_name)
                .ok_or("invalid calendar limb")?;
            names.karanas[roman_index]
        }
        _ => return Err("invalid calendar limb".into()),
    };
    Ok(json!({
        "index":index,
        "name":name,
        "romanized_name":romanized_name,
        "paksha":limb.get("paksha").cloned().unwrap_or(Value::Null)
    }))
}

fn display_sources(names: &calendar::CalendarDisplayNames, profile_sources: &[&str]) -> Value {
    json!({
        "display_lexicon_profile":names.profile_id,
        "tamil_calendar_names":{
            "source_url":names.tamil_source_url,
            "source_sha256":names.tamil_source_sha256,
            "source_locator":names.tamil_source_locator,
            "reuse_terms_status":names.tamil_reuse_terms_status
        },
        "tamil_weekdays":{
            "source_url":names.weekday_source_url,
            "source_sha256":names.weekday_source_sha256,
            "source_locator":names.weekday_source_locator
        },
        "romanized_weekdays":{
            "source_url":names.weekday_romanization_source_url,
            "source_sha256":names.weekday_romanization_source_sha256,
            "source_locator":names.weekday_romanization_source_locator,
            "license":names.weekday_romanization_license
        },
        "romanized_profile_labels":{
            "policy":"existing selected-profile month and limb names are returned unchanged; this display layer adds no transliteration mapping"
        },
        "romanized_cycle_names":{
            "source_id":names.cycle_romanized_source_id,
            "source_sha256":names.cycle_romanized_source_sha256,
            "crosscheck_url":names.cycle_tamil_crosscheck_url
        },
        "profile_sources":profile_sources,
        "regional_scope":names.regional_scope,
        "karana_source_note":names.karana_source_note
    })
}

pub(crate) fn calendar_display_info(input: &Value) -> Result<Value, String> {
    let request = parse_display_request(input, false)?;
    let date = solar_display_date(&request)?;
    let cycle = calendar::solar_year_cycle_info(date.solar_year)?;
    let weekday = weekday_index(numerals::weekday(request.date))?;
    let month_name = request
        .names
        .months
        .get(usize::from(date.month - 1))
        .ok_or("outside supported calendar coverage")?;
    let cycle_name = request
        .names
        .year_cycles
        .get(usize::from(cycle.cycle_index - 1))
        .ok_or("outside supported calendar coverage")?;
    let (panchangam, panchangam_json, profile_name) = match &request.context {
        DisplayContext::Thirukanitham(context) => {
            let day = calendar::thirukanitham_panchangam_day(request.date, *context)?;
            let vara_index = weekday_index(day.vara)?;
            let displayed = json!({
                "tithi":limb_display_json(crate::calendar_limb_json(day.limbs_at_sunrise.tithi),"tithi",&request.names)?,
                "nakshatra":limb_display_json(crate::calendar_limb_json(day.limbs_at_sunrise.nakshatra),"nakshatra",&request.names)?,
                "yoga":limb_display_json(crate::calendar_limb_json(day.limbs_at_sunrise.yoga),"yoga",&request.names)?,
                "karana":limb_display_json(crate::calendar_limb_json(day.limbs_at_sunrise.karana),"karana",&request.names)?
            });
            (
                json!({"vara":day.vara,"display_vara":request.names.weekdays[vara_index],"limbs_at_sunrise":displayed}),
                json!({"sunrise_minute_of_day":day.sunrise_minute_of_day,"sunset_minute_of_day":day.sunset_minute_of_day,"transitions":day.transitions.iter().map(|item|json!({"limb":item.limb,"from_index":item.from_index,"to_index":item.to_index,"minute_of_day":item.minute_of_day})).collect::<Vec<_>>()}),
                "thirukanitham",
            )
        }
        DisplayContext::VakyaCivil(context) => {
            let day = calendar::vakya_panchangam_day(request.date, *context)?;
            let vara_index = weekday_index(day.vara)?;
            let displayed = json!({
                "tithi":limb_display_json(crate::vakya_limb_json(day.limbs_at_sunrise.tithi),"tithi",&request.names)?,
                "nakshatra":limb_display_json(crate::vakya_limb_json(day.limbs_at_sunrise.nakshatra),"nakshatra",&request.names)?,
                "yoga":limb_display_json(crate::vakya_limb_json(day.limbs_at_sunrise.yoga),"yoga",&request.names)?,
                "karana":limb_display_json(crate::vakya_limb_json(day.limbs_at_sunrise.karana),"karana",&request.names)?
            });
            (
                json!({"vara":day.vara,"display_vara":request.names.weekdays[vara_index],"limbs_at_sunrise":displayed}),
                json!({"sunrise_minute_of_day":day.sunrise_minute_of_day,"sunrise_basis":day.sunrise_basis,"sunset_status":day.sunset_status,"transitions":day.transitions.iter().map(|item|json!({"limb":item.limb,"from_index":item.from_index,"to_index":item.to_index,"day_offset":item.day_offset,"minute_of_day":item.minute_of_day})).collect::<Vec<_>>()}),
                "vakyakarana",
            )
        }
    };
    let weekday_name = request
        .names
        .weekdays
        .get(weekday)
        .ok_or("invalid calendar weekday")?;
    let displayed_date = format_solar_date(
        &date,
        weekday,
        &request.names,
        &request.digits,
        "weekday_day_month_year",
    )?;
    Ok(json!({
        "definition_id":date.definition_id,
        "profile":profile_name,
        "context":request.context_value,
        "gregorian_date":calendar_gregorian_json(request.date),
        "display":{"script":request.script,"digits":request.digits,"formatted_date":displayed_date},
        "tamil_date":{"solar_year":date.solar_year,"month":date.month,"day":date.day,"romanized_month_name":date.month_name,"display_month_name":month_name},
        "weekday":{"index":weekday,"display_name":weekday_name,"basis":"Gregorian civil date"},
        "year_cycle":{"cycle_index":cycle.cycle_index,"romanized_name":cycle.cycle_name,"display_name":cycle_name,"anchor":{"solar_year":cycle.anchor_solar_year,"cycle_index":cycle.anchor_cycle_index},"source_id":cycle.source_id,"source_sha256":cycle.source_sha256,"region_scope":cycle.region_scope},
        "calendar_basis":{"solar_month_rule":date.solar_month_basis,"day_boundary":date.day_boundary,"position_basis":date.position_basis},
        "panchangam_day":panchangam,
        "panchangam_basis":panchangam_json,
        "sources":display_sources(&request.names,&date.model_sources)
    }))
}

fn context_json(context: &Value) -> Value {
    context.clone()
}

fn profile_provenance(
    definition: CalendarDefinition,
) -> Result<(String, Vec<&'static str>), String> {
    match definition {
        CalendarDefinition::Thirukanitham => {
            let profile = calendar::thirukanitham_profile_info();
            Ok((
                "Thirukanitham apparent-position profile evaluated at the supplied TN/SL coordinates and civil zone".into(),
                profile.sources,
            ))
        }
        CalendarDefinition::VakyaCivil => {
            let profile = calendar::vakya_civil_profile_info()?;
            Ok((
                "1962 Vakyakarana/Laghuprakashika equations; Ujjain mean-solar-time positions with the supplied Kolkata or Colombo civil label".into(),
                profile.sources,
            ))
        }
    }
}

fn compare_solar_dates(left: Value, right: Value) -> Vec<String> {
    ["solar_year", "month", "day"]
        .into_iter()
        .filter(|field| left.get(*field) != right.get(*field))
        .map(|field| format!("solar_date.{field}"))
        .collect()
}

fn add_if_different(fields: &mut Vec<String>, path: &str, left: &Value, right: &Value) {
    if left != right {
        fields.push(path.to_owned());
    }
}

pub(crate) fn compare_calendar_profiles(input: &Value) -> Result<Value, String> {
    let object = input.as_object().ok_or("invalid calendar input")?;
    let has_date = object.contains_key("date");
    let has_instant = object.contains_key("instant_unix_seconds");
    let expected_len = 2 + usize::from(has_date) + usize::from(has_instant);
    if object.len() != expected_len
        || !object.contains_key("thirukanitham_context")
        || !object.contains_key("vakya_context")
        || has_date == has_instant
    {
        return Err("invalid calendar input".into());
    }
    let thirukanitham_context = calendar_context(&object["thirukanitham_context"])?;
    let vakya_context = vakya_civil_context(&object["vakya_context"])?;
    let (thirukanitham_basis, thirukanitham_sources) =
        profile_provenance(CalendarDefinition::Thirukanitham)?;
    let (vakya_basis, vakya_sources) = profile_provenance(CalendarDefinition::VakyaCivil)?;
    let thirukanitham_context_value = context_json(&object["thirukanitham_context"]);
    let vakya_context_value = context_json(&object["vakya_context"]);
    if has_date {
        let date = calendar_gregorian_date(calendar_date_fields(&object["date"], false)?)?;
        let thirukanitham =
            calendar::thirukanitham_gregorian_to_tamil_date(date, thirukanitham_context)?;
        let vakya = calendar::vakya_gregorian_to_tamil_date(date, vakya_context)?;
        let thirukanitham_solar = json!({
            "solar_year":thirukanitham.tamil_date.solar_year,
            "month":thirukanitham.tamil_date.month,
            "day":thirukanitham.tamil_date.day
        });
        let vakya_solar = json!({
            "solar_year":vakya.tamil_date.solar_year,
            "month":vakya.tamil_date.month,
            "day":vakya.tamil_date.day
        });
        let differences = compare_solar_dates(thirukanitham_solar.clone(), vakya_solar.clone());
        return Ok(json!({
            "comparison_basis":"same_gregorian_civil_date",
            "moment":{"date":calendar_gregorian_json(date)},
            "profiles":{
                "thirukanitham":{"definition_id":THIRUKANITHAM_DEFINITION,"context":thirukanitham_context_value,"semantic_basis":thirukanitham_basis,"sources":thirukanitham_sources,"result":{"gregorian_date":calendar_gregorian_json(date),"solar_date":thirukanitham_solar,"month_name":thirukanitham.tamil_date.month_name}},
                "vakya_civil":{"definition_id":VAKYA_CIVIL_DEFINITION,"context":vakya_context_value,"semantic_basis":vakya_basis,"sources":vakya_sources,"result":{"gregorian_date":calendar_gregorian_json(date),"solar_date":vakya_solar,"month_name":vakya.tamil_date.month_name,"reference_station":vakya.reference_station,"day_boundary":vakya.day_boundary}}
            },
            "differing_fields":differences,
            "accuracy_assessment":"not_assessed"
        }));
    }

    let instant = calendar_integer(&object["instant_unix_seconds"])?;
    let thirukanitham = calendar::thirukanitham_panchangam_at(instant, thirukanitham_context)?;
    let vakya = calendar::vakya_panchangam_at(instant, vakya_context)?;
    let thirukanitham_result = json!({
        "definition_id":thirukanitham.definition_id,
        "local_date":calendar_gregorian_json(thirukanitham.local_date),
        "local_time":{"hour":thirukanitham.local_time.hour,"minute":thirukanitham.local_time.minute,"second":thirukanitham.local_time.second},
        "vara":thirukanitham.vara,
        "limbs":crate::calendar_limbs_json(thirukanitham.limbs)
    });
    let vakya_result = json!({
        "definition_id":vakya.definition_id,
        "local_date":calendar_gregorian_json(vakya.local_date),
        "local_time":{"hour":vakya.local_time.hour,"minute":vakya.local_time.minute,"second":vakya.local_time.second},
        "vara":vakya.vara,
        "limbs":crate::vakya_limbs_json(vakya.limbs),
        "reference_station":vakya.reference_station,
        "position_basis":vakya.position_basis
    });
    let mut differences = Vec::new();
    for field in ["local_date", "local_time", "vara"] {
        add_if_different(
            &mut differences,
            field,
            &thirukanitham_result[field],
            &vakya_result[field],
        );
    }
    for limb in ["tithi", "nakshatra", "yoga", "karana"] {
        for field in ["index", "paksha"] {
            add_if_different(
                &mut differences,
                &format!("limbs.{limb}.{field}"),
                &thirukanitham_result["limbs"][limb][field],
                &vakya_result["limbs"][limb][field],
            );
        }
    }
    Ok(json!({
        "comparison_basis":"same_utc_instant",
        "moment":{"instant_unix_seconds":instant},
        "profiles":{
            "thirukanitham":{"definition_id":THIRUKANITHAM_DEFINITION,"context":thirukanitham_context_value,"semantic_basis":thirukanitham_basis,"sources":thirukanitham_sources,"result":thirukanitham_result},
            "vakya_civil":{"definition_id":VAKYA_CIVIL_DEFINITION,"context":vakya_context_value,"semantic_basis":vakya_basis,"sources":vakya_sources,"result":vakya_result}
        },
        "differing_fields":differences,
        "accuracy_assessment":"not_assessed"
    }))
}

pub(crate) fn thiruvalluvar_year_info(input: &Value) -> Result<Value, String> {
    const CONVENTION_ID: &str = "tn-thiruvalluvar-thai1-thirukanitham-v1";
    let object = calendar_exact_object(
        input,
        &["convention_id", "date", "context"],
        "invalid calendar input",
    )?;
    if object["convention_id"].as_str() != Some(CONVENTION_ID) {
        return Err("unsupported Thiruvalluvar year convention".into());
    }
    let context = calendar_context(&object["context"])?;
    if context.region() != "TN" {
        return Err("unsupported region".into());
    }
    let fields = calendar_date_fields(&object["date"], false)?;
    if !(2025..=2027).contains(&fields.0) {
        return Err("outside supported calendar coverage".into());
    }
    let date = calendar_gregorian_date(fields)?;

    // Thai month 10 starts in the solar year preceding this Gregorian year.
    // The output is deliberately a named Thirukanitham profile convention,
    // since the Tamil Nadu Gazette witness has a different 2026 date label.
    let thai1 = calendar::thirukanitham_month_info(fields.0 - 1, 10, context)?.start_date;
    let on_or_after_thai1 =
        (date.year(), date.month(), date.day()) >= (thai1.year(), thai1.month(), thai1.day());
    let year_offset = if on_or_after_thai1 { 31 } else { 30 };
    let thiruvalluvar_year = fields.0 + year_offset;

    Ok(json!({
        "convention_id":CONVENTION_ID,
        "calendar_definition_id":THIRUKANITHAM_DEFINITION,
        "context":object["context"],
        "gregorian_date":calendar_gregorian_json(date),
        "thiruvalluvar_year":thiruvalluvar_year,
        "thai1_date":calendar_gregorian_json(thai1),
        "boundary_status":if on_or_after_thai1 { "on_or_after_thai1" } else { "before_thai1" },
        "year_number_rule":"proleptic_gregorian_year_plus_30_before_profile_thai1_or_plus_31_on_or_after",
        "official_equivalence":"not_established",
        "scope_note":"Named Tamil Nadu Thai-1 convention evaluated with the specified Thirukanitham TN context; this is not an official Gazette-year lookup.",
        "known_source_conflict":"Tamil Nadu Government Gazette issue 2, Part I, dated 2026-01-14 has a masthead of Margazhi 30 and Thiruvalluvar year 2056; Gazette issue 31 dated 2026-01-23 has a masthead of Thai 9 and year 2057. This profile's Thai-1 boundary is 2026-01-14 and differs on that date. These two mastheads do not establish the exact official boundary.",
        "sources":[
            {"id":"tn-go-91-1981","url":"https://mayiladuthurai.nic.in/tamil-development/","locator":"Tamil Development page, Government Order Official Language Scheme; G.O.(Ms) No.91, Personnel and Administrative Department, 1981-02-03; Thiruvalluvar year in official proceedings."},
            {"id":"tn-governors-address-2008","url":"https://www.tnbudget.tn.gov.in/tnweb_files/Bud_gov_speeches/Governor%27s%20Address%202008-English.pdf","locator":"Governor's Address 2008, printed page 35; states 31 BCE year anchor and Thai 1 as the Tamil year start."},
            {"id":"tn-gazette-2026-2-part-i","url":"https://stationeryprinting.tn.gov.in/gazette/2026/2_I_2026.pdf","locator":"Government Gazette issue 2, Part I, PDF page 1; masthead dated 2026-01-14 / Margazhi 30 / Visuvaavasu / Thiruvalluvar 2056. Official PDF text retrieved; no local file digest asserted."},
            {"id":"tn-gazette-2026-31-part-iii-1a","url":"https://www.stationeryprinting.tn.gov.in/extraordinary/2026/31_Ex_III_1a_2026.pdf","locator":"Government Gazette Extraordinary issue 31, Part III-Section 1(a), PDF page 1; masthead dated 2026-01-23 as Thai 9, Visuvaavasu, Thiruvalluvar 2057. This does not identify Thai 1's exact official date."}
        ]
    }))
}


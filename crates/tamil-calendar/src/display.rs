use crate::tables;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CalendarDisplayNames {
    pub profile_id: &'static str,
    pub script: &'static str,
    pub months: Vec<&'static str>,
    pub weekdays: Vec<&'static str>,
    pub tithis: Vec<&'static str>,
    pub new_moon_tithi: &'static str,
    pub nakshatras: Vec<&'static str>,
    pub yogas: Vec<&'static str>,
    pub karanas: Vec<&'static str>,
    pub romanized_karanas: Vec<&'static str>,
    pub year_cycles: Vec<&'static str>,
    pub tamil_source_url: &'static str,
    pub tamil_source_sha256: &'static str,
    pub tamil_source_locator: &'static str,
    pub tamil_reuse_terms_status: &'static str,
    pub weekday_source_url: &'static str,
    pub weekday_source_sha256: &'static str,
    pub weekday_source_locator: &'static str,
    pub weekday_romanization_source_url: &'static str,
    pub weekday_romanization_source_sha256: &'static str,
    pub weekday_romanization_source_locator: &'static str,
    pub weekday_romanization_license: &'static str,
    pub cycle_romanized_source_id: &'static str,
    pub cycle_romanized_source_sha256: &'static str,
    pub cycle_tamil_crosscheck_url: &'static str,
    pub regional_scope: &'static str,
    pub karana_source_note: &'static str,
}

pub fn calendar_display_names(script: &str) -> Result<CalendarDisplayNames, String> {
    let canonical_script = match script {
        "tamil" => "tamil",
        "romanized" => "romanized",
        _ => return Err("unsupported calendar display script".into()),
    };
    let (months, weekdays, tithis, new_moon_tithi, nakshatras, yogas, karanas, year_cycles) =
        match script {
            "tamil" => (
                tables::CALENDAR_MONTH_NAMES_TAMIL.as_slice(),
                tables::CALENDAR_WEEKDAY_NAMES_TAMIL.as_slice(),
                tables::CALENDAR_TITHI_NAMES_TAMIL.as_slice(),
                tables::CALENDAR_TITHI_NEW_MOON_NAME_TAMIL,
                tables::CALENDAR_NAKSHATRA_NAMES_TAMIL.as_slice(),
                tables::CALENDAR_YOGA_NAMES_TAMIL.as_slice(),
                tables::CALENDAR_KARANA_NAMES_TAMIL.as_slice(),
                tables::CALENDAR_CYCLE_NAMES_TAMIL.as_slice(),
            ),
            "romanized" => (
                tables::DRIK_MONTH_NAMES.as_slice(),
                tables::CALENDAR_WEEKDAY_NAMES_ROMANIZED.as_slice(),
                tables::DRIK_TITHI_NAMES.as_slice(),
                "Amavasya",
                tables::DRIK_NAKSHATRA_NAMES.as_slice(),
                tables::DRIK_YOGA_NAMES.as_slice(),
                tables::DRIK_KARANA_NAMES.as_slice(),
                tables::TAMIL_SOLAR_YEAR_CYCLE_NAMES.as_slice(),
            ),
            _ => unreachable!("script was validated above"),
        };

    Ok(CalendarDisplayNames {
        profile_id: tables::CALENDAR_TAMIL_DISPLAY_PROFILE,
        script: canonical_script,
        months: months.to_vec(),
        weekdays: weekdays.to_vec(),
        tithis: tithis.to_vec(),
        new_moon_tithi,
        nakshatras: nakshatras.to_vec(),
        yogas: yogas.to_vec(),
        karanas: karanas.to_vec(),
        romanized_karanas: tables::DRIK_KARANA_NAMES.to_vec(),
        year_cycles: year_cycles.to_vec(),
        tamil_source_url: tables::CALENDAR_TVA_SOURCE_URL,
        tamil_source_sha256: tables::CALENDAR_TVA_SOURCE_SHA256,
        tamil_source_locator: tables::CALENDAR_TVA_SOURCE_LOCATOR,
        tamil_reuse_terms_status: tables::CALENDAR_TVA_REUSE_TERMS_STATUS,
        weekday_source_url: tables::CALENDAR_CLDR_SOURCE_URL,
        weekday_source_sha256: tables::CALENDAR_CLDR_SOURCE_SHA256,
        weekday_source_locator: tables::CALENDAR_CLDR_WEEKDAY_LOCATOR,
        weekday_romanization_source_url: tables::CALENDAR_MSU_WEEKDAY_SOURCE_URL,
        weekday_romanization_source_sha256: tables::CALENDAR_MSU_WEEKDAY_SOURCE_SHA256,
        weekday_romanization_source_locator: tables::CALENDAR_MSU_WEEKDAY_SOURCE_LOCATOR,
        weekday_romanization_license: tables::CALENDAR_MSU_WEEKDAY_SOURCE_LICENSE,
        cycle_romanized_source_id: tables::CALENDAR_CYCLE_ROMANIZED_SOURCE_ID,
        cycle_romanized_source_sha256: tables::CALENDAR_CYCLE_ROMANIZED_SOURCE_SHA256,
        cycle_tamil_crosscheck_url: tables::CALENDAR_CYCLE_TAMIL_CROSSCHECK_URL,
        regional_scope: tables::CALENDAR_DISPLAY_SCOPE,
        karana_source_note: tables::CALENDAR_KARANA_SOURCE_NOTE,
    })
}

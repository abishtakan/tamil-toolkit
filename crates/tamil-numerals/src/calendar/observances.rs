use super::super::tables::{
    CalendarObservanceSourceData, CALENDAR_OBSERVANCES_ASTRONOMY_NOTE,
    CALENDAR_OBSERVANCES_DEFINITION_ID, CALENDAR_OBSERVANCES_END_YEAR,
    CALENDAR_OBSERVANCES_JURISDICTION, CALENDAR_OBSERVANCES_REUSE_TERMS_STATUS,
    CALENDAR_OBSERVANCES_RULES, CALENDAR_OBSERVANCES_RULE_SET_ID, CALENDAR_OBSERVANCES_SCOPE_NOTE,
    CALENDAR_OBSERVANCES_SOURCES, CALENDAR_OBSERVANCES_START_YEAR,
};
use super::drik::{
    thirukanitham_aparahna_tithi_dates, thirukanitham_ayudha_puja_date,
    thirukanitham_krishna_jayanthi_dates, thirukanitham_nakshatra_observance_dates,
    thirukanitham_nava_pradosham_dates, thirukanitham_sankatahara_chaturthi_dates,
    thirukanitham_sri_vaishnava_ekadashi_dates, thirukanitham_tamil_to_gregorian_date,
    thirukanitham_tithi_observance_dates, thirukanitham_vijayadashami_date, ThirukanithamContext,
};
use crate::{add_gregorian_date, GregorianDate};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ThirukanithamObservanceSource {
    pub id: &'static str,
    pub url: &'static str,
    pub locator: &'static str,
    pub sha256: Option<&'static str>,
    pub year: Option<i64>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ThirukanithamObservanceEvent {
    pub event_id: &'static str,
    pub display_name: &'static str,
    pub date: GregorianDate,
    pub rule_id: &'static str,
    pub tithi_index: Option<u8>,
    pub nakshatra_index: Option<u8>,
    pub source_ids: Vec<&'static str>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ThirukanithamObservances {
    pub definition_id: &'static str,
    pub rule_set_id: &'static str,
    pub gregorian_year: i64,
    pub jurisdiction: &'static str,
    pub context: ThirukanithamContext,
    pub scope_note: &'static str,
    pub astronomy_note: &'static str,
    pub source_compatibility: &'static str,
    pub reuse_terms_status: &'static str,
    pub sources: Vec<ThirukanithamObservanceSource>,
    pub supported_event_ids: Vec<&'static str>,
    pub events: Vec<ThirukanithamObservanceEvent>,
}

pub fn thirukanitham_observances(
    rule_set_id: &str,
    gregorian_year: i64,
    month: Option<u8>,
    context: ThirukanithamContext,
) -> Result<ThirukanithamObservances, String> {
    if rule_set_id != CALENDAR_OBSERVANCES_RULE_SET_ID {
        return Err("unsupported calendar observance rule set".into());
    }
    if context.region() != CALENDAR_OBSERVANCES_JURISDICTION {
        return Err("unsupported jurisdiction for observance rule set".into());
    }
    if !(CALENDAR_OBSERVANCES_START_YEAR..=CALENDAR_OBSERVANCES_END_YEAR).contains(&gregorian_year)
    {
        return Err("outside supported observance rule-set coverage".into());
    }
    if month.is_some_and(|month| !(1..=12).contains(&month)) {
        return Err("invalid calendar input".into());
    }

    let sources = CALENDAR_OBSERVANCES_SOURCES
        .iter()
        .filter(|source| {
            source_covers_query(source, gregorian_year, month)
                && source_covers_location(source.0, context)
        })
        .map(|source| ThirukanithamObservanceSource {
            id: source.0,
            url: source.1,
            locator: source.2,
            sha256: (!source.3.is_empty()).then_some(source.3),
            year: (source.4 != 0).then_some(source.4),
        })
        .collect::<Vec<_>>();
    let supported_event_ids = CALENDAR_OBSERVANCES_RULES
        .iter()
        .map(|rule| rule.0)
        .collect::<Vec<_>>();
    let mut events = Vec::new();

    for rule in CALENDAR_OBSERVANCES_RULES {
        match rule.3 {
            "solar_month_day" => {
                let solar_year = if rule.4 >= 10 {
                    gregorian_year - 1
                } else {
                    gregorian_year
                };
                let date = thirukanitham_tamil_to_gregorian_date(
                    solar_year,
                    i64::from(rule.4),
                    i64::from(rule.5),
                    context,
                )?
                .gregorian_date;
                let date = add_gregorian_date(date, "days", rule.6, "reject")
                    .map_err(|_| "outside supported calendar coverage")?;
                if date.year() == gregorian_year {
                    if month.is_some_and(|month| date.month() != u32::from(month)) {
                        continue;
                    }
                    events.push(ThirukanithamObservanceEvent {
                        event_id: rule.0,
                        display_name: rule.1,
                        date,
                        rule_id: rule.2,
                        tithi_index: None,
                        nakshatra_index: None,
                        source_ids: applicable_source_ids(rule.9, date, context),
                    });
                }
            }
            "tithi_aparahna_then_sunrise" => {
                for date in
                    thirukanitham_aparahna_tithi_dates(gregorian_year, month, rule.7, context)?
                {
                    if month.is_some_and(|month| date.month() != u32::from(month)) {
                        continue;
                    }
                    events.push(ThirukanithamObservanceEvent {
                        event_id: rule.0,
                        display_name: rule.1,
                        date,
                        rule_id: rule.2,
                        tithi_index: Some(rule.7),
                        nakshatra_index: None,
                        source_ids: applicable_source_ids(rule.9, date, context),
                    });
                }
            }
            "tithi_solar_month_sunrise"
            | "tithi_solar_month_first_third"
            | "tithi_solar_month_brahma_muhurta"
            | "tithi_madhyahna_then_start"
            | "tithi_nishita_then_sunset" => {
                let window = match rule.3 {
                    "tithi_solar_month_sunrise" => "sunrise",
                    "tithi_solar_month_first_third" => "first_third",
                    "tithi_solar_month_brahma_muhurta" => "brahma_muhurta",
                    "tithi_madhyahna_then_start" => "madhyahna_first",
                    "tithi_nishita_then_sunset" => "nishita_then_sunset",
                    _ => unreachable!("calendar observance rules are build-validated"),
                };
                for date in thirukanitham_tithi_observance_dates(
                    gregorian_year,
                    month,
                    rule.4,
                    rule.7,
                    window,
                    context,
                )? {
                    events.push(ThirukanithamObservanceEvent {
                        event_id: rule.0,
                        display_name: rule.1,
                        date,
                        rule_id: rule.2,
                        tithi_index: Some(rule.7),
                        nakshatra_index: None,
                        source_ids: applicable_source_ids(rule.9, date, context),
                    });
                }
            }
            "tithi_navaratri_navami_sunrise" => {
                if let Some(date) = thirukanitham_ayudha_puja_date(gregorian_year, month, context)?
                {
                    events.push(ThirukanithamObservanceEvent {
                        event_id: rule.0,
                        display_name: rule.1,
                        date,
                        rule_id: rule.2,
                        tithi_index: Some(rule.7),
                        nakshatra_index: None,
                        source_ids: applicable_source_ids(rule.9, date, context),
                    });
                }
            }
            "tithi_navaratri_dasara_aparahna" => {
                if let Some(date) =
                    thirukanitham_vijayadashami_date(gregorian_year, month, context)?
                {
                    events.push(ThirukanithamObservanceEvent {
                        event_id: rule.0,
                        display_name: rule.1,
                        date,
                        rule_id: rule.2,
                        tithi_index: Some(rule.7),
                        nakshatra_index: Some(rule.8),
                        source_ids: applicable_source_ids(rule.9, date, context),
                    });
                }
            }
            "tithi_moonrise_first_if_repeated_else_second" => {
                for date in
                    thirukanitham_sankatahara_chaturthi_dates(gregorian_year, month, context)?
                {
                    events.push(ThirukanithamObservanceEvent {
                        event_id: rule.0,
                        display_name: rule.1,
                        date,
                        rule_id: rule.2,
                        tithi_index: Some(rule.7),
                        nakshatra_index: None,
                        source_ids: applicable_source_ids(rule.9, date, context),
                    });
                }
            }
            "tithi_nishita_rohini_then_second" => {
                for date in thirukanitham_krishna_jayanthi_dates(
                    gregorian_year,
                    month,
                    rule.7,
                    rule.8,
                    context,
                )? {
                    events.push(ThirukanithamObservanceEvent {
                        event_id: rule.0,
                        display_name: rule.1,
                        date,
                        rule_id: rule.2,
                        tithi_index: Some(rule.7),
                        nakshatra_index: Some(rule.8),
                        source_ids: applicable_source_ids(rule.9, date, context),
                    });
                }
            }
            "tithi_arunodaya_defer" => {
                for (date, tithi_index) in
                    thirukanitham_sri_vaishnava_ekadashi_dates(gregorian_year, month, context)?
                {
                    if date.year() != gregorian_year
                        || month.is_some_and(|month| date.month() != u32::from(month))
                    {
                        continue;
                    }
                    events.push(ThirukanithamObservanceEvent {
                        event_id: rule.0,
                        display_name: rule.1,
                        date,
                        rule_id: rule.2,
                        tithi_index: Some(tithi_index),
                        nakshatra_index: None,
                        source_ids: applicable_source_ids(rule.9, date, context),
                    });
                }
            }
            "tithi_pradosha_sunset_window" => {
                for (date, tithi_index) in
                    thirukanitham_nava_pradosham_dates(gregorian_year, month, context)?
                {
                    if date.year() != gregorian_year
                        || month.is_some_and(|month| date.month() != u32::from(month))
                    {
                        continue;
                    }
                    events.push(ThirukanithamObservanceEvent {
                        event_id: rule.0,
                        display_name: rule.1,
                        date,
                        rule_id: rule.2,
                        tithi_index: Some(tithi_index),
                        nakshatra_index: None,
                        source_ids: applicable_source_ids(rule.9, date, context),
                    });
                }
            }
            "nakshatra_sunrise"
            | "nakshatra_arunodaya"
            | "nakshatra_night"
            | "nakshatra_sunset_later_if_repeated"
            | "nakshatra_tithi_daytime_then_sunrise"
            | "nakshatra_sunrise_nearest_purnima"
            | "nakshatra_sunrise_purnima_then_sunrise" => {
                let window = match rule.3 {
                    "nakshatra_sunrise" => "sunrise",
                    "nakshatra_arunodaya" => "arunodaya",
                    "nakshatra_night" => "night",
                    "nakshatra_sunset_later_if_repeated" => "sunset",
                    "nakshatra_tithi_daytime_then_sunrise" => "thai_purnima_pushya",
                    "nakshatra_sunrise_nearest_purnima" => "sunrise_nearest_purnima",
                    "nakshatra_sunrise_purnima_then_sunrise" => "panguni_purnima_uthiram",
                    _ => unreachable!("calendar observance rules are build-validated"),
                };
                for (date, tithi_index) in thirukanitham_nakshatra_observance_dates(
                    gregorian_year,
                    month,
                    rule.4,
                    rule.7,
                    rule.8,
                    window,
                    context,
                )? {
                    events.push(ThirukanithamObservanceEvent {
                        event_id: rule.0,
                        display_name: rule.1,
                        date,
                        rule_id: rule.2,
                        tithi_index,
                        nakshatra_index: Some(rule.8),
                        source_ids: applicable_source_ids(rule.9, date, context),
                    });
                }
            }
            _ => unreachable!("calendar observance rules are build-validated"),
        }
    }

    events.sort_by_key(|event| {
        (
            event.date.year(),
            event.date.month(),
            event.date.day(),
            event.event_id,
        )
    });
    Ok(ThirukanithamObservances {
        definition_id: CALENDAR_OBSERVANCES_DEFINITION_ID,
        rule_set_id: CALENDAR_OBSERVANCES_RULE_SET_ID,
        gregorian_year,
        jurisdiction: CALENDAR_OBSERVANCES_JURISDICTION,
        context,
        scope_note: CALENDAR_OBSERVANCES_SCOPE_NOTE,
        astronomy_note: CALENDAR_OBSERVANCES_ASTRONOMY_NOTE,
        source_compatibility: "publisher_equivalence_not_claimed",
        reuse_terms_status: CALENDAR_OBSERVANCES_REUSE_TERMS_STATUS,
        sources,
        supported_event_ids,
        events,
    })
}

fn applicable_source_ids(
    source_ids: &str,
    date: GregorianDate,
    context: ThirukanithamContext,
) -> Vec<&'static str> {
    source_ids
        .split(',')
        .filter_map(|id| {
            CALENDAR_OBSERVANCES_SOURCES
                .iter()
                .find(|source| {
                    source.0 == id
                        && (source.4 == 0 || source.4 == date.year())
                        && source_covers_date(source, date)
                        && source_covers_location(source.0, context)
                })
                .map(|source| source.0)
        })
        .collect()
}

fn source_covers_location(id: &str, context: ThirukanithamContext) -> bool {
    if id.contains("chennai") {
        context.latitude_microdegrees() == 13_087_840
            && context.longitude_microdegrees() == 80_278_470
            && context.elevation_meters() == 14
    } else if id.contains("kanchipuram") {
        context.latitude_microdegrees() == 12_840_700
            && context.longitude_microdegrees() == 79_703_200
    } else {
        true
    }
}

#[cfg(test)]
fn source_covers_query_year(source: &CalendarObservanceSourceData, year: i64) -> bool {
    source_covers_query(source, year, None)
}

fn source_covers_query(
    source: &CalendarObservanceSourceData,
    year: i64,
    month: Option<u8>,
) -> bool {
    if source.4 != 0 && source.4 != year {
        return false;
    }
    let query_start = match month {
        Some(month) => format!("{year:04}-{month:02}-01"),
        None => format!("{year:04}-01-01"),
    };
    let query_end = match month {
        Some(month) => {
            let (next_year, next_month) = if month == 12 {
                (year + 1, 1_i64)
            } else {
                (year, i64::from(month) + 1)
            };
            let next = GregorianDate::new(next_year, next_month, 1)
                .expect("next month start is a valid Gregorian date");
            let last = add_gregorian_date(next, "days", -1, "reject")
                .expect("previous Gregorian date exists");
            format!("{:04}-{:02}-{:02}", last.year(), last.month(), last.day())
        }
        None => format!("{year:04}-12-31"),
    };
    if !source.7.is_empty() {
        return source
            .7
            .split(',')
            .any(|date| query_start.as_str() <= date && date <= query_end.as_str());
    }
    if source.5.is_empty() {
        return source.4 == 0 || source.4 == year;
    }
    source.5 <= query_end.as_str() && source.6 >= query_start.as_str()
}

fn source_covers_date(source: &CalendarObservanceSourceData, date: GregorianDate) -> bool {
    let date = format!("{:04}-{:02}-{:02}", date.year(), date.month(), date.day());
    if !source.7.is_empty() {
        return source
            .7
            .split(',')
            .any(|observed| observed == date.as_str());
    }
    if source.5.is_empty() {
        return true;
    }
    source.5 <= date.as_str() && date.as_str() <= source.6
}

#[cfg(test)]
mod tests {
    use super::*;

    fn context() -> ThirukanithamContext {
        ThirukanithamContext::new("TN", 13_087_840, 80_278_470, 14, "Asia/Kolkata").unwrap()
    }

    #[test]
    fn annual_witnesses_are_local_to_chennai() {
        let other =
            ThirukanithamContext::new("TN", 10_000_000, 78_000_000, 14, "Asia/Kolkata").unwrap();
        assert!(!source_covers_location(
            "nava-amavasya-chennai-2026-27",
            other
        ));
        assert!(source_covers_location(
            "nava-amavasya-chennai-2026-27",
            context()
        ));
        assert!(source_covers_location(
            "nava-panchangam-observance-method",
            other
        ));

        let kanchipuram =
            ThirukanithamContext::new("TN", 12_840_700, 79_703_200, 0, "Asia/Kolkata").unwrap();
        assert!(!source_covers_location(
            "udyog-janmashtami-kanchipuram-2027",
            context()
        ));
        assert!(source_covers_location(
            "udyog-janmashtami-kanchipuram-2027",
            kanchipuram
        ));
    }

    fn source(id: &str) -> &'static CalendarObservanceSourceData {
        CALENDAR_OBSERVANCES_SOURCES
            .iter()
            .find(|source| source.0 == id)
            .expect("source is present in the compiled observance lexicon")
    }

    #[test]
    fn annual_tithi_sources_are_limited_to_the_retained_page_dates() {
        let amavasya = source("nava-amavasya-chennai-2026-27");
        let pournami = source("nava-pournami-chennai-2026-27");
        assert!(!source_covers_query_year(amavasya, 2025));
        assert!(source_covers_query_year(amavasya, 2026));
        assert!(source_covers_query_year(amavasya, 2027));

        assert!(!source_covers_date(
            amavasya,
            GregorianDate::new(2026, 11, 7).unwrap()
        ));
        assert!(source_covers_date(
            amavasya,
            GregorianDate::new(2026, 11, 8).unwrap()
        ));
        assert!(source_covers_date(
            amavasya,
            GregorianDate::new(2027, 10, 29).unwrap()
        ));
        assert!(!source_covers_date(
            amavasya,
            GregorianDate::new(2027, 10, 30).unwrap()
        ));
        assert!(!source_covers_date(
            pournami,
            GregorianDate::new(2027, 10, 16).unwrap()
        ));
    }

    #[test]
    fn event_source_ids_keep_the_rule_but_only_attach_matching_annual_witnesses() {
        assert_eq!(
            applicable_source_ids(
                "nava-panchangam-observance-method,nava-amavasya-chennai-2026-27",
                GregorianDate::new(2026, 10, 10).unwrap(),
                context()
            ),
            ["nava-panchangam-observance-method"]
        );
        assert_eq!(
            applicable_source_ids(
                "nava-panchangam-observance-method,nava-amavasya-chennai-2026-27",
                GregorianDate::new(2026, 11, 8).unwrap(),
                context()
            ),
            [
                "nava-panchangam-observance-method",
                "nava-amavasya-chennai-2026-27"
            ]
        );
    }

    #[test]
    fn new_festival_witnesses_are_exact_month_scoped_and_chennai_only() {
        let chitra = source("tamilcalendar-com-chitra-pournami-chennai-2026");
        let chitra_2025 = source("drik-chitra-pournami-chennai-2025");
        let vinayaka = source("drik-vinayaka-chennai-2025-2027");
        let sivaratri = source("tamilcalendar-com-sivarathri-chennai-2026");
        let panguni = source("panjangam-panguni-uthiram-chennai-2025");
        let karthigai = source("nammacalendar-karthigai-deepam-chennai-2025-vakya");
        assert!(source_covers_query(chitra, 2026, Some(5)));
        assert!(!source_covers_query(chitra, 2026, Some(4)));
        assert!(source_covers_date(
            chitra,
            GregorianDate::new(2026, 5, 1).unwrap()
        ));
        assert!(!source_covers_date(
            chitra,
            GregorianDate::new(2026, 5, 2).unwrap()
        ));
        assert!(source_covers_date(
            chitra_2025,
            GregorianDate::new(2025, 5, 12).unwrap()
        ));
        assert!(source_covers_date(
            vinayaka,
            GregorianDate::new(2025, 8, 27).unwrap()
        ));
        assert!(source_covers_date(
            vinayaka,
            GregorianDate::new(2026, 9, 14).unwrap()
        ));
        assert!(source_covers_date(
            vinayaka,
            GregorianDate::new(2027, 9, 4).unwrap()
        ));
        assert!(!source_covers_date(
            vinayaka,
            GregorianDate::new(2026, 9, 15).unwrap()
        ));
        assert!(source_covers_date(
            sivaratri,
            GregorianDate::new(2026, 2, 15).unwrap()
        ));
        assert!(source_covers_date(
            panguni,
            GregorianDate::new(2025, 4, 11).unwrap()
        ));
        assert!(source_covers_date(
            karthigai,
            GregorianDate::new(2025, 12, 3).unwrap()
        ));

        let other_tn =
            ThirukanithamContext::new("TN", 10_000_000, 78_000_000, 14, "Asia/Kolkata").unwrap();
        assert_eq!(
            applicable_source_ids(
                "drik-vinayaka-madhyahna-method,drik-vinayaka-chennai-2025-2027,tamilcalendar-com-vinayaka-chaturthi-chennai-2026",
                GregorianDate::new(2026, 9, 14).unwrap(),
                other_tn
            ),
            ["drik-vinayaka-madhyahna-method"]
        );
        assert_eq!(
            applicable_source_ids(
                "udaya-sivaratri-nishita-method,drik-sivarathri-chennai-2026,tamilcalendar-com-sivarathri-chennai-2026",
                GregorianDate::new(2026, 2, 15).unwrap(),
                context()
            ),
            [
                "udaya-sivaratri-nishita-method",
                "drik-sivarathri-chennai-2026",
                "tamilcalendar-com-sivarathri-chennai-2026"
            ]
        );
        assert_eq!(
            applicable_source_ids(
                "drik-karthigai-deepam-method,pujadeep-karthigai-evening-method,nammacalendar-karthigai-deepam-chennai-2025-vakya",
                GregorianDate::new(2025, 12, 3).unwrap(),
                other_tn
            ),
            [
                "drik-karthigai-deepam-method",
                "pujadeep-karthigai-evening-method"
            ]
        );
    }

    #[test]
    fn ekadashi_annual_witnesses_are_exact_and_month_scoped() {
        let nava = source("nava-sri-vaishnava-ekadashi-chennai-2026-27");
        let drik = source("drik-iskcon-ekadashi-chennai-2026");

        assert!(!source_covers_query(nava, 2026, Some(10)));
        assert!(source_covers_query(nava, 2026, Some(11)));
        assert!(!source_covers_date(
            nava,
            GregorianDate::new(2026, 10, 22).unwrap()
        ));
        assert!(!source_covers_query(nava, 2026, Some(9)));
        assert!(source_covers_query(drik, 2026, Some(10)));
        assert!(!source_covers_query(drik, 2026, Some(12)));
        assert!(source_covers_date(
            nava,
            GregorianDate::new(2026, 11, 20).unwrap()
        ));
        assert!(!source_covers_date(
            nava,
            GregorianDate::new(2026, 11, 21).unwrap()
        ));
        assert!(source_covers_date(
            drik,
            GregorianDate::new(2026, 11, 21).unwrap()
        ));
        assert!(!source_covers_date(
            drik,
            GregorianDate::new(2026, 11, 20).unwrap()
        ));
    }

    #[test]
    fn pradosham_method_and_chennai_date_witnesses_are_exact_and_month_scoped() {
        let nava = source("nava-panchangam-pradosham-chennai-2026-27");
        let tamil_calendar_2026 = source("tamilcalendar-app-pradosham-chennai-2026");
        let tamil_calendar_2027 = source("tamilcalendar-app-pradosham-chennai-2027");

        assert!(source_covers_query(nava, 2026, Some(11)));
        assert!(!source_covers_query(nava, 2026, Some(10)));
        assert!(source_covers_query(tamil_calendar_2026, 2026, Some(11)));
        assert!(!source_covers_query(tamil_calendar_2026, 2027, Some(11)));
        assert!(source_covers_query(tamil_calendar_2027, 2027, Some(10)));

        let february_toolkit_date = GregorianDate::new(2027, 2, 3).unwrap();
        let february_nava_date = GregorianDate::new(2027, 2, 4).unwrap();
        assert!(!source_covers_date(nava, february_toolkit_date));
        assert!(source_covers_date(nava, february_nava_date));
        assert!(source_covers_date(
            tamil_calendar_2027,
            february_toolkit_date
        ));
        assert_eq!(
            applicable_source_ids(
                "nava-panchangam-pradosham-method,nava-panchangam-pradosham-chennai-2026-27,tamilcalendar-app-pradosham-chennai-2027",
                february_toolkit_date,
                context()
            ),
            [
                "nava-panchangam-pradosham-method",
                "tamilcalendar-app-pradosham-chennai-2027"
            ]
        );

        let other_tn =
            ThirukanithamContext::new("TN", 10_000_000, 78_000_000, 14, "Asia/Kolkata").unwrap();
        assert_eq!(
            applicable_source_ids(
                "nava-panchangam-pradosham-method,nava-panchangam-pradosham-chennai-2026-27,tamilcalendar-app-pradosham-chennai-2027",
                february_toolkit_date,
                other_tn
            ),
            ["nava-panchangam-pradosham-method"]
        );
    }
}

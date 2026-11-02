use serde_json::{json, Value};
use tamil_toolkit::execute;

fn request(op: &str, input: Value) -> Value {
    execute(&json!({"op":op,"input":input})).unwrap()
}

fn chennai() -> Value {
    json!({
        "region":"TN", "latitude_microdegrees":13087840,
        "longitude_microdegrees":80278470, "elevation_meters":14,
        "time_zone":"Asia/Kolkata"
    })
}

fn colombo() -> Value {
    json!({
        "region":"SL", "latitude_microdegrees":6935480,
        "longitude_microdegrees":79848680, "elevation_meters":7,
        "time_zone":"Asia/Colombo"
    })
}

fn jaffna(elevation_meters: i64) -> Value {
    json!({
        "region":"SL", "latitude_microdegrees":9668450,
        "longitude_microdegrees":80007420, "elevation_meters":elevation_meters,
        "time_zone":"Asia/Colombo"
    })
}

fn local_minute(value: &Value) -> i64 {
    let value = value.as_str().unwrap().split_whitespace().last().unwrap();
    let (hour, minute) = value.split_once(':').unwrap();
    hour.parse::<i64>().unwrap() * 60 + minute.parse::<i64>().unwrap()
}

const DEFINITION: &str = "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2";

#[test]
fn profile_exposes_finite_model_and_location_contract() {
    let actual = request("calendar_profile_info", json!({"definition_id":DEFINITION}));
    assert_eq!(actual["definition_id"], DEFINITION);
    assert_eq!(actual["coverage"]["start_date"], "2024-01-01");
    assert_eq!(actual["coverage"]["end_date"], "2027-12-31");
    assert_eq!(actual["ephemeris"]["provider"], "astro");
    assert_eq!(actual["ephemeris"]["version"], "2.0.0");
    assert_eq!(actual["ephemeris"]["license"], "MIT");
    assert_eq!(actual["ephemeris"]["sun_model"], "VSOP87-D");
    assert_eq!(actual["ephemeris"]["moon_model"], "partial ELP-2000/82");
    assert_eq!(
        actual["ephemeris"]["nutation_model"],
        "astro-2.0.0-63-term-iau1980"
    );
    assert_eq!(
        actual["sidereal_parameters"]["true_anchor_milliarcseconds"],
        83_700_658
    );
    assert_eq!(
        actual["sidereal_parameters"]["mean_anchor_microarcseconds"],
        83_683_889_520i64
    );
    assert_eq!(actual["vara_definition"], "panchangam-day:weekday-of-report-civil-date-at-computed-sunrise;panchangam-at:weekday-of-local-civil-date-including-before-sunrise;not-sunrise-to-sunrise");
    assert_eq!(
        actual["sunrise"]["horizon_definition"],
        "apparent_solar_center_altitude_minus_47_arcminutes_with_spherical_elevation_dip"
    );
    assert_eq!(actual["supported_regions"].as_array().unwrap().len(), 2);
    assert_eq!(actual["reference_stations"].as_array().unwrap().len(), 3);
    assert_eq!(
        actual["reference_stations"][2]["id"],
        "jaffna-geonames-1242833"
    );
    assert!(actual["sources"].as_array().unwrap().len() >= 7);
}

#[test]
fn solar_dates_match_independent_chennai_boundary_observations() {
    let cases = [
        ((2024, 4, 13), 2023, 12, 31),
        ((2024, 4, 14), 2024, 1, 1),
        ((2025, 4, 14), 2025, 1, 1),
        ((2025, 4, 15), 2025, 1, 2),
        ((2026, 4, 13), 2025, 12, 30),
        ((2026, 4, 14), 2026, 1, 1),
    ];
    for ((year, month, day), solar_year, tamil_month, tamil_day) in cases {
        let actual = request(
            "gregorian_to_tamil_date",
            json!({"definition_id":DEFINITION,"date":{"year":year,"month":month,"day":day},"context":chennai()}),
        );
        assert_eq!(actual["tamil_date"]["solar_year"], solar_year);
        assert_eq!(actual["tamil_date"]["month"], tamil_month);
        assert_eq!(actual["tamil_date"]["day"], tamil_day);
    }
}

#[test]
fn tamil_date_reverse_and_month_length_use_computed_ingresses() {
    let context = chennai();
    let reverse = request(
        "tamil_to_gregorian_date",
        json!({"definition_id":DEFINITION,"date":{"solar_year":2026,"month":7,"day":15},"context":context}),
    );
    assert_eq!(
        reverse["gregorian_date"],
        json!({"year":2026,"month":11,"day":1})
    );
    let month = request(
        "tamil_month_info",
        json!({"definition_id":DEFINITION,"solar_year":2026,"month":7,"context":chennai()}),
    );
    assert_eq!(
        month["start_date"],
        json!({"year":2026,"month":10,"day":18})
    );
    assert_eq!(
        month["end_date_exclusive"],
        json!({"year":2026,"month":11,"day":17})
    );
    assert_eq!(month["days"], 30);
}

#[test]
fn panchangam_matches_independent_chennai_and_colombo_daily_witnesses() {
    let published: Value = serde_json::from_str(include_str!(
        "../../../tests/reference/calendar-thirukanitham-v1/drik-panchang-observations-2026-11-01.json"
    ))
    .unwrap();
    let chennai_reference = &published["locations"][0];
    let colombo_reference = &published["locations"][1];
    let instant = request(
        "panchangam_at",
        json!({"definition_id":DEFINITION,"instant_unix_seconds":1793514600,"context":chennai()}),
    );
    assert_eq!(
        instant["local_date"],
        json!({"year":2026,"month":11,"day":1})
    );
    assert_eq!(instant["vara"], "Sunday");
    assert_eq!(instant["limbs"]["tithi"]["index"], 22);
    assert_eq!(instant["limbs"]["nakshatra"]["index"], 8);
    assert_eq!(instant["limbs"]["yoga"]["index"], 22);
    assert_eq!(instant["limbs"]["karana"]["index"], 43);

    let chennai_day = request(
        "panchangam_day",
        json!({"definition_id":DEFINITION,"date":{"year":2026,"month":11,"day":1},"context":chennai()}),
    );
    // Preserve each publisher difference as observed. The hidden publisher
    // settings are not inferred from these rounded minute values.
    assert_eq!(
        chennai_day["sunrise_minute_of_day"].as_i64().unwrap(),
        local_minute(&chennai_reference["sunrise_local"]) - 1
    );
    assert_eq!(
        chennai_day["sunset_minute_of_day"].as_i64().unwrap(),
        local_minute(&chennai_reference["sunset_local"]) + 1
    );
    assert_eq!(chennai_day["transitions"].as_array().unwrap().len(), 5);
    assert!(chennai_day["transitions"]
        .as_array()
        .unwrap()
        .iter()
        .all(|event| event["day_offset"] == 0));
    assert!(chennai_day["transitions"]
        .as_array()
        .unwrap()
        .iter()
        .all(|event| { (0..1_440).contains(&event["minute_of_day"].as_i64().unwrap()) }));
    let yoga_end = chennai_day["transitions"]
        .as_array()
        .unwrap()
        .iter()
        .find(|event| event["limb"] == "yoga" && event["to_index"] == 23)
        .unwrap();
    assert_eq!(
        yoga_end["minute_of_day"].as_i64().unwrap(),
        local_minute(&chennai_reference["yoga"]["ends_local"])
    );
    let tithi_end = chennai_day["transitions"]
        .as_array()
        .unwrap()
        .iter()
        .find(|event| event["limb"] == "tithi" && event["to_index"] == 23)
        .unwrap();
    assert_eq!(
        tithi_end["minute_of_day"].as_i64().unwrap(),
        local_minute(&chennai_reference["tithi"]["ends_local"]) + 1
    );
    let karana_end = chennai_day["transitions"]
        .as_array()
        .unwrap()
        .iter()
        .find(|event| event["limb"] == "karana" && event["to_index"] == 44)
        .unwrap();
    assert_eq!(
        karana_end["minute_of_day"].as_i64().unwrap(),
        local_minute(&chennai_reference["karana"]["ends_local"]) + 1
    );

    let next_day = request(
        "panchangam_day",
        json!({"definition_id":DEFINITION,"date":{"year":2026,"month":11,"day":2},"context":chennai()}),
    );
    let pushya_end = next_day["transitions"]
        .as_array()
        .unwrap()
        .iter()
        .find(|event| event["limb"] == "nakshatra" && event["from_index"] == 8)
        .unwrap();
    assert_eq!(
        pushya_end["minute_of_day"].as_i64().unwrap(),
        local_minute(&chennai_reference["nakshatra"]["ends_local"]) + 1
    );

    let colombo_day = request(
        "panchangam_day",
        json!({"definition_id":DEFINITION,"date":{"year":2026,"month":11,"day":1},"context":colombo()}),
    );
    assert_eq!(
        colombo_day["sunrise_minute_of_day"].as_i64().unwrap(),
        local_minute(&colombo_reference["sunrise_local"])
    );
    assert_eq!(
        colombo_day["sunset_minute_of_day"].as_i64().unwrap(),
        local_minute(&colombo_reference["sunset_local"]) + 1
    );
    assert_eq!(colombo_day["limbs_at_sunrise"]["tithi"]["index"], 22);
}

#[test]
fn every_public_month_boundary_roundtrips_at_both_ends() {
    for solar_year in 2024..=2027 {
        let final_month = if solar_year == 2027 { 9 } else { 12 };
        for month in 1..=final_month {
            let info = request(
                "tamil_month_info",
                json!({"definition_id":DEFINITION,"solar_year":solar_year,"month":month,"context":chennai()}),
            );
            let days = info["days"].as_i64().unwrap();
            assert!((29..=32).contains(&days));
            let start = info["start_date"].clone();
            let start_result = request(
                "tamil_to_gregorian_date",
                json!({"definition_id":DEFINITION,"date":{"solar_year":solar_year,"month":month,"day":1},"context":chennai()}),
            );
            assert_eq!(start_result["gregorian_date"], start);
            let public_end = json!({"year":2027,"month":12,"day":31});
            let available_days = if solar_year < 2027 || (solar_year == 2027 && month <= 8) {
                days
            } else {
                let start = info["start_date"].as_object().unwrap();
                let start = tamil_numerals::GregorianDate::new(
                    start["year"].as_i64().unwrap(),
                    start["month"].as_i64().unwrap(),
                    start["day"].as_i64().unwrap(),
                )
                .unwrap();
                let end = tamil_numerals::GregorianDate::new(2027, 12, 31).unwrap();
                (tamil_numerals::date_difference(start, end) + 1).min(days)
            };
            let last_result = request(
                "tamil_to_gregorian_date",
                json!({"definition_id":DEFINITION,"date":{"solar_year":solar_year,"month":month,"day":available_days},"context":chennai()}),
            );
            if available_days == days {
                assert_eq!(
                    request(
                        "gregorian_to_tamil_date",
                        json!({"definition_id":DEFINITION,"date":last_result["gregorian_date"],"context":chennai()})
                    )["tamil_date"]["day"],
                    days
                );
            } else {
                assert_eq!(
                    request(
                        "gregorian_to_tamil_date",
                        json!({"definition_id":DEFINITION,"date":public_end,"context":chennai()})
                    )["tamil_date"]["day"],
                    available_days
                );
                let outside = execute(&json!({"op":"tamil_to_gregorian_date","input":{"definition_id":DEFINITION,"date":{"solar_year":solar_year,"month":month,"day":available_days + 1},"context":chennai()}})).unwrap_err();
                assert_eq!(outside, "outside supported calendar coverage");
            }
        }
    }
}

#[test]
fn coverage_endpoints_include_chennai_colombo_jaffna_and_elevation_limits() {
    let contexts = [chennai(), colombo(), jaffna(7), jaffna(-100), jaffna(3_000)];
    let dates = [(2024, 1, 1), (2027, 12, 31)];
    for context in contexts {
        for (year, month, day) in dates {
            let date = json!({"year":year,"month":month,"day":day});
            let converted = request(
                "gregorian_to_tamil_date",
                json!({"definition_id":DEFINITION,"date":date,"context":context}),
            );
            assert_eq!(converted["gregorian_date"], date);
            let report = request(
                "panchangam_day",
                json!({"definition_id":DEFINITION,"date":date,"context":context}),
            );
            assert_eq!(report["date"], date);
            assert!((0..1_440).contains(&report["sunrise_minute_of_day"].as_i64().unwrap()));
            assert!((0..1_440).contains(&report["sunset_minute_of_day"].as_i64().unwrap()));
        }
    }
}

#[test]
fn profile_context_coverage_and_date_errors_follow_contract_order() {
    let unknown_definition = execute(&json!({
        "op":"gregorian_to_tamil_date",
        "input":{"definition_id":"unknown","date":{"year":2023,"month":2,"day":30},"context":{"region":"XX","latitude_microdegrees":0,"longitude_microdegrees":0,"elevation_meters":0,"time_zone":"Mars/Olympus"}}
    })).unwrap_err();
    assert_eq!(unknown_definition, "unsupported calendar definition");
    let invalid_context = execute(&json!({
        "op":"gregorian_to_tamil_date",
        "input":{"definition_id":DEFINITION,"date":{"year":2023,"month":2,"day":30},"context":{"region":"XX","latitude_microdegrees":0,"longitude_microdegrees":0,"elevation_meters":0,"time_zone":"Asia/Kolkata"}}
    })).unwrap_err();
    assert_eq!(invalid_context, "invalid calendar context");
    let invalid_date = execute(&json!({
        "op":"gregorian_to_tamil_date",
        "input":{"definition_id":DEFINITION,"date":{"year":2026,"month":2,"day":30},"context":chennai()}
    })).unwrap_err();
    assert_eq!(invalid_date, "invalid Gregorian date");
}

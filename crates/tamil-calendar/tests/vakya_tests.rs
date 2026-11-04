use tamil_calendar::{
    vakya_bhujaantara_from_true_sun, vakya_cara_from_sayana_sun,
    vakya_desantara_from_yojana_distance, vakya_gregorian_to_tamil_date,
    vakya_solar_transits, vakya_true_moon_from_kali_day,
    vakya_true_sun_from_mesha_elapsed, RasiDmsAngle, VakyaCivilContext,
};
use tamil_numerals::GregorianDate;

#[test]
fn test_vakya_solar_transits_coverage() {
    let year = vakya_solar_transits(1869).unwrap();
    assert_eq!(year.saka_year_elapsed, 1869);
    assert_eq!(year.kali_year, 5048);
    assert_eq!(year.transits.len(), 12);
    assert_eq!(year.transits[0].rasi, "vrishabha");
    assert_eq!(year.transits[11].rasi, "mesha");
}

#[test]
fn test_vakya_true_sun_from_mesha_elapsed() {
    let sun = vakya_true_sun_from_mesha_elapsed(0, 0, 0).unwrap();
    assert_eq!(sun.elapsed_days, 0);
    assert_eq!(sun.nadi, 0);
    assert_eq!(sun.vinadi, 0);
    assert_eq!(sun.true_sun.degrees, 0);
}

#[test]
fn test_vakya_true_moon_from_kali_day() {
    let moon = vakya_true_moon_from_kali_day(1_844_000).unwrap();
    assert_eq!(moon.kali_day, 1_844_000);
    assert!(moon.true_moon.rasi < 12);
}

#[test]
fn test_vakya_corrections_properties() {
    let desantara = vakya_desantara_from_yojana_distance(100).unwrap();
    assert!(desantara.desantara_vinadi_tenths != 0);

    let bhujaantara = vakya_bhujaantara_from_true_sun(0, 54_000).unwrap();
    assert_eq!(bhujaantara.sun_rasi, 0);

    let sayana_sun = RasiDmsAngle {
        rasi: 0,
        degrees: 15,
        minutes: 30,
        seconds: 0,
    };
    let cara = vakya_cara_from_sayana_sun(sayana_sun, 50).unwrap();
    assert_eq!(cara.sayana_sun, sayana_sun);
}

#[test]
fn test_vakya_civil_gregorian_to_tamil_date() {
    let ctx = VakyaCivilContext::new("ujjain", "Asia/Kolkata").unwrap();
    let gdate = GregorianDate::new(1947, 8, 15).unwrap();
    let res = vakya_gregorian_to_tamil_date(gdate, ctx).unwrap();
    assert_eq!(res.tamil_date.month_name, "Aadi");
    assert_eq!(res.tamil_date.month, 4);
    assert!(res.tamil_date.day >= 1 && res.tamil_date.day <= 32);
}

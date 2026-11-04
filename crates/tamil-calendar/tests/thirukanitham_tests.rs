use tamil_calendar::{
    thirukanitham_gregorian_to_tamil_date, thirukanitham_month_info,
    thirukanitham_tamil_to_gregorian_date, ThirukanithamContext,
};
use tamil_numerals::GregorianDate;

fn chennai() -> ThirukanithamContext {
    ThirukanithamContext::new("TN", 13_087_840, 80_278_470, 14, "Asia/Kolkata").unwrap()
}

fn colombo() -> ThirukanithamContext {
    ThirukanithamContext::new("SL", 6_935_480, 79_848_680, 7, "Asia/Colombo").unwrap()
}

#[test]
fn test_thirukanitham_gregorian_to_tamil_date_chennai() {
    let ctx = chennai();
    let gdate = GregorianDate::new(2026, 4, 14).unwrap();
    let res = thirukanitham_gregorian_to_tamil_date(gdate, ctx).unwrap();
    assert_eq!(res.tamil_date.solar_year, 2026);
    assert_eq!(res.tamil_date.month, 1); // Chithirai
    assert_eq!(res.tamil_date.day, 1);
    assert_eq!(res.tamil_date.month_name, "Chithirai");
}

#[test]
fn test_thirukanitham_gregorian_to_tamil_date_colombo() {
    let ctx = colombo();
    let gdate = GregorianDate::new(2026, 4, 14).unwrap();
    let res = thirukanitham_gregorian_to_tamil_date(gdate, ctx).unwrap();
    assert_eq!(res.tamil_date.solar_year, 2026);
    assert_eq!(res.tamil_date.month, 1);
    assert_eq!(res.tamil_date.day, 1);
}

#[test]
fn test_thirukanitham_tamil_to_gregorian_roundtrip() {
    let ctx = chennai();
    for year in 2025..=2026 {
        for month in 1..=12 {
            let month_info = thirukanitham_month_info(year, month, ctx).unwrap();
            assert!(month_info.days >= 29 && month_info.days <= 32);

            let reverse = thirukanitham_tamil_to_gregorian_date(year, month, 1, ctx).unwrap();
            let roundtrip = thirukanitham_gregorian_to_tamil_date(reverse.gregorian_date, ctx).unwrap();
            assert_eq!(roundtrip.tamil_date.solar_year, year);
            assert_eq!(i64::from(roundtrip.tamil_date.month), month);
            assert_eq!(roundtrip.tamil_date.day, 1);
        }
    }
}

use super::super::tables::{OFFICIAL_HOLIDAYS, OFFICIAL_HOLIDAY_SCHEDULES};
use super::super::{CalendarOfficialHoliday, CalendarOfficialHolidayYearInfo, GregorianDate};

/// Return an authority-published annual named-holiday schedule in the bundled source range.
/// Weekly rules are reported in `scope_note` and are not expanded into dated rows.
pub fn calendar_official_holiday_year(
    jurisdiction: &str,
    year: i64,
) -> Result<CalendarOfficialHolidayYearInfo, String> {
    let schedule = OFFICIAL_HOLIDAY_SCHEDULES
        .iter()
        .find(|schedule| schedule.1 == jurisdiction && schedule.2 == year)
        .ok_or("official holiday schedule unavailable for jurisdiction/year")?;
    let holidays = OFFICIAL_HOLIDAYS
        .iter()
        .filter(|holiday| holiday.0 == schedule.0)
        .map(|holiday| {
            Ok(CalendarOfficialHoliday {
                date: GregorianDate::new(holiday.1, holiday.2, holiday.3)
                    .map_err(|_| "invalid compiled official holiday date")?,
                name: holiday.4,
                categories: holiday.5,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;
    if holidays.is_empty() {
        return Err("official holiday schedule unavailable for jurisdiction/year".into());
    }
    Ok(CalendarOfficialHolidayYearInfo {
        jurisdiction: schedule.1,
        year: schedule.2,
        schedule_id: schedule.0,
        source_id: schedule.3,
        source: schedule.4,
        source_url: schedule.5,
        source_sha256: schedule.6,
        reuse_terms_status: schedule.7,
        scope_note: schedule.8,
        holidays,
    })
}

#[cfg(test)]
mod tests {
    use super::calendar_official_holiday_year;

    #[test]
    fn returns_authority_rows_and_preserves_same_day_names() {
        let tn = calendar_official_holiday_year("TN", 2025).unwrap();
        assert_eq!(tn.holidays.len(), 24);
        assert_eq!(tn.reuse_terms_status, "unverified");
        assert_eq!(tn.holidays[1].name, "Pongal");
        assert_eq!(
            tn.holidays[8].categories,
            ["commercial_banks", "cooperative_banks"]
        );
        assert_eq!(tn.holidays[20].date, tn.holidays[21].date);
        assert_eq!(tn.holidays[20].name, "Vijaya Dasami");
        assert_eq!(tn.holidays[21].name, "Gandhi Jayanthi");

        let sl = calendar_official_holiday_year("SL", 2027).unwrap();
        assert_eq!(sl.holidays.len(), 25);
        assert_eq!(sl.holidays[0].categories, ["bank", "public", "mercantile"]);
        assert_eq!(sl.source_sha256.unwrap().len(), 64);
    }

    #[test]
    fn unavailable_schedule_is_an_error() {
        assert_eq!(
            calendar_official_holiday_year("TN", 2027).unwrap_err(),
            "official holiday schedule unavailable for jurisdiction/year"
        );
        assert_eq!(
            calendar_official_holiday_year("XX", 2026).unwrap_err(),
            "official holiday schedule unavailable for jurisdiction/year"
        );
    }
}

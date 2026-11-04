use crate::tables;
use super::drik::{
    thirukanitham_gregorian_to_tamil_date, thirukanitham_month_info,
    thirukanitham_tamil_to_gregorian_date,
};
use super::vakya_civil::{
    vakya_gregorian_to_tamil_date, vakya_month_info, vakya_tamil_to_gregorian_date,
};
use super::{ThirukanithamContext, VakyaCivilContext};
use tamil_numerals::{add_gregorian_date, date_difference, GregorianDate};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CalendarSolarDate {
    pub solar_year: i64,
    pub month: u8,
    pub month_name: &'static str,
    pub day: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CalendarSolarMonth {
    pub month: u8,
    pub month_name: &'static str,
    pub start_date: GregorianDate,
    pub end_date_exclusive: GregorianDate,
    pub days: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CalendarSolarYearInfo {
    pub solar_year: i64,
    pub year_cycle: CalendarSolarYearCycleInfo,
    pub start_date: GregorianDate,
    pub end_date_exclusive: GregorianDate,
    pub days: i64,
    pub months: Vec<CalendarSolarMonth>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CalendarSolarYearCycleInfo {
    pub solar_year: i64,
    pub cycle_index: u8,
    pub cycle_name: &'static str,
    pub anchor_solar_year: i64,
    pub anchor_cycle_index: u8,
    pub source_id: &'static str,
    pub source: &'static str,
    pub source_sha256: &'static str,
    pub region_scope: &'static str,
    pub sources: &'static [&'static str],
}

pub fn solar_year_cycle_info(solar_year: i64) -> Result<CalendarSolarYearCycleInfo, String> {
    if !(1..=9_999).contains(&solar_year) {
        return Err("outside supported calendar coverage".into());
    }
    let offset = (solar_year - tables::TAMIL_SOLAR_YEAR_CYCLE_ANCHOR_YEAR).rem_euclid(60);
    let cycle_index = (tables::TAMIL_SOLAR_YEAR_CYCLE_ANCHOR_INDEX - 1 + offset).rem_euclid(60);
    Ok(CalendarSolarYearCycleInfo {
        solar_year,
        cycle_index: u8::try_from(cycle_index + 1).expect("cycle index is one through sixty"),
        cycle_name: tables::TAMIL_SOLAR_YEAR_CYCLE_NAMES
            [usize::try_from(cycle_index).expect("cycle index is nonnegative")],
        anchor_solar_year: tables::TAMIL_SOLAR_YEAR_CYCLE_ANCHOR_YEAR,
        anchor_cycle_index: u8::try_from(tables::TAMIL_SOLAR_YEAR_CYCLE_ANCHOR_INDEX)
            .expect("cycle anchor is one through sixty"),
        source_id: tables::TAMIL_SOLAR_YEAR_CYCLE_SOURCE_ID,
        source: tables::TAMIL_SOLAR_YEAR_CYCLE_SOURCE,
        source_sha256: tables::TAMIL_SOLAR_YEAR_CYCLE_SOURCE_SHA256,
        region_scope: tables::TAMIL_SOLAR_YEAR_CYCLE_REGION_SCOPE,
        sources: &tables::TAMIL_SOLAR_YEAR_CYCLE_SOURCES,
    })
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CalendarSolarDateArithmetic {
    pub tamil_date: CalendarSolarDate,
    pub gregorian_date: GregorianDate,
}

struct SolarDateAddition<'a> {
    solar_year: i64,
    month: i64,
    day: i64,
    unit: &'a str,
    amount: i64,
    overflow: &'a str,
}

fn collect_year<F>(solar_year: i64, mut month_info: F) -> Result<CalendarSolarYearInfo, String>
where
    F: FnMut(i64, i64) -> Result<CalendarSolarMonth, String>,
{
    let mut months = Vec::with_capacity(12);
    let mut days = 0_i64;
    for month in 1..=12 {
        let info = month_info(solar_year, month)?;
        days = days
            .checked_add(info.days)
            .ok_or("outside supported calendar coverage")?;
        months.push(info);
    }
    let start_date = months[0].start_date;
    let end_date_exclusive = months[11].end_date_exclusive;
    if date_difference(start_date, end_date_exclusive) != days {
        return Err("outside supported calendar coverage".into());
    }
    Ok(CalendarSolarYearInfo {
        solar_year,
        year_cycle: solar_year_cycle_info(solar_year)?,
        start_date,
        end_date_exclusive,
        days,
        months,
    })
}

pub fn thirukanitham_solar_year_info(
    solar_year: i64,
    context: ThirukanithamContext,
) -> Result<CalendarSolarYearInfo, String> {
    collect_year(solar_year, |year, month| {
        let info = thirukanitham_month_info(year, month, context)?;
        Ok(CalendarSolarMonth {
            month: info.month,
            month_name: info.month_name,
            start_date: info.start_date,
            end_date_exclusive: info.end_date_exclusive,
            days: info.days,
        })
    })
}

pub fn vakya_solar_year_info(
    solar_year: i64,
    context: VakyaCivilContext,
) -> Result<CalendarSolarYearInfo, String> {
    collect_year(solar_year, |year, month| {
        let info = vakya_month_info(year, month, context)?;
        Ok(CalendarSolarMonth {
            month: info.month,
            month_name: info.month_name,
            start_date: info.start_date,
            end_date_exclusive: info.end_date_exclusive,
            days: info.days,
        })
    })
}

fn add_date<M, R, F>(
    request: SolarDateAddition<'_>,
    mut month_length: M,
    mut to_gregorian: R,
    mut from_gregorian: F,
) -> Result<CalendarSolarDateArithmetic, String>
where
    M: FnMut(i64, i64) -> Result<i64, String>,
    R: FnMut(i64, i64, i64) -> Result<GregorianDate, String>,
    F: FnMut(GregorianDate) -> Result<CalendarSolarDate, String>,
{
    let SolarDateAddition {
        solar_year,
        month,
        day,
        unit,
        amount,
        overflow,
    } = request;
    if !matches!(unit, "days" | "months" | "years") || !matches!(overflow, "reject" | "clamp") {
        return Err("invalid calendar input".into());
    }

    // This reverse conversion validates the complete input against its profile.
    let start_date = to_gregorian(solar_year, month, day)?;
    let (target_year, target_month, target_day) = match unit {
        "days" => {
            let gregorian_date = add_gregorian_date(start_date, "days", amount, "reject")
                .map_err(|_| "outside supported calendar coverage")?;
            let tamil_date = from_gregorian(gregorian_date)?;
            return Ok(CalendarSolarDateArithmetic {
                tamil_date,
                gregorian_date,
            });
        }
        "months" => {
            let absolute = i128::from(solar_year)
                .checked_mul(12)
                .and_then(|value| value.checked_add(i128::from(month - 1)))
                .and_then(|value| value.checked_add(i128::from(amount)))
                .ok_or("outside supported calendar coverage")?;
            (
                i64::try_from(absolute.div_euclid(12))
                    .map_err(|_| "outside supported calendar coverage")?,
                i64::try_from(absolute.rem_euclid(12) + 1)
                    .map_err(|_| "outside supported calendar coverage")?,
                day,
            )
        }
        "years" => (
            solar_year
                .checked_add(amount)
                .ok_or("outside supported calendar coverage")?,
            month,
            day,
        ),
        _ => unreachable!(),
    };
    let target_length = month_length(target_year, target_month)?;
    let target_day = if target_day <= target_length {
        target_day
    } else if overflow == "clamp" {
        target_length
    } else {
        return Err("invalid Tamil date".into());
    };
    let gregorian_date = to_gregorian(target_year, target_month, target_day)?;
    let tamil_date = from_gregorian(gregorian_date)?;
    if tamil_date.solar_year != target_year
        || i64::from(tamil_date.month) != target_month
        || tamil_date.day != target_day
    {
        return Err("outside supported calendar coverage".into());
    }
    Ok(CalendarSolarDateArithmetic {
        tamil_date,
        gregorian_date,
    })
}

pub fn thirukanitham_add_solar_date(
    solar_year: i64,
    month: i64,
    day: i64,
    unit: &str,
    amount: i64,
    overflow: &str,
    context: ThirukanithamContext,
) -> Result<CalendarSolarDateArithmetic, String> {
    add_date(
        SolarDateAddition {
            solar_year,
            month,
            day,
            unit,
            amount,
            overflow,
        },
        |year, month| Ok(thirukanitham_month_info(year, month, context)?.days),
        |year, month, day| {
            thirukanitham_tamil_to_gregorian_date(year, month, day, context)
                .map(|date| date.gregorian_date)
        },
        |date| {
            thirukanitham_gregorian_to_tamil_date(date, context).map(|date| CalendarSolarDate {
                solar_year: date.tamil_date.solar_year,
                month: date.tamil_date.month,
                month_name: date.tamil_date.month_name,
                day: i64::from(date.tamil_date.day),
            })
        },
    )
}

pub fn vakya_add_solar_date(
    solar_year: i64,
    month: i64,
    day: i64,
    unit: &str,
    amount: i64,
    overflow: &str,
    context: VakyaCivilContext,
) -> Result<CalendarSolarDateArithmetic, String> {
    add_date(
        SolarDateAddition {
            solar_year,
            month,
            day,
            unit,
            amount,
            overflow,
        },
        super::vakya_civil::vakya_month_length,
        |year, month, day| {
            vakya_tamil_to_gregorian_date(year, month, day, context).map(|date| date.gregorian_date)
        },
        |date| {
            vakya_gregorian_to_tamil_date(date, context).map(|date| CalendarSolarDate {
                solar_year: date.tamil_date.solar_year,
                month: date.tamil_date.month,
                month_name: date.tamil_date.month_name,
                day: date.tamil_date.day,
            })
        },
    )
}

#[cfg(test)]
mod tests {
    use super::solar_year_cycle_info;
    use tamil_numerals::GregorianDate;

    #[test]
    fn review_regression_final_partial_month_supports_valid_date_arithmetic() {
        let context = super::VakyaCivilContext::new("ujjain", "Asia/Kolkata").unwrap();
        for unit in ["days", "months", "years"] {
            let unchanged =
                super::vakya_add_solar_date(9999, 5, 7, unit, 0, "reject", context).unwrap();
            assert_eq!(
                unchanged.gregorian_date,
                GregorianDate::new(9999, 12, 31).unwrap()
            );
            assert_eq!(unchanged.tamil_date.day, 7);
        }
        let previous =
            super::vakya_add_solar_date(9999, 5, 6, "months", 0, "reject", context).unwrap();
        assert_eq!(
            previous.gregorian_date,
            GregorianDate::new(9999, 12, 30).unwrap()
        );
        let into_final_month =
            super::vakya_add_solar_date(9999, 4, 7, "months", 1, "reject", context).unwrap();
        assert_eq!(
            into_final_month.gregorian_date,
            GregorianDate::new(9999, 12, 31).unwrap()
        );
    }

    #[test]
    fn solar_cycle_anchor_and_independent_chronology_positions() {
        let cases = [
            (187, 1, "Prabhava"),
            (1880, 14, "Vikrama"),
            (1927, 1, "Prabhava"),
            (1941, 15, "Vishu"),
            (1947, 21, "Sarvajit"),
            (2024, 38, "Krodhi"),
            (2025, 39, "Visvavasu"),
            (9999, 33, "Vikari"),
        ];
        for (year, index, name) in cases {
            let info = solar_year_cycle_info(year).unwrap();
            assert_eq!(info.solar_year, year);
            assert_eq!(info.cycle_index, index);
            assert_eq!(info.cycle_name, name);
            assert_eq!(info.anchor_solar_year, 187);
            assert_eq!(info.anchor_cycle_index, 1);
        }
        assert_eq!(
            solar_year_cycle_info(0).unwrap_err(),
            "outside supported calendar coverage"
        );
        assert_eq!(
            solar_year_cycle_info(10_000).unwrap_err(),
            "outside supported calendar coverage"
        );
    }

    #[test]
    fn solar_cycle_repeats_after_sixty_solar_years() {
        for year in 1..=9_939 {
            let first = solar_year_cycle_info(year).unwrap();
            let repeated = solar_year_cycle_info(year + 60).unwrap();
            assert_eq!(repeated.cycle_index, first.cycle_index);
            assert_eq!(repeated.cycle_name, first.cycle_name);
        }
    }
}

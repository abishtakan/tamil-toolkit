//! Standalone Tamil calendar engine covering Thirukanitham (Drik), Vakiya,
//! panchangam limbs, daylight intervals, official holidays, and festival observances.
#![forbid(unsafe_code)]

use tamil_numerals::GregorianDate;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CalendarOfficialHoliday {
    pub date: GregorianDate,
    pub name: &'static str,
    pub categories: &'static [&'static str],
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CalendarOfficialHolidayYearInfo {
    pub jurisdiction: &'static str,
    pub year: i64,
    pub schedule_id: &'static str,
    pub source_id: &'static str,
    pub source: &'static str,
    pub source_url: &'static str,
    pub source_sha256: Option<&'static str>,
    pub reuse_terms_status: &'static str,
    pub scope_note: &'static str,
    pub holidays: Vec<CalendarOfficialHoliday>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct SolarVakya {
    pub rasi: &'static str,
    pub days: i64,
    pub nadis: i64,
    pub vinadis: i64,
}

mod tables {
    use super::SolarVakya;
    include!(concat!(env!("OUT_DIR"), "/calendar_tables.rs"));
}

mod display;
mod drik;
mod holidays;
mod observances;
mod solar_arithmetic;
mod vakya;
mod vakya_civil;

pub use display::{calendar_display_names, CalendarDisplayNames};
pub use drik::{
    thirukanitham_daylight_periods, thirukanitham_gregorian_to_tamil_date,
    thirukanitham_lunar_phase_events, thirukanitham_month_info, thirukanitham_panchangam_at,
    thirukanitham_panchangam_day, thirukanitham_profile_info,
    thirukanitham_tamil_to_gregorian_date, ThirukanithamContext, ThirukanithamDateConversion,
    ThirukanithamDateReverse, ThirukanithamDaylightInterval, ThirukanithamDaylightPeriods,
    ThirukanithamLimb, ThirukanithamLimbs, ThirukanithamLocalTime, ThirukanithamLunarPhaseEvent,
    ThirukanithamMonthInfo, ThirukanithamPanchangamAt, ThirukanithamPanchangamDay,
    ThirukanithamProfileInfo, ThirukanithamRegionInfo, ThirukanithamStationInfo,
    ThirukanithamTamilDate, ThirukanithamTransition, ThirukanithamUtcMinute,
};

pub use vakya::{
    vakya_bhujaantara_from_true_sun, vakya_cara_from_sayana_sun,
    vakya_desantara_from_yojana_distance, vakya_reduce_to_local_true_sunrise, vakya_solar_transits,
    vakya_true_moon_from_kali_day, vakya_true_sun_from_mesha_elapsed, Ahargana, DmsAngle,
    RasiDmsAngle, SolarTransit, VakyaBhujaantara, VakyaCara, VakyaDesantara,
    VakyaLocalSunriseReduction, VakyaSolarYear, VakyaTrueMoon, VakyaTrueSun,
};

pub use vakya_civil::{
    vakya_civil_profile_info, vakya_gregorian_to_tamil_date, vakya_month_info, vakya_panchangam_at,
    vakya_panchangam_day, vakya_tamil_to_gregorian_date, VakyaCivilContext,
    VakyaCivilDateConversion, VakyaCivilDateReverse, VakyaCivilLimb, VakyaCivilLimbs,
    VakyaCivilMonthInfo, VakyaCivilPanchangamAt, VakyaCivilPanchangamDay, VakyaCivilProfileInfo,
    VakyaCivilTamilDate, VakyaCivilTime, VakyaCivilTransition,
};

pub use holidays::calendar_official_holiday_year;
pub use observances::{
    thirukanitham_observances, ThirukanithamObservanceEvent, ThirukanithamObservanceSource,
    ThirukanithamObservances,
};
pub use solar_arithmetic::{
    solar_year_cycle_info, thirukanitham_add_solar_date, thirukanitham_solar_year_info,
    vakya_add_solar_date, vakya_solar_year_info, CalendarSolarDate, CalendarSolarDateArithmetic,
    CalendarSolarMonth, CalendarSolarYearCycleInfo, CalendarSolarYearInfo,
};

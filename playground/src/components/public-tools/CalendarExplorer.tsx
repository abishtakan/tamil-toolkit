import { useState, useEffect, useMemo } from "react";
import {
  type CalendarProfileComparisonResult,
  calendarDefinitions,
  compareCalendarProfiles,
  formatTamilDate,
  getThiruvalluvarYearInfo,
  isEngineReady,
  tt,
} from "../../lib/engine";
import { runWorkerExecute } from "../../lib/worker-client";
import { useLanguage } from "../../lib/i18n";
import { ToolHeader } from "../common/ToolHeader";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { CopyButton } from "../common/CopyButton";
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, Loader2, MapPin, Sunrise, Sunset } from "lucide-react";

interface CalendarCity {
  id: string;
  labelEn: string;
  labelTa: string;
  region: "TN" | "SL";
  lat: number;
  lon: number;
  elev: number;
  tz: "Asia/Kolkata" | "Asia/Colombo";
}

const PRESET_CITIES: readonly CalendarCity[] = [
  { id: "chennai", labelEn: "Chennai", labelTa: "சென்னை", region: "TN", lat: 13.08784, lon: 80.27847, elev: 14, tz: "Asia/Kolkata" },
  { id: "madurai", labelEn: "Madurai", labelTa: "மதுரை", region: "TN", lat: 9.9252, lon: 78.1198, elev: 134, tz: "Asia/Kolkata" },
  { id: "coimbatore", labelEn: "Coimbatore", labelTa: "கோயம்புத்தூர்", region: "TN", lat: 11.0168, lon: 76.9558, elev: 411, tz: "Asia/Kolkata" },
  { id: "jaffna", labelEn: "Jaffna", labelTa: "யாழ்ப்பாணம்", region: "SL", lat: 9.66845, lon: 80.00742, elev: 7, tz: "Asia/Colombo" },
  { id: "colombo", labelEn: "Colombo", labelTa: "கொழும்பு", region: "SL", lat: 6.93548, lon: 79.84868, elev: 7, tz: "Asia/Colombo" },
  { id: "batticaloa", labelEn: "Batticaloa", labelTa: "மட்டக்களப்பு", region: "SL", lat: 7.717, lon: 81.7, elev: 3, tz: "Asia/Colombo" },
];

const TAMIL_MONTHS = [
  { num: 1, en: "Chithirai", ta: "சித்திரை" },
  { num: 2, en: "Vaikasi", ta: "வைகாசி" },
  { num: 3, en: "Aani", ta: "ஆனி" },
  { num: 4, en: "Aadi", ta: "ஆடி" },
  { num: 5, en: "Avani", ta: "ஆவணி" },
  { num: 6, en: "Purattasi", ta: "புரட்டாசி" },
  { num: 7, en: "Aippasi", ta: "ஐப்பசி" },
  { num: 8, en: "Karthigai", ta: "கார்த்திகை" },
  { num: 9, en: "Margazhi", ta: "மார்கழி" },
  { num: 10, en: "Thai", ta: "தை" },
  { num: 11, en: "Maasi", ta: "மாசி" },
  { num: 12, en: "Panguni", ta: "பங்குனி" },
] as const;

const TN_OBSERVANCES_CONTEXT: tt.CalendarContext = {
  region: "TN",
  latitude_microdegrees: 13087840,
  longitude_microdegrees: 80278470,
  elevation_meters: 14,
  time_zone: "Asia/Kolkata",
};

const yearInfoCache = new Map<string, tt.TamilYearInfo>();
const observancesCache = new Map<string, tt.CalendarObservanceEvent[]>();

type CalendarTab = "daily" | "convertYear" | "festivals" | "compare";

function getTodayIso(): string {
  return new Date().toISOString().split("T")[0];
}

function shiftIsoDate(isoDate: string, deltaDays: number): string {
  const parts = isoDate.split("-").map(Number);
  if (parts.length !== 3 || parts.some((n) => !Number.isFinite(n))) return isoDate;
  const [y, m, d] = parts;
  const dt = new Date(Date.UTC(y, m - 1, d + deltaDays));
  return dt.toISOString().split("T")[0];
}

function formatHm(time?: { hour: number; minute: number }): string {
  if (!time) return "—";
  const h = time.hour % 12 || 12;
  const ampm = time.hour >= 12 ? "PM" : "AM";
  const m = time.minute.toString().padStart(2, "0");
  return `${h}:${m} ${ampm}`;
}

function formatMinuteOfDay(mins?: number | null): string {
  if (typeof mins !== "number" || !Number.isFinite(mins)) return "—";
  const total = ((Math.round(mins) % 1440) + 1440) % 1440;
  return formatHm({ hour: Math.floor(total / 60), minute: total % 60 });
}

function formatGregorian(d: tt.GregorianDate): string {
  return `${d.year}-${String(d.month).padStart(2, "0")}-${String(d.day).padStart(2, "0")}`;
}

function formatLimbTithi(limb?: tt.CalendarLimb | null): string {
  if (!limb) return "—";
  const paksha = limb.paksha === "shukla" ? "Shukla" : limb.paksha === "krishna" ? "Krishna" : "";
  return paksha ? `${paksha} ${limb.name}` : limb.name;
}

interface CalendarExplorerProps {
  engineReady?: boolean;
}

export function CalendarExplorer({ engineReady }: CalendarExplorerProps) {
  const { t, language } = useLanguage();
  const ready = engineReady ?? isEngineReady();

  const [activeTab, setActiveTab] = useState<CalendarTab>("daily");

  // Shared Date & City
  const [dateStr, setDateStr] = useState<string>(getTodayIso);
  const [selectedCityId, setSelectedCityId] = useState<string>("chennai");
  const [gpsLocation, setGpsLocation] = useState<{
    region: "TN" | "SL";
    lat: number;
    lon: number;
    tz: "Asia/Kolkata" | "Asia/Colombo";
  } | null>(null);
  const [gpsNotice, setGpsNotice] = useState<string | null>(null);

  // Daily Sheet options
  const [profileMode, setProfileMode] = useState<"thirukanitham" | "vakya">("thirukanitham");
  const [tamilDigits, setTamilDigits] = useState<boolean>(false);
  const [atTimeStr, setAtTimeStr] = useState<string>("09:00");

  // Tab 2: Reverse conversion & Year schedule
  const [revSolarYear, setRevSolarYear] = useState<number>(2026);
  const [revTamilMonth, setRevTamilMonth] = useState<number>(1);
  const [revTamilDay, setRevTamilDay] = useState<number>(1);
  const [addUnit, setAddUnit] = useState<"days" | "months" | "years">("days");
  const [addAmount, setAddAmount] = useState<number>(15);

  // Tab 3: Festivals & Holidays
  const [festYear, setFestYear] = useState<number>(2026);
  const [festMonthFilter, setFestMonthFilter] = useState<number>(() => new Date().getMonth() + 1);
  const [holidayRegion, setHolidayRegion] = useState<"TN" | "SL">("TN");

  // Async worker-backed state for heavy Tab 2 (tamil_year_info) & Tab 3 (calendar_observances)
  const [yearInfo, setYearInfo] = useState<tt.TamilYearInfo | null>(null);
  const [yearError, setYearError] = useState<string | null>(null);
  const [yearLoading, setYearLoading] = useState<boolean>(false);

  const [observances, setObservances] = useState<tt.CalendarObservanceEvent[]>([]);
  const [obsError, setObsError] = useState<string | null>(null);
  const [obsLoading, setObsLoading] = useState<boolean>(false);

  const activeLocation = useMemo(() => {
    if (selectedCityId === "gps" && gpsLocation) {
      return {
        label: t.tools.calendar.gpsLocationLabel,
        region: gpsLocation.region,
        lat: gpsLocation.lat,
        lon: gpsLocation.lon,
        elev: 10,
        tz: gpsLocation.tz,
      };
    }
    const city = PRESET_CITIES.find((c) => c.id === selectedCityId) ?? PRESET_CITIES[0];
    return {
      label: language === "ta" ? city.labelTa : city.labelEn,
      region: city.region,
      lat: city.lat,
      lon: city.lon,
      elev: city.elev,
      tz: city.tz,
    };
  }, [selectedCityId, gpsLocation, language, t]);

  const drikCtx: tt.CalendarContext = useMemo(
    () => ({
      region: activeLocation.region,
      latitude_microdegrees: Math.round(activeLocation.lat * 1_000_000),
      longitude_microdegrees: Math.round(activeLocation.lon * 1_000_000),
      elevation_meters: activeLocation.elev,
      time_zone: activeLocation.tz,
    }),
    [activeLocation]
  );

  const vakyaCtx: tt.VakyaCivilContext = useMemo(
    () => ({
      reference_station: "ujjain",
      time_zone: activeLocation.tz,
    }),
    [activeLocation.tz]
  );

  const activeCtx: tt.CalendarContextInput = profileMode === "vakya" ? vakyaCtx : drikCtx;
  const activeDefId =
    profileMode === "vakya" ? calendarDefinitions.vakyaCivil : calendarDefinitions.thirukanitham;

  const parsedDate = useMemo<tt.GregorianDate | null>(() => {
    const parts = dateStr.split("-").map(Number);
    if (parts.length !== 3 || parts.some((n) => !Number.isFinite(n))) return null;
    return { year: parts[0], month: parts[1], day: parts[2] };
  }, [dateStr]);

  // Tab 1: Daily Sheet Calculation (lazy when daily tab active)
  const dailyData = useMemo(() => {
    if (!ready || !parsedDate || activeTab !== "daily") return null;

    let solarDate = "";
    let solarYear = parsedDate.year;
    let thiruvalluvarYear = 0;

    try {
      const conv = tt.gregorian_to_tamil_date(parsedDate, activeCtx, activeDefId);
      if (conv?.tamil_date) {
        solarYear = conv.tamil_date.solar_year;
        solarDate = `${conv.tamil_date.month_name} ${conv.tamil_date.day}, ${solarYear}`;
        thiruvalluvarYear = solarYear + 31;
      }
    } catch {
      // ignore out-of-range
    }

    try {
      const tv = getThiruvalluvarYearInfo(parsedDate, drikCtx);
      if (tv?.thiruvalluvar_year) thiruvalluvarYear = tv.thiruvalluvar_year;
    } catch {
      // fallback preserved
    }

    let cycleYearTitle = "";
    try {
      const cycle = tt.tamil_year_cycle_info(solarYear, activeCtx, activeDefId);
      if (cycle?.cycle_name) cycleYearTitle = cycle.cycle_name;
    } catch {
      // ignore
    }

    let holidays: string[] = [];
    try {
      const holidayInfo = tt.calendar_official_holidays(activeLocation.region, parsedDate.year);
      if (holidayInfo?.holidays) {
        holidays = holidayInfo.holidays
          .filter(
            (h) =>
              h.date.year === parsedDate.year &&
              h.date.month === parsedDate.month &&
              h.date.day === parsedDate.day
          )
          .map((h) => h.name);
      }
    } catch {
      holidays = [];
    }

    let rahu = "—";
    let yamagandam = "—";
    let gulikai = "—";
    let sunrise = "—";
    let sunset = "—";
    try {
      const periods = tt.calendar_daylight_periods(parsedDate, drikCtx);
      if (periods?.intervals) {
        const r = periods.intervals.find((p) => p.period === "rahukalam");
        const y = periods.intervals.find((p) => p.period === "yamagandam");
        const g = periods.intervals.find((p) => p.period === "kuligai");
        if (r) rahu = `${formatHm(r.start_local_time)} – ${formatHm(r.end_local_time)}`;
        if (y) yamagandam = `${formatHm(y.start_local_time)} – ${formatHm(y.end_local_time)}`;
        if (g) gulikai = `${formatHm(g.start_local_time)} – ${formatHm(g.end_local_time)}`;
      }
      if (periods?.sunrise_local_time) sunrise = formatHm(periods.sunrise_local_time);
      if (periods?.sunset_local_time) sunset = formatHm(periods.sunset_local_time);
    } catch {
      // ignore
    }

    let nakshatra = "—";
    let tithi = "—";
    let yoga = "—";
    let karana = "—";
    let vara = "";
    let transitions: tt.PanchangamTransition[] = [];
    try {
      const panchangam = tt.panchangam_day(parsedDate, activeCtx, activeDefId);
      if (panchangam) {
        vara = panchangam.vara;
        const limbs = panchangam.limbs_at_sunrise;
        if (limbs?.nakshatra?.name) nakshatra = limbs.nakshatra.name;
        tithi = formatLimbTithi(limbs?.tithi);
        if (limbs?.yoga?.name) yoga = limbs.yoga.name;
        if (limbs?.karana?.name) karana = limbs.karana.name;
        if (sunrise === "—") sunrise = formatMinuteOfDay(panchangam.sunrise_minute_of_day);
        if (sunset === "—") sunset = formatMinuteOfDay(panchangam.sunset_minute_of_day);
        transitions = panchangam.transitions ?? [];
      }
    } catch {
      // ignore
    }

    return {
      solarDate,
      thiruvalluvarYear,
      cycleYearTitle,
      holidays,
      rahu,
      yamagandam,
      gulikai,
      sunrise,
      sunset,
      nakshatra,
      tithi,
      yoga,
      karana,
      vara,
      transitions,
    };
  }, [ready, activeTab, parsedDate, activeCtx, drikCtx, activeDefId, activeLocation.region]);

  // Separate lightweight memos so toggling digits or time does not recompute full daily panchangam
  const formattedTamil = useMemo(() => {
    if (!ready || !parsedDate || activeTab !== "daily") return "";
    try {
      return formatTamilDate(
        parsedDate,
        activeCtx,
        "tamil",
        tamilDigits ? "tamil" : "latin",
        "weekday_day_month_year",
        activeDefId
      );
    } catch {
      return "";
    }
  }, [ready, activeTab, parsedDate, activeCtx, activeDefId, tamilDigits]);

  const atTimePanchangam = useMemo<tt.PanchangamAt | null>(() => {
    if (!ready || !parsedDate || activeTab !== "daily") return null;
    try {
      const [hh, mm] = atTimeStr.split(":").map(Number);
      if (!Number.isFinite(hh) || !Number.isFinite(mm)) return null;
      // Asia/Kolkata and Asia/Colombo are both UTC+05:30 (+19800s)
      const utcMs =
        Date.UTC(parsedDate.year, parsedDate.month - 1, parsedDate.day, hh, mm, 0) -
        19800 * 1000;
      return tt.panchangam_at(Math.floor(utcMs / 1000), activeCtx, activeDefId);
    } catch {
      return null;
    }
  }, [ready, activeTab, parsedDate, activeCtx, activeDefId, atTimeStr]);

  // Tab 2: Lightweight Reverse Conversion & Tamil Date Math (lazy on tab active)
  const convertYearData = useMemo(() => {
    if (!ready || activeTab !== "convertYear") return null;
    const monthMeta = TAMIL_MONTHS.find((m) => m.num === revTamilMonth) ?? TAMIL_MONTHS[0];
    const tamilInput: tt.TamilSolarDate = {
      solar_year: revSolarYear,
      month: revTamilMonth,
      month_name: monthMeta.en,
      day: revTamilDay,
    };

    let reverseGregorian = "";
    let reverseError: string | null = null;
    try {
      const res = tt.tamil_to_gregorian_date(tamilInput, drikCtx);
      reverseGregorian = formatGregorian(res.gregorian_date);
    } catch (err: unknown) {
      reverseError = err instanceof Error ? err.message : String(err);
    }

    let addedTamilResult: tt.AddTamilDateResult | null = null;
    let addError: string | null = null;
    try {
      addedTamilResult = tt.add_tamil_date(tamilInput, addUnit, addAmount, drikCtx, "clamp");
    } catch (err: unknown) {
      addError = err instanceof Error ? err.message : String(err);
    }

    return {
      reverseGregorian,
      reverseError,
      addedTamilResult,
      addError,
    };
  }, [ready, activeTab, revSolarYear, revTamilMonth, revTamilDay, addUnit, addAmount, drikCtx]);

  // Tab 2 Async Cached 12-Month Solar Schedule (off main UI thread via Web Worker)
  useEffect(() => {
    if (!ready || activeTab !== "convertYear") return;
    const key = `${revSolarYear}|${drikCtx.region}|${drikCtx.latitude_microdegrees}|${drikCtx.longitude_microdegrees}`;
    const cached = yearInfoCache.get(key);
    if (cached) {
      setYearInfo(cached);
      setYearError(null);
      setYearLoading(false);
      return;
    }

    let cancelled = false;
    setYearLoading(true);
    setYearError(null);

    runWorkerExecute<tt.TamilYearInfo>("tamil_year_info", {
      definition_id: calendarDefinitions.thirukanitham,
      solar_year: revSolarYear,
      context: drikCtx,
    })
      .then((res) => {
        if (cancelled) return;
        yearInfoCache.set(key, res);
        setYearInfo(res);
        setYearError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setYearError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setYearLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [ready, activeTab, revSolarYear, drikCtx]);

  // Tab 3 Lightweight: Official Holidays (TN & SL) + Lunar Phases (lazy on tab active)
  const holidaysAndLunar = useMemo(() => {
    if (!ready || activeTab !== "festivals") return null;

    let officialHolidays: tt.OfficialHolidayYearInfo["holidays"] = [];
    let holError: string | null = null;
    try {
      const res = tt.calendar_official_holidays(holidayRegion, festYear);
      officialHolidays = res.holidays ?? [];
    } catch (err: unknown) {
      holError = err instanceof Error ? err.message : String(err);
    }

    let lunarEvents: tt.LunarPhaseEvent[] = [];
    let lunarError: string | null = null;
    try {
      const m = festMonthFilter > 0 ? festMonthFilter : (parsedDate?.month ?? 4);
      const startSec = Math.floor(Date.UTC(festYear, m - 1, 1) / 1000);
      const endSec = Math.floor(Date.UTC(festYear, m, 1) / 1000);
      const res = tt.lunar_phase_events(startSec, endSec);
      lunarEvents = res.events ?? [];
    } catch (err: unknown) {
      lunarError = err instanceof Error ? err.message : String(err);
    }

    return { officialHolidays, holError, lunarEvents, lunarError };
  }, [ready, activeTab, festYear, festMonthFilter, holidayRegion, parsedDate]);

  // Tab 3 Async Cached Observances (off main UI thread via Web Worker; explicit TN scope when SL city selected)
  useEffect(() => {
    if (!ready || activeTab !== "festivals") return;
    const obsCtx = drikCtx.region === "TN" ? drikCtx : TN_OBSERVANCES_CONTEXT;
    const key = `${festYear}|${festMonthFilter}|${obsCtx.region}|${obsCtx.latitude_microdegrees}|${obsCtx.longitude_microdegrees}`;
    const cached = observancesCache.get(key);
    if (cached) {
      setObservances(cached);
      setObsError(null);
      setObsLoading(false);
      return;
    }

    let cancelled = false;
    setObsLoading(true);
    setObsError(null);

    runWorkerExecute<tt.CalendarObservances>("calendar_observances", {
      definition_id: calendarDefinitions.thirukanitham,
      rule_set: "thirukanitham-tamil-named-observances-v1",
      gregorian_year: festYear,
      ...(festMonthFilter > 0 ? { month: festMonthFilter } : {}),
      context: obsCtx,
    })
      .then((res) => {
        if (cancelled) return;
        const events = res.events ?? [];
        observancesCache.set(key, events);
        setObservances(events);
        setObsError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setObsError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setObsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [ready, activeTab, festYear, festMonthFilter, drikCtx]);

  // Tab 4: Thirukanitham vs Vakya Profile Comparison (lazy on tab active)
  const comparisonData = useMemo(() => {
    if (!ready || !parsedDate || activeTab !== "compare") {
      return { result: null as CalendarProfileComparisonResult | null, error: null as string | null };
    }
    try {
      const result = compareCalendarProfiles({
        date: parsedDate,
        thirukanitham_context: drikCtx,
        vakya_context: vakyaCtx,
      });
      return { result, error: null };
    } catch (err: unknown) {
      return { result: null, error: err instanceof Error ? err.message : String(err) };
    }
  }, [ready, activeTab, parsedDate, drikCtx, vakyaCtx]);

  const requestGeolocation = () => {
    setGpsNotice(null);
    if (typeof navigator !== "undefined" && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;
          if (lat >= 5.8 && lat <= 9.9 && lon >= 79.4 && lon <= 82.0) {
            setGpsLocation({ region: "SL", lat, lon, tz: "Asia/Colombo" });
            setSelectedCityId("gps");
            setHolidayRegion("SL");
          } else if (lat >= 8.0 && lat <= 13.7 && lon >= 76.0 && lon <= 80.5) {
            setGpsLocation({ region: "TN", lat, lon, tz: "Asia/Kolkata" });
            setSelectedCityId("gps");
            setHolidayRegion("TN");
          } else {
            setGpsNotice(t.tools.calendar.outOfBoundsNotice);
            setSelectedCityId("chennai");
          }
        },
        () => {
          setSelectedCityId("chennai");
        }
      );
    }
  };

  const copySummary = dailyData
    ? `${formattedTamil || dailyData.solarDate || dateStr} | ${t.tools.calendar.thiruvalluvarYearLabel}: ${dailyData.thiruvalluvarYear || "—"} | ${t.tools.calendar.nakshatraLabel}: ${dailyData.nakshatra} | ${t.tools.calendar.rahuKalamLabel}: ${dailyData.rahu}`
    : dateStr;

  const tabSwitcher = (
    <div className="inline-flex flex-wrap items-center gap-1 p-1 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)]">
      {(
        [
          { id: "daily", label: t.tools.calendar.tabDaily },
          { id: "convertYear", label: t.tools.calendar.tabConvertYear },
          { id: "festivals", label: t.tools.calendar.tabFestivals },
          { id: "compare", label: t.tools.calendar.tabCompare },
        ] as const
      ).map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => setActiveTab(tab.id)}
          className={`px-3 py-1.5 min-h-[36px] rounded-lg text-xs font-medium transition-colors cursor-pointer ${
            activeTab === tab.id
              ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
              : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.calendar.title}
        description={t.tools.calendar.desc}
        actions={
          <CopyButton
            text={copySummary}
            label={t.actions.copy}
            copiedLabel={t.actions.copied}
            size="sm"
            variant="outline"
          />
        }
      />

      {tabSwitcher}

      {/* Shared Date & City Bar (on Daily and Compare tabs) */}
      {(activeTab === "daily" || activeTab === "compare") && (
        <Card className="p-4 sm:p-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label htmlFor="calendar-date-input" className="text-xs font-semibold text-[var(--color-mai)] block">
                {t.tools.calendar.dateSelectLabel}
              </label>
              <div className="flex items-center gap-1.5">
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setDateStr((d) => shiftIsoDate(d, -1))}
                  aria-label={t.tools.calendar.prevDay}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <input
                  id="calendar-date-input"
                  type="date"
                  value={dateStr}
                  onChange={(e) => setDateStr(e.target.value)}
                  className="flex-1 min-h-[44px] rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] px-3 py-2 text-sm font-mono-tamil text-[var(--color-mai)] focus-visible:outline-none focus-visible:border-[var(--color-semman)]"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setDateStr((d) => shiftIsoDate(d, 1))}
                  aria-label={t.tools.calendar.nextDay}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  size="md"
                  onClick={() => setDateStr(getTodayIso())}
                  className="text-xs shrink-0"
                >
                  {t.tools.calendar.todayButton}
                </Button>
              </div>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="calendar-city-select" className="text-xs font-semibold text-[var(--color-mai)] block">
                {t.tools.calendar.coordsLabel}
              </label>
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <MapPin className="w-3.5 h-3.5 text-[var(--color-semman)] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <select
                    id="calendar-city-select"
                    value={selectedCityId}
                    onChange={(e) => {
                      setGpsNotice(null);
                      const id = e.target.value;
                      setSelectedCityId(id);
                      const matched = PRESET_CITIES.find((c) => c.id === id);
                      if (matched) setHolidayRegion(matched.region);
                    }}
                    className="w-full min-h-[44px] pl-9 pr-3 py-2 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-sm text-[var(--color-mai)] focus-visible:outline-none focus-visible:border-[var(--color-semman)]"
                  >
                    {PRESET_CITIES.map((city) => (
                      <option key={city.id} value={city.id}>
                        {language === "ta" ? city.labelTa : city.labelEn} ({city.region})
                      </option>
                    ))}
                    {gpsLocation && (
                      <option value="gps">{t.tools.calendar.gpsLocationLabel}</option>
                    )}
                  </select>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="md"
                  onClick={requestGeolocation}
                  className="text-xs shrink-0"
                >
                  {t.tools.calendar.locationPrompt}
                </Button>
              </div>
            </div>
          </div>

          {activeTab === "daily" && (
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-[var(--border-line)] text-xs">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[var(--color-muted)] font-semibold">
                  {t.tools.calendar.profileLabel}:
                </span>
                <div className="inline-flex items-center gap-1 p-0.5 rounded-lg bg-[var(--bg-canvas)] border border-[var(--border-line)]">
                  <button
                    type="button"
                    onClick={() => setProfileMode("thirukanitham")}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium cursor-pointer ${
                      profileMode === "thirukanitham"
                        ? "bg-[var(--color-semman)] text-[#faf7f2]"
                        : "text-[var(--color-muted)]"
                    }`}
                  >
                    {t.tools.calendar.profileThirukanitham}
                  </button>
                  <button
                    type="button"
                    onClick={() => setProfileMode("vakya")}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium cursor-pointer ${
                      profileMode === "vakya"
                        ? "bg-[var(--color-semman)] text-[#faf7f2]"
                        : "text-[var(--color-muted)]"
                    }`}
                  >
                    {t.tools.calendar.profileVakya}
                  </button>
                </div>
              </div>

              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={tamilDigits}
                  onChange={(e) => setTamilDigits(e.target.checked)}
                  className="accent-[var(--color-semman)] w-4 h-4 cursor-pointer"
                />
                <span>{t.tools.calendar.digitsToggle}</span>
              </label>
            </div>
          )}

          {gpsNotice && (
            <p className="text-xs text-[var(--color-sandhanam)]">{gpsNotice}</p>
          )}
        </Card>
      )}

      {/* TAB 1: DAILY CALENDAR SHEET */}
      {activeTab === "daily" && (
        <div className="space-y-6">
          <Card className="p-5 sm:p-7 border-l-4 border-l-[var(--color-semman)] space-y-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-[var(--color-semman)] uppercase tracking-wider">
                  <span>{t.tools.calendar.tamilDateLabel}</span>
                  {dailyData?.vara && (
                    <span className="text-[var(--color-muted)]">· {dailyData.vara}</span>
                  )}
                </div>
                <p className="text-2xl sm:text-3xl font-tamil font-bold text-[var(--color-mai)]">
                  {formattedTamil || dailyData?.solarDate || "—"}
                </p>
                {dailyData?.solarDate && formattedTamil && (
                  <p className="text-xs font-mono-tamil text-[var(--color-muted)]">
                    {dailyData.solarDate}
                  </p>
                )}
                <p className="text-sm text-[var(--color-muted)]">
                  {t.tools.calendar.thiruvalluvarYearLabel}:{" "}
                  <strong className="text-[var(--color-mai)] font-mono-tamil">
                    {dailyData?.thiruvalluvarYear || "—"}
                  </strong>
                  {" · "}
                  <span>{activeLocation.label}</span>
                </p>
              </div>

              <Badge variant="terracotta">
                <CalendarIcon className="w-3.5 h-3.5 mr-1" />
                {dailyData?.cycleYearTitle || t.tools.calendar.yearFallback}
              </Badge>
            </div>

            <div className="pt-4 border-t border-[var(--border-line)] flex flex-wrap items-center gap-6 text-xs text-[var(--color-muted)]">
              <div className="flex items-center gap-2">
                <Sunrise className="w-4 h-4 text-[var(--color-sandhanam)]" />
                <span>{t.tools.calendar.sunriseLabel}:</span>
                <strong className="font-mono-tamil text-[var(--color-mai)]">
                  {dailyData?.sunrise || "—"}
                </strong>
              </div>
              <div className="flex items-center gap-2">
                <Sunset className="w-4 h-4 text-[var(--color-semman)]" />
                <span>{t.tools.calendar.sunsetLabel}:</span>
                <strong className="font-mono-tamil text-[var(--color-mai)]">
                  {dailyData?.sunset || "—"}
                </strong>
              </div>
            </div>
          </Card>

          <section className="space-y-2.5">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
              {t.tools.calendar.panchangamHeading}
            </h2>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
              {[
                { label: t.tools.calendar.nakshatraLabel, value: dailyData?.nakshatra },
                { label: t.tools.calendar.tithiLabel, value: dailyData?.tithi },
                { label: t.tools.calendar.yogaLabel, value: dailyData?.yoga },
                { label: t.tools.calendar.karanaLabel, value: dailyData?.karana },
              ].map((item) => (
                <Card key={item.label} className="p-4 space-y-1">
                  <span className="text-xs font-medium text-[var(--color-muted)] block">
                    {item.label}
                  </span>
                  <p className="text-sm sm:text-base font-semibold text-[var(--color-mai)]">
                    {item.value || "—"}
                  </p>
                </Card>
              ))}
            </div>
          </section>

          {/* Panchangam at Specific Local Time + Daily Transitions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="p-4 sm:p-5 space-y-3">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
                  {t.tools.calendar.atTimeHeading}
                </h3>
                <input
                  type="time"
                  value={atTimeStr}
                  onChange={(e) => setAtTimeStr(e.target.value)}
                  aria-label={t.tools.calendar.atTimeLabel}
                  className="px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] font-mono-tamil text-xs text-[var(--color-mai)]"
                />
              </div>
              {atTimePanchangam ? (
                <div className="grid grid-cols-2 gap-2.5 text-xs">
                  <div>
                    <span className="text-[var(--color-muted)] block">{t.tools.calendar.nakshatraLabel}</span>
                    <strong className="text-[var(--color-mai)]">
                      {atTimePanchangam.limbs.nakshatra.name}
                    </strong>
                  </div>
                  <div>
                    <span className="text-[var(--color-muted)] block">{t.tools.calendar.tithiLabel}</span>
                    <strong className="text-[var(--color-mai)]">
                      {formatLimbTithi(atTimePanchangam.limbs.tithi)}
                    </strong>
                  </div>
                  <div>
                    <span className="text-[var(--color-muted)] block">{t.tools.calendar.yogaLabel}</span>
                    <strong className="text-[var(--color-mai)]">
                      {atTimePanchangam.limbs.yoga.name}
                    </strong>
                  </div>
                  <div>
                    <span className="text-[var(--color-muted)] block">{t.tools.calendar.karanaLabel}</span>
                    <strong className="text-[var(--color-mai)]">
                      {atTimePanchangam.limbs.karana.name}
                    </strong>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-[var(--color-muted)]">{t.tools.calendar.panchangamError}</p>
              )}
            </Card>

            <Card className="p-4 sm:p-5 space-y-2.5">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
                {t.tools.calendar.transitionsHeading}
              </h3>
              {dailyData && dailyData.transitions.length > 0 ? (
                <ul className="space-y-1.5 text-xs">
                  {dailyData.transitions.map((tr, i) => (
                    <li key={i} className="flex items-center justify-between gap-2 py-1 border-b border-[var(--border-line)]/50 last:border-0">
                      <span className="capitalize font-medium text-[var(--color-mai)]">
                        {tr.limb} ({tr.from_index} → {tr.to_index})
                      </span>
                      <span className="font-mono-tamil text-[var(--color-muted)]">
                        {formatMinuteOfDay(tr.minute_of_day)}
                        {tr.day_offset !== 0 ? ` (+${tr.day_offset}d)` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-[var(--color-muted)]">{t.tools.calendar.noTransitions}</p>
              )}
            </Card>
          </div>

          <section className="space-y-2.5">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
              {t.tools.calendar.daylightHeading}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
              {[
                { label: t.tools.calendar.rahuKalamLabel, value: dailyData?.rahu },
                { label: t.tools.calendar.yamagandamLabel, value: dailyData?.yamagandam },
                { label: t.tools.calendar.gulikaiLabel, value: dailyData?.gulikai },
              ].map((slot) => (
                <Card key={slot.label} className="p-4 space-y-1">
                  <span className="text-xs font-medium text-[var(--color-muted)] block">
                    {slot.label}
                  </span>
                  <p className="text-sm sm:text-base font-mono-tamil font-semibold text-[var(--color-mai)]">
                    {slot.value || "—"}
                  </p>
                </Card>
              ))}
            </div>
          </section>

          {dailyData && dailyData.holidays.length > 0 && (
            <Card className="p-4 border-l-4 border-l-[var(--color-sandhanam)] space-y-2">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[var(--color-sandhanam)]" />
                <span className="text-xs font-bold text-[var(--color-mai)] uppercase tracking-wide">
                  {t.tools.calendar.holidayLabel} ({activeLocation.region})
                </span>
              </div>
              <ul className="list-disc list-inside text-sm font-tamil text-[var(--color-mai)] font-medium space-y-1">
                {dailyData.holidays.map((h, i) => (
                  <li key={i}>{h}</li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      )}

      {/* TAB 2: TAMIL -> GREGORIAN, TAMIL DATE ARITHMETIC & 12-MONTH YEAR TABLE */}
      {activeTab === "convertYear" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <Card className="p-5 space-y-4">
              <h2 className="text-sm font-bold text-[var(--color-mai)]">
                {t.tools.calendar.reverseConvertHeading}
              </h2>
              <div className="grid grid-cols-3 gap-2.5">
                <div className="space-y-1">
                  <label className="text-xs text-[var(--color-muted)] block">
                    {t.tools.calendar.tamilYearLabel}
                  </label>
                  <input
                    type="number"
                    min="2023"
                    max="2027"
                    value={revSolarYear}
                    onChange={(e) => setRevSolarYear(Number.parseInt(e.target.value, 10) || 2026)}
                    className="w-full min-h-[38px] px-2.5 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-mono-tamil text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-[var(--color-muted)] block">
                    {t.tools.calendar.tamilMonthLabel}
                  </label>
                  <select
                    value={revTamilMonth}
                    onChange={(e) => setRevTamilMonth(Number.parseInt(e.target.value, 10))}
                    className="w-full min-h-[38px] px-2 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-sm"
                  >
                    {TAMIL_MONTHS.map((m) => (
                      <option key={m.num} value={m.num}>
                        {language === "ta" ? m.ta : m.en}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-[var(--color-muted)] block">
                    {t.tools.calendar.tamilDayLabel}
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="32"
                    value={revTamilDay}
                    onChange={(e) => setRevTamilDay(Number.parseInt(e.target.value, 10) || 1)}
                    className="w-full min-h-[38px] px-2.5 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-mono-tamil text-sm"
                  />
                </div>
              </div>

              {convertYearData?.reverseError ? (
                <p className="text-xs text-red-600 dark:text-red-400">{convertYearData.reverseError}</p>
              ) : (
                <div className="p-3.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] flex items-center justify-between">
                  <div>
                    <span className="text-[11px] text-[var(--color-muted)] block">
                      {t.tools.calendar.gregorianResultLabel}
                    </span>
                    <span className="text-lg font-mono-tamil font-bold text-[var(--color-semman)]">
                      {convertYearData?.reverseGregorian || "—"}
                    </span>
                  </div>
                  {convertYearData?.reverseGregorian && (
                    <CopyButton text={convertYearData.reverseGregorian} size="sm" variant="ghost" />
                  )}
                </div>
              )}
            </Card>

            <Card className="p-5 space-y-4">
              <h2 className="text-sm font-bold text-[var(--color-mai)]">
                {t.tools.calendar.addTamilDateHeading}
              </h2>
              <div className="grid grid-cols-2 gap-2.5">
                <div className="space-y-1">
                  <label className="text-xs text-[var(--color-muted)] block">
                    {t.tools.numeral.addAmountLabel}
                  </label>
                  <input
                    type="number"
                    value={addAmount}
                    onChange={(e) => setAddAmount(Number.parseInt(e.target.value, 10) || 0)}
                    className="w-full min-h-[38px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-mono-tamil text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-[var(--color-muted)] block">
                    {t.tools.numeral.addUnitLabel}
                  </label>
                  <select
                    value={addUnit}
                    onChange={(e) => setAddUnit(e.target.value as "days" | "months" | "years")}
                    className="w-full min-h-[38px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-sm"
                  >
                    <option value="days">{t.tools.numeral.unitDays}</option>
                    <option value="months">{t.tools.numeral.unitMonths}</option>
                    <option value="years">{t.tools.numeral.unitYears}</option>
                  </select>
                </div>
              </div>

              {convertYearData?.addError ? (
                <p className="text-xs text-red-600 dark:text-red-400">{convertYearData.addError}</p>
              ) : convertYearData?.addedTamilResult ? (
                <div className="p-3.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-1">
                  <p className="text-base font-bold text-[var(--color-mai)]">
                    {convertYearData.addedTamilResult.tamil_date.month_name}{" "}
                    {convertYearData.addedTamilResult.tamil_date.day},{" "}
                    {convertYearData.addedTamilResult.tamil_date.solar_year}
                  </p>
                  <p className="text-xs font-mono-tamil text-[var(--color-muted)]">
                    {formatGregorian(convertYearData.addedTamilResult.gregorian_date)}
                  </p>
                </div>
              ) : null}
            </Card>
          </div>

          <Card className="p-5 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-[var(--color-mai)]">
                  {t.tools.calendar.yearMonthsHeading} ({revSolarYear})
                </h2>
                {yearLoading && (
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--color-semman)]" />
                )}
              </div>
              {yearInfo && (
                <Badge variant="terracotta">
                  {yearInfo.year_cycle.cycle_name} · {yearInfo.days}{" "}
                  {t.tools.numeral.daysSuffix}
                </Badge>
              )}
            </div>

            {yearError ? (
              <p className="text-xs text-red-600 dark:text-red-400">{yearError}</p>
            ) : yearInfo ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-[var(--border-line)] text-[var(--color-muted)]">
                      <th className="py-2 pr-3 font-medium">#</th>
                      <th className="py-2 pr-3 font-medium">{t.tools.calendar.monthCol}</th>
                      <th className="py-2 pr-3 font-medium">{t.tools.calendar.startDateCol}</th>
                      <th className="py-2 pr-3 font-medium">{t.tools.calendar.endDateCol}</th>
                      <th className="py-2 text-right font-medium">{t.tools.calendar.daysCol}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-line)]/60">
                    {yearInfo.months.map((m) => (
                      <tr key={m.month} className="hover:bg-[var(--bg-raised)]/40">
                        <td className="py-2 pr-3 font-mono-tamil text-[var(--color-muted)]">{m.month}</td>
                        <td className="py-2 pr-3 font-semibold text-[var(--color-mai)]">{m.month_name}</td>
                        <td className="py-2 pr-3 font-mono-tamil">{formatGregorian(m.start_date)}</td>
                        <td className="py-2 pr-3 font-mono-tamil text-[var(--color-muted)]">
                          {formatGregorian(m.end_date_exclusive)}
                        </td>
                        <td className="py-2 text-right font-mono-tamil font-semibold">{m.days}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </Card>
        </div>
      )}

      {/* TAB 3: FESTIVALS, OFFICIAL HOLIDAYS (TN & SL) & LUNAR PHASES */}
      {activeTab === "festivals" && (
        <div className="space-y-6">
          <Card className="p-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                <label className="text-xs font-semibold text-[var(--color-mai)]">Year:</label>
                <input
                  type="number"
                  min="2024"
                  max="2027"
                  value={festYear}
                  onChange={(e) => setFestYear(Number.parseInt(e.target.value, 10) || 2026)}
                  className="w-24 min-h-[36px] px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] font-mono-tamil text-xs"
                />
              </div>
              <select
                value={festMonthFilter}
                onChange={(e) => setFestMonthFilter(Number.parseInt(e.target.value, 10))}
                className="min-h-[36px] px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] text-xs"
              >
                <option value={0}>{t.tools.calendar.monthFilterAll}</option>
                {Array.from({ length: 12 }, (_, idx) => idx + 1).map((m) => (
                  <option key={m} value={m}>
                    {new Date(Date.UTC(2026, m - 1, 1)).toLocaleString("en", { month: "long" })} ({m})
                  </option>
                ))}
              </select>
            </div>

            <div className="inline-flex items-center gap-1 p-1 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)]">
              {(["TN", "SL"] as const).map((jur) => (
                <button
                  key={jur}
                  type="button"
                  onClick={() => setHolidayRegion(jur)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium cursor-pointer ${
                    holidayRegion === jur
                      ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
                      : "text-[var(--color-muted)]"
                  }`}
                >
                  {jur === "TN" ? t.tools.calendar.jurisdictionTN : t.tools.calendar.jurisdictionSL}
                </button>
              ))}
            </div>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-start">
            {/* Observances */}
            <Card className="p-5 space-y-3">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-[var(--color-mai)]">
                    {t.tools.calendar.observancesHeading}
                  </h2>
                  {drikCtx.region === "SL" && <Badge variant="outline">TN</Badge>}
                  {obsLoading && (
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--color-semman)]" />
                  )}
                </div>
                <Badge variant="outline">{observances.length}</Badge>
              </div>
              {obsError ? (
                <p className="text-xs text-red-600 dark:text-red-400">{obsError}</p>
              ) : obsLoading && observances.length === 0 ? (
                <div className="py-8 flex items-center justify-center gap-2 text-xs text-[var(--color-muted)]">
                  <Loader2 className="w-4 h-4 animate-spin text-[var(--color-semman)]" />
                  <span>{t.shell.engineLoading}</span>
                </div>
              ) : observances.length > 0 ? (
                <ul className="divide-y divide-[var(--border-line)]/60 max-h-[420px] overflow-y-auto text-xs">
                  {observances.map((ev, i) => (
                    <li key={`${ev.event_id}-${i}`} className="py-2.5 flex items-center justify-between gap-2">
                      <span className="font-medium text-[var(--color-mai)]">{ev.display_name}</span>
                      <span className="font-mono-tamil text-[var(--color-muted)] shrink-0">
                        {formatGregorian(ev.date)}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-[var(--color-muted)]">{t.tools.calendar.noEvents}</p>
              )}
            </Card>

            {/* Official Public Holidays */}
            <Card className="p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-[var(--color-mai)]">
                  {t.tools.calendar.holidaysHeading} ({holidayRegion})
                </h2>
                <Badge variant="sandhanam">{holidaysAndLunar?.officialHolidays.length ?? 0}</Badge>
              </div>
              {holidaysAndLunar?.holError ? (
                <p className="text-xs text-red-600 dark:text-red-400">{holidaysAndLunar.holError}</p>
              ) : holidaysAndLunar && holidaysAndLunar.officialHolidays.length > 0 ? (
                <ul className="divide-y divide-[var(--border-line)]/60 max-h-[420px] overflow-y-auto text-xs">
                  {holidaysAndLunar.officialHolidays
                    .filter((h) => festMonthFilter === 0 || h.date.month === festMonthFilter)
                    .map((h, i) => (
                      <li key={i} className="py-2.5 flex items-center justify-between gap-2">
                        <span className="font-medium text-[var(--color-mai)]">{h.name}</span>
                        <span className="font-mono-tamil text-[var(--color-muted)] shrink-0">
                          {formatGregorian(h.date)}
                        </span>
                      </li>
                    ))}
                </ul>
              ) : (
                <p className="text-xs text-[var(--color-muted)]">{t.tools.calendar.noEvents}</p>
              )}
            </Card>
          </div>

          {/* Lunar Phases */}
          <Card className="p-5 space-y-3">
            <h2 className="text-sm font-bold text-[var(--color-mai)]">
              {t.tools.calendar.lunarPhasesHeading}
            </h2>
            {holidaysAndLunar?.lunarError ? (
              <p className="text-xs text-red-600 dark:text-red-400">{holidaysAndLunar.lunarError}</p>
            ) : holidaysAndLunar && holidaysAndLunar.lunarEvents.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {holidaysAndLunar.lunarEvents.map((ev, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] text-xs space-y-1"
                  >
                    <span className="font-semibold capitalize text-[var(--color-semman)] block">
                      {ev.phase.replace(/_/g, " ")}
                    </span>
                    <span className="font-mono-tamil text-[var(--color-mai)]">
                      {formatGregorian(ev.utc_minute)} · {String(ev.utc_minute.hour).padStart(2, "0")}:
                      {String(ev.utc_minute.minute).padStart(2, "0")} UTC
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[var(--color-muted)]">{t.tools.calendar.noEvents}</p>
            )}
          </Card>
        </div>
      )}

      {/* TAB 4: THIRUKANITHAM VS VAKYA PROFILE COMPARISON */}
      {activeTab === "compare" && (
        <Card className="p-5 sm:p-6 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-bold text-[var(--color-mai)]">
              {t.tools.calendar.compareHeading} ({dateStr})
            </h2>
            {comparisonData.result && (
              <span className="text-xs text-[var(--color-muted)]">
                {t.tools.calendar.differingFieldsLabel}{" "}
                <strong>{comparisonData.result.differing_fields.length}</strong>
              </span>
            )}
          </div>

          {comparisonData.error && (
            <p className="text-xs text-red-600 dark:text-red-400">{comparisonData.error}</p>
          )}

          {comparisonData.result && (
            <div className="space-y-4">
              {comparisonData.result.differing_fields.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {comparisonData.result.differing_fields.map((field: string) => (
                    <Badge key={field} variant="terracotta" className="font-mono-tamil text-[11px]">
                      {field}
                    </Badge>
                  ))}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(comparisonData.result.profiles).map(([profKey, profVal]) => (
                  <div
                    key={profKey}
                    className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-2"
                  >
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--color-semman)]">
                      {profKey.includes("vakya")
                        ? t.tools.calendar.vakyaCol
                        : t.tools.calendar.thirukanithamCol}
                    </h3>
                    <pre className="text-[11px] font-mono-tamil text-[var(--color-mai)] overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(profVal, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

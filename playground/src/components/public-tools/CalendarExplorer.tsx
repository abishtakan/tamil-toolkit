import { useState, useEffect } from "react";
import { tt } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { CopyButton } from "../common/CopyButton";
import { Calendar as CalendarIcon, MapPin } from "lucide-react";

export function CalendarExplorer() {
  const { t } = useLanguage();

  const [dateStr, setDateStr] = useState<string>(() => {
    return new Date().toISOString().split("T")[0];
  });

  const [coords, setCoords] = useState<{ lat: number; lon: number; label: string }>({
    lat: 13.0827,
    lon: 80.2707,
    label: "Chennai"
  });

  // Calendar info
  const [solarDate, setSolarDate] = useState<string>("");
  const [thiruvalluvarYear, setThiruvalluvarYear] = useState<number>(0);
  const [cycleYearTitle, setCycleYearTitle] = useState<string>("");
  const [holidays, setHolidays] = useState<string[]>([]);
  const [daylightPeriods, setDaylightPeriods] = useState<{
    rahu: string;
    yamagandam: string;
    gulikai: string;
  }>({
    rahu: "1:30 PM - 3:00 PM",
    yamagandam: "6:00 AM - 7:30 AM",
    gulikai: "9:00 AM - 10:30 AM"
  });

  const formatTime = (time?: { hour: number; minute: number }) => {
    if (!time) return "—";
    const h = time.hour % 12 || 12;
    const ampm = time.hour >= 12 ? "PM" : "AM";
    const m = time.minute.toString().padStart(2, "0");
    return `${h}:${m} ${ampm}`;
  };

  const updateCalendar = (currentDateStr: string, lat: number, lon: number) => {
    try {
      const parts = currentDateStr.split("-").map(Number);
      if (parts.length !== 3) return;
      const [year, month, day] = parts;

      const calendarContext: tt.CalendarContext = {
        region: "TN",
        latitude_microdegrees: Math.round(lat * 1_000_000),
        longitude_microdegrees: Math.round(lon * 1_000_000),
        elevation_meters: 10,
        time_zone: "Asia/Kolkata"
      };

      const gDate: tt.GregorianDate = { year, month, day };

      // Solar date lookup
      const conv = tt.gregorian_to_tamil_date(gDate, calendarContext);
      let calculatedSolarYear = year;
      if (conv && conv.tamil_date) {
        const { month_name, day: tDay, solar_year } = conv.tamil_date;
        calculatedSolarYear = solar_year;
        setSolarDate(`${month_name} ${tDay}, ${solar_year}`);
        setThiruvalluvarYear(solar_year + 31);
      }

      // Year cycle title (60-year Jovian title)
      try {
        const cycle = tt.tamil_year_cycle_info(calculatedSolarYear, calendarContext);
        if (cycle && cycle.cycle_name) {
          setCycleYearTitle(cycle.cycle_name);
        }
      } catch {
        setCycleYearTitle("");
      }

      // Public holidays
      try {
        const holidayInfo = tt.calendar_official_holidays("TN", year);
        if (holidayInfo && holidayInfo.holidays) {
          const found = holidayInfo.holidays
            .filter((h) => h.date.year === year && h.date.month === month && h.date.day === day)
            .map((h) => h.name);
          setHolidays(found);
        } else {
          setHolidays([]);
        }
      } catch {
        setHolidays([]);
      }

      // Daylight periods
      try {
        const periods = tt.calendar_daylight_periods(gDate, calendarContext);
        if (periods && periods.intervals) {
          const rahu = periods.intervals.find((p) => p.period === "rahukalam");
          const yama = periods.intervals.find((p) => p.period === "yamagandam");
          const guli = periods.intervals.find((p) => p.period === "kuligai");
          setDaylightPeriods({
            rahu: rahu
              ? `${formatTime(rahu.start_local_time)} - ${formatTime(rahu.end_local_time)}`
              : "1:30 PM - 3:00 PM",
            yamagandam: yama
              ? `${formatTime(yama.start_local_time)} - ${formatTime(yama.end_local_time)}`
              : "6:00 AM - 7:30 AM",
            gulikai: guli
              ? `${formatTime(guli.start_local_time)} - ${formatTime(guli.end_local_time)}`
              : "9:00 AM - 10:30 AM"
          });
        }
      } catch {
        // use standard defaults
      }
    } catch (err) {
      console.error("Calendar update error:", err);
    }
  };

  useEffect(() => {
    updateCalendar(dateStr, coords.lat, coords.lon);
  }, [dateStr, coords]);

  const requestGeolocation = () => {
    if (typeof navigator !== "undefined" && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setCoords({
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
            label: t.tools.calendar.gpsLocationLabel
          });
        },
        () => {
          // fallback to Chennai
          setCoords({
            lat: 13.0827,
            lon: 80.2707,
            label: t.tools.calendar.chennaiFallbackLabel
          });
        }
      );
    }
  };

  const copySummary = `${solarDate} | ${t.tools.calendar.thiruvalluvarYearLabel}: ${thiruvalluvarYear} | ${t.tools.calendar.cycleYearLabel}: ${cycleYearTitle} | ${t.tools.calendar.rahuKalamLabel}: ${daylightPeriods.rahu}`;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[var(--border-line)]">
        <div>
          <h2 className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-mai)]">
            {t.tools.calendar.title}
          </h2>
          <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans mt-1">
            {t.tools.calendar.desc}
          </p>
        </div>

        <CopyButton
          text={copySummary}
          label={t.actions.copy}
          copiedLabel={t.actions.copied}
          size="sm"
          variant="outline"
        />
      </div>

      {/* Date & Location Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[var(--color-mai)] font-tamil">
            {t.tools.calendar.dateSelectLabel}
          </label>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={dateStr}
              onChange={(e) => setDateStr(e.target.value)}
              className="flex-1 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] px-4 py-2.5 text-base font-tamil text-[var(--color-mai)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)]"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[var(--color-mai)] font-tamil">
            {t.tools.calendar.coordsLabel}
          </label>
          <div className="flex items-center gap-2">
            <span className="text-xs font-tamil text-[var(--color-muted)] bg-[var(--bg-raised)] px-3 py-2.5 rounded-xl border border-[var(--border-line)] flex-1 truncate">
              <MapPin className="w-3.5 h-3.5 inline mr-1 text-[var(--color-semman)]" />
              {coords.label}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={requestGeolocation}
              className="text-xs font-tamil whitespace-nowrap min-h-[42px]"
            >
              {t.tools.calendar.locationPrompt}
            </Button>
          </div>
        </div>
      </div>

      {/* Primary Solar Date Banner */}
      <Card className="bg-[var(--bg-surface)] border-l-4 border-l-[var(--color-semman)] p-5">
        <div className="flex items-center justify-between pb-1">
          <span className="text-xs font-semibold text-[var(--color-semman)] font-tamil uppercase tracking-wide">
            {t.tools.calendar.tamilDateLabel}
          </span>
          <Badge variant="terracotta">
            <CalendarIcon className="w-3.5 h-3.5 mr-1" />
            {cycleYearTitle || t.tools.calendar.yearFallback}
          </Badge>
        </div>
        <p className="text-2xl sm:text-3xl font-tamil font-bold text-[var(--color-mai)] mt-1">
          {solarDate || "—"}
        </p>
        <p className="text-sm font-tamil text-[var(--color-muted)] mt-2">
          {t.tools.calendar.thiruvalluvarYearLabel}:{" "}
          <strong className="text-[var(--color-mai)]">{thiruvalluvarYear || "—"}</strong>
        </p>
      </Card>

      {/* Daylight Periods Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="bg-[var(--bg-surface)]">
          <span className="text-xs font-semibold text-[var(--color-muted)] font-tamil block mb-1">
            {t.tools.calendar.rahuKalamLabel}
          </span>
          <p className="text-base font-tamil font-semibold text-[var(--color-mai)]">
            {daylightPeriods.rahu}
          </p>
        </Card>

        <Card className="bg-[var(--bg-surface)]">
          <span className="text-xs font-semibold text-[var(--color-muted)] font-tamil block mb-1">
            {t.tools.calendar.yamagandamLabel}
          </span>
          <p className="text-base font-tamil font-semibold text-[var(--color-mai)]">
            {daylightPeriods.yamagandam}
          </p>
        </Card>

        <Card className="bg-[var(--bg-surface)]">
          <span className="text-xs font-semibold text-[var(--color-muted)] font-tamil block mb-1">
            {t.tools.calendar.gulikaiLabel}
          </span>
          <p className="text-base font-tamil font-semibold text-[var(--color-mai)]">
            {daylightPeriods.gulikai}
          </p>
        </Card>
      </div>

      {/* Holidays Notice */}
      {holidays.length > 0 && (
        <Card className="bg-[var(--bg-surface)] border-l-4 border-l-[var(--color-sandhanam)] border-[var(--border-line)] p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-2 h-2 rounded-full bg-[var(--color-sandhanam)]"></span>
            <span className="text-xs font-bold text-[var(--color-mai)] font-tamil uppercase">
              {t.tools.calendar.holidayLabel}
            </span>
          </div>
          <ul className="list-disc list-inside text-sm font-tamil text-[var(--color-mai)] font-medium space-y-1">
            {holidays.map((h, i) => (
              <li key={i}>{h}</li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}

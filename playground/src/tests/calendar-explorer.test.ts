import { describe, it, expect, beforeAll } from "vitest";
import { ensureToolkitInitialized } from "./setup";
import * as tt from "tamil-toolkit/web";

describe("T017: CalendarExplorer", () => {
  beforeAll(async () => {
    await ensureToolkitInitialized();
  });

  const chennaiContext: tt.CalendarContext = {
    region: "TN",
    latitude_microdegrees: 13082700,
    longitude_microdegrees: 80270700,
    elevation_meters: 10,
    time_zone: "Asia/Kolkata"
  };

  it("converts Gregorian date to Tamil solar date", () => {
    const conv = tt.gregorian_to_tamil_date({ year: 2026, month: 4, day: 14 }, chennaiContext);
    expect(conv).toBeDefined();
    expect(conv.tamil_date).toBeDefined();
    expect(conv.tamil_date.month_name).toBe("Chithirai");
  });

  it("computes 60-year Jovian cycle name", () => {
    const cycle = tt.tamil_year_cycle_info(2026, chennaiContext);
    expect(cycle).toBeDefined();
    expect(cycle.cycle_name).toBeTruthy();
  });

  it("calculates daylight periods (Rahu kalam, Yamagandam, Kuligai)", () => {
    const periods = tt.calendar_daylight_periods({ year: 2026, month: 11, day: 5 }, chennaiContext);
    expect(periods).toBeDefined();
    expect(periods.intervals.length).toBeGreaterThan(0);

    const rahu = periods.intervals.find((p) => p.period === "rahukalam");
    expect(rahu).toBeDefined();
    expect(rahu?.start_local_time).toBeDefined();
  });
});

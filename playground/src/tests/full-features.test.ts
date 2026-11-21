import { describe, it, expect, beforeAll } from "vitest";
import { ensureToolkitInitialized } from "./setup";
import * as tt from "tamil-toolkit/web";
import {
  bytesToHex,
  compareCalendarProfiles,
  formatTamilDate,
  getThiruvalluvarYearInfo,
  hexToBytes,
  latin1BytesToString,
  stringToLatin1Bytes,
} from "../lib/engine";

describe("Full Playground Feature Parity", () => {
  beforeAll(async () => {
    await ensureToolkitInitialized();
  });

  const chennaiContext: tt.CalendarContext = {
    region: "TN",
    latitude_microdegrees: 13087840,
    longitude_microdegrees: 80278470,
    elevation_meters: 14,
    time_zone: "Asia/Kolkata",
  };

  const jaffnaContext: tt.CalendarContext = {
    region: "SL",
    latitude_microdegrees: 9661500,
    longitude_microdegrees: 80025500,
    elevation_meters: 5,
    time_zone: "Asia/Colombo",
  };

  it("supports Sri Lankan Rupee (LKR / SL) alongside INR / TN", () => {
    const lkrWords = tt.currency_to_words(12500000, "LKR", "SL");
    expect(lkrWords).toContain("ரூபா");
    expect(lkrWords).toContain("சதம்");

    const lkrFormatted = tt.format_currency(12500000, "LKR", "SL");
    expect(lkrFormatted).toBe("LKR 1,25,000.00");

    const lkrDecimalWords = tt.currency_decimal_to_words(
      "1250.50",
      "latin",
      "LKR",
      "SL",
      "indian"
    );
    expect(lkrDecimalWords).toContain("ரூபா");
    expect(lkrDecimalWords).toContain("சதம்");

    const inrWords = tt.currency_to_words(12500000, "INR", "TN");
    expect(inrWords).toContain("ரூபாய்");
  });

  it("exposes ordinals, digit sequences, traditional integers, fractions, percents, and date math", () => {
    expect(tt.ordinal_to_words(1, "TN")).toBeTruthy();
    expect(tt.ordinal_to_words(5, "SL")).toBeTruthy();
    expect(tt.digit_sequence_to_words("2026", "latin", "TN")).toBeTruthy();
    expect(tt.convert_digits("2026", "tamil")).toBe("௨௦௨௬");

    const trad = tt.format_traditional_integer(1250);
    expect(tt.parse_traditional_integer(trad)).toBe(1250);

    const fracGlyph = tt.fraction_symbol(3, 4);
    expect(fracGlyph).toBeTruthy();
    expect(tt.parse_fraction_symbol(fracGlyph)).toEqual({
      numerator: 3,
      denominator: 4,
    });
    expect(tt.fraction_to_words(3, 4, "SL")).toBeTruthy();

    const mixed = tt.format_mixed_fraction(
      { negative: false, whole: 2, numerator: 1, denominator: 4 },
      "tamil"
    );
    expect(mixed).toBeTruthy();

    const pctDec = tt.parse_percent("12.5%", "latin", "none");
    expect(tt.format_percent(pctDec, "tamil", "none")).toBeTruthy();

    const ratioDec = tt.parse_decimal("0.25", "latin", "none");
    const pctFromRatio = tt.ratio_to_percent(ratioDec);
    expect(tt.format_percent(pctFromRatio, "latin", "none")).toContain("25");

    const range = tt.format_numeric_range(
      { type: "decimal", value: { negative: false, coefficient: "1", scale: 0 } },
      { type: "decimal", value: { negative: false, coefficient: "10", scale: 0 } },
      true,
      true,
      "–",
      "tamil"
    );
    expect(range).toBeTruthy();

    expect(tt.format_date(2026, 4, 14, "SL", "long", "tamil")).toBeTruthy();
    expect(
      tt.date_difference(
        { year: 2026, month: 4, day: 14 },
        { year: 2026, month: 4, day: 24 }
      )
    ).toBe(10);
    expect(tt.add_gregorian_date(2026, 4, 14, "days", 10, "clamp")).toEqual({
      year: 2026,
      month: 4,
      day: 24,
    });
  });

  it("exposes full calendar features including engine wrappers, reverse conversion, SL holidays, and panchangam_at", () => {
    const formatted = formatTamilDate(
      { year: 2026, month: 4, day: 14 },
      jaffnaContext,
      "tamil",
      "tamil"
    );
    expect(formatted).toBeTruthy();

    const yearInfo = getThiruvalluvarYearInfo(
      { year: 2026, month: 4, day: 14 },
      chennaiContext
    );
    expect(yearInfo.thiruvalluvar_year).toBeGreaterThan(2000);

    const rev = tt.tamil_to_gregorian_date(
      { solar_year: 2026, month: 1, day: 1 },
      chennaiContext
    );
    expect(rev.gregorian_date.year).toBe(2026);

    const solarYear = tt.tamil_year_info(2026, chennaiContext);
    expect(solarYear.months.length).toBe(12);

    const added = tt.add_tamil_date(
      { solar_year: 2026, month: 1, day: 1 },
      "days",
      10,
      chennaiContext
    );
    expect(added.tamil_date.day).toBe(11);

    const instant = tt.panchangam_at(
      Math.floor(Date.UTC(2026, 3, 14, 6, 30, 0) / 1000),
      jaffnaContext
    );
    expect(instant.limbs.nakshatra.name).toBeTruthy();
    expect(instant.limbs.tithi.name).toBeTruthy();

    const dispPanchangam = tt.execute({
      op: "panchangam_day",
      input: {
        definition_id: "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2",
        date: { year: 2026, month: 4, day: 14 },
        context: jaffnaContext,
      },
    }) as tt.PanchangamDay;
    expect(dispPanchangam.vara).toBeTruthy();

    const dispObservances = tt.execute({
      op: "calendar_observances",
      input: {
        definition_id: "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2",
        rule_set: "thirukanitham-tamil-named-observances-v1",
        gregorian_year: 2026,
        month: 4,
        context: chennaiContext,
      },
    }) as tt.CalendarObservances;
    expect(dispObservances.events.length).toBeGreaterThan(0);

    const obs = tt.calendar_observances(
      2026,
      chennaiContext,
      "thirukanitham-tamil-named-observances-v1",
      "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2",
      4
    );
    expect(obs.events.length).toBeGreaterThan(0);

    const slHolidays = tt.calendar_official_holidays("SL", 2026);
    const tnHolidays = tt.calendar_official_holidays("TN", 2026);
    expect(slHolidays.holidays.length).toBeGreaterThan(0);
    expect(tnHolidays.holidays.length).toBeGreaterThan(0);

    const lunars = tt.lunar_phase_events(
      Math.floor(Date.UTC(2026, 3, 1, 0, 0, 0) / 1000),
      Math.floor(Date.UTC(2026, 3, 30, 23, 59, 59) / 1000)
    );
    expect(lunars.events.length).toBeGreaterThan(0);

    const compared = compareCalendarProfiles({
      date: { year: 2026, month: 4, day: 14 },
      thirukanitham_context: chennaiContext,
      vakya_context: {
        reference_station: "ujjain",
        time_zone: "Asia/Kolkata",
      },
    });
    expect(compared).toBeDefined();
  }, 30000);

  it("round-trips 8-bit legacy TSCII bytes via Latin-1 and hex helpers without UTF-8 corruption", () => {
    const original = "தமிழ்";
    const tsciiBytes = tt.unicode_to_tscii_bytes(original);
    const hex = bytesToHex(tsciiBytes);
    const parsedHex = hexToBytes(hex);
    expect(parsedHex).not.toBeNull();
    expect(tt.tscii_bytes_to_unicode(parsedHex!)).toBe(original);

    const latin1 = latin1BytesToString(tsciiBytes);
    const roundTrippedBytes = stringToLatin1Bytes(latin1);
    expect(tt.tscii_bytes_to_unicode(roundTrippedBytes)).toBe(original);

    expect(tt.bamini_to_unicode("jkpo;", "strict")).toBe("தமிழ்");
  });

  it("supports syllable composition, olippasai, cognates, collation comparison/keys, symbol lookup, and string inspection", () => {
    expect(tt.compose_uyirmei("க்", "ஆ")).toBe("கா");

    const olippasai = tt.get_olippasai("தங்கம்");
    expect(olippasai.length).toBeGreaterThan(0);
    expect(olippasai[0].has_coda).toBe(true);

    expect(tt.are_cognates("க்", "ங்")).toBe(true);
    expect(tt.are_cognates("க்", "த்")).toBe(false);

    expect(tt.compare("அகத்தியர்", "கம்பர்", "agara-v1")).toBe(-1);
    expect(tt.sort_key("தமிழ்", "agara-v1").length).toBeGreaterThan(0);
    expect(
      tt.folded_search_key("பழம்", "comprehensive", "agara-v1").length
    ).toBeGreaterThan(0);

    const info = tt.symbol_info("௳");
    expect(info.codepoint).toBe(0x0bf3);

    const inspection = tt.inspect_tamil_string("தமிழ்");
    expect(inspection.is_nfc).toBe(true);
    expect(inspection.ezhuthu_count).toBe(3);
  });
});

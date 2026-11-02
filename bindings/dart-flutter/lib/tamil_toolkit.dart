import 'dart:convert';
import 'dart:ffi';
import 'package:ffi/ffi.dart';

typedef ExactDecimal = Map<String, Object?>;
typedef NumericRangeEndpoint = Map<String, Object?>;
typedef GregorianDate = Map<String, int>;

abstract interface class CalendarContextInput {
  Map<String, Object?> toJson();
}

class CalendarContext implements CalendarContextInput {
  final String region;
  final int latitudeMicrodegrees;
  final int longitudeMicrodegrees;
  final int elevationMeters;
  final String timeZone;

  const CalendarContext({
    required this.region,
    required this.latitudeMicrodegrees,
    required this.longitudeMicrodegrees,
    required this.elevationMeters,
    required this.timeZone,
  });

  @override
  Map<String, Object?> toJson() => {
        'region': region,
        'latitude_microdegrees': latitudeMicrodegrees,
        'longitude_microdegrees': longitudeMicrodegrees,
        'elevation_meters': elevationMeters,
        'time_zone': timeZone,
      };
}

class VakyaCivilContext implements CalendarContextInput {
  final String referenceStation;
  final String timeZone;

  const VakyaCivilContext({
    this.referenceStation = 'ujjain',
    required this.timeZone,
  });

  @override
  Map<String, Object?> toJson() => {
        'reference_station': referenceStation,
        'time_zone': timeZone,
      };
}

class TamilSolarDate {
  final int solarYear;
  final int month;
  final int day;
  const TamilSolarDate(
      {required this.solarYear, required this.month, required this.day});
  Map<String, int> toJson() =>
      {'solar_year': solarYear, 'month': month, 'day': day};
  factory TamilSolarDate.fromJson(Map<String, dynamic> value) => TamilSolarDate(
        solarYear: value['solar_year'] as int,
        month: value['month'] as int,
        day: value['day'] as int,
      );
}

class LunarPhaseEvent {
  final String phase;
  final int eclipticLongitudeDifferenceDegrees;
  final GregorianDate utcMinute;
  const LunarPhaseEvent({
    required this.phase,
    required this.eclipticLongitudeDifferenceDegrees,
    required this.utcMinute,
  });
  factory LunarPhaseEvent.fromJson(Map<String, dynamic> value) =>
      LunarPhaseEvent(
        phase: value['phase'] as String,
        eclipticLongitudeDifferenceDegrees:
            value['ecliptic_longitude_difference_degrees'] as int,
        utcMinute: Map<String, int>.from(value['utc_minute'] as Map),
      );
}

class LunarPhaseEvents {
  final String definitionId;
  final List<LunarPhaseEvent> events;
  const LunarPhaseEvents({required this.definitionId, required this.events});
}

class CalendarLimb {
  final int index;
  final String name;
  final String? paksha;
  const CalendarLimb({required this.index, required this.name, this.paksha});
  factory CalendarLimb.fromJson(Map<String, dynamic> value) => CalendarLimb(
        index: value['index'] as int,
        name: value['name'] as String,
        paksha: value['paksha'] as String?,
      );
}

class CalendarLimbs {
  final CalendarLimb tithi;
  final CalendarLimb nakshatra;
  final CalendarLimb yoga;
  final CalendarLimb karana;
  const CalendarLimbs(
      {required this.tithi,
      required this.nakshatra,
      required this.yoga,
      required this.karana});
  factory CalendarLimbs.fromJson(Map<String, dynamic> value) => CalendarLimbs(
        tithi: CalendarLimb.fromJson(
            Map<String, dynamic>.from(value['tithi'] as Map)),
        nakshatra: CalendarLimb.fromJson(
            Map<String, dynamic>.from(value['nakshatra'] as Map)),
        yoga: CalendarLimb.fromJson(
            Map<String, dynamic>.from(value['yoga'] as Map)),
        karana: CalendarLimb.fromJson(
            Map<String, dynamic>.from(value['karana'] as Map)),
      );
}

class PanchangamTransition {
  final String limb;
  final int fromIndex;
  final int toIndex;
  final int dayOffset;
  final int minuteOfDay;
  const PanchangamTransition(
      {required this.limb,
      required this.fromIndex,
      required this.toIndex,
      required this.dayOffset,
      required this.minuteOfDay});
  factory PanchangamTransition.fromJson(Map<String, dynamic> value) =>
      PanchangamTransition(
        limb: value['limb'] as String,
        fromIndex: value['from_index'] as int,
        toIndex: value['to_index'] as int,
        dayOffset: value['day_offset'] as int,
        minuteOfDay: value['minute_of_day'] as int,
      );
}

class PanchangamAt {
  final String definitionId;
  final GregorianDate localDate;
  final Map<String, int> localTime;
  final String vara;
  final CalendarLimbs limbs;
  final String? referenceStation;
  final String? positionBasis;
  const PanchangamAt(
      {required this.definitionId,
      required this.localDate,
      required this.localTime,
      required this.vara,
      required this.limbs,
      this.referenceStation,
      this.positionBasis});
}

class PanchangamDay {
  final String definitionId;
  final GregorianDate date;
  final int sunriseMinuteOfDay;
  final int? sunsetMinuteOfDay;
  final String? sunriseBasis;
  final String? sunsetStatus;
  final String vara;
  final CalendarLimbs limbsAtSunrise;
  final List<PanchangamTransition> transitions;
  const PanchangamDay(
      {required this.definitionId,
      required this.date,
      required this.sunriseMinuteOfDay,
      required this.sunsetMinuteOfDay,
      this.sunriseBasis,
      this.sunsetStatus,
      required this.vara,
      required this.limbsAtSunrise,
      required this.transitions});
}

typedef _NativeCall = Pointer<Utf8> Function(Pointer<Utf8>);
typedef _NativeFree = Void Function(Pointer<Utf8>);

/// Thin JSON marshalling around the Rust C ABI. Supply the built library path.
class TamilToolkit {
  final Pointer<Utf8> Function(Pointer<Utf8>) _call;
  final void Function(Pointer<Utf8>) _free;

  TamilToolkit(String libraryPath) : this._(DynamicLibrary.open(libraryPath));

  TamilToolkit._(DynamicLibrary library)
      : _call = library.lookupFunction<_NativeCall,
            Pointer<Utf8> Function(Pointer<Utf8>)>('tamil_toolkit_call'),
        _free =
            library.lookupFunction<_NativeFree, void Function(Pointer<Utf8>)>(
                'tamil_toolkit_free');

  Object? execute(Map<String, Object?> request) {
    final input = jsonEncode(request).toNativeUtf8();
    try {
      final output = _call(input);
      if (output == nullptr) throw StateError('Rust returned a null response');
      try {
        final result =
            jsonDecode(output.toDartString()) as Map<String, dynamic>;
        if (result.containsKey('error')) throw ArgumentError(result['error']);
        return result['ok'];
      } finally {
        _free(output);
      }
    } finally {
      malloc.free(input);
    }
  }

  List<String> getLetters(String text) =>
      (execute({'op': 'get_letters', 'input': text}) as List).cast<String>();
  String normalizeNfc(String text) =>
      execute({'op': 'normalize_nfc', 'input': text}) as String;
  String normalizeNfd(String text) =>
      execute({'op': 'normalize_nfd', 'input': text}) as String;
  Map<String, dynamic> splitUyirmei(String text) =>
      execute({'op': 'split_uyirmei', 'input': text}) as Map<String, dynamic>;
  String composeUyirmei(String mei, String uyir) => execute({
        'op': 'compose_uyirmei',
        'input': {'mei': mei, 'uyir': uyir},
      }) as String;
  int compare(String left, String right) => execute({
        'op': 'compare',
        'input': {'left': left, 'right': right}
      }) as int;
  List<String> sortWords(List<String> words) =>
      (execute({'op': 'sort_words', 'input': words}) as List).cast<String>();
  List<int> sortKey(String text) =>
      (execute({'op': 'sort_key', 'input': text}) as List).cast<int>();
  List<int> searchKey(String text) =>
      (execute({'op': 'search_key', 'input': text}) as List).cast<int>();
  String toWords(int value, {String locale = 'TN'}) => execute({
        'op': 'to_words',
        'input': {'value': value, 'locale': locale},
      }) as String;
  String formatCurrency(int amountMinor, String currency,
          {String locale = 'TN'}) =>
      execute({
        'op': 'format_currency',
        'input': {
          'amount_minor': amountMinor,
          'currency': currency,
          'locale': locale
        },
      }) as String;
  String currencyToWords(int amountMinor, String currency,
          {String locale = 'TN'}) =>
      execute({
        'op': 'currency_to_words',
        'input': {
          'amount_minor': amountMinor,
          'currency': currency,
          'locale': locale
        },
      }) as String;
  String baminiToUnicode(String text, {String errors = 'strict'}) => execute({
        'op': 'bamini_to_unicode',
        'input': {'text': text, 'errors': errors},
      }) as String;
  String unicodeToBamini(String text) => execute({
        'op': 'unicode_to_bamini',
        'input': {'text': text},
      }) as String;
  String anjalBytesToUnicode(List<int> bytes) => execute({
        'op': 'anjal_bytes_to_unicode',
        'input': {'bytes': bytes},
      }) as String;
  List<int> unicodeToAnjalBytes(String text) => (execute({
        'op': 'unicode_to_anjal_bytes',
        'input': {'text': text}
      }) as List)
          .cast<int>();
  String tamBytesToUnicode(List<int> bytes) => execute({
        'op': 'tam_bytes_to_unicode',
        'input': {'bytes': bytes},
      }) as String;
  List<int> unicodeToTamBytes(String text) => (execute({
        'op': 'unicode_to_tam_bytes',
        'input': {'text': text}
      }) as List)
          .cast<int>();
  String tabBytesToUnicode(List<int> bytes) => execute({
        'op': 'tab_bytes_to_unicode',
        'input': {'bytes': bytes},
      }) as String;
  List<int> unicodeToTabBytes(String text) => (execute({
        'op': 'unicode_to_tab_bytes',
        'input': {'text': text}
      }) as List)
          .cast<int>();
  String tsciiBytesToUnicode(List<int> bytes) => execute({
        'op': 'tscii_bytes_to_unicode',
        'input': {'bytes': bytes},
      }) as String;
  List<int> unicodeToTsciiBytes(String text) => (execute({
        'op': 'unicode_to_tscii_bytes',
        'input': {'text': text}
      }) as List)
          .cast<int>();
  String ltTmCodesToUnicode(List<int> codes, {String errors = 'strict'}) =>
      execute({
        'op': 'lt_tm_codes_to_unicode',
        'input': {'codes': codes, 'errors': errors},
      }) as String;
  String ltTmTextToUnicode(String text, {String errors = 'strict'}) => execute({
        'op': 'lt_tm_text_to_unicode',
        'input': {'text': text, 'errors': errors},
      }) as String;
  List<int> unicodeToLtTmCodes(String text) => (execute({
        'op': 'unicode_to_lt_tm_codes',
        'input': {'text': text}
      }) as List)
          .cast<int>();
  String unicodeToLtTmText(String text) => execute({
        'op': 'unicode_to_lt_tm_text',
        'input': {'text': text},
      }) as String;
  String vanavilCodesToUnicode(List<int> codes, {String errors = 'strict'}) =>
      execute({
        'op': 'vanavil_codes_to_unicode',
        'input': {'codes': codes, 'errors': errors},
      }) as String;
  String vanavilTextToUnicode(String text, {String errors = 'strict'}) =>
      execute({
        'op': 'vanavil_text_to_unicode',
        'input': {'text': text, 'errors': errors},
      }) as String;
  List<int> unicodeToVanavilCodes(String text) => (execute({
        'op': 'unicode_to_vanavil_codes',
        'input': {'text': text}
      }) as List)
          .cast<int>();
  String unicodeToVanavilText(String text) => execute({
        'op': 'unicode_to_vanavil_text',
        'input': {'text': text},
      }) as String;
  String formatFraction(int numerator, int denominator,
          {String digits = 'latin'}) =>
      execute({
        'op': 'format_fraction',
        'input': {
          'numerator': numerator,
          'denominator': denominator,
          'digits': digits
        },
      }) as String;
  String fractionToWords(int numerator, int denominator,
          {String locale = 'TN'}) =>
      execute({
        'op': 'fraction_to_words',
        'input': {
          'numerator': numerator,
          'denominator': denominator,
          'locale': locale
        },
      }) as String;
  String fractionSymbol(int numerator, int denominator) => execute({
        'op': 'fraction_symbol',
        'input': {'numerator': numerator, 'denominator': denominator},
      }) as String;
  String formatDate(int year, int month, int day,
          {String locale = 'TN',
          String style = 'long',
          String digits = 'latin'}) =>
      execute({
        'op': 'format_date',
        'input': {
          'year': year,
          'month': month,
          'day': day,
          'locale': locale,
          'style': style,
          'digits': digits
        },
      }) as String;

  String convertDigits(String text, String to) => execute({
        'op': 'convert_digits',
        'input': {'text': text, 'to': to}
      }) as String;
  ExactDecimal parseDecimal(String text, String sourceDigits,
          {String grouping = 'none', bool allowMixedDigits = false}) =>
      execute({
        'op': 'parse_decimal',
        'input': {
          'text': text,
          'source_digits': sourceDigits,
          'grouping': grouping,
          'allow_mixed_digits': allowMixedDigits
        },
      }) as ExactDecimal;
  String formatDecimal(ExactDecimal value,
          {String digits = 'latin', String grouping = 'none'}) =>
      execute({
        'op': 'format_decimal',
        'input': {'value': value, 'digits': digits, 'grouping': grouping},
      }) as String;
  String decimalToWords(String text, String sourceDigits,
          {String locale = 'TN',
          String grouping = 'none',
          bool allowMixedDigits = false}) =>
      execute({
        'op': 'decimal_to_words',
        'input': {
          'text': text,
          'source_digits': sourceDigits,
          'locale': locale,
          'grouping': grouping,
          'allow_mixed_digits': allowMixedDigits
        },
      }) as String;
  String ordinalToWords(int value, {String locale = 'TN'}) => execute({
        'op': 'ordinal_to_words',
        'input': {'value': value, 'locale': locale}
      }) as String;
  String digitSequenceToWords(String text, String sourceDigits,
          {String locale = 'TN'}) =>
      execute({
        'op': 'digit_sequence_to_words',
        'input': {
          'text': text,
          'source_digits': sourceDigits,
          'locale': locale
        },
      }) as String;
  String formatCurrencyDecimal(
          String amount, String sourceDigits, String currency,
          {String locale = 'TN', String grouping = 'none'}) =>
      execute({
        'op': 'format_currency_decimal',
        'input': {
          'amount': amount,
          'source_digits': sourceDigits,
          'currency': currency,
          'locale': locale,
          'grouping': grouping
        },
      }) as String;
  String currencyDecimalToWords(
          String amount, String sourceDigits, String currency,
          {String locale = 'TN', String grouping = 'none'}) =>
      execute({
        'op': 'currency_decimal_to_words',
        'input': {
          'amount': amount,
          'source_digits': sourceDigits,
          'currency': currency,
          'locale': locale,
          'grouping': grouping
        },
      }) as String;
  Map<String, int> parseFractionSymbol(String text) => Map<String, int>.from(
        execute({
          'op': 'parse_fraction_symbol',
          'input': {'text': text}
        }) as Map,
      );
  Map<String, dynamic> symbolInfo(String text) => execute({
        'op': 'symbol_info',
        'input': {'text': text}
      }) as Map<String, dynamic>;
  String formatMixedFraction(
          {required bool negative,
          required int whole,
          required int numerator,
          required int denominator,
          String digits = 'latin'}) =>
      execute({
        'op': 'format_mixed_fraction',
        'input': {
          'negative': negative,
          'whole': whole,
          'numerator': numerator,
          'denominator': denominator,
          'digits': digits
        },
      }) as String;
  Map<String, dynamic> parseMixedFraction(String text, String sourceDigits) =>
      execute({
        'op': 'parse_mixed_fraction',
        'input': {'text': text, 'source_digits': sourceDigits},
      }) as Map<String, dynamic>;
  String formatTraditionalInteger(int value) => execute({
        'op': 'format_traditional_integer',
        'input': {'value': value}
      }) as String;
  int parseTraditionalInteger(String text) => execute({
        'op': 'parse_traditional_integer',
        'input': {'text': text}
      }) as int;
  ExactDecimal parsePercent(String text, String sourceDigits,
          {String grouping = 'none'}) =>
      execute({
        'op': 'parse_percent',
        'input': {
          'text': text,
          'source_digits': sourceDigits,
          'grouping': grouping
        },
      }) as ExactDecimal;
  String formatPercent(ExactDecimal value,
          {String digits = 'latin', String grouping = 'none'}) =>
      execute({
        'op': 'format_percent',
        'input': {'value': value, 'digits': digits, 'grouping': grouping},
      }) as String;
  ExactDecimal ratioToPercent(ExactDecimal value) => execute({
        'op': 'ratio_to_percent',
        'input': {'value': value}
      }) as ExactDecimal;
  ExactDecimal percentToRatio(ExactDecimal value) => execute({
        'op': 'percent_to_ratio',
        'input': {'value': value}
      }) as ExactDecimal;
  String formatNumericRange(
          NumericRangeEndpoint start, NumericRangeEndpoint end,
          {required bool startInclusive,
          required bool endInclusive,
          String separator = '–',
          String digits = 'latin'}) =>
      execute({
        'op': 'format_numeric_range',
        'input': {
          'start': start,
          'end': end,
          'start_inclusive': startInclusive,
          'end_inclusive': endInclusive,
          'separator': separator,
          'digits': digits
        },
      }) as String;
  bool validateGregorianDate(int year, int month, int day) => execute({
        'op': 'validate_gregorian_date',
        'input': {'year': year, 'month': month, 'day': day}
      }) as bool;
  GregorianDate parseGregorianDate(String text) => Map<String, int>.from(
        execute({
          'op': 'parse_gregorian_date',
          'input': {'text': text}
        }) as Map,
      );
  String weekday(int year, int month, int day) => execute({
        'op': 'weekday',
        'input': {'year': year, 'month': month, 'day': day}
      }) as String;
  GregorianDate addGregorianDate(
      int year, int month, int day, String unit, int amount,
      {String overflow = 'reject'}) {
    final value = execute({
      'op': 'add_gregorian_date',
      'input': {
        'year': year,
        'month': month,
        'day': day,
        'unit': unit,
        'amount': amount,
        'overflow': overflow
      },
    });
    return Map<String, int>.from(value as Map);
  }

  int dateDifference(GregorianDate start, GregorianDate end) => execute({
        'op': 'date_difference',
        'input': {'start': start, 'end': end}
      }) as int;
  Map<String, dynamic> dateInterval(String start, String end) => execute({
        'op': 'date_interval',
        'input': {'start': start, 'end': end}
      }) as Map<String, dynamic>;
  Map<String, dynamic> vakyaSolarTransits(int sakaYearElapsed) => execute({
        'op': 'vakya_solar_transits',
        'input': {
          'definition_id': 'vakyakarana-1962-laghuprakashika-solar-transits-v1',
          'saka_year_elapsed': sakaYearElapsed,
        },
      }) as Map<String, dynamic>;
  Map<String, dynamic> vakyaTrueSunFromMeshaElapsed(
          int elapsedDays, int nadi, int vinadi) =>
      execute({
        'op': 'vakya_true_sun_from_mesha_elapsed',
        'input': {
          'definition_id': 'vakyakarana-1962-laghuprakashika-solar-transits-v1',
          'elapsed_days': elapsedDays,
          'nadi': nadi,
          'vinadi': vinadi,
        },
      }) as Map<String, dynamic>;
  Map<String, dynamic> vakyaTrueMoonFromKaliDay(int kaliDay) => execute({
        'op': 'vakya_true_moon_from_kali_day',
        'input': {
          'definition_id': 'vakyakarana-1962-laghuprakashika-true-moon-v1',
          'kali_day': kaliDay,
        },
      }) as Map<String, dynamic>;
  Map<String, dynamic> vakyaReduceToLocalTrueSunrise({
    required Map<String, int> truePosition,
    required Map<String, int> dailyMotion,
    required int caraHalfVinadiTenths,
    required int desantaraVinadiTenths,
    required int bhujaantaraVinadiTenths,
  }) =>
      execute({
        'op': 'vakya_reduce_to_local_true_sunrise',
        'input': {
          'definition_id': 'vakyakarana-1962-laghuprakashika-local-sunrise-v1',
          'true_position': truePosition,
          'daily_motion': dailyMotion,
          'cara_half_vinadi_tenths': caraHalfVinadiTenths,
          'desantara_vinadi_tenths': desantaraVinadiTenths,
          'bhujaantara_vinadi_tenths': bhujaantaraVinadiTenths,
        },
      }) as Map<String, dynamic>;

  Map<String, dynamic> vakyaCaraFromSayanaSun({
    required Map<String, int> sayanaSun,
    required int equinoctialShadowTenths,
  }) =>
      execute({
        'op': 'vakya_cara_from_sayana_sun',
        'input': {
          'definition_id': 'vakyakarana-1962-laghuprakashika-cara-v1',
          'sayana_sun': sayanaSun,
          'equinoctial_shadow_tenths': equinoctialShadowTenths,
        },
      }) as Map<String, dynamic>;

  Map<String, dynamic> vakyaDesantaraFromYojanaDistance(
    int eastWestDistanceTenthsYojana,
  ) =>
      execute({
        'op': 'vakya_desantara_from_yojana_distance',
        'input': {
          'definition_id': 'vakyakarana-1962-laghuprakashika-desantara-v1',
          'east_west_distance_tenths_yojana': eastWestDistanceTenthsYojana,
        },
      }) as Map<String, dynamic>;

  Map<String, dynamic> vakyaBhujaantaraFromTrueSun({
    required int sunRasi,
    required int sunRasiProgressArcseconds,
  }) =>
      execute({
        'op': 'vakya_bhujaantara_from_true_sun',
        'input': {
          'definition_id':
              'vakyakarana-1962-laghuprakashika-bhujaantara-linear-experimental-v1',
          'sun_rasi': sunRasi,
          'sun_rasi_progress_arcseconds': sunRasiProgressArcseconds,
        },
      }) as Map<String, dynamic>;

  Map<String, dynamic> calendarProfileInfo({
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      execute({
        'op': 'calendar_profile_info',
        'input': {'definition_id': definitionId},
      }) as Map<String, dynamic>;

  Map<String, dynamic> gregorianToTamilDate(
    GregorianDate date,
    CalendarContextInput context, {
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      execute({
        'op': 'gregorian_to_tamil_date',
        'input': {
          'definition_id': definitionId,
          'date': date,
          'context': context.toJson(),
        },
      }) as Map<String, dynamic>;

  Map<String, dynamic> tamilToGregorianDate(
    TamilSolarDate date,
    CalendarContextInput context, {
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      execute({
        'op': 'tamil_to_gregorian_date',
        'input': {
          'definition_id': definitionId,
          'date': date.toJson(),
          'context': context.toJson(),
        },
      }) as Map<String, dynamic>;

  Map<String, dynamic> tamilMonthInfo(
    int solarYear,
    int month,
    CalendarContextInput context, {
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      execute({
        'op': 'tamil_month_info',
        'input': {
          'definition_id': definitionId,
          'solar_year': solarYear,
          'month': month,
          'context': context.toJson(),
        },
      }) as Map<String, dynamic>;

  Map<String, dynamic> tamilYearInfo(
    int solarYear,
    CalendarContextInput context, {
    String definitionId =
        'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      execute({
        'op': 'tamil_year_info',
        'input': {
          'definition_id': definitionId,
          'solar_year': solarYear,
          'context': context.toJson(),
        },
      }) as Map<String, dynamic>;

  Map<String, dynamic> tamilYearCycleInfo(
    int solarYear,
    CalendarContextInput context, {
    String definitionId =
        'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      execute({
        'op': 'tamil_year_cycle_info',
        'input': {
          'definition_id': definitionId,
          'solar_year': solarYear,
          'context': context.toJson(),
        },
      }) as Map<String, dynamic>;

  Map<String, dynamic> calendarOfficialHolidays(String jurisdiction, int year) =>
      execute({
        'op': 'calendar_official_holidays',
        'input': {'jurisdiction': jurisdiction, 'year': year},
      }) as Map<String, dynamic>;

  Map<String, dynamic> calendarObservances(
    int gregorianYear,
    CalendarContextInput context, {
    String ruleSet = 'thirukanitham-tamil-named-observances-v1',
    String definitionId =
        'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
    int? month,
  }) =>
      execute({
        'op': 'calendar_observances',
        'input': {
          'definition_id': definitionId,
          'rule_set': ruleSet,
          'gregorian_year': gregorianYear,
          if (month != null) 'month': month,
          'context': context.toJson(),
        },
      }) as Map<String, dynamic>;

  Map<String, dynamic> addTamilDate(
    TamilSolarDate date,
    String unit,
    int amount,
    CalendarContextInput context, {
    String overflow = 'reject',
    String definitionId =
        'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      execute({
        'op': 'add_tamil_date',
        'input': {
          'definition_id': definitionId,
          'date': date.toJson(),
          'unit': unit,
          'amount': amount,
          'overflow': overflow,
          'context': context.toJson(),
        },
      }) as Map<String, dynamic>;

  Map<String, dynamic> calendarDaylightPeriods(
    Map<String, int> date,
    CalendarContextInput context, {
    String definitionId =
        'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      execute({
        'op': 'calendar_daylight_periods',
        'input': {
          'definition_id': definitionId,
          'date': date,
          'context': context.toJson(),
        },
      }) as Map<String, dynamic>;

  String formatTamilDate(
    GregorianDate date,
    CalendarContextInput context, {
    String script = 'tamil',
    String digits = 'latin',
    String style = 'weekday_day_month_year',
    String definitionId =
        'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      execute({
        'op': 'format_tamil_date',
        'input': {
          'definition_id': definitionId,
          'date': date,
          'context': context.toJson(),
          'script': script,
          'digits': digits,
          'style': style,
        },
      }) as String;

  Map<String, dynamic> calendarDisplayInfo(
    GregorianDate date,
    CalendarContextInput context, {
    String script = 'tamil',
    String digits = 'latin',
    String definitionId =
        'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      execute({
        'op': 'calendar_display_info',
        'input': {
          'definition_id': definitionId,
          'date': date,
          'context': context.toJson(),
          'script': script,
          'digits': digits,
        },
      }) as Map<String, dynamic>;

  Map<String, dynamic> compareCalendarProfiles({
    GregorianDate? date,
    int? instantUnixSeconds,
    required CalendarContext thirukanithamContext,
    required VakyaCivilContext vakyaContext,
  }) {
    final moment = <String, Object?>{};
    if (date != null) moment['date'] = date;
    if (instantUnixSeconds != null) {
      moment['instant_unix_seconds'] = instantUnixSeconds;
    }
    return execute({
      'op': 'compare_calendar_profiles',
      'input': {
        ...moment,
        'thirukanitham_context': thirukanithamContext.toJson(),
        'vakya_context': vakyaContext.toJson(),
      },
    }) as Map<String, dynamic>;
  }

  Map<String, dynamic> thiruvalluvarYearInfo(
    GregorianDate date,
    CalendarContext context, {
    String conventionId = 'tn-thiruvalluvar-thai1-thirukanitham-v1',
  }) =>
      execute({
        'op': 'thiruvalluvar_year_info',
        'input': {
          'convention_id': conventionId,
          'date': date,
          'context': context.toJson(),
        },
      }) as Map<String, dynamic>;

  PanchangamAt panchangamAt(
    int instantUnixSeconds,
    CalendarContextInput context, {
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) {
    final value = execute({
      'op': 'panchangam_at',
      'input': {
        'definition_id': definitionId,
        'instant_unix_seconds': instantUnixSeconds,
        'context': context.toJson(),
      },
    }) as Map<String, dynamic>;
    return PanchangamAt(
      definitionId: value['definition_id'] as String,
      localDate: Map<String, int>.from(value['local_date'] as Map),
      localTime: Map<String, int>.from(value['local_time'] as Map),
      vara: value['vara'] as String,
      limbs: CalendarLimbs.fromJson(
          Map<String, dynamic>.from(value['limbs'] as Map)),
      referenceStation: value['reference_station'] as String?,
      positionBasis: value['position_basis'] as String?,
    );
  }

  PanchangamDay panchangamDay(
    GregorianDate date,
    CalendarContextInput context, {
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) {
    final value = execute({
      'op': 'panchangam_day',
      'input': {
        'definition_id': definitionId,
        'date': date,
        'context': context.toJson(),
      },
    }) as Map<String, dynamic>;
    return PanchangamDay(
      definitionId: value['definition_id'] as String,
      date: Map<String, int>.from(value['date'] as Map),
      sunriseMinuteOfDay: value['sunrise_minute_of_day'] as int,
      sunsetMinuteOfDay: value['sunset_minute_of_day'] as int?,
      sunriseBasis: value['sunrise_basis'] as String?,
      sunsetStatus: value['sunset_status'] as String?,
      vara: value['vara'] as String,
      limbsAtSunrise: CalendarLimbs.fromJson(
          Map<String, dynamic>.from(value['limbs_at_sunrise'] as Map)),
      transitions: (value['transitions'] as List)
          .map((item) => PanchangamTransition.fromJson(
              Map<String, dynamic>.from(item as Map)))
          .toList(),
    );
  }

  LunarPhaseEvents lunarPhaseEvents({
    required int startUnixSeconds,
    required int endUnixSeconds,
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) {
    final value = execute({
      'op': 'lunar_phase_events',
      'input': {
        'definition_id': definitionId,
        'start_unix_seconds': startUnixSeconds,
        'end_unix_seconds': endUnixSeconds,
      },
    }) as Map<String, dynamic>;
    return LunarPhaseEvents(
      definitionId: value['definition_id'] as String,
      events: (value['events'] as List)
          .map((item) =>
              LunarPhaseEvent.fromJson(Map<String, dynamic>.from(item as Map)))
          .toList(),
    );
  }
}

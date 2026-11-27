import 'dart:convert';
import 'dart:ffi';
import 'dart:typed_data';
import 'package:ffi/ffi.dart';

export 'src/lexicon_pack_manager.dart';

typedef ExactDecimal = Map<String, Object?>;
typedef NumericRangeEndpoint = Map<String, Object?>;
typedef GregorianDate = Map<String, int>;

class TokenizationSpan {
  final String text;
  final int startByte;
  final int endByte;
  final int startUnit;
  final int endUnit;

  TokenizationSpan.fromJson(Map<String, dynamic> json)
      : text = json['text'] as String,
        startByte = json['start_byte'] as int,
        endByte = json['end_byte'] as int,
        startUnit = json['start_unit'] as int,
        endUnit = json['end_unit'] as int;
}

enum TokenKind { abbreviation, word, number, other }

class WordToken extends TokenizationSpan {
  final TokenKind kind;

  WordToken.fromJson(super.json)
      : kind = TokenKind.values.byName(json['kind'] as String),
        super.fromJson();
}

class EncodingCandidate {
  final String encoding;
  final double confidence;
  const EncodingCandidate({required this.encoding, required this.confidence});
  factory EncodingCandidate.fromJson(Map<String, dynamic> json) =>
      EncodingCandidate(
        encoding: json['encoding'] as String,
        confidence: (json['confidence'] as num).toDouble(),
      );
  Map<String, dynamic> toJson() => {
        'encoding': encoding,
        'confidence': confidence,
      };
}

class DetectionResult {
  final String status;
  final String? encoding;
  final double confidence;
  final String? reason;
  final List<EncodingCandidate> candidates;

  const DetectionResult({
    required this.status,
    this.encoding,
    required this.confidence,
    this.reason,
    required this.candidates,
  });

  factory DetectionResult.fromJson(Map<String, dynamic> json) =>
      DetectionResult(
        status: json['status'] as String,
        encoding: json['encoding'] as String?,
        confidence: (json['confidence'] as num).toDouble(),
        reason: json['reason'] as String?,
        candidates: (json['candidates'] as List)
            .map((e) => EncodingCandidate.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  Map<String, dynamic> toJson() => {
        'status': status,
        'encoding': encoding,
        'confidence': confidence,
        'reason': reason,
        'candidates': candidates.map((e) => e.toJson()).toList(),
      };
}

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

class LexiconCompactPackSummary {
  final String packId;
  final String category;
  final int indexFormatVersion;
  final int schemaVersion;
  final String packTier;
  final String rightsStatus;
  final String license;
  final String datasetVersion;
  final String description;
  final int entryCount;
  final int senseCount;
  final int relationCount;
  final int distinctHeadwords;
  final int byteLen;
  final String checksumSha256;
  final bool hasFoldedIndex;
  final bool hasRelations;
  final bool hasEnglishIndex;
  final List<String> sourceIds;
  final String attributionNotice;
  final List<String> domains;
  final List<String> regions;
  final List<String> registers;

  const LexiconCompactPackSummary({
    required this.packId,
    required this.category,
    required this.indexFormatVersion,
    required this.schemaVersion,
    required this.packTier,
    required this.rightsStatus,
    required this.license,
    required this.datasetVersion,
    required this.description,
    required this.entryCount,
    required this.senseCount,
    required this.relationCount,
    required this.distinctHeadwords,
    required this.byteLen,
    required this.checksumSha256,
    required this.hasFoldedIndex,
    required this.hasRelations,
    required this.hasEnglishIndex,
    required this.sourceIds,
    required this.attributionNotice,
    required this.domains,
    required this.regions,
    required this.registers,
  });

  factory LexiconCompactPackSummary.fromJson(Map<String, dynamic> json) =>
      LexiconCompactPackSummary(
        packId: json['pack_id'] as String,
        category: json['category'] as String,
        indexFormatVersion: json['index_format_version'] as int,
        schemaVersion: json['schema_version'] as int,
        packTier: json['pack_tier'] as String,
        rightsStatus: json['rights_status'] as String,
        license: json['license'] as String,
        datasetVersion: json['dataset_version'] as String,
        description: json['description'] as String,
        entryCount: json['entry_count'] as int,
        senseCount: json['sense_count'] as int,
        relationCount: json['relation_count'] as int,
        distinctHeadwords: json['distinct_headwords'] as int,
        byteLen: json['byte_len'] as int,
        checksumSha256: json['checksum_sha256'] as String,
        hasFoldedIndex: json['has_folded_index'] as bool? ?? false,
        hasRelations: json['has_relations'] as bool? ?? false,
        hasEnglishIndex: json['has_english_index'] as bool? ?? false,
        sourceIds: ((json['source_ids'] as List?) ?? const []).cast<String>(),
        attributionNotice: json['attribution_notice'] as String? ?? '',
        domains: ((json['domains'] as List?) ?? const []).cast<String>(),
        regions: ((json['regions'] as List?) ?? const []).cast<String>(),
        registers: ((json['registers'] as List?) ?? const []).cast<String>(),
      );
}

class LexiconStoreStats {
  final int packCount;
  final int totalEntries;
  final int totalSenses;
  final int totalRelations;
  final int totalBytes;
  final List<LexiconCompactPackSummary> packs;
  final Map<String, int> categoryCounts;
  final Map<String, int> posCounts;
  final Map<String, int> domainCounts;
  final Map<String, int> regionCounts;
  final Map<String, int> registerCounts;
  final bool hasEnglishIndex;

  const LexiconStoreStats({
    required this.packCount,
    required this.totalEntries,
    required this.totalSenses,
    required this.totalRelations,
    required this.totalBytes,
    required this.packs,
    required this.categoryCounts,
    required this.posCounts,
    required this.domainCounts,
    required this.regionCounts,
    required this.registerCounts,
    required this.hasEnglishIndex,
  });

  static Map<String, int> _intMap(Object? raw) {
    if (raw is! Map) return const {};
    return {
      for (final entry in raw.entries)
        entry.key.toString(): (entry.value as num).toInt(),
    };
  }

  factory LexiconStoreStats.fromJson(Map<String, dynamic> json) =>
      LexiconStoreStats(
        packCount: (json['pack_count'] as num).toInt(),
        totalEntries: (json['total_entries'] as num).toInt(),
        totalSenses: (json['total_senses'] as num).toInt(),
        totalRelations: (json['total_relations'] as num).toInt(),
        totalBytes: (json['total_bytes'] as num).toInt(),
        packs: ((json['packs'] as List?) ?? const [])
            .map((e) => LexiconCompactPackSummary.fromJson(
                Map<String, dynamic>.from(e as Map)))
            .toList(),
        categoryCounts: _intMap(json['category_counts']),
        posCounts: _intMap(json['pos_counts']),
        domainCounts: _intMap(json['domain_counts']),
        regionCounts: _intMap(json['region_counts']),
        registerCounts: _intMap(json['register_counts']),
        hasEnglishIndex: json['has_english_index'] as bool? ?? false,
      );
}

typedef _NativeCall = Pointer<Utf8> Function(Pointer<Utf8>);
typedef _NativeLoadLexiconPack = Pointer<Utf8> Function(Pointer<Uint8>, Size);
typedef _NativeFree = Void Function(Pointer<Utf8>);

/// Thin JSON marshalling around the Rust C ABI. Supply the built library path.
class TamilToolkit {
  final Pointer<Utf8> Function(Pointer<Utf8>) _call;
  final Pointer<Utf8> Function(Pointer<Uint8>, int) _loadLexiconPack;
  final void Function(Pointer<Utf8>) _free;

  TamilToolkit(String libraryPath) : this._(DynamicLibrary.open(libraryPath));

  TamilToolkit._(DynamicLibrary library)
      : _call = library.lookupFunction<_NativeCall,
            Pointer<Utf8> Function(Pointer<Utf8>)>('tamil_toolkit_call'),
        _loadLexiconPack = library.lookupFunction<_NativeLoadLexiconPack,
            Pointer<Utf8> Function(Pointer<Uint8>, int)>(
            'tamil_toolkit_load_lexicon_pack'),
        _free =
            library.lookupFunction<_NativeFree, void Function(Pointer<Utf8>)>(
                'tamil_toolkit_free');

  late final TamilCalendar calendar = TamilCalendar(this);

  Object? _decodeNativeResponse(Pointer<Utf8> output) {
    if (output == nullptr) throw StateError('Rust returned a null response');
    try {
      final result =
          jsonDecode(output.toDartString()) as Map<String, dynamic>;
      if (result.containsKey('error')) throw ArgumentError(result['error']);
      return result['ok'];
    } finally {
      _free(output);
    }
  }

  Object? execute(Map<String, Object?> request) {
    final input = jsonEncode(request).toNativeUtf8();
    try {
      return _decodeNativeResponse(_call(input));
    } finally {
      malloc.free(input);
    }
  }

  List<WordToken> tokenizeWords(String text, {String? stopwordProfile}) =>
      (execute({
        'op': 'tokenize_words',
        'input': {
          'text': text,
          if (stopwordProfile != null) 'stopword_profile': stopwordProfile,
        },
      }) as List)
          .map((row) => WordToken.fromJson(row as Map<String, dynamic>))
          .toList();

  List<TokenizationSpan> segmentSentences(String text) => (execute({
        'op': 'segment_sentences',
        'input': {'text': text},
      }) as List)
          .map((row) => TokenizationSpan.fromJson(row as Map<String, dynamic>))
          .toList();

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
  String senthamilCodesToUnicode(List<int> codes, {String errors = 'strict'}) =>
      execute({
        'op': 'senthamil_codes_to_unicode',
        'input': {'codes': codes, 'errors': errors},
      }) as String;
  String senthamilTextToUnicode(String text, {String errors = 'strict'}) =>
      execute({
        'op': 'senthamil_text_to_unicode',
        'input': {'text': text, 'errors': errors},
      }) as String;
  List<int> unicodeToSenthamilCodes(String text) => (execute({
        'op': 'unicode_to_senthamil_codes',
        'input': {'text': text},
      }) as List<dynamic>)
          .cast<int>();
  String unicodeToSenthamilText(String text) => execute({
        'op': 'unicode_to_senthamil_text',
        'input': {'text': text},
      }) as String;
  String shreeTamCodesToUnicode(List<int> codes, {String errors = 'strict'}) =>
      execute({
        'op': 'shree_tam_codes_to_unicode',
        'input': {'codes': codes, 'errors': errors},
      }) as String;
  String shreeTamTextToUnicode(String text, {String errors = 'strict'}) =>
      execute({
        'op': 'shree_tam_text_to_unicode',
        'input': {'text': text, 'errors': errors},
      }) as String;
  List<int> unicodeToShreeTamCodes(String text) => (execute({
        'op': 'unicode_to_shree_tam_codes',
        'input': {'text': text},
      }) as List<dynamic>)
          .cast<int>();
  String unicodeToShreeTamText(String text) => execute({
        'op': 'unicode_to_shree_tam_text',
        'input': {'text': text},
      }) as String;
  String softviewCodesToUnicode(List<int> codes, {String errors = 'strict'}) =>
      execute({
        'op': 'softview_codes_to_unicode',
        'input': {'codes': codes, 'errors': errors},
      }) as String;
  String softviewTextToUnicode(String text, {String errors = 'strict'}) =>
      execute({
        'op': 'softview_text_to_unicode',
        'input': {'text': text, 'errors': errors},
      }) as String;
  List<int> unicodeToSoftviewCodes(String text) => (execute({
        'op': 'unicode_to_softview_codes',
        'input': {'text': text},
      }) as List<dynamic>)
          .cast<int>();
  String unicodeToSoftviewText(String text) => execute({
        'op': 'unicode_to_softview_text',
        'input': {'text': text},
      }) as String;
  String tboCodesToUnicode(List<int> codes, {String errors = 'strict'}) =>
      execute({
        'op': 'tbo_codes_to_unicode',
        'input': {'codes': codes, 'errors': errors},
      }) as String;
  String tboTextToUnicode(String text, {String errors = 'strict'}) => execute({
        'op': 'tbo_text_to_unicode',
        'input': {'text': text, 'errors': errors},
      }) as String;
  List<int> unicodeToTboCodes(String text) => (execute({
        'op': 'unicode_to_tbo_codes',
        'input': {'text': text},
      }) as List<dynamic>)
          .cast<int>();
  String unicodeToTboText(String text) => execute({
        'op': 'unicode_to_tbo_text',
        'input': {'text': text},
      }) as String;
  String unicodeToBraille(String text, {String errors = 'strict'}) => execute({
        'op': 'unicode_to_braille',
        'input': {'text': text, 'errors': errors},
      }) as String;
  String brailleToUnicode(String text, {String errors = 'strict'}) => execute({
        'op': 'braille_to_unicode',
        'input': {'text': text, 'errors': errors},
      }) as String;
  DetectionResult detectEncoding(dynamic data) {
    Map<String, dynamic> input;
    if (data is String) {
      input = {'text': data};
    } else if (data is List<int>) {
      if (data.any((x) => x > 255)) {
        input = {'codes': data};
      } else {
        input = {'bytes': data};
      }
    } else {
      throw ArgumentError('data must be String or List<int>');
    }
    final raw = execute({
      'op': 'detect_encoding',
      'input': input,
    }) as Map<String, dynamic>;
    return DetectionResult.fromJson(raw);
  }

  String detectAndDecode(dynamic data) {
    Map<String, dynamic> input;
    if (data is String) {
      input = {'text': data};
    } else if (data is List<int>) {
      input = {'bytes': data};
    } else {
      throw ArgumentError('data must be String or List<int>');
    }
    return execute({
      'op': 'detect_and_decode',
      'input': input,
    }) as String;
  }

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
  String mixedFractionToWords(
          {required bool negative,
          required int whole,
          required int numerator,
          required int denominator,
          String locale = 'TN'}) =>
      execute({
        'op': 'mixed_fraction_to_words',
        'input': {
          'negative': negative,
          'whole': whole,
          'numerator': numerator,
          'denominator': denominator,
          'locale': locale
        },
      }) as String;
  int wordsToNumber(String text, {String locale = 'TN'}) => execute({
        'op': 'words_to_number',
        'input': {'text': text, 'locale': locale},
      }) as int;
  String transliterate(String text, String scheme,
          {String direction = 'to_tamil'}) =>
      execute({
        'op': 'transliterate',
        'input': {'text': text, 'scheme': scheme, 'direction': direction},
      }) as String;
  List<dynamic> transliterateSchemes() => execute({
        'op': 'transliterate_schemes',
        'input': <String, dynamic>{},
      }) as List<dynamic>;
  List<String> transliterateSuggest(String text,
          {String scheme = 'phonetic-v1', int limit = 5}) =>
      (execute({
        'op': 'transliterate_suggest',
        'input': {'text': text, 'scheme': scheme, 'limit': limit},
      }) as List<dynamic>)
          .cast<String>();
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
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
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
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      execute({
        'op': 'tamil_year_cycle_info',
        'input': {
          'definition_id': definitionId,
          'solar_year': solarYear,
          'context': context.toJson(),
        },
      }) as Map<String, dynamic>;

  Map<String, dynamic> calendarOfficialHolidays(
          String jurisdiction, int year) =>
      execute({
        'op': 'calendar_official_holidays',
        'input': {'jurisdiction': jurisdiction, 'year': year},
      }) as Map<String, dynamic>;

  Map<String, dynamic> calendarObservances(
    int gregorianYear,
    CalendarContextInput context, {
    String ruleSet = 'thirukanitham-tamil-named-observances-v1',
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
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
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
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
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
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
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
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
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
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

  Map<String, dynamic> hyphenateWord(
    String word, {
    String delimiter = '\u00AD',
    int leftMin = 2,
    int rightMin = 2,
  }) =>
      execute({
        'op': 'hyphenate_word',
        'input': {
          'word': word,
          'delimiter': delimiter,
          'left_min': leftMin,
          'right_min': rightMin,
        },
      }) as Map<String, dynamic>;

  List<dynamic> hyphenationPoints(
    String word, {
    int leftMin = 2,
    int rightMin = 2,
  }) =>
      execute({
        'op': 'hyphenation_points',
        'input': {
          'word': word,
          'left_min': leftMin,
          'right_min': rightMin,
        },
      }) as List<dynamic>;

  String hyphenateText(
    String text, {
    String delimiter = '\u00AD',
    int leftMin = 2,
    int rightMin = 2,
  }) =>
      execute({
        'op': 'hyphenate_text',
        'input': {
          'text': text,
          'delimiter': delimiter,
          'left_min': leftMin,
          'right_min': rightMin,
        },
      }) as String;

  Map<String, dynamic> wrapText(
    String text,
    int maxWidth, {
    String delimiter = '-',
    int leftMin = 2,
    int rightMin = 2,
  }) =>
      execute({
        'op': 'wrap_text',
        'input': {
          'text': text,
          'max_width': maxWidth,
          'delimiter': delimiter,
          'left_min': leftMin,
          'right_min': rightMin,
        },
      }) as Map<String, dynamic>;

  /// Look up a Tamil word in compiled embedded lexicon packs.
  Map<String, dynamic> lexiconLookup(
    String text, {
    List<String>? packs,
    String? region,
    String? register,
  }) {
    final request = <String, Object?>{
      'op': 'lexicon_lookup',
      'input': text,
    };
    if (packs != null) {
      request['packs'] = packs;
    }
    if (region != null) {
      request['region'] = region;
    }
    if (register != null) {
      request['register'] = register;
    }
    return Map<String, dynamic>.from(execute(request) as Map);
  }

  /// Return metadata for compiled lexicon packs available in this build.
  List<Map<String, dynamic>> lexiconPacks() =>
      (execute({'op': 'lexicon_packs', 'input': null}) as List)
          .map((item) => Map<String, dynamic>.from(item as Map))
          .toList();

  Map<String, Object?> _buildLexiconScopeRequest(
    String op,
    String text, {
    int? limit,
    String? afterKey,
    int? maxDistance,
    List<String>? packs,
    String? tier,
    String? category,
    String? pos,
    String? domain,
    String? region,
    String? register,
    bool? folded,
  }) =>
      {
        'op': op,
        'input': text,
        if (limit != null) 'limit': limit,
        if (afterKey != null) 'after_key': afterKey,
        if (maxDistance != null) 'max_distance': maxDistance,
        if (packs != null) 'packs': packs,
        if (tier != null) 'tier': tier,
        if (category != null) 'category': category,
        if (pos != null) 'pos': pos,
        if (domain != null) 'domain': domain,
        if (region != null) 'region': region,
        if (register != null) 'register': register,
        if (folded != null) 'folded': folded,
      };

  /// Initialize the runtime lexicon registry using a named [profile]
  /// (`'open-lite'`, `'open'`, `'local'`, `'full'`) from [path] (or
  /// auto-discovered pack directory when [path] is null).
  Map<String, dynamic> lexiconInit({
    String profile = 'full',
    String? path,
    bool replace = true,
  }) =>
      Map<String, dynamic>.from(
        execute({
          'op': 'lexicon_init',
          'input': {
            'profile': profile,
            'replace': replace,
            if (path != null) 'path': path,
          },
        }) as Map,
      );

  /// Load a `.tlpack` v1 or v2 binary image from bytes into the runtime registry.
  Map<String, dynamic> lexiconLoadPackBytes(Uint8List bytes) {
    if (bytes.isEmpty) {
      return Map<String, dynamic>.from(
        _decodeNativeResponse(_loadLexiconPack(nullptr, 0)) as Map,
      );
    }
    final buffer = malloc<Uint8>(bytes.length);
    try {
      buffer.asTypedList(bytes.length).setAll(0, bytes);
      return Map<String, dynamic>.from(
        _decodeNativeResponse(_loadLexiconPack(buffer, bytes.length)) as Map,
      );
    } finally {
      malloc.free(buffer);
    }
  }

  /// Load a `.tlpack` file or directory of packs into the runtime registry.
  Map<String, dynamic> lexiconLoadPack(String path) =>
      Map<String, dynamic>.from(
        execute({
          'op': 'lexicon_load_pack',
          'input': {'path': path},
        }) as Map,
      );

  /// Unmount one runtime pack by [packId], or clear all runtime packs if null.
  Map<String, dynamic> lexiconUnloadPack([String? packId]) =>
      Map<String, dynamic>.from(
        execute({
          'op': 'lexicon_unload_pack',
          'input': packId,
        }) as Map,
      );

  /// Return runtime pack counts, totals, and loaded pack summaries.
  Map<String, dynamic> lexiconStats() => Map<String, dynamic>.from(
        execute({'op': 'lexicon_stats', 'input': null}) as Map,
      );

  /// Return typed runtime pack statistics including facet counts and English index status.
  LexiconStoreStats lexiconStatsModel() =>
      LexiconStoreStats.fromJson(lexiconStats());

  /// Build a unified, deduplicated word definition across mounted runtime packs.
  Map<String, dynamic> lexiconDefine(
    String text, {
    List<String>? packs,
    String? tier,
    String? category,
    String? pos,
    String? domain,
    String? region,
    String? register,
    bool folded = false,
  }) =>
      Map<String, dynamic>.from(
        execute(_buildLexiconScopeRequest(
          'lexicon_define',
          text,
          packs: packs,
          tier: tier,
          category: category,
          pos: pos,
          domain: domain,
          region: region,
          register: register,
          folded: folded,
        )) as Map,
      );

  /// Query compact runtime lexicon entries with optional scope filters.
  Map<String, dynamic> lexiconQuery(
    String text, {
    List<String>? packs,
    String? tier,
    String? category,
    String? pos,
    String? domain,
    String? region,
    String? register,
    bool folded = false,
  }) =>
      Map<String, dynamic>.from(
        execute(_buildLexiconScopeRequest(
          'lexicon_query',
          text,
          packs: packs,
          tier: tier,
          category: category,
          pos: pos,
          domain: domain,
          region: region,
          register: register,
          folded: folded,
        )) as Map,
      );

  /// Run FST prefix search across mounted runtime lexicon packs.
  Map<String, dynamic> lexiconSearch(
    String prefix, {
    int limit = 25,
    String? afterKey,
    List<String>? packs,
    String? tier,
    String? category,
    String? pos,
    String? domain,
    String? region,
    String? register,
    bool folded = false,
  }) =>
      Map<String, dynamic>.from(
        execute(_buildLexiconScopeRequest(
          'lexicon_search',
          prefix,
          limit: limit,
          afterKey: afterKey,
          packs: packs,
          tier: tier,
          category: category,
          pos: pos,
          domain: domain,
          region: region,
          register: register,
          folded: folded,
        )) as Map,
      );

  /// Search mounted runtime lexicon packs by English gloss/definition keywords.
  Map<String, dynamic> lexiconSearchEnglish(
    String query, {
    int limit = 25,
    List<String>? packs,
    String? tier,
    String? category,
    String? pos,
    String? domain,
    String? region,
    String? register,
  }) =>
      Map<String, dynamic>.from(
        execute({
          'op': 'lexicon_search_english',
          'input': {
            'query': query,
            'limit': limit,
            if (packs != null) 'packs': packs,
            if (tier != null) 'tier': tier,
            if (category != null) 'category': category,
            if (pos != null) 'pos': pos,
            if (domain != null) 'domain': domain,
            if (region != null) 'region': region,
            if (register != null) 'register': register,
          },
        }) as Map,
      );

  /// Run bounded Damerau-Levenshtein fuzzy search across mounted runtime lexicon packs.
  Map<String, dynamic> lexiconFuzzySearch(
    String text, {
    int maxDistance = 1,
    int limit = 10,
    List<String>? packs,
    String? tier,
    String? category,
    String? pos,
    String? domain,
    String? region,
    String? register,
  }) =>
      Map<String, dynamic>.from(
        execute(_buildLexiconScopeRequest(
          'lexicon_fuzzy_search',
          text,
          maxDistance: maxDistance,
          limit: limit,
          packs: packs,
          tier: tier,
          category: category,
          pos: pos,
          domain: domain,
          region: region,
          register: register,
        )) as Map,
      );

  /// Return exact FST keys that are char-boundary prefixes of [text], longest-first.
  Map<String, dynamic> lexiconLongestPrefix(
    String text, {
    List<String>? packs,
    String? tier,
    String? category,
  }) =>
      Map<String, dynamic>.from(
        execute(_buildLexiconScopeRequest(
          'lexicon_longest_prefix',
          text,
          packs: packs,
          tier: tier,
          category: category,
        )) as Map,
      );

  /// Query indexed lexical relations for [text] across mounted packs.
  Map<String, dynamic> lexiconRelations(
    String text, {
    List<String>? packs,
    String? tier,
    String? category,
    bool folded = false,
  }) =>
      Map<String, dynamic>.from(
        execute(_buildLexiconScopeRequest(
          'lexicon_relations',
          text,
          packs: packs,
          tier: tier,
          category: category,
          folded: folded,
        )) as Map,
      );

  /// Compute the normalized SHA-256 bucket key for an owner-supplied source query.
  Map<String, dynamic> lexiconSourceBucket(String query) =>
      Map<String, dynamic>.from(
        execute({'op': 'lexicon_source_bucket', 'input': query}) as Map,
      );

  /// Look up paginated owner-supplied historical source records in [bucket].
  Map<String, dynamic> lexiconSourceLookup(
    String query,
    Map<String, Object?> bucket, {
    int offset = 0,
    int limit = 25,
  }) =>
      Map<String, dynamic>.from(
        execute({
          'op': 'lexicon_source_lookup',
          'input': {
            'query': query,
            'bucket': bucket,
            'offset': offset,
            'limit': limit,
          },
        }) as Map,
      );

  Map<String, dynamic> punarchiJoin(
    String first,
    String second, {
    String profile = 'nannool-v1',
    Map<String, Object?>? context,
  }) =>
      execute({
        'op': 'punarchi_join',
        'input': {
          'first': first,
          'second': second,
          'profile': profile,
          if (context != null) 'context': context,
        },
      }) as Map<String, dynamic>;

  List<Map<String, dynamic>> punarchiSplitCandidates(
    String surface, {
    String profile = 'nannool-v1',
    bool poetic = false,
  }) =>
      (execute({
        'op': 'punarchi_split_candidates',
        'input': {
          'surface': surface,
          'profile': profile,
          'poetic': poetic,
        },
      }) as List<dynamic>)
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();

  List<Map<String, dynamic>> punarchiRules({
    String profile = 'nannool-v1',
    String? chapter,
    int? sutra,
  }) =>
      (execute({
        'op': 'punarchi_rules',
        'input': {
          'profile': profile,
          if (chapter != null) 'chapter': chapter,
          if (sutra != null) 'sutra': sutra,
        },
      }) as List<dynamic>)
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
}

class TamilCalendar {
  final TamilToolkit _toolkit;
  TamilCalendar(this._toolkit);

  Map<String, dynamic> gregorianToTamilDate(
    GregorianDate date,
    CalendarContextInput context, {
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      _toolkit.gregorianToTamilDate(date, context, definitionId: definitionId);

  Map<String, dynamic> tamilToGregorianDate(
    TamilSolarDate date,
    CalendarContextInput context, {
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      _toolkit.tamilToGregorianDate(date, context, definitionId: definitionId);

  Map<String, dynamic> tamilMonthInfo(
    int solarYear,
    int month,
    CalendarContextInput context, {
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      _toolkit.tamilMonthInfo(solarYear, month, context,
          definitionId: definitionId);

  Map<String, dynamic> tamilYearInfo(
    int solarYear,
    CalendarContextInput context, {
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      _toolkit.tamilYearInfo(solarYear, context, definitionId: definitionId);

  Map<String, dynamic> tamilYearCycleInfo(
    int solarYear,
    CalendarContextInput context, {
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      _toolkit.tamilYearCycleInfo(solarYear, context,
          definitionId: definitionId);

  Map<String, dynamic> officialHolidays(String jurisdiction, int year) =>
      _toolkit.calendarOfficialHolidays(jurisdiction, year);

  Map<String, dynamic> observances(
    int gregorianYear,
    CalendarContextInput context, {
    String ruleSet = 'thirukanitham-tamil-named-observances-v1',
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
    int? month,
  }) =>
      _toolkit.calendarObservances(gregorianYear, context,
          ruleSet: ruleSet, definitionId: definitionId, month: month);

  PanchangamAt panchangamAt(
    int instantUnixSeconds,
    CalendarContextInput context, {
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      _toolkit.panchangamAt(instantUnixSeconds, context,
          definitionId: definitionId);

  PanchangamDay panchangamDay(
    GregorianDate date,
    CalendarContextInput context, {
    String definitionId = 'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
  }) =>
      _toolkit.panchangamDay(date, context, definitionId: definitionId);
}

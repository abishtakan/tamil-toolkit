import 'dart:convert';
import 'dart:io';
import 'package:tamil_toolkit/tamil_toolkit.dart';
import 'package:test/test.dart';

void main() {
  final root = Directory('../..').absolute.path;
  final extension =
      Platform.isWindows ? 'dll' : (Platform.isMacOS ? 'dylib' : 'so');
  final prefix = Platform.isWindows ? '' : 'lib';
  final tamil =
      TamilToolkit('$root/target/debug/${prefix}tamil_toolkit_ffi.$extension');
  final golden = '$root/tests/golden';
  final manifest = jsonDecode(File('$golden/manifest.json').readAsStringSync());
  if (manifest['version'] != 1) throw StateError('Unsupported golden manifest');
  final ids = <String>{};
  final files = <String>{};
  final includePlanned =
      (Platform.environment['TAMIL_GOLDEN_INCLUDE_PLANNED'] ?? '')
          .split(',')
          .map((name) => name.trim())
          .where((name) => name.isNotEmpty)
          .toSet();
  var count = 0;
  var plannedReviewCount = 0;
  Map<String, dynamic>? wordCase;
  Map<String, dynamic>? keyCase;
  Map<String, dynamic>? numeralCase;
  Map<String, dynamic>? codecWord;
  Map<String, dynamic>? codecPreserved;
  Map<String, dynamic>? encoderWord;
  Map<String, dynamic>? encoderNfd;
  Map<String, dynamic>? encoderCollision;
  final moneyCases = <Map<String, dynamic>>[];
  final formatCases = <Map<String, dynamic>>[];
  for (final suite in manifest['suites']) {
    if (!files.add(suite['file'] as String)) {
      throw StateError('Duplicate suite');
    }
    if (!['active', 'planned'].contains(suite['status'])) {
      throw StateError('Unknown status');
    }
    final lines = File('$golden/${suite['file']}').readAsLinesSync();
    if (suite['status'] == 'active' && lines.isEmpty) {
      throw StateError('Empty active suite');
    }
    for (final line in lines) {
      final row = jsonDecode(line) as Map<String, dynamic>;
      if (row['id'] == 'collate_words_basic') wordCase = row;
      if (row['id'] == 'collate_key_001') keyCase = row;
      if (row['id'] == 'num_014') numeralCase = row;
      if (row['id'] == 'codec_word_000_tn_strict') codecWord = row;
      if (row['id'] == 'codec_joiner_boundary_0') codecPreserved = row;
      if (row['id'] == 'encode_word_000_tn') encoderWord = row;
      if (row['id'] == 'encode_collision_000_tn') encoderCollision = row;
      if (encoderNfd == null &&
          (row['id'] as String).startsWith('encode_mapping_') &&
          (row['id'] as String).endsWith('_tn_nfd')) {
        encoderNfd = row;
      }
      if (['format_currency', 'currency_to_words'].contains(row['op']) &&
          row.containsKey('expected')) {
        moneyCases.add(row);
      }
      if ([
            'format_fraction',
            'fraction_to_words',
            'fraction_symbol',
            'format_date'
          ].contains(row['op']) &&
          row.containsKey('expected')) {
        formatCases.add(row);
      }
      if (!ids.add(row['id'] as String)) {
        throw StateError('Duplicate golden ID');
      }
      if (suite['status'] == 'planned' &&
          !includePlanned.contains(suite['file'])) {
        continue;
      }
      if (!(suite['operations'] as List).contains(row['op'])) {
        throw StateError('Undeclared operation');
      }
      if (row.containsKey('expected') == row.containsKey('expected_error')) {
        throw StateError('Require exactly one outcome');
      }
      if (row.containsKey('expected_error') &&
          (row['expected_error'] is! String ||
              (row['expected_error'] as String).isEmpty)) {
        throw StateError('Invalid expected error');
      }
      count++;
      if (suite['status'] == 'planned') plannedReviewCount++;
      test(row['id'] as String, () {
        if (row.containsKey('expected_error')) {
          expect(
              () => tamil.execute(row),
              throwsA(isA<ArgumentError>().having(
                (error) => error.message,
                'message',
                row['expected_error'],
              )));
        } else {
          expect(tamil.execute(row), equals(row['expected']));
        }
      });
    }
  }
  final onDisk = Directory(golden)
      .listSync()
      .whereType<File>()
      .where((f) => f.path.endsWith('.jsonl'))
      .map((f) => f.uri.pathSegments.last)
      .toSet();
  if (files.length != onDisk.length || !files.containsAll(onDisk)) {
    throw StateError('Unregistered suite');
  }
  if (count == 0) {
    throw StateError('No active golden vectors');
  }
  if (plannedReviewCount > 0) {
    stdout.writeln(
        'PRE-ACTIVATION REVIEW executed $plannedReviewCount selected planned vectors; they are not active parity coverage.');
  }
  test('invalid operation crosses C ABI as an error', () {
    expect(() => tamil.execute({'op': 'unknown', 'input': ''}),
        throwsArgumentError);
  });
  test('collation convenience APIs', () {
    final words = wordCase!;
    final key = keyCase!;
    expect(tamil.sortWords((words['input'] as List).cast<String>()),
        equals(words['expected']));
    expect(tamil.sortKey(key['input'] as String), equals(key['expected']));
    expect(tamil.searchKey(key['input'] as String), equals(key['expected']));
    expect(tamil.compare(key['input'] as String, key['input'] as String), 0);
  });
  test('numeral convenience APIs', () {
    expect(tamil.toWords(1025, locale: 'SL'), numeralCase!['expected']);
    for (final row in moneyCases) {
      final input = row['input'] as Map<String, dynamic>;
      final amount = (input['amount_minor'] as num).toInt();
      final currency = input['currency'] as String;
      final locale = input['locale'] as String? ?? 'TN';
      final result = row['op'] == 'format_currency'
          ? tamil.formatCurrency(amount, currency, locale: locale)
          : tamil.currencyToWords(amount, currency, locale: locale);
      expect(result, row['expected']);
    }
    expect(() => tamil.formatCurrency(1, 'USD'), throwsArgumentError);
  });
  test('codec convenience API', () {
    final word = codecWord!;
    final preserved = codecPreserved!;
    final input = preserved['input'] as Map<String, dynamic>;
    expect(tamil.baminiToUnicode((word['input'] as Map)['text'] as String),
        word['expected']);
    expect(
        tamil.baminiToUnicode(input['text'] as String,
            errors: input['errors'] as String),
        preserved['expected']);
    expect(() => tamil.baminiToUnicode('*'), throwsArgumentError);
    expect(() => tamil.baminiToUnicode('f', errors: 'ignore'),
        throwsArgumentError);
  });
  test('encoder convenience API', () {
    final word = encoderWord!;
    final nfd = encoderNfd!;
    final collision = encoderCollision!;
    final text = (word['input'] as Map)['text'] as String;
    final encoded = tamil.unicodeToBamini(text);
    expect(encoded, word['expected']);
    expect(tamil.baminiToUnicode(encoded), tamil.normalizeNfc(text));
    expect(tamil.unicodeToBamini((nfd['input'] as Map)['text'] as String),
        nfd['expected']);
    expect(
        () => tamil
            .unicodeToBamini((collision['input'] as Map)['text'] as String),
        throwsA(isA<ArgumentError>().having(
          (error) => error.message,
          'message',
          collision['expected_error'],
        )));
  });
  test('Anjal byte convenience APIs', () {
    expect(tamil.anjalBytesToUnicode([0x8d]), '\u0b95');
    expect(tamil.unicodeToAnjalBytes('\u0b95'), [0x8d]);
    expect(() => tamil.anjalBytesToUnicode([0xe5]), throwsArgumentError);
  });
  test('TAM byte convenience APIs', () {
    expect(tamil.tamBytesToUnicode([0x41]), '\u0b95\u0bbf');
    expect(tamil.unicodeToTamBytes('\u0b95\u0bbf'), [0x41]);
    expect(() => tamil.unicodeToTamBytes('A'), throwsArgumentError);
  });
  test('TAB byte convenience APIs', () {
    expect(tamil.tabBytesToUnicode([0xe8, 0xa4]), '\u0b95\u0bbf');
    expect(tamil.unicodeToTabBytes('\u0b95\u0bbf'), [0xe8, 0xa4]);
    expect(() => tamil.tabBytesToUnicode([0x98]), throwsArgumentError);
  });
  test('TSCII byte convenience API', () {
    expect(tamil.tsciiBytesToUnicode([0xba, 0xa2, 0xc5, 0xfd]),
        '\u0b9a\u0bbf\u0bb5\u0ba9\u0bcd');
    expect(tamil.unicodeToTsciiBytes('\u0b87'), [0xfe]);
    expect(() => tamil.tsciiBytesToUnicode([65, 255]), throwsArgumentError);
  });
  test('Vanavil convenience APIs', () {
    expect(tamil.vanavilCodesToUnicode([0x006a, 0x00e4, 0x0153]),
        '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd');
    expect(tamil.vanavilTextToUnicode('j\u00e4\u0153'),
        '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd');
    expect(tamil.unicodeToVanavilCodes('\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'),
        [0x006a, 0x00e4, 0x0153]);
    expect(tamil.unicodeToVanavilText('\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'),
        'j\u00e4\u0153');
    expect(() => tamil.unicodeToVanavilText('\u0bb6\u0bcd\u0bb0\u0bc0'),
        throwsArgumentError);
  });
  test('fraction and date convenience APIs', () {
    for (final row in formatCases) {
      final input = row['input'] as Map<String, dynamic>;
      final locale = input['locale'] as String? ?? 'TN';
      final digits = input['digits'] as String? ?? 'latin';
      final result = switch (row['op']) {
        'format_fraction' => tamil.formatFraction(
            (input['numerator'] as num).toInt(),
            (input['denominator'] as num).toInt(),
            digits: digits),
        'fraction_to_words' => tamil.fractionToWords(
            (input['numerator'] as num).toInt(),
            (input['denominator'] as num).toInt(),
            locale: locale),
        'fraction_symbol' => tamil.fractionSymbol(
            (input['numerator'] as num).toInt(),
            (input['denominator'] as num).toInt()),
        'format_date' => tamil.formatDate((input['year'] as num).toInt(),
            (input['month'] as num).toInt(), (input['day'] as num).toInt(),
            locale: locale,
            style: input['style'] as String? ?? 'long',
            digits: digits),
        _ => throw StateError('Undeclared format API'),
      };
      expect(result, row['expected']);
    }
    expect(() => tamil.formatFraction(1, 0), throwsArgumentError);
    expect(() => tamil.formatDate(2023, 2, 29), throwsArgumentError);
  });
  test('exact numeral and Gregorian convenience APIs', () {
    final value = tamil.parseDecimal('12.3400', 'latin');
    expect(value, {'negative': false, 'coefficient': '123400', 'scale': 4});
    expect(tamil.formatDecimal(value), '12.3400');
    expect(tamil.formatDecimal(value, digits: 'tamil'),
        '\u0be7\u0be8.\u0be9\u0bea\u0be6\u0be6');
    expect(
        tamil.decimalToWords('12.03', 'latin'),
        endsWith(
          '\u0baa\u0bc1\u0bb3\u0bcd\u0bb3\u0bbf \u0baa\u0bc2\u0b9c\u0bcd\u0baf\u0bae\u0bcd \u0bae\u0bc2\u0ba9\u0bcd\u0bb1\u0bc1',
        ));
    expect(tamil.ordinalToWords(21), isNotEmpty);
    expect(tamil.digitSequenceToWords('0071', 'latin').split(' ').length, 4);
    expect(tamil.formatCurrencyDecimal('123.45', 'latin', 'LKR'), 'LKR 123.45');
    expect(tamil.parseFractionSymbol('-\u{11fd1}'),
        {'numerator': -1, 'denominator': 2});
    expect(tamil.symbolInfo('\u{11fd1}')['canonical_alternative'], 73681);
    final mixed = tamil.formatMixedFraction(
        negative: false, whole: 5, numerator: 2, denominator: 4);
    expect(tamil.parseMixedFraction(mixed, 'latin'), {
      'negative': false,
      'whole': 5,
      'numerator': 1,
      'denominator': 2,
    });
    final traditional = tamil.formatTraditionalInteger(1234567);
    expect(tamil.parseTraditionalInteger(traditional), 1234567);
    expect(tamil.parsePercent('12.50%', 'latin'), {
      'negative': false,
      'coefficient': '1250',
      'scale': 2,
    });
    expect(
        tamil.ratioToPercent(
            {'negative': false, 'coefficient': '125', 'scale': 3}),
        {
          'negative': false,
          'coefficient': '125',
          'scale': 1,
        });
    expect(
        tamil.formatNumericRange(
          {'type': 'fraction', 'numerator': 1, 'denominator': 4},
          {
            'type': 'decimal',
            'value': {'negative': false, 'coefficient': '5', 'scale': 0}
          },
          startInclusive: false,
          endInclusive: true,
          separator: ' to ',
        ),
        '(1/4 to 5]');
    expect(tamil.weekday(2024, 1, 1), 'monday');
    expect(
        tamil.addGregorianDate(2024, 1, 31, 'months', 1, overflow: 'clamp'), {
      'year': 2024,
      'month': 2,
      'day': 29,
    });
    expect(
        tamil.dateDifference(
          {'year': 2024, 'month': 2, 'day': 28},
          {'year': 2024, 'month': 3, 'day': 1},
        ),
        2);
    expect(tamil.dateInterval('2024-02-28', '2024-03-01')['inclusive_days'], 3);
  });
  test('historical Vakyakarana solar convenience APIs', () {
    final year = tamil.vakyaSolarTransits(1890);
    expect(year['ahargana'],
        {'days': 1851494, 'nadi': 6, 'vinadi': 15, 'weekday': 'Saturday'});
    expect((year['transits'] as List).first, {
      'rasi': 'vrishabha',
      'day_field': 4,
      'weekday': 'Tuesday',
      'nadi': 1,
      'vinadi': 47,
    });
    final sun = tamil.vakyaTrueSunFromMeshaElapsed(180, 19, 41);
    expect(sun['true_sun'], {'degrees': 173, 'minutes': 28, 'seconds': 33});
    final moon = tamil.vakyaTrueMoonFromKaliDay(1844004);
    expect(moon['moon_vakya_number'], 154);
    expect(moon['uncorrected_true_moon'],
        {'rasi': 4, 'degrees': 11, 'minutes': 14, 'seconds': 1});
    expect(moon['true_moon'],
        {'rasi': 4, 'degrees': 11, 'minutes': 17, 'seconds': 32});
    final localSunrise = tamil.vakyaReduceToLocalTrueSunrise(
      truePosition: {'rasi': 4, 'degrees': 11, 'minutes': 17, 'seconds': 32},
      dailyMotion: {'degrees': 14, 'minutes': 12, 'seconds': 0},
      caraHalfVinadiTenths: 130,
      desantaraVinadiTenths: -266,
      bhujaantaraVinadiTenths: -210,
    );
    expect(localSunrise['correction_arcseconds'], -491);
    expect(localSunrise['local_true_position'], {
      'rasi': 4,
      'degrees': 11,
      'minutes': 9,
      'seconds': 21,
    });
    final cara = tamil.vakyaCaraFromSayanaSun(
      sayanaSun: {'rasi': 4, 'degrees': 22, 'minutes': 30, 'seconds': 0},
      equinoctialShadowTenths: 30,
    );
    expect(cara['bhuja'], {
      'rasi': 1,
      'degrees': 7,
      'minutes': 30,
      'seconds': 0,
    });
    expect(cara['cara_vinadi_tenths'], -720);
    final desantara = tamil.vakyaDesantaraFromYojanaDistance(244);
    expect(desantara['desantara_vinadi_tenths'], -266);
    final bhujaantara = tamil.vakyaBhujaantaraFromTrueSun(
      sunRasi: 5,
      sunRasiProgressArcseconds: 84513,
    );
    expect(bhujaantara['bhujaantara_vinadi_tenths'], -210);
  });
  test('Thirukanitham typed calendar APIs', () {
    const context = CalendarContext(
      region: 'TN',
      latitudeMicrodegrees: 13087840,
      longitudeMicrodegrees: 80278470,
      elevationMeters: 14,
      timeZone: 'Asia/Kolkata',
    );
    final date = {'year': 2026, 'month': 11, 'day': 1};
    expect(
      tamil.calendarProfileInfo()['definition_id'],
      'thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2',
    );
    final converted = tamil.gregorianToTamilDate(date, context);
    expect(converted['tamil_date'], {
      'solar_year': 2026,
      'month': 7,
      'month_name': 'Aippasi',
      'day': 15,
    });
    expect(
      tamil.tamilToGregorianDate(
        const TamilSolarDate(solarYear: 2026, month: 7, day: 15),
        context,
      )['gregorian_date'],
      date,
    );
    expect(tamil.tamilMonthInfo(2026, 7, context)['days'], 30);
    final year = tamil.tamilYearInfo(2025, context);
    expect(year['days'], 365);
    expect(year['months'], hasLength(12));
    expect((year['year_cycle'] as Map)['cycle_name'], 'Visvavasu');
    expect(tamil.tamilYearCycleInfo(2024, context)['cycle_name'], 'Krodhi');
    expect(
      tamil.addTamilDate(
        const TamilSolarDate(solarYear: 2025, month: 1, day: 1),
        'days',
        1,
        context,
      )['gregorian_date'],
      {'year': 2025, 'month': 4, 'day': 15},
    );
    final instant = tamil.panchangamAt(1793514600, context);
    expect(instant.limbs.tithi.name, 'Saptami');
    expect(instant.vara, 'Sunday');
    final day = tamil.panchangamDay(date, context);
    expect(day.sunriseMinuteOfDay, 362);
    expect(day.transitions, hasLength(5));
    final periods = tamil.calendarDaylightPeriods(date, context);
    expect(
      (periods['intervals'] as List)
          .map((period) => (period as Map)['period']),
      ['yamagandam', 'kuligai', 'rahukalam'],
    );
  });
  test('named observance convenience API', () {
    const context = CalendarContext(
      region: 'TN',
      latitudeMicrodegrees: 13087840,
      longitudeMicrodegrees: 80278470,
      elevationMeters: 14,
      timeZone: 'Asia/Kolkata',
    );
    final result = tamil.calendarObservances(2026, context);
    expect(result['rule_set_id'], 'thirukanitham-tamil-named-observances-v1');
    expect(result['source_compatibility'], 'publisher_equivalence_not_claimed');
    expect(result['supported_event_ids'], contains('amavasya_tithi_day'));
    expect(result['events'], isNotEmpty);
  });
  test('bounded Vakyakarana civil APIs', () {
    const definition =
        'vakyakarana-1962-laghuprakashika-civil-ujjain-mean-sunrise-v1';
    const context = VakyaCivilContext(timeZone: 'Asia/Kolkata');
    final date = {'year': 1947, 'month': 10, 'day': 11};
    expect(tamil.calendarProfileInfo(definitionId: definition)['day_boundary'],
        'ujjain_mean_sunrise');
    final converted = tamil.gregorianToTamilDate(
      date,
      context,
      definitionId: definition,
    );
    expect(converted['tamil_date'], {
      'solar_year': 1947,
      'month': 6,
      'month_name': 'Purattasi',
      'day': 24,
    });
    expect(
      tamil.tamilToGregorianDate(
        const TamilSolarDate(solarYear: 1947, month: 6, day: 24),
        context,
        definitionId: definition,
      )['gregorian_date'],
      date,
    );
    expect(
        tamil.tamilMonthInfo(1947, 6, context,
            definitionId: definition)['days'],
        30);
    final year = tamil.tamilYearInfo(1947, context, definitionId: definition);
    expect(year['days'], 365);
    expect(year['months'], hasLength(12));
    expect(year['reference_station'], 'ujjain');
    expect((year['year_cycle'] as Map)['cycle_name'], 'Sarvajit');
    expect(
      tamil.tamilYearCycleInfo(1947, context, definitionId: definition)
          ['cycle_index'],
      21,
    );
    expect(
      tamil.addTamilDate(
        const TamilSolarDate(solarYear: 1947, month: 6, day: 24),
        'days',
        1,
        context,
        definitionId: definition,
      )['gregorian_date'],
      {'year': 1947, 'month': 10, 'day': 12},
    );
    final at =
        tamil.panchangamAt(-701391788, context, definitionId: definition);
    expect(at.limbs.tithi.name, 'Dwadashi');
    expect(at.referenceStation, 'ujjain');
    final day = tamil.panchangamDay(date, context, definitionId: definition);
    expect(day.sunriseMinuteOfDay, 387);
    expect(day.sunsetMinuteOfDay, isNull);
    expect(day.sunsetStatus,
        'unavailable_source_bhujaantara_interpolation_unresolved');
  });
  test('official annual holiday schedules', () {
    final tn = tamil.calendarOfficialHolidays('TN', 2025);
    expect(tn['source_sha256'], isNull);
    expect(tn['holidays'], hasLength(24));
    expect((tn['holidays'] as List)[1]['name'], 'Pongal');
    final sl = tamil.calendarOfficialHolidays('SL', 2027);
    expect(sl['source_sha256'],
        '9071010e6d253e72aee4cdd40057cebc2dfc98e45e713de65ceb9d209cb09eb9');
    expect(sl['holidays'], hasLength(25));
  });
  test('Tamil script display and explicit profile comparison', () {
    const thirukanitham = CalendarContext(
      region: 'TN',
      latitudeMicrodegrees: 13087840,
      longitudeMicrodegrees: 80278470,
      elevationMeters: 14,
      timeZone: 'Asia/Kolkata',
    );
    const vakya = VakyaCivilContext(timeZone: 'Asia/Kolkata');
    const date = {'year': 2026, 'month': 4, 'day': 14};
    expect(
      tamil.formatTamilDate(
        date,
        thirukanitham,
        script: 'tamil',
        digits: 'tamil',
      ),
      '\u0b9a\u0bc6\u0bb5\u0bcd\u0bb5\u0bbe\u0baf\u0bcd, \u0be7 \u0b9a\u0bbf\u0ba4\u0bcd\u0ba4\u0bbf\u0bb0\u0bc8 \u0be8\u0be6\u0be8\u0bec',
    );
    final display = tamil.calendarDisplayInfo(date, thirukanitham);
    expect((display['tamil_date'] as Map)['display_month_name'],
        '\u0b9a\u0bbf\u0ba4\u0bcd\u0ba4\u0bbf\u0bb0\u0bc8');
    expect((display['year_cycle'] as Map)['display_name'],
        '\u0baa\u0bb0\u0bbe\u0baa\u0bb5');
    final comparison = tamil.compareCalendarProfiles(
      date: date,
      thirukanithamContext: thirukanitham,
      vakyaContext: vakya,
    );
    expect(comparison['accuracy_assessment'], 'not_assessed');
    expect(comparison['differing_fields'], [
      'solar_date.solar_year',
      'solar_date.month',
      'solar_date.day',
    ]);
    final beforeThai1 = tamil.thiruvalluvarYearInfo(
      const {'year': 2025, 'month': 1, 'day': 13},
      thirukanitham,
    );
    final onThai1 = tamil.thiruvalluvarYearInfo(
      const {'year': 2025, 'month': 1, 'day': 14},
      thirukanitham,
    );
    final afterThai1 = tamil.thiruvalluvarYearInfo(
      const {'year': 2025, 'month': 1, 'day': 15},
      thirukanitham,
    );
    expect(beforeThai1['thiruvalluvar_year'], 2055);
    expect(onThai1['thiruvalluvar_year'], 2056);
    expect(afterThai1['thiruvalluvar_year'], 2056);
    final officialConflict = tamil.thiruvalluvarYearInfo(
      const {'year': 2026, 'month': 1, 'day': 14},
      thirukanitham,
    );
    expect(officialConflict['official_equivalence'], 'not_established');
    expect(officialConflict['thiruvalluvar_year'], 2057);
  });
  test('Thirukanitham primary lunar phases match USNO UTC minutes', () {
    final result = tamil.lunarPhaseEvents(
      startUnixSeconds: 1736121600,
      endUnixSeconds: 1738195200,
    );
    expect(result.events.map((event) => event.phase), [
      'first_quarter',
      'full_moon',
      'last_quarter',
      'new_moon',
    ]);
    expect(result.events.map((event) => event.utcMinute), [
      {'year': 2025, 'month': 1, 'day': 6, 'hour': 23, 'minute': 56},
      {'year': 2025, 'month': 1, 'day': 13, 'hour': 22, 'minute': 27},
      {'year': 2025, 'month': 1, 'day': 21, 'hour': 20, 'minute': 31},
      {'year': 2025, 'month': 1, 'day': 29, 'hour': 12, 'minute': 36},
    ]);
  });
}

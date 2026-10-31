import 'dart:convert';
import 'dart:io';
import 'package:tamil_toolkit/tamil_toolkit.dart';
import 'package:test/test.dart';

void main() {
  final root = Directory('../..').absolute.path;
  final extension = Platform.isWindows ? 'dll' : (Platform.isMacOS ? 'dylib' : 'so');
  final prefix = Platform.isWindows ? '' : 'lib';
  final tamil = TamilToolkit('$root/target/debug/${prefix}tamil_toolkit_ffi.$extension');
  final golden = '$root/tests/golden';
  final manifest = jsonDecode(File('$golden/manifest.json').readAsStringSync());
  if (manifest['version'] != 1) throw StateError('Unsupported golden manifest');
  final ids = <String>{};
  final files = <String>{};
  var count = 0;
  Map<String, dynamic>? wordCase;
  Map<String, dynamic>? keyCase;
  Map<String, dynamic>? numeralCase;
  Map<String, dynamic>? codecWord;
  Map<String, dynamic>? codecPreserved;
  Map<String, dynamic>? encoderWord;
  Map<String, dynamic>? encoderNfd;
  Map<String, dynamic>? encoderCollision;
  final moneyCases = <Map<String, dynamic>>[];
  for (final suite in manifest['suites']) {
    if (!files.add(suite['file'] as String)) throw StateError('Duplicate suite');
    if (!['active', 'planned'].contains(suite['status'])) throw StateError('Unknown status');
    final lines = File('$golden/${suite['file']}').readAsLinesSync();
    if (suite['status'] == 'active' && lines.isEmpty) throw StateError('Empty active suite');
    for (final line in lines) {
      final row = jsonDecode(line) as Map<String, dynamic>;
      if (row['id'] == 'collate_words_basic') wordCase = row;
      if (row['id'] == 'collate_key_001') keyCase = row;
      if (row['id'] == 'num_014') numeralCase = row;
      if (row['id'] == 'codec_word_000_tn_strict') codecWord = row;
      if (row['id'] == 'codec_joiner_boundary_0') codecPreserved = row;
      if (row['id'] == 'encode_word_000_tn') encoderWord = row;
      if (row['id'] == 'encode_collision_000_tn') encoderCollision = row;
      if (encoderNfd == null && (row['id'] as String).startsWith('encode_mapping_') && (row['id'] as String).endsWith('_tn_nfd')) encoderNfd = row;
      if (['format_currency', 'currency_to_words'].contains(row['op']) && row.containsKey('expected')) moneyCases.add(row);
      if (!ids.add(row['id'] as String)) throw StateError('Duplicate golden ID');
      if (suite['status'] == 'planned') continue;
      if (!(suite['operations'] as List).contains(row['op'])) throw StateError('Undeclared operation');
      if (row.containsKey('expected') == row.containsKey('expected_error')) throw StateError('Require exactly one outcome');
      if (row.containsKey('expected_error') && (row['expected_error'] is! String || (row['expected_error'] as String).isEmpty)) throw StateError('Invalid expected error');
      count++;
      test(row['id'] as String, () {
        if (row.containsKey('expected_error')) {
          expect(() => tamil.execute(row), throwsA(isA<ArgumentError>().having(
            (error) => error.message, 'message', row['expected_error'],
          )));
        } else {
          expect(tamil.execute(row), equals(row['expected']));
        }
      });
    }
  }
  final onDisk = Directory(golden).listSync().whereType<File>()
      .where((f) => f.path.endsWith('.jsonl')).map((f) => f.uri.pathSegments.last).toSet();
  if (files.length != onDisk.length || !files.containsAll(onDisk)) throw StateError('Unregistered suite');
  if (count == 0) throw StateError('No active golden vectors');
  test('invalid operation crosses C ABI as an error', () {
    expect(() => tamil.execute({'op': 'unknown', 'input': ''}), throwsArgumentError);
  });
  test('collation convenience APIs', () {
    final words = wordCase!;
    final key = keyCase!;
    expect(tamil.sortWords((words['input'] as List).cast<String>()), equals(words['expected']));
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
    expect(tamil.baminiToUnicode((word['input'] as Map)['text'] as String), word['expected']);
    expect(tamil.baminiToUnicode(input['text'] as String, errors: input['errors'] as String), preserved['expected']);
    expect(() => tamil.baminiToUnicode('*'), throwsArgumentError);
    expect(() => tamil.baminiToUnicode('f', errors: 'ignore'), throwsArgumentError);
  });
  test('encoder convenience API', () {
    final word = encoderWord!;
    final nfd = encoderNfd!;
    final collision = encoderCollision!;
    final text = (word['input'] as Map)['text'] as String;
    final encoded = tamil.unicodeToBamini(text);
    expect(encoded, word['expected']);
    expect(tamil.baminiToUnicode(encoded), tamil.normalizeNfc(text));
    expect(tamil.unicodeToBamini((nfd['input'] as Map)['text'] as String), nfd['expected']);
    expect(() => tamil.unicodeToBamini((collision['input'] as Map)['text'] as String), throwsA(isA<ArgumentError>().having(
      (error) => error.message, 'message', collision['expected_error'],
    )));
  });
}

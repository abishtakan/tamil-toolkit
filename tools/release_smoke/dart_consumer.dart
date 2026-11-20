// Private offline archive consumer; never changes Pub release scope.
import 'dart:convert';
import 'dart:io';
import 'package:tamil_toolkit/tamil_toolkit.dart';

bool equalJson(Object? actual, Object? expected) {
  if (actual is List && expected is List) {
    return actual.length == expected.length &&
        List.generate(
          actual.length,
          (i) => equalJson(actual[i], expected[i]),
        ).every((value) => value);
  }
  if (actual is Map && expected is Map) {
    return actual.length == expected.length &&
        expected.keys.every(
          (key) =>
              actual.containsKey(key) && equalJson(actual[key], expected[key]),
        );
  }
  return actual == expected;
}

void _verifyLexiconContracts(
  TamilToolkit toolkit,
  String nanri,
  String absent,
  String unavailablePack,
) {
  final matched = toolkit.lexiconLookup(nanri);
  if (matched['status'] != 'matched') {
    throw StateError('Expected matched lookup for $nanri');
  }
  final missing = toolkit.lexiconLookup(absent);
  if (missing['status'] != 'not_found' ||
      (missing['entries'] as List).isNotEmpty) {
    throw StateError('Expected empty not_found lookup for $absent');
  }
  void expectError(void Function() fn, String expectedMessage) {
    try {
      fn();
    } on ArgumentError catch (error) {
      if (error.message == expectedMessage) return;
      throw StateError('Unexpected error ${error.message} != $expectedMessage');
    }
    throw StateError('Expected ArgumentError($expectedMessage)');
  }

  expectError(
    () => toolkit.lexiconLookup(nanri, packs: [unavailablePack]),
    "lexicon: pack unavailable '$unavailablePack'",
  );
  expectError(
    () => toolkit.lexiconLookup(nanri, packs: []),
    'lexicon: packs must be a nonempty string array',
  );
  expectError(
    () => toolkit.lexiconLookup(nanri, packs: ['unknown']),
    "lexicon: unknown pack 'unknown'",
  );
  expectError(
    () => toolkit.lexiconLookup(nanri, region: 'LK-JAFFNA'),
    "lexicon: unknown region 'LK-JAFFNA'",
  );
  expectError(
    () => toolkit.lexiconLookup(
      '\u0b85\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0bc8',
      register: 'written',
    ),
    "lexicon: unknown register 'written'",
  );
}

void main(List<String> args) {
  if (args.length != 4)
    throw ArgumentError('library, fixtures, profile, manifest');
  final toolkit = TamilToolkit(args[0]);
  final packs = toolkit.lexiconPacks();
  const nanri = '\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf';
  const absent = '\u0b87\u0bb2\u0bcd\u0bb2\u0bbe\u0ba4\u0b9a\u0bca\u0bb2\u0bcd';
  if (args[2] == 'core') {
    if (packs.length != 1 ||
        packs.single['id'] != 'core' ||
        packs.single['manifest_sha256'] != args[3]) {
      throw StateError('Archive core profile/manifest mismatch');
    }
    _verifyLexiconContracts(toolkit, nanri, absent, 'regional');
  } else if (args[2] == 'full') {
    if (packs.length != 3 ||
        packs[0]['id'] != 'core' ||
        packs[1]['id'] != 'names_taxa' ||
        packs[2]['id'] != 'regional' ||
        packs.any((pack) => pack['available'] != true) ||
        packs.first['manifest_sha256'] != args[3]) {
      throw StateError('Archive full profile/manifest mismatch');
    }
    final rawManifests = Platform.environment['TAMIL_LEXICON_PACK_MANIFESTS'];
    if (rawManifests != null && rawManifests.isNotEmpty) {
      final envManifests = jsonDecode(rawManifests) as Map<String, dynamic>;
      for (final pack in packs) {
        final expected = envManifests[pack['id']] as Map<String, dynamic>;
        if (pack['manifest_sha256'] != expected['manifest_sha256'] ||
            pack['dataset_version'] != expected['dataset_version']) {
          throw StateError(
            'Archive full pack metadata mismatch for ${pack['id']}',
          );
        }
      }
    }
    _verifyLexiconContracts(toolkit, nanri, absent, 'terminology');
  } else if (args[2] == 'default') {
    if (packs.isNotEmpty) throw StateError('Default archive embeds dictionary');
    try {
      toolkit.lexiconLookup('');
      throw StateError('Default archive lookup must fail');
    } on ArgumentError catch (error) {
      if (error.message != "lexicon: pack unavailable 'core'") rethrow;
    }
  } else {
    throw ArgumentError('Unknown archive profile');
  }
  var count = 0;
  for (final line in File(args[1]).readAsLinesSync()) {
    final row = jsonDecode(line) as Map<String, dynamic>;
    final request = Map<String, dynamic>.from(row);
    if (['lexicon_lookup', 'lexicon_packs'].contains(row['op'])) {
      for (final key in [
        'id',
        'expected',
        'expected_error',
        'dialect',
        'tags',
        'source',
        'unicode_exceptions',
      ]) {
        request.remove(key);
      }
    }
    Object? result;
    ArgumentError? failure;
    try {
      result = toolkit.execute(request);
    } on ArgumentError catch (error) {
      failure = error;
    }
    if (row.containsKey('expected_error')) {
      if (failure == null || failure.message != row['expected_error']) {
        throw StateError('${row['id']}: incorrect archive error: $failure');
      }
    } else if (failure != null || !equalJson(result, row['expected'])) {
      throw StateError('${row['id']}: archive response differs');
    }
    count++;
  }
  if (count == 0) throw StateError('No archive fixtures executed');
  print('Private Dart archive (${args[2]}): $count golden rows passed.');
}

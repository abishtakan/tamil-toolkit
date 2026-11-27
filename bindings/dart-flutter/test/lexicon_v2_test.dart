import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:tamil_toolkit/tamil_toolkit.dart';
import 'package:test/test.dart';

void main() {
  final root = Directory('../..').absolute.path;
  final extension =
      Platform.isWindows ? 'dll' : (Platform.isMacOS ? 'dylib' : 'so');
  final prefix = Platform.isWindows ? '' : 'lib';
  final tamil =
      TamilToolkit('$root/target/debug/${prefix}tamil_toolkit_ffi.$extension');

  test('Dart FFI passes all lexicon_v02_runtime.jsonl golden vectors', () {
    tamil.lexiconUnloadPack();
    final lines = File('$root/tests/golden/lexicon_v02_runtime.jsonl')
        .readAsLinesSync()
        .where((l) => l.trim().isNotEmpty);
    for (final line in lines) {
      final row = jsonDecode(line) as Map<String, dynamic>;
      final req = <String, Object?>{
        'op': row['op'],
        'input': row['input'],
      };
      if (row.containsKey('expected_error')) {
        expect(
          () => tamil.execute(req),
          throwsA(isA<ArgumentError>().having(
            (e) => e.message,
            'message',
            row['expected_error'],
          )),
          reason: row['id'] as String,
        );
      } else {
        expect(tamil.execute(req), equals(row['expected']),
            reason: row['id'] as String);
      }
    }
  });

  test('Dart FFI loads TMLPACK2 packs via bytes and runs query/search/relations', () {
    final coreFile = File('$root/dist/lexicon-packs/open/core.tlpack');
    final relFile = File('$root/dist/lexicon-packs/local/local_relations.tlpack');
    final dialectFile = File('$root/dist/lexicon-packs/local/local_dialect.tlpack');
    if (!coreFile.existsSync() || !relFile.existsSync() || !dialectFile.existsSync()) {
      return;
    }

    tamil.lexiconUnloadPack();
    try {
      final sCore = tamil.lexiconLoadPackBytes(coreFile.readAsBytesSync());
      final sRel = tamil.lexiconLoadPackBytes(relFile.readAsBytesSync());
      final sDial = tamil.lexiconLoadPackBytes(dialectFile.readAsBytesSync());

      expect(sCore['pack_id'], 'core');
      expect(sCore['category'], 'dictionary');
      expect(sCore['pack_tier'], 'verified_open');
      expect(sRel['category'], 'relations');
      expect(sRel['relation_count'], 30858);
      expect(sDial['category'], 'regional');
      expect(sDial['pack_tier'], 'local_historical');

      final stats = tamil.lexiconStats();
      expect(stats['pack_count'], 3);
      expect(stats['total_relations'], 30858);

      // Mayangoli-folded open-only query: தமில் -> தமிழ்
      final folded = tamil.lexiconQuery(
        '\u0ba4\u0bae\u0bbf\u0bb2\u0bcd',
        tier: 'open',
        folded: true,
      );
      expect(folded['status'], 'matched');
      expect(
        (folded['entries'] as List).every((e) => e['pack_tier'] == 'verified_open'),
        isTrue,
      );

      // Category filtering on query, search, and relations
      final qDict = tamil.lexiconQuery(
        '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd',
        category: 'dictionary',
      );
      expect(qDict['status'], 'matched');
      expect(qDict['searched_packs'], ['core']);

      // Prefix search & cursor pagination (afterKey)
      final search = tamil.lexiconSearch('\u0ba4\u0bae\u0bbf\u0bb4\u0bcd', limit: 5);
      final hits = search['hits'] as List;
      expect(hits, isNotEmpty);
      expect(hits.first['headword'], '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd');

      final page1 = tamil.lexiconSearch('\u0ba4', limit: 2);
      expect((page1['hits'] as List).length, 2);
      expect(page1['has_more'], isTrue);
      final cursor = page1['next_cursor'] as String;
      expect(cursor, isNotEmpty);
      final page2 = tamil.lexiconSearch(
        '\u0ba4',
        limit: 2,
        afterKey: cursor,
      );
      final page2Hits = (page2['hits'] as List).cast<Map<String, dynamic>>();
      expect(page2Hits, isNotEmpty);
      expect(
        page2Hits.every((h) => (h['matched_key'] as String).compareTo(cursor) > 0),
        isTrue,
      );

      final searchDict = tamil.lexiconSearch(
        '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd',
        limit: 5,
        category: 'dictionary',
      );
      expect(searchDict['searched_packs'], ['core']);
      expect((searchDict['hits'] as List), isNotEmpty);

      // Fuzzy search & longest-prefix stemmer probes
      final fuzzy = tamil.lexiconFuzzySearch(
        '\u0ba4\u0bae\u0bbf\u0bb2\u0bcd',
        maxDistance: 1,
        limit: 5,
      );
      expect(fuzzy['query'], '\u0ba4\u0bae\u0bbf\u0bb2\u0bcd');
      expect(fuzzy['max_distance'], 1);
      final fuzzyHits = (fuzzy['hits'] as List).cast<Map<String, dynamic>>();
      expect(
        fuzzyHits.any((h) => h['headword'] == '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd' && h['distance'] == 1),
        isTrue,
      );

      final stems = tamil.lexiconLongestPrefix(
        '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd\u0ba8\u0bbe\u0b9f\u0bc1',
      );
      expect(stems['query'], '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd\u0ba8\u0bbe\u0b9f\u0bc1');
      expect((stems['prefixes'] as List), contains('\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'));

      // Relations lookup (exact, category-filtered, and folded)
      final rels = tamil.lexiconRelations('\u0b85\u0ba9\u0bcd\u0baa\u0bc1');
      expect(rels['status'], 'matched');
      expect((rels['relations'] as List).length, greaterThanOrEqualTo(4));

      final relsCat = tamil.lexiconRelations(
        '\u0b85\u0ba9\u0bcd\u0baa\u0bc1',
        category: 'relations',
      );
      expect(relsCat['status'], 'matched');
      expect(relsCat['searched_packs'], ['local_relations']);

      final relsFolded = tamil.lexiconRelations(
        '\u0b85\u0ba3\u0bcd\u0baa\u0bc1',
        folded: true,
      );
      expect(relsFolded['status'], 'matched');
      expect((relsFolded['relations'] as List).length, greaterThanOrEqualTo(4));

      // Unified word definitions
      final defTa = tamil.lexiconDefine('\u0ba4\u0bae\u0bbf\u0bb4\u0bcd');
      expect(defTa['status'], 'matched');
      expect(defTa['headword'], '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd');
      expect(defTa['has_verified_open'], isTrue);
      expect(defTa['categories'] as List, contains('dictionary'));
      expect((defTa['meanings_en'] as List), isNotEmpty);
      expect((defTa['sources'] as List), isNotEmpty);

      final defAnbu = tamil.lexiconDefine('\u0b85\u0ba9\u0bcd\u0baa\u0bc1');
      expect(defAnbu['status'], 'matched');
      expect(defAnbu['headword'], '\u0b85\u0ba9\u0bcd\u0baa\u0bc1');
      expect(defAnbu['has_verified_open'], isTrue);
      expect((defAnbu['meanings_en'] as List), isNotEmpty);
      final relGroup = defAnbu['relations'] as Map<String, dynamic>;
      final hasRel = (relGroup['synonyms'] as List).isNotEmpty ||
          (relGroup['antonyms'] as List).isNotEmpty ||
          (relGroup['related'] as List).isNotEmpty ||
          (relGroup['hypernyms'] as List).isNotEmpty;
      expect(hasRel, isTrue);
    } finally {
      tamil.lexiconUnloadPack();
    }
  });

  test('Dart FFI lexiconInit loads open-lite profile and exposes pack categories', () {
    final packsDir = Directory('$root/dist/lexicon-packs');
    final manifest = File('${packsDir.path}/MANIFEST.json');
    if (!manifest.existsSync()) {
      return;
    }

    tamil.lexiconUnloadPack();
    try {
      final lite = tamil.lexiconInit(profile: 'open-lite', path: packsDir.path);
      expect(lite['profile'], 'open-lite');
      expect(lite['pack_count'], 3);
      final loaded = (lite['loaded'] as List).cast<Map<String, dynamic>>();
      expect(loaded.length, 3);
      final byId = {for (final p in loaded) p['pack_id'] as String: p['category'] as String};
      expect(byId, {
        'core': 'dictionary',
        'names_taxa': 'names_taxa',
        'regional': 'regional',
      });
    } finally {
      tamil.lexiconUnloadPack();
    }
  });

  test('TamilLexiconPackManager computes SHA-256 and filters manifest packs', () {
    expect(
      TamilLexiconPackManager.sha256Hex(utf8.encode('')),
      'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    );
    expect(
      TamilLexiconPackManager.sha256Hex(utf8.encode('abc')),
      'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
    );

    final manifest = <String, dynamic>{
      'schema_version': 2,
      'pack_count': 4,
      'packs': [
        {
          'file': 'open/core.tlpack',
          'summary': {'pack_id': 'core', 'pack_tier': 'verified_open', 'checksum_sha256': 'a'}
        },
        {
          'file': 'open/names_taxa.tlpack',
          'summary': {'pack_id': 'names_taxa', 'pack_tier': 'verified_open', 'checksum_sha256': 'b'}
        },
        {
          'file': 'open/ta_wiktionary.tlpack',
          'summary': {'pack_id': 'ta_wiktionary', 'pack_tier': 'verified_open', 'checksum_sha256': 'c'}
        },
        {
          'file': 'local/local_core.tlpack',
          'summary': {'pack_id': 'local_core', 'pack_tier': 'local_historical', 'checksum_sha256': 'd'}
        },
      ],
    };

    expect(
      TamilLexiconPackManager.filterManifestPacks(manifest, profile: 'open-lite')
          .map((e) => (e['summary'] as Map)['pack_id'])
          .toList(),
      ['core', 'names_taxa'],
    );
    expect(
      TamilLexiconPackManager.filterManifestPacks(manifest, profile: 'open')
          .map((e) => (e['summary'] as Map)['pack_id'])
          .toList(),
      ['core', 'names_taxa', 'ta_wiktionary'],
    );
    expect(
      TamilLexiconPackManager.filterManifestPacks(manifest, profile: 'local')
          .map((e) => (e['summary'] as Map)['pack_id'])
          .toList(),
      ['local_core'],
    );
    expect(
      TamilLexiconPackManager.filterManifestPacks(manifest, profile: 'full').length,
      4,
    );
  });

  test('TamilLexiconPackManager downloads, verifies, and skips packs offline via HttpServer', () async {
    final tempRoot = Directory.systemTemp.createTempSync('tamil_dart_pack_mgr_');
    final serveDir = Directory('${tempRoot.path}/serve')..createSync(recursive: true);
    final dlDir = Directory('${tempRoot.path}/dl');

    final coreBytes = Uint8List.fromList(utf8.encode('MOCK-DART-CORE'));
    final localBytes = Uint8List.fromList(utf8.encode('MOCK-DART-LOCAL'));
    File('${serveDir.path}/open/core.tlpack')
      ..parent.createSync(recursive: true)
      ..writeAsBytesSync(coreBytes);
    File('${serveDir.path}/local/local_core.tlpack')
      ..parent.createSync(recursive: true)
      ..writeAsBytesSync(localBytes);

    final manifest = <String, dynamic>{
      'schema_version': 2,
      'pack_count': 2,
      'packs': [
        {
          'file': 'open/core.tlpack',
          'summary': {
            'pack_id': 'core',
            'pack_tier': 'verified_open',
            'checksum_sha256': TamilLexiconPackManager.sha256Hex(coreBytes),
          },
        },
        {
          'file': 'local/local_core.tlpack',
          'summary': {
            'pack_id': 'local_core',
            'pack_tier': 'local_historical',
            'checksum_sha256': TamilLexiconPackManager.sha256Hex(localBytes),
          },
        },
      ],
    };
    File('${serveDir.path}/MANIFEST.json').writeAsStringSync(jsonEncode(manifest));

    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    server.listen((request) async {
      final rel = request.uri.path.replaceFirst(RegExp(r'^/+'), '');
      final file = File('${serveDir.path}/$rel');
      if (!file.existsSync()) {
        request.response.statusCode = HttpStatus.notFound;
        await request.response.close();
        return;
      }
      request.response.statusCode = HttpStatus.ok;
      request.response.add(file.readAsBytesSync());
      await request.response.close();
    });

    try {
      final manager = TamilLexiconPackManager(tamil);
      final manifestUrl = 'http://127.0.0.1:${server.port}/MANIFEST.json';

      final res1 = await manager.downloadProfile(
        profile: 'open',
        directory: dlDir.path,
        manifestUrl: manifestUrl,
      );
      expect(res1.downloaded, ['core']);
      expect(res1.skipped, isEmpty);
      expect(File('${dlDir.path}/open/core.tlpack').existsSync(), isTrue);
      expect(File('${dlDir.path}/local/local_core.tlpack').existsSync(), isFalse);
      expect(File('${dlDir.path}/MANIFEST.json').existsSync(), isTrue);

      final res2 = await manager.downloadProfile(
        profile: 'open',
        directory: dlDir.path,
        manifestUrl: manifestUrl,
      );
      expect(res2.downloaded, isEmpty);
      expect(res2.skipped, ['core']);

      final res3 = await manager.downloadProfile(
        profile: 'open',
        directory: dlDir.path,
        manifestUrl: manifestUrl,
        force: true,
      );
      expect(res3.downloaded, ['core']);
      expect(res3.skipped, isEmpty);

      // Bad SHA-256 fails cleanly
      final badManifest = jsonDecode(jsonEncode(manifest)) as Map<String, dynamic>;
      ((badManifest['packs'] as List)[0]['summary'] as Map)['checksum_sha256'] = '0' * 64;
      File('${serveDir.path}/BAD_MANIFEST.json').writeAsStringSync(jsonEncode(badManifest));
      await expectLater(
        manager.downloadProfile(
          packs: ['core'],
          directory: '${tempRoot.path}/dl_bad',
          manifestUrl: 'http://127.0.0.1:${server.port}/BAD_MANIFEST.json',
        ),
        throwsStateError,
      );
      expect(File('${tempRoot.path}/dl_bad/open/core.tlpack').existsSync(), isFalse);
    } finally {
      await server.close(force: true);
      if (tempRoot.existsSync()) {
        tempRoot.deleteSync(recursive: true);
      }
    }
  });

  test('LexiconStoreStats model parses facet counts and lexiconSearchEnglish works when rebuilt', () {
    final parsed = LexiconStoreStats.fromJson({
      'pack_count': 1,
      'total_entries': 10,
      'total_senses': 12,
      'total_relations': 0,
      'total_bytes': 2048,
      'packs': [
        {
          'pack_id': 'core',
          'category': 'dictionary',
          'index_format_version': 2,
          'schema_version': 2,
          'pack_tier': 'verified_open',
          'rights_status': 'CC-BY-SA-4.0',
          'license': 'CC-BY-SA-4.0',
          'dataset_version': '0.2.0',
          'description': 'Core',
          'entry_count': 10,
          'sense_count': 12,
          'relation_count': 0,
          'distinct_headwords': 10,
          'byte_len': 2048,
          'checksum_sha256': 'abc',
          'has_folded_index': true,
          'has_relations': false,
          'has_english_index': true,
          'source_ids': ['wikt'],
          'attribution_notice': 'CC',
          'domains': ['Nature'],
          'regions': ['TN'],
          'registers': ['standard'],
        }
      ],
      'category_counts': {'dictionary': 10},
      'pos_counts': {'noun': 7},
      'domain_counts': {'Nature': 3},
      'region_counts': {'TN': 2},
      'register_counts': {'standard': 8},
      'has_english_index': true,
    });
    expect(parsed.hasEnglishIndex, isTrue);
    expect(parsed.categoryCounts, {'dictionary': 10});
    expect(parsed.posCounts, {'noun': 7});
    expect(parsed.domainCounts, {'Nature': 3});
    expect(parsed.regionCounts, {'TN': 2});
    expect(parsed.registerCounts, {'standard': 8});
    expect(parsed.packs.single.hasEnglishIndex, isTrue);

    final coreFile = File('$root/dist/lexicon-packs/open/core.tlpack');
    if (!coreFile.existsSync()) {
      return;
    }
    tamil.lexiconUnloadPack();
    try {
      tamil.lexiconLoadPackBytes(coreFile.readAsBytesSync());
      final stats = tamil.lexiconStatsModel();
      if (!stats.hasEnglishIndex) {
        return;
      }
      expect(stats.categoryCounts['dictionary'], greaterThan(0));
      final en = tamil.lexiconSearchEnglish('water', limit: 10);
      expect((en['hits'] as List), isNotEmpty);
    } on ArgumentError catch (err) {
      final msg = err.message.toString();
      if (msg.contains('unsupported operation: lexicon_search_english') ||
          msg.contains('unsupported flags')) {
        return;
      }
      rethrow;
    } finally {
      tamil.lexiconUnloadPack();
    }
  });
}

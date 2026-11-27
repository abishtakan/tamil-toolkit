import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';

import '../tamil_toolkit.dart';

class LexiconDownloadResult {
  final String directory;
  final List<String> downloaded;
  final List<String> skipped;
  final String manifestUrl;

  const LexiconDownloadResult({
    required this.directory,
    required this.downloaded,
    required this.skipped,
    required this.manifestUrl,
  });
}

class TamilLexiconPackManager {
  static const String defaultManifestUrl =
      'https://github.com/abishtakan/tamil-toolkit/releases/latest/download/MANIFEST.json';

  static const Set<String> _openLitePackIds = {
    'core',
    'names_taxa',
    'regional',
  };

  final TamilToolkit? toolkit;

  const TamilLexiconPackManager([this.toolkit]);

  static String resolveDefaultDirectory() {
    final envDir = Platform.environment['TAMIL_LEXICON_DIR']?.trim();
    if (envDir != null && envDir.isNotEmpty) {
      return envDir;
    }
    final home = Platform.environment['HOME'] ??
        Platform.environment['USERPROFILE'] ??
        '.';
    return '$home${Platform.pathSeparator}.tamil-toolkit${Platform.pathSeparator}lexicon-packs';
  }

  static String resolveDefaultManifestUrl() {
    final envUrl = Platform.environment['TAMIL_LEXICON_MANIFEST_URL']?.trim();
    if (envUrl != null && envUrl.isNotEmpty) {
      return envUrl;
    }
    return defaultManifestUrl;
  }

  static List<Map<String, dynamic>> filterManifestPacks(
    Map<String, dynamic> manifest, {
    String profile = 'open',
    List<String>? packs,
  }) {
    final rawPacks = manifest['packs'];
    if (rawPacks is! List) {
      throw const FormatException("lexicon: manifest missing 'packs' list");
    }
    final entries =
        rawPacks.map((e) => Map<String, dynamic>.from(e as Map)).toList();

    if (packs != null) {
      final byId = <String, Map<String, dynamic>>{};
      for (final entry in entries) {
        final summary = entry['summary'];
        if (summary is Map && summary['pack_id'] is String) {
          byId[summary['pack_id'] as String] = entry;
        }
      }
      final selected = <Map<String, dynamic>>[];
      final seen = <String>{};
      for (final packId in packs) {
        if (!seen.add(packId)) continue;
        final found = byId[packId];
        if (found == null) {
          throw ArgumentError("lexicon: unknown pack '$packId'");
        }
        selected.add(found);
      }
      return selected;
    }

    final norm = profile.trim().toLowerCase().replaceAll('_', '-');
    if (norm == 'open-lite' || norm == 'lite') {
      return entries
          .where((e) => _openLitePackIds.contains((e['summary'] as Map)['pack_id']))
          .toList();
    }
    if (norm == 'open' || norm == 'verified' || norm == 'verified-open') {
      return entries
          .where((e) => (e['summary'] as Map)['pack_tier'] == 'verified_open')
          .toList();
    }
    if (norm == 'local' || norm == 'local-historical') {
      return entries
          .where((e) => (e['summary'] as Map)['pack_tier'] == 'local_historical')
          .toList();
    }
    if (norm == 'full' || norm == 'all') {
      return entries;
    }
    throw ArgumentError("lexicon: unknown profile '$profile'");
  }

  Future<LexiconDownloadResult> downloadProfile({
    String profile = 'open',
    List<String>? packs,
    String? directory,
    String? manifestUrl,
    bool force = false,
  }) async {
    final destDir = Directory(directory ?? resolveDefaultDirectory());
    final resolvedManifestUrl = manifestUrl ?? resolveDefaultManifestUrl();
    final manifestUri = Uri.parse(resolvedManifestUrl);

    final client = HttpClient();
    try {
      final manifestBytes = await _fetchBytes(client, manifestUri);
      final manifest =
          jsonDecode(utf8.decode(manifestBytes)) as Map<String, dynamic>;
      final selected =
          filterManifestPacks(manifest, profile: profile, packs: packs);

      await destDir.create(recursive: true);

      final downloaded = <String>[];
      final skipped = <String>[];

      for (final entry in selected) {
        final summary = Map<String, dynamic>.from(entry['summary'] as Map);
        final packId = summary['pack_id'] as String;
        final expectedSha =
            (summary['checksum_sha256'] as String).toLowerCase();
        if (expectedSha.isEmpty) {
          throw StateError(
              "lexicon: manifest entry '$packId' missing checksum_sha256");
        }

        final relPath = _sanitizeRelativePath(entry['file'] as String);
        final targetFile = File(_joinPath(destDir.path, relPath));
        await targetFile.parent.create(recursive: true);

        if (!force && await targetFile.exists()) {
          final existingBytes = await targetFile.readAsBytes();
          if (sha256Hex(existingBytes) == expectedSha) {
            skipped.add(packId);
            continue;
          }
        }

        final explicitUrl = entry['url'] as String?;
        final packUri = explicitUrl != null && explicitUrl.isNotEmpty
            ? Uri.parse(explicitUrl)
            : manifestUri.resolve(relPath);

        final tmpFile = File('${targetFile.path}.tmp');
        try {
          final bytes = await _fetchBytes(client, packUri);
          final actualSha = sha256Hex(bytes);
          if (actualSha != expectedSha) {
            throw StateError(
                "lexicon: SHA-256 mismatch for '$packId': expected $expectedSha, got $actualSha");
          }
          await tmpFile.writeAsBytes(bytes, flush: true);
          if (await targetFile.exists()) {
            await targetFile.delete();
          }
          await tmpFile.rename(targetFile.path);
          downloaded.add(packId);
        } catch (_) {
          if (await tmpFile.exists()) {
            await tmpFile.delete();
          }
          rethrow;
        }
      }

      final manifestTmp =
          File('${destDir.path}${Platform.pathSeparator}MANIFEST.json.tmp');
      final manifestTarget =
          File('${destDir.path}${Platform.pathSeparator}MANIFEST.json');
      try {
        await manifestTmp.writeAsBytes(manifestBytes, flush: true);
        if (await manifestTarget.exists()) {
          await manifestTarget.delete();
        }
        await manifestTmp.rename(manifestTarget.path);
      } catch (_) {
        if (await manifestTmp.exists()) {
          await manifestTmp.delete();
        }
        rethrow;
      }

      return LexiconDownloadResult(
        directory: destDir.path,
        downloaded: downloaded,
        skipped: skipped,
        manifestUrl: resolvedManifestUrl,
      );
    } finally {
      client.close(force: true);
    }
  }

  Map<String, dynamic> loadFromDirectory(
    String dir, {
    String profile = 'full',
    bool replace = true,
  }) {
    final tk = _requireToolkit();
    return tk.lexiconInit(profile: profile, path: dir, replace: replace);
  }

  Map<String, dynamic> loadPackBytes(String packId, Uint8List bytes) {
    final tk = _requireToolkit();
    final summary = tk.lexiconLoadPackBytes(bytes);
    if (packId.isNotEmpty && summary['pack_id'] != packId) {
      throw StateError(
          "lexicon: loaded pack_id '${summary['pack_id']}' did not match expected '$packId'");
    }
    return summary;
  }

  TamilToolkit _requireToolkit() {
    final tk = toolkit;
    if (tk == null) {
      throw StateError(
          'TamilLexiconPackManager requires a TamilToolkit instance to mount packs');
    }
    return tk;
  }

  static Future<Uint8List> _fetchBytes(HttpClient client, Uri uri) async {
    if (uri.scheme == 'file') {
      return await File.fromUri(uri).readAsBytes();
    }
    if (uri.scheme != 'http' && uri.scheme != 'https') {
      throw UnsupportedError("lexicon: unsupported URL scheme '${uri.scheme}'");
    }
    final request = await client.getUrl(uri);
    request.headers.set(HttpHeaders.userAgentHeader, 'tamil-toolkit-dart');
    final response = await request.close();
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw HttpException(
        'lexicon: HTTP ${response.statusCode} fetching $uri',
        uri: uri,
      );
    }
    final builder = BytesBuilder(copy: false);
    await for (final chunk in response) {
      builder.add(chunk);
    }
    return builder.takeBytes();
  }

  static String _sanitizeRelativePath(String rawPath) {
    final normalized = rawPath.replaceAll('\\', '/').replaceFirst(RegExp(r'^/+'), '');
    if (normalized.isEmpty) {
      throw ArgumentError("lexicon: empty manifest pack path '$rawPath'");
    }
    final segments = normalized.split('/');
    if (segments.any((s) => s.isEmpty || s == '.' || s == '..')) {
      throw ArgumentError("lexicon: invalid manifest pack file path '$rawPath'");
    }
    return segments.join('/');
  }

  static String _joinPath(String baseDir, String posixRelPath) {
    final parts = posixRelPath.split('/');
    return [baseDir, ...parts].join(Platform.pathSeparator);
  }

  static String sha256Hex(List<int> data) => _Sha256.digestHex(data);
}

class _Sha256 {
  static final Uint32List _iv = _computeRootWords(8, 2);
  static final Uint32List _rc = _computeRootWords(64, 3);

  static Uint32List _computeRootWords(int count, int rootOrder) {
    final out = Uint32List(count);
    var n = 2;
    var found = 0;
    while (found < count) {
      if (_isPrime(n)) {
        final root = rootOrder == 2
            ? math.sqrt(n)
            : math.pow(n.toDouble(), 1.0 / 3.0).toDouble();
        final frac = root - root.floorToDouble();
        out[found++] = (frac * 4294967296.0).floor() & 0xffffffff;
      }
      n++;
    }
    return out;
  }

  static bool _isPrime(int n) {
    if (n < 2) return false;
    for (var d = 2; d * d <= n; d++) {
      if (n % d == 0) return false;
    }
    return true;
  }

  static int _rotr(int x, int n) =>
      ((x >>> n) | (x << (32 - n))) & 0xffffffff;

  static String digestHex(List<int> input) {
    final len = input.length;
    final bitLen = len * 8;
    final padLen = ((len + 9 + 63) ~/ 64) * 64;
    final padded = Uint8List(padLen);
    padded.setRange(0, len, input);
    padded[len] = 0x80;
    final bd = ByteData.sublistView(padded);
    bd.setUint32(padLen - 8, (bitLen ~/ 0x100000000) & 0xffffffff, Endian.big);
    bd.setUint32(padLen - 4, bitLen & 0xffffffff, Endian.big);

    final h = Uint32List.fromList(_iv);
    final w = Uint32List(64);

    for (var offset = 0; offset < padLen; offset += 64) {
      for (var i = 0; i < 16; i++) {
        w[i] = bd.getUint32(offset + i * 4, Endian.big);
      }
      for (var i = 16; i < 64; i++) {
        final s0 = _rotr(w[i - 15], 7) ^ _rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3);
        final s1 = _rotr(w[i - 2], 17) ^ _rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10);
        w[i] = (w[i - 16] + s0 + w[i - 7] + s1) & 0xffffffff;
      }

      var a = h[0];
      var b = h[1];
      var c = h[2];
      var d = h[3];
      var e = h[4];
      var f = h[5];
      var g = h[6];
      var hh = h[7];

      for (var i = 0; i < 64; i++) {
        final s1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25);
        final ch = (e & f) ^ ((~e) & g);
        final temp1 = (hh + s1 + ch + _rc[i] + w[i]) & 0xffffffff;
        final s0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22);
        final maj = (a & b) ^ (a & c) ^ (b & c);
        final temp2 = (s0 + maj) & 0xffffffff;

        hh = g;
        g = f;
        f = e;
        e = (d + temp1) & 0xffffffff;
        d = c;
        c = b;
        b = a;
        a = (temp1 + temp2) & 0xffffffff;
      }

      h[0] = (h[0] + a) & 0xffffffff;
      h[1] = (h[1] + b) & 0xffffffff;
      h[2] = (h[2] + c) & 0xffffffff;
      h[3] = (h[3] + d) & 0xffffffff;
      h[4] = (h[4] + e) & 0xffffffff;
      h[5] = (h[5] + f) & 0xffffffff;
      h[6] = (h[6] + g) & 0xffffffff;
      h[7] = (h[7] + hh) & 0xffffffff;
    }

    final sb = StringBuffer();
    for (final word in h) {
      sb.write(word.toRadixString(16).padLeft(8, '0'));
    }
    return sb.toString();
  }
}

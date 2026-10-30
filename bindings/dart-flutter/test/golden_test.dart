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
  for (final suite in manifest['suites']) {
    if (!files.add(suite['file'] as String)) throw StateError('Duplicate suite');
    if (!['active', 'planned'].contains(suite['status'])) throw StateError('Unknown status');
    final lines = File('$golden/${suite['file']}').readAsLinesSync();
    if (suite['status'] == 'active' && lines.isEmpty) throw StateError('Empty active suite');
    for (final line in lines) {
      final row = jsonDecode(line) as Map<String, dynamic>;
      if (!ids.add(row['id'] as String)) throw StateError('Duplicate golden ID');
      if (suite['status'] == 'planned') continue;
      if (!(suite['operations'] as List).contains(row['op'])) throw StateError('Undeclared operation');
      count++;
      test(row['id'] as String, () => expect(tamil.execute(row), equals(row['expected'])));
    }
  }
  final onDisk = Directory(golden).listSync().whereType<File>()
      .where((f) => f.path.endsWith('.jsonl')).map((f) => f.uri.pathSegments.last).toSet();
  if (files.length != onDisk.length || !files.containsAll(onDisk)) throw StateError('Unregistered suite');
  if (count == 0) throw StateError('No active golden vectors');
  test('invalid operation crosses C ABI as an error', () {
    expect(() => tamil.execute({'op': 'unknown', 'input': ''}), throwsArgumentError);
  });
}

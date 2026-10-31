import 'dart:convert';
import 'dart:io';

import 'package:tamil_toolkit/tamil_toolkit.dart';

Future<void> main(List<String> args) async {
  if (args.length != 1) {
    stderr.writeln('Usage: manual_request.dart <path-to-tamil-toolkit-library>');
    exitCode = 64;
    return;
  }

  try {
    final request = jsonDecode(await stdin.transform(utf8.decoder).join())
        as Map<String, Object?>;
    final result = TamilToolkit(args.single).execute(request);
    stdout.writeln(jsonEncode({'ok': result}));
  } catch (error) {
    stdout.writeln(jsonEncode({'error': error.toString()}));
  }
}

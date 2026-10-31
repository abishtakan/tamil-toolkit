import 'dart:convert';
import 'dart:ffi';
import 'package:ffi/ffi.dart';

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
        _free = library.lookupFunction<_NativeFree,
            void Function(Pointer<Utf8>)>('tamil_toolkit_free');

  Object? execute(Map<String, Object?> request) {
    final input = jsonEncode(request).toNativeUtf8();
    try {
      final output = _call(input);
      if (output == nullptr) throw StateError('Rust returned a null response');
      try {
        final result = jsonDecode(output.toDartString()) as Map<String, dynamic>;
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
    'op': 'compose_uyirmei', 'input': {'mei': mei, 'uyir': uyir},
  }) as String;
  int compare(String left, String right) =>
      execute({'op': 'compare', 'input': {'left': left, 'right': right}}) as int;
  List<String> sortWords(List<String> words) =>
      (execute({'op': 'sort_words', 'input': words}) as List).cast<String>();
  List<int> sortKey(String text) =>
      (execute({'op': 'sort_key', 'input': text}) as List).cast<int>();
  List<int> searchKey(String text) =>
      (execute({'op': 'search_key', 'input': text}) as List).cast<int>();
  String toWords(int value, {String locale = 'TN'}) => execute({
    'op': 'to_words', 'input': {'value': value, 'locale': locale},
  }) as String;
  String formatCurrency(int amountMinor, String currency, {String locale = 'TN'}) => execute({
    'op': 'format_currency', 'input': {'amount_minor': amountMinor, 'currency': currency, 'locale': locale},
  }) as String;
  String currencyToWords(int amountMinor, String currency, {String locale = 'TN'}) => execute({
    'op': 'currency_to_words', 'input': {'amount_minor': amountMinor, 'currency': currency, 'locale': locale},
  }) as String;
  String baminiToUnicode(String text, {String errors = 'strict'}) => execute({
    'op': 'bamini_to_unicode', 'input': {'text': text, 'errors': errors},
  }) as String;
  String unicodeToBamini(String text) => execute({
    'op': 'unicode_to_bamini', 'input': {'text': text},
  }) as String;
}

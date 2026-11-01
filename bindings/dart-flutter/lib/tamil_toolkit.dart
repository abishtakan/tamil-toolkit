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
  String anjalBytesToUnicode(List<int> bytes) => execute({
    'op': 'anjal_bytes_to_unicode', 'input': {'bytes': bytes},
  }) as String;
  List<int> unicodeToAnjalBytes(String text) =>
      (execute({'op': 'unicode_to_anjal_bytes', 'input': {'text': text}}) as List).cast<int>();
  String tamBytesToUnicode(List<int> bytes) => execute({
    'op': 'tam_bytes_to_unicode', 'input': {'bytes': bytes},
  }) as String;
  List<int> unicodeToTamBytes(String text) =>
      (execute({'op': 'unicode_to_tam_bytes', 'input': {'text': text}}) as List).cast<int>();
  String tabBytesToUnicode(List<int> bytes) => execute({
    'op': 'tab_bytes_to_unicode', 'input': {'bytes': bytes},
  }) as String;
  List<int> unicodeToTabBytes(String text) =>
      (execute({'op': 'unicode_to_tab_bytes', 'input': {'text': text}}) as List).cast<int>();
  String tsciiBytesToUnicode(List<int> bytes) => execute({
    'op': 'tscii_bytes_to_unicode', 'input': {'bytes': bytes},
  }) as String;
  List<int> unicodeToTsciiBytes(String text) =>
      (execute({'op': 'unicode_to_tscii_bytes', 'input': {'text': text}}) as List).cast<int>();
  String ltTmCodesToUnicode(List<int> codes, {String errors = 'strict'}) => execute({
    'op': 'lt_tm_codes_to_unicode', 'input': {'codes': codes, 'errors': errors},
  }) as String;
  String ltTmTextToUnicode(String text, {String errors = 'strict'}) => execute({
    'op': 'lt_tm_text_to_unicode', 'input': {'text': text, 'errors': errors},
  }) as String;
  List<int> unicodeToLtTmCodes(String text) =>
      (execute({'op': 'unicode_to_lt_tm_codes', 'input': {'text': text}}) as List).cast<int>();
  String unicodeToLtTmText(String text) => execute({
    'op': 'unicode_to_lt_tm_text', 'input': {'text': text},
  }) as String;
  String vanavilCodesToUnicode(List<int> codes, {String errors = 'strict'}) => execute({
    'op': 'vanavil_codes_to_unicode', 'input': {'codes': codes, 'errors': errors},
  }) as String;
  String vanavilTextToUnicode(String text, {String errors = 'strict'}) => execute({
    'op': 'vanavil_text_to_unicode', 'input': {'text': text, 'errors': errors},
  }) as String;
  List<int> unicodeToVanavilCodes(String text) =>
      (execute({'op': 'unicode_to_vanavil_codes', 'input': {'text': text}}) as List).cast<int>();
  String unicodeToVanavilText(String text) => execute({
    'op': 'unicode_to_vanavil_text', 'input': {'text': text},
  }) as String;
  String formatFraction(int numerator, int denominator, {String digits = 'latin'}) => execute({
    'op': 'format_fraction', 'input': {'numerator': numerator, 'denominator': denominator, 'digits': digits},
  }) as String;
  String fractionToWords(int numerator, int denominator, {String locale = 'TN'}) => execute({
    'op': 'fraction_to_words', 'input': {'numerator': numerator, 'denominator': denominator, 'locale': locale},
  }) as String;
  String fractionSymbol(int numerator, int denominator) => execute({
    'op': 'fraction_symbol', 'input': {'numerator': numerator, 'denominator': denominator},
  }) as String;
  String formatDate(int year, int month, int day, {String locale = 'TN', String style = 'long', String digits = 'latin'}) => execute({
    'op': 'format_date', 'input': {'year': year, 'month': month, 'day': day, 'locale': locale, 'style': style, 'digits': digits},
  }) as String;
}

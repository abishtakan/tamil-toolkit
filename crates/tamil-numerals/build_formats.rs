use serde::Deserialize;
use std::{collections::BTreeSet, env, fs, path::PathBuf};
use unicode_normalization::is_nfc;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Formats {
    profile: String,
    division: String,
    decimal_point_word: String,
    latin_digits: String,
    tamil_digits: String,
    months: Vec<String>,
    abbreviated_months: Vec<String>,
    weekdays: Vec<String>,
    common_fractions: Vec<Named>,
    symbols: Vec<Symbol>,
    date_styles: Vec<Style>,
}
#[derive(Deserialize)]
struct Named {
    numerator: u64,
    denominator: u64,
    words: String,
}
#[derive(Deserialize)]
struct Symbol {
    numerator: u64,
    denominator: u64,
    symbol: String,
}
#[derive(Deserialize)]
struct Style {
    name: String,
    pattern: String,
}
fn literal(text: &str) -> String {
    format!(
        "\"{}\"",
        text.chars()
            .flat_map(char::escape_unicode)
            .collect::<String>()
    )
}
fn clean(text: &str) -> bool {
    !text.is_empty()
        && is_nfc(text)
        && text
            .chars()
            .all(|c| !matches!(u32::from(c), 0x200c | 0x200d))
}
fn gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        (a, b) = (b, a % b);
    }
    a
}
fn pattern(text: &str) -> String {
    assert!(text.is_ascii(), "unsupported date pattern syntax");
    let mut index = 0;
    let mut result = Vec::new();
    let bytes = text.as_bytes();
    while index < bytes.len() {
        let start = index;
        let byte = bytes[index];
        if byte.is_ascii_alphabetic() {
            while index < bytes.len() && bytes[index] == byte {
                index += 1;
            }
            let op = match &text[start..index] {
                "d" => "Day",
                "M" => "MonthNumber",
                "MMM" => "MonthAbbreviated",
                "MMMM" => "MonthWide",
                "EEEE" => "Weekday",
                "y" => "Year",
                "yy" => "YearTwo",
                _ => panic!("unsupported date pattern token"),
            };
            result.push(format!("DateOp::{op}"));
        } else {
            while index < bytes.len() && !bytes[index].is_ascii_alphabetic() {
                assert!(b" ,/".contains(&bytes[index]), "unsupported date literal");
                index += 1;
            }
            result.push(format!("DateOp::Literal({})", literal(&text[start..index])));
        }
    }
    format!("&[{}]", result.join(","))
}
pub fn compile() {
    let path = "lexicon/numerals-formats.toml";
    println!("cargo:rerun-if-changed={path}");
    let data: Formats = toml::from_str(&fs::read_to_string(path).expect("read numeral formats"))
        .expect("valid numeral formats");
    assert_eq!(data.profile, "numerals-formats-v1");
    assert_eq!(data.latin_digits, "0123456789");
    assert!(clean(&data.division));
    assert!(clean(&data.decimal_point_word));
    let digits: Vec<_> = data.tamil_digits.chars().collect();
    assert_eq!(digits.len(), 10);
    assert_eq!(digits.iter().collect::<BTreeSet<_>>().len(), 10);
    assert!(clean(&data.tamil_digits));
    let mut code = format!(
        "pub const FORMAT_PROFILE:&str={};\npub const DIVISION:&str={};\npub const DECIMAL_POINT_WORD:&str={};\npub const TAMIL_DIGITS:&[char]=&[{}];\n",
        literal(&data.profile),
        literal(&data.division),
        literal(&data.decimal_point_word),
        digits
            .iter()
            .map(|c| format!("'{}'", c.escape_unicode()))
            .collect::<Vec<_>>()
            .join(",")
    );
    for (name, values, length) in [
        ("MONTHS", &data.months, 12),
        ("ABBREVIATED_MONTHS", &data.abbreviated_months, 12),
        ("WEEKDAYS", &data.weekdays, 7),
    ] {
        assert_eq!(values.len(), length);
        assert!(values.iter().all(|value| clean(value)));
        code.push_str(&format!(
            "pub const {name}:&[&str]=&[{}];\n",
            values
                .iter()
                .map(|value| literal(value))
                .collect::<Vec<_>>()
                .join(",")
        ));
    }
    let mut seen = BTreeSet::new();
    assert_eq!(data.common_fractions.len(), 3);
    let named = data
        .common_fractions
        .iter()
        .map(|value| {
            assert!(
                value.numerator > 0
                    && value.numerator < value.denominator
                    && gcd(value.numerator, value.denominator) == 1
                    && clean(&value.words)
            );
            assert!(
                seen.insert((value.numerator, value.denominator)),
                "duplicate named fraction"
            );
            format!(
                "({}, {}, {})",
                value.numerator,
                value.denominator,
                literal(&value.words)
            )
        })
        .collect::<Vec<_>>()
        .join(",");
    code.push_str(&format!(
        "pub const NAMED_FRACTIONS:&[(u64,u64,&str)]=&[{named}];\n"
    ));
    let mut values = BTreeSet::new();
    let mut chars = BTreeSet::new();
    assert_eq!(data.symbols.len(), 18);
    let symbols = data
        .symbols
        .iter()
        .map(|value| {
            assert!(
                value.numerator > 0
                    && value.numerator < value.denominator
                    && gcd(value.numerator, value.denominator) == 1
                    && clean(&value.symbol)
            );
            assert_eq!(value.symbol.chars().count(), 1);
            assert!(values.insert((value.numerator, value.denominator)));
            assert!(chars.insert(value.symbol.as_str()));
            format!(
                "({}, {}, '{}')",
                value.numerator,
                value.denominator,
                value
                    .symbol
                    .chars()
                    .next()
                    .expect("symbol")
                    .escape_unicode()
            )
        })
        .collect::<Vec<_>>()
        .join(",");
    assert!(seen.is_subset(&values));
    code.push_str(&format!(
        "pub const FRACTION_SYMBOLS:&[(u64,u64,char)]=&[{symbols}];\n"
    ));
    assert_eq!(data.date_styles.len(), 4);
    let mut styles = BTreeSet::new();
    let mut patterns = Vec::new();
    for name in ["short", "medium", "long", "full"] {
        let style = data
            .date_styles
            .iter()
            .find(|value| value.name == name)
            .expect("required date style");
        assert!(styles.insert(&style.name));
        patterns.push(pattern(&style.pattern));
    }
    code.push_str(&format!(
        "pub const DATE_PATTERNS:&[&[DateOp]]=&[{}];\n",
        patterns.join(",")
    ));
    fs::write(
        PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR")).join("numeral_format_tables.rs"),
        code,
    )
    .expect("write numeral format tables");
}

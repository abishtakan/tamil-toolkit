use serde::Deserialize;
use std::{collections::BTreeMap, env, fs, path::PathBuf};
use unicode_normalization::is_nfc;
mod build_formats;

#[derive(Deserialize)]
struct Profile {
    profile: String,
    max_integer: i64,
    max_minor: i64,
    primary_group: usize,
    secondary_group: usize,
    negative: String,
    sl_lakh_from: String,
    sl_lakh_to: String,
    currencies: Vec<Currency>,
    rulesets: Vec<Ruleset>,
}

#[derive(Deserialize)]
struct Currency {
    code: String,
    major: String,
    minor: String,
    factor: u64,
}
#[derive(Deserialize)]
struct Ruleset {
    name: String,
    rules: Vec<Rule>,
}
#[derive(Deserialize)]
struct Rule {
    base: u64,
    divisor: u64,
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

// Only compile the CLDR syntax required by the bounded profile.
// Reject unsupported RBNF constructs rather than treating them as literal text.
fn compile(pattern: &str, current: usize, names: &BTreeMap<&str, usize>) -> String {
    let mut rest = pattern;
    let mut ops = Vec::new();
    while !rest.is_empty() {
        let end = rest
            .find(['[', ']', '|', '<', '>', '='])
            .unwrap_or(rest.len());
        if end > 0 {
            let text = &rest[..end];
            assert!(
                text.chars()
                    .all(|c| c == ' ' || ('\u{0b80}'..='\u{0bff}').contains(&c)),
                "unsupported RBNF literal"
            );
            ops.push(format!("Op::Literal({})", literal(text)));
            rest = &rest[end..];
            continue;
        }
        let delimiter = rest.as_bytes()[0] as char;
        if delimiter == '[' {
            let end = rest.find(']').expect("unclosed optional rule");
            let inner = &rest[1..end];
            assert!(
                !inner.contains('['),
                "nested optional rules are unsupported"
            );
            let (nonzero, zero) = inner.split_once('|').unwrap_or((inner, ""));
            ops.push(format!(
                "Op::Optional({}, {})",
                compile(nonzero, current, names),
                compile(zero, current, names)
            ));
            rest = &rest[end + 1..];
        } else {
            let operand = match delimiter {
                '<' => "Quotient",
                '>' => "Remainder",
                '=' => "Same",
                _ => panic!("unexpected RBNF delimiter"),
            };
            let end = rest[1..].find(delimiter).expect("unclosed substitution") + 1;
            let name = &rest[1..end];
            let target = if name.is_empty() {
                assert_ne!(
                    delimiter, '=',
                    "same-value substitution requires a named set"
                );
                current
            } else {
                *names.get(name).expect("unknown named RBNF ruleset")
            };
            ops.push(format!("Op::Substitute(Operand::{operand}, {target})"));
            rest = &rest[end + 1..];
        }
    }
    format!("&[{}]", ops.join(","))
}

fn main() {
    build_formats::compile();
    let path = "../../lexicon/numerals.toml";
    println!("cargo:rerun-if-changed={path}");
    let profile: Profile = toml::from_str(&fs::read_to_string(path).expect("read numerals.toml"))
        .expect("valid numerals.toml");
    assert_eq!(profile.profile, "numerals-v1");
    assert_eq!(profile.max_integer, 999_999_999);
    assert_eq!(profile.max_minor, profile.max_integer * 100 + 99);
    assert_eq!((profile.primary_group, profile.secondary_group), (3, 2));
    for text in [
        &profile.negative,
        &profile.sl_lakh_from,
        &profile.sl_lakh_to,
    ] {
        assert!(!text.is_empty() && is_nfc(text));
    }
    assert_eq!(profile.currencies.len(), 2);
    let currencies = profile
        .currencies
        .iter()
        .zip(["INR", "LKR"])
        .map(|(data, code)| {
            assert_eq!(data.code, code);
            assert_eq!(data.factor, 100);
            assert!(!data.major.is_empty() && is_nfc(&data.major));
            assert!(!data.minor.is_empty() && is_nfc(&data.minor));
            format!(
                "CurrencyUnits {{code: {}, major: {}, minor: {}, factor: {}}}",
                literal(code),
                literal(&data.major),
                literal(&data.minor),
                data.factor
            )
        })
        .collect::<Vec<_>>()
        .join(",");
    let names: BTreeMap<_, _> = profile
        .rulesets
        .iter()
        .enumerate()
        .map(|(index, set)| (set.name.as_str(), index))
        .collect();
    assert_eq!(names.len(), profile.rulesets.len(), "duplicate ruleset");
    assert_eq!(names.len(), 6);
    let numbering = names["%spellout-numbering"];
    let cardinal = names["%spellout-cardinal"];
    let mut output = format!(
        "pub const PROFILE: &str = {};\npub const MAX_INTEGER: i64 = {};\npub const MAX_MINOR: i64 = {};\npub const PRIMARY_GROUP: usize = {};\npub const SECONDARY_GROUP: usize = {};\npub const NEGATIVE: &str = {};\npub const CURRENCIES: &[CurrencyUnits] = &[{currencies}];\npub const NUMBERING: usize = {numbering};\npub const CARDINAL: usize = {cardinal};\n",
        literal(&profile.profile), profile.max_integer, profile.max_minor, profile.primary_group, profile.secondary_group, literal(&profile.negative),
    );
    for (locale, regional) in [("TN", false), ("SL", true)] {
        let mut sets = Vec::new();
        for (index, set) in profile.rulesets.iter().enumerate() {
            assert!(!set.rules.is_empty());
            let mut previous = None;
            let mut rules = Vec::new();
            for rule in &set.rules {
                assert!(
                    previous.is_none_or(|base| rule.base > base),
                    "unordered/duplicate base"
                );
                previous = Some(rule.base);
                assert!(rule.base <= profile.max_integer as u64);
                assert_eq!(
                    rule.divisor,
                    if rule.base == 0 {
                        1
                    } else {
                        10_u64.pow(rule.base.ilog10())
                    }
                );
                assert!(is_nfc(&rule.pattern), "non-NFC rule data");
                let pattern = if regional {
                    rule.pattern
                        .replace(&profile.sl_lakh_from, &profile.sl_lakh_to)
                } else {
                    rule.pattern.clone()
                };
                rules.push(format!(
                    "Rule {{base: {}, divisor: {}, ops: {}}}",
                    rule.base,
                    rule.divisor,
                    compile(&pattern, index, &names)
                ));
            }
            sets.push(format!("&[{}]", rules.join(",")));
        }
        output.push_str(&format!(
            "pub const {locale}: &[&[Rule]] = &[{}];\n",
            sets.join(",")
        ));
    }
    fs::write(
        PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR")).join("numeral_tables.rs"),
        output,
    )
    .expect("write numeral tables");
}

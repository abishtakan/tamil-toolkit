use serde::Deserialize;
use std::{
    collections::{BTreeMap, BTreeSet},
    env, fs,
    path::PathBuf,
};
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
#[derive(Deserialize, Clone)]
struct Ruleset {
    name: String,
    rules: Vec<Rule>,
}
#[derive(Deserialize, Clone)]
struct Rule {
    base: u64,
    divisor: u64,
    pattern: String,
}
#[derive(Deserialize)]
struct RbnfProfile {
    profile: String,
    max_integer: u64,
    negative: Option<String>,
    rulesets: Vec<Ruleset>,
}
#[derive(Deserialize)]
struct SymbolsProfile {
    profile: String,
    source_version: String,
    symbols: Vec<Symbol>,
}
#[derive(Deserialize)]
struct Symbol {
    codepoint: u32,
    character: String,
    name: String,
    kind: String,
    rational: Option<Rational>,
    canonical_alternative: Option<u32>,
}
#[derive(Deserialize)]
struct Rational {
    numerator: i64,
    denominator: u64,
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

fn compile_rulesets(
    data: &RbnfProfile,
    maximum: u64,
    main_name: &str,
    sl_stems: Option<(&str, &str)>,
) -> (String, usize) {
    let names: BTreeMap<_, _> = data
        .rulesets
        .iter()
        .enumerate()
        .map(|(index, set)| (set.name.as_str(), index))
        .collect();
    assert_eq!(names.len(), data.rulesets.len(), "duplicate ruleset");
    let mut sets = Vec::new();
    for (index, set) in data.rulesets.iter().enumerate() {
        assert!(!set.rules.is_empty());
        let mut previous = None;
        let mut rules = Vec::new();
        for rule in &set.rules {
            assert!(
                previous.is_none_or(|base| rule.base > base),
                "unordered/duplicate base"
            );
            previous = Some(rule.base);
            assert!(rule.base <= maximum);
            assert!(
                rule.divisor > 0
                    && if rule.base == 0 {
                        rule.divisor == 1
                    } else {
                        rule.divisor <= rule.base
                            && 10_u64.pow(rule.divisor.ilog10()) == rule.divisor
                    },
                "RBNF divisor must be a bounded power of ten"
            );
            assert!(is_nfc(&rule.pattern), "non-NFC rule data");
            let pattern = sl_stems.map_or_else(
                || rule.pattern.clone(),
                |(from, to)| rule.pattern.replace(from, to),
            );
            rules.push(format!(
                "Rule {{base: {}, divisor: {}, ops: {}}}",
                rule.base,
                rule.divisor,
                compile(&pattern, index, &names)
            ));
        }
        sets.push(format!("&[{}]", rules.join(",")));
    }
    (format!("&[{}]", sets.join(",")), names[main_name])
}

fn compile_extra_data(output: &mut String) {
    for (path, expected, constant, main_name, negative) in [
        (
            "lexicon/numerals-ordinals.toml",
            "numerals-ordinals-v1",
            "ORDINAL",
            "%spellout-ordinal",
            false,
        ),
        (
            "lexicon/numerals-traditional.toml",
            "numerals-traditional-v1",
            "TRADITIONAL",
            "%tamil",
            true,
        ),
    ] {
        println!("cargo:rerun-if-changed={path}");
        let mut profile: RbnfProfile =
            toml::from_str(&fs::read_to_string(path).expect("read extra RBNF data"))
                .expect("valid extra RBNF data");
        assert_eq!(profile.profile, expected);
        let mut sl_stems = None;
        if !negative {
            let base: Profile = toml::from_str(
                &fs::read_to_string("lexicon/numerals.toml").expect("read cardinal rules"),
            )
            .expect("valid cardinal rules");
            profile.rulesets.extend(base.rulesets.clone());
            sl_stems = Some((base.sl_lakh_from, base.sl_lakh_to));
        }
        let rulesets_max = if negative {
            profile.max_integer
        } else {
            999_999_999
        };
        if let Some((from, to)) = sl_stems {
            let (tn, main) = compile_rulesets(&profile, rulesets_max, main_name, None);
            let (sl, sl_main) =
                compile_rulesets(&profile, rulesets_max, main_name, Some((&from, &to)));
            assert_eq!(main, sl_main);
            output.push_str(&format!("pub const {constant}_TN:&[&[Rule]]={tn};\npub const {constant}_SL:&[&[Rule]]={sl};\npub const {constant}_MAIN:usize={main};\npub const {constant}_MAX:u64={};\n", profile.max_integer));
        } else {
            let (sets, main) = compile_rulesets(&profile, rulesets_max, main_name, None);
            output.push_str(&format!("pub const {constant}: &[&[Rule]]={sets};\npub const {constant}_MAIN:usize={main};\npub const {constant}_MAX:u64={};\n", profile.max_integer));
        }
        if negative {
            let sign = profile.negative.expect("traditional negative sign");
            assert_eq!(sign, "−");
            output.push_str(&format!(
                "pub const TRADITIONAL_NEGATIVE:&str={};\n",
                literal(&sign)
            ));
        }
    }
    let path = "lexicon/numerals-symbols.toml";
    println!("cargo:rerun-if-changed={path}");
    let profile: SymbolsProfile =
        toml::from_str(&fs::read_to_string(path).expect("read numeric symbols"))
            .expect("valid numeric symbols");
    assert_eq!(profile.profile, "numerals-symbols-v1");
    let mut codepoints = BTreeSet::new();
    let symbols = profile.symbols.iter().map(|symbol| {
        assert!(codepoints.insert(symbol.codepoint), "duplicate symbol codepoint");
        assert_eq!(symbol.character.chars().count(), 1);
        assert_eq!(symbol.character.chars().next().unwrap() as u32, symbol.codepoint);
        assert!(!symbol.name.is_empty() && is_nfc(&symbol.name));
        assert!(!symbol.kind.is_empty() && is_nfc(&symbol.kind));
        let rational = if let Some(value) = &symbol.rational {
            assert_ne!(value.denominator, 0);
            format!("Some(({}, {}))", value.numerator, value.denominator)
        } else { "None".to_owned() };
        let alternative = symbol.canonical_alternative.map_or("None".to_owned(), |value| format!("Some({value})"));
        format!("SymbolInfo {{codepoint:{},character:{},name:{},kind:{},rational:{},canonical_alternative:{},source_version:{}}}",
            symbol.codepoint, literal(&symbol.character), literal(&symbol.name), literal(&symbol.kind), rational,
            alternative, literal(&profile.source_version))
    }).collect::<Vec<_>>().join(",");
    assert!(profile.symbols.len() >= 50);
    output.push_str(&format!("pub const SYMBOLS:&[SymbolInfo]=&[{symbols}];\n"));
}

fn main() {
    build_formats::compile();
    let path = "lexicon/numerals.toml";
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
        literal(&profile.profile),
        profile.max_integer,
        profile.max_minor,
        profile.primary_group,
        profile.secondary_group,
        literal(&profile.negative),
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
    compile_extra_data(&mut output);
    fs::write(
        PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR")).join("numeral_tables.rs"),
        output,
    )
    .expect("write numeral tables");
}


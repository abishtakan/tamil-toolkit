#![forbid(unsafe_code)]

use tamil_norm::{repair_tamil_text, RepairOptions};

#[test]
fn test_repair_duplicate_pulli() {
    let input = "\u{0B95}\u{0BCD}\u{0BCD}"; // க்்
    let res = repair_tamil_text(input, &RepairOptions::default());
    assert_eq!(res.text, "\u{0B95}\u{0BCD}"); // க்
    assert_eq!(res.diagnostics.duplicate_pulli_count, 1);
    assert_eq!(res.diagnostics.total_repairs, 1);

    // Triple pulli
    let input3 = "\u{0BA4}\u{0BCD}\u{0BCD}\u{0BCD}";
    let res3 = repair_tamil_text(input3, &RepairOptions::default());
    assert_eq!(res3.text, "\u{0BA4}\u{0BCD}");
    assert_eq!(res3.diagnostics.duplicate_pulli_count, 2);
    assert_eq!(res3.diagnostics.total_repairs, 2);
}

#[test]
fn test_repair_visual_kombu() {
    // ெ + க -> கெ
    let input_e = "\u{0BC6}\u{0B95}";
    let res_e = repair_tamil_text(input_e, &RepairOptions::default());
    assert_eq!(res_e.text, "\u{0B95}\u{0BC6}");
    assert_eq!(res_e.diagnostics.visual_kombu_count, 1);

    // ே + க -> கே
    let input_ee = "\u{0BC7}\u{0B95}";
    let res_ee = repair_tamil_text(input_ee, &RepairOptions::default());
    assert_eq!(res_ee.text, "\u{0B95}\u{0BC7}");
    assert_eq!(res_ee.diagnostics.visual_kombu_count, 1);

    // ை + க -> கை
    let input_ai = "\u{0BC8}\u{0B95}";
    let res_ai = repair_tamil_text(input_ai, &RepairOptions::default());
    assert_eq!(res_ai.text, "\u{0B95}\u{0BC8}");
    assert_eq!(res_ai.diagnostics.visual_kombu_count, 1);

    // ெ + க + ா -> கொ
    let input_o = "\u{0BC6}\u{0B95}\u{0BBE}";
    let res_o = repair_tamil_text(input_o, &RepairOptions::default());
    assert_eq!(res_o.text, "\u{0B95}\u{0BCA}");
    assert_eq!(res_o.diagnostics.visual_kombu_count, 1);

    // ே + க + ா -> கோ
    let input_oo = "\u{0BC7}\u{0B95}\u{0BBE}";
    let res_oo = repair_tamil_text(input_oo, &RepairOptions::default());
    assert_eq!(res_oo.text, "\u{0B95}\u{0BCB}");
    assert_eq!(res_oo.diagnostics.visual_kombu_count, 1);

    // ெ + க + ௗ -> கௌ
    let input_au = "\u{0BC6}\u{0B95}\u{0BD7}";
    let res_au = repair_tamil_text(input_au, &RepairOptions::default());
    assert_eq!(res_au.text, "\u{0B95}\u{0BCC}");
    assert_eq!(res_au.diagnostics.visual_kombu_count, 1);
}

#[test]
fn test_repair_soft_hyphens_and_controls() {
    let input = "த\u{00AD}மிழ்\u{0007}";
    let res = repair_tamil_text(input, &RepairOptions::default());
    assert_eq!(res.text, "தமிழ்");
    assert_eq!(res.diagnostics.stripped_control_count, 2);
    assert_eq!(res.diagnostics.total_repairs, 2);
}

#[test]
fn test_repair_joiner_preservation_and_stripping() {
    let zwj = char::from_u32(0x200D).unwrap();
    let input = format!("\u{0B95}{zwj}\u{0BCD}");
    // Default: preserves joiners
    let res_default = repair_tamil_text(&input, &RepairOptions::default());
    assert_eq!(res_default.text, input);
    assert_eq!(res_default.diagnostics.stripped_control_count, 0);

    // Opt-in: strip joiners
    let opt = RepairOptions {
        strip_joiners: true,
        ..Default::default()
    };
    let res_strip = repair_tamil_text(&input, &opt);
    assert_eq!(res_strip.text, "\u{0B95}\u{0BCD}");
    assert_eq!(res_strip.diagnostics.stripped_control_count, 1);
}

#[test]
fn test_repair_clean_text_is_idempotent() {
    let input = "தமிழ் வாழ்க!";
    let res = repair_tamil_text(input, &RepairOptions::default());
    assert_eq!(res.text, input);
    assert_eq!(res.diagnostics.total_repairs, 0);

    let res2 = repair_tamil_text(&res.text, &RepairOptions::default());
    assert_eq!(res2.text, res.text);
    assert_eq!(res2.diagnostics.total_repairs, 0);
}

use std::io::{Cursor, Read, Write};
use tamil_hyphen::docx::{is_prose_xml_part, process_docx_bytes, process_xml_text};
use tamil_hyphen::types::DocxStats;
use zip::write::SimpleFileOptions;
use zip::{ZipArchive, ZipWriter};

const SOFT_HYPHEN: char = '\u{00AD}';

#[test]
fn test_is_prose_xml_part() {
    assert!(is_prose_xml_part("word/document.xml"));
    assert!(is_prose_xml_part("word/header1.xml"));
    assert!(is_prose_xml_part("word/header2.xml"));
    assert!(is_prose_xml_part("word/footer1.xml"));
    assert!(is_prose_xml_part("word/footnotes.xml"));
    assert!(is_prose_xml_part("word/endnotes.xml"));
    assert!(is_prose_xml_part("word/comments.xml"));

    // Case insensitivity
    assert!(is_prose_xml_part("Word/Document.xml"));

    // Non-prose parts must return false
    assert!(!is_prose_xml_part("[Content_Types].xml"));
    assert!(!is_prose_xml_part("_rels/.rels"));
    assert!(!is_prose_xml_part("word/styles.xml"));
    assert!(!is_prose_xml_part("word/settings.xml"));
    assert!(!is_prose_xml_part("word/media/image1.png"));
}

#[test]
fn test_process_xml_text_formatting_and_preservation() {
    let input_xml = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:pPr><w:jc w:val="both"/></w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
        <w:t>தமிழ்நாடு</w:t>
      </w:r>
      <w:r>
        <w:t xml:space="preserve"> மற்றும் </w:t>
      </w:r>
      <w:r>
        <w:rPr><w:i/></w:rPr>
        <w:t>பல்கலைக்கழகம்</w:t>
      </w:r>
      <w:r>
        <w:t> (Tamil Nadu &amp; University 2026)</w:t>
      </w:r>
    </w:p>
  </w:body>
</w:document>"#;

    let mut stats = DocxStats::default();
    let result = process_xml_text(input_xml, None, &mut stats).expect("processing should succeed");

    // Paragraph count
    assert_eq!(stats.paragraphs_processed, 1);
    // Tamil words evaluated: தமிழ்நாடு, மற்றும், பல்கலைக்கழகம் = 3
    assert_eq!(stats.words_hyphenated, 3);
    // Soft hyphens should be inserted on >=6-letter word பல்கலைக்கழகம்
    assert!(stats.soft_hyphens_inserted > 0);

    // Verify preservation of styles and attributes
    assert!(result.contains(r#"<w:pPr><w:jc w:val="both"/></w:pPr>"#));
    assert!(result.contains(r#"<w:rPr><w:b/><w:sz w:val="24"/></w:rPr>"#));
    assert!(result.contains(r#"xml:space="preserve""#));
    assert!(result.contains(r#"<w:rPr><w:i/></w:rPr>"#));

    // Verify non-Tamil text and XML entities are preserved verbatim
    assert!(result.contains("(Tamil Nadu &amp; University 2026)"));

    // Short words (<6 letters) remain unbroken, while பல்கலைக்கழகம் breaks cleanly at Asai boundary
    assert!(result.contains("<w:t>தமிழ்நாடு</w:t>"));
    assert!(result.contains(&format!("பல்கலைக்{}கழகம்", SOFT_HYPHEN)));
}

#[test]
fn test_process_xml_text_idempotency() {
    let input_xml =
        r#"<w:p><w:r><w:t>தமிழ்நாடு மற்றும் பல்கலைக்கழகம்</w:t></w:r></w:p>"#;

    let mut stats1 = DocxStats::default();
    let pass1 = process_xml_text(input_xml, None, &mut stats1).unwrap();
    let initial_hyphens = stats1.soft_hyphens_inserted;
    assert!(initial_hyphens > 0);

    // Second pass on already-hyphenated text
    let mut stats2 = DocxStats::default();
    let pass2 = process_xml_text(&pass1, None, &mut stats2).unwrap();

    // No new soft-hyphens should be added
    assert_eq!(stats2.soft_hyphens_inserted, 0);
    // The XML text must be byte-for-byte identical
    assert_eq!(pass1, pass2);
}

#[test]
fn test_process_xml_text_self_closing_and_empty() {
    let input_xml =
        r#"<w:p><w:r><w:t/><w:t></w:t><w:t>பல்கலைக்கழகம்</w:t></w:r></w:p>"#;
    let mut stats = DocxStats::default();
    let result = process_xml_text(input_xml, None, &mut stats).unwrap();

    assert!(result.contains("<w:t/>"));
    assert!(result.contains("<w:t></w:t>"));
    assert!(result.contains(&format!("பல்கலைக்{}கழகம்", SOFT_HYPHEN)));
}

/// Helper to create a minimal valid in-memory DOCX ZIP archive
fn create_test_docx_archive() -> Vec<u8> {
    let buf = Vec::new();
    let cursor = Cursor::new(buf);
    let mut writer = ZipWriter::new(cursor);
    let options = SimpleFileOptions::default();

    // 1. [Content_Types].xml
    writer.start_file("[Content_Types].xml", options).unwrap();
    let ct = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml" ContentType="application/xml"/>
</Types>"#;
    writer.write_all(ct.as_bytes()).unwrap();

    // 2. word/document.xml
    writer.start_file("word/document.xml", options).unwrap();
    let doc = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r><w:t>வணக்கம் தமிழ்நாடு</w:t></w:r>
    </w:p>
    <w:tbl>
      <w:tr>
        <w:tc>
          <w:p><w:r><w:t>பல்கலைக்கழகம்</w:t></w:r></w:p>
        </w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>"#;
    writer.write_all(doc.as_bytes()).unwrap();

    // 3. word/header1.xml
    writer.start_file("word/header1.xml", options).unwrap();
    let hdr = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p><w:r><w:t>தொழில்நுட்பம் ஒன்று</w:t></w:r></w:p>
</w:hdr>"#;
    writer.write_all(hdr.as_bytes()).unwrap();

    // 4. word/footnotes.xml
    writer.start_file("word/footnotes.xml", options).unwrap();
    let fn_xml = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:footnote w:id="1">
    <w:p><w:r><w:t>அடிக்குறிப்பு விளக்கம்</w:t></w:r></w:p>
  </w:footnote>
</w:footnotes>"#;
    writer.write_all(fn_xml.as_bytes()).unwrap();

    // 5. Binary passthrough: word/media/image1.png
    writer
        .start_file("word/media/image1.png", options)
        .unwrap();
    writer
        .write_all(&[0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
        .unwrap();

    let finished = writer.finish().unwrap();
    finished.into_inner()
}

#[test]
fn test_process_docx_bytes_roundtrip_and_stats() {
    let original_docx_bytes = create_test_docx_archive();
    let (hyphenated_bytes, stats) =
        process_docx_bytes(&original_docx_bytes, None).expect("DOCX processing should succeed");

    // Check stats
    // Parts updated: document.xml, header1.xml, footnotes.xml = 3
    assert_eq!(stats.parts_updated, 3);
    assert!(stats.paragraphs_processed >= 3);
    assert!(stats.words_hyphenated >= 5);
    assert!(stats.soft_hyphens_inserted > 0);

    // Verify output archive structure
    let cursor = Cursor::new(&hyphenated_bytes);
    let mut reader = ZipArchive::new(cursor).expect("output must be valid ZIP");

    // Verify non-prose part passthrough
    {
        let mut img_file = reader.by_name("word/media/image1.png").unwrap();
        let mut img_data = Vec::new();
        img_file.read_to_end(&mut img_data).unwrap();
        assert_eq!(
            img_data,
            vec![0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]
        );
    }

    // Verify document.xml content: short words unbroken, பல்கலைக்கழகம் -> பல்கலைக்-கழகம்
    let doc_xml = {
        let mut doc_file = reader.by_name("word/document.xml").unwrap();
        let mut s = String::new();
        doc_file.read_to_string(&mut s).unwrap();
        s
    };
    assert!(doc_xml.contains("வணக்கம் தமிழ்நாடு"));
    assert!(doc_xml.contains(&format!("பல்கலைக்{}கழகம்", SOFT_HYPHEN)));

    // Verify header1.xml content: தொழில்நுட்பம் -> தொழில்-நுட்பம்
    {
        let mut hdr_file = reader.by_name("word/header1.xml").unwrap();
        let mut hdr_xml = String::new();
        hdr_file.read_to_string(&mut hdr_xml).unwrap();
        assert!(hdr_xml.contains(&format!("தொழில்{}நுட்பம்", SOFT_HYPHEN)));
    }

    // Verify footnotes.xml content
    {
        let mut fn_file = reader.by_name("word/footnotes.xml").unwrap();
        let mut fn_xml = String::new();
        fn_file.read_to_string(&mut fn_xml).unwrap();
        let expected_fn =
            tamil_hyphen::hyphenate_text("அடிக்குறிப்பு விளக்கம்", None).unwrap();
        assert!(fn_xml.contains(&expected_fn));
    }

    // Idempotency: Process the hyphenated bytes again
    let (rehyphenated_bytes, stats2) =
        process_docx_bytes(&hyphenated_bytes, None).expect("second pass must succeed");
    assert_eq!(stats2.soft_hyphens_inserted, 0);
    assert_eq!(stats2.parts_updated, 0);

    // Byte-identical or identical ZIP entries
    let cursor2 = Cursor::new(&rehyphenated_bytes);
    let mut reader2 = ZipArchive::new(cursor2).unwrap();
    let mut doc2 = String::new();
    reader2
        .by_name("word/document.xml")
        .unwrap()
        .read_to_string(&mut doc2)
        .unwrap();
    assert_eq!(doc_xml, doc2);
}

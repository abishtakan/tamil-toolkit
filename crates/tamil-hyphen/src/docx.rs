use std::fs;
use std::io::{Cursor, Read, Write};
use std::path::Path;
use zip::write::SimpleFileOptions;
use zip::{ZipArchive, ZipWriter};

use crate::text::{hyphenate_text, is_tamil_char, tokenize_words, TextToken};
use crate::types::{DocxError, DocxStats, HyphenationConfig};

const SOFT_HYPHEN: char = '\u{00AD}';

/// Checks if a ZIP entry name represents a WordprocessingML part containing text prose.
pub fn is_prose_xml_part(name: &str) -> bool {
    let lower = name.to_lowercase();
    if lower == "word/document.xml"
        || lower == "word/footnotes.xml"
        || lower == "word/endnotes.xml"
        || lower == "word/comments.xml"
    {
        return true;
    }

    if (lower.starts_with("word/header") || lower.starts_with("word/footer"))
        && lower.ends_with(".xml")
    {
        return true;
    }

    false
}

/// Hyphenates text runs inside `<w:t>` and `<m:t>` XML elements while preserving all
/// XML formatting, attributes, non-text tags, and non-Tamil content verbatim.
pub fn process_xml_text(
    xml: &str,
    config: Option<&HyphenationConfig>,
    stats: &mut DocxStats,
) -> Result<String, String> {
    let mut out = String::with_capacity(xml.len() + 256);
    let mut cursor = 0;
    let bytes = xml.as_bytes();
    let len = bytes.len();

    while cursor < len {
        // Count paragraphs (<w:p> or <w:p ...)
        if bytes[cursor..].starts_with(b"<w:p") {
            let after_wp = cursor + 4;
            if after_wp < len {
                let next_b = bytes[after_wp];
                if next_b == b'>' || next_b.is_ascii_whitespace() {
                    stats.paragraphs_processed += 1;
                }
            }
        }

        // Search for text run tag start: <w:t or <m:t
        let is_wt = bytes[cursor..].starts_with(b"<w:t");
        let is_mt = bytes[cursor..].starts_with(b"<m:t");

        if is_wt || is_mt {
            let tag_name = if is_wt { "w:t" } else { "m:t" };
            let tag_len = tag_name.len() + 1; // 4
            let after_tag = cursor + tag_len;

            if after_tag < len {
                let next_b = bytes[after_tag];
                // Must be followed by space, tab, newline, '>', or '/' (self-closing)
                if next_b == b'>' || next_b == b'/' || next_b.is_ascii_whitespace() {
                    // Find the end of this opening tag '>'
                    if let Some(open_tag_end_rel) = xml[cursor..].find('>') {
                        let open_tag_end = cursor + open_tag_end_rel;
                        let open_tag_str = &xml[cursor..=open_tag_end];

                        // Check if self-closing: e.g. <w:t/>
                        if open_tag_str.ends_with("/>") {
                            out.push_str(open_tag_str);
                            cursor = open_tag_end + 1;
                            continue;
                        }

                        // Find the matching closing tag </w:t> or </m:t>
                        let close_tag = format!("</{tag_name}>");
                        if let Some(close_tag_rel) = xml[open_tag_end + 1..].find(&close_tag) {
                            let text_start = open_tag_end + 1;
                            let text_end = open_tag_end + 1 + close_tag_rel;
                            let inner_text = &xml[text_start..text_end];

                            // Hyphenate the inner text if it contains Tamil
                            let mut has_tamil = false;
                            for c in inner_text.chars() {
                                if is_tamil_char(c) {
                                    has_tamil = true;
                                    break;
                                }
                            }

                            out.push_str(open_tag_str);

                            if has_tamil {
                                // Count pre-existing soft hyphens
                                let pre_soft_count =
                                    inner_text.chars().filter(|&c| c == SOFT_HYPHEN).count();

                                // Count Tamil words
                                for token in tokenize_words(inner_text) {
                                    if let TextToken::TamilWord(_) = token {
                                        stats.words_hyphenated += 1;
                                    }
                                }

                                let hyphenated = hyphenate_text(inner_text, config)?;
                                let post_soft_count =
                                    hyphenated.chars().filter(|&c| c == SOFT_HYPHEN).count();

                                if post_soft_count > pre_soft_count {
                                    stats.soft_hyphens_inserted +=
                                        post_soft_count - pre_soft_count;
                                }

                                out.push_str(&hyphenated);
                            } else {
                                out.push_str(inner_text);
                            }

                            out.push_str(&close_tag);
                            cursor = text_end + close_tag.len();
                            continue;
                        }
                    }
                }
            }
        }

        // Regular character pass-through
        if let Some(ch) = xml[cursor..].chars().next() {
            out.push(ch);
            cursor += ch.len_utf8();
        } else {
            break;
        }
    }

    Ok(out)
}

/// Hyphenates an in-memory `.docx` archive byte buffer and returns the updated archive and statistics.
pub fn process_docx_bytes(
    data: &[u8],
    config: Option<&HyphenationConfig>,
) -> Result<(Vec<u8>, DocxStats), DocxError> {
    let reader = Cursor::new(data);
    let mut archive = ZipArchive::new(reader)?;

    let out_buffer = Vec::with_capacity(data.len() + 2048);
    let out_cursor = Cursor::new(out_buffer);
    let mut writer = ZipWriter::new(out_cursor);

    let mut stats = DocxStats::default();

    for i in 0..archive.len() {
        let mut file = archive.by_index(i)?;
        let name = file.name().to_string();

        let options = SimpleFileOptions::default()
            .compression_method(file.compression())
            .unix_permissions(file.unix_mode().unwrap_or(0o644));

        let mut content = Vec::with_capacity(file.size() as usize);
        file.read_to_end(&mut content)?;

        if is_prose_xml_part(&name) {
            let xml_str = String::from_utf8(content).map_err(|e| DocxError::XmlError {
                part: name.clone(),
                error: format!("UTF-8 decode error: {e}"),
            })?;

            let updated_xml = process_xml_text(&xml_str, config, &mut stats).map_err(|e| {
                DocxError::XmlError {
                    part: name.clone(),
                    error: e,
                }
            })?;

            if updated_xml != xml_str {
                stats.parts_updated += 1;
            }

            writer.start_file(&name, options)?;
            writer.write_all(updated_xml.as_bytes())?;
        } else {
            // Passthrough non-prose parts byte-for-byte
            writer.start_file(&name, options)?;
            writer.write_all(&content)?;
        }
    }

    let finished_cursor = writer.finish()?;
    Ok((finished_cursor.into_inner(), stats))
}

/// Reads a `.docx` file from `input`, hyphenates all Tamil prose runs, and writes to `output`.
pub fn process_docx_file<P: AsRef<Path>, Q: AsRef<Path>>(
    input: P,
    output: Q,
    config: Option<&HyphenationConfig>,
) -> Result<DocxStats, DocxError> {
    let input_path = input.as_ref();
    let output_path = output.as_ref();

    if !input_path.exists() {
        return Err(DocxError::Io(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            format!("Input file not found: {}", input_path.display()),
        )));
    }

    let input_bytes = fs::read(input_path)?;
    let (output_bytes, stats) = process_docx_bytes(&input_bytes, config)?;

    // Handle atomic write (especially when input and output point to the same file)
    if input_path == output_path {
        let temp_path = input_path.with_extension("docx.tmp");
        fs::write(&temp_path, &output_bytes)?;
        fs::rename(&temp_path, output_path)?;
    } else {
        if let Some(parent) = output_path.parent() {
            if !parent.as_os_str().is_empty() && !parent.exists() {
                fs::create_dir_all(parent)?;
            }
        }
        fs::write(output_path, &output_bytes)?;
    }

    Ok(stats)
}

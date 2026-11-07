use std::fs::File;
use std::io::{self, Read, Write};
use std::path::Path;
use zip::write::SimpleFileOptions;
use zip::ZipWriter;

/// Generates META-INF/manifest.xml for LibreOffice extension.
pub fn generate_manifest_xml() -> &'static str {
    r#"<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="http://openoffice.org/2001/manifest">
  <manifest:file-entry manifest:media-type="application/vnd.sun.star.configuration-data"
                       manifest:full-path="dictionaries.xcu"/>
</manifest:manifest>
"#
}

/// Generates dictionaries.xcu binding hyph_ta_IN.dic to all Tamil locales.
pub fn generate_dictionaries_xcu() -> &'static str {
    r#"<?xml version="1.0" encoding="UTF-8"?>
<oor:component-data xmlns:oor="http://openoffice.org/2001/registry"
                    xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    oor:name="Linguistic"
                    oor:package="org.openoffice.Office">
  <node oor:name="ServiceManager">
    <node oor:name="Dictionaries">
      <node oor:name="HyphDic_ta" oor:op="fuse">
        <prop oor:name="Locations" oor:type="oor:string-list">
          <value>%origin%/hyph_ta_IN.dic</value>
        </prop>
        <prop oor:name="Format" oor:type="xs:string">
          <value>DICT_HYPH</value>
        </prop>
        <prop oor:name="Locales" oor:type="oor:string-list">
          <value>ta-IN ta-LK ta-SG ta-MY ta</value>
        </prop>
      </node>
    </node>
  </node>
</oor:component-data>
"#
}

/// Generates description.xml extension metadata.
pub fn generate_description_xml(version: &str) -> String {
    format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<description xmlns="http://openoffice.org/extensions/description/2006"
             xmlns:d="http://openoffice.org/extensions/description/2006"
             xmlns:xlink="http://www.w3.org/1999/xlink">
  <version value="{version}"/>
  <identifier value="org.tamiltoolkit.hyphenation"/>
  <display-name>
    <name lang="en">Tamil Syllabic Hyphenation Dictionary</name>
    <name lang="ta">தமிழ் அசைசார் சொல் பிரிப்பான்</name>
  </display-name>
  <publisher>
    <name xlink:href="https://github.com/tamil-toolkit/tamil-toolkit">Tamil Toolkit Community</name>
  </publisher>
</description>
"#
    )
}

/// Bundles the given `.dic` file into a ready-to-install LibreOffice `.oxt` extension.
pub fn package_oxt(
    dic_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
    version: &str,
) -> io::Result<()> {
    let dic_path = dic_path.as_ref();
    let output_path = output_path.as_ref();

    if let Some(parent) = output_path.parent() {
        std::fs::create_dir_all(parent)?;
    }

    let mut dic_content = Vec::new();
    let mut dic_file = File::open(dic_path)?;
    dic_file.read_to_end(&mut dic_content)?;

    let out_file = File::create(output_path)?;
    let mut zip = ZipWriter::new(out_file);
    let options = SimpleFileOptions::default().compression_method(zip::CompressionMethod::Deflated);

    // 1. META-INF/manifest.xml
    zip.start_file("META-INF/manifest.xml", options)?;
    zip.write_all(generate_manifest_xml().as_bytes())?;

    // 2. dictionaries.xcu
    zip.start_file("dictionaries.xcu", options)?;
    zip.write_all(generate_dictionaries_xcu().as_bytes())?;

    // 3. description.xml
    zip.start_file("description.xml", options)?;
    zip.write_all(generate_description_xml(version).as_bytes())?;

    // 4. hyph_ta_IN.dic
    zip.start_file("hyph_ta_IN.dic", options)?;
    zip.write_all(&dic_content)?;

    // 5. LICENSE.txt
    let license = r#"MIT License / LGPL v3 / GPL v3 Tri-license

Tamil Hyphenation Patterns & LibreOffice Extension
Developed by Tamil Toolkit Community (https://github.com/tamil-toolkit/tamil-toolkit)
Based on W3C Tamil Layout Requirements (tam-lreq) and Classical Tamil Orthography.
"#;
    zip.start_file("LICENSE.txt", options)?;
    zip.write_all(license.as_bytes())?;

    zip.finish()?;
    Ok(())
}

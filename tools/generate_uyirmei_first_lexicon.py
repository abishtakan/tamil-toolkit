import tomllib

def generate():
    with open("lexicon/collate.toml", "rb") as f:
        data = tomllib.load(f)

    order = data["order"]
    assert len(order) == 325

    vowels_aytham = order[:13]
    consonant_rows = []
    for i in range(13, len(order), 13):
        row = order[i:i+13]
        mei = row[0]
        uyirmei = row[1:]
        # In uyirmei-first-v1, the 12 vowel forms precede the mei
        consonant_rows.extend(uyirmei)
        consonant_rows.append(mei)

    new_order = vowels_aytham + consonant_rows
    assert len(new_order) == 325
    assert set(new_order) == set(order)

    # Read original text to preserve comments and format
    with open("lexicon/collate.toml", "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Lines 0 to 4 are header
    # Lines 6 to 18 (0-indexed) are vowels + visarga
    # Lines 19 to 330 are consonant rows
    header = [
        '# uyirmei-first-v1: Modern pedagogical school dictionary order (Uyirmei syllables precede pure consonant).\n',
        '# Sourced from Tamil Nadu textbook society and school lexicons.\n',
        'profile = "uyirmei-first-v1"\n',
        'key_version = 1\n',
        '\n',
        'order = [\n',
    ]

    vowel_lines = lines[6:19]
    consonant_lines = lines[19:331]

    new_consonant_lines = []
    for r in range(0, len(consonant_lines), 13):
        row_lines = consonant_lines[r:r+13]
        mei_line = row_lines[0]
        uyirmei_lines = row_lines[1:]
        new_consonant_lines.extend(uyirmei_lines)
        new_consonant_lines.append(mei_line)

    footer = lines[331:]

    all_lines = header + vowel_lines + new_consonant_lines + footer
    with open("lexicon/collate_uyirmei_first.toml", "w", encoding="utf-8", newline="\n") as f:
        f.writelines(all_lines)

    # Verify newly written toml
    with open("lexicon/collate_uyirmei_first.toml", "rb") as f:
        verified = tomllib.load(f)

    assert verified["profile"] == "uyirmei-first-v1"
    assert verified["key_version"] == 1
    assert len(verified["order"]) == 325
    assert verified["order"] == new_order
    print("Successfully generated and verified lexicon/collate_uyirmei_first.toml (325 elements)")

if __name__ == "__main__":
    generate()

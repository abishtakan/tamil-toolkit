# CLI Contract: `tamil-toolkit hyphen export-dic` & `package-oxt`

## 1. `export-dic` Command

Export phonotactically synthesized Frank Liang / Hunspell hyphenation patterns to a `.dic` file.

### Usage
```bash
tamil-toolkit hyphen export-dic [OPTIONS]
```

### Options
| Option | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output <PATH>` | `-o` | Path | `hyph_ta_IN.dic` | Destination filepath for the `.dic` dictionary |
| `--lefthyphenmin <N>` | `-l` | Integer | `2` | Minimum character margin before first hyphenation point |
| `--righthyphenmin <N>` | `-r` | Integer | `2` | Minimum character margin after last hyphenation point |
| `--verify` | | Flag | `false` | Run simulated hyphenation against golden corpus after export |

### Output
- Standard exit code `0` on success with summary to stdout:
  ```text
  Successfully exported 184 Frank Liang hyphenation patterns to hyph_ta_IN.dic
  LEFTHYPHENMIN: 2, RIGHTHYPHENMIN: 2, Enforced locales: ta-IN, ta-LK, ta-SG, ta-MY, ta
  ```
- Exit code `1` on invalid arguments or write errors.

---

## 2. `package-oxt` Command

Bundle the generated dictionary into a standard, distribution-ready LibreOffice extension (`.oxt`).

### Usage
```bash
tamil-toolkit hyphen package-oxt [OPTIONS]
```

### Options
| Option | Short | Type | Default | Description |
|---|---|---|---|---|
| `--input <PATH>` | `-i` | Path | `hyph_ta_IN.dic` | Source `.dic` file to bundle |
| `--output <PATH>` | `-o` | Path | `dist/tamil-hyphenation.oxt` | Destination `.oxt` archive path |
| `--version <VER>` | `-v` | String | Cargo workspace version | Extension version string |

### Output
- Generates a valid ZIP archive at `--output` containing:
  - `META-INF/manifest.xml`
  - `dictionaries.xcu`
  - `description.xml`
  - `hyph_ta_IN.dic`
  - `LICENSE.txt`
